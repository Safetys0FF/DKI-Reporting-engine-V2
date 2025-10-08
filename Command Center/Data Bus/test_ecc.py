#!/usr/bin/env python3
"""
ECC Individual System Test
Test ECC for fault codes in isolation
"""

import sys
import os
import traceback
from datetime import datetime

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "The Warden"))

def test_ecc():
    """Test ECC system individually"""
    print("=" * 80)
    print("ECC INDIVIDUAL SYSTEM TEST")
    print("=" * 80)
    
    fault_codes = []
    
    try:
        # Test 1: Import ECC
        try:
            from ecosystem_controller import EcosystemController
            print("[OK] ECC imported successfully")
        except Exception as e:
            fault_code = f"2-1-01-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Import error: {str(e)}")
            return fault_codes
        
        # Test 2: Initialize ECC
        try:
            ecc = EcosystemController()
            print("[OK] ECC initialized successfully")
        except Exception as e:
            fault_code = f"2-1-02-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Initialization error: {str(e)}")
            return fault_codes
        
        # Test 3: Validate Section with None
        try:
            ecc.validate_section(None)
        except Exception as e:
            fault_code = f"2-1-50-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Validate section error: {str(e)}")
        
        # Test 4: Validate Section with Invalid ID
        try:
            ecc.validate_section("INVALID_SECTION")
        except Exception as e:
            fault_code = f"2-1-51-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Invalid section ID error: {str(e)}")
        
        # Test 5: Check Permissions with None
        try:
            ecc.check_permissions(None, None)
        except Exception as e:
            fault_code = f"2-1-52-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Check permissions error: {str(e)}")
        
        # Test 6: Authorize Operation with Invalid Data
        try:
            ecc.authorize_operation(None, "test_operation")
        except Exception as e:
            fault_code = f"2-1-53-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Authorize operation error: {str(e)}")
        
        # Test 7: Get System Status
        try:
            status = ecc.get_system_status()
            print(f"[OK] System status retrieved: {status}")
        except Exception as e:
            fault_code = f"2-1-54-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Get system status error: {str(e)}")
        
        # Test 8: Get Module Status with Invalid Module
        try:
            ecc.get_module_status("INVALID_MODULE")
        except Exception as e:
            fault_code = f"2-1-55-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Get module status error: {str(e)}")
        
        # Test 9: Start New Case with None
        try:
            ecc.start_new_case(None)
        except Exception as e:
            fault_code = f"2-1-56-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Start new case error: {str(e)}")
        
        # Test 10: End Case with Invalid Case ID
        try:
            ecc.end_case("INVALID_CASE")
        except Exception as e:
            fault_code = f"2-1-57-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - End case error: {str(e)}")
        
        # Test 11: Get Active Cases
        try:
            cases = ecc.get_active_cases()
            print(f"[OK] Active cases retrieved: {len(cases) if cases else 0}")
        except Exception as e:
            fault_code = f"2-1-58-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Get active cases error: {str(e)}")
        
        # Test 12: Register Module with None
        try:
            ecc.register_module(None)
        except Exception as e:
            fault_code = f"2-1-59-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Register module error: {str(e)}")
        
        # Test 13: Unregister Module with Invalid Module
        try:
            ecc.unregister_module("INVALID_MODULE")
        except Exception as e:
            fault_code = f"2-1-60-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Unregister module error: {str(e)}")
        
        # Test 14: Get Registered Modules
        try:
            modules = ecc.get_registered_modules()
            print(f"[OK] Registered modules retrieved: {len(modules) if modules else 0}")
        except Exception as e:
            fault_code = f"2-1-61-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Get registered modules error: {str(e)}")
        
        # Test 15: Broadcast Signal with Invalid Signal
        try:
            ecc.broadcast_signal(None, None)
        except Exception as e:
            fault_code = f"2-1-62-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Broadcast signal error: {str(e)}")
        
    except Exception as e:
        fault_code = f"2-1-90-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
        fault_codes.append(fault_code)
        print(f"[FAULT] {fault_code} - System error: {str(e)}")
    
    return fault_codes

if __name__ == "__main__":
    print("Testing ECC System...")
    fault_codes = test_ecc()
    
    print("\n" + "=" * 80)
    print("ECC FAULT SUMMARY")
    print("=" * 80)
    print(f"Total fault codes: {len(fault_codes)}")
    for i, fault_code in enumerate(fault_codes, 1):
        print(f"{i:2d}. {fault_code}")
    
    # Store results with symptoms
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = f"F:\\The Central Command\\The War Room\\SOP's\\READ FILES\\System fault codes\\ecc_faults_{timestamp}.txt"
    
    with open(result_file, "w") as f:
        f.write("ECC FAULT CODE RESULTS\n")
        f.write("=" * 50 + "\n")
        f.write(f"Test Date: {datetime.now().isoformat()}\n")
        f.write(f"Total Faults: {len(fault_codes)}\n\n")
        
        for i, fault_code in enumerate(fault_codes, 1):
            f.write(f"{i:2d}. {fault_code}\n")
    
    print(f"\nResults stored in: {result_file}")

