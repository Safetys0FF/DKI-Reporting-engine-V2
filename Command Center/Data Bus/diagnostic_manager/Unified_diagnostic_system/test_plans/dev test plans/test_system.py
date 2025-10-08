#!/usr/bin/env python3
"""
Simple test script for Unified Diagnostic System
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from __init__ import UnifiedDiagnosticSystem
    
    print("Creating Unified Diagnostic System...")
    uds = UnifiedDiagnosticSystem()
    
    print("System Status:", uds.get_unified_status())
    print("CAN-BUS Status:", uds.get_bus_status())
    
    print("Launching system...")
    launch_result = uds.launch_diagnostic_system()
    print("Launch Result:", launch_result)
    
    if launch_result:
        print("System launched successfully!")
        print("Shutting down...")
        uds.shutdown_diagnostic_system()
        print("Shutdown complete.")
    else:
        print("System launch failed!")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
