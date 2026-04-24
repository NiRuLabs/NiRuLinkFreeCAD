#!/usr/bin/env python3
"""
NiRuLink FreeCAD - MCP Server
Part of the NiRuLink family by NiRuLabs
Provides full API access to FreeCAD
"""

import json
import sys
from typing import Any

from nirulink_bridge import NiRuLinkClient

# Global client
client: NiRuLinkClient | None = None


def log(msg: str):
    """Log to stderr (not stdout, which is for MCP protocol)"""
    print(msg, file=sys.stderr, flush=True)


def send_response(response: dict):
    """Send JSON-RPC response to stdout"""
    msg = json.dumps(response)
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()


def send_error(id: Any, code: int, message: str):
    """Send JSON-RPC error response"""
    send_response({
        "jsonrpc": "2.0",
        "id": id,
        "error": {"code": code, "message": message}
    })


def send_result(id: Any, result: Any):
    """Send JSON-RPC success response"""
    send_response({
        "jsonrpc": "2.0",
        "id": id,
        "result": result
    })


def handle_initialize(id: Any, params: dict):
    """Handle initialize request"""
    send_result(id, {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {}
        },
        "serverInfo": {
            "name": "nirulink-freecad",
            "version": "1.0.0"
        }
    })


def handle_tools_list(id: Any, params: dict):
    """Return list of available tools"""
    tools = [
        {
            "name": "connect_to_freecad",
            "description": "Connect to a running FreeCAD instance with NiRuLink FreeCAD addon",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "host": {
                        "type": "string",
                        "description": "Host address (default: localhost)",
                        "default": "localhost"
                    },
                    "port": {
                        "type": "integer",
                        "description": "Port number (default: 9876)",
                        "default": 9876
                    }
                }
            }
        },
        {
            "name": "execute_python",
            "description": "Execute Python code in FreeCAD. Has full access to FreeCAD API including FreeCAD (App), FreeCADGui (Gui), Part, PartDesign, Sketcher, Draft, Mesh, and all other modules.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code to execute in FreeCAD"
                    }
                },
                "required": ["code"]
            }
        },
        {
            "name": "new_document",
            "description": "Create a new FreeCAD document",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Document name",
                        "default": "Unnamed"
                    }
                }
            }
        },
        {
            "name": "create_body",
            "description": "Create a new PartDesign Body for parametric modeling",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Body name (optional)"
                    }
                }
            }
        },
        {
            "name": "create_sketch",
            "description": "Create a new sketch on a plane",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "plane": {
                        "type": "string",
                        "enum": ["XY", "XZ", "YZ"],
                        "description": "Plane to sketch on",
                        "default": "XY"
                    },
                    "body": {
                        "type": "string",
                        "description": "Body to attach sketch to (optional)"
                    }
                }
            }
        },
        {
            "name": "add_sketch_rectangle",
            "description": "Add a rectangle to the active sketch",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "x": {"type": "number", "description": "Bottom-left X coordinate (mm)"},
                    "y": {"type": "number", "description": "Bottom-left Y coordinate (mm)"},
                    "width": {"type": "number", "description": "Width (mm)"},
                    "height": {"type": "number", "description": "Height (mm)"},
                    "sketch": {"type": "string", "description": "Sketch name (optional)"}
                },
                "required": ["x", "y", "width", "height"]
            }
        },
        {
            "name": "add_sketch_circle",
            "description": "Add a circle to the active sketch",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "cx": {"type": "number", "description": "Center X coordinate (mm)"},
                    "cy": {"type": "number", "description": "Center Y coordinate (mm)"},
                    "radius": {"type": "number", "description": "Radius (mm)"},
                    "sketch": {"type": "string", "description": "Sketch name (optional)"}
                },
                "required": ["cx", "cy", "radius"]
            }
        },
        {
            "name": "close_sketch",
            "description": "Close/finalize a sketch",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "sketch": {"type": "string", "description": "Sketch name (optional)"}
                }
            }
        },
        {
            "name": "pad",
            "description": "Extrude a sketch to create a 3D solid (add material)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "sketch": {"type": "string", "description": "Sketch to extrude"},
                    "length": {"type": "number", "description": "Extrusion length (mm)"},
                    "symmetric": {"type": "boolean", "description": "Extrude both directions", "default": False},
                    "reversed": {"type": "boolean", "description": "Reverse direction", "default": False}
                },
                "required": ["sketch", "length"]
            }
        },
        {
            "name": "pocket",
            "description": "Cut into a solid using a sketch (remove material)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "sketch": {"type": "string", "description": "Sketch defining cut profile"},
                    "length": {"type": "number", "description": "Cut depth (mm), 0 for through all"},
                    "through_all": {"type": "boolean", "description": "Cut through entire part", "default": False}
                },
                "required": ["sketch"]
            }
        },
        {
            "name": "fillet",
            "description": "Add fillet (rounded edge) to edges",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "radius": {"type": "number", "description": "Fillet radius (mm)"},
                    "edges": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Edge names to fillet (e.g., ['Edge1', 'Edge2'])"
                    }
                },
                "required": ["radius", "edges"]
            }
        },
        {
            "name": "chamfer",
            "description": "Add chamfer (angled cut) to edges",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "size": {"type": "number", "description": "Chamfer size (mm)"},
                    "edges": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Edge names to chamfer"
                    }
                },
                "required": ["size", "edges"]
            }
        },
        {
            "name": "export_stl",
            "description": "Export model to STL format for 3D printing",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Output file path (.stl)"},
                    "object": {"type": "string", "description": "Object to export (optional)"}
                },
                "required": ["filepath"]
            }
        },
        {
            "name": "export_step",
            "description": "Export model to STEP format",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Output file path (.step)"},
                    "object": {"type": "string", "description": "Object to export (optional)"}
                },
                "required": ["filepath"]
            }
        },
        {
            "name": "get_objects",
            "description": "List all objects in the active document",
            "inputSchema": {
                "type": "object",
                "properties": {}
            }
        },
        {
            "name": "get_shape_info",
            "description": "Get information about a shape (volume, area, bounding box)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "object": {"type": "string", "description": "Object name (optional)"}
                }
            }
        }
    ]
    send_result(id, {"tools": tools})


