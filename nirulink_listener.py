# NiRuLink FreeCAD - TCP Server
# Part of the NiRuLink family by NiRuLabs
# Uses Qt's QTcpServer for thread-safe socket handling

import json
import struct
import sys
import traceback
from io import StringIO

import FreeCAD
import FreeCADGui

try:
    from PySide2.QtCore import QObject, Signal, Slot
    from PySide2.QtNetwork import QTcpServer, QTcpSocket, QHostAddress
except ImportError:
    from PySide6.QtCore import QObject, Signal, Slot
    from PySide6.QtNetwork import QTcpServer, QTcpSocket, QHostAddress


class NiRuLinkFreeCADServer(QObject):
    """TCP server that executes Python code and returns results"""

    def __init__(self, port=9876, parent=None):
        super().__init__(parent)
        self.port = port
        self.server = None
        self.clients = []
        self.client_buffers = {}  # Buffer for incomplete messages

    def start(self):
        """Start the TCP server"""
        self.server = QTcpServer(self)
        self.server.newConnection.connect(self._on_new_connection)

        if self.server.listen(QHostAddress.LocalHost, self.port):
            FreeCAD.Console.PrintMessage(
                f"NiRuLink FreeCAD listening on localhost:{self.port}\n"
            )
            return True
        else:
            FreeCAD.Console.PrintError(
                f"NiRuLink FreeCAD failed to start: {self.server.errorString()}\n"
            )
            return False

    def stop(self):
        """Stop the server"""
        if self.server:
            for client in self.clients:
                client.close()
            self.server.close()
            FreeCAD.Console.PrintMessage("NiRuLink FreeCAD stopped\n")

    @Slot()
    def _on_new_connection(self):
        """Handle new client connection"""
        client = self.server.nextPendingConnection()
        if client:
            self.clients.append(client)
            self.client_buffers[client] = b""
            client.readyRead.connect(lambda: self._on_data_ready(client))
            client.disconnected.connect(lambda: self._on_client_disconnected(client))
            FreeCAD.Console.PrintMessage(
                f"NiRuLink FreeCAD: client connected from {client.peerAddress().toString()}\n"
            )

    def _on_client_disconnected(self, client):
        """Handle client disconnect"""
        if client in self.clients:
            self.clients.remove(client)
        if client in self.client_buffers:
            del self.client_buffers[client]
        FreeCAD.Console.PrintMessage("NiRuLink FreeCAD: client disconnected\n")

    def _on_data_ready(self, client):
        """Handle incoming data from client"""
        # Read all available data into buffer
        self.client_buffers[client] += bytes(client.readAll())
        buffer = self.client_buffers[client]

        # Process complete messages
        while len(buffer) >= 4:
            # Read message length (4 bytes, big-endian)
            msg_length = struct.unpack(">I", buffer[:4])[0]

            # Check if we have the complete message
            if len(buffer) < 4 + msg_length:
                break  # Wait for more data

            # Extract message
            msg_data = buffer[4 : 4 + msg_length]
            buffer = buffer[4 + msg_length :]
            self.client_buffers[client] = buffer

            # Process message
            try:
                request = json.loads(msg_data.decode("utf-8"))
                response = self._execute_request(request)
            except json.JSONDecodeError as e:
                response = {"ok": False, "error": f"Invalid JSON: {e}", "result": None, "output": ""}
            except Exception as e:
                response = {"ok": False, "error": str(e), "result": None, "output": ""}

            # Send response
            self._send_response(client, response)

    def _send_response(self, client, response):
        """Send length-prefixed JSON response"""
        data = json.dumps(response).encode("utf-8")
        length = struct.pack(">I", len(data))
        client.write(length + data)
        client.flush()

    def _execute_request(self, request):
        """Execute a code request and return the result"""

        # Handle ping requests (for MCP compatibility)
        if request.get("method") == "ping" or request.get("ping") or request.get("command") == "ping":
            return {"ok": True, "pong": True, "result": "pong", "output": ""}

        code = request.get("code", "")

        if not code:
            return {"ok": False, "error": "No code provided", "result": None, "output": ""}

        # Capture stdout
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        captured_output = StringIO()
        sys.stdout = captured_output
        sys.stderr = captured_output

        result = None
        error = None

        try:
            # Create execution namespace with FreeCAD modules
            namespace = {
                "FreeCAD": FreeCAD,
                "App": FreeCAD,
                "FreeCADGui": FreeCADGui,
                "Gui": FreeCADGui,
                "__builtins__": __builtins__,
            }

            # Try common imports
            try:
                import Part
                namespace["Part"] = Part
            except:
                pass

            try:
                import PartDesign
                namespace["PartDesign"] = PartDesign
            except:
                pass

            try:
                import Sketcher
                namespace["Sketcher"] = Sketcher
            except:
                pass

            try:
                import Draft
                namespace["Draft"] = Draft
            except:
                pass

            try:
                import Mesh
                namespace["Mesh"] = Mesh
            except:
                pass

            try:
                import Path
                namespace["Path"] = Path
            except:
                pass

            try:
                import Arch
                namespace["Arch"] = Arch
            except:
                pass

            # Try eval first (for expressions), fall back to exec (for statements)
            try:
                result = eval(code, namespace)
            except SyntaxError:
                exec(code, namespace)
                result = None

            # Convert result to string representation
            if result is not None:
                result = repr(result)

        except Exception as e:
            error = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"

        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        output = captured_output.getvalue()

        return {
            "ok": error is None,
            "result": result,
            "output": output,
            "error": error,
        }


# Global server instance
_server = None


def start_server(port=9876):
    """Start the NiRuLink FreeCAD server"""
    global _server
    if _server is None:
        _server = NiRuLinkFreeCADServer(port)
        _server.start()
    return _server


def stop_server():
    """Stop the NiRuLink FreeCAD server"""
    global _server
    if _server:
        _server.stop()
        _server = None
