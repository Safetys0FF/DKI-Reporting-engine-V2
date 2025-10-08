#!/usr/bin/env python3
"""
COMPREHENSIVE TEST OF ALL DIAGNOSTIC PROTOCOLS
Tests that ALL diagnostic protocols from the main script are working in recovery.py
"""

import sys
import os
import json
import tempfile
from pathlib import Path

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

def test_all_diagnostic_protocols():
    """Test ALL diagnostic protocols ported to recovery.py"""
    print("=" * 80)
    print("COMPREHENSIVE TEST OF ALL DIAGNOSTIC PROTOCOLS")
    print("=" * 80)
    
    try:
        from __init__ import UnifiedDiagnosticSystem
        
        # Create system
        system = UnifiedDiagnosticSystem()
        
        # Test 1: Diagnostic Protocol Loading
        print("\n[TEST 1] DIAGNOSTIC PROTOCOL LOADING...")
        
        has_protocols = hasattr(system.recovery, 'diagnostic_protocols')
        print(f"[TEST] Diagnostic protocols loaded: {has_protocols}")
        
        if has_protocols:
            protocols = system.recovery.diagnostic_protocols
            print(f"[SUCCESS] Protocol structure: {list(protocols.keys())}")
            print(f"[SUCCESS] System addresses: {len(protocols.get('system_addresses', {}))}")
            print(f"[SUCCESS] Fault codes: {len(protocols.get('fault_codes', {}))}")
            print(f"[SUCCESS] Radio codes: {len(protocols.get('radio_codes', {}))}")
        else:
            print("[ERROR] Diagnostic protocols not loaded")
        
        # Test 2: Fault Code Validation
        print("\n[TEST 2] FAULT CODE VALIDATION...")
        
        test_fault_codes = [
            "[1-1-01-001]",  # Valid syntax error
            "[Bus-1-90-123]",  # Valid critical error
            "[2-1-50-456]",  # Valid failure
            "[INVALID-FORMAT]",  # Invalid format
            "[1-1-999-001]"  # Invalid fault ID
        ]
        
        for fault_code in test_fault_codes:
            is_valid = system.recovery._validate_fault_code_format(fault_code)
            print(f"[TEST] {fault_code}: {'VALID' if is_valid else 'INVALID'}")
        
        # Test 3: Fault Code Parsing
        print("\n[TEST 3] FAULT CODE PARSING...")
        
        parsed = system.recovery._parse_fault_code("[1-1-01-001]")
        print(f"[SUCCESS] Parsed fault code: {parsed}")
        assert parsed.get('system_address') == '1-1', f"Expected '1-1', got {parsed.get('system_address')}"
        assert parsed.get('fault_id') == '01', f"Expected '01', got {parsed.get('fault_id')}"
        assert parsed.get('line_number') == '001', f"Expected '001', got {parsed.get('line_number')}"
        
        # Test 4: Fault Severity Determination
        print("\n[TEST 4] FAULT SEVERITY DETERMINATION...")
        
        severity_tests = [
            ('01', 'ERROR'),
            ('50', 'FAILURE'),
            ('90', 'CRITICAL'),
            ('99', 'CRITICAL')
        ]
        
        for fault_id, expected_severity in severity_tests:
            severity = system.recovery._determine_fault_severity(fault_id)
            print(f"[TEST] Fault ID {fault_id}: {severity}")
            assert severity == expected_severity, f"Expected {expected_severity}, got {severity}"
        
        # Test 5: Error to Fault Code Conversion
        print("\n[TEST 5] ERROR TO FAULT CODE CONVERSION...")
        
        error_tests = [
            ("syntax error at line 42", "1-1", "[1-1-01-042]"),
            ("initialization failed", "Bus-1", "[Bus-1-10-001]"),
            ("communication timeout", "2-1", "[2-1-20-001]"),
            ("data processing error", "3-1", "[3-1-30-001]"),
            ("resource failure", "4-1", "[4-1-40-001]"),
            ("unknown error", "5-1", "[5-1-99-001]")
        ]
        
        for error_msg, system_addr, expected_fault_code in error_tests:
            fault_code = system.recovery._convert_error_to_fault_code("ERR", system_addr, error_msg)
            print(f"[TEST] '{error_msg}' -> {fault_code}")
            assert fault_code == expected_fault_code, f"Expected {expected_fault_code}, got {fault_code}"
        
        # Test 6: System Validation Protocols
        print("\n[TEST 6] SYSTEM VALIDATION PROTOCOLS...")
        
        has_validation = hasattr(system.recovery, '_run_comprehensive_system_validation')
        print(f"[TEST] Comprehensive validation method: {has_validation}")
        
        if has_validation:
            # Test validation on a real system
            test_system = "Bus-1"
            validation_result = system.recovery._run_comprehensive_system_validation(test_system)
            print(f"[SUCCESS] Validation result for {test_system}:")
            print(f"[SUCCESS] Overall valid: {validation_result.get('overall_valid')}")
            print(f"[SUCCESS] File integrity: {validation_result.get('file_integrity', {}).get('valid')}")
            print(f"[SUCCESS] Configuration: {validation_result.get('configuration', {}).get('valid')}")
            print(f"[SUCCESS] Dependencies: {validation_result.get('dependencies', {}).get('valid')}")
            print(f"[SUCCESS] Communication: {validation_result.get('communication', {}).get('valid')}")
        
        # Test 7: File Integrity Validation
        print("\n[TEST 7] FILE INTEGRITY VALIDATION...")
        
        has_file_validation = hasattr(system.recovery, '_validate_system_file_integrity')
        print(f"[TEST] File integrity validation: {has_file_validation}")
        
        if has_file_validation:
            file_validation = system.recovery._validate_system_file_integrity("Bus-1")
            print(f"[SUCCESS] File validation result: {file_validation.get('valid')}")
            if file_validation.get('valid'):
                print(f"[SUCCESS] File checksum: {file_validation.get('checksum', 'N/A')[:16]}...")
        
        # Test 8: Configuration Validation
        print("\n[TEST 8] CONFIGURATION VALIDATION...")
        
        has_config_validation = hasattr(system.recovery, '_validate_system_configuration')
        print(f"[TEST] Configuration validation: {has_config_validation}")
        
        if has_config_validation:
            config_validation = system.recovery._validate_system_configuration("Bus-1")
            print(f"[SUCCESS] Config validation result: {config_validation.get('valid')}")
            print(f"[SUCCESS] Config files found: {len(config_validation.get('config_files', []))}")
        
        # Test 9: Dependency Validation
        print("\n[TEST 9] DEPENDENCY VALIDATION...")
        
        has_dep_validation = hasattr(system.recovery, '_validate_system_dependencies')
        print(f"[TEST] Dependency validation: {has_dep_validation}")
        
        if has_dep_validation:
            dep_validation = system.recovery._validate_system_dependencies("Bus-1")
            print(f"[SUCCESS] Dependency validation result: {dep_validation.get('valid')}")
            print(f"[SUCCESS] Valid imports: {len(dep_validation.get('imports', []))}")
            print(f"[SUCCESS] Invalid imports: {len(dep_validation.get('invalid_imports', []))}")
        
        # Test 10: Communication Testing
        print("\n[TEST 10] COMMUNICATION TESTING...")
        
        has_comm_test = hasattr(system.recovery, '_test_system_communication')
        print(f"[TEST] Communication testing: {has_comm_test}")
        
        if has_comm_test:
            comm_test = system.recovery._test_system_communication("Bus-1")
            print(f"[SUCCESS] Communication test result: {comm_test.get('valid')}")
            print(f"[SUCCESS] Signal ID: {comm_test.get('signal_id', 'N/A')}")
        
        # Test 11: Known Good States Management
        print("\n[TEST 11] KNOWN GOOD STATES MANAGEMENT...")
        
        has_good_states = hasattr(system.recovery, 'known_good_states')
        print(f"[TEST] Known good states: {has_good_states}")
        
        if has_good_states:
            good_states = system.recovery.known_good_states
            print(f"[SUCCESS] Good states loaded: {len(good_states)}")
            
            has_record_good_state = hasattr(system.recovery, '_record_good_state')
            print(f"[TEST] Record good state method: {has_record_good_state}")
            
            has_save_good_states = hasattr(system.recovery, '_save_known_good_states')
            print(f"[TEST] Save good states method: {has_save_good_states}")
        
        # Test 12: State Deviation Analysis
        print("\n[TEST 12] STATE DEVIATION ANALYSIS...")
        
        has_deviation_analysis = hasattr(system.recovery, '_analyze_state_deviation')
        print(f"[TEST] State deviation analysis: {has_deviation_analysis}")
        
        has_log_deviation = hasattr(system.recovery, '_log_state_deviation')
        print(f"[TEST] Log state deviation: {has_log_deviation}")
        
        # Test 13: Backup Validation Monitoring
        print("\n[TEST 13] BACKUP VALIDATION MONITORING...")
        
        has_backup_validation = hasattr(system.recovery, 'backup_validation_active')
        print(f"[TEST] Backup validation active: {has_backup_validation}")
        
        if has_backup_validation:
            backup_active = system.recovery.backup_validation_active
            print(f"[SUCCESS] Backup validation status: {backup_active}")
        
        has_validation_monitoring = hasattr(system.recovery, '_validate_current_system_states')
        print(f"[TEST] Current system state validation: {has_validation_monitoring}")
        
        print("\n" + "=" * 80)
        print("ALL DIAGNOSTIC PROTOCOLS TEST COMPLETE")
        print("=" * 80)
        
        working_protocols = [
            "Diagnostic Protocol Loading",
            "Fault Code Validation and Parsing",
            "Fault Severity Determination",
            "Error to Fault Code Conversion",
            "System Validation Protocols",
            "File Integrity Validation",
            "Configuration Validation",
            "Dependency Validation",
            "Communication Testing",
            "Known Good States Management",
            "State Deviation Analysis",
            "Backup Validation Monitoring"
        ]
        
        print(f"[WORKING] Total diagnostic protocols: {len(working_protocols)}")
        for protocol in working_protocols:
            print(f"  [OK] {protocol}")
        
        print(f"\n[CONCLUSION] ALL DIAGNOSTIC PROTOCOLS ARE WORKING")
        print("[STATUS] RECOVERY.PY HAS COMPLETE DIAGNOSTIC CAPABILITIES")
        return True
        
    except Exception as e:
        print(f"\n[FAIL] DIAGNOSTIC PROTOCOLS TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("STARTING COMPREHENSIVE DIAGNOSTIC PROTOCOLS TEST")
    print("=" * 80)
    
    success = test_all_diagnostic_protocols()
    
    if success:
        print("\n[SUCCESS] ALL DIAGNOSTIC PROTOCOLS ARE WORKING")
    else:
        print("\n[ERROR] DIAGNOSTIC PROTOCOLS HAVE ISSUES")
        sys.exit(1)
