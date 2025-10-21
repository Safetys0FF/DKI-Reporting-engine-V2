"""
Test Warden Module self-test.
Should validate Ecosystem Controller (2-2) and Gateway Controller (2-3).
"""
import sys
import time
import logging

# Configure logging to see self-test output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from warden_module import Warden

def test_warden_self_test():
    """
    Instantiate Warden Module and run self-test.
    Should validate Ecosystem Controller (2-2) and Gateway Controller (2-3).
    """
    print("\n" + "="*60)
    print("TEST: Warden Module Self-Test")
    print("="*60)
    
    print("\n[TEST] Initializing Warden Module...")
    print("[TEST] Expected: Self-test should validate Ecosystem Controller and Gateway Controller\n")
    
    warden = Warden()
    
    # Run lifecycle start (triggers self-test)
    print("[TEST] Starting Warden (triggers self-test)...")
    operational = warden.start()
    
    print(f"\n[TEST] Warden self-test result: {'PASSED' if operational else 'FAILED'}")
    
    # Wait for fault to be processed
    print("\n[TEST] Waiting 2 seconds for UDS to receive any faults...")
    time.sleep(2)
    
    # Stop Warden
    warden.stop()
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("Expected in logs above:")
    print("  - [2-1] Self-test PASSED: Ecosystem Controller (2-2) operational")
    print("  - [2-1] Self-test PASSED: Gateway Controller (2-3) operational")
    print("  - [2-1] PASS - Self-test COMPLETE")
    print("="*60 + "\n")
    
    return operational

if __name__ == "__main__":
    result = test_warden_self_test()
    sys.exit(0 if result else 1)


