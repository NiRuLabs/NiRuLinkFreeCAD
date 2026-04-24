"""
NiRuLink CAD - TCP Client
Part of the NiRuLink family by NiRuLabs
Communicates with NiRuLink CAD addon via length-prefixed JSON protocol
"""

import json
import socket
import struct
from typing import Any, Optional


class NiRuLinkClient:
    """Client for communicating with NiRuLink CAD server"""

    def __init__(self, host: str = "localhost", port: int = 9876):
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None

    def connect(self, timeout: float = 30.0) -> bool:
        """Connect to NiRuLink CAD server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(timeout)
            self.socket.connect((self.host, self.port))
            return True
        except Exception as e:
            self.socket = None
            raise ConnectionError(f"Failed to connect to NiRuLink CAD at {self.host}:{self.port}: {e}")

    def disconnect(self):
        """Disconnect from server"""
        if self.socket:
            self.socket.close()
            self.socket = None

    def is_connected(self) -> bool:
        """Check if connected"""
        return self.socket is not None

    def execute(self, code: str) -> dict[str, Any]:
        """
        Execute Python code in FreeCAD and return result

        Returns dict with:
        - ok: bool - True if execution succeeded
        - result: str | None - repr() of return value
        - output: str - captured stdout/stderr
        - error: str | None - error message if failed
        """
        if not self.socket:
            raise ConnectionError("Not connected to FreeCAD")

        # Send request
        request = {"code": code}
        self._send(request)

        # Receive response
        return self._receive()

    def _send(self, data: dict):
        """Send length-prefixed JSON message"""
        msg = json.dumps(data).encode("utf-8")
        length = struct.pack(">I", len(msg))
        self.socket.sendall(length + msg)

    def _receive(self) -> dict:
        """Receive length-prefixed JSON message"""
        # Read length (4 bytes)
        length_data = self._recv_exact(4)
        if not length_data:
            raise ConnectionError("Connection closed by server")

        msg_length = struct.unpack(">I", length_data)[0]

        # Read message
        msg_data = self._recv_exact(msg_length)
        if not msg_data:
            raise ConnectionError("Connection closed by server")

        return json.loads(msg_data.decode("utf-8"))

    def _recv_exact(self, n: int) -> bytes:
        """Receive exactly n bytes"""
        data = b""
        while len(data) < n:
            chunk = self.socket.recv(n - len(data))
            if not chunk:
                return b""
            data += chunk
        return data


# Convenience function for one-off execution
def execute_in_freecad(code: str, host: str = "localhost", port: int = 9876) -> dict:
    """Execute code in FreeCAD (opens new connection each time)"""
    client = NiRuLinkClient(host, port)
    client.connect()
    try:
        return client.execute(code)
    finally:
        client.disconnect()
