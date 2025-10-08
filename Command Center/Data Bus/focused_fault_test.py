#!/usr/bin/env python3
"""
Focused Fault Code Test
Quick test to capture specific fault codes without interruption
"""

import sys
import os
import traceback
from datetime import datetime

# Add paths for imports
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "Bus Core Design"))

from universal_communicator import UniversalCommunicator
from bus_core import DKIReportBus

def focused_fault_test():
    """Focused test to capture specific fault codes"""
    print("=" * 80)
    print("FOCUSED FAULT CODE DETECTION TEST")
    print("=" * 80)
    
    fault_codes = []
    
    try:
        # Initialize Bus
        bus = DKIReportBus()
        communicator = UniversalCommunicator("Bus-1", bus_connection=bus)
        
        print("Testing specific fault scenarios...")
        
        # Test 1: Communication Failures
        try:
            communicator.send_signal("INVALID", "10-4", "Test", timeout=0.1)
        except Exception as e:
            fault_code = f"Bus-1-20-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Communication timeout")
        
        # Test 2: Invalid Signal
        try:
            communicator.send_signal("", "INVALID", "Test")
        except Exception as e:
            fault_code = f"Bus-1-22-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Invalid signal")
        
        # Test 3: Data Processing Error
        try:
            bus.generate_section("")
        except Exception as e:
            fault_code = f"Bus-1-50-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Invalid section name")
        
        # Test 4: File System Error
        try:
            bus.export_report({}, "/invalid/path", "PDF")
        except Exception as e:
            fault_code = f"Bus-1-70-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Invalid file path")
        
        # Test 5: Database Error
        try:
            bus.get_evidence_manifest("INVALID")
        except Exception as e:
            fault_code = f"Bus-1-80-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Invalid evidence ID")
        
        # Test 6: Configuration Error
        try:
            bus.new_case(None)
        except Exception as e:
            fault_code = f"Bus-1-02-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Invalid configuration")
        
        # Test 7: Validation Error
        try:
            bus.add_files(None)
        except Exception as e:
            fault_code = f"Bus-1-31-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Validation error")
        
        # Test 8: Permission Error
        try:
            bus.create_user("", "", "invalid")
        except Exception as e:
            fault_code = f"Bus-1-14-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Permission error")
        
        # Test 9: Resource Error
        try:
            bus.process_files()
        except Exception as e:
            fault_code = f"Bus-1-40-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Resource error")
        
        # Test 10: Business Logic Error
        try:
            bus.generate_full_report()
        except Exception as e:
            fault_code = f"Bus-1-52-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Business logic error")
        
        # Test 11: External Service Error
        try:
            bus.authenticate_user("", "")
        except Exception as e:
            fault_code = f"Bus-1-60-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - External service error")
        
        # Test 12: Critical System Error
        try:
            bus.reset_for_new_case()
            bus.new_case({"invalid": None})
        except Exception as e:
            fault_code = f"Bus-1-90-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Critical system error")
        
        # Test 13: Signal Handler Error
        try:
            bus.register_signal("", None)
        except Exception as e:
            fault_code = f"Bus-1-01-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Signal handler error")
        
        # Test 14: Memory Error
        try:
            large_data = {"data": "x" * 1000000}
            communicator.send_signal("1-1", "10-6", "Test", payload=large_data)
        except Exception as e:
            fault_code = f"Bus-1-91-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Memory error")
        
        # Test 15: Network Error
        try:
            bus.send("network_test", {"test": "data"})
        except Exception as e:
            fault_code = f"Bus-1-93-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Network error")
        
        # Test 16: Serialization Error
        try:
            import json
            json.dumps(bus)
        except Exception as e:
            fault_code = f"Bus-1-37-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Serialization error")
        
        # Test 17: Threading Error
        try:
            bus.lock.acquire()
            bus.lock.acquire()
        except Exception as e:
            fault_code = f"Bus-1-11-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Threading error")
        
        # Test 18: Module Integration Errors
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "Evidence Locker"))
            from evidence_locker_main import EvidenceLocker
            evidence_locker = EvidenceLocker(bus=bus)
            evidence_locker.process_evidence_with_communication(None)
        except Exception as e:
            fault_code = f"1-1-30-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Evidence Locker error")
        
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "The Warden"))
            from gateway_controller import GatewayController
            gateway_controller = GatewayController(bus=bus)
            gateway_controller.validate_section_with_communication(None)
        except Exception as e:
            fault_code = f"2-2-30-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Gateway Controller error")
        
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Mission Debrief", "Debrief", "README"))
            from mission_debrief_manager import MissionDebriefManager
            mission_debrief = MissionDebriefManager()
            mission_debrief.generate_report(None)
        except Exception as e:
            fault_code = f"3-1-30-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - Mission Debrief error")
        
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "The Warden"))
            from ecosystem_controller import EcosystemController
            ecc = EcosystemController()
            ecc.validate_section("INVALID")
        except Exception as e:
            fault_code = f"2-1-50-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes.append(fault_code)
            print(f"[FAULT] {fault_code} - ECC error")
        
    except Exception as e:
        fault_code = f"Bus-1-90-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
        fault_codes.append(fault_code)
        print(f"[FAULT] {fault_code} - System error: {str(e)}")
    
    # Report Results
    print("\n" + "=" * 80)
    print("FAULT CODE SUMMARY")
    print("=" * 80)
    
    if fault_codes:
        print(f"Total fault codes captured: {len(fault_codes)}")
        print("\nAll Fault Codes:")
        for i, fault_code in enumerate(fault_codes, 1):
            print(f"{i:2d}. {fault_code}")
        
        # Group by category
        print("\nFault Code Categories:")
        categories = {
            "Communication": [f for f in fault_codes if "20" in f or "22" in f or "24" in f],
            "Data Processing": [f for f in fault_codes if "30" in f or "31" in f or "32" in f],
            "Business Logic": [f for f in fault_codes if "50" in f or "52" in f],
            "File System": [f for f in fault_codes if "70" in f],
            "Database": [f for f in fault_codes if "80" in f],
            "Configuration": [f for f in fault_codes if "01" in f or "02" in f],
            "Permission": [f for f in fault_codes if "14" in f],
            "Resource": [f for f in fault_codes if "40" in f or "41" in f],
            "External Service": [f for f in fault_codes if "60" in f],
            "Critical System": [f for f in fault_codes if "90" in f or "91" in f],
            "Memory": [f for f in fault_codes if "91" in f],
            "Network": [f for f in fault_codes if "93" in f],
            "Serialization": [f for f in fault_codes if "37" in f],
            "Threading": [f for f in fault_codes if "11" in f],
            "Module Integration": [f for f in fault_codes if "1-1" in f or "2-2" in f or "3-1" in f or "2-1" in f]
        }
        
        for category, codes in categories.items():
            if codes:
                print(f"\n{category}:")
                for code in codes:
                    print(f"  - {code}")
    else:
        print("[OK] No fault codes detected!")
    
    print(f"\nTest completed at: {datetime.now().isoformat()}")
    return fault_codes

if __name__ == "__main__":
    print("Starting Focused Fault Code Test...")
    fault_codes = focused_fault_test()
    print(f"\nCaptured {len(fault_codes)} fault codes total!")

