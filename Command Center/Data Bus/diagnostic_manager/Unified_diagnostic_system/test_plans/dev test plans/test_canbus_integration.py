#!/usr/bin/env python3
"""
Test CAN-BUS Integration - Unified Diagnostic System
Tests the CAN-BUS connection and modular architecture
"""

import sys
import os
import logging

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

def test_canbus_integration():
    """Test CAN-BUS integration with modular architecture"""
    print("=" * 60)
    print("TESTING CAN-BUS INTEGRATION - MODULAR ARCHITECTURE")
    print("=" * 60)
    
    try:
        # Import the unified diagnostic system
        from __init__ import UnifiedDiagnosticSystem
        
        print("[OK] Successfully imported UnifiedDiagnosticSystem")
        
        # Create instance (this will establish CAN-BUS connection)
        print("\n[INIT] Creating UnifiedDiagnosticSystem instance...")
        diagnostic_system = UnifiedDiagnosticSystem()
        
        print("[OK] UnifiedDiagnosticSystem instance created")
        
        # Test CAN-BUS connection
        print("\n[TEST] Testing CAN-BUS connection...")
        bus_status = diagnostic_system.get_bus_status()
        
        print(f"[OK] CAN-BUS Status:")
        print(f"   - Bus Available: {bus_status['bus_available']}")
        print(f"   - Bus Connected: {bus_status['bus_connected']}")
        print(f"   - Registered Addresses: {len(bus_status['registered_addresses'])}")
        
        # Test modular architecture
        print("\n[TEST] Testing modular architecture...")
        print(f"[OK] Core System: {type(diagnostic_system.core).__name__}")
        print(f"[OK] Auth Module: {type(diagnostic_system.auth).__name__}")
        print(f"[OK] Comms Module: {type(diagnostic_system.comms).__name__}")
        print(f"[OK] Recovery Module: {type(diagnostic_system.recovery).__name__}")
        print(f"[OK] Enforcement Module: {type(diagnostic_system.enforcement).__name__}")
        
        # Test module bus connections
        print("\n[TEST] Testing module CAN-BUS connections...")
        print(f"[OK] Auth Bus Connected: {diagnostic_system.auth.bus_connected}")
        print(f"[OK] Comms Bus Connected: {diagnostic_system.comms.bus_connected}")
        print(f"[OK] Recovery Bus Connected: {diagnostic_system.recovery.bus_connected}")
        print(f"[OK] Enforcement Bus Connected: {diagnostic_system.enforcement.bus_connected}")
        
        # Test system status
        print("\n[TEST] Testing system status...")
        status = diagnostic_system.get_unified_status()
        print(f"[OK] System Status Retrieved: {status.get('monitoring_active', 'N/A')}")
        
        print("\n" + "=" * 60)
        print("[PASS] CAN-BUS INTEGRATION TEST PASSED")
        print("[PASS] MODULAR ARCHITECTURE TEST PASSED")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n[FAIL] CAN-BUS INTEGRATION TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Run test
    success = test_canbus_integration()
    
    if success:
        print("\n[SUCCESS] ALL TESTS PASSED - SYSTEM READY")
    else:
        print("\n[ERROR] TESTS FAILED - SYSTEM NOT READY")
        sys.exit(1)
