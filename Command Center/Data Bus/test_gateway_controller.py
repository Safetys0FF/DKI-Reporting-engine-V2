#!/usr/bin/env python3
"""
Gateway Controller Individual System Test
Test Gateway Controller for fault codes in isolation
"""

import sys
import os
import traceback
from datetime import datetime

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "The Warden"))
sys.path.append(os.path.join(os.path.dirname(__file__), "Bus Core Design"))

def test_gateway_controller():
    """Test Gateway Controller system individually"""
    print("=" * 80)
    print("GATEWAY CONTROLLER INDIVIDUAL SYSTEM TEST")
    print("=" * 80)
    
    fault_codes = []
    
    try:
        # Test 1: Import Gateway Controller
        try:
            from gateway_controller import GatewayController
            print("[OK] Gateway Controller imported successfully")
        except Exception as e:
            fault_code = f"2-2-01-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Import error: {str(e)}")
            return fault_codes
        
        # Test 2: Initialize Gateway Controller
        try:
            gateway_controller = GatewayController()
            print("[OK] Gateway Controller initialized successfully")
        except Exception as e:
            fault_code = f"2-2-02-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Initialization error: {str(e)}")
            return fault_codes
        
        # Test 3: Process Evidence with None
        try:
            gateway_controller.process_evidence(None)
        except Exception as e:
            fault_code = f"2-2-30-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Process evidence error: {str(e)}")
        
        # Test 4: Process Evidence with Invalid Data
        try:
            gateway_controller.process_evidence({"invalid": "data"})
        except Exception as e:
            fault_code = f"2-2-31-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Invalid evidence data: {str(e)}")
        
        # Test 5: Validate Section with None
        try:
            gateway_controller.validate_section(None)
        except Exception as e:
            fault_code = f"2-2-32-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Validate section error: {str(e)}")
        
        # Test 6: Process Files with None
        try:
            gateway_controller.process_files(None)
        except Exception as e:
            fault_code = f"2-2-33-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Process files error: {str(e)}")
        
        # Test 7: Get Section Status with Invalid ID
        try:
            gateway_controller.get_section_status("INVALID_ID")
        except Exception as e:
            fault_code = f"2-2-50-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Get section status error: {str(e)}")
        
        # Test 8: Generate Section with None
        try:
            gateway_controller.generate_section(None)
        except Exception as e:
            fault_code = f"2-2-51-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Generate section error: {str(e)}")
        
        # Test 9: OCR Processing with Invalid File
        try:
            gateway_controller.process_ocr("invalid_file.pdf")
        except Exception as e:
            fault_code = f"2-2-52-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - OCR processing error: {str(e)}")
        
        # Test 10: Evidence Classification with None
        try:
            gateway_controller.classify_evidence(None)
        except Exception as e:
            fault_code = f"2-2-53-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Evidence classification error: {str(e)}")
        
        # Test 11: Route Evidence with Invalid Data
        try:
            gateway_controller.route_evidence({"invalid": "data"})
        except Exception as e:
            fault_code = f"2-2-54-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Route evidence error: {str(e)}")
        
        # Test 12: Get Processing Status
        try:
            status = gateway_controller.get_processing_status()
            print(f"[OK] Processing status retrieved: {status}")
        except Exception as e:
            fault_code = f"2-2-55-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Get processing status error: {str(e)}")
        
        # Test 13: Communication Status
        try:
            comm_status = gateway_controller.get_communication_status()
            print(f"[OK] Communication status retrieved: {comm_status}")
        except Exception as e:
            fault_code = f"2-2-56-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Communication status error: {str(e)}")
        
    except Exception as e:
        fault_code = f"2-2-90-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
        fault_codes.append(fault_code)
        print(f"[FAULT] {fault_code} - System error: {str(e)}")
    
    return fault_codes

if __name__ == "__main__":
    print("Testing Gateway Controller System...")
    fault_codes = test_gateway_controller()
    
    print("\n" + "=" * 80)
    print("GATEWAY CONTROLLER FAULT SUMMARY")
    print("=" * 80)
    print(f"Total fault codes: {len(fault_codes)}")
    for i, fault_code in enumerate(fault_codes, 1):
        print(f"{i:2d}. {fault_code}")
    
    # Store results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = f"F:\\The Central Command\\The War Room\\SOP's\\READ FILES\\System fault codes\\gateway_controller_faults_{timestamp}.txt"
    
    with open(result_file, "w") as f:
        f.write("GATEWAY CONTROLLER FAULT CODE RESULTS\n")
        f.write("=" * 50 + "\n")
        f.write(f"Test Date: {datetime.now().isoformat()}\n")
        f.write(f"Total Faults: {len(fault_codes)}\n\n")
        
        for i, fault_code in enumerate(fault_codes, 1):
            f.write(f"{i:2d}. {fault_code}\n")
    
    print(f"\nResults stored in: {result_file}")

