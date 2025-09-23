# Section 2 – Pre-Surveillance / Case Preparation Guide

## Overview
Section 2 transitions the case from intake to operational readiness. It inventories verified subjects, routines, geographic anchors, and planning directives so field teams can mobilize. Each subsection (2A–2E) is tied to specific data from the intake package, investigator notes, toolkit intelligence, and prior sections. The renderer enforces a whitelist and multi-pass fallback to keep the planning narrative legally defensible.

## Required Inputs & Extraction Workflow
- **Document Processor** pulls structured data (subject aliases, addresses, employer records) through OCR and metadata extraction. JSON summaries of routines, locations, and planning notes populate `processed_data['intake']` and toolkit caches.
- **Toolkit Modules**:
  - `metadata_tool_v_5.py` normalizes names, addresses, and classification tags (`summary_tags`, `poi_tags`).
  - `northstar_protocol_tool.py` ensures planned routes and surveillance areas obey physical constraints.
  - `cochran_match_tool.py` verifies that planned operations align with evidence and contractual obligations.
- **OSINT Integration** (via `smart_lookup.py`): Reverse geocoding, entity verification, and risk checks fill lists like `verified_subjects`, `known_aliases`, and `pinned_locations`.
- **Voice/Photo Analysis**: If planning notes contain spoken briefings or whiteboard captures, the voice transcription pipeline and OCR will surface them as structured planning directives.

## Data Handling & Sorting
- Subsections group fields by operational purpose:
  - **2A – Case Summary:** goals, tags, case type tokens.
  - **2B – Subject Verification:** identity confirmation across records.
  - **2C – Patterns & Timelines:** known routines, POIs, timeline blocks.
  - **2D – Geospatial Prep:** maps, pinned coordinates, visual aids.
  - **2E – Operational Readiness:** ethics statements, resource allocation, planning checklists.
- Each field uses placeholder logic to highlight missing data. Toolkit fallback cycles through `intake`, `notes`, `evidence`, and `prior_section` before leaving placeholders.

## Cross-Reference & Validation
- Section 2 must agree with Section 1 on subjects and objectives; toolkit diffing flags discrepancies.
- Maps/geospatial entries connect to Section 8 so media captured later can be correlated with planned waypoints.
- Ethics statements and readiness flags surface in Section 9’s disclaimers to prove lawful planning.

## Reporting Expectations
- Provide a compact yet detailed operational plan: verified subject identities, routine summaries, surveillance zones, and readiness status.
- Avoid narrative speculation; only data corroborated by intake documents, toolkit intelligence, or confirmed OSINT sources should appear.

## Inter-Section & Gateway Flow
- Render result informs Section 3 (daily logs) and Section 4 (session reviews) by establishing the baseline plan; the gateway stores the manifest so timeline anomalies can be detected.
- When the toolkit runs before Section 6, it reuses planning costs and readiness flags to allocate billing categories.
- JSON handoffs (e.g., `timeline_blocks`, `geo_areas`) are ingested by the media engine to attach coordinates to future evidence.

## Presentation Guidelines
- Subsection headers (`SUBSECTION 2A`, etc.) uppercase and underlined; no deviation allowed.
- Field labels auto-title-case from snake_case; ensure upstream data uses descriptive keys.
- Placeholders appear italicized so reviewers can spot missing intelligence before field deployment.
