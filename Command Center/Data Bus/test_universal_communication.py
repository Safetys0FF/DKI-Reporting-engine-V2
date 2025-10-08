#!/usr/bin/env python3
"""
Test Universal Communication Protocol
Force run the system and capture fault codes
"""

import sys
import os
import traceback
from datetime import datetime

# Add paths for imports
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from universal_communicator import UniversalCommunicator
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "Bus Core Design"))
from bus_core import DKIReportBus

def test_system_startup():
    """Test system startup and capture any fault codes"""
    print("=" * 80)
    print("CENTRAL COMMAND SYSTEM STARTUP TEST")
    print("=" * 80)
    print(f"Test started at: {datetime.now().isoformat()}")
    
    fault_codes_captured = []
    
    try:
        # Initialize Bus
        print("\n1. Initializing Central Command Bus...")
        bus = DKIReportBus()
        print("[OK] Bus initialized successfully")
        
        # Test Universal Communicator
        print("\n2. Testing Universal Communicator...")
        communicator = UniversalCommunicator("Bus-1", bus_connection=bus)
        print("[OK] Universal Communicator initialized")
        
        # Test Evidence Locker Integration
        print("\n3. Testing Evidence Locker Integration...")
        try:
            from evidence_locker_main import EvidenceLocker
            evidence_locker = EvidenceLocker(bus=bus)
            print("[OK] Evidence Locker initialized with universal communication")
            
            # Test evidence processing with communication
            test_evidence = {"file_path": "test_evidence.pdf", "evidence_type": "document"}
            result = evidence_locker.process_evidence_with_communication(test_evidence)
            print("[OK] Evidence processing with communication successful")
            
        except Exception as e:
            fault_code = f"1-1-10-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes_captured.append({
                "fault_code": fault_code,
                "component": "Evidence Locker",
                "error": str(e),
                "line": traceback.extract_tb(e.__traceback__)[-1].lineno
            })
            print(f"[ERROR] Evidence Locker fault: {fault_code} - {str(e)}")
        
        # Test Gateway Controller Integration
        print("\n4. Testing Gateway Controller Integration...")
        try:
            from gateway_controller import GatewayController
            gateway_controller = GatewayController(bus=bus)
            print("[OK] Gateway Controller initialized with universal communication")
            
            # Test section validation with communication
            result = gateway_controller.validate_section_with_communication("test_section")
            print("[OK] Section validation with communication successful")
            
        except Exception as e:
            fault_code = f"2-2-10-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes_captured.append({
                "fault_code": fault_code,
                "component": "Gateway Controller",
                "error": str(e),
                "line": traceback.extract_tb(e.__traceback__)[-1].lineno
            })
            print(f"[ERROR] Gateway Controller fault: {fault_code} - {str(e)}")
        
        # Test Communication Signals
        print("\n5. Testing Communication Signals...")
        try:
            # Test radio check
            response = communicator.send_radio_check("1-1")
            print(f"[OK] Radio check response: {response}")
            
            # Test status request
            response = communicator.send_status_request("2-2")
            print(f"[OK] Status request response: {response}")
            
            # Test SOS fault (simulated)
            response = communicator.send_sos_fault("TEST-01-123", "Test fault for system validation")
            print(f"[OK] SOS fault test: {response}")
            
        except Exception as e:
            fault_code = f"Bus-1-20-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes_captured.append({
                "fault_code": fault_code,
                "component": "Bus Communication",
                "error": str(e),
                "line": traceback.extract_tb(e.__traceback__)[-1].lineno
            })
            print(f"[ERROR] Communication fault: {fault_code} - {str(e)}")
        
        # Test Rollcall System
        print("\n6. Testing Rollcall System...")
        try:
            rollcall_results = bus.broadcast_rollcall()
            print(f"[OK] Rollcall results: {rollcall_results}")
            
        except Exception as e:
            fault_code = f"Bus-1-30-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes_captured.append({
                "fault_code": fault_code,
                "component": "Rollcall System",
                "error": str(e),
                "line": traceback.extract_tb(e.__traceback__)[-1].lineno
            })
            print(f"[ERROR] Rollcall fault: {fault_code} - {str(e)}")
        
        # Test Mission Debrief Integration
        print("\n7. Testing Mission Debrief Integration...")
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Mission Debrief", "Debrief", "README"))
            from mission_debrief_manager import MissionDebriefManager
            mission_debrief = MissionDebriefManager()
            print("[OK] Mission Debrief Manager initialized")
            
        except Exception as e:
            fault_code = f"3-1-10-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes_captured.append({
                "fault_code": fault_code,
                "component": "Mission Debrief",
                "error": str(e),
                "line": traceback.extract_tb(e.__traceback__)[-1].lineno
            })
            print(f"[ERROR] Mission Debrief fault: {fault_code} - {str(e)}")
        
        # Test GUI Integration
        print("\n8. Testing GUI Integration...")
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
            from enhanced_functional_gui import EnhancedFunctionalGUI
            gui = EnhancedFunctionalGUI()
            print("[OK] Enhanced Functional GUI initialized")
            
        except Exception as e:
            fault_code = f"7-1-10-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes_captured.append({
                "fault_code": fault_code,
                "component": "Enhanced GUI",
                "error": str(e),
                "line": traceback.extract_tb(e.__traceback__)[-1].lineno
            })
            print(f"[ERROR] GUI fault: {fault_code} - {str(e)}")
        
        # Test ECC Integration
        print("\n9. Testing ECC Integration...")
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "The Warden"))
            from ecosystem_controller import EcosystemController
            ecc = EcosystemController()
            print("[OK] Ecosystem Controller initialized")
            
        except Exception as e:
            fault_code = f"2-1-10-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes_captured.append({
                "fault_code": fault_code,
                "component": "Ecosystem Controller",
                "error": str(e),
                "line": traceback.extract_tb(e.__traceback__)[-1].lineno
            })
            print(f"[ERROR] ECC fault: {fault_code} - {str(e)}")
        
        # Test Analyst Deck Integration
        print("\n10. Testing Analyst Deck Integration...")
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "The Analyst Deck"))
            from section_1_framework import Section1Framework
            section1 = Section1Framework()
            print("[OK] Section 1 Framework initialized")
            
        except Exception as e:
            fault_code = f"4-1-10-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes_captured.append({
                "fault_code": fault_code,
                "component": "Section 1 Framework",
                "error": str(e),
                "line": traceback.extract_tb(e.__traceback__)[-1].lineno
            })
            print(f"[ERROR] Section 1 fault: {fault_code} - {str(e)}")
        
    except Exception as e:
        fault_code = f"Bus-1-90-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
        fault_codes_captured.append({
            "fault_code": fault_code,
            "component": "System Startup",
            "error": str(e),
            "line": traceback.extract_tb(e.__traceback__)[-1].lineno
        })
        print(f"[ERROR] System startup fault: {fault_code} - {str(e)}")
    
    # Report Results
    print("\n" + "=" * 80)
    print("FAULT CODE ANALYSIS REPORT")
    print("=" * 80)
    
    if fault_codes_captured:
        print(f"Total fault codes captured: {len(fault_codes_captured)}")
        print("\nFault Codes Detected:")
        for i, fault in enumerate(fault_codes_captured, 1):
            print(f"\n{i}. {fault['fault_code']}")
            print(f"   Component: {fault['component']}")
            print(f"   Error: {fault['error']}")
            print(f"   Line: {fault['line']}")
    else:
        print("[OK] No fault codes detected - System running cleanly!")
    
    print(f"\nTest completed at: {datetime.now().isoformat()}")
    return fault_codes_captured

