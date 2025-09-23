# Section CP – Cover Page Execution Guide

## Overview
The cover page establishes the canonical case identity before any narrative content. It mirrors client intake and contract data so the gateway can stamp every subsequent section with consistent metadata. The renderer pulls from `section_payload['case_data']`, the authenticated user profile, and configuration defaults (company and investigator records). When present, it also surfaces profile assets (logos, signature images) for downstream reuse by the disclosure page and final assembly.

## Required Inputs & Extraction Workflow
- **Client profile and contract data** come from `processed_data['case_data']` produced by `DocumentProcessor.process_files()`. OCR pipelines surface names, addresses, phones, contract dates, and case IDs out of intake forms, signed agreements, and ID cards.
- **User profile defaults** are injected via `UserProfileManager.get_api_keys()` and configuration helpers (if available). They populate agency licensing, investigator credentials, company branding, and contact channels.
- **Voice or media sources** do not directly enrich Section CP, but metadata extracted by the toolkit (e.g., `metadata_tool_v_5.py`) can provide consistent casing/formatting for client names and case IDs.
- **Toolkit orchestration:** `MasterToolKitEngine.run_all()` normalizes dates, deduplicates contact blocks, and exposes a `client_profile` dictionary in `section_payload`. The cover renderer uses this as the authoritative record, ensuring the same values are recycled in Sections DP and 9.

## Data Handling, Sorting & Placeholder Rules
- Field whitelist enforces drift control. Anything outside the approved set (client/investigator identifiers, agency data, case metadata) is bounced into the manifest’s `drift_bounced` block for audit.
- Placeholder policy: blank or banned tokens resolve to italicized stand-ins (`Unknown`, etc.) until the toolkit or user supplies a valid value.
- Case number generation derives from client surname + contract date. OCR artifacts are cleaned by toolkit regex passes before they reach this section.

## Cross-Reference & Validation
- Section CP expects Section 1 to confirm the same client and investigator roster. Toolkit continuity checks compare cover values against Section 1 payload and raise Q&A prompts on mismatch.
- Billing logic later in Section 6 reuses `cover_profile` licensing data; therefore, any update made here must propagate through the gateway so downstream sections stay synchronized.

## Reporting Expectations
- Display client, investigator, and agency credentials in professional language. No investigative detail or evidence appears here—only context and contact information.
- Provide a manifest with `cover_profile` so Section DP can embed the identical disclosures without recomputation.

## Inter-Section & Gateway Flow
- Renderer output shape: `{ "render_tree": [...], "manifest": {...}, "handoff": "gateway" }`. The gateway stores this in `section_outputs['section_cp']` and uses `manifest['cover_profile']` when later sections request branding or licensing data.
- When cases reload, the application seeds `case_metadata` with the same values so `_ensure_gateway_case_initialized()` can broadcast them again before generation.
- No voice/OCR processors run on-demand for this section, but the document pipeline must have executed successfully earlier so the `case_data` block is populated.

## Presentation Guidelines
- Font locked to Times New Roman; headings uppercase with shaded background.
- Optional logo path injects an `image` block at the top of the render tree. Exporters (DOCX/PDF) scale the asset to fit.
- Ensure generated date reflects the current run; the final assembly recalculates pagination but keeps this metadata intact.
