# Section 5 – Supporting Documents & Records Guide

## Overview
Section 5 catalogs all supplemental records gathered during the investigation—public records, contracts, subpoenas, correspondence, and any evidentiary paperwork. It must present a legally defensible inventory that aligns with Section 1 objectives, Section 2 planning, and Section 3/4 findings.

## Required Inputs & Extraction Workflow
- **Document Processor** performs OCR on PDFs, images, and scans, extracting metadata (jurisdiction, dates, parties) and storing it in structured JSON for grouping.
- **Toolkit Modules**:
  - `metadata_tool_v_5.py` normalizes document names, jurisdictions, and subject references (enforcing `Last, First`).
  - `cochran_match_tool.py` checks each record against investigative objectives to confirm relevance.
  - `northstar_protocol_tool.py` ensures referenced locations/times remain consistent with observed movement.
- **Chain of Custody** metadata is preserved through `DocumentProcessor._extract_file_metadata` and stored in `processed_data['files']` so Section 5 can cite anchor IDs without revealing internal filenames.

## Data Handling & Sorting
- Group records into generalized categories (e.g., Court Filings, Financial Records, Employment Records). Toolkit and config mappings help assign categories.
- Suppress raw filenames; use jurisdictional naming (`Sheriff Report – Tulsa County`).
- Client intake form and signed contract always appear last to demonstrate contractual scope.
- Placeholder policy flags missing core fields (name, date, jurisdiction) and blocks report finalization until resolved via Q&A.

## Cross-Reference & Validation
- Reverse continuity test compares Section 5 data to Section 1 (client/subject/contract details). Any conflict triggers prompts for correction.
- Section 2 planning references records to justify surveillance; Section 5 confirms those records were indeed obtained and vetted.
- Billing (Section 6) may reference document acquisition costs; ensure the manifest includes retrieval dates and effort notes.

## Reporting Expectations
- Present a clean, indented inventory with enough description for clients or courts to understand each document’s significance.
- Note verification status (verified vs pending) when toolkit or OSINT lookups confirm authenticity.
- Keep descriptive text objective; do not analyze content here—that belongs in Section 4 or the conclusion.

## Inter-Section & Gateway Flow
- Renderer outputs `render_tree` entries for each document, plus a manifest enabling downstream audit.
- Section 9 uses this manifest to confirm all disclaimers mention the existence of supporting documents.
- Final Assembly leverages the manifest to attach appendices or file indexes.

## Presentation Guidelines
- Times New Roman, 12pt, bold labels; no bullet glyphs—use indentation for hierarchy.
- Clearly separate categories with headers.
- Ensure all entries contain jurisdiction and date to support legal chain of custody.

## Parsing Map Reference
The detailed parsing and validation map for this section is kept at F:\Report Engine\Gateway\parsing maps\SECTION_5_PARSING_MAP.md. Consult it for data sourcing, OpenAI trigger timing, and UI checklist expectations.

