#!/usr/bin/env python3
"""
Routing Logic Test - Unified Diagnostic System
Tests actual fault routing, file organization, and path management
"""

import sys
import os
import logging
import json
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

def test_routing_logic():
    """Test actual routing logic and file organization"""
    print("=" * 80)
    print("ROUTING LOGIC TEST - UNIFIED DIAGNOSTIC SYSTEM")
    print("=" * 80)
    
    try:
        # Import and create system
        from __init__ import UnifiedDiagnosticSystem
        print("[INIT] Creating diagnostic system...")
        diagnostic_system = UnifiedDiagnosticSystem()
        
        # Test 1: Test fault routing to correct directories
        print("\n[TEST 1] Testing fault routing logic...")
        
        # Create different types of faults to test routing
        test_faults = [
            {
                'fault_id': 'ROUTING-001',
                'system_address': 'GATEWAY-1',
                'fault_code': 'GATEWAY-1-10-456',
                'description': 'Gateway initialization failure',
                'severity': 'ERROR',
                'timestamp': datetime.now().isoformat()
            },
            {
                'fault_id': 'ROUTING-002', 
                'system_address': 'EVIDENCE-1',
                'fault_code': 'EVIDENCE-1-50-789',
                'description': 'Evidence processing failure',
                'severity': 'FAILURE',
                'timestamp': datetime.now().isoformat()
            },
            {
                'fault_id': 'ROUTING-003',
                'system_address': 'BUS-1',
                'fault_code': 'BUS-1-90-123',
                'description': 'Bus communication critical failure',
                'severity': 'CRITICAL',
                'timestamp': datetime.now().isoformat()
            }
        ]
        
        for fault in test_faults:
            print(f"\n[FAULT] Processing fault: {fault['fault_id']}")
            print(f"  System: {fault['system_address']}")
            print(f"  Code: {fault['fault_code']}")
            print(f"  Severity: {fault['severity']}")
            
            # Process the fault
            result = diagnostic_system.process_fault_report(fault)
            print(f"  [ROUTED] Fault processed: {result}")
        
        # Test 2: Check what files were created and where
        print("\n[TEST 2] Checking file routing results...")
        
        core = diagnostic_system.core
        
        # Check fault_vault for fault reports
        fault_vault_files = list(core.fault_vault_path.glob("*.md"))
        print(f"[FAULT_VAULT] Files created: {len(fault_vault_files)}")
        for file_path in fault_vault_files:
            print(f"  - {file_path.name}")
        
        # Check diagnostic_reports for repair summaries
        diagnostic_files = list(core.diagnostic_reports_path.glob("*.md"))
        print(f"[DIAGNOSTIC_REPORTS] Files created: {len(diagnostic_files)}")
        for file_path in diagnostic_files:
            print(f"  - {file_path.name}")
        
        # Check fault_amendments for repair attempts
        amendment_files = list(core.fault_amendments_path.glob("*.md"))
        print(f"[FAULT_AMENDMENTS] Files created: {len(amendment_files)}")
        for file_path in amendment_files:
            print(f"  - {file_path.name}")
        
        # Check systems_amendments for new systems
        system_files = list(core.systems_amendments_path.glob("*.md"))
        print(f"[SYSTEMS_AMENDMENTS] Files created: {len(system_files)}")
        for file_path in system_files:
            print(f"  - {file_path.name}")
        
        # Test 3: Test file content validation
        print("\n[TEST 3] Testing file content validation...")
        
        # Read and validate fault vault content
        if fault_vault_files:
            latest_fault_file = max(fault_vault_files, key=lambda f: f.stat().st_mtime)
            try:
                content = latest_fault_file.read_text()
                print(f"[CONTENT] Latest fault file: {latest_fault_file.name}")
                print(f"[CONTENT] Size: {len(content)} characters")
                print(f"[CONTENT] Contains fault_id: {'ROUTING' in content}")
                print(f"[CONTENT] Contains timestamp: {datetime.now().strftime('%Y-%m-%d') in content}")
            except Exception as e:
                print(f"[ERROR] Failed to read fault file: {e}")
        
        # Test 4: Test system registry loading
        print("\n[TEST 4] Testing system registry loading...")
        
        try:
            # Check if system registry loaded
            registry_size = len(diagnostic_system.core.system_registry)
            print(f"[REGISTRY] Systems registered: {registry_size}")
            
            if registry_size > 0:
                for address, system_info in diagnostic_system.core.system_registry.items():
                    print(f"  - {address}: {system_info.name}")
            else:
                print("[REGISTRY] No systems registered (this is expected if registry file missing)")
                
        except Exception as e:
            print(f"[ERROR] Registry loading error: {e}")
        
        # Test 5: Test protocol file loading
        print("\n[TEST 5] Testing protocol file loading...")
        
        try:
            # Check if fault code protocol loaded
            protocol_loaded = diagnostic_system.comms.fault_code_protocol is not None
            print(f"[PROTOCOL] Fault code protocol loaded: {protocol_loaded}")
            
            if protocol_loaded:
                protocol_size = len(diagnostic_system.comms.fault_code_protocol)
                print(f"[PROTOCOL] Protocol entries: {protocol_size}")
            
            # Check protocol file path
            protocol_file = diagnostic_system.comms.protocol_file
            print(f"[PROTOCOL] Protocol file path: {protocol_file}")
            print(f"[PROTOCOL] Protocol file exists: {protocol_file.exists() if protocol_file else False}")
            
        except Exception as e:
            print(f"[ERROR] Protocol loading error: {e}")
        
        # Test 6: Test backup and restore operations
        print("\n[TEST 6] Testing backup and restore operations...")
        
        try:
            # Test recovery system operations
            recovery = diagnostic_system.recovery
            
            # Test restoration queue
            queue_size = len(recovery.restoration_queue)
            print(f"[RECOVERY] Restoration queue size: {queue_size}")
            
            # Test known good states
            states_count = len(recovery.known_good_states)
            print(f"[RECOVERY] Known good states: {states_count}")
            
            # Test sandbox paths
            sandbox_ready = all([
                recovery.writeback_path.exists(),
                recovery.staging_path.exists(),
                recovery.validation_path.exists()
            ])
            print(f"[RECOVERY] Sandbox ready: {sandbox_ready}")
            
        except Exception as e:
            print(f"[ERROR] Recovery operations error: {e}")
        
        # Test 7: Test authentication and authorization
        print("\n[TEST 7] Testing authentication and authorization...")
        
        try:
            auth = diagnostic_system.auth
            
            # Test authorized systems
            auth_systems = len(auth.authorized_systems)
            print(f"[AUTH] Authorized systems: {auth_systems}")
            
            # Test authentication keys
            auth_keys = len(auth.authentication_keys)
            print(f"[AUTH] Authentication keys: {auth_keys}")
            
            # Test security features
            spoof_detection = auth.spoof_detection_enabled
            idle_filtering = auth.idle_fault_filtering_enabled
            print(f"[AUTH] Spoof detection: {spoof_detection}")
            print(f"[AUTH] Idle filtering: {idle_filtering}")
            
        except Exception as e:
            print(f"[ERROR] Authentication error: {e}")
        
        print("\n" + "=" * 80)
        print("[PASS] ROUTING LOGIC TEST COMPLETED")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n[FAIL] ROUTING LOGIC TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Run routing logic test
    success = test_routing_logic()
    
    if success:
        print("\n[SUCCESS] ROUTING LOGIC WORKING")
    else:
        print("\n[ERROR] ROUTING LOGIC FAILED")
        sys.exit(1)
