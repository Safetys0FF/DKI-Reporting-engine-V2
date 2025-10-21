#!/usr/bin/env python3
"""Run synthetic section smoke tests using bundled JSON payloads."""
from __future__ import annotations

import json
import copy
import traceback
from pathlib import Path
from datetime import datetime
import sys

DEV_TRACKING_DIR = Path(__file__).resolve().parents[1]
if str(DEV_TRACKING_DIR) not in sys.path:
    sys.path.insert(0, str(DEV_TRACKING_DIR))

from path_bootstrap import bootstrap_paths

REPO_ROOT = bootstrap_paths(__file__)
app_dir = REPO_ROOT / 'app'
gateway_dir = REPO_ROOT / 'Gateway'
for entry in (app_dir, gateway_dir, REPO_ROOT):
    entry_str = str(entry)
    if entry_str not in sys.path:
        sys.path.insert(0, entry_str)

import importlib.util

module_path = app_dir / 'gateway_controller.py'
spec = importlib.util.spec_from_file_location('bundle_gateway_controller', module_path)
gateway_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gateway_module)
GatewayController = gateway_module.GatewayController

print(f"Using gateway_controller from {gateway_module.__file__}")

BUNDLES_DIR = REPO_ROOT / 'Tests' / '_tust bundles'
OUTPUT_DIR = REPO_ROOT / 'dev_tracking' / 'logs'


def load_json(name: str) -> dict:
    data_path = BUNDLES_DIR / name
    with data_path.open('r', encoding='utf-8') as handle:
        return json.load(handle)


def build_mileage_segments(entries):
    segments = []
    for item in entries:
        segments.append({
            'origin': item['origin'],
            'destination': item['destination'],
            'logged_miles': item['miles'],
            'expected_miles': item['miles'],
            'variance': 0.0,
            'timestamp': item['timestamp'],
        })
    return segments


def build_sessions(entries):
    sessions = []
    for idx, item in enumerate(entries, start=1):
        sessions.append({
            'session_id': f'session_{idx}',
            'start': item['timestamp'],
            'end': item['timestamp'],
            'origin': item['origin'],
            'destination': item['destination'],
            'variance_miles': 0.0,
            'status': 'aligned',
        })
    return sessions


def build_documents(legal_text: dict) -> tuple[dict, dict]:
    contracts = {}
    forms = {}
    for key, text in legal_text.items():
        entry = {
            'text': text,
            'file_info': {'name': f'{key}.txt', 'path': str((BUNDLES_DIR / f'{key}.txt').resolve())},
            'metadata': {
                'record_type': key.replace('_', ' ').title(),
                'created_time': '2025-05-12',
                'jurisdiction': 'Franklin County, OH',
            },
        }
        if 'contract' in key or 'agreement' in key:
            contracts[key] = entry
        else:
            forms[key] = entry
    return contracts, forms


def build_media_assets(media_payload: dict) -> tuple[dict, dict]:
    images = {}
    videos = {}
    for item in media_payload.get('filename_only', []):
        images[item['filename']] = {
            'file_info': {'name': item['filename'], 'path': str((BUNDLES_DIR / item['filename']).resolve())},
            'captured_at': item['timestamp'],
            'notes': 'Observed subject activity',
        }
    for block in media_payload.get('metadata_blocks', []):
        container = images if block['filename'].lower().endswith(('.png', '.jpg', '.jpeg')) else videos
        container[block['filename']] = {
            'file_info': {'name': block['filename'], 'path': str((BUNDLES_DIR / block['filename']).resolve())},
            'captured_at': block['timestamp'],
            'metadata': {k: v for k, v in block.items() if k not in {'filename', 'timestamp'}},
        }
    return images, videos


def build_timeline(entries, media_names):
    timeline = []
    for idx, item in enumerate(entries, start=1):
        timeline.append({
            'id': f'event_{idx}',
            'timestamp': item['timestamp'],
            'event': f"Travel from {item['origin']} to {item['destination']}",
            'distance_miles': item['miles'],
            'related_media': media_names[:2],
        })
    return timeline


