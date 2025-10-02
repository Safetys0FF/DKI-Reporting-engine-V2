# Section 4 Parsing Map (Review of Surveillance Sessions)

## Purpose
Convert the raw daily logs into courtroom-ready surveillance summaries, capturing conditions, observations, deviations, and linked media for each session window.

## Data Inputs
| Field / Element                | Source Path(s)                                                                                   | Notes |
|--------------------------------|--------------------------------------------------------------------------------------------------|-------|
| surveillance_date              | `section3.render_manifest.windows[].date`, `processed.manual_notes.daily_logs[].date`            | Session header (e.g., “Date of surveillance”). |
| time_blocks                    | `section3.render_manifest.windows[].time_range`, toolkit continuity sessions                     | Supplies start/end times and durations. |
| locations                      | `section3.render_manifest.windows[].location`, `case_data.primary_location`                      | Feeding “Locations” line and map notes. |
| subject_confirmed              | `toolkit_results.continuity_check.sessions[].subject_confirmed`, manual notes                    | Boolean/description for template field. |
| observed_behavior              | `toolkit_results.session_summary.behavior`, `processed.manual_notes.session_notes`               | Narrative describing activities observed. |
| subject_interactions           | `processed.manual_notes.session_interactions`, narrative assembler output                        | Records contacts and interactions. |
| visual_evidence references     | `processed.images`, `processed.videos`, matched by session timestamp                             | Described in “Visual Evidence” field; also exported to Section 8. |
| deviations_noted               | `toolkit_results.continuity_check.sessions[].deviations`, gap detection comments                 | Summarises anomalies/variances. |
| closure_status                 | `toolkit_results.session_summary.closure_status`, manual disposition notes                       | Informs whether objectives met or session incomplete. |
| voice_memos                    | `processed.audio`, `processed.manual_notes.voice_memos`                                          | Rendered as list in template. |
| environmental conditions       | `processed.metadata.environmental`, weather API integrations                                     | Adds context for performance statements. |

## Toolkit & AI Triggers
- OpenAI `session_summary` (post_compile) – drafts narrative for each surveillance window.
- OpenAI `condition_validation` (post_compile) – verifies environmental statements align with data.
- Continuity toolkit slices Section 3 logs into sessions and calculates variances.

## UI Checklist
- Review session boundaries and adjust if toolkit segmentation differs from investigator intent.
- Ensure visual evidence and voice memos link back to media IDs.
- Confirm deviations and closure status are documented for each session.

## Dependencies
- Feeds Section 7 conclusions and Section 8 photo manifest with session-level findings.
- Provides deviation metrics and matched media back to billing and audit logs.
