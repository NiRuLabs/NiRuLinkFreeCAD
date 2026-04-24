# NiRuLink FreeCAD — User Manual

**Version 1.0.0** · Part of the NiRuLink family by NiRuLabs

NiRuLink FreeCAD lets an AI assistant that speaks MCP (Model Context Protocol) — such as Claude Code or Claude Desktop — drive FreeCAD for parametric mechanical design, 3D printing, and general CAD work. You describe what you want in plain language, the assistant picks the right tools, and parts appear in FreeCAD in real time.

---

## Table of contents

1. [How it works](#1-how-it-works)
2. [Prerequisites](#2-prerequisites)
3. [Installation](#3-installation)
4. [First-run verification](#4-first-run-verification)
5. [Connecting your MCP client](#5-connecting-your-mcp-client)
6. [Using the tools](#6-using-the-tools)
7. [Troubleshooting](#7-troubleshooting)
8. [Uninstalling](#8-uninstalling)
9. [Security notes](#9-security-notes)
10. [Protocol reference (for developers)](#10-protocol-reference-for-developers)

---

## 1. How it works

NiRuLink FreeCAD is a two-piece system.

```
┌──────────────┐  stdio/JSON-RPC  ┌──────────────┐  TCP :9876   ┌──────────────┐
│  MCP client  │◀────────────────▶│  MCP server  │◀────────────▶│   Add-on     │
│  (e.g.       │   (MCP 2024-11)  │  (Python     │  (length-    │   (inside    │
│  Claude Code)│                  │  process)    │  prefixed    │   FreeCAD)   │
└──────────────┘                  └──────────────┘  JSON)       └──────────────┘
                                                                       │
                                                                       ▼
                                                                 FreeCAD Python API
```

Both halves live in one GitHub repository (`NiRuLinkFreeCAD`). The **add-on** files sit at the repo root (`Init.py`, `InitGui.py`, `__init__.py`, `nirulink_listener.py`); they get installed into FreeCAD's `Mod` folder. When FreeCAD starts, the add-on loads automatically, registers a workbench called *NiRuLink FreeCAD*, and opens a Qt-based TCP listener on `localhost:9876`. Its job is to accept Python code from the server, execute it against FreeCAD's full API, capture the result, and send it back.

The **MCP server** lives in the `server/` subfolder of the same repo and runs as a stand-alone Python process. It speaks MCP over stdio on one side (so MCP clients like Claude can call its tools) and forwards commands to the add-on over TCP on the other side. It exposes sixteen high-level tools (see Section 6) that translate common CAD operations into the right FreeCAD Python calls.

The split exists because FreeCAD cannot itself be an MCP server — MCP clients want to launch and own the stdio lifecycle of the process they talk to, which is incompatible with a long-running GUI application. The add-on is the "hands inside FreeCAD"; the MCP server is the "translator" between MCP and FreeCAD's API.

---

## 2. Prerequisites

| Requirement        | Notes                                                                                     |
| ------------------ | ----------------------------------------------------------------------------------------- |
| FreeCAD            | Version 0.21 or later. Either the stable 0.21 series or 1.0. Ships with its own Python.   |
| Python 3.9+        | For running the MCP server. Use the system Python, not FreeCAD's embedded interpreter.    |
| An MCP client      | Claude Code (recommended, auto-configurable) or any MCP-capable client (manual config).   |
| Free TCP port 9876 | Default. Can be changed if in use — see Troubleshooting.                                  |
| Git (optional)     | Only needed if you install by `git clone` rather than downloading ZIPs.                   |

Supported operating systems: Windows 10/11, macOS 11+, Linux (tested on Ubuntu and Fedora). The add-on uses Qt, which FreeCAD already ships, so there are no additional native dependencies.

---

## 3. Installation

There are three installation paths. Pick whichever fits your situation.

### 3.1 Automated installer (recommended for Claude Code users)

This is the fastest path if you use Claude Code.

```bash
git clone https://github.com/YOUR-USERNAME/NiRuLinkFreeCAD.git
cd NiRuLinkFreeCAD/server
python install.py
```

What `install.py` does:

1. Finds your FreeCAD `Mod` directory for your OS.
2. Copies the repo's add-on files (the root-level `.py` files plus this repo's contents) into `Mod/NiRuLinkFreeCAD/`.
3. Registers this MCP server with Claude Code by running `claude mcp add nirulink-freecad -s user -- python /path/to/server/nirulink_mcp_server.py`.
4. Prints next-step instructions.

Flags:

| Flag            | Meaning                                                                 |
| --------------- | ----------------------------------------------------------------------- |
| *(no flag)*     | Install both the add-on and the Claude Code MCP config.                 |
| `--addon-only`  | Only copy the add-on into FreeCAD's `Mod` folder. Skip MCP client side. |
| `--mcp-only`    | Only register the MCP server with Claude Code. Skip the add-on copy.    |
| `--verify`      | Check that both the add-on and the MCP registration are in place.       |
| `--uninstall`   | Remove the add-on and the Claude Code MCP registration.                 |
| `--help`        | Show usage.                                                             |

The installer expects the default monorepo layout: `install.py` sits in `server/` and the add-on files are at the repo root. If you have moved files around, use manual installation.

### 3.2 Manual installation (works with any MCP client)

Use this path if you use Claude Desktop, Cline, Continue, or any other MCP client that isn't Claude Code.

**Step 1 — Install the add-on.** Copy the four add-on files from the repo root (`Init.py`, `InitGui.py`, `__init__.py`, `nirulink_listener.py`) into a new folder called `NiRuLinkFreeCAD` inside FreeCAD's `Mod` directory:

| OS      | Destination path                                             |
| ------- | ------------------------------------------------------------ |
| Windows | `%APPDATA%\FreeCAD\Mod\NiRuLinkFreeCAD\`                     |
| macOS   | `~/Library/Application Support/FreeCAD/Mod/NiRuLinkFreeCAD/` |
| Linux   | `~/.local/share/FreeCAD/Mod/NiRuLinkFreeCAD/`                |

After copying, the folder should contain `Init.py`, `InitGui.py`, `__init__.py`, and `nirulink_listener.py`.

**Step 2 — Register the MCP server with your client.** Configure your client to launch `nirulink_mcp_server.py` as an MCP server over stdio. The exact setting file differs between clients; the values are always the same:

| Field     | Value                                                     |
| --------- | --------------------------------------------------------- |
| Name      | `nirulink-freecad`                                        |
| Command   | `python` (or the full path to a Python 3.9+ interpreter)  |
| Arguments | `["/absolute/path/to/NiRuLinkFreeCAD/server/nirulink_mcp_server.py"]` |
| Transport | stdio                                                     |

**Example — Claude Desktop (`claude_desktop_config.json`):**

```json
{
  "mcpServers": {
    "nirulink-freecad": {
      "command": "python",
      "args": ["/absolute/path/to/NiRuLinkFreeCAD/server/nirulink_mcp_server.py"]
    }
  }
}
```

The config file lives at `%APPDATA%\Claude\claude_desktop_config.json` on Windows, `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS, and `~/.config/Claude/claude_desktop_config.json` on Linux.

**Example — Claude Code (CLI):**

```bash
claude mcp add nirulink-freecad -s user -- python /absolute/path/to/NiRuLinkFreeCAD/server/nirulink_mcp_server.py
```

### 3.3 FreeCAD Addon Manager

Once `NiRuLinkFreeCAD` is listed in the official FreeCAD-addons registry, you can install the add-on in one click:

1. In FreeCAD, open the **Tools → Addon Manager** menu.
2. Search for "NiRuLink".
3. Click **Install**.
4. Restart FreeCAD.

The Addon Manager clones the entire repo into `Mod/NiRuLinkFreeCAD/`, which includes the `server/` subfolder. FreeCAD ignores that subfolder — but the MCP server's Python files are already there, on disk, ready to run. You still need to configure your MCP client to point at `Mod/NiRuLinkFreeCAD/server/nirulink_mcp_server.py` (Section 3.2, step 2). Claude Code users can `cd` into that folder and run `python install.py --mcp-only` instead.

---

## 4. First-run verification

After installation, do this once to confirm everything works.

**Step 1 — Launch FreeCAD.** On the report view (View → Panels → Report view) you should see:

```
NiRuLink CAD addon loaded
NiRuLink FreeCAD listening on localhost:9876
```

If you don't see those lines, the add-on has not loaded — see Troubleshooting.

**Step 2 — Test the TCP connection standalone.** From the `server/` subfolder of the repo, run:

```bash
python test_connection.py
```

Expected output:

```
Testing NiRuLink CAD connection...
[OK] Connected to FreeCAD via NiRuLink CAD
[OK] FreeCAD version: ('0.21.2', ...)
[OK] Created test document
[OK] Objects in document: []
[OK] Closed test document

[OK] All tests passed! NiRuLink CAD is working.
```

**Step 3 — Test from your MCP client.** Start (or restart) your MCP client. Ask it to call the `connect_to_freecad` tool. It should reply with something like:

```
Connected to FreeCAD via NiRuLink FreeCAD at localhost:9876
FreeCAD version: ('0.21.2', '32353', '2024/01/15', ...)
```

---

## 5. Connecting your MCP client

Before any CAD tool will work, the MCP server has to open its TCP connection to the FreeCAD add-on. This is a one-time call per session.

In the client, invoke the tool **`connect_to_freecad`**. Optional arguments:

| Argument | Default     | Meaning                          |
| -------- | ----------- | -------------------------------- |
| `host`   | `localhost` | Host running FreeCAD.            |
| `port`   | `9876`      | TCP port the add-on listens on.  |

You only need to do this once per conversation. If the connection drops (e.g. FreeCAD is closed and reopened) you must call it again.

---

## 6. Using the tools

> **Status, as of v1.0.0:** This is a work in progress. The `execute_python` tool is the commissioned, battle-tested path and is currently the recommended way to drive FreeCAD through NiRuLink — it has turned out to be powerful enough on its own that the other fifteen tools haven't yet been needed in day-to-day use, and so they have not yet been commissioned against a live FreeCAD instance. They ship with the server and should work, but consider them provisional until they have been exercised. If you try one and it doesn't behave as expected, fall back to `execute_python` (Section 6.6) — it has the full FreeCAD API available and can do everything the high-level tools do. Feedback from early users on the high-level tools is welcome and will help prioritise which ones to commission first.

The MCP server exposes sixteen tools. They fall into five groups.

### 6.1 Connection

| Tool                  | Arguments            | What it does                                                |
| --------------------- | -------------------- | ----------------------------------------------------------- |
| `connect_to_freecad`  | `host?`, `port?`     | Opens TCP connection and pings FreeCAD. Call this first.    |

### 6.2 Document and body lifecycle

| Tool            | Arguments  | What it does                                                                  |
| --------------- | ---------- | ----------------------------------------------------------------------------- |
| `new_document`  | `name?`    | Creates a new FreeCAD document (equivalent to `App.newDocument(name)`).       |
| `create_body`   | `name?`    | Creates a PartDesign Body and makes it the active body for parametric work.   |

### 6.3 Sketching

| Tool                   | Arguments                                        | What it does                                                                       |
| ---------------------- | ------------------------------------------------ | ---------------------------------------------------------------------------------- |
| `create_sketch`        | `plane` (XY/XZ/YZ, default XY), `body?`          | Creates a sketch on a reference plane, attached to the active (or specified) body. |
| `add_sketch_rectangle` | `x`, `y`, `width`, `height`, `sketch?`           | Adds a rectangle to the active sketch, with coincident constraints at corners.     |
| `add_sketch_circle`    | `cx`, `cy`, `radius`, `sketch?`                  | Adds a circle to the active sketch.                                                |
| `close_sketch`         | `sketch?`                                        | Closes (finalizes) the sketch and triggers a recompute.                            |

### 6.4 3D operations

| Tool       | Arguments                                                        | What it does                                                                         |
| ---------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| `pad`      | `sketch`, `length`, `symmetric?`, `reversed?`                    | PartDesign Pad: extrude a sketch to add material.                                    |
| `pocket`   | `sketch`, `length?`, `through_all?`                              | PartDesign Pocket: remove material using a sketch as the profile.                    |
| `fillet`   | `radius`, `edges` (array of edge names)                          | Rounds the selected edges.                                                           |
| `chamfer`  | `size`, `edges` (array of edge names)                            | Chamfers the selected edges.                                                         |

Edge names look like `"Edge1"`, `"Edge2"`. The quickest way to find them is to call `get_shape_info` or ask the model to list them; FreeCAD also shows edge names in its tree when hovered.

### 6.5 Inspection and export

| Tool              | Arguments               | What it does                                                                                         |
| ----------------- | ----------------------- | ---------------------------------------------------------------------------------------------------- |
| `get_objects`     | *(none)*                | Lists all objects in the active document as `(name, type_id, label)` triples.                        |
| `get_shape_info`  | `object?`               | Returns volume, surface area, bounding-box dimensions, and centre of mass for the active/named body. |
| `export_stl`      | `filepath`, `object?`   | Writes an STL of the body to disk (good for 3D printing). Mesh resolution defaults to 0.1 mm.        |
| `export_step`     | `filepath`, `object?`   | Writes a STEP file (industry standard for CAD interchange).                                          |

### 6.6 Escape hatch

| Tool              | Arguments | What it does                                                                                                                  |
| ----------------- | --------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `execute_python`  | `code`    | Runs arbitrary Python inside FreeCAD. You have the full FreeCAD API: `FreeCAD`/`App`, `FreeCADGui`/`Gui`, `Part`, `PartDesign`, `Sketcher`, `Draft`, `Mesh`, `Path`, `Arch`. |

Use `execute_python` when you need something the high-level tools don't cover (e.g. loft, sweep, mirror, array, boolean ops on Part objects, or any custom macro). Anything you can type into FreeCAD's built-in Python console, you can run through this tool.

### 6.7 A worked example

What the MCP client sends → what appears in FreeCAD.

1. `connect_to_freecad` → *Connected to FreeCAD version 0.21.2*
2. `new_document` `{ name: "Bracket" }` → *Created document: Bracket*
3. `create_body` `{ name: "MainBody" }` → *Created body: MainBody*
4. `create_sketch` `{ plane: "XY" }` → *Created sketch on XY plane: Sketch*
5. `add_sketch_rectangle` `{ x: 0, y: 0, width: 40, height: 20 }` → *Added rectangle: 40x20mm at (0, 0)*
6. `close_sketch` → *Sketch closed*
7. `pad` `{ sketch: "Sketch", length: 5 }` → *Created pad: 5mm extrusion*
8. `fillet` `{ radius: 2, edges: ["Edge3", "Edge5"] }` → *Created fillet: 2mm radius*
9. `export_stl` `{ filepath: "/tmp/bracket.stl" }` → *Exported STL to: /tmp/bracket.stl*

At this point your bracket is ready to slice and print.

---

## 7. Troubleshooting

### "NiRuLink FreeCAD listening on localhost:9876" does not appear in FreeCAD

Check that the add-on folder is in the right place and is named exactly `NiRuLinkFreeCAD` (not `NiRuLinkFreeCAD-main` — which is what a GitHub ZIP download produces and needs renaming). The contents must include `__init__.py`, `InitGui.py`, and `nirulink_listener.py` directly inside that folder. Restart FreeCAD after moving files.

If it still fails, open **View → Panels → Python console** in FreeCAD and run:

```python
import nirulink_listener
nirulink_listener.start_server()
```

Any error message that appears will point you at the cause (most commonly a `PySide2` vs `PySide6` mismatch on older FreeCAD installs — the listener tries both but some niche builds have neither; install FreeCAD 0.21.2+ or 1.0+ to resolve).

### `Failed to connect to NiRuLink CAD at localhost:9876`

FreeCAD is probably not running, or the add-on isn't loaded. Also check for port conflict:

- Windows: `netstat -ano | findstr 9876`
- macOS / Linux: `lsof -iTCP:9876 -sTCP:LISTEN`

If port 9876 is taken by another process, you can change the port the add-on listens on by editing the last line of `InitGui.py` to `nirulink_listener.start_server(port=9xxx)`, then restart FreeCAD. Pass the same port to `connect_to_freecad` from your MCP client.

### The MCP server launches but no tools appear in my client

Make sure the client is actually running the server. In Claude Code, run `claude mcp list` — `nirulink-freecad` should appear. In Claude Desktop, check the MCP server icon in the input box. Restart the client after changing its configuration.

Check the MCP server's stderr for startup errors. Claude Code surfaces this automatically; Claude Desktop writes it to the app log.

### "Not connected to FreeCAD. Call connect_to_freecad first."

This happens when the other tools are invoked without having established the TCP connection first. Call `connect_to_freecad` once per session. If FreeCAD is restarted, call it again.

### Commands succeed but the 3D view doesn't update

Run `App.ActiveDocument.recompute()` via `execute_python`, or close and re-create the sketch using `close_sketch`. Some operations (like boolean combinations using `execute_python`) don't automatically trigger a recompute.

### Fillet or chamfer fails with "no suitable edge"

The edge name you supplied probably doesn't exist in the current body. Call `get_objects` and `get_shape_info` to inspect the model, or use `execute_python`:

```python
[e.Name for e in App.ActiveDocument.ActiveObject.Shape.Edges]
```

---

## 8. Uninstalling

### Via the installer (Claude Code users)

```bash
cd NiRuLinkFreeCAD/server
python install.py --uninstall
```

This removes the `Mod/NiRuLinkFreeCAD` folder and runs `claude mcp remove nirulink-freecad`.

### Manual uninstall

1. Delete `%APPDATA%\FreeCAD\Mod\NiRuLinkFreeCAD\` (Windows) / equivalent on macOS / Linux.
2. Remove the `nirulink-freecad` entry from your MCP client's configuration file.
3. Restart FreeCAD and your MCP client.

---

## 9. Security notes

- The add-on listens on `localhost` only (`QHostAddress.LocalHost`). Remote machines cannot reach it without your opening a firewall rule or using SSH forwarding.
- There is **no authentication** on the TCP channel. Any process on the same machine that can reach `localhost:9876` can execute arbitrary Python inside FreeCAD while FreeCAD is running. On a single-user developer machine this is equivalent to existing trust boundaries; on a shared machine, think twice.
- The MCP server does not sandbox or sanitise the code it forwards. `execute_python` can read/write files, make network requests, launch processes — anything Python can do inside FreeCAD. Treat it like a Python REPL.
- Don't forward port 9876 across a network. If you need remote operation, SSH tunnel and point `connect_to_freecad` at `localhost` on the tunnel endpoint.

---

## 10. Protocol reference (for developers)

For anyone wanting to write their own client, replace a component, or debug the wire.

### 10.1 Add-on TCP protocol (server ↔ add-on)

Transport: TCP on `localhost:9876`.
Framing: **4-byte big-endian length prefix**, followed by the payload.
Payload: UTF-8 encoded JSON.

**Request:**

```json
{ "code": "<python source as string>" }
```

**Response:**

```json
{
  "ok": true,
  "result": "<repr() of the expression value, or null>",
  "output": "<captured stdout/stderr during execution>",
  "error": null
}
```

On error: `ok` is `false`, `result` is `null`, `error` is a string including the exception type, message, and traceback.

The add-on tries `eval()` first; if that raises `SyntaxError`, it falls back to `exec()`. This means expressions return their value via `result` while statements don't.

The execution namespace pre-imports: `FreeCAD` (alias `App`), `FreeCADGui` (alias `Gui`), `Part`, `PartDesign`, `Sketcher`, `Draft`, `Mesh`, `Path`, `Arch`.

### 10.2 MCP server (client ↔ server)

Transport: stdio.
Protocol: JSON-RPC 2.0, one message per line.
MCP protocol version: `2024-11-05`.
Server name: `nirulink-freecad` · version `1.0.0`.

Methods implemented:

| Method                       | Notes                                                                    |
| ---------------------------- | ------------------------------------------------------------------------ |
| `initialize`                 | Returns server capabilities (only `tools`).                              |
| `notifications/initialized`  | Acknowledged, no response.                                               |
| `tools/list`                 | Returns the 16 tool schemas documented in Section 6.                     |
| `tools/call`                 | Invokes the named tool with the given arguments.                         |
| `ping`                       | Returns an empty result.                                                 |

The server logs to stderr (never stdout — stdout is reserved for MCP responses).

### 10.3 Writing your own client

The TCP protocol is stable and simple enough that you can drive the add-on directly without MCP. A minimal Python client:

```python
import socket, struct, json

def run(code, host="localhost", port=9876):
    s = socket.create_connection((host, port))
    try:
        msg = json.dumps({"code": code}).encode("utf-8")
        s.sendall(struct.pack(">I", len(msg)) + msg)

        (n,) = struct.unpack(">I", _recv(s, 4))
        return json.loads(_recv(s, n).decode("utf-8"))
    finally:
        s.close()

def _recv(s, n):
    buf = b""
    while len(buf) < n:
        chunk = s.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("closed")
        buf += chunk
    return buf

print(run("FreeCAD.Version()"))
```

### 10.4 File inventory

**Add-on files (at repo root):**

| File                     | Role                                                                    |
| ------------------------ | ----------------------------------------------------------------------- |
| `Init.py`                | Runs at FreeCAD startup for both GUI and headless (`freecadcmd`) modes. |
| `InitGui.py`             | GUI-only init; registers the workbench and starts the listener.         |
| `__init__.py`            | Marks the folder as a Python package (and for FreeCAD's scanner).        |
| `nirulink_listener.py`   | QTcpServer implementation; accepts connections, executes code.          |

**Server files (in `server/` subfolder):**

| File                       | Role                                                                           |
| -------------------------- | ------------------------------------------------------------------------------ |
| `nirulink_mcp_server.py`   | JSON-RPC/MCP stdio server. Houses the 16 tool definitions.                     |
| `nirulink_bridge.py`       | Thin TCP client used by the MCP server to talk to the add-on.                  |
| `install.py`               | Cross-platform installer. Handles Mod-folder copy and Claude Code MCP config.  |
| `build_installer.py`       | PyInstaller wrapper for producing a standalone `.exe` installer.               | File                       | Role                                                                           |
| -------------------------- | ------------------------------------------------------------------------------ |
| `nirulink_mcp_server.py`   | JSON-RPC/MCP stdio server. Houses the 16 tool definitions.                     |
| `nirulink_bridge.py`       | Thin TCP client used by the MCP server to talk to the add-on.                  |
| `install.py`               | Cross-platform installer. Handles Mod-folder copy and Claude Code MCP config.  |
| `build_installer.py`       | PyInstaller wrapper for producing a standalone `.exe` installer.               |
| `test_connection.py`       | Standalone smoke test against the add-on (does not require an MCP client).     |

---

## License

MIT License. Copyright (c) 2026 Arnold Vosloo / NiRuLabs. Full license text in the `LICENSE` file at the root of this repository.

---

## Contributing and feedback

Bug reports and pull requests are welcome on this GitHub repo. For general discussion, post on the [FreeCAD forum](https://forum.freecad.org/) in the **Add-ons** subforum — tag the post with `nirulink` so it's easy to find.