def make_toolkit_results(scenario_name: str, mileage_segments, sessions, billing_cycle):
    total_miles = sum(seg['logged_miles'] for seg in mileage_segments)
    return {
        'mileage_check': {
            'status': 'ok',
            'total_miles': round(total_miles, 2),
            'entries': mileage_segments,
        },
        'northstar_analysis': {
            'classified': [
                {'id': seg['origin'], 'classification': 'PRE-SURVEILLANCE'}
                for seg in mileage_segments
            ] + [
                {'id': seg['destination'], 'classification': 'SURVEILLANCE RETURN'}
                for seg in mileage_segments
            ],
            'deadfile_registry': [],
        },
        'billing_validation': {
            'scenario': billing_cycle['type'],
            'contracts_total': billing_cycle['contracts'],
            'surveillance_total': billing_cycle['surveillance'],
            'grand_total': billing_cycle['total'],
            'warnings': [],
            'issues': [],
        },
        'cochran_result': {
            'verified': True,
            'notes': f'Subject identity verified for {scenario_name}.',
        },
        'metadata': {
            'tags': ['leasing', 'fraud', scenario_name],
            'summary_tags': ['investigation', 'surveillance'],
            'agency': {'logo_path': 'assets/branding/dki_logo.png'},
        },
        'continuity_check': {
            'status': 'success',
            'ok': True,
            'sessions': sessions,
        },
        'osint_verification': {
            'status': 'verified',
            'entities': ['Matthew Harris', 'Maria Huerta'],
        },
    }


def make_processed_data(mileage_entries, legal_docs, media_payload, billing_cycle):
    contracts, forms = build_documents(legal_docs)
    images, videos = build_media_assets(media_payload)
    timeline = build_timeline(mileage_entries, list(images.keys()) + list(videos.keys()))
    mileage_segments = build_mileage_segments(mileage_entries)

    processed = {
        'text': '\n\n'.join(legal_docs.values()),
        'contracts': contracts,
        'forms': forms,
        'files': {f'file_{idx}': {'text': entry['event']} for idx, entry in enumerate(timeline, start=1)},
        'images': images,
        'videos': videos,
        'audio': {
            'voice_memo_1': {
                'file_info': {'name': 'voice_memo_1.wav', 'path': str((BUNDLES_DIR / 'voice_memo_1.wav').resolve())},
                'summary': 'Investigator notes on subject meeting.',
                'duration': '00:01:45',
                'transcription': {'text': 'Subject met with potential tenant at coffee shop.', 'language': 'en', 'generated_at': '2025-08-21T19:00:00Z'},
            }
        },
        'manual_notes': {
            'prep_plan': ['Verify permits', 'Brief team on rotation', 'Configure vehicle cameras'],
            'resource_assignments': [
                {'investigator': 'Agent Alpha', 'shift': '0600-1400', 'task': 'Morning coverage'},
                {'investigator': 'Agent Bravo', 'shift': '1400-2200', 'task': 'Evening follow-up'},
            ],
            'risk': ['Neighbor awareness increases exposure risk', 'Night visibility requires IR optics'],
            'logs': [f"{event['timestamp']} - {event['event']}" for event in timeline],
            'tactics': ['Two-vehicle rolling surveillance', 'Static camera at parking lot'],
            'issues': ['Minor GPS drift recorded', 'Evening fog reduced video clarity'],
            'custody': 'Evidence stored on encrypted drive with daily hashes.',
            'objective_status': [{'objective': 'Observe fraudulent leasing', 'status': 'in-progress'}],
            'findings': ['Subject presented lease documents to unsuspecting buyer.'],
            'recommendations': ['Coordinate undercover meeting with prospective tenant.'],
            'expenses': [
                {'item': 'Fuel', 'amount': 42.35, 'evidence': 'receipt_fuel_0821.jpg'},
                {'item': 'Meals', 'amount': 18.50, 'evidence': 'receipt_meal_0821.jpg'},
            ],
            'subcontractor_invoices': [{'vendor': 'CovertOps LLC', 'amount': 325.00, 'status': 'pending approval'}],
            'validation': [{'evidence_id': key, 'status': 'validated'} for key in images.keys()],
            'routing': {key: ['section_3', 'section_8'] for key in images.keys()},
            'attachments': ['surveillance_plan.pdf', 'credential_scan.png'],
        },
        'metadata': {
            'client_info': {
                'client_name': 'Maria Huerta',
                'client_phone': '(614) 555-4922',
                'client_address': '4217 Briarwood Ln, Columbus, OH 43228',
            },
            'client_profile': {
                'cover_logo_path': 'assets/branding/dki_logo.png',
                'signature_path': 'assets/branding/signature.png',
                'mailing_address': 'PO Box 120, Columbus, OH 43216',
            },
            'compliance_flags': ['All activities logged for Franklin County, OH'],
            'equipment_ready': ['Vehicle kit', 'Covert cameras', 'Audio recorder'],
            'location_tracks': [
                {'lat': 39.9612, 'lon': -82.9988, 'timestamp': entries['timestamp']}
                for entries in mileage_entries
            ],
            'environmental': 'Temperatures mid-80s, humidity high, evening fog on 08-23.',
            'reports': {'hashes': [{'file': key, 'md5': 'stub-md5'} for key in contracts.keys()]},
        },
        'summary': {
            'time_entries': [
                {'date': '2025-08-21', 'hours': 4.5, 'activity': 'Day surveillance'},
                {'date': '2025-08-22', 'hours': 6.0, 'activity': 'Evening follow-up'},
            ],
            'mileage_total': sum(item['miles'] for item in mileage_entries),
        },
        'media_analysis': {
            'dashcam_clip_01.mp4': {'highlights': 'Subject enters store, timestamp 00:01:32'},
        },
        'timeline': timeline,
        'scan_results': {f'scan_{idx}': {'event': entry['event'], 'timestamp': entry['timestamp']} for idx, entry in enumerate(timeline, start=1)},
        'processing_log': [
            {'timestamp': entries['timestamp'], 'operation': 'timeline_event', 'status': 'recorded'}
            for entries in mileage_entries
        ],
    }
    return processed, mileage_segments


