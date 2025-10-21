#!/usr/bin/env python3
"""
Test GUI CANBUS Connection Through UDS Pathway
Tests if GUI can connect to bus_core and send/receive signals
"""

import sys
from pathlib import Path

# Add paths
ui_root = Path("F:/The Central Command/Command Center/UI")
bus_root = Path("F:/The Central Command/Command Center/Data Bus/Bus Core Design")
data_bus_root = Path("F:/The Central Command/Command Center/Data Bus")
sys.path.insert(0, str(ui_root))
sys.path.insert(0, str(bus_root))
sys.path.insert(0, str(data_bus_root))

from bus_core import DKIReportBus

def test_bus_connection():
    """Test basic bus connection"""
    print("=== Testing CANBUS Connection ===")
    
    try:
        # Initialize bus
        print("Initializing DKIReportBus...")
        bus = DKIReportBus()
        print("SUCCESS: Bus initialized")
        
        # Test signal emission
        print("Testing signal emission...")
        bus.emit("test.signal", {"test": "data"})
        print("SUCCESS: Signal emitted")
        
        # Test handler registration
        print("Testing handler registration...")
        def test_handler(payload):
            print(f"Handler received: {payload}")
            return {"response": "acknowledged"}
        
        bus.register_signal("gui.test", test_handler)
        print("SUCCESS: Handler registered")
        
        # Test signal with handler
        print("Testing signal with handler...")
        bus.emit("gui.test", {"message": "hello"})
        print("SUCCESS: Handler executed")
        
        print("\n=== CANBUS CONNECTION TEST PASSED ===")
        return True
        
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_bus_connection()
    sys.exit(0 if success else 1)

