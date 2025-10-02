# Section 3 Parsing Map (Investigation Details / Daily Logs)

## Purpose
Produce the day-by-day field narrative, combining surveillance times, objectives, observations, vehicle sightings, and investigator summaries with the supporting media and GPS evidence.

## Data Inputs
| Field / Element                     | Source Path(s)                                                                                     | Notes |
|-------------------------------------|----------------------------------------------------------------------------------------------------|-------|
| surveillance_date                   | `processed.manual_notes.daily_logs[].date`, `processed.timeline[].date`                             | Drives headings such as “(Insert Date for first day of Investigation)”. |
| surveillance_time windows           | `processed.manual_notes.daily_logs[].time_range`, `processed.timeline[].time_range`, GPS metadata   | Populates “Surveillance Time” line per day. |
| daily_objective                     | `processed.manual_notes.daily_logs[].objective`, `case_data.investigation_goals`                    | Restates targeted outcomes for the day. |
| observations & activities           | `processed.manual_notes.daily_logs[].observations`, OCR log extracts, toolkit narrative alignment   | Forms the “Observations” paragraph blocks. |
| daily_summary                       | `processed.manual_notes.daily_logs[].summary`, `toolkit_results.narrative_alignment.summary`        | Fuels “Summary of (date)” lines in template. |
| vehicles_present / subject movement | `processed.manual_notes.daily_logs[].vehicles`, `processed.manual_notes.daily_logs[].movement`      | Maps to template prompts (vehicles present? subject movement?). |
| media_assets                        | `processed.images`, `processed.videos`, `processed.audio`, matched by timestamp                    | Linked into Sections 3 & 8 sidebars and manifest. |
| gps_tracks / mileage                | `processed.metadata.location_tracks`, `processed.gps_tracks`                                        | Supports mileage calculations and continuity notes. |
| continuity_flags                    | `toolkit_results.continuity_check`, `toolkit_results.gap_detection`                                 | Surfaces required investigator commentary on gaps. |

## Toolkit & AI Triggers
- OpenAI `narrative_alignment` (post_compile) – ensures every log entry references supporting evidence.
- OpenAI `gap_detection` (post_compile) – flags missing coverage or timeline anomalies.
- Toolkit continuity check compares planned vs actual coverage and tags mileage variances.

## UI Checklist
- Verify each log entry has media or observation evidence linked.
- Resolve continuity/gap alerts before approving the section.
- Confirm vehicle and subject movement notes are recorded for each surveillance block.

## Dependencies
- Feeds Sections 4 (session review), 6 (billing hours), 7 (conclusion narrative), and 8 (photo manifest) with time windows and evidence references.
- Shares GPS/mileage info with billing tool and narrative assembler.
