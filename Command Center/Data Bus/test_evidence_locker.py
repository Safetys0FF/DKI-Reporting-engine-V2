#!/usr/bin/env python3
"""
Evidence Locker Individual System Test
Test Evidence Locker for fault codes in isolation
"""

import sys
import os
import traceback
from datetime import datetime

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "Evidence Locker"))
sys.path.append(os.path.join(os.path.dirname(__file__), "Bus Core Design"))

def test_evidence_locker():
    """Test Evidence Locker system individually"""
    print("=" * 80)
    print("EVIDENCE LOCKER INDIVIDUAL SYSTEM TEST")
    print("=" * 80)
    
    fault_codes = []
    
    try:
        # Test 1: Import Evidence Locker
        try:
            from evidence_locker_main import EvidenceLocker
            print("[OK] Evidence Locker imported successfully")
        except Exception as e:
            fault_code = f"1-1-01-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Import error: {str(e)}")
            return fault_codes
        
        # Test 2: Initialize Evidence Locker
        try:
            evidence_locker = EvidenceLocker()
            print("[OK] Evidence Locker initialized successfully")
        except Exception as e:
            fault_code = f"1-1-02-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Initialization error: {str(e)}")
            return fault_codes
        
        # Test 3: Process Evidence with None
        try:
            evidence_locker.process_evidence(None)
        except Exception as e:
            fault_code = f"1-1-30-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Process evidence error: {str(e)}")
        
        # Test 4: Process Evidence with Invalid Data
        try:
            evidence_locker.process_evidence({"invalid": "data"})
        except Exception as e:
            fault_code = f"1-1-31-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Invalid evidence data: {str(e)}")
        
        # Test 5: Start New Case with None
        try:
            evidence_locker.start_new_case(None)
        except Exception as e:
            fault_code = f"1-1-32-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Start new case error: {str(e)}")
        
        # Test 6: Get Evidence with Invalid ID
        try:
            evidence_locker.get_evidence("INVALID_ID")
        except Exception as e:
            fault_code = f"1-1-50-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Get evidence error: {str(e)}")
        
        # Test 7: Clear Evidence Pool
        try:
            evidence_locker.clear_evidence_pool()
            print("[OK] Evidence pool cleared successfully")
        except Exception as e:
            fault_code = f"1-1-33-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Clear evidence pool error: {str(e)}")
        
        # Test 8: Get Manifest
        try:
            manifest = evidence_locker.get_manifest()
            print(f"[OK] Manifest retrieved: {len(manifest.get('entries', []))} entries")
        except Exception as e:
            fault_code = f"1-1-51-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Get manifest error: {str(e)}")
        
        # Test 9: Evidence Index Operations
        try:
            from evidence_index import EvidenceIndex
            index = EvidenceIndex()
            index.add_evidence("test_id", {"test": "data"})
            result = index.get_evidence("test_id")
            print(f"[OK] Evidence index operations successful")
        except Exception as e:
            fault_code = f"1-1-52-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Evidence index error: {str(e)}")
        
        # Test 10: Evidence Classifier
        try:
            from evidence_classifier import EvidenceClassifier
            classifier = EvidenceClassifier()
            result = classifier.classify_evidence({"type": "test"})
            print(f"[OK] Evidence classifier operations successful")
        except Exception as e:
            fault_code = f"1-1-53-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Evidence classifier error: {str(e)}")
        
        # Test 11: Static Data Flow
        try:
            from static_data_flow import StaticDataFlow
            flow = StaticDataFlow()
            result = flow.process_static_data({"test": "data"})
            print(f"[OK] Static data flow operations successful")
        except Exception as e:
            fault_code = f"1-1-54-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Static data flow error: {str(e)}")
        
        # Test 12: Case Manifest Builder
        try:
            from case_manifest_builder import CaseManifestBuilder
            builder = CaseManifestBuilder()
            result = builder.build_manifest("test_case")
            print(f"[OK] Case manifest builder operations successful")
        except Exception as e:
            fault_code = f"1-1-55-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Case manifest builder error: {str(e)}")
        
    except Exception as e:
        fault_code = f"1-1-90-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
        fault_codes.append(fault_code)
        print(f"[FAULT] {fault_code} - System error: {str(e)}")
    
    return fault_codes

if __name__ == "__main__":
    print("Testing Evidence Locker System...")
    fault_codes = test_evidence_locker()
    
    print("\n" + "=" * 80)
    print("EVIDENCE LOCKER FAULT SUMMARY")
    print("=" * 80)
    print(f"Total fault codes: {len(fault_codes)}")
    for i, fault_code in enumerate(fault_codes, 1):
        print(f"{i:2d}. {fault_code}")
    
    # Store results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = f"F:\\The Central Command\\The War Room\\SOP's\\READ FILES\\System fault codes\\evidence_locker_faults_{timestamp}.txt"
    
    with open(result_file, "w") as f:
        f.write("EVIDENCE LOCKER FAULT CODE RESULTS\n")
        f.write("=" * 50 + "\n")
        f.write(f"Test Date: {datetime.now().isoformat()}\n")
        f.write(f"Total Faults: {len(fault_codes)}\n\n")
        
        for i, fault_code in enumerate(fault_codes, 1):
            f.write(f"{i:2d}. {fault_code}\n")
    
    print(f"\nResults stored in: {result_file}")

