#!/usr/bin/env python3
"""
Test API Integration - Verify Central Plugin and Data Bus API functionality
"""

import sys
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
START_MENU_RUNTIME = ROOT_DIR / "Start Menu" / "Run Time"
if str(START_MENU_RUNTIME) not in sys.path:
    sys.path.insert(0, str(START_MENU_RUNTIME))

DATA_BUS_PATH = ROOT_DIR / "Data Bus"
if str(DATA_BUS_PATH) not in sys.path:
    sys.path.insert(0, str(DATA_BUS_PATH))

CANDIDATE_TOOL_PATHS = [
    ROOT_DIR.parent / "The War Room" / "Processors",
    ROOT_DIR.parent / "Tool kit",
    ROOT_DIR / "Mission Debrief" / "tools",
]
for candidate in CANDIDATE_TOOL_PATHS:
    if candidate.exists():
        candidate_str = str(candidate)
        if candidate_str not in sys.path:
            sys.path.insert(0, candidate_str)

import sys
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
START_MENU_RUNTIME = ROOT_DIR / "Start Menu" / "Run Time"
if str(START_MENU_RUNTIME) not in sys.path:
    sys.path.insert(0, str(START_MENU_RUNTIME))

DATA_BUS_PATH = ROOT_DIR / "Data Bus"
if str(DATA_BUS_PATH) not in sys.path:
    sys.path.insert(0, str(DATA_BUS_PATH))

CANDIDATE_TOOL_PATHS = [
    ROOT_DIR.parent / "The War Room" / "Processors",
    ROOT_DIR.parent / "Tool kit",
    ROOT_DIR / "Mission Debrief" / "tools",
]
for candidate in CANDIDATE_TOOL_PATHS:
    if candidate.exists():
        candidate_str = str(candidate)
        if candidate_str not in sys.path:
            sys.path.insert(0, candidate_str)

