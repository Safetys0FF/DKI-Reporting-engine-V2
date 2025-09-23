# Path Remap Actions - 2025-09-19

## Summary
- Rebased import/path wiring to treat `Report Engine` as project root.
- Replaced hard-coded F:\\ paths with runtime discovery using `Path(__file__)`.
- Normalised `sys.path` bootstrapping so shared modules load from the relocated structure.

## Files Updated
- `Report Engine/Gateway/file_processing_orchestrator.py`
- `Report Engine/Gateway/openai_trigger_engine.py`
- `Report Engine/app/media_processing_engine.py`
- `Report Engine/CoreSystem/Plugins/osint_module.py`
- `Report Engine/CoreSystem/Archives/paddleocr_integration.py`
- `Report Engine/CoreSystem/Archives/test_complete_system_validation.py`
- `Report Engine/CoreSystem/Archives/test_evidence_flow.py`
- `Report Engine/CoreSystem/Archives/test_error_handling.py`
- `Report Engine/CoreSystem/Archives/test_entity_extraction.py`
- `Report Engine/CoreSystem/Archives/test_ocr_engines.py`
- `Report Engine/CoreSystem/Archives/test_integration_validation.py`
- `Report Engine/CoreSystem/Archives/test_environment_monitoring.py`
- `Report Engine/CoreSystem/Archives/run_dki_engine.py`
- `Report Engine/dev_tracking/tools/import_keys_from_txt.py`
