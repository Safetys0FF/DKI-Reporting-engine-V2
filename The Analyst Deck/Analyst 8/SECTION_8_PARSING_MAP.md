# Section 8 Parsing Map (Investigation Evidence Review)

## Purpose
Index all evidence objects with provenance, validation status, and routing so other sections can reference media, documents, and transcripts reliably.

## Data Inputs
| Field | Origin | Notes |
|-------|--------|-------|
| evidence_manifest | `processed.images/videos/audio/files` | Raw and derived assets grouped by media type. |
| media_analysis | `processed.media_analysis` | Analytics from media processing engine (faces, transcription, quality). |
| chain_of_custody | `processed.manual_notes.custody` | Custody chain remarks for auditing. |
| validation_status | `processed.manual_notes.validation` | Manual or automated validation outcomes. |
| section_routing | `processed.manual_notes.routing` | Links between evidence items and report sections. |

## Toolkit & AI Triggers
- OpenAI `content_verification` (post_ocr) – extracts salient facts and checks for tampering cues.
- OpenAI `chain_integrity` (pre_render) – summarises custody sequence and flags breaks.

## UI Checklist
- Ensure each evidence item has title, description, custody, and validation status.
- Initiate re-validation where required.

## Dependencies
- Feeds: Sections 3, 7, 9, and DP rely on evidence links and validation summaries.
- Shares: `evidence_links`, `validation_summary`, `routing`.
