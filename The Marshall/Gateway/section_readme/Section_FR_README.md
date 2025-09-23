# Section FR – Final Assembly Guide

## Overview
The Final Assembly Manager compiles all approved sections into the final report artifact. It receives section outputs from the gateway, tracks approval states, and invokes `ReportGenerator` to produce the report structure consumed by export routines (DOCX/PDF). It enforces deduplication and normalization to ensure a consistent final package.

## Required Inputs & Workflow
- **Gateway Section Outputs:** Each renderer (Sections CP through DP) hands its `{render_tree, manifest}` to the Final Assembly via `add_section_output(section_id, output)` once the gateway marks the section completed/approved.
- **Section States:** `mark_section_state(section_id, state)` keeps track of workflow progress; only sections with `completed` or `approved` states participate in final assembly.
- **Case Snapshot:** Optional `case_snapshot` metadata includes case_name, case_id, and report type. It mirrors the `case_metadata` tracked in the UI/gateway handshake.
- **ReportGenerator:** `generate_full_report(section_data, report_type)` merges ordered sections, applies formatting, and prepares export-ready structures.

## Data Handling & Deduplication
- `assemble_final_report` filters for ready sections and pulls their output directly into the generator.
- `_deduplicate_and_clean_sections` removes duplicate content blocks and collapses excessive newlines.
- The final report dictionary includes ordered `sections`, summary metadata, and any toolkit-derived annotations.

## Cross-Reference & Validation
- Before assembly, ensure all sections reached the approved state via the gateway (signals 10-4). Sections with outstanding flags (e.g., Section 7 or Section DP) must be resolved first.
- The assembled report respects the canonical order from `GatewayController.report_types` so pagination and TOC integration remain correct.
- Section manifests (cover profile, billing data, voice memo summaries) stay intact for exporters to consume.

## Inter-Section & Gateway Flow
- Final Assembly listens to callbox signals via `push_signal` for auditing.
- When the user triggers export, the application calls `assemble_final_report`, then passes the result to UI/export modules.
- After assembly, the gateway can archive `last_compiled` for re-download or incremental updates.

## Presentation & Export
- Final assembly doesn’t render UI; it prepares structured data for exporters. Ensure exporters maintain styling guidelines defined in each section README (Times New Roman, heading structure, bullet formats).
- When new sections are added in future releases, update the canonical order and this README so assembly expectations remain accurate.

## Parsing Map Reference
The detailed parsing and validation map for this section is kept at F:\Report Engine\Gateway\parsing maps\SECTION_FR_PARSING_MAP.md. Consult it for data sourcing, OpenAI trigger timing, and UI checklist expectations.

