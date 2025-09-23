#!/usr/bin/env python3
"""
Run a broader section smoke test to exercise:
- Section generation across the current report type sequence
- Signal emissions: 10-6 (toolkit), 10-8 (complete), 10-4 (approved), 10-9 (revision), 10-10 (halt)

Writes a concise JSON result to dev_tracking/SMOKE_RUN_RESULTS_EXTENDED.json
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
import sys

DEV_TRACKING_DIR = Path(__file__).resolve().parents[1]
if str(DEV_TRACKING_DIR) not in sys.path:
    sys.path.insert(0, str(DEV_TRACKING_DIR))

from path_bootstrap import bootstrap_paths

bootstrap_paths(__file__)

from gateway_controller import GatewayController, SignalType
from repository_manager import RepositoryManager
from user_profile_manager import UserProfileManager


def run():
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

    # Attach authenticated user profile to toolkit so user context and API keys flow
    repo = RepositoryManager()
    upm = UserProfileManager(str(repo.repo_root / 'user_profiles.db'))
    username = 'smokeuser'
    password = 'Sm0kePass!'
    try:
        upm.create_user(username, password, email='smoke@example.com', full_name='Smoke User')
    except Exception:
        pass
    upm.authenticate_user(username, password)
    upm.save_api_key('google_maps_api', f"test_key_{datetime.now().strftime('%H%M%S')}")
    # Attach to toolkit engine
    try:
        gc.toolkit_engine.set_user_profile_manager(upm)
    except Exception:
        pass

    init = gc.initialize_case(None, case)
    seq = init.get('sections', [])
    friendly_names = [name for (_sid, name) in seq]

    successes = []
    failures = []

    for name in friendly_names:
        try:
            gc.generate_section(name, {}, gc.current_report_type)
            successes.append(name)
        except Exception as e:
            failures.append({'section': name, 'error': str(e)})

    # Emit additional signals using public APIs
    try:
        if successes:
            gc.approve_section(successes[0])  # 10-4
        if len(successes) > 1:
            gc.request_revision(successes[1], feedback='Smoke: request revision sample')  # 10-9
    except Exception:
        pass

    # Emit a HALT as a final signal to confirm 10-10 appears in queue
    try:
        gc._emit_signal(SignalType.HALT, {'reason': 'smoke_test_halt'})  # Internal, for smoke only
    except Exception:
        pass

    result = {
        'timestamp': datetime.now().isoformat(),
        'generated': len(successes),
        'failed': len(failures),
        'failures': failures,
        'signals': gc.get_signal_queue(),
        'section_states': gc.get_section_status(),
        'processing_log_count': len(gc.get_processing_log()),
    }

    out = Path('dev_tracking/SMOKE_RUN_RESULTS_EXTENDED.json')
    out.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    run()
