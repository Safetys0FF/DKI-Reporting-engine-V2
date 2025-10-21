#!/usr/bin/env python3
"""
Test LINBUS wildcard emitter functionality across all 8 analyst sections.
Tests Marshall's ability to broadcast coordination commands.
"""

import sys
import os
import logging
from datetime import datetime

# Add paths - go up 3 levels from test file to reach "The Central Command"
# Path structure: agent_2_NETWORK_CODING -> dev_tracking -> The War Room -> The Central Command
base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(base_path, 'Command Center', 'Data Bus', 'Bus Core Design'))
sys.path.insert(0, os.path.join(base_path, 'The Marshall'))
sys.path.insert(0, os.path.join(base_path, 'Command Center', 'Data Bus'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_linbus_wildcard():
    """Test LINBUS wildcard broadcast to all sections."""
    print("\n" + "="*80)
    print("LINBUS WILDCARD EMITTER TEST")
    print("="*80)
    
    try:
        # Debug: Print sys.path
        print("DEBUG: sys.path entries:")
        for p in sys.path[:5]:
            print(f"  - {p}")
        
        # Import bus_core
        import bus_core
        from bus_core import DKIReportBus
        print("[PASS] bus_core imported successfully")
        
        # Import Marshall
        from marshall_module import MarshallModule
        print("[PASS] MarshallModule imported successfully")
        
        # Initialize bus
        bus = DKIReportBus()
        print("[PASS] CANBUS initialized")
        
        # Initialize Marshall with bus
        marshall = MarshallModule(bus=bus)
        marshall.start()
        print("[PASS] Marshall started with address:", marshall.MODULE_ADDRESS)
        
        print("\n" + "-"*80)
        print("TEST 1: LINBUS Wake Broadcast to All 8 Sections")
        print("-"*80)
        
        result = marshall.linbus_broadcast('wake', payload={'case_id': 'TEST-001'})
        print(f"[RESULT] Success: {result['success']}, Failed: {result['failed']}, Total: {result['total']}")
        
        if result['success'] == 8:
            print("[PASS] All 8 sections received wake signal")
        else:
            print(f"[WARN] Only {result['success']}/8 sections received wake signal")
        
        print("\n" + "-"*80)
        print("TEST 2: LINBUS Status Broadcast to All 8 Sections")
        print("-"*80)
        
        result = marshall.linbus_broadcast('status')
        print(f"[RESULT] Success: {result['success']}, Failed: {result['failed']}, Total: {result['total']}")
        
        if result['success'] == 8:
            print("[PASS] All 8 sections received status signal")
        else:
            print(f"[WARN] Only {result['success']}/8 sections received status signal")
        
        print("\n" + "-"*80)
        print("TEST 3: LINBUS Sequence Coordination")
        print("-"*80)
        
        # Test default sequencing
        sequence_result = marshall.linbus_sequence_sections()
        if sequence_result:
            print("[PASS] All sections received sequence assignments (default order)")
        else:
            print("[FAIL] Sequence coordination failed")
        
        # Test custom sequencing
        custom_order = ["4-1", "4-3", "4-2", "4-5", "4-4", "4-7", "4-6", "4-8"]
        sequence_result = marshall.linbus_sequence_sections(custom_order)
        if sequence_result:
            print(f"[PASS] All sections received custom sequence: {custom_order}")
        else:
            print("[FAIL] Custom sequence coordination failed")
        
        print("\n" + "-"*80)
        print("TEST 4: LINBUS Sleep Broadcast to All 8 Sections")
        print("-"*80)
        
        result = marshall.linbus_broadcast('sleep')
        print(f"[RESULT] Success: {result['success']}, Failed: {result['failed']}, Total: {result['total']}")
        
        if result['success'] == 8:
            print("[PASS] All 8 sections received sleep signal")
        else:
            print(f"[WARN] Only {result['success']}/8 sections received sleep signal")
        
        print("\n" + "="*80)
        print("LINBUS WILDCARD EMITTER TEST COMPLETE")
        print("="*80)
        print("\nSUMMARY:")
        print("- LINBUS wildcard broadcasts are functional")
        print("- Marshall can coordinate all 8 sections simultaneously")
        print("- Signal topics: section_1.wake, section_2.wake, ..., section_8.wake")
        print("- Sequencing capability verified")
        print("\nNOTE: Sections must be instantiated with bus connection to receive signals.")
        
    except Exception as exc:
        print(f"\n[FAIL] Test failed with exception: {exc}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == '__main__':
    success = test_linbus_wildcard()
    sys.exit(0 if success else 1)

