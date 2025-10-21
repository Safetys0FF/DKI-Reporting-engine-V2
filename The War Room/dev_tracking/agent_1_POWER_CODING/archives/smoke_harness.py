#!/usr/bin/env python3
"""
Smoke Harness for POWER Agent
- API key system E2E: create user, save/retrieve keys, confirm roundtrip
- Auto report-type detection: exercise None/auto paths and cues
- Minimal section generation for CP/TOC/Section 1 and signal verification
"""
from __future__ import annotations

import os
import json
from pathlib import Path
from datetime import datetime
import sys

DEV_TRACKING_DIR = Path(__file__).resolve().parents[1]
if str(DEV_TRACKING_DIR) not in sys.path:
    sys.path.insert(0, str(DEV_TRACKING_DIR))

from path_bootstrap import bootstrap_paths

REPO_ROOT = bootstrap_paths(__file__)

from repository_manager import RepositoryManager
from user_profile_manager import UserProfileManager
from gateway_controller import GatewayController



def api_keys_e2e() -> dict:
    repo = RepositoryManager()
    db_path = os.path.join(str(repo.repo_root), 'user_profiles.db')
    upm = UserProfileManager(db_path)

    username = 'smokeuser'
    password = 'Sm0kePass!'

    # Create user if not exists
    upm.create_user(username, password, email='smoke@example.com', full_name='Smoke User', company='DKI', license_number='TEST-0000')
    assert upm.authenticate_user(username, password), 'Authentication failed for smokeuser'

    # Save and retrieve API keys
    test_key = f"test_key_{datetime.now().strftime('%H%M%S')}"
    upm.save_api_key('google_maps_api', test_key)
    keys = upm.get_api_keys()
    ok = keys.get('google_maps_api') == test_key
    return {
        'db_path': db_path,
        'keys_count': len(keys),
        'roundtrip_ok': ok,
    }



def auto_detect_validation() -> dict:
    gc = GatewayController()
    results = {}

    cases = {
        'investigative': {'contract_type': 'Investigative', 'investigation_goals': 'desk analysis only'},
        'field': {'contract_type': 'Field', 'investigation_goals': 'surveillance and tail'},
        'hybrid': {'contract_type': 'Hybrid', 'investigation_goals': 'investigative and in-field verification'},
        'ambiguous': {'investigation_goals': 'review'}
    }

    for name, data in cases.items():
        init = gc.initialize_case(None, data)
        results[name] = init['report_type']

    return results



def minimal_section_generation() -> dict:
    gc = GatewayController()
    case = {
        'contract_type': 'Investigative',
        'client_name': 'Client X',
        'contract_date': '2025-01-01',
        'assigned_investigator': 'David Krashin',
        'investigator_license': '0163814-C000480',
        'agency_name': 'DKI Services LLC',
        'agency_license': '0200812-IA000307',
        'investigation_goals': 'desk analysis',
    }
    gc.initialize_case(None, case)
    processed = {}
    # Generate CP, TOC, and Section 1 by friendly names used in controller map
    seq = ["Cover Page", "Table of Contents", "Investigation Objectives"]
    for name in seq:
        try:
            gc.generate_section(name, processed, gc.current_report_type)
        except Exception:
            # Non-fatal for smoke harness
            pass
    return {
        'signals': gc.get_signal_queue(),
        'processing_log_count': len(gc.get_processing_log()),
        'section_states': gc.get_section_status(),
    }



def main():
    report = {
        'api_e2e': api_keys_e2e(),
        'auto_detect': auto_detect_validation(),
        'sections': minimal_section_generation(),
    }
    out = REPO_ROOT / 'dev_tracking' / 'SMOKE_RUN_RESULTS.json'
    out.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
