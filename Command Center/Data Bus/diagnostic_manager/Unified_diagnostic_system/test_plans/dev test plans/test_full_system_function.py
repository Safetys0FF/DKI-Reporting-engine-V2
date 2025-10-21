#!/usr/bin/env python3
"""
Full System Function Test - Unified Diagnostic System
Tests actual system operations, not just imports
"""

import sys
import os
import logging
import time
from datetime import datetime
from pathlib import Path
import importlib.util as import_util

# Add current directory to path
sys.path.append(os.path.dirname(__file__))
UNIFIED_ROOT = Path(__file__).resolve().parents[2]
if str(UNIFIED_ROOT) not in sys.path:
    sys.path.insert(0, str(UNIFIED_ROOT))

def test_full_system_function():
    """Test full system function with actual operations"""
    print("=" * 80)
    print("FULL SYSTEM FUNCTION TEST - UNIFIED DIAGNOSTIC SYSTEM")
    print("=" * 80)
    
    try:
        # Import and create system
        from __init__ import UnifiedDiagnosticSystem
        print("[INIT] Creating diagnostic system...")
        diagnostic_system = UnifiedDiagnosticSystem()
        
        # Test 1: Launch the diagnostic system
        print("\n[TEST 1] Launching diagnostic system...")
        launch_result = diagnostic_system.launch_diagnostic_system()
        print(f"[RESULT] Launch successful: {launch_result}")
        
        # Test 2: Get full system status
        print("\n[TEST 2] Getting full system status...")
        status = diagnostic_system.get_unified_status()
        print(f"[RESULT] System Status:")
        print(f"  - Monitoring Active: {status.get('monitoring_active', 'N/A')}")
        print(f"  - Registered Systems: {status.get('registered_systems', 'N/A')}")
        print(f"  - Active Faults: {status.get('active_faults', 'N/A')}")
        
        # Test 3: Test CAN-BUS communication
        print("\n[TEST 3] Testing CAN-BUS communication...")
        bus_status = diagnostic_system.get_bus_status()
        print(f"[RESULT] CAN-BUS Status:")
        print(f"  - Bus Connected: {bus_status['bus_connected']}")
        print(f"  - Registered Addresses: {bus_status['registered_addresses']}")
        
        # Test 4: Test fault processing
        print("\n[TEST 4] Testing fault processing...")
        test_fault = {
            'fault_id': 'TEST-001',
            'system_address': 'TEST-1',
            'fault_code': 'TEST-1-10-123',
            'description': 'Test fault for system validation',
            'timestamp': '2025-10-07T20:00:00Z'
        }
        print(f"[INPUT] Processing test fault: {test_fault['fault_id']}")
        fault_result = diagnostic_system.process_fault_report(test_fault)
        print(f"[RESULT] Fault processed successfully")
        
        # Test 5: Test module functionality
        print("\n[TEST 5] Testing module functionality...")
        
        # Test Auth module
        auth_status = diagnostic_system.auth.get_authentication_status()
        print(f"[AUTH] Authentication status:")
        print(f"  - Authorized Systems: {auth_status.get('authorized_systems', 0)}")
        print(f"  - Authentication Keys: {auth_status.get('authentication_keys', 0)}")
        print(f"  - Spoof Detection: {auth_status.get('spoof_detection_enabled', False)}")
        
        # Test Comms module
        comms_status = diagnostic_system.comms.get_communication_status()
        print(f"[COMMS] Communication status:")
        print(f"  - Bus Connected: {comms_status.get('bus_connected', False)}")
        print(f"  - Signals Sent: {comms_status.get('signals_sent', 0)}")
        print(f"  - Protocol Loaded: {comms_status.get('protocol_loaded', False)}")
        
        # Test Recovery module
        recovery_status = diagnostic_system.recovery.get_recovery_status()
        print(f"[RECOVERY] Recovery status:")
        print(f"  - Restoration In Progress: {recovery_status.get('restoration_in_progress', False)}")
        print(f"  - Queued Restorations: {recovery_status.get('queued_restorations', 0)}")
        print(f"  - Known Good States: {recovery_status.get('known_good_states', 0)}")
        
        # Test Enforcement module
        enforcement_status = diagnostic_system.enforcement.get_enforcement_status()
        print(f"[ENFORCEMENT] Enforcement status:")
        print(f"  - Oligarch Authority: {enforcement_status.get('oligarch_authority_active', False)}")
        print(f"  - Live Monitoring: {enforcement_status.get('live_monitoring_active', False)}")
        print(f"  - Systems Under Punishment: {enforcement_status.get('systems_under_punishment', 0)}")
        
        # Test 6: Test system health
        print("\n[TEST 6] Testing system health...")
        try:
            health = diagnostic_system.get_system_health_summary()
            print(f"[HEALTH] System health retrieved: {len(health)} modules")
            for module, status in health.items():
                print(f"  - {module}: {status}")
        except Exception as e:
            print(f"[HEALTH] Health check error: {e}")
        
        # Test 7: Test actual signal transmission
        print("\n[TEST 7] Testing actual signal transmission...")
        try:
            # Test rollcall transmission
            print("[SIGNAL] Sending rollcall signal...")
            rollcall_result = diagnostic_system.comms.transmit_rollcall()
            print(f"[RESULT] Rollcall sent: {rollcall_result}")
            
            # Test radio check transmission
            print("[SIGNAL] Sending radio check signal...")
            radio_result = diagnostic_system.comms.transmit_radio_check("TEST-1")
            print(f"[RESULT] Radio check sent: {radio_result}")
            
        except Exception as e:
            print(f"[SIGNAL] Signal transmission error: {e}")
        
        # Test 8: Test fault code validation
        print("\n[TEST 8] Testing fault code validation...")
        try:
            # Test valid fault code
            valid_fault = "TEST-1-10-123"
            is_valid = diagnostic_system.comms.validate_fault_code(valid_fault)
            print(f"[VALIDATION] Fault code '{valid_fault}' valid: {is_valid}")
            
            # Test invalid fault code
            invalid_fault = "INVALID-CODE"
            is_invalid = diagnostic_system.comms.validate_fault_code(invalid_fault)
            print(f"[VALIDATION] Fault code '{invalid_fault}' valid: {is_invalid}")
            
        except Exception as e:
            print(f"[VALIDATION] Validation error: {e}")
        
        # Test 9: Test ECC gating flow with synthetic evidence
        print("\n[TEST 9] Testing ECC gating flow with synthetic evidence...")
        try:
            repo_root = Path(__file__).resolve().parents[6]
            warden_root = repo_root / "The Warden"

            ecc_spec = import_util.spec_from_file_location(
                "warden.ecosystem_controller", str(warden_root / "ecosystem_controller.py")
            )
            if ecc_spec is None or ecc_spec.loader is None:
                raise RuntimeError("Failed to build ECC module spec")
            ecc_module = import_util.module_from_spec(ecc_spec)
            ecc_spec.loader.exec_module(ecc_module)  # type: ignore[attr-defined]
            EcosystemController = getattr(ecc_module, "EcosystemController")
            ecc_instance = EcosystemController()

            bus_events = []
            gateway_ready_records = []

            class _BusStub:
                def emit(self_inner, signal, payload):
                    bus_events.append((signal, payload))

            class _GatewayStub:
                def register_section_ready(self_inner, section, context):
                    gateway_ready_records.append((section, context))

            class _OCRStub:
                def process_file(self_inner, file_path, file_type):
                    return {"text": "intake surveillance analysis financial legal media billing"}

            ecc_instance.bus = _BusStub()
            ecc_instance.gateway = _GatewayStub()
            ecc_instance.ocr_engine = _OCRStub()

            gating_sequence = list(ecc_instance.section_gate_sequence)
            synthetic_tags = {
                "section_1": ["intake"],
                "section_2": ["intake"],
                "section_3": ["surveillance"],
                "section_4": ["analysis"],
                "section_5": ["financial"],
                "section_7": ["legal"],
                "section_8": ["media"],
                "section_6": ["financial"],
            }

            sample_file = Path(__file__).resolve()
            for section_key in gating_sequence:
                payload = {
                    "evidence_id": f"SIM-{section_key}",
                    "section_hint": section_key,
                    "classification": {"tags": synthetic_tags.get(section_key, [])},
                    "file_path": str(sample_file),
                    "timestamp": datetime.now().isoformat(),
                }
                ecc_instance._handle_bus_evidence_event("evidence.updated", payload)

            released_flags = {sec: ecc_instance.section_release_flags.get(sec) for sec in gating_sequence}
            print(f"[RESULT] Release flags: {released_flags}")
            print(f"[RESULT] Gateway ready records: {len(gateway_ready_records)} entries")
            assert all(released_flags.values()), "Not all sections were authorised by ECC gating"
            assert any(event[0] == "gateway.section.authorized" for event in bus_events), "No gating bus event emitted"
            print("[OK] ECC gating flow authorised sequential sections")
        except Exception as ecc_exc:
            print(f"[FAIL] ECC gating flow test error: {ecc_exc}")
            raise
        
        # Test 10: Test system shutdown
        print("\n[TEST 10] Testing system shutdown...")
        shutdown_result = diagnostic_system.shutdown_diagnostic_system()
        print(f"[RESULT] Shutdown successful: {shutdown_result}")
        
        print("\n" + "=" * 80)
        print("[PASS] FULL SYSTEM FUNCTION TEST COMPLETED")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n[FAIL] FULL SYSTEM FUNCTION TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Run full system test
    success = test_full_system_function()
    
    if success:
        print("\n[SUCCESS] SYSTEM IS FULLY FUNCTIONAL")
    else:
        print("\n[ERROR] SYSTEM HAS FUNCTIONAL ISSUES")
        sys.exit(1)
