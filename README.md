# NiRuLink FreeCAD

**MCP (Model Context Protocol) bridge between AI assistants and FreeCAD.**
Part of the NiRuLink family by NiRuLabs.

NiRuLink FreeCAD lets an AI assistant that speaks MCP — such as Claude Code
or Claude Desktop — drive FreeCAD for parametric mechanical design, 3D
printing, and general CAD work. You describe what you want in plain language;
the assistant picks the right tools; parts appear in FreeCAD in real time.

## Demo

[![NiRuLink FreeCAD demo — AI-driven CAD with Claude](https://img.youtube.com/vi/FvuR39n4I9U/maxresdefault.jpg)](https://youtu.be/FvuR39n4I9U)

Click the thumbnail to watch on YouTube.

## What's in this repo

This repo contains both halves of the system:

```
NiRuLinkFreeCAD/              ← FreeCAD add-on (this folder, when installed in FreeCAD's Mod directory)
├── Init.py
├── InitGui.py
├── __init__.py
├── nirulink_listener.py
└── server/                   ← MCP server (runs as a separate Python process)
    ├── nirulink_mcp_server.py
    ├── nirulink_bridge.py
    ├── install.py
    ├── build_installer.py
    └── test_connection.py
```

The add-on files live at the repo root so FreeCAD's Addon Manager picks them
up when it clones the repository into `Mod/NiRuLinkFreeCAD/`. The MCP server
lives in the `server/` subfolder; FreeCAD simply ignores it.

## Architecture

```
┌──────────────┐  stdio/JSON-RPC  ┌──────────────┐  TCP :9876   ┌──────────────┐
│  MCP client  │◀────────────────▶│  MCP server  │◀────────────▶│   Add-on     │
│  (e.g.       │   (MCP 2024-11)  │  (server/    │  (length-    │   (root of   │
│  Claude Code)│                  │  Python)     │  prefixed    │   this repo) │
└──────────────┘                  └──────────────┘  JSON)       └──────────────┘
                                                                       │
                                                                       ▼
                                                                 FreeCAD Python API
```

## Quick install

### Claude Code users (automated)

```bash
git clone https://github.com/YOUR-USERNAME/NiRuLinkFreeCAD.git
cd NiRuLinkFreeCAD/server
python install.py
```

`install.py` copies the repo into FreeCAD's `Mod` folder and registers the
MCP server with Claude Code.

### Other MCP clients (manual)

1. Copy the **contents of this repo's root** (not the `server/` subfolder)
   into FreeCAD's `Mod/NiRuLinkFreeCAD/` directory. Specifically these four
   Python files: `Init.py`, `InitGui.py`, `__init__.py`,
   `nirulink_listener.py`.
2. Configure your MCP client (e.g. Claude Desktop) to launch
   `server/nirulink_mcp_server.py` with Python over stdio.

See `USER_MANUAL.md` for detailed install paths, per-client config examples,
usage examples for all 16 MCP tools, the wire protocol, and troubleshooting.

## FreeCAD Addon Manager

Once this repository is listed in the official FreeCAD-addons registry, users
can install the add-on in one click: **Tools → Addon Manager → search
"NiRuLink" → Install**. They will still need to configure the MCP server
separately (it runs outside FreeCAD).

## Status

**Version 1.0.0 — work in progress.** The `execute_python` tool is
commissioned and is currently the recommended way to drive FreeCAD. The
other fifteen high-level tools (sketch, pad, pocket, fillet, chamfer, etc.)
are implemented but not yet commissioned. See `USER_MANUAL.md` §6 for
details and the fallback pattern.

## License

MIT — see `LICENSE`. Copyright (c) 2026 Arnold Vosloo / NiRuLabs.

## Contributing

Bug reports and pull requests are welcome on this GitHub repo. For general
discussion, post on the [FreeCAD forum](https://forum.freecad.org/) in the
**Add-ons** subforum — tag the post with `nirulink` so it's easy to find.
