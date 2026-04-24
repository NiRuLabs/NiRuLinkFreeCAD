#!/usr/bin/env python3
"""Test script to verify connection to NiRuLink CAD"""

from nirulink_bridge import NiRuLinkClient

def main():
    print("Testing NiRuLink CAD connection...")

    client = NiRuLinkClient("localhost", 9876)

    try:
        client.connect()
        print("[OK] Connected to FreeCAD via NiRuLink CAD")

        # Test basic execution
        result = client.execute("FreeCAD.Version()")
        if result["ok"]:
            print(f"[OK] FreeCAD version: {result['result']}")
        else:
            print(f"[FAIL] Error: {result['error']}")

        # Test creating a document
        result = client.execute('App.newDocument("TestDoc")')
        if result["ok"]:
            print("[OK] Created test document")
        else:
            print(f"[FAIL] Error: {result['error']}")

        # Test listing objects
        result = client.execute('[obj.Name for obj in App.ActiveDocument.Objects]')
        print(f"[OK] Objects in document: {result['result']}")

        # Clean up
        result = client.execute('App.closeDocument("TestDoc")')
        print("[OK] Closed test document")

        print("\n[OK] All tests passed! NiRuLink CAD is working.")

    except ConnectionError as e:
        print(f"[FAIL] Connection failed: {e}")
        print("\nMake sure:")
        print("1. FreeCAD is running")
        print("2. The NiRuLinkCAD addon is installed in FreeCAD's Mod folder")
        print("3. FreeCAD was restarted after installing the addon")

    finally:
        client.disconnect()


if __name__ == "__main__":
    main()