def make_case_data(base_case: dict, scenario_name: str) -> dict:
    case = copy.deepcopy(base_case)
    case['case_id'] = f"{scenario_name.upper()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    case['preparation_plan'] = ['Verify permits', 'Schedule surveillance vehicles', 'Configure evidence intake']
    case['assignments'] = [
        {'investigator': 'Agent Alpha', 'role': 'Lead', 'shift': '0600-1400'},
        {'investigator': 'Agent Bravo', 'role': 'Support', 'shift': '1400-2200'},
    ]
    case['risk_matrix'] = [{'risk': 'Exposure by neighbors', 'mitigation': 'Limit stakeout duration'}]
    case['objectives'] = ['Document fraudulent leasing activity', 'Identify accomplices']
    case['investigation_goals'] = case['objectives']
    case['subjects'] = [{'name': 'Matthew Harris', 'role': 'Primary subject'}]
    case['jurisdiction'] = 'Franklin County, OH'
    case['objective_status'] = [{'objective': 'Observe handoff of documents', 'status': 'in-progress'}]
    case['recommendations'] = ['Coordinate with client counsel before confronting subject.']
    case['distribution_list'] = ['maria.huerta@example.com', 'legal@dkiservices.com']
    case['delivery_instructions'] = 'Deliver via secure portal within 24 hours of approval.'
    case['acknowledgment'] = 'Client signature required prior to release.'
    case['appendices'] = ['contract_standard', 'renters_addendum']
    case['compliance_flags'] = {'licensing': 'OK', 'privacy': 'No medical surveillance'}
    case['contract'] = {
        'title': 'Investigative Services Agreement',
        'effective_date': '2025-05-12',
        'client': case['client_info']['client_name'],
    }
    case['export_settings'] = {'formats': ['docx', 'pdf'], 'watermark': 'CONFIDENTIAL'}
    case['legal'] = {
        'disclosures': ['This report is confidential and intended for the client named.'],
        'disclaimers': ['All observations are accurate to the best of our knowledge at time of reporting.'],
    }
    return case


