#!/usr/bin/env python3
"""
Build script for NiRuLink FreeCAD Installer
Creates distributable .exe files and packages everything into a zip.

Usage:
    python build_installer.py

Output:
    dist/NiRuLinkFreeCAD-Installer.zip
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

# Paths
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent
ADDON_DIR = PROJECT_ROOT / "NiRuLinkFreeCAD-addon"
SERVER_DIR = SCRIPT_DIR
DIST_DIR = SCRIPT_DIR / "dist"
BUILD_DIR = SCRIPT_DIR / "build"
PACKAGE_NAME = "NiRuLinkFreeCAD-Installer"


def clean():
    """Remove previous build artifacts."""
    print("\n[1/5] Cleaning previous builds...")
    for d in [DIST_DIR, BUILD_DIR]:
        if d.exists():
            shutil.rmtree(d)
            print(f"  Removed {d}")

    # Remove .spec files
    for spec in SCRIPT_DIR.glob("*.spec"):
        spec.unlink()
        print(f"  Removed {spec}")


def build_exe(script_name: str, exe_name: str):
    """Build an executable using PyInstaller."""
    print(f"\n  Building {exe_name}...")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", exe_name,
        "--distpath", str(DIST_DIR),
        "--workpath", str(BUILD_DIR),
        "--specpath", str(BUILD_DIR),
        "--clean",
        "--noconfirm",
        str(SCRIPT_DIR / script_name)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"  [X] Failed to build {exe_name}")
        print(result.stderr)
        return False

    print(f"  [OK] Built {exe_name}")
    return True


def create_uninstaller_script():
    """Create a simple uninstaller script."""
    uninstall_script = SCRIPT_DIR / "uninstall_wrapper.py"
    uninstall_script.write_text('''#!/usr/bin/env python3
"""Uninstaller wrapper - calls install.py --uninstall"""
import sys
sys.argv.append("--uninstall")
exec(open("install.py").read())
''')
    return uninstall_script


def build_executables():
    """Build the installer and uninstaller executables."""
    print("\n[2/5] Building executables...")

    # Build main installer
    if not build_exe("install.py", "Install-NiRuLinkFreeCAD"):
        return False

    # For uninstaller, we'll create a modified version
    uninstall_py = SCRIPT_DIR / "uninstall.py"
    uninstall_py.write_text('''#!/usr/bin/env python3
"""
NiRuLink FreeCAD Uninstaller
Removes the FreeCAD addon and Claude Code MCP configuration.
"""
import sys
# Force uninstall mode
sys.argv = [sys.argv[0], "--uninstall"]
# Import and run the installer in uninstall mode
from install import main
sys.exit(main())
''')

    if not build_exe("uninstall.py", "Uninstall-NiRuLinkFreeCAD"):
        uninstall_py.unlink()
        return False

    # Clean up temp uninstall script
    uninstall_py.unlink()

    return True


def create_package_structure():
    """Create the final package directory structure."""
    print("\n[3/5] Creating package structure...")

    package_dir = DIST_DIR / PACKAGE_NAME
    package_dir.mkdir(parents=True, exist_ok=True)

    # Copy executables
    for exe in ["Install-NiRuLinkFreeCAD.exe", "Uninstall-NiRuLinkFreeCAD.exe"]:
        src = DIST_DIR / exe
        dst = package_dir / exe
        if src.exists():
            shutil.copy2(src, dst)
            print(f"  Copied {exe}")

    # Copy addon folder
    addon_dst = package_dir / "NiRuLinkFreeCAD-addon"
    if ADDON_DIR.exists():
        shutil.copytree(ADDON_DIR, addon_dst)
        print(f"  Copied NiRuLinkFreeCAD-addon/")
    else:
        print(f"  [X] Addon directory not found: {ADDON_DIR}")
        return False

    # Copy server files
    server_dst = package_dir / "NiRuLinkFreeCAD-server"
    server_dst.mkdir(exist_ok=True)

    server_files = [
        "nirulink_mcp_server.py",
        "nirulink_bridge.py",
        "README.md"
    ]

    for f in server_files:
        src = SERVER_DIR / f
        if src.exists():
            shutil.copy2(src, server_dst / f)
            print(f"  Copied NiRuLinkFreeCAD-server/{f}")

    # Create a simple README for the package
    readme = package_dir / "README.txt"
    readme.write_text("""NiRuLink FreeCAD - Claude Code + FreeCAD Connector
