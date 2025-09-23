# Section 3 – Surveillance Reports / Daily Logs Guide

## Overview
Section 3 chronicles field surveillance activity. It stitches together investigator logs, GPS/metadata, media captures, and voice notes into a time-ordered narrative the gateway can audit. The renderer enforces whitelist fields and automatically cross-references media time stamps so every observation is grounded in evidence.

## Required Inputs & Extraction Workflow
- **Field Logs & Forms:** OCR converts PDF logs, handwritten notes, and checklists into structured text (`date_block`, `time_logs`, `activities_observed`, etc.).
- **GPS / Metadata:** `metadata_tool_v_5.py` parses EXIF timestamps, GPS coordinates, and device info from processed images/videos; `DocumentProcessor` stores them in `processed_data['media_processing_results']`.
- **Voice Recordings:** Audio files transcribed by `voice_transcription.py` (Whisper + soundfile/ffmpeg) produce memo summaries. Section 3 consumes them through `_format_voice_memos()` and presents concise bullet summaries.
- **Toolkit Validations:**
  - `northstar_protocol_tool.py` checks travel times and routes between logged events.
  - `cochran_match_tool.py` enforces factual, time-bound statements.
  - `mileage_tool_v_2.py` contributes mileage/time data for later billing.

## Data Handling & Sorting
- Fields appear in a fixed order: date, time log, agent, location context, observed activities, photo counts, vehicle tracking, weather, narrative notes, voice memo summary.
- `_extract_time_windows()` uses regular expressions to find chronological windows; `_build_internal_sidebar()` cross-maps images/videos captured within those windows.
- Placeholder policy ensures missing entries appear italicized but still present for review.

## Cross-Reference & Validation
- Section 3 draws from Section 2’s planned timelines and subjects. If observed events break expected patterns, toolkit flags them for Section 4’s analysis.
- Media cross-links (photos/videos/audio) feed Section 8, carrying the same IDs and timestamps to maintain chain of evidence.
- Billing and mileage modules use narrative timestamps alongside `mileage_tool` outputs, ensuring Section 6 reflects actual operational time.

## Reporting Expectations
- Provide detailed, objective, timestamped accounts; avoid speculation or unsupported conclusions.
- Each entry must relate to authorized subjects or objectives defined in Section 1 and Section 2.
- Voice memo summaries should capture key spoken observations, call-outs, or quick recaps that relate to surveillance decisions.

## Inter-Section & Gateway Flow
- Render manifest includes `internal_sidebar` with matched media so the gateway can audit log-to-evidence continuity.
- Section 4 consumes Section 3 data (`previous_sections['section_3']`) to write narrative summaries; Section 8 uses the association map to cluster media per day.
- Gateway signals (10-4/10-9) rely on reviewers approving Section 3 before Section 4 can incorporate the information.

## Presentation Guidelines
- Title uppercase; headers follow style rules.
- Use clear paragraph or bullet formatting in exporters; internal sidebar remains non-client-facing but available to auditors.
- Ensure time formats remain ISO or 24-hour to simplify downstream calculations.

## Parsing Map Reference
The detailed parsing and validation map for this section is kept at F:\Report Engine\Gateway\parsing maps\SECTION_3_PARSING_MAP.md. Consult it for data sourcing, OpenAI trigger timing, and UI checklist expectations.

