#!/usr/bin/env python3
"""
GUI Individual System Test
Test GUI for fault codes in isolation
"""

import sys
import os
import traceback
from datetime import datetime

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "Command Center"))

def test_gui():
    """Test GUI system individually"""
    print("=" * 80)
    print("GUI INDIVIDUAL SYSTEM TEST")
    print("=" * 80)
    
    fault_codes = []
    
    try:
        # Test 1: Import Enhanced Functional GUI
        try:
            from enhanced_functional_gui import EnhancedFunctionalGUI
            print("[OK] Enhanced Functional GUI imported successfully")
        except Exception as e:
            fault_code = f"7-1-01-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Import error: {str(e)}")
            return fault_codes
        
        # Test 2: Initialize GUI
        try:
            gui = EnhancedFunctionalGUI()
            print("[OK] GUI initialized successfully")
        except Exception as e:
            fault_code = f"7-1-02-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Initialization error: {str(e)}")
            return fault_codes
        
        # Test 3: Load Case with None
        try:
            gui.load_case(None)
        except Exception as e:
            fault_code = f"7-1-50-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Load case error: {str(e)}")
        
        # Test 4: Process Files with Invalid Data
        try:
            gui.process_files({"invalid": "data"})
        except Exception as e:
            fault_code = f"7-1-51-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Process files error: {str(e)}")
        
        # Test 5: Generate Report with None
        try:
            gui.generate_report(None)
        except Exception as e:
            fault_code = f"7-1-52-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Generate report error: {str(e)}")
        
        # Test 6: Export Report with Invalid Data
        try:
            gui.export_report(None, None, None)
        except Exception as e:
            fault_code = f"7-1-70-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Export report error: {str(e)}")
        
        # Test 7: Update Status with Invalid Data
        try:
            gui.update_status(None, None)
        except Exception as e:
            fault_code = f"7-1-53-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Update status error: {str(e)}")
        
        # Test 8: Show Health Monitor
        try:
            gui.show_health_monitor()
            print("[OK] Health monitor displayed")
        except Exception as e:
            fault_code = f"7-1-54-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Show health monitor error: {str(e)}")
        
        # Test 9: Show Diagnostics
        try:
            gui.show_diagnostics()
            print("[OK] Diagnostics displayed")
        except Exception as e:
            fault_code = f"7-1-55-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Show diagnostics error: {str(e)}")
        
        # Test 10: Get GUI Status
        try:
            status = gui.get_gui_status()
            print(f"[OK] GUI status retrieved: {status}")
        except Exception as e:
            fault_code = f"7-1-56-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Get GUI status error: {str(e)}")
        
        # Test 11: Connect to Bus with None
        try:
            gui.connect_to_bus(None)
        except Exception as e:
            fault_code = f"7-1-57-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Connect to bus error: {str(e)}")
        
        # Test 12: Send Signal with Invalid Data
        try:
            gui.send_signal(None, None, None)
        except Exception as e:
            fault_code = f"7-1-58-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Send signal error: {str(e)}")
        
        # Test 13: Receive Signal with Invalid Data
        try:
            gui.receive_signal(None)
        except Exception as e:
            fault_code = f"7-1-59-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Receive signal error: {str(e)}")
        
        # Test 14: Update Health Status
        try:
            gui.update_health_status("test_component", "OK")
            print("[OK] Health status updated")
        except Exception as e:
            fault_code = f"7-1-60-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Update health status error: {str(e)}")
        
        # Test 15: Show Communication Log
        try:
            gui.show_communication_log()
            print("[OK] Communication log displayed")
        except Exception as e:
            fault_code = f"7-1-61-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Show communication log error: {str(e)}")
        
    except Exception as e:
        fault_code = f"7-1-90-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
        fault_codes.append(fault_code)
        print(f"[FAULT] {fault_code} - System error: {str(e)}")
    
    return fault_codes

if __name__ == "__main__":
    print("Testing GUI System...")
    fault_codes = test_gui()
    
    print("\n" + "=" * 80)
    print("GUI FAULT SUMMARY")
    print("=" * 80)
    print(f"Total fault codes: {len(fault_codes)}")
    for i, fault_code in enumerate(fault_codes, 1):
        print(f"{i:2d}. {fault_code}")
    
    # Store results with symptoms
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = f"F:\\The Central Command\\The War Room\\SOP's\\READ FILES\\System fault codes\\gui_faults_{timestamp}.txt"
    
    with open(result_file, "w") as f:
        f.write("GUI FAULT CODE RESULTS\n")
        f.write("=" * 50 + "\n")
        f.write(f"Test Date: {datetime.now().isoformat()}\n")
        f.write(f"Total Faults: {len(fault_codes)}\n\n")
        
        for i, fault_code in enumerate(fault_codes, 1):
            f.write(f"{i:2d}. {fault_code}\n")
    
    print(f"\nResults stored in: {result_file}")

