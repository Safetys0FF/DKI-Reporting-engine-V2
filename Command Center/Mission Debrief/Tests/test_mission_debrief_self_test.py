"""
Test Mission Debrief Module self-test.
Should validate Debrief Manager (5-1) and Librarian (5-2).
"""
import sys
import time
import logging
from pathlib import Path

# Add paths
mission_debrief_dir = Path(__file__).parent
command_center = mission_debrief_dir.parent
data_bus = command_center / "Data Bus"

sys.path.insert(0, str(data_bus / "Bus Core Design"))
sys.path.insert(0, str(data_bus))
sys.path.insert(0, str(mission_debrief_dir / "Debrief"))
sys.path.insert(0, str(mission_debrief_dir / "The Librarian"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from mission_debrief_module import MissionDebriefModule
from bus_core import DKIReportBus

def test_mission_debrief_self_test():
    """
    Instantiate Mission Debrief Module and run self-test.
    Should validate Debrief Manager (5-1) and Librarian (5-2).
    """
    print("\n" + "="*60)
    print("TEST: Mission Debrief Module Self-Test")
    print("="*60)
    
    print("\n[TEST] Initializing CANBUS...")
    bus = DKIReportBus()
    
    print("[TEST] Initializing Mission Debrief Module...")
    print("[TEST] Expected: Self-test should validate Debrief Manager and Librarian\n")
    
    # Initialize module (triggers self-test in __init__)
    mission_debrief = MissionDebriefModule(bus=bus)
    
    print("\n[TEST] Mission Debrief Module initialized")
    
    # Wait for fault to be processed
    print("\n[TEST] Waiting 2 seconds for UDS to receive any faults...")
    time.sleep(2)
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("Expected in logs above:")
    print("  - [5] Self-test PASSED: Debrief Manager (5-1) operational")
    print("  - [5] Self-test PASSED: Librarian (5-2) operational")
    print("  - [5] PASS - Self-test COMPLETE")
    print("="*60 + "\n")
    
    return True

if __name__ == "__main__":
    result = test_mission_debrief_self_test()
    sys.exit(0 if result else 1)


