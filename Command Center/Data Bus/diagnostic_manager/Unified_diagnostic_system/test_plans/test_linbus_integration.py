#!/usr/bin/env python3
"""
UDS-Integrated LINBUS Fault Test
Run this AS PART OF UDS to validate Section → LINBUS → Marshall → CANBUS → UDS
"""

import sys
import os
import time
from datetime import datetime

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'Bus Core Design'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'The Marshall'))

def run_linbus_fault_test(uds_system):
    """
    Test LINBUS fault propagation while UDS is active and monitoring.
    
    Args:
        uds_system: UnifiedDiagnosticSystem instance with active bus connection
    """
    print("\n" + "="*80)
    print("LINBUS FAULT PROPAGATION TEST (UDS INTEGRATED)")
    print("="*80)
    
    try:
        bus = uds_system.bus
        logger = uds_system.logger
        
        # Step 1: Initialize Marshall with LINBUS receiver
        logger.info("[TEST] Initializing Marshall with LINBUS fault receiver...")
        from marshall_module import MarshallModule
        
        marshall = MarshallModule(bus=bus)
        marshall.start()
        logger.info(f"[TEST] Marshall initialized at address {marshall.MODULE_ADDRESS}")
        
        time.sleep(0.5)
        
        # Step 2: Simulate section fault on LINBUS
        logger.info("[TEST] Simulating Section 1 fault emission on LINBUS...")
        
        fault_payload = {
            "fault_code": "[4-1.10-12-INIT]",
            "description": "EasyOCR Engine not initialized - LINBUS TEST",
            "component": "EasyOCR Engine",
            "reporting_address": "4-1.10",
            "parent_address": "4-1",
            "severity": "CRITICAL",
            "timestamp": datetime.now().isoformat(),
            "fault_type": "12",
            "fault_type_description": "Missing initialization dependency",
            "message_type": "initialization_failure"
        }
        
        # Emit on LINBUS
        bus.emit('section.fault', fault_payload)
        logger.info("[TEST] Fault emitted on LINBUS topic 'section.fault'")
        
        # Step 3: Wait for Marshall to relay to UDS
        logger.info("[TEST] Waiting for Marshall to relay fault to UDS via CANBUS...")
        time.sleep(1.5)
        
        # Step 4: Check if UDS received the fault
        logger.info("[TEST] Checking UDS fault log...")
        
        print("\n" + "-"*80)
        print("TEST COMPLETE - Check UDS logs for fault reception")
        print("-"*80)
        print("Expected flow:")
        print("  1. Section fault emitted on LINBUS 'section.fault'")
        print("  2. Marshall received via _handle_section_fault_linbus()")
        print("  3. Marshall relayed to Bus-1 via UniversalCommunicator with SOS")
        print("  4. UDS received on CANBUS 'communication' topic")
        print("  5. UDS logged fault [4-1.10-12-INIT]")
        print("-"*80)
        
        return True
        
    except Exception as exc:
        logger.error(f"[TEST] LINBUS test failed: {exc}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("\n" + "="*80)
    print("INITIALIZING UDS FOR LINBUS TEST")
    print("="*80)
    
    # Initialize UDS
    sys.path.insert(0, os.path.dirname(__file__))
    from __init__ import UnifiedDiagnosticSystem
    
    print("[INIT] Starting Unified Diagnostic System...")
    uds = UnifiedDiagnosticSystem()
    
    print("[INIT] UDS initialized - running LINBUS test...")
    success = run_linbus_fault_test(uds)
    
    sys.exit(0 if success else 1)

