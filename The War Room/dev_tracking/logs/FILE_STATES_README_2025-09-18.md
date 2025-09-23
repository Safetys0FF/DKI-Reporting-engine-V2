# File States Snapshot – 2025-09-18

Files touched during the path bootstrap rollout are now tracked with fresh metadata:

| File | Size (bytes) | Last Modified (local) | Notes |
|------|--------------|-----------------------|-------|
| dev_tracking/path_bootstrap.py | 1417 | 2025-09-18 11:10:57 | New helper that injects the repo root on sys.path. |
| dev_tracking/tools/ai_osint_readiness.py | 1861 | 2025-09-18 11:09:04 | Updated to import ootstrap_paths. |
| dev_tracking/tools/e2e_smoke.py | 3289 | 2025-09-18 11:08:40 | End-to-end smoke now runs without manual env setup. |
| dev_tracking/tools/import_keys_to_profile.py | 6386 | 2025-09-18 11:09:21 | Key importer gains automatic path bootstrapping. |
| dev_tracking/agent_1_POWER_CODING/smoke_harness.py | 3690 | 2025-09-18 11:10:15 | POWER smoke harness uses shared helper. |
| dev_tracking/agent_1_POWER_CODING/export_rtf_smoke.py | 3300 | 2025-09-18 11:09:37 | RTF/DOCX/PDF export script updated. |
| dev_tracking/agent_1_POWER_CODING/run_section_smoke_all.py | 3414 | 2025-09-18 11:09:52 | Section smoke runner bootstraps paths; still relies on future save_api_key work. |

> The JSON log files remain the system of record for automation, but this table provides human-readable context for the architect and other agents.
