"""
Test Marshall Module self-test.
Should validate Evidence Manager (3-1).
"""
import sys
import time
import logging
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent / "Command Center" / "Data Bus" / "Bus Core Design"))
sys.path.insert(0, str(Path(__file__).parent.parent / "Command Center" / "Data Bus"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from marshall_module import MarshallModule
from bus_core import DKIReportBus

def test_marshall_self_test():
    """
    Instantiate Marshall Module and run self-test.
    Should detect missing Evidence Manager (3-1).
    """
    print("\n" + "="*60)
    print("TEST: Marshall Module Self-Test")
    print("="*60)
    
    print("\n[TEST] Initializing CANBUS...")
    bus = DKIReportBus()
    
    print("[TEST] Initializing Marshall Module...")
    print("[TEST] Expected: Self-test should detect missing Evidence Manager\n")
    
    marshall = MarshallModule(bus=bus)
    
    # Run lifecycle start (triggers self-test)
    print("[TEST] Starting Marshall (triggers self-test)...")
    operational = marshall.start()
    
    print(f"\n[TEST] Marshall self-test result: {'PASSED' if operational else 'FAILED'}")
    
    # Wait for fault to be processed
    print("\n[TEST] Waiting 2 seconds for UDS to receive any faults...")
    time.sleep(2)
    
    # Stop Marshall
    marshall.stop()
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("Expected in logs above:")
    print("  - [3] Self-test FAILED: Evidence Manager (3-1) not initialized")
    print("  - [3] Fault code emitted: [3-1-12-INIT]")
    print("  - [3] FAIL - Self-test COMPLETE")
    print("="*60 + "\n")
    
    return operational

if __name__ == "__main__":
    result = test_marshall_self_test()
    sys.exit(0 if result else 1)


