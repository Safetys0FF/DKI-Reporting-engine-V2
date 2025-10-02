# Section 1 Parsing Map (Investigation Objectives / Case Information)

## Purpose
Establish the investigation charter by consolidating client profile, contract metadata, objectives, subject roster, jurisdiction, and compliance posture. Section 1 feeds the downstream narrative, billing expectations, photo manifest, and certification language used in Sections 6–9.

## Data Inputs
| Field                              | Source Path(s)                                                                                     | Notes |
|------------------------------------|----------------------------------------------------------------------------------------------------|-------|
| client_name / address / phone      | `case_data.client_name`, `case_data.client_address`, `case_data.client_phone`; fallback intake OCR | Populated by intake parser; resolves to Section 1 “Client Information”. |
| contract_date                      | `case_data.contract_date` or `contract_type_details[].metadata.contract_date`                       | Derived from contract classifier; controls case number stamp and disclosures. |
| investigation_goals                | `case_data.investigation_goals`, `case_data.objectives`, `toolkit_results.goal_clarification`      | Normalised goal list used across Sections 2, 3, 7. |
| subjects roster                    | `case_data.subjects`, `case_data.subject_primary/secondary/tertiary`, `processed.metadata.subjects` | Drives Section 2 behavioral matrix and Section 4/8 photo captions. |
| subject employers / addresses      | `case_data.subject_employers`, `case_data.subject_employer_address`                                 | Validated against intake + contract clauses for billing alignment. |
| agency / investigator credentials  | `case_data.agency_name`, `case_data.agency_license`, `case_data.assigned_investigator`, `case_data.investigator_license` | Injected from user profile merge; required for disclosures. |
| location_of_investigation          | `case_data.location_of_investigation` with fallback to intake `case_data.case_locations`            | Fuels map references in Sections 2 & 3. |
| jurisdiction & compliance_flags    | `case_data.jurisdiction`, `processed.metadata.compliance_flags`, `toolkit_results.compliance_scan` | Ensures licensing statements align with venue; alerts surfaced in UI. |
| contract classification summary    | `case_data.contract_type`, `case_data.contract_type_auto`, `case_data.contract_type_details[]`     | Displayed as “Case Type” token and passed to downstream billing logic. |

## Toolkit & AI Triggers
- Toolkit: OSINT verification module enriches subject and compliance context.
- OpenAI `goal_clarification` (post_intake) – standardises free-form objectives.
- OpenAI `compliance_scan` (pre_render) – validates jurisdiction vs investigator licensing.

## UI Checklist
- Confirm client contact, contract date, and investigator credentials.
- Resolve compliance alerts before approval.
- Verify contract classification (`Investigative` / `Surveillance` / `Hybrid`) matches case intent.

## Dependencies
- Provides case identity to Sections 2, 3, 6, 7, 9, CP, TOC.
- Shares contract type and credentials with billing summary, disclosure page, and final report assembler.
