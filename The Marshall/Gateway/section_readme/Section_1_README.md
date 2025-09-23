# Section 1 – Investigation Objectives & Case Profile Guide

## Overview
Section 1 is the gateway’s master filter. It cements the case identity, defines subjects, and selects the investigation mode (Investigative, Surveillance, Hybrid). Every downstream module—billing, evidence handling, toolkit triggers—references the values surfaced here. The renderer enforces a strict whitelist and structured layout to keep legal and contract metadata locked.

## Required Inputs & Extraction Workflow
- **Document Processor** extracts client, subject, contract, and location data from intake packets, contracts, and IDs using OCR (Tesseract + pdfplumber/PyPDF2). It writes normalized values into `processed_data['case_data']` and `processed_data['intake']`.
- **Toolkit Passes** (`MasterToolKitEngine.run_all`) apply continuity checks (North Star, Cochran), deduplicate aliases, and push enriched fields into `section_payload`. These checks also ingest AI outputs (entity extraction, voice transcripts) to confirm subject references.
- **Manual Overrides**: User profile data (investigator name/license) enters via the setup wizard; fallbacks come from configuration defaults. The renderer blends these sources so the same credentials appear on the cover, disclosure, and certification pages.
- **Voice & Media Signals**: Though spoken notes don’t display here, voice transcription metadata is stored in case context for later sections. Section 1 references those flags to mark whether field audio evidence exists.

## Data Handling, Sorting & Placeholder Policy
- Fields outside the approved list are bounced and logged (`drift_bounced`). This protects the legal formatting of objectives.
- Null, blank, or banned tokens output italicized placeholders (`Unknown`, etc.) pending correction.
- Subject lists support up to three named parties; toolkit logic ensures the same order is mirrored in Sections 3–4 when logs/evidence are grouped by subject.
- Employer, routine, and objective text is sourced from structured JSON produced by toolkit modules—no free-form guessing.

## Cross-Reference & Validation
- Section 1 drives `GatewayController.report_types` selection. Contract metadata (flat-rate vs surveillance clause) sets the report mode, which controls section visibility and billing behaviors.
- Billing logic, surveillance scheduling, and evidence matching all trace back to this section via the gateway’s `case_metadata` and `section_states`.
- Reverse continuity tests compare Section 1 values with Section 5 (documents) and Section 6 (billing). Any mismatch triggers Q&A prompts before final assembly.

## Reporting Expectations
- Provide a clear, courtroom-ready statement of purpose, client, subjects, investigators, and operational area.
- No narrative or analysis—just authoritative case inputs.
- Ensure subject listings tie directly to the contract scope so later sections don’t introduce unapproved targets.

## Inter-Section & Gateway Flow
- `generate_section()` now calls `_ensure_gateway_case_initialized()` before dispatch, so `section_payload` always includes current case metadata.
- Gateway stores Section 1’s manifest and uses it to validate other sections (e.g., ensuring Section 3 logs reference known subjects).
- Toolkit results (e.g., from `metadata_tool_v_5.py`, `northstar_protocol_tool.py`) appear in `section_payload['toolkit_results']` and provide confidence tags or flags—including those derived from OCR, voice, and geospatial modules.

## Presentation Guidelines
- Static headings and labels; font family and sizes are locked.
- Subject and client names should appear as `Last, First` if the toolkit can infer formatting; otherwise placeholders signal manual correction.
- Ensure contract date and location fields reflect normalized (ISO) values; exporters handle localization.

## Parsing Map Reference
The detailed parsing and validation map for this section is kept at F:\Report Engine\Gateway\parsing maps\SECTION_1_PARSING_MAP.md. Consult it for data sourcing, OpenAI trigger timing, and UI checklist expectations.

