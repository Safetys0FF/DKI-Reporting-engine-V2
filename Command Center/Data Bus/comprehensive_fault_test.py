#!/usr/bin/env python3
"""
Comprehensive Fault Code Test
Force run ALL system operations to capture maximum fault codes
"""

import sys
import os
import traceback
import time
from datetime import datetime

# Add paths for imports
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "Bus Core Design"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from universal_communicator import UniversalCommunicator
from bus_core import DKIReportBus

def comprehensive_fault_test():
    """Comprehensive test to capture ALL possible fault codes"""
    print("=" * 100)
    print("COMPREHENSIVE FAULT CODE DETECTION TEST")
    print("=" * 100)
    print(f"Test started at: {datetime.now().isoformat()}")
    
    all_fault_codes = []
    
    try:
        # Initialize Bus
        print("\n1. INITIALIZING CENTRAL COMMAND BUS...")
        bus = DKIReportBus()
        print("[OK] Bus initialized")
        
        # Initialize Communicator
        communicator = UniversalCommunicator("Bus-1", bus_connection=bus)
        print("[OK] Universal Communicator initialized")
        
        # Test 1: Force Communication Failures
        print("\n2. TESTING COMMUNICATION FAILURES...")
        try:
            # Test invalid addresses
            response = communicator.send_signal("INVALID-ADDRESS", "10-4", "Test invalid address", timeout=1)
        except Exception as e:
            fault_code = f"Bus-1-24-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            all_fault_codes.append({
                "fault_code": fault_code,
                "component": "Bus Communication",
                "error": str(e),
                "test": "Invalid Address"
            })
            print(f"[FAULT] {fault_code} - Invalid address: {str(e)}")
        
        try:
            # Test communication timeout
            response = communicator.send_signal("TIMEOUT-TEST", "10-4", "Test timeout", timeout=0.1)
        except Exception as e:
            fault_code = f"Bus-1-20-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            all_fault_codes.append({
                "fault_code": fault_code,
                "component": "Bus Communication",
                "error": str(e),
                "test": "Communication Timeout"
            })
            print(f"[FAULT] {fault_code} - Communication timeout: {str(e)}")
        
        try:
            # Test invalid radio codes
            response = communicator.send_signal("1-1", "INVALID-CODE", "Test invalid radio code")
        except Exception as e:
            fault_code = f"Bus-1-22-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            all_fault_codes.append({
                "fault_code": fault_code,
                "component": "Bus Communication",
                "error": str(e),
                "test": "Invalid Radio Code"
            })
            print(f"[FAULT] {fault_code} - Invalid radio code: {str(e)}")
        
        # Test 2: Force Data Processing Failures
        print("\n3. TESTING DATA PROCESSING FAILURES...")
        try:
            # Test invalid payload
            response = communicator.send_signal("1-1", "10-6", "Test invalid payload", payload="INVALID_PAYLOAD")
        except Exception as e:
            fault_code = f"Bus-1-30-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            all_fault_codes.append({
                "fault_code": fault_code,
                "component": "Bus Data Processing",
                "error": str(e),
                "test": "Invalid Payload"
            })
            print(f"[FAULT] {fault_code} - Invalid payload: {str(e)}")
        
        try:
            # Test corrupted data
            corrupted_data = {"corrupted": "data", "invalid": None, "missing": ""}
            response = communicator.send_signal("1-1", "10-6", "Test corrupted data", payload=corrupted_data)
        except Exception as e:
            fault_code = f"Bus-1-32-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            all_fault_codes.append({
                "fault_code": fault_code,
                "component": "Bus Data Processing",
                "error": str(e),
                "test": "Corrupted Data"
            })
            print(f"[FAULT] {fault_code} - Corrupted data: {str(e)}")
        
        # Test 3: Force Resource Failures
        print("\n4. TESTING RESOURCE FAILURES...")
        try:
            # Test resource exhaustion
            for i in range(1000):
                communicator.send_signal(f"TEST-{i}", "10-4", f"Resource test {i}")
        except Exception as e:
            fault_code = f"Bus-1-41-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            all_fault_codes.append({
                "fault_code": fault_code,
                "component": "Bus Resource",
                "error": str(e),
                "test": "Resource Exhaustion"
            })
            print(f"[FAULT] {fault_code} - Resource exhaustion: {str(e)}")
        
        # Test 4: Force File System Failures
        print("\n5. TESTING FILE SYSTEM FAILURES...")
        try:
            # Test file operations
            bus.export_report({"test": "data"}, "/invalid/path/file.pdf", "PDF")
        except Exception as e:
            fault_code = f"Bus-1-70-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            all_fault_codes.append({
                "fault_code": fault_code,
                "component": "Bus File System",
                "error": str(e),
                "test": "Invalid File Path"
            })
            print(f"[FAULT] {fault_code} - Invalid file path: {str(e)}")
        
        # Test 5: Force Database Failures
        print("\n6. TESTING DATABASE FAILURES...")
        try:
            # Test database operations
            bus.get_evidence_manifest("INVALID_EVIDENCE_ID")
        except Exception as e:
            fault_code = f"Bus-1-80-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            all_fault_codes.append({
                "fault_code": fault_code,
                "component": "Bus Database",
                "error": str(e),
                "test": "Invalid Evidence ID"
            })
            print(f"[FAULT] {fault_code} - Invalid evidence ID: {str(e)}")
        
        # Test 6: Force Business Logic Failures
        print("\n7. TESTING BUSINESS LOGIC FAILURES...")
        try:
            # Test invalid case operations
            bus.generate_section("")
        except Exception as e:
            fault_code = f"Bus-1-50-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            all_fault_codes.append({
                "fault_code": fault_code,
                "component": "Bus Business Logic",
                "error": str(e),
                "test": "Invalid Section Name"
            })
            print(f"[FAULT] {fault_code} - Invalid section name: {str(e)}")
        
        try:
            # Test invalid report generation
            bus.generate_full_report()
        except Exception as e:
            fault_code = f"Bus-1-52-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            all_fault_codes.append({
                "fault_code": fault_code,
                "component": "Bus Business Logic",
                "error": str(e),
                "test": "Invalid Report Generation"
            })
            print(f"[FAULT] {fault_code} - Invalid report generation: {str(e)}")
        
        # Test 7: Force External Service Failures
        print("\n8. TESTING EXTERNAL SERVICE FAILURES...")
        try:
            # Test external service calls
            bus.authenticate_user("", "")
        except Exception as e:
            fault_code = f"Bus-1-60-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            all_fault_codes.append({
                "fault_code": fault_code,
                "component": "Bus External Service",
                "error": str(e),
                "test": "Invalid Authentication"
            })
            print(f"[FAULT] {fault_code} - Invalid authentication: {str(e)}")
        
        # Test 8: Force Critical System Failures
        print("\n9. TESTING CRITICAL SYSTEM FAILURES...")
        try:
            # Test system crash simulation
            bus.reset_for_new_case()
            bus.new_case(None)
        except Exception as e:
            fault_code = f"Bus-1-90-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            all_fault_codes.append({
                "fault_code": fault_code,
                "component": "Bus Critical System",
                "error": str(e),
                "test": "System Crash Simulation"
            })
            print(f"[FAULT] {fault_code} - System crash simulation: {str(e)}")
        
        # Test 9: Force SOS Fault Generation
        print("\n10. TESTING SOS FAULT GENERATION...")
        try:
            # Generate multiple SOS faults
            for i in range(5):
                fault_code = f"TEST-SOS-{i:02d}-123"
                response = communicator.send_sos_fault(fault_code, f"Test SOS fault {i}")
                print(f"[SOS] {fault_code} - SOS fault generated")
        except Exception as e:
            fault_code = f"Bus-1-30-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            all_fault_codes.append({
                "fault_code": fault_code,
                "component": "Bus SOS Fault",
                "error": str(e),
                "test": "SOS Fault Generation"
            })
            print(f"[FAULT] {fault_code} - SOS fault generation: {str(e)}")
        
        # Test 10: Force Module Integration Failures
        print("\n11. TESTING MODULE INTEGRATION FAILURES...")
        try:
            # Test Evidence Locker integration
            sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "Evidence Locker"))
            from evidence_locker_main import EvidenceLocker
            evidence_locker = EvidenceLocker(bus=bus)
            
            # Force evidence processing error
            result = evidence_locker.process_evidence_with_communication(None)
        except Exception as e:
            fault_code = f"1-1-30-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            all_fault_codes.append({
                "fault_code": fault_code,
                "component": "Evidence Locker",
                "error": str(e),
                "test": "Evidence Processing Error"
            })
            print(f"[FAULT] {fault_code} - Evidence processing error: {str(e)}")
        
        try:
            # Test Gateway Controller integration
            sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "The Warden"))
            from gateway_controller import GatewayController
            gateway_controller = GatewayController(bus=bus)
            
            # Force section validation error
            result = gateway_controller.validate_section_with_communication(None)
        except Exception as e:
            fault_code = f"2-2-30-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            all_fault_codes.append({
                "fault_code": fault_code,
                "component": "Gateway Controller",
                "error": str(e),
                "test": "Section Validation Error"
            })
            print(f"[FAULT] {fault_code} - Section validation error: {str(e)}")
        
        # Test 11: Force Mission Debrief Failures
        print("\n12. TESTING MISSION DEBRIEF FAILURES...")
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Mission Debrief", "Debrief", "README"))
            from mission_debrief_manager import MissionDebriefManager
            mission_debrief = MissionDebriefManager()
            
            # Force report generation error
            result = mission_debrief.generate_report(None)
        except Exception as e:
            fault_code = f"3-1-30-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            all_fault_codes.append({
                "fault_code": fault_code,
                "component": "Mission Debrief",
                "error": str(e),
                "test": "Report Generation Error"
            })
            print(f"[FAULT] {fault_code} - Report generation error: {str(e)}")
        
        # Test 12: Force ECC Failures
        print("\n13. TESTING ECC FAILURES...")
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "The Warden"))
            from ecosystem_controller import EcosystemController
            ecc = EcosystemController()
            
            # Force ECC operations
            result = ecc.validate_section("INVALID_SECTION")
        except Exception as e:
            fault_code = f"2-1-50-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            all_fault_codes.append({
                "fault_code": fault_code,
                "component": "Ecosystem Controller",
                "error": str(e),
                "test": "ECC Validation Error"
            })
            print(f"[FAULT] {fault_code} - ECC validation error: {str(e)}")
        
        # Test 13: Force Signal Handler Failures
        print("\n14. TESTING SIGNAL HANDLER FAILURES...")
        try:
            # Test invalid signal handlers
            bus.register_signal("", None)
        except Exception as e:
            fault_code = f"Bus-1-01-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            all_fault_codes.append({
                "fault_code": fault_code,
                "component": "Bus Signal Handler",
                "error": str(e),
                "test": "Invalid Signal Handler"
            })
            print(f"[FAULT] {fault_code} - Invalid signal handler: {str(e)}")
        
        try:
            # Test invalid signal emission
            bus.emit("", None)
        except Exception as e:
            fault_code = f"Bus-1-30-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            all_fault_codes.append({
                "fault_code": fault_code,
                "component": "Bus Signal Emission",
                "error": str(e),
                "test": "Invalid Signal Emission"
            })
            print(f"[FAULT] {fault_code} - Invalid signal emission: {str(e)}")
        
        # Test 14: Force Memory and Performance Failures
        print("\n15. TESTING MEMORY AND PERFORMANCE FAILURES...")
        try:
            # Test memory allocation
            large_data = {"data": "x" * 10000000}  # 10MB string
            response = communicator.send_signal("1-1", "10-6", "Test large data", payload=large_data)
        except Exception as e:
            fault_code = f"Bus-1-91-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            all_fault_codes.append({
                "fault_code": fault_code,
                "component": "Bus Memory",
                "error": str(e),
                "test": "Memory Allocation Error"
            })
            print(f"[FAULT] {fault_code} - Memory allocation error: {str(e)}")
        
        # Test 15: Force Network and Connection Failures
        print("\n16. TESTING NETWORK AND CONNECTION FAILURES...")
        try:
            # Test network operations
            bus.send("network_test", {"test": "data"})
        except Exception as e:
            fault_code = f"Bus-1-93-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            all_fault_codes.append({
                "fault_code": fault_code,
                "component": "Bus Network",
                "error": str(e),
                "test": "Network Connection Error"
            })
            print(f"[FAULT] {fault_code} - Network connection error: {str(e)}")
        
        # Test 16: Force Configuration Failures
        print("\n17. TESTING CONFIGURATION FAILURES...")
        try:
            # Test configuration operations
            bus.case_metadata = None
            bus.new_case({"invalid": "config"})
        except Exception as e:
            fault_code = f"Bus-1-02-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            all_fault_codes.append({
                "fault_code": fault_code,
                "component": "Bus Configuration",
                "error": str(e),
                "test": "Configuration Error"
            })
            print(f"[FAULT] {fault_code} - Configuration error: {str(e)}")
        
        # Test 17: Force Permission Failures
        print("\n18. TESTING PERMISSION FAILURES...")
        try:
            # Test permission operations
            bus.create_user("", "", "invalid_role")
        except Exception as e:
            fault_code = f"Bus-1-14-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            all_fault_codes.append({
                "fault_code": fault_code,
                "component": "Bus Permission",
                "error": str(e),
                "test": "Permission Error"
            })
            print(f"[FAULT] {fault_code} - Permission error: {str(e)}")
        
        # Test 18: Force Validation Failures
        print("\n19. TESTING VALIDATION FAILURES...")
        try:
            # Test validation operations
            bus.add_files(None)
        except Exception as e:
            fault_code = f"Bus-1-31-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            all_fault_codes.append({
                "fault_code": fault_code,
                "component": "Bus Validation",
                "error": str(e),
                "test": "Validation Error"
            })
            print(f"[FAULT] {fault_code} - Validation error: {str(e)}")
        
        # Test 19: Force Serialization Failures
        print("\n20. TESTING SERIALIZATION FAILURES...")
        try:
            # Test serialization operations
            import json
            json.dumps(bus)
        except Exception as e:
            fault_code = f"Bus-1-37-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            all_fault_codes.append({
                "fault_code": fault_code,
                "component": "Bus Serialization",
                "error": str(e),
                "test": "Serialization Error"
            })
            print(f"[FAULT] {fault_code} - Serialization error: {str(e)}")
        
        # Test 20: Force Threading Failures
        print("\n21. TESTING THREADING FAILURES...")
        try:
            # Test threading operations
            bus.lock.acquire()
            bus.lock.acquire()  # This should cause a deadlock
        except Exception as e:
            fault_code = f"Bus-1-11-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
            all_fault_codes.append({
                "fault_code": fault_code,
                "component": "Bus Threading",
                "error": str(e),
                "test": "Threading Error"
            })
            print(f"[FAULT] {fault_code} - Threading error: {str(e)}")
        
    except Exception as e:
        fault_code = f"Bus-1-90-{traceback.extract_tb(e.__traceback__)[-1].lineno}"
        all_fault_codes.append({
            "fault_code": fault_code,
            "component": "System Startup",
            "error": str(e),
            "test": "System Startup Error"
        })
        print(f"[FAULT] {fault_code} - System startup error: {str(e)}")
    
    # Report Results
    print("\n" + "=" * 100)
    print("COMPREHENSIVE FAULT CODE ANALYSIS REPORT")
    print("=" * 100)
    
    if all_fault_codes:
        print(f"Total fault codes captured: {len(all_fault_codes)}")
        print("\nAll Fault Codes Detected:")
        for i, fault in enumerate(all_fault_codes, 1):
            print(f"{i:2d}. {fault['fault_code']} - {fault['component']} - {fault['test']}")
            print(f"    Error: {fault['error']}")
    else:
        print("[OK] No fault codes detected - System is running perfectly!")
    
    print(f"\nTest completed at: {datetime.now().isoformat()}")
    return all_fault_codes

if __name__ == "__main__":
    print("Starting Comprehensive Fault Code Detection Test...")
    
    # Run comprehensive test
    all_faults = comprehensive_fault_test()
    
    print("\n" + "=" * 100)
    print("FINAL COMPREHENSIVE FAULT CODE SUMMARY")
    print("=" * 100)
    
    if all_faults:
        print(f"Total fault codes captured: {len(all_faults)}")
        print("\nFault Code Categories:")
        
        # Group by component
        components = {}
        for fault in all_faults:
            component = fault['component']
            if component not in components:
                components[component] = []
            components[component].append(fault)
        
        for component, faults in components.items():
            print(f"\n{component}:")
            for fault in faults:
                print(f"  - {fault['fault_code']} - {fault['test']}")
    else:
        print("[OK] No fault codes detected - System is running perfectly!")
    
    print("\nComprehensive test completed successfully!")

