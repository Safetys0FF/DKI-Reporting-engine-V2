# F-Drive Root Reconfiguration Summary - 2025-09-19

## Scope
- Updated hard-coded F: drive references after root moved to F:\DKI-Report-Engine.
- Limited edits to Python modules, batch scripts, environment config, and JSON artifacts with broken import targets.

## Updates
- Media processing engines now fall back to F:/DKI-Report-Engine/Report Engine/Processors when importing MoviePy (app + legacy copies).
- Legacy profile-related tests and utilities now read/write from F:/DKI-Report-Engine/Report Engine/DKI_Repository and helper scripts point at the new update_profile_data.py location.
- Startup/support tooling (run_dki_engine.py, paddleocr_integration.py, osint_module.py, smoke fixtures) now target the corrected root folder.
- Batch launchers and installer shortcuts re-pointed to the new root so desktop entry points continue to resolve assets.
- poppler_path.env and smoke result JSON updated so auxiliary tooling loads binaries and repositories from the relocated structure.

## Validation
- `rg -n "F:/Report Engine"` and `rg -n "F:\\Report Engine"` now return no hits in Python/JSON/config surfaces.
