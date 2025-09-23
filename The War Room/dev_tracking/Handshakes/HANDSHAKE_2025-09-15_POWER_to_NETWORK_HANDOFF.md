# HANDSHAKE — 2025-09-15 — POWER → NETWORK (Control Handoff)

From Agent: POWER (Core Functions)
To Agent: NETWORK (External Services & API Integration)
Priority: High — unblock smoke and integration

Context
- Phase 1 config hygiene completed; labels and mappings aligned to fallback logic.
- Launcher hardened; smoke pre-check executed and blocked only by missing deps.
- Auto report-type detection implemented in `gateway_controller.py` (supports None/auto + Field≡Surveillance alias).

Deliverables Provided
- Config validators: `core_config_validator.py`, `normalize_core_configs.py` (12/12 files pass)
- Updated configs and labels (see change logs under dev_tracking)
- Smoke plan & results: `dev_tracking/agent_1_POWER_CODING/SMOKE_TEST_PLAN_2025-09-15.md`, `dev_tracking/SMOKE_VALIDATION_2025-09-15.md`
- Policy handshakes: fallback logic alignment and coding policy

NETWORK Tasks (Immediate)
1) Install required dependencies (requirements.txt)
   - Required: python-docx, openpyxl, opencv-python, reportlab
   - Optional (FYI): pytesseract, openai, spacy, transformers, beautifulsoup4
   - Confirm install by running: `python run_dki_engine.py` (expect clean dependency pass)

2) Rerun smoke (post-install)
   - Launch-only validation: confirm no missing-deps halt
   - Provide brief ACK with environment summary (OS, Python, pip list subset)

3) API key readiness (after smoke)
   - Verify `UserProfileManager` DB path fix works end-to-end
   - Confirm ability to store and load API keys (no decryption errors)

Optional (Next)
- Prepare connectivity tests for OSINT/Geocoding and AI services (no blocking)

Expected Outputs
- ACK of dependency install and smoke pass
- Notes on any environment constraints that could affect section renderers/toolkit

Due-by: 2025-09-16
Status: SENT — Awaiting NETWORK ACK

