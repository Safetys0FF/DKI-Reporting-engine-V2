# System Execution Plan – POWER Agent (2025-09-19)

## Objective
Operationalise the architect workflow (OCR → API validation → Gateway orchestration → Toolkit validation → Evidence processing → Section rendering → Final assembly) for an end-to-end report issuance cycle.

## Execution Path
1. **Stage Case Assets** – Create `DKI_Repository/cases/<test_run>/` with intake JSON, contract PDFs, surveillance logs, mileage JSON under `Report Engine/artifacts/mileage/`, audio/video evidence, and billing metadata. Record sources in `dev_tracking/agent_1_POWER_CODING/SESSION_LOG`.
2. **Configure Credentials** – Populate `Start Menu/api_keys.json` or user profile via API dialog; confirm `.venv` Whisper/librosa/pytorch stack loads (voice_transcription ready).
3. **Toolkit Calibration** – Run `Tools/billing_tool_engine.py`, `Tools/mileage_tool_v2.py`, `Tools/metadata_tool_v_5.py`, `Tools/cochran_match_tool.py`, and OSINT checks against staged data; store outputs in `DKI_Repository/cases/<test_run>/toolkit_cache/`.
4. **Processor Validation** – Execute media/OCR passes (`Processors/document_processor.py`, `Processors/media_processing_engine.py`) ensuring outputs populate case directories and schemas in `dev_tracking/logs/SECTION_*_PARSING_MAP.md`.
5. **Gateway Workflow** – Within UI (`app/main_application.py` or launcher), follow section order per `SECTION_ACTION_PLAYBOOK_2025-09-19.md`, verifying toolkit dispatch signals (10-6) and section approvals (10-8). Capture adjustments/notes per section.
6. **Issue Pipeline** – Once all sections green, trigger final assembly (`Gateway/final_assembly.py`), run signature + packaging routine (per `POWER_REPORTING_MASTER_PLAN_2025-09-19.md`), log dispatch metadata in `DKI_Repository/cases/<test_run>/dispatch_log.json`, and emit handshake to NETWORK/DEESCALATION.

## Files / Modules Impacted
- `DKI_Repository/...` (case data, toolkit cache, dispatch logs).
- `Report Engine/artifacts/mileage/` (mileage audit inputs).
- `Report Engine/Tools/*` and `Tool kit/tools.py/*` (toolkit execution).
- `Report Engine/Gateway/*` and `Sections/section_engines` (section orchestration/render).
- `dev_tracking/logs/SMOKE_RUN_RESULTS.json` and new dispatch log for audit trail.

## Core System Impact
- Validates the full evidence-to-report pipeline with production-like data.
- Confirms toolkit resiliency (billing/mileage/identity/metadata) after real inputs.
- Exercises media/voice transcription inside `.venv`, ensuring dependencies resolved.
- Provides NETWORK/DEESCALATION with concrete outputs to regression-test against.

## Next Steps
1. Populate the test case artifacts and credentials (POWER agent).
2. Execute toolkit unit checks, update logs with findings.
3. Run UI-driven section approvals; document anomalies and resolutions.
4. Complete Issue pipeline, store deliverables, and log handshake for validation sweep.
5. Incorporate feedback from NETWORK/DEESCALATION, then plan automation/regression scripts around the completed run.