def build_scenarios():
    mileage_payload = load_json('mileage_test_payload.json')
    legal_payload = load_json('legal_docs_test_payload.json')
    billing_payload = load_json('billing_cycle_scenarios.json')['billing_cycles']
    media_payload = load_json('media_test_payload.json')

    scenarios = []
    scenario_defs = [
        ('simple_route', mileage_payload['simple'][:2], {'contract_standard': legal_payload['contract_standard']}, billing_payload[0], {'filename_only': media_payload['filename_only']}),
        ('renters_focus', mileage_payload['simple'][1:], {'renters_addendum': legal_payload['renters_addendum']}, billing_payload[1], {'filename_only': media_payload['filename_only'][::-1]}),
        ('surveillance_only', mileage_payload['simple'], {'subcontractor_agreement': legal_payload['subcontractor_agreement']}, billing_payload[2], {'metadata_blocks': media_payload['metadata_blocks']}),
        ('intake_review', mileage_payload['simple'] + [
            {
                'origin': mileage_payload['stress_test']['structure']['trip_1']['from'],
                'destination': mileage_payload['stress_test']['structure']['trip_1']['to'],
                'miles': mileage_payload['stress_test']['structure']['trip_1']['miles'],
                'timestamp': mileage_payload['stress_test']['timestamp'],
            }
        ], {'intake_form': legal_payload['intake_form']}, billing_payload[3], media_payload),
    ]

    base_case = {
        'client_info': {
            'client_name': 'Maria Huerta',
            'client_phone': '(614) 555-4922',
            'client_address': '4217 Briarwood Ln, Columbus, OH 43228',
        },
        'client_profile': {
            'cover_logo_path': 'assets/branding/dki_logo.png',
            'signature_path': 'assets/branding/signature.png',
            'profile_photo_path': 'assets/branding/profile.png',
        },
        'contract_type': 'Investigative',
        'contract_date': '2025-05-12',
        'assigned_investigator': 'David Krashin',
        'investigator_license': '0163814-C000480',
        'agency_name': 'DKI Services LLC',
        'agency_license': '0200812-IA000307',
    }

    for name, mileage_entries, legal_docs, billing_cycle, media in scenario_defs:
        processed_data, mileage_segments = make_processed_data(mileage_entries, legal_docs, media, billing_cycle)
        sessions = build_sessions(mileage_entries)
        toolkit_results = make_toolkit_results(name, mileage_segments, sessions, billing_cycle)
        case_data = make_case_data(base_case, name)
        scenarios.append({
            'name': name,
            'case_data': case_data,
            'processed_data': processed_data,
            'toolkit_results': toolkit_results,
        })
    return scenarios


def run_scenario(controller: GatewayController, scenario: dict, report_type: str) -> dict:
    controller.reset_gateway()
    controller.initialize_case(report_type, scenario['case_data'])

    def fake_run_all(section_id, text_data, report_meta, documents, assets):
        return copy.deepcopy(scenario['toolkit_results'])

    controller.toolkit_engine.run_all = fake_run_all

    outputs = {}
    for section_id, section_name in controller.report_types[report_type]['sections']:
        try:
            section_result = controller.generate_section(section_name, copy.deepcopy(scenario['processed_data']), report_type)
            manifest = section_result.get('render_data', {}).get('manifest', {}) if isinstance(section_result, dict) else {}
            outputs[section_id] = {
                'status': controller.section_states.get(section_id).value,
                'manifest': manifest,
                'preview': section_result.get('content', '')[:160] if isinstance(section_result, dict) else '',
            }
        except Exception as exc:
            print(f'Section generation failed for {section_name}: {exc}')
            print(traceback.format_exc())
            outputs[section_id] = {'status': 'failed', 'error': str(exc)}
    return outputs


def main():
    scenarios = build_scenarios()
    controller = GatewayController()
    # Stub media processing to avoid hard dependencies on actual media assets
    controller.media_engine.process_media_file = lambda file_path, *_, **__: {
        'file_info': {
            'path': file_path,
            'created': datetime.now().isoformat(),
        }
    }
    report_type = 'Investigative'
    summary = {}

    for scenario in scenarios:
        outputs = run_scenario(controller, scenario, report_type)
        summary[scenario['name']] = outputs

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_path = OUTPUT_DIR / f'SECTION_SMOKE_RESULTS_{timestamp}.json'
    out_path.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))
    print(f'Wrote section smoke results to {out_path}')


if __name__ == '__main__':
    main()
