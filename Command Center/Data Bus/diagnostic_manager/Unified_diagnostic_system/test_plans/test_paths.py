#!/usr/bin/env python3
"""
Test script to verify path configuration and test plan access
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from __init__ import UnifiedDiagnosticSystem
    
    print("Creating Unified Diagnostic System...")
    uds = UnifiedDiagnosticSystem()
    
    # Check paths
    print("\n=== PATH VERIFICATION ===")
    print(f"Base Path: {uds.core.base_path}")
    print(f"Test Plans Path: {uds.core.test_plans_path}")
    print(f"Test Plans Exists: {uds.core.test_plans_path.exists()}")
    print(f"Test Plans Main Path: {uds.core.test_plans_main_path}")
    print(f"Test Plans Main Exists: {uds.core.test_plans_main_path.exists()}")
    
    # List test plan directories
    if uds.core.test_plans_main_path.exists():
        print(f"\n=== AVAILABLE TEST PLAN SYSTEMS ===")
        for item in uds.core.test_plans_main_path.iterdir():
            if item.is_dir():
                print(f"  {item.name}")
    
    # Test loading a specific test plan
    print(f"\n=== TEST PLAN LOADING TEST ===")
    test_plan = uds.core.load_test_plan("1-1.1", "smoke_test")
    if test_plan:
        print(f"Successfully loaded test plan for 1-1.1")
        print(f"Test plan keys: {list(test_plan.keys())}")
    else:
        print(f"Failed to load test plan for 1-1.1")
    
    # Test system registry loading
    print(f"\n=== SYSTEM REGISTRY TEST ===")
    registry_file = uds.core.test_plans_path / "system_registry.json"
    print(f"Registry file exists: {registry_file.exists()}")
    
    if registry_file.exists():
        import json
        with open(registry_file, 'r') as f:
            registry = json.load(f)
        print(f"Registry loaded with {len(registry.get('system_registry', {}).get('connected_systems', {}))} systems")
    
    print("\n=== TEST COMPLETE ===")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