def handle_tool_call(id: Any, params: dict):
    """Handle tool invocation"""
    global client

    tool_name = params.get("name")
    args = params.get("arguments", {})

    try:
        if tool_name == "connect_to_freecad":
            host = args.get("host", "localhost")
            port = args.get("port", 9876)
            log(f"Connecting to FreeCAD at {host}:{port}...")
            client = NiRuLinkClient(host, port)
            client.connect()
            log("TCP connection established, testing with ping...")

            # Test the connection with a simple command
            try:
                test_result = client.execute("FreeCAD.Version()")
                log(f"Ping test result: {test_result}")
                if test_result.get("ok"):
                    version = test_result.get("result", "unknown")
                    send_result(id, {
                        "content": [{"type": "text", "text": f"Connected to FreeCAD via NiRuLink FreeCAD at {host}:{port}\nFreeCAD version: {version}"}]
                    })
                else:
                    error_msg = test_result.get("error", "Unknown error during connection test")
                    raise ConnectionError(f"Connection test failed: {error_msg}")
            except Exception as e:
                log(f"Connection test failed: {e}")
                client.disconnect()
                client = None
                raise

        elif tool_name == "execute_python":
            if not client or not client.is_connected():
                raise ConnectionError("Not connected to FreeCAD. Call connect_to_freecad first.")
            code = args.get("code", "")
            result = client.execute(code)

            # Format response
            text_parts = []
            if result.get("ok"):
                if result.get("output"):
                    text_parts.append(f"Output:\n{result['output']}")
                if result.get("result"):
                    text_parts.append(f"Result: {result['result']}")
                if not text_parts:
                    text_parts.append("Executed successfully (no output)")
            else:
                text_parts.append(f"Error:\n{result.get('error', 'Unknown error')}")

            send_result(id, {
                "content": [{"type": "text", "text": "\n".join(text_parts)}]
            })

        elif tool_name == "new_document":
            if not client:
                raise ConnectionError("Not connected to FreeCAD")
            name = args.get("name", "Unnamed")
            result = client.execute(f'App.newDocument("{name}")')
            send_result(id, {
                "content": [{"type": "text", "text": f"Created document: {name}"}]
            })

        elif tool_name == "create_body":
            if not client:
                raise ConnectionError("Not connected to FreeCAD")
            name = args.get("name", "Body")
            code = f'''
doc = App.ActiveDocument
body = doc.addObject("PartDesign::Body", "{name}")
Gui.ActiveDocument.ActiveView.setActiveObject("pdbody", body)
body.Label
'''
            result = client.execute(code)
            send_result(id, {
                "content": [{"type": "text", "text": f"Created body: {result.get('result', name)}"}]
            })

        elif tool_name == "create_sketch":
            if not client:
                raise ConnectionError("Not connected to FreeCAD")
            plane = args.get("plane", "XY")
            body = args.get("body")

            plane_map = {"XY": "XY_Plane", "XZ": "XZ_Plane", "YZ": "YZ_Plane"}
            plane_obj = plane_map.get(plane, "XY_Plane")

            code = f'''
doc = App.ActiveDocument
sketch = doc.addObject("Sketcher::SketchObject", "Sketch")
body = doc.getObject("{body}") if "{body}" else Gui.ActiveDocument.ActiveView.getActiveObject("pdbody")
if body:
    body.addObject(sketch)
sketch.AttachmentSupport = [(doc.getObject("{plane_obj}"), "")]
sketch.MapMode = "FlatFace"
Gui.ActiveDocument.setEdit(sketch.Name)
sketch.Name
'''
            result = client.execute(code)
            send_result(id, {
                "content": [{"type": "text", "text": f"Created sketch on {plane} plane: {result.get('result', 'Sketch')}"}]
            })

        elif tool_name == "add_sketch_rectangle":
            if not client:
                raise ConnectionError("Not connected to FreeCAD")
            x, y = args["x"], args["y"]
            w, h = args["width"], args["height"]
            sketch = args.get("sketch", "")

            code = f'''
import Part
sketch = App.ActiveDocument.getObject("{sketch}") if "{sketch}" else App.ActiveDocument.ActiveObject
sketch.addGeometry(Part.LineSegment(App.Vector({x}, {y}, 0), App.Vector({x+w}, {y}, 0)))
sketch.addGeometry(Part.LineSegment(App.Vector({x+w}, {y}, 0), App.Vector({x+w}, {y+h}, 0)))
sketch.addGeometry(Part.LineSegment(App.Vector({x+w}, {y+h}, 0), App.Vector({x}, {y+h}, 0)))
sketch.addGeometry(Part.LineSegment(App.Vector({x}, {y+h}, 0), App.Vector({x}, {y}, 0)))
# Add coincident constraints to close the rectangle
sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1))
sketch.addConstraint(Sketcher.Constraint("Coincident", 1, 2, 2, 1))
sketch.addConstraint(Sketcher.Constraint("Coincident", 2, 2, 3, 1))
sketch.addConstraint(Sketcher.Constraint("Coincident", 3, 2, 0, 1))
App.ActiveDocument.recompute()
"Rectangle added"
'''
            result = client.execute(code)
            send_result(id, {
                "content": [{"type": "text", "text": f"Added rectangle: {w}x{h}mm at ({x}, {y})"}]
            })

        elif tool_name == "add_sketch_circle":
            if not client:
                raise ConnectionError("Not connected to FreeCAD")
            cx, cy, radius = args["cx"], args["cy"], args["radius"]
            sketch = args.get("sketch", "")

            code = f'''
import Part
sketch = App.ActiveDocument.getObject("{sketch}") if "{sketch}" else App.ActiveDocument.ActiveObject
sketch.addGeometry(Part.Circle(App.Vector({cx}, {cy}, 0), App.Vector(0, 0, 1), {radius}))
App.ActiveDocument.recompute()
"Circle added"
'''
            result = client.execute(code)
            send_result(id, {
                "content": [{"type": "text", "text": f"Added circle: radius {radius}mm at ({cx}, {cy})"}]
            })

        elif tool_name == "close_sketch":
            if not client:
                raise ConnectionError("Not connected to FreeCAD")
            sketch = args.get("sketch", "")
            code = f'''
sketch = App.ActiveDocument.getObject("{sketch}") if "{sketch}" else App.ActiveDocument.ActiveObject
Gui.ActiveDocument.resetEdit()
App.ActiveDocument.recompute()
"Sketch closed"
'''
            result = client.execute(code)
            send_result(id, {
                "content": [{"type": "text", "text": "Sketch closed"}]
            })

        elif tool_name == "pad":
            if not client:
                raise ConnectionError("Not connected to FreeCAD")
            sketch = args["sketch"]
            length = args["length"]
            symmetric = args.get("symmetric", False)
            reversed_dir = args.get("reversed", False)

            code = f'''
doc = App.ActiveDocument
sketch = doc.getObject("{sketch}")
body = Gui.ActiveDocument.ActiveView.getActiveObject("pdbody")
pad = doc.addObject("PartDesign::Pad", "Pad")
if body:
    body.addObject(pad)
pad.Profile = sketch
pad.Length = {length}
pad.Symmetric = {symmetric}
pad.Reversed = {reversed_dir}
doc.recompute()
Gui.ActiveDocument.ActiveView.viewIsometric()
Gui.SendMsgToActiveView("ViewFit")
pad.Name
'''
            result = client.execute(code)
            send_result(id, {
                "content": [{"type": "text", "text": f"Created pad: {length}mm extrusion"}]
            })

        elif tool_name == "pocket":
            if not client:
                raise ConnectionError("Not connected to FreeCAD")
            sketch = args["sketch"]
            length = args.get("length", 0)
            through_all = args.get("through_all", False)

            pocket_type = "PartDesign.Pocket.ThroughAll" if through_all else "PartDesign.Pocket.Dimension"
            code = f'''
doc = App.ActiveDocument
sketch = doc.getObject("{sketch}")
body = Gui.ActiveDocument.ActiveView.getActiveObject("pdbody")
pocket = doc.addObject("PartDesign::Pocket", "Pocket")
if body:
    body.addObject(pocket)
pocket.Profile = sketch
pocket.Type = {"1" if through_all else "0"}  # 0=Dimension, 1=ThroughAll
pocket.Length = {length}
doc.recompute()
pocket.Name
'''
            result = client.execute(code)
            send_result(id, {
                "content": [{"type": "text", "text": f"Created pocket: {'through all' if through_all else f'{length}mm deep'}"}]
            })

        elif tool_name == "fillet":
            if not client:
                raise ConnectionError("Not connected to FreeCAD")
            radius = args["radius"]
            edges = args["edges"]

            edge_list = ", ".join([f'"{e}"' for e in edges])
            code = f'''
doc = App.ActiveDocument
body = Gui.ActiveDocument.ActiveView.getActiveObject("pdbody")
fillet = doc.addObject("PartDesign::Fillet", "Fillet")
if body:
    body.addObject(fillet)
    base = body.Tip
    fillet.Base = (base, [{edge_list}])
fillet.Radius = {radius}
doc.recompute()
fillet.Name
'''
            result = client.execute(code)
            send_result(id, {
                "content": [{"type": "text", "text": f"Created fillet: {radius}mm radius"}]
            })

        elif tool_name == "chamfer":
            if not client:
                raise ConnectionError("Not connected to FreeCAD")
            size = args["size"]
            edges = args["edges"]

            edge_list = ", ".join([f'"{e}"' for e in edges])
            code = f'''
doc = App.ActiveDocument
body = Gui.ActiveDocument.ActiveView.getActiveObject("pdbody")
chamfer = doc.addObject("PartDesign::Chamfer", "Chamfer")
if body:
    body.addObject(chamfer)
    base = body.Tip
    chamfer.Base = (base, [{edge_list}])
chamfer.Size = {size}
doc.recompute()
chamfer.Name
'''
            result = client.execute(code)
            send_result(id, {
                "content": [{"type": "text", "text": f"Created chamfer: {size}mm"}]
            })

        elif tool_name == "export_stl":
            if not client:
                raise ConnectionError("Not connected to FreeCAD")
            filepath = args["filepath"].replace("\\", "/")
            obj = args.get("object", "")

            code = f'''
import Mesh
doc = App.ActiveDocument
obj = doc.getObject("{obj}") if "{obj}" else Gui.ActiveDocument.ActiveView.getActiveObject("pdbody")
if obj:
    shape = obj.Shape if hasattr(obj, "Shape") else obj.Tip.Shape
    mesh = Mesh.Mesh()
    mesh.addFacets(shape.tessellate(0.1)[0])
    mesh.write("{filepath}")
    "Exported to {filepath}"
else:
    "No object to export"
'''
            result = client.execute(code)
            send_result(id, {
                "content": [{"type": "text", "text": f"Exported STL to: {filepath}"}]
            })

        elif tool_name == "export_step":
            if not client:
                raise ConnectionError("Not connected to FreeCAD")
            filepath = args["filepath"].replace("\\", "/")
            obj = args.get("object", "")

            code = f'''
import Part
doc = App.ActiveDocument
obj = doc.getObject("{obj}") if "{obj}" else Gui.ActiveDocument.ActiveView.getActiveObject("pdbody")
if obj:
    shape = obj.Shape if hasattr(obj, "Shape") else obj.Tip.Shape
    shape.exportStep("{filepath}")
    "Exported to {filepath}"
else:
    "No object to export"
'''
            result = client.execute(code)
            send_result(id, {
                "content": [{"type": "text", "text": f"Exported STEP to: {filepath}"}]
            })

        elif tool_name == "get_objects":
            if not client:
                raise ConnectionError("Not connected to FreeCAD")
            code = '''
doc = App.ActiveDocument
if doc:
    objects = [(obj.Name, obj.TypeId, obj.Label) for obj in doc.Objects]
    objects
else:
    "No active document"
'''
            result = client.execute(code)
            send_result(id, {
                "content": [{"type": "text", "text": f"Objects:\n{result.get('result', 'None')}"}]
            })

        elif tool_name == "get_shape_info":
            if not client:
                raise ConnectionError("Not connected to FreeCAD")
            obj = args.get("object", "")

            code = f'''
doc = App.ActiveDocument
obj = doc.getObject("{obj}") if "{obj}" else Gui.ActiveDocument.ActiveView.getActiveObject("pdbody")
if obj:
    shape = obj.Shape if hasattr(obj, "Shape") else obj.Tip.Shape
    info = {{
        "volume": shape.Volume,
        "area": shape.Area,
        "bbox": (shape.BoundBox.XLength, shape.BoundBox.YLength, shape.BoundBox.ZLength),
        "center": (shape.CenterOfMass.x, shape.CenterOfMass.y, shape.CenterOfMass.z)
    }}
    info
else:
    "No object found"
'''
            result = client.execute(code)
            send_result(id, {
                "content": [{"type": "text", "text": f"Shape info:\n{result.get('result', 'None')}"}]
            })

        else:
            send_error(id, -32601, f"Unknown tool: {tool_name}")

    except Exception as e:
        send_result(id, {
            "content": [{"type": "text", "text": f"Error: {str(e)}"}],
            "isError": True
        })


