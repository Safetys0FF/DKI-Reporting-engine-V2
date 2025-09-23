# Section 1 Parsing Map (Investigation Objectives / Case Information)

## Purpose
Establish the investigation charter by consolidating client profile, objectives, subject roster, jurisdiction, and compliance posture. Section 1 feeds the downstream narrative, billing expectations, and certification language.

## Data Inputs
| Field | Origin | Notes |
|-------|--------|-------|
| client_info | `case_data.client_info`, fallback to OCR metadata | Name, contact, contract IDs merged from intake and scanned contracts. |
| objectives | `case_data.objectives` / `case_data.investigation_goals` | Normalised list of goals; OpenAI clarifies phrasing. |
| subjects | `case_data.subjects`, `processed.metadata.subjects` | Primary/secondary actors with identifiers for evidence linking. |
| jurisdiction | `case_data.jurisdiction`, `processed.metadata.jurisdiction` | Drives license validation and disclosure wording. |
| compliance_flags | `processed.metadata.compliance_flags` | Risk markers surfaced by OCR/toolkit preprocessing. |
| osint_summary | `toolkit_results.osint_verification` | Cross-check of subject identities and public-record anomalies. |

## Toolkit & AI Triggers
- Toolkit: OSINT verification module enriches subject and compliance context.
- OpenAI `goal_clarification` (post_intake) – standardises free-form objectives.
- OpenAI `compliance_scan` (pre_render) – validates jurisdiction vs investigator licensing.

## UI Checklist
- Confirm objectives and subject roster.
- Review and resolve compliance alerts before approval.

## Dependencies
- Feeds: Sections 3, 7, 9 consume objectives, subjects, and compliance posture.
- Shares: `subjects`, `jurisdiction`, and `compliance_flags` with downstream builders.
