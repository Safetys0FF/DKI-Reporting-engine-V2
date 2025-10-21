#!/usr/bin/env python3
"""
Test section fault propagation through Marshall to UDS.
Tests that Section 1's broken Tesseract engine is detected and reported.
"""
import sys
import time
import logging
from pathlib import Path

# Add necessary paths
project_root = Path(__file__).resolve().parents[3]
command_center = project_root / "Command Center"
data_bus = command_center / "Data Bus"
bus_core = data_bus / "Bus Core Design"
analyst_deck = project_root / "The Analyst Deck"
marshall_path = project_root / "The Marshall"

sys.path.insert(0, str(bus_core))
sys.path.insert(0, str(data_bus))
sys.path.insert(0, str(analyst_deck))
sys.path.insert(0, str(marshall_path))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

print("=" * 80)
print("SECTION FAULT PROPAGATION TEST")
print("=" * 80)
print()

print("[1/4] Initializing CANBUS...")
from bus_core import DKIReportBus
bus = DKIReportBus()
print("[OK] CANBUS initialized")
print()

print("[2/4] Initializing Marshall Module...")
from marshall_module import MarshallModule
marshall = MarshallModule(bus=bus)
marshall.start()
print("[OK] Marshall initialized")
print()

print("[3/4] Initializing Section 1 (with broken Tesseract)...")
sys.path.insert(0, str(analyst_deck / "Analyst 1"))
from section_1_framework import Section1Framework

# Section 1 will emit fault for broken Tesseract during __init__
section_1 = Section1Framework(gateway=None, marshal_client=marshall)
print("[OK] Section 1 initialized (fault should be emitted)")
print()

print("[4/4] Checking for fault emission...")
time.sleep(2)  # Allow fault propagation

# Check logs for fault codes
print()
print("=" * 80)
print("TEST RESULT:")
print("=" * 80)
print("Expected fault code: [4-1.8-12-INIT] (Section 1 Tesseract Engine initialization failure)")
print()
print("Check logs above for:")
print("  1. Section 1 self-test FAILED for Tesseract (4-1.8)")
print("  2. Marshall received initialization_failure")
print("  3. Marshall relayed fault to UDS (Bus-1) with SOS")
print()
print("If all three appear, fault propagation is working correctly.")
print("=" * 80)

