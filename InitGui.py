# NiRuLink FreeCAD - GUI initialization
# Part of the NiRuLink family by NiRuLabs

import FreeCAD
import FreeCADGui

class NiRuLinkFreeCADWorkbench(FreeCADGui.Workbench):
    """Minimal workbench for NiRuLink FreeCAD"""

    MenuText = "NiRuLink FreeCAD"
    ToolTip = "FreeCAD + Claude Code connector by NiRuLabs"

    def Initialize(self):
        pass

    def Activated(self):
        pass

    def Deactivated(self):
        pass

# Register workbench
FreeCADGui.addWorkbench(NiRuLinkFreeCADWorkbench())

# Start the listener
import nirulink_listener
nirulink_listener.start_server()
