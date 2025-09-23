# Section Action Playbook – Reporting Pipeline (2025-09-19)

Order of operations always follows the architect directive:
OCR extraction → API validation (ChatGPT → Gemini → Maps) → Gateway orchestration → Toolkit validation → Evidence processing → Section rendering → Final assembly.

## Section CP – Cover Page
- **Inputs:** Case metadata (client, contract, investigator).
- **Actions:** OCR intake ➜ API verification of client data ➜ Toolkit billing snapshot (contract totals) ➜ Render cover header and logos.

## Section TOC – Table of Contents
- Build from approved section manifest; no external calls beyond ensuring section states are current.

## Section 1 – Investigation Objectives / Case Info
- OCR + contract parsing, ChatGPT summarises goals, Gemini cross-validates contract clauses, Maps confirms investigation locale.
- Toolkit: billing baseline, continuity check, OSINT identity verification.

## Section 2 – Pre-Surveillance / Planning
- OCR planning docs, ChatGPT summarises routines, Gemini/MAPS validate locations.
- Toolkit: metadata normaliser (tags, routines), northstar route checks, OSINT for subjects.

## Section 3 – Investigation Details / Daily Logs
- OCR daily logs, transcription of voice memos, API summarisation of key events.
- Toolkit: continuity + mileage (compare planned vs actual), duplicates flagged for Section 8.

## Section 4 – Review of Sessions
- Process surveillance reports & video, run media analysis + transcription.
- Toolkit: continuity/mileage diffs, OSINT follow-up on observed locations.

## Section 5 – Supporting Documents
- OCR all exhibits, hash via metadata tool, map docs to sections.
- Toolkit: metadata hashing, cochran identity for subject evidence.

## Section 6 – Billing Summary
- Use toolkit billing (BillingTool) after mileage + subcontractor logs processed; flag anomalies.

## Section 7 – Conclusion
- Summarise approved sections (ChatGPT/Gemini cross-check) and include legal statements.

## Section 8 – Evidence Review
- Media engine runs OCR/audio/vision, dedupe & timeline via toolkit media analysis.

## Section 9 – Certification & Disclaimers
- Pull compliance text, ethics statements (from Section 2) and signature data.

## Section DP – Disclosure Page
- Populate final disclosure checkboxes, ensure OSINT/contract obligations satisfied.

## Section FR – Final Assembly
- Gather approved sections, add logos/disclaimers, trigger Issue pipeline (signature, packaging, dispatch).

### Toolkit + API Roles
- **Toolkit**: billing_tool_engine, mileage_tool_v_2, metadata_tool_v_5, northstar_protocol_tool, cochran_match_tool, reverse_continuity_tool, OSINTEngine (managed via API keys).
- **API Sequence**: ChatGPT (context), Gemini (cross-check), Google Maps (geo validation).

### Next Steps to Enable Testing
1. Stage evidence package (contracts, logs, media) + mileage JSON and subject metadata in `DKI_Repository/cases/<test>`.
2. Configure API keys, confirm Whisper/Librosa available inside `.venv`.
3. Run toolkit unit checks with the staged data.
4. Step through UI section approvals in order, confirming each action above executes.
5. Trigger Issue pipeline to package, sign, and dispatch final report; log results for DEESCALATION validation.
