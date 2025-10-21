#!/usr/bin/env python3
"""
Main entry point for Central Command GUI
Launches GUIModule (parent module wrapper) with full CANBUS integration
"""

import sys
# Add Processors directory for psutil and other dependencies (GUI runs as subprocess)
sys.path.insert(0, r"F:\The Central Command\The War Room\Processors")

import traceback
from gui_module import GUIModule
from enhanced_functional_gui import EnhancedDKIGUI


def main():
    """Launch GUI with GUIModule integration"""
    try:
        # Initialize GUI Module (parent module wrapper)
        print("[LAUNCH] Initializing GUI-1 parent module...")
        gui_module = GUIModule()
        
        # Run startup controller
        print("[LAUNCH] Running startup sequence...")
        if not gui_module.initialize_system():
            print("[FATAL] GUI initialization failed - check logs")
            return 1
        
        print("[LAUNCH] GUI-1 ready - starting Enhanced GUI...")
        
        # Create Enhanced GUI instance (integrated with parent module)
        gui = EnhancedDKIGUI(gui_module=gui_module)
        
        # Register GUI instance with module
        gui_module.set_gui_instance(gui)
        
        # Store reference to module in GUI
        gui.gui_module = gui_module
        
        print("[LAUNCH] GUI launched successfully")
        print("=" * 70)
        print("CENTRAL COMMAND GUI - ONLINE")
        print(f"Module: {gui_module.module_address}")
        print(f"State: {gui_module.state.value}")
        print(f"Bus: {'Connected' if gui_module.bus else 'SAFEMODE'}")
        print("=" * 70)
        
        # Start GUI mainloop (blocking)
        gui.mainloop()
        
        # Shutdown when GUI closes
        print("\n[SHUTDOWN] GUI closed - running shutdown sequence...")
        gui_module.shutdown()
        
        print("[OK] Shutdown complete")
        return 0
        
    except Exception as e:
        print(f"[ERROR] GUI launch failed: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
