# Section TOC Parsing Map (Table of Contents)

## Purpose
Automatically compile the ordered list of report sections, reflecting custom titles and approval state for the final deliverable.

## Data Inputs
| Field | Origin | Notes |
|-------|--------|-------|
| report_type | `report_type` from gateway context | Determines mandatory sections. |
| section_sequence | `section_sequence` | Ordered tuples of section IDs and display names. |
| title_overrides | `section_outputs.*.manifest.title_override` | User-provided titles applied when present. |
| section_states | `section_states` | Used to flag incomplete sections prior to export. |

## Toolkit & AI Triggers
- OpenAI `title_quality` (post_compose) – ensures overrides maintain professional tone.
- OpenAI `coverage_gap` (post_compose) – checks required sections are present for the report type.

## UI Checklist
- Confirm section order and optional inclusions.
- Verify custom titles and attachment placement.

## Dependencies
- Feeds: Section FR uses TOC data for pagination/export.
- Shares: `section_titles`, `section_states`.
