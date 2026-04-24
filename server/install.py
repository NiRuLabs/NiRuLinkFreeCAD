#!/usr/bin/env python3
"""
NiRuLink FreeCAD Installer
==========================
Installs the FreeCAD addon and configures Claude Code MCP settings.

Usage:
    python install.py              # Install everything
    python install.py --uninstall  # Remove installation
    python install.py --addon-only # Install only the FreeCAD addon
    python install.py --verify     # Verify installation

Part of the NiRuLink family by NiRuLabs
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ADDON_NAME = "NiRuLinkFreeCAD"
MCP_SERVER_NAME = "nirulink-freecad"
VERSION = "1.0.0"


def get_install_dir():
    """Get the directory containing the installer.

    Handles both:
    - Running as Python script: uses __file__
    - Running as PyInstaller exe: uses sys.executable
    """
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller exe
        return Path(sys.executable).parent.resolve()
    else:
        # Running as Python script
        return Path(__file__).parent.resolve()


def get_freecad_mod_path():
    """Get the FreeCAD Mod directory path."""
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "FreeCAD" / "Mod"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "FreeCAD" / "Mod"
    else:
        # Linux
        return Path.home() / ".local" / "share" / "FreeCAD" / "Mod"
    return None


def get_server_path():
    """Get the absolute path to the MCP server script."""
    install_dir = get_install_dir()
    # When running as exe, server is in NiRuLinkFreeCAD-server subfolder
    # When running as script, it's in the same folder as install.py
    if getattr(sys, 'frozen', False):
        return install_dir / "NiRuLinkFreeCAD-server" / "nirulink_mcp_server.py"
    else:
        return install_dir / "nirulink_mcp_server.py"


def get_addon_source_path():
    """Get the path to the addon source directory.

    In the monorepo layout the addon files live at the repo root,
    and install.py lives in repo_root/server/. So when running as a
    Python script, the addon source is install.py's parent directory
    (i.e. the repo root itself).

    When running as a PyInstaller exe, build_installer.py bundles the
    addon files into a NiRuLinkFreeCAD-addon subfolder next to the exe.
    """
    install_dir = get_install_dir()
    if getattr(sys, 'frozen', False):
        return install_dir / "NiRuLinkFreeCAD-addon"
    else:
        return install_dir.parent


def install_addon():
    """Install the FreeCAD addon."""
    source_dir = get_addon_source_path()
    mod_path = get_freecad_mod_path()

    if not mod_path:
        print("  [X] Could not determine FreeCAD Mod directory")
        return False

    if not source_dir.exists():
        print(f"  [X] Addon source not found at {source_dir}")
        return False

    target_dir = mod_path / ADDON_NAME

    print(f"\n  Installing FreeCAD Addon")
    print(f"  Source: {source_dir}")
    print(f"  Target: {target_dir}")

    # Create Mod directory if needed
    mod_path.mkdir(parents=True, exist_ok=True)

    # Remove existing installation
    if target_dir.exists():
        print(f"  Removing existing installation...")
        shutil.rmtree(target_dir)

    # Copy addon files (skip VCS, bytecode, and editor cruft)
    print(f"  Copying addon files...")
    ignore = shutil.ignore_patterns(
        ".git", ".github", "__pycache__",
        "*.pyc", "*.pyo", ".DS_Store",
        ".vscode", ".idea",
    )
    shutil.copytree(source_dir, target_dir, ignore=ignore)

    print("  [OK] Addon installed successfully!")
    return True


def configure_claude_code():
    """Configure Claude Code MCP settings using 'claude mcp add' command."""
    server_path = get_server_path()

    print(f"\n  Configuring Claude Code")
    print(f"  Server: {server_path}")

    # Use forward slashes for cross-platform compatibility
    server_path_str = str(server_path).replace("\\", "/")

    # First, try to remove any existing configuration (ignore errors)
    subprocess.run(
        ["claude", "mcp", "remove", MCP_SERVER_NAME],
        capture_output=True,
        text=True
    )

    # Add the MCP server using claude mcp add
    # Format: claude mcp add <name> -s user -- <command> <args>
    result = subprocess.run(
        ["claude", "mcp", "add", MCP_SERVER_NAME, "-s", "user", "--",
         "python", server_path_str],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("  [OK] Claude Code configured!")
        print(f"  Added MCP server: {MCP_SERVER_NAME}")
        return True
    else:
        print(f"  [X] Failed to configure Claude Code")
        print(f"  Error: {result.stderr}")
        return False


def uninstall_addon():
    """Remove the FreeCAD addon."""
    mod_path = get_freecad_mod_path()
    if not mod_path:
        print("  [X] Could not determine FreeCAD Mod directory")
        return False

    target_dir = mod_path / ADDON_NAME

    print(f"\n  Uninstalling Addon")
    if target_dir.exists():
        print(f"  Removing {target_dir}")
        shutil.rmtree(target_dir)
        print("  [OK] Addon removed!")
    else:
        print("  Addon not installed")
    return True


def unconfigure_claude_code():
    """Remove Claude Code MCP configuration using 'claude mcp remove' command."""
    print(f"\n  Removing Claude Code Configuration")

    result = subprocess.run(
        ["claude", "mcp", "remove", MCP_SERVER_NAME],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print(f"  [OK] Removed {MCP_SERVER_NAME} from MCP servers")
    else:
        # Not configured is not an error
        if "not found" in result.stderr.lower() or "does not exist" in result.stderr.lower():
            print(f"  {MCP_SERVER_NAME} was not configured")
        else:
            print(f"  Warning: {result.stderr}")
    return True


def verify_installation():
    """Verify the installation."""
    print("\n  Verifying Installation")
    print("  " + "-" * 40)
    all_ok = True

    # Check addon
    mod_path = get_freecad_mod_path()
    addon_path = mod_path / ADDON_NAME if mod_path else None

    if addon_path and addon_path.exists():
        required_files = ["__init__.py", "InitGui.py", "nirulink_listener.py"]
        missing = [f for f in required_files if not (addon_path / f).exists()]
        if missing:
            print(f"  [X] Addon missing files: {missing}")
            all_ok = False
        else:
            print(f"  [OK] Addon installed: {addon_path}")
    else:
        print(f"  [X] Addon not installed")
        all_ok = False

    # Check Claude Code config using 'claude mcp list'
    result = subprocess.run(
        ["claude", "mcp", "list"],
        capture_output=True,
        text=True
    )

    if result.returncode == 0 and MCP_SERVER_NAME in result.stdout:
        print(f"  [OK] Claude Code MCP configured: {MCP_SERVER_NAME}")
    else:
        print(f"  [X] {MCP_SERVER_NAME} not found in Claude Code MCP servers")
        all_ok = False

    # Check nirulink_mcp_server.py exists
    server_path = get_server_path()
    if server_path.exists():
        print(f"  [OK] MCP server: {server_path}")
    else:
        print(f"  [X] MCP server not found: {server_path}")
        all_ok = False

    print("  " + "-" * 40)
    if all_ok:
        print("  All checks passed!")
    else:
        print("  Some checks failed - see above")

    return all_ok


def print_banner():
    """Print installation banner."""
    print(r"""
    _   _ _           _     _       _      ______              _____          _____
   | \ | (_)         | |   (_)     | |    |  ____|            / ____|   /\   |  __ \
   |  \| |_ _ __ _   | |    _ _ __ | | __ | |__ _ __ ___  ___| |       /  \  | |  | |
   | . ` | | '__| | | | |   | | '_ \| |/ / |  __| '__/ _ \/ _ \ |      / /\ \ | |  | |
   | |\  | | |  | |_| | |___| | | | |   <  | |  | | |  __/  __/ |____ / ____ \| |__| |
   |_| \_|_|_|   \__,_|_____|_|_| |_|_|\_\ |_|  |_|  \___|\___|\_____/_/    \_\_____/

                           FreeCAD + Claude Code Connector
                                    by NiRuLabs
                                   Version """ + VERSION + """
""")


def print_next_steps():
    """Print post-installation instructions."""
    print(r"""
  +-------------------------------------------------------------------+
  |                          NEXT STEPS                               |
  +-------------------------------------------------------------------+
  |                                                                   |
  |  1. Start (or restart) FreeCAD                                    |
  |     Look for: "NiRuLink FreeCAD listening on localhost:9876"      |
  |                                                                   |
  |  2. Start (or restart) Claude Code                                |
  |     The """ + MCP_SERVER_NAME + """ MCP server should be available          |
  |                                                                   |
  |  3. In Claude Code, use: connect_to_freecad                       |
  |     Then: new_document, create_body, create_sketch, pad, etc.     |
  |                                                                   |
  +-------------------------------------------------------------------+
""")


def print_usage():
    """Print usage information."""
    print("""
  Usage:
    python install.py              Install addon + configure Claude Code
    python install.py --addon-only Install only the FreeCAD addon
    python install.py --mcp-only   Configure only Claude Code MCP settings
    python install.py --uninstall  Remove installation
    python install.py --verify     Verify installation
    python install.py --help       Show this help
""")


def main():
    print_banner()

    if "--help" in sys.argv or "-h" in sys.argv:
        print_usage()
        return 0

    if "--uninstall" in sys.argv:
        uninstall_addon()
        unconfigure_claude_code()
        print("\n  Uninstallation complete!")
        return 0

    if "--verify" in sys.argv:
        return 0 if verify_installation() else 1

    addon_only = "--addon-only" in sys.argv
    mcp_only = "--mcp-only" in sys.argv

    success = True

    # Install addon (unless mcp-only)
    if not mcp_only:
        if not install_addon():
            print("\n  [X] Addon installation failed!")
            success = False

    # Configure Claude Code (unless addon-only)
    if not addon_only:
        if not configure_claude_code():
            print("\n  [X] Claude Code configuration failed!")
            success = False

    if success:
        print("\n  Installation complete!")
        print_next_steps()
        verify_installation()
        return 0
    else:
        print("\n  Installation had errors - see above")
        return 1


def wait_for_key():
    """Wait for user input before closing (only when running as exe)."""
    if getattr(sys, 'frozen', False):
        print("\n  Press Enter to exit...")
        try:
            input()
        except EOFError:
            pass  # No stdin available (running non-interactively)


if __name__ == "__main__":
    result = main()
    wait_for_key()
    sys.exit(result)
