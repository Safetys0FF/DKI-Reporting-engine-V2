# Change Log Summary – 2025-09-18

## Highlighted Entries

- **2025-09-18** · document_processor.py
  - Added process_file(...) wrapper and _infer_file_type(...) helper so any component can process a single document without assembling the bulk list structure.
  - Impact: consistent metadata normalization for GUI, automation, and test harnesses.

- **2025-09-18** · dev_tracking/path_bootstrap.py
  - Introduced ootstrap_paths helper used by DevTracking tools to append the repo root to sys.path before importing engine modules.
  - Scripts updated to call the helper:
    - dev_tracking/tools/ai_osint_readiness.py
    - dev_tracking/tools/e2e_smoke.py
    - dev_tracking/tools/import_keys_to_profile.py
    - dev_tracking/agent_1_POWER_CODING/smoke_harness.py
    - dev_tracking/agent_1_POWER_CODING/export_rtf_smoke.py
    - dev_tracking/agent_1_POWER_CODING/run_section_smoke_all.py
  - Impact: DevTracking utilities now run via python dev_tracking/... without manual PYTHONPATH overrides.

## Operational Notes

- Tests executed after the updates:
  - python dev_tracking/tools/e2e_smoke.py
  - python dev_tracking/tools/ai_osint_readiness.py
  - python dev_tracking/tools/import_keys_to_profile.py --help
  - python dev_tracking/agent_1_POWER_CODING/run_section_smoke_all.py (still blocked by missing UserProfileManager.save_api_key routine; helper loads correctly.)
- Detailed narrative recorded in dev_tracking/agent_1_POWER_CODING/CHANGE_SUMMARY_2025-09-18.md and dev_tracking/Handshakes/HANDSHAKE_2025-09-18_POWER_Path_Bootstrap.md.