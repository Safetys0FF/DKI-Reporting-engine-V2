#!/usr/bin/env python3
"""
Generate a minimal final report and export to RTF (dependency-light) using
currently available section outputs. This validates export pipeline without
requiring python-docx or reportlab.
"""
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import sys

DEV_TRACKING_DIR = Path(__file__).resolve().parents[1]
if str(DEV_TRACKING_DIR) not in sys.path:
    sys.path.insert(0, str(DEV_TRACKING_DIR))

from path_bootstrap import bootstrap_paths

bootstrap_paths(__file__)

from gateway_controller import GatewayController
from repository_manager import RepositoryManager
from user_profile_manager import UserProfileManager
from report_generator import ReportGenerator


def run():
    gc = GatewayController()

    # Attach authenticated user profile
    repo = RepositoryManager()
    upm = UserProfileManager(str(repo.repo_root / 'user_profiles.db'))
    try:
        upm.create_user('smokeuser', 'Sm0kePass!', email='smoke@example.com')
    except Exception:
        pass
    upm.authenticate_user('smokeuser', 'Sm0kePass!')
    try:
        gc.toolkit_engine.set_user_profile_manager(upm)
    except Exception:
        pass

    # Initialize a simple investigative case
    case = {
        'contract_type': 'Investigative',
        'client_name': 'Smoke Client',
        'contract_date': '2025-01-01',
        'assigned_investigator': 'David Krashin',
        'investigator_license': '0163814-C000480',
        'agency_name': 'DKI Services LLC',
        'agency_license': '0200812-IA000307',
        'investigation_goals': 'desk analysis',
    }
    init = gc.initialize_case(None, case)

    # Generate as many sections as possible with minimal data
    generated = []
    for _sid, name in init.get('sections', []):
        try:
            gc.generate_section(name, {}, gc.current_report_type)
            generated.append(name)
        except Exception:
            # Continue; export should handle partial content
            pass

    # Build final report from whatever completed sections exist
    gen = ReportGenerator()
    section_data = gc.section_outputs.copy()
    snapshot = gc.export_case_data()
    report = gen.generate_full_report({**section_data, "_case_meta": snapshot}, gc.current_report_type)

    # Export to RTF (no extra deps)
    exports_dir = repo.folders['exports']
    exports_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_rtf = exports_dir / f"smoke_report_{ts}.rtf"
    gen.export_rtf(report, str(out_rtf))
    print(f"Exported RTF: {out_rtf}")

    # Try DOCX export
    try:
        out_docx = exports_dir / f"smoke_report_{ts}.docx"
        gen.export_report(report, str(out_docx), 'docx')
        print(f"Exported DOCX: {out_docx}")
    except Exception as e:
        print(f"DOCX export skipped: {e}")

    # Try PDF export
    try:
        out_pdf = exports_dir / f"smoke_report_{ts}.pdf"
        gen.export_report(report, str(out_pdf), 'pdf')
        print(f"Exported PDF: {out_pdf}")
    except Exception as e:
        print(f"PDF export skipped: {e}")
    print(f"Sections generated: {len(generated)}")


if __name__ == '__main__':
    run()
