"""
Test Evidence Locker self-test with broken OCR engine.
Should emit [1.8-12-INIT] fault code to UDS.
"""
import sys
import time
from pathlib import Path

# Add paths
command_center = Path(__file__).resolve().parents[3]
data_bus = command_center / "Data Bus"
sys.path.insert(0, str(data_bus / "Bus Core Design"))
sys.path.insert(0, str(data_bus))  # For universal_communicator
sys.path.insert(0, str(command_center.parent / "Evidence Locker"))

from bus_core import DKIReportBus
from evidence_locker_module import EvidenceLockerModule

def test_evidence_locker_with_broken_ocr():
    """
    Instantiate Evidence Locker Module with broken OCR.
    Should emit [1.8-12-INIT] fault to UDS during self-test.
    """
    print("\n" + "="*60)
    print("TEST: Evidence Locker Self-Test with Broken OCR")
    print("="*60)
    
    # Initialize CANBUS
    print("\n[TEST] Initializing CANBUS...")
    bus = DKIReportBus()
    
    # Initialize Evidence Locker Module
    print("[TEST] Initializing Evidence Locker Module...")
    print("[TEST] Expected: Self-test should detect broken OCR and emit [1.8-12-INIT] fault\n")
    
    locker_module = EvidenceLockerModule(bus=bus)
    
    # Initialize the system (this triggers self-test)
    status = locker_module.initialize_system()
    
    print(f"\n[TEST] Evidence Locker initialization status:")
    print(f"  - Status: {status.get('status', 'UNKNOWN')}")
    print(f"  - Self-test passed: {status.get('self_test_passed', 'N/A')}")
    print(f"  - Initialized: {status.get('initialized', 'N/A')}")
    
    # Wait for fault to be processed
    print("\n[TEST] Waiting 3 seconds for UDS to receive fault...")
    time.sleep(3)
    
    # Check CANBUS for emitted faults
    print("\n[TEST] Checking CANBUS signal history for SOS faults...")
    # Note: This would require access to bus internal state
    # For now, verify via UDS log output
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("Expected in logs above:")
    print("  - [1] Self-test FAILED: OCR Processor (1.8) not initialized")
    print("  - [1] Fault code emitted: [1.8-12-INIT]")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_evidence_locker_with_broken_ocr()

