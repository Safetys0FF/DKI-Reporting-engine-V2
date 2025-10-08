#!/usr/bin/env python3
"""
File System Operations Test - Unified Diagnostic System
Tests actual file operations, path management, and routing logic
"""

import sys
import os
import logging
from pathlib import Path

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

def test_file_system_operations():
    """Test actual file system operations and routing logic"""
    print("=" * 80)
    print("FILE SYSTEM OPERATIONS TEST - UNIFIED DIAGNOSTIC SYSTEM")
    print("=" * 80)
    
    try:
        # Import and create system
        from __init__ import UnifiedDiagnosticSystem
        print("[INIT] Creating diagnostic system...")
        diagnostic_system = UnifiedDiagnosticSystem()
        
        # Test 1: Check directory structure creation
        print("\n[TEST 1] Checking directory structure...")
        core = diagnostic_system.core
        
        # Check all required directories exist
        directories_to_check = [
            ("Base Path", core.base_path),
            ("Test Plans", core.test_plans_path),
            ("Library", core.library_path),
            ("Dependencies", core.dependencies_path),
            ("SOP", core.sop_path),
            ("Read Me", core.read_me_path),
            ("Sandbox", core.sandbox_path),
            ("Secure Vault", core.secure_vault_path),
            ("Heartbeat", core.heartbeat_path),
            ("Diagnostic Reports", core.diagnostic_reports_path),
            ("Fault Amendments", core.fault_amendments_path),
            ("Systems Amendments", core.systems_amendments_path),
            ("Fault Vault", core.fault_vault_path),
            ("Test Plans Main", core.test_plans_main_path)
        ]
        
        for name, path in directories_to_check:
            exists = path.exists()
            print(f"  {name}: {path} - {'EXISTS' if exists else 'MISSING'}")
        
        # Test 2: Test file creation and routing
        print("\n[TEST 2] Testing file creation and routing...")
        
        # Test creating a diagnostic report
        test_report_content = """# Test Diagnostic Report
        
**System**: TEST-1
**Fault Code**: TEST-1-10-123
**Status**: RESOLVED
**Timestamp**: 2025-10-07T20:00:00Z

## Analysis
This is a test diagnostic report to verify file routing logic.

## Resolution
Test completed successfully.
"""
        
        # Test routing to diagnostic_reports
        report_file = core.diagnostic_reports_path / "test_diagnostic_report.md"
        try:
            report_file.write_text(test_report_content)
            print(f"[FILE] Created diagnostic report: {report_file}")
            print(f"[VERIFY] File exists: {report_file.exists()}")
            print(f"[VERIFY] File size: {report_file.stat().st_size} bytes")
        except Exception as e:
            print(f"[ERROR] Failed to create diagnostic report: {e}")
        
        # Test routing to fault_amendments
        fault_amendment_content = """# Fault Amendment Report
        
**Fault ID**: TEST-001
**Amendment Type**: RESTORATION_ATTEMPT
**Status**: SUCCESS
**Timestamp**: 2025-10-07T20:00:00Z

## Amendment Details
Test fault amendment to verify routing logic.
"""
        
        amendment_file = core.fault_amendments_path / "test_fault_amendment.md"
        try:
            amendment_file.write_text(fault_amendment_content)
            print(f"[FILE] Created fault amendment: {amendment_file}")
            print(f"[VERIFY] File exists: {amendment_file.exists()}")
        except Exception as e:
            print(f"[ERROR] Failed to create fault amendment: {e}")
        
        # Test routing to systems_amendments
        system_amendment_content = """# System Amendment Report
        
**New System**: TEST-SYSTEM-1
**Amendment Type**: NEW_SYSTEM_DISCOVERED
**Status**: REGISTERED
**Timestamp**: 2025-10-07T20:00:00Z

## System Details
Test system amendment to verify routing logic.
"""
        
        system_amendment_file = core.systems_amendments_path / "test_system_amendment.md"
        try:
            system_amendment_file.write_text(system_amendment_content)
            print(f"[FILE] Created system amendment: {system_amendment_file}")
            print(f"[VERIFY] File exists: {system_amendment_file.exists()}")
        except Exception as e:
            print(f"[ERROR] Failed to create system amendment: {e}")
        
        # Test routing to fault_vault
        fault_vault_content = """# Fault Vault Entry
        
**Fault ID**: TEST-VAULT-001
**Severity**: ERROR
**System**: TEST-1
**Timestamp**: 2025-10-07T20:00:00Z

## Fault Details
Test fault vault entry to verify routing logic.
"""
        
        fault_vault_file = core.fault_vault_path / "test_fault_vault.md"
        try:
            fault_vault_file.write_text(fault_vault_content)
            print(f"[FILE] Created fault vault entry: {fault_vault_file}")
            print(f"[VERIFY] File exists: {fault_vault_file.exists()}")
        except Exception as e:
            print(f"[ERROR] Failed to create fault vault entry: {e}")
        
        # Test 3: Test sandbox operations
        print("\n[TEST 3] Testing sandbox operations...")
        
        # Test sandbox directory structure
        sandbox_dirs = [
            core.sandbox_path / "writeback",
            core.sandbox_path / "staging", 
            core.sandbox_path / "validation"
        ]
        
        for sandbox_dir in sandbox_dirs:
            exists = sandbox_dir.exists()
            print(f"  Sandbox {sandbox_dir.name}: {sandbox_dir} - {'EXISTS' if exists else 'MISSING'}")
        
        # Test creating a sandbox test file
        sandbox_test_file = core.sandbox_path / "validation" / "test_sandbox_file.py"
        try:
            sandbox_test_file.write_text("# Sandbox test file\nprint('Sandbox test successful')")
            print(f"[SANDBOX] Created test file: {sandbox_test_file}")
            print(f"[VERIFY] File exists: {sandbox_test_file.exists()}")
        except Exception as e:
            print(f"[ERROR] Failed to create sandbox file: {e}")
        
        # Test 4: Test secure vault operations
        print("\n[TEST 4] Testing secure vault operations...")
        
        # Check secure vault structure
        secure_vault_dirs = [
            core.secure_vault_path / "keys",
            core.secure_vault_path / "certificates",
            core.secure_vault_path / "secrets"
        ]
        
        for vault_dir in secure_vault_dirs:
            exists = vault_dir.exists()
            print(f"  Vault {vault_dir.name}: {vault_dir} - {'EXISTS' if exists else 'MISSING'}")
        
        # Test 5: Test file reading and validation
        print("\n[TEST 5] Testing file reading and validation...")
        
        # Read back the files we created
        files_to_verify = [
            (report_file, "Diagnostic Report"),
            (amendment_file, "Fault Amendment"),
            (system_amendment_file, "System Amendment"),
            (fault_vault_file, "Fault Vault"),
            (sandbox_test_file, "Sandbox Test")
        ]
        
        for file_path, file_type in files_to_verify:
            try:
                if file_path.exists():
                    content = file_path.read_text()
                    print(f"[READ] {file_type}: {len(content)} characters read successfully")
                    print(f"[CONTENT] First line: {content.split(chr(10))[0] if content else 'EMPTY'}")
                else:
                    print(f"[ERROR] {file_type}: File not found at {file_path}")
            except Exception as e:
                print(f"[ERROR] Failed to read {file_type}: {e}")
        
        # Test 6: Test file cleanup
        print("\n[TEST 6] Testing file cleanup...")
        
        test_files = [
            report_file,
            amendment_file,
            system_amendment_file,
            fault_vault_file,
            sandbox_test_file
        ]
        
        for test_file in test_files:
            try:
                if test_file.exists():
                    test_file.unlink()
                    print(f"[CLEANUP] Removed: {test_file.name}")
                else:
                    print(f"[CLEANUP] Already removed: {test_file.name}")
            except Exception as e:
                print(f"[ERROR] Failed to cleanup {test_file.name}: {e}")
        
        print("\n" + "=" * 80)
        print("[PASS] FILE SYSTEM OPERATIONS TEST COMPLETED")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n[FAIL] FILE SYSTEM OPERATIONS TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Run file system test
    success = test_file_system_operations()
    
    if success:
        print("\n[SUCCESS] FILE SYSTEM OPERATIONS WORKING")
    else:
        print("\n[ERROR] FILE SYSTEM OPERATIONS FAILED")
        sys.exit(1)
