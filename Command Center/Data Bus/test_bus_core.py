#!/usr/bin/env python3
"""
Bus Core Individual System Test
Test Bus Core for fault codes in isolation
"""

import sys
import os
import traceback
from datetime import datetime

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "Bus Core Design"))

def test_bus_core():
    """Test Bus Core system individually"""
    print("=" * 80)
    print("BUS CORE INDIVIDUAL SYSTEM TEST")
    print("=" * 80)
    
    fault_codes = []
    
    try:
        # Test 1: Import Bus Core
        try:
            from bus_core import DKIReportBus
            print("[OK] Bus Core imported successfully")
        except Exception as e:
            fault_code = f"Bus-1-01-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Import error: {str(e)}")
            return fault_codes
        
        # Test 2: Initialize Bus Core
        try:
            bus = DKIReportBus()
            print("[OK] Bus Core initialized successfully")
        except Exception as e:
            fault_code = f"Bus-1-02-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Initialization error: {str(e)}")
            return fault_codes
        
        # Test 3: New Case with None
        try:
            bus.new_case(None)
        except Exception as e:
            fault_code = f"Bus-1-30-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - New case error: {str(e)}")
        
        # Test 4: Add Files with None
        try:
            bus.add_files(None)
        except Exception as e:
            fault_code = f"Bus-1-31-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Add files error: {str(e)}")
        
        # Test 5: Process Files
        try:
            bus.process_files()
        except Exception as e:
            fault_code = f"Bus-1-32-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Process files error: {str(e)}")
        
        # Test 6: Generate Section with None
        try:
            bus.generate_section(None)
        except Exception as e:
            fault_code = f"Bus-1-50-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Generate section error: {str(e)}")
        
        # Test 7: Generate Full Report
        try:
            bus.generate_full_report()
        except Exception as e:
            fault_code = f"Bus-1-51-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Generate full report error: {str(e)}")
        
        # Test 8: Export Report with Invalid Data
        try:
            bus.export_report(None, None, None)
        except Exception as e:
            fault_code = f"Bus-1-70-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Export report error: {str(e)}")
        
        # Test 9: Get Evidence Manifest with Invalid ID
        try:
            bus.get_evidence_manifest("INVALID_ID")
        except Exception as e:
            fault_code = f"Bus-1-80-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Get evidence manifest error: {str(e)}")
        
        # Test 10: Register Signal with None
        try:
            bus.register_signal(None, None)
        except Exception as e:
            fault_code = f"Bus-1-11-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Register signal error: {str(e)}")
        
        # Test 11: Send Signal with Invalid Data
        try:
            bus.send(None, None)
        except Exception as e:
            fault_code = f"Bus-1-12-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Send signal error: {str(e)}")
        
        # Test 12: Create User with Invalid Data
        try:
            bus.create_user(None, None, None)
        except Exception as e:
            fault_code = f"Bus-1-14-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Create user error: {str(e)}")
        
        # Test 13: Authenticate User with Invalid Data
        try:
            bus.authenticate_user(None, None)
        except Exception as e:
            fault_code = f"Bus-1-60-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Authenticate user error: {str(e)}")
        
        # Test 14: Reset for New Case
        try:
            bus.reset_for_new_case()
            print("[OK] Reset for new case successful")
        except Exception as e:
            fault_code = f"Bus-1-33-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Reset for new case error: {str(e)}")
        
        # Test 15: Get System Status
        try:
            status = bus.get_system_status()
            print(f"[OK] System status retrieved: {status}")
        except Exception as e:
            fault_code = f"Bus-1-52-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Get system status error: {str(e)}")
        
    except Exception as e:
        fault_code = f"Bus-1-90-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
        fault_codes.append(fault_code)
        print(f"[FAULT] {fault_code} - System error: {str(e)}")
    
    return fault_codes

if __name__ == "__main__":
    print("Testing Bus Core System...")
    fault_codes = test_bus_core()
    
    print("\n" + "=" * 80)
    print("BUS CORE FAULT SUMMARY")
    print("=" * 80)
    print(f"Total fault codes: {len(fault_codes)}")
    for i, fault_code in enumerate(fault_codes, 1):
        print(f"{i:2d}. {fault_code}")
    
    # Store results with symptoms
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = f"F:\\The Central Command\\The War Room\\SOP's\\READ FILES\\System fault codes\\bus_core_faults_{timestamp}.txt"
    
    with open(result_file, "w") as f:
        f.write("BUS CORE FAULT CODE RESULTS\n")
        f.write("=" * 50 + "\n")
        f.write(f"Test Date: {datetime.now().isoformat()}\n")
        f.write(f"Total Faults: {len(fault_codes)}\n\n")
        
        for i, fault_code in enumerate(fault_codes, 1):
            f.write(f"{i:2d}. {fault_code}\n")
    
    print(f"\nResults stored in: {result_file}")

