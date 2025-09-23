# Section 3 Parsing Map (Investigation Details / Daily Logs)

## Purpose
Assemble the chronological narrative of investigative activity, tying observations to evidence, GPS tracks, and continuity checks.

## Data Inputs
| Field | Origin | Notes |
|-------|--------|-------|
| timeline | `processed.timeline` or `processed.scan_results` | Timestamped activity blocks extracted from OCR/manual logs. |
| log_entries | `processed.manual_notes.logs` | Analyst annotations and supplemental clarifications. |
| media_assets | `processed.images/videos/audio` | Linked photos, video pulls, and voice memos for each event. |
| gps_tracks | `processed.metadata.location_tracks` | Route data for mileage/continuity comparison. |
| continuity | `toolkit_results.continuity_check` | Toolkit reconciliation of planned vs actual coverage. |

## Toolkit & AI Triggers
- OpenAI `narrative_alignment` (post_compile) – enforces evidence links for every log entry.
- OpenAI `gap_detection` (post_compile) – flags timeline gaps needing investigator comment.

## UI Checklist
- Confirm each narrative element references supporting evidence.
- Review and resolve flagged timeline gaps.

## Dependencies
- Feeds: Sections 4, 6, 7, 8 inherit timeline, mileage, and evidence references.
- Shares: `timeline`, `evidence_links`, `gps_tracks`.
