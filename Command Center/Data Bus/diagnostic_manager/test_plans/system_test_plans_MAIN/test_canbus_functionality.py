#!/usr/bin/env python3
"""
Test CAN-BUS functionality and communication capabilities
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_canbus_connection():
    """Test CAN-BUS connection and communication"""
    print("=" * 60)
    print("TESTING CAN-BUS CONNECTION AND FUNCTIONALITY")
    print("=" * 60)
    
    try:
        from __init__ import UnifiedDiagnosticSystem
        
        print("1. Creating Unified Diagnostic System...")
        uds = UnifiedDiagnosticSystem()
        
        print("2. Checking CAN-BUS Status...")
        bus_status = uds.get_bus_status()
        print(f"   CAN-BUS Available: {bus_status['bus_available']}")
        print(f"   CAN-BUS Connected: {bus_status['bus_connected']}")
        print(f"   Registered Addresses: {bus_status['registered_addresses']}")
        
        if not bus_status['bus_available']:
            print("   WARNING: CAN-BUS not available - checking Bus Core Design path...")
            bus_core_path = Path(__file__).parent.parent.parent / "Bus Core Design"
            print(f"   Bus Core Design Path: {bus_core_path}")
            print(f"   Bus Core Design Exists: {bus_core_path.exists()}")
            
            if bus_core_path.exists():
                bus_core_files = list(bus_core_path.glob("*.py"))
                print(f"   Bus Core Files Found: {[f.name for f in bus_core_files]}")
        
        print("\n3. Testing System Registry and Communication...")
        print(f"   Systems Registered: {len(uds.core.system_registry)}")
        
        if uds.core.system_registry:
            print("   Sample Systems:")
            for i, (address, info) in enumerate(list(uds.core.system_registry.items())[:3]):
                print(f"     {address}: {info.get('name', 'Unknown')}")
        
        print("\n4. Testing Diagnostic Capabilities...")
        
        # Test payload creation
        print("   Testing payload creation...")
        payload = uds.create_diagnostic_payload("test", {"test_data": "hello"})
        print(f"   Payload created: {payload['operation']} ({payload['size_bytes']} bytes)")
        
        # Test rollcall
        print("   Testing rollcall transmission...")
        rollcall_result = uds.transmit_rollcall()
        print(f"   Rollcall result: {rollcall_result}")
        
        # Test radio check
        print("   Testing radio check...")
        radio_result = uds.transmit_radio_check("1-1.1")
        print(f"   Radio check result: {radio_result}")
        
        # Test SOS fault transmission
        print("   Testing SOS fault transmission...")
        sos_result = uds.transmit_sos_fault("1-1.1", "01-001", "Test fault")
        print(f"   SOS fault result: {sos_result}")
        
        print("\n5. Testing Test Plan Execution...")
        test_result = uds.execute_test_plan("1-1.1", "smoke_test")
        print(f"   Test execution: {test_result['tests_executed']} tests executed")
        print(f"   Tests passed: {test_result['tests_passed']}")
        print(f"   Tests failed: {test_result['tests_failed']}")
        
        print("\n6. Testing System Launch...")
        launch_result = uds.launch_diagnostic_system()
        print(f"   System launch: {'SUCCESS' if launch_result else 'FAILED'}")
        
        if launch_result:
            print("   System launched successfully - testing shutdown...")
            uds.shutdown_diagnostic_system()
            print("   System shutdown complete")
        
        print("\n" + "=" * 60)
        print("CAN-BUS FUNCTIONALITY TEST COMPLETE")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_canbus_connection()
    sys.exit(0 if success else 1)