def handle_request(request: dict):
    """Route request to appropriate handler"""
    method = request.get("method")
    id = request.get("id")
    params = request.get("params", {})

    if method == "initialize":
        handle_initialize(id, params)
    elif method == "notifications/initialized":
        pass  # No response needed
    elif method == "tools/list":
        handle_tools_list(id, params)
    elif method == "tools/call":
        handle_tool_call(id, params)
    elif method == "ping":
        log("Handling ping request")
        send_result(id, {})
    else:
        if id is not None:  # Only send error for requests, not notifications
            send_error(id, -32601, f"Method not found: {method}")


def main():
    """Main loop - read JSON-RPC requests from stdin, write responses to stdout"""
    log("NiRuLink FreeCAD MCP Server starting...")

    # Use unbuffered stdin reading for Windows compatibility
    import io
    stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', newline='\n')

    for line in stdin:
        line = line.strip()
        if not line:
            continue

        log(f"Received: {line[:500]}")  # Log incoming requests (truncated)

        try:
            request = json.loads(line)
            log(f"Parsed method: {request.get('method')}")
            handle_request(request)
        except json.JSONDecodeError as e:
            log(f"Invalid JSON: {e}")
            send_error(None, -32700, f"Parse error: {e}")
        except Exception as e:
            log(f"Error handling request: {e}")
            send_error(None, -32603, f"Internal error: {e}")


if __name__ == "__main__":
    main()
