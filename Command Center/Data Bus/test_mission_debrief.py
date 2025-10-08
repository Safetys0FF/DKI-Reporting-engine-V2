#!/usr/bin/env python3
"""
Mission Debrief Individual System Test
Test Mission Debrief for fault codes in isolation
"""

import sys
import os
import traceback
from datetime import datetime

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Mission Debrief", "Debrief", "README"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Mission Debrief", "The Librarian"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Mission Debrief", "report generator"))

def test_mission_debrief():
    """Test Mission Debrief system individually"""
    print("=" * 80)
    print("MISSION DEBRIEF INDIVIDUAL SYSTEM TEST")
    print("=" * 80)
    
    fault_codes = []
    
    try:
        # Test 1: Import Mission Debrief Manager
        try:
            from mission_debrief_manager import MissionDebriefManager
            print("[OK] Mission Debrief Manager imported successfully")
        except Exception as e:
            fault_code = f"3-1-01-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Import error: {str(e)}")
            return fault_codes
        
        # Test 2: Initialize Mission Debrief Manager
        try:
            mission_debrief = MissionDebriefManager()
            print("[OK] Mission Debrief Manager initialized successfully")
        except Exception as e:
            fault_code = f"3-1-02-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Initialization error: {str(e)}")
            return fault_codes
        
        # Test 3: Generate Report with None
        try:
            mission_debrief.generate_report(None)
        except Exception as e:
            fault_code = f"3-1-50-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Generate report error: {str(e)}")
        
        # Test 4: Process Complete Report with Invalid Data
        try:
            mission_debrief.process_complete_report({"invalid": "data"})
        except Exception as e:
            fault_code = f"3-1-51-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Process complete report error: {str(e)}")
        
        # Test 5: Create Cover Page with None
        try:
            mission_debrief.create_cover_page(None)
        except Exception as e:
            fault_code = f"3-1-52-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Create cover page error: {str(e)}")
        
        # Test 6: Generate TOC with Invalid Data
        try:
            mission_debrief.generate_toc({"invalid": "data"})
        except Exception as e:
            fault_code = f"3-1-53-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Generate TOC error: {str(e)}")
        
        # Test 7: Import Narrative Assembler
        try:
            from narrative_assembler import NarrativeAssembler
            print("[OK] Narrative Assembler imported successfully")
        except Exception as e:
            fault_code = f"3-2-01-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Import error: {str(e)}")
        
        # Test 8: Initialize Narrative Assembler
        try:
            narrative_assembler = NarrativeAssembler()
            print("[OK] Narrative Assembler initialized successfully")
        except Exception as e:
            fault_code = f"3-2-02-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Initialization error: {str(e)}")
        
        # Test 9: Assemble and Broadcast with None
        try:
            narrative_assembler.assemble_and_broadcast(None)
        except Exception as e:
            fault_code = f"3-2-50-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Assemble and broadcast error: {str(e)}")
        
        # Test 10: Import Report Generator
        try:
            from report_generator import ReportGenerator
            print("[OK] Report Generator imported successfully")
        except Exception as e:
            fault_code = f"3-3-01-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Import error: {str(e)}")
        
        # Test 11: Initialize Report Generator
        try:
            report_generator = ReportGenerator()
            print("[OK] Report Generator initialized successfully")
        except Exception as e:
            fault_code = f"3-3-02-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Initialization error: {str(e)}")
        
        # Test 12: Generate Full Report with None
        try:
            report_generator.generate_full_report(None)
        except Exception as e:
            fault_code = f"3-3-50-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Generate full report error: {str(e)}")
        
        # Test 13: Export Report with Invalid Data
        try:
            report_generator.export_report(None, None, None)
        except Exception as e:
            fault_code = f"3-3-70-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Export report error: {str(e)}")
        
        # Test 14: Get Report Status
        try:
            status = mission_debrief.get_report_status()
            print(f"[OK] Report status retrieved: {status}")
        except Exception as e:
            fault_code = f"3-1-54-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Get report status error: {str(e)}")
        
        # Test 15: Get Processing Status
        try:
            status = narrative_assembler.get_processing_status()
            print(f"[OK] Processing status retrieved: {status}")
        except Exception as e:
            fault_code = f"3-2-51-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Get processing status error: {str(e)}")
        
    except Exception as e:
        fault_code = f"3-1-90-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
        fault_codes.append(fault_code)
        print(f"[FAULT] {fault_code} - System error: {str(e)}")
    
    return fault_codes

if __name__ == "__main__":
    print("Testing Mission Debrief System...")
    fault_codes = test_mission_debrief()
    
    print("\n" + "=" * 80)
    print("MISSION DEBRIEF FAULT SUMMARY")
    print("=" * 80)
    print(f"Total fault codes: {len(fault_codes)}")
    for i, fault_code in enumerate(fault_codes, 1):
        print(f"{i:2d}. {fault_code}")
    
    # Store results with symptoms
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = f"F:\\The Central Command\\The War Room\\SOP's\\READ FILES\\System fault codes\\mission_debrief_faults_{timestamp}.txt"
    
    with open(result_file, "w") as f:
        f.write("MISSION DEBRIEF FAULT CODE RESULTS\n")
        f.write("=" * 50 + "\n")
        f.write(f"Test Date: {datetime.now().isoformat()}\n")
        f.write(f"Total Faults: {len(fault_codes)}\n\n")
        
        for i, fault_code in enumerate(fault_codes, 1):
            f.write(f"{i:2d}. {fault_code}\n")
    
    print(f"\nResults stored in: {result_file}")

