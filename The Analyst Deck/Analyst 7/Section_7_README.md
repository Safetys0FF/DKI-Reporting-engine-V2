# Section 7 – Conclusion Guide

## Overview
Section 7 delivers the professional conclusion for the investigation. It aggregates the results of Sections 1–5 and Section 8, checks continuity, and declares whether the case is closed or requires further work. It intentionally excludes billing (Section 6) to keep the conclusion focused on investigative outcomes and evidence integrity.

## Required Inputs & Extraction Workflow
- **Case Data:** Section payload includes `case_data` (client, case ID) and toolkit summaries.
- **Previous Sections:** The renderer inspects `previous_sections['section_X']` for Sections 1–5 and 8 to confirm availability. Missing inputs generate review flags.
- **Toolkit Results:** Continuity checks (`toolkit_results['continuity_check']`) indicate whether North Star/Cochran validations passed. Mileage/time/billing outputs are not considered here.
- **Voice & Media:** While the conclusion doesn’t process raw audio or images, it references the successful indexing of those assets (Section 8) to support its statements.

## Data Handling & Logic
- Determine coverage map—whether each upstream section completed successfully.
- If continuity tools report issues or any section is missing, the conclusion declares “Further Investigation Required.” Otherwise, “Case Closed.”
- Generates bullet list summarizing evidence sources (Objectives, Requirements, Logs, Sessions, Docs, Media).
- Stores flags in the manifest for the gateway and final assembly to act on.

## Cross-Reference & Validation
- Ensures all referenced findings exist; if not, they appear in the review flags list.
- Serves as the gateway checkpoint before final assembly: unresolved flags block closing status.
- Provides concise summary tying back to Section 1 objectives.

## Reporting Expectations
- Use objective, formal tone summarizing the confirmed findings and compliance checks.
- Do not reprint detailed narratives; reference the sections where evidence resides.
- Clearly articulate the final case decision and any outstanding actions.

## Inter-Section & Gateway Flow
- Manifest (`coverage`, `flags`, `decision`) enables downstream workflows (e.g., final assembly footers, case status updates in repository).
- Gateway uses the decision to determine whether the case can be sealed or if additional work orders should be opened.
- If voice/media analysis uncovered unresolved anomalies (through toolkit flags), they appear here to prompt remediation.

## Presentation Guidelines
- Title and headers follow standard styling.
- Provide bullet summary of evidence sources and integrity checks.
- Ending paragraphs state the closing statement and decision for clarity.