def test_forced_errors():
    """Test forced errors to generate fault codes"""
    print("\n" + "=" * 80)
    print("FORCED ERROR TESTING")
    print("=" * 80)
    
    fault_codes_captured = []
    
    try:
        # Initialize basic components
        bus = DKIReportBus()
        communicator = UniversalCommunicator("Bus-1", bus_connection=bus)
        
        # Force communication timeout
        print("\nTesting communication timeout...")
        try:
            response = communicator.send_signal("INVALID-ADDRESS", "10-4", "Test timeout", timeout=1)
        except Exception as e:
            fault_code = f"Bus-1-20-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes_captured.append({
                "fault_code": fault_code,
                "component": "Communication Timeout",
                "error": str(e),
                "line": traceback.extract_tb(e.__traceback__)[-1].lineno
            })
            print(f"[ERROR] Communication timeout fault: {fault_code}")
        
        # Force invalid signal
        print("\nTesting invalid signal...")
        try:
            response = communicator.send_signal("", "INVALID-CODE", "Test invalid", timeout=1)
        except Exception as e:
            fault_code = f"Bus-1-22-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes_captured.append({
                "fault_code": fault_code,
                "component": "Invalid Signal",
                "error": str(e),
                "line": traceback.extract_tb(e.__traceback__)[-1].lineno
            })
            print(f"[ERROR] Invalid signal fault: {fault_code}")
        
        # Force SOS fault
        print("\nTesting SOS fault generation...")
        try:
            response = communicator.send_sos_fault("TEST-SOS-01", "Forced test fault")
            print(f"[OK] SOS fault generated: {response}")
        except Exception as e:
            fault_code = f"Bus-1-30-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            fault_codes_captured.append({
                "fault_code": fault_code,
                "component": "SOS Fault Generation",
                "error": str(e),
                "line": traceback.extract_tb(e.__traceback__)[-1].lineno
            })
            print(f"[ERROR] SOS fault generation fault: {fault_code}")
        
    except Exception as e:
        fault_code = f"Bus-1-90-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
        fault_codes_captured.append({
            "fault_code": fault_code,
            "component": "Forced Error Test",
            "error": str(e),
            "line": traceback.extract_tb(e.__traceback__)[-1].lineno
        })
        print(f"[ERROR] Forced error test fault: {fault_code}")
    
    return fault_codes_captured

if __name__ == "__main__":
    print("Starting Central Command System Test...")
    
    # Run system startup test
    startup_faults = test_system_startup()
    
    # Run forced error test
    forced_faults = test_forced_errors()
    
    # Combine all fault codes
    all_faults = startup_faults + forced_faults
    
    print("\n" + "=" * 80)
    print("FINAL FAULT CODE SUMMARY")
    print("=" * 80)
    
    if all_faults:
        print(f"Total fault codes captured: {len(all_faults)}")
        print("\nAll Fault Codes:")
        for i, fault in enumerate(all_faults, 1):
            print(f"{i:2d}. {fault['fault_code']} - {fault['component']}")
    else:
        print("[OK] No fault codes detected - System is running perfectly!")
    
    print("\nTest completed successfully!")
