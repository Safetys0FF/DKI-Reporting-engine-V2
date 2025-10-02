# Section 2 Parsing Map (Pre-Surveillance / Case Preparation)

## Purpose
Capture the investigative preview—objective recap, subject dossiers, behavioural intelligence, surveillance zones, and the ethics/planning statement—before any field work begins.

## Data Inputs
| Field / Subsection                      | Source Path(s)                                                                                     | Notes |
|-----------------------------------------|----------------------------------------------------------------------------------------------------|-------|
| 2A Case Summary                         | `case_data.investigation_goals`, `case_data.case_summary`, `toolkit_results.goal_clarification`    | Restates why the client engaged DKI; limited to 3–5 sentences. |
| 2B Subject Profile                      | `case_data.subject_primary/secondary/tertiary`, `case_data.subject_addresses`, intake parser output | Provides validated identities and addresses; cross-checked with TLO/background results. |
| Subject Employers & Addresses           | `case_data.subject_employers`, `case_data.subject_employer_address`                                | Ensures verification for billing disclosure. |
| 2C Behavioral Patterns & Known Locations| `case_data.behavioral_patterns`, `processed.manual_notes.routines`, intake “known information”     | Aggregates routines, travel patterns, hobbies, and work schedules. |
| 2D Surveillance Zones                   | `case_data.primary_location`, `case_data.secondary_locations`, `case_data.tertiary_zones`          | Derived from intake + map validation to feed Section 3 and GIS overlays. |
| 2E Planning Statement & Ethics Clause   | `case_data.planning_statement`, `case_data.ethics_statement`, `case_data.surveillance_hours_allocated` | Declares subcontractor usage, allotted hours, and compliance message. |
| Case Type Token                         | `case_data.contract_type`, `case_data.contract_type_auto`                                          | Drives internal headings (Investigative vs Surveillance vs Hybrid). |

## Toolkit & AI Triggers
- OpenAI `plan_consistency` (pre_render) – confirms logistics align with Section 1 objectives.
- OpenAI `legal_compliance` (pre_render) – validates permits, legal notices, and subcontractor coverage.
- Toolkit: Northstar planning tool verifies locations, time budgets, and compliance flags.

## UI Checklist
- Confirm subject profiles and addresses are verified (map + intake).
- Ensure surveillance hours/allotted budgets match signed contract.
- Validate ethics statement and subcontractor declaration are populated.

## Dependencies
- Provides planning context to Sections 3 & 4, and establishes hour budgets used by Section 6 billing.
- Shares behavioural intel with narrative assembler and evidence routing.
