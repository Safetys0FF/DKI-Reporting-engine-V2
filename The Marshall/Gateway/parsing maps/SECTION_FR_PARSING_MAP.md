# Section FR Parsing Map (Final Assembly / Report Packaging)

## Purpose
Assemble approved sections, attachments, and export settings into deliverable packages while ensuring narrative consistency and redaction compliance.

## Data Inputs
| Field | Origin | Notes |
|-------|--------|-------|
| approved_sections | `section_outputs` filtered by `section_states == approved` | Manifest snapshots for each approved section. |
| pending_sections | `section_states` != approved | Drives warnings for incomplete content. |
| attachments | `processed.manual_notes.attachments` | Supplemental files slated for export bundles. |
| export_settings | `case_data.export_settings` | Formats, watermarks, delivery preferences. |

## Toolkit & AI Triggers
- OpenAI `narrative_consistency_sweep` (pre_export) – compares executive summaries with section conclusions.
- OpenAI `redaction_check` (pre_export) – scans attachments for unredacted PII. 

## UI Checklist
- Verify all required sections are approved.
- Confirm export formats, attachment order, and delivery settings. 

## Dependencies
- Feeds: Final deliverables and distribution actions.
- Shares: `export_manifest`, `attachments`, `pending_sections` for audit logs.
