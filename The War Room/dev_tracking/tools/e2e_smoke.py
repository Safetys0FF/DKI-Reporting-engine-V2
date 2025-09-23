#!/usr/bin/env python3
"""
GatewayController end-to-end smoke for DEESCALATION QC
- Initializes a case
- Generates CP, TOC, Section 1, and Section 8 with a sample image
- Approves generated sections to exercise 10-4/10-8 flow
- Attempts final assembly (will succeed only if all content approved)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from pprint import pprint

DEV_TRACKING_DIR = Path(__file__).resolve().parents[1]
if str(DEV_TRACKING_DIR) not in sys.path:
    sys.path.insert(0, str(DEV_TRACKING_DIR))

from path_bootstrap import bootstrap_paths

bootstrap_paths(__file__)

from gateway_controller import GatewayController, SectionState


def ensure_test_image() -> str:
    p = Path('test_ocr_image.png')
    if not p.exists():
        try:
            from PIL import Image
            Image.new('RGB', (200, 100), 'white').save(p)
        except Exception:
            # Create an empty placeholder if PIL is unavailable
            p.write_bytes(b'')
    return str(p.resolve())


def main() -> int:
    case = {
        'client_name': 'QC Test Client',
        'contract_date': '2025-09-15',
        'assigned_investigator': 'Test Investigator',
        'investigator_license': '0163814-C000480',
    }

    gc = GatewayController()
    info = gc.initialize_case('Investigative', case)
    print('INIT:', info['report_type'], len(info['sections']))

    img_path = ensure_test_image()
    processed = {
        'files': {},
        'images': {'img1': {'file_info': {'path': img_path}}},
        'videos': {},
    }

    # Generate all sections defined for the report type, in order
    names = [name for _, name in info['sections']]
    for name in names:
        try:
            res = gc.generate_section(name, processed, info['report_type'])
            print('GENERATED:', res['section_id'], '| content_len=', len(res.get('content', '')))
            sid = res['section_id']
            gc.section_states[sid] = SectionState.COMPLETED
            gc.approve_section(name)
        except Exception as e:
            print('GEN_FAIL:', name, str(e))

    interesting = ['section_cp', 'section_toc', 'section_1', 'section_8']
    print('STATES:', {k: gc.section_states.get(k).value for k in interesting if k in gc.section_states})
    print('SIGNALS:', [s['type'] for s in gc.get_signal_queue()])

    # Attempt final assembly (will assemble if content sections approved)
    try:
        assembled = gc.final_assembly.assemble_final_report(info['report_type'], case)
        print('FINAL_ASSEMBLY_SECTIONS:', len(assembled.get('sections', [])))
    except Exception as e:
        print('FINAL_ASSEMBLY_FAIL:', str(e))

    # Error-path exercise: bad media path
    bad_processed = {
        'files': {},
        'images': {'bad1': {'file_info': {'path': str(Path('nonexistent.jpg').resolve())}}},
        'videos': {},
    }
    try:
        res = gc.generate_section('Investigation Evidence Review', bad_processed, info['report_type'])
        print('BAD_MEDIA_GENERATED:', res['section_id'])
    except Exception as e:
        print('BAD_MEDIA_ERROR:', str(e))

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
