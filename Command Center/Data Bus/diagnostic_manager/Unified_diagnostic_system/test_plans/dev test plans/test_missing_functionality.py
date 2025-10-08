#!/usr/bin/env python3
"""
Missing Functionality Test - Unified Diagnostic System
Tests what functionality is missing from the modular system vs original
"""

import sys
import os
import logging
from pathlib import Path

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

def test_missing_functionality():
    """Test what functionality is missing from modular system"""
    print("=" * 80)
    print("MISSING FUNCTIONALITY ANALYSIS - UNIFIED DIAGNOSTIC SYSTEM")
    print("=" * 80)
    
    try:
        # Import and create system
        from __init__ import UnifiedDiagnosticSystem
        print("[INIT] Creating diagnostic system...")
        diagnostic_system = UnifiedDiagnosticSystem()
        
        # Test 1: Check system registry loading
        print("\n[TEST 1] System Registry Loading...")
        registry_size = len(diagnostic_system.core.system_registry)
        print(f"[REGISTRY] Systems loaded: {registry_size}")
        
        if registry_size == 0:
            print("[MISSING] System registry not loading properly")
            print("[EXPECTED] Should load 27-29 systems from system_registry.json")
        
        # Test 2: Check test plan loading and execution
        print("\n[TEST 2] Test Plan Loading and Execution...")
        
        # Check if test plans exist
        test_plans_path = diagnostic_system.core.test_plans_main_path
        print(f"[TEST_PLANS] Path: {test_plans_path}")
        print(f"[TEST_PLANS] Exists: {test_plans_path.exists()}")
        
        if test_plans_path.exists():
            test_plan_files = list(test_plans_path.glob("**/*.json"))
            print(f"[TEST_PLANS] Files found: {len(test_plan_files)}")
            
            # Check if we can load a test plan
            if test_plan_files:
                try:
                    import json
                    with open(test_plan_files[0], 'r') as f:
                        test_plan = json.load(f)
                    print(f"[TEST_PLANS] Sample plan loaded: {test_plan.get('test_name', 'UNKNOWN')}")
                    print(f"[TEST_PLANS] Test vectors: {len(test_plan.get('test_vectors', []))}")
                except Exception as e:
                    print(f"[ERROR] Failed to load test plan: {e}")
        else:
            print("[MISSING] Test plans directory not found")
        
        # Test 3: Check payload creation and validation
        print("\n[TEST 3] Payload Creation and Validation...")
        
        # Check if payload creation methods exist
        has_payload_creation = hasattr(diagnostic_system, 'create_diagnostic_payload')
        print(f"[PAYLOAD] Create method exists: {has_payload_creation}")
        
        if has_payload_creation:
            try:
                # Try to create a test payload
                test_payload = diagnostic_system.create_diagnostic_payload(
                    operation='test_operation',
                    data={'test': True}
                )
                print(f"[PAYLOAD] Created successfully: {type(test_payload)}")
                print(f"[PAYLOAD] Size: {test_payload.get('size_bytes', 0)} bytes")
            except Exception as e:
                print(f"[ERROR] Payload creation failed: {e}")
        else:
            print("[MISSING] Payload creation functionality")
        
        # Test 4: Check test execution capabilities
        print("\n[TEST 4] Test Execution Capabilities...")
        
        # Check if test execution methods exist
        has_test_execution = hasattr(diagnostic_system, 'execute_test_plan')
        print(f"[EXECUTION] Execute test plan method: {has_test_execution}")
        
        has_comprehensive_test = hasattr(diagnostic_system, 'run_comprehensive_test_suite')
        print(f"[EXECUTION] Comprehensive test suite: {has_comprehensive_test}")
        
        if not has_test_execution and not has_comprehensive_test:
            print("[MISSING] Test execution functionality")
        
        # Test 5: Check rollcall and system communication
        print("\n[TEST 5] System Communication and Rollcall...")
        
        # Check if rollcall methods exist
        has_rollcall = hasattr(diagnostic_system, 'transmit_rollcall')
        print(f"[ROLLCALL] Transmit rollcall method: {has_rollcall}")
        
        has_radio_check = hasattr(diagnostic_system, 'transmit_radio_check')
        print(f"[COMMS] Radio check method: {has_radio_check}")
        
        if not has_rollcall:
            print("[MISSING] Rollcall functionality")
        
        # Test 6: Check protocol monitoring and auto-registration
        print("\n[TEST 6] Protocol Monitoring and Auto-Registration...")
        
        has_protocol_monitoring = hasattr(diagnostic_system, 'start_protocol_monitoring_engine')
        print(f"[PROTOCOL] Protocol monitoring: {has_protocol_monitoring}")
        
        has_auto_registration = hasattr(diagnostic_system, 'force_mandatory_auto_registration')
        print(f"[AUTO_REG] Auto-registration: {has_auto_registration}")
        
        if not has_protocol_monitoring:
            print("[MISSING] Protocol monitoring functionality")
        
        # Test 7: Check fault code enforcement
        print("\n[TEST 7] Fault Code Enforcement...")
        
        has_fault_enforcement = hasattr(diagnostic_system, 'start_fault_code_enforcement')
        print(f"[ENFORCEMENT] Fault code enforcement: {has_fault_enforcement}")
        
        has_universal_language = hasattr(diagnostic_system, 'enforce_universal_language')
        print(f"[ENFORCEMENT] Universal language enforcement: {has_universal_language}")
        
        if not has_fault_enforcement:
            print("[MISSING] Fault code enforcement functionality")
        
        # Test 8: Check oligarch authority and punishment
        print("\n[TEST 8] Oligarch Authority and Punishment...")
        
        has_oligarch = hasattr(diagnostic_system, 'exercise_oligarch_authority')
        print(f"[OLIGARCH] Oligarch authority: {has_oligarch}")
        
        has_system_isolation = hasattr(diagnostic_system, 'isolate_system')
        print(f"[OLIGARCH] System isolation: {has_system_isolation}")
        
        has_forced_shutdown = hasattr(diagnostic_system, 'force_system_shutdown')
        print(f"[OLIGARCH] Forced shutdown: {has_forced_shutdown}")
        
        if not has_oligarch:
            print("[MISSING] Oligarch authority functionality")
        
        # Test 9: Check live operational monitoring
        print("\n[TEST 9] Live Operational Monitoring...")
        
        has_live_monitoring = hasattr(diagnostic_system, 'start_live_operational_monitoring')
        print(f"[MONITORING] Live operational monitoring: {has_live_monitoring}")
        
        has_operational_flow = hasattr(diagnostic_system, 'enforce_operational_flow_standards')
        print(f"[MONITORING] Operational flow enforcement: {has_operational_flow}")
        
        if not has_live_monitoring:
            print("[MISSING] Live operational monitoring functionality")
        
        # Test 10: Check root cause analysis
        print("\n[TEST 10] Root Cause Analysis...")
        
        has_root_cause = hasattr(diagnostic_system, 'perform_root_cause_analysis')
        print(f"[RCA] Root cause analysis: {has_root_cause}")
        
        has_cascading_detection = hasattr(diagnostic_system, 'detect_cascading_failures')
        print(f"[RCA] Cascading failure detection: {has_cascading_detection}")
        
        if not has_root_cause:
            print("[MISSING] Root cause analysis functionality")
        
        # Summary
        print("\n" + "=" * 80)
        print("MISSING FUNCTIONALITY SUMMARY")
        print("=" * 80)
        
        missing_features = []
        if registry_size == 0:
            missing_features.append("System Registry Loading")
        if not has_payload_creation:
            missing_features.append("Payload Creation")
        if not has_test_execution:
            missing_features.append("Test Execution")
        if not has_rollcall:
            missing_features.append("Rollcall Communication")
        if not has_protocol_monitoring:
            missing_features.append("Protocol Monitoring")
        if not has_fault_enforcement:
            missing_features.append("Fault Code Enforcement")
        if not has_oligarch:
            missing_features.append("Oligarch Authority")
        if not has_live_monitoring:
            missing_features.append("Live Operational Monitoring")
        if not has_root_cause:
            missing_features.append("Root Cause Analysis")
        
        print(f"[MISSING] Total missing features: {len(missing_features)}")
        for feature in missing_features:
            print(f"  - {feature}")
        
        if len(missing_features) > 0:
            print(f"\n[CONCLUSION] {len(missing_features)} major features missing from modular system")
            print("[ACTION REQUIRED] Need to port functionality from unified_diagnostic_system.py")
            return False
        else:
            print("\n[CONCLUSION] All major features present in modular system")
            return True
        
    except Exception as e:
        print(f"\n[FAIL] MISSING FUNCTIONALITY TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Run missing functionality test
    success = test_missing_functionality()
    
    if not success:
        print("\n[ERROR] MAJOR FUNCTIONALITY MISSING - SYSTEM INCOMPLETE")
        sys.exit(1)
    else:
        print("\n[SUCCESS] ALL FUNCTIONALITY PRESENT")
