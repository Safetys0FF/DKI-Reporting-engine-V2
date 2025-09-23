# TEST PLAN – NETWORK DIAGNOSTIC SUITE (2025-09-21)

**Prepared By:** Network Agent 2  
**Context:** Derived from EOD_HANDSHAKE_2025-09-21_NETWORK_SYSTEM_FAILURE_ANALYSIS.md

## 1. Evidence OCR Processing Test
- **Purpose:** Ensure files dropped into a case produce processed artifacts consumable by section renderers.
- **Procedure:**
  1. Create case with new case dialog (case number + date + client).
  2. Upload mixed document set (PDF + DOCX + IMAGE + VIDEO).
  3. Run `document_processor.process_files` and confirm populated entries under `section_data['processed_files']`.
- **Pass Criteria:** Count of processed files equals uploaded evidence count; OCR/metadata keys present for each file ID.

## 2. Section Approval Persistence Test
- **Purpose:** Verify reviewer notes and approvals survive after `gateway_controller.approve_section` and appear in final assembly.
- **Procedure:**
  1. Generate Section 1, add reviewer comments, approve.
  2. Navigate to final assembly preview; export PDF.
  3. Confirm reviewer comments embedded in exported section content.
- **Pass Criteria:** Reviewer comments visible in final report; no loss of approved text.

## 3. API Integration Pipeline Test
- **Purpose:** Validate System Architect API sequence (ChatGPT → Gemini → Google Maps) with stored keys.
- **Procedure:**
  1. Configure keys via Profile Center → API Keys tab, re-auth with password.
  2. Trigger gateway request requiring AI + geocoding (e.g., Section 2 requirements).
  3. Inspect logs / section payload for AI + map enrichment.
- **Pass Criteria:** Gateway call chain executes in required order; enriched data present in section result metadata.

## 4. Export Integrity Test
- **Purpose:** Ensure approved content survives final export stage without truncation.
- **Procedure:**
  1. Approve Sections 1–3 with sample text.
  2. Run `report_generator.generate_full_report` followed by PDF export.
  3. Inspect exported document to confirm sections match approved content.
- **Pass Criteria:** Zero discrepancies between approved section text and exported report.

## 5. End-to-End Regression Test
- **Purpose:** Validate entire pipeline after fixes (upload → process → generate → approve → export).
- **Procedure:**
  1. Execute tests #1–#4 sequentially on a fresh case.
  2. Record timings and any warnings/errors in `dki_engine.log`.
- **Pass Criteria:** All intermediate tests pass; no errors in log; final report contains complete evidence-driven narrative.

**Execution Notes:**
- Run after POWER/DEESCALATION deliver fixes.
- Capture results in `dev_tracking/logs/NETWORK_TEST_RESULTS_2025-09-21.md` (to be created post-run).