==================================================
Part of the NiRuLink family by NiRuLabs

INSTALLATION
------------
1. Double-click "Install-NiRuLinkFreeCAD.exe"
2. Start (or restart) FreeCAD
3. Start (or restart) Claude Code
4. In Claude Code, use: connect_to_freecad

UNINSTALLATION
--------------
Double-click "Uninstall-NiRuLinkFreeCAD.exe"

WHAT GETS INSTALLED
-------------------
1. FreeCAD Addon -> %APPDATA%\\FreeCAD\\Mod\\NiRuLinkFreeCAD\\
2. Claude Code MCP config -> ~/.claude/settings.json

For more info, see NiRuLinkFreeCAD-server/README.md
""")
    print(f"  Created README.txt")

    return True


def create_zip():
    """Create the final distributable zip file."""
    print("\n[4/5] Creating zip archive...")

    package_dir = DIST_DIR / PACKAGE_NAME
    zip_path = DIST_DIR / f"{PACKAGE_NAME}.zip"

    with ZipFile(zip_path, 'w') as zipf:
        for file_path in package_dir.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(DIST_DIR)
                zipf.write(file_path, arcname)
                print(f"  Added {arcname}")

    print(f"\n  [OK] Created {zip_path}")
    print(f"  Size: {zip_path.stat().st_size / 1024 / 1024:.2f} MB")

    return zip_path


def cleanup_build():
    """Remove intermediate build files."""
    print("\n[5/5] Cleaning up...")

    # Remove individual exe files (they're in the zip now)
    for exe in DIST_DIR.glob("*.exe"):
        exe.unlink()
        print(f"  Removed {exe.name}")

    # Remove build directory
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
        print(f"  Removed build/")

    # Remove spec files
    for spec in SCRIPT_DIR.glob("*.spec"):
        spec.unlink()


def main():
    print("""
    _   _ _           _     _       _      ______              _____          _____
   | \\ | (_)         | |   (_)     | |    |  ____|            / ____|   /\\   |  __ \\
   |  \\| |_ _ __ _   | |    _ _ __ | | __ | |__ _ __ ___  ___| |       /  \\  | |  | |
   | . ` | | '__| | | | |   | | '_ \\| |/ / |  __| '__/ _ \\/ _ \\ |      / /\\ \\ | |  | |
   | |\\  | | |  | |_| | |___| | | | |   <  | |  | | |  __/  __/ |____ / ____ \\| |__| |
   |_| \\_|_|_|   \\__,_|_____|_|_| |_|_|\\_\\ |_|  |_|  \\___|\\___|\\____/_/    \\_\\_____/

                              BUILD INSTALLER
                                by NiRuLabs
""")

    clean()

    if not build_executables():
        print("\n[X] Build failed!")
        return 1

    if not create_package_structure():
        print("\n[X] Package creation failed!")
        return 1

    zip_path = create_zip()

    cleanup_build()

    print(f"""
  =====================================================
  BUILD COMPLETE!
  =====================================================

  Output: {zip_path}

  To test:
  1. Extract the zip
  2. Double-click Install-NiRuLinkFreeCAD.exe
  3. Check FreeCAD and Claude Code

  To distribute:
  - Upload {PACKAGE_NAME}.zip to S3 or GitHub releases
  =====================================================
""")

    return 0


if __name__ == "__main__":
    sys.exit(main())
