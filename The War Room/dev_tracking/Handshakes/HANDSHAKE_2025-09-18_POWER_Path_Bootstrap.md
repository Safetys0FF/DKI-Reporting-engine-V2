# HANDSHAKE – POWER to NETWORK & DEESCALATION (Read-Only)

**Date**: 2025-09-18  
**From**: POWER Agent  
**To**: NETWORK & DEESCALATION Agents  
**Subject**: DevTracking path bootstrap helper

## Summary
- Added dev_tracking/path_bootstrap.py to inject the repo root onto sys.path for DevTracking utilities.
- Updated smoke tools (	ools/e2e_smoke.py, 	ools/ai_osint_readiness.py, 	ools/import_keys_to_profile.py) and POWER harnesses (gent_1_POWER_CODING/smoke_harness.py, export_rtf_smoke.py, un_section_smoke_all.py) to call ootstrap_paths(__file__) before importing engine modules.
- Scripts now run via python dev_tracking/... without exporting PYTHONPATH manually.

## Actions for Receiving Agents
- NETWORK: Use the helper when adding new DevTracking diagnostics or importers so path injection is consistent.
- DEESCALATION: When validating future smoke suites, confirm ootstrap_paths is present before raising PATH-related blockers.
- All agents: Reference dev_tracking/path_bootstrap.py for reuse; change summary logged in dev_tracking/agent_1_POWER_CODING/CHANGE_SUMMARY_2025-09-18.md.

## Verification Artifacts
- python dev_tracking/tools/e2e_smoke.py
- python dev_tracking/agent_1_POWER_CODING/run_section_smoke_all.py (noting existing UserProfileManager.save_api_key limitation)
