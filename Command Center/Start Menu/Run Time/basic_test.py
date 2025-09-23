#!/usr/bin/env python3
print("Starting Central Command Smoke Test...")

try:
    import sys
    sys.path.append(r"F:\The Central Command\The Warden")
    from warden_main import Warden
    print("SUCCESS: Warden imported")
    
    warden = Warden()
    print("SUCCESS: Warden created")
    
    warden.start_warden()
    print("SUCCESS: Warden started")
    
    print("ALL TESTS PASSED!")
    
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()


