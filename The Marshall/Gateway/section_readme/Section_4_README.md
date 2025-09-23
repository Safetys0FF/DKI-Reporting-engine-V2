# Section 4 – Review of Surveillance Sessions Guide

## Overview
Section 4 transforms raw surveillance logs into a court-ready narrative, explaining what was observed, why it matters, and how it ties to investigative goals. It references timelines from Section 2, observations from Section 3, and media evidence tracked in Section 8. The output must stay factual, subject-driven, and aligned with client objectives as mandated by the Cochran Theory and North Star protocol.

## Required Inputs & Extraction Workflow
- **Section 3 Logs** provide the chronological backbone (`previous_sections['section_3']`).
- **Toolkit Analyses** compile continuity checks (North Star), speculation warnings (Cochran), and entity resolution to ensure every observation maps to authorized subjects.
- **Media Evidence** metadata (photos/videos/audio) flowing from the media engine allows this section to reference corroborating proof without embedding raw files.
- **Voice Transcripts** supply verbatim quotes or field commentary, allowing investigators to reference spoken confirmations while maintaining objective tone.

## Data Handling & Sorting
- Narrative structured by date/time, aligning with Section 3 windows.
- Each paragraph should include: location, subject identification, observed behavior, relevance to objectives.
- All statements must be verifiable via logs or media metadata; the renderer rejects speculative text when toolkit flags contradictions.
- Deviations from planned behavior (Section 2) are highlighted and rationalized.

## Cross-Reference & Validation
- Continuity enforcement: Observations must have matching entries in Section 3; mismatches trigger Q&A before approval.
- Billing tie-ins: Hours and mileage derived from these sessions feed Section 6; mileage tool results ensure time blocks match.
- Media cross-links: Section 4 references media IDs so Section 8 can display evidence panels for the same events.

## Reporting Expectations
- Write in objective, courtroom-ready language. Include only relevant observations that advance the case.
- Explicitly connect surveillance findings back to client objectives recorded in Section 1.
- Note any subject interactions, vehicles, or deviations with context for investigative decisions.

## Inter-Section & Gateway Flow
- Section 4 consumes manifests from Sections 2 and 3 and passes a cleaned narrative to Section 8 and Final Assembly.
- Gateway uses Section 4 approval as a prerequisite before billing (Section 6) finalizes, ensuring operations were justified.
- Any transcription snippets or geocoding assistance used here must already exist in toolkit outputs; this section never executes integrations on its own.

## Presentation Guidelines
- Maintain organized headings (date or session labels). Exporters may convert them into subheaders.
- Avoid raw GPS coordinates; translate into context (“Observed near [address]”) leveraging geocoded metadata provided earlier.
- Ensure voice-derived statements are clearly attributed and fact-checked.

## Parsing Map Reference
The detailed parsing and validation map for this section is kept at F:\Report Engine\Gateway\parsing maps\SECTION_4_PARSING_MAP.md. Consult it for data sourcing, OpenAI trigger timing, and UI checklist expectations.

