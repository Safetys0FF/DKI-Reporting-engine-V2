# Section CP Parsing Map (Cover Page)

## Purpose
Generate the branded cover page containing case identifiers, client details, investigator credentials, and motto/branding elements exactly as defined in the master template.

## Data Inputs
| Field                                 | Source Path(s)                                                                                           | Notes |
|---------------------------------------|----------------------------------------------------------------------------------------------------------|-------|
| case_number (CLIENT LAST NAME - mm/yy)| `_compute_case_number(client_name, contract_date)`                                                       | Uses client last name + contract month to match template header. |
| case_title / report name              | `case_data.case_name` (fallback “INVESTIGATION FINAL REPORT”)                                           | Uppercase title at top of cover page. |
| agency contact details                | `case_data.agency_name`, `case_data.agency_license`, `case_data.agency_phone`, `case_data.agency_email` | Populates license line, phone, email. |
| investigator credentials              | `case_data.assigned_investigator`, `case_data.investigator_license`                                      | Shown beneath agency details and reused in Section 9. |
| client details                        | `case_data.client_name`, `case_data.client_address`, `case_data.client_phone`                            | Displayed before objectives. |
| contract_date                         | `case_data.contract_date`                                                                                | Appears in client metadata and drives case number. |
| motto / tagline                       | `config.templates.cover.motto` (defaults to “Truth Conquers ALL”)                                        | Fixed text block under contact details. |
| branding assets                       | `case_data.branding.logo_path`, `case_data.branding.signature_path`, user profile overrides              | Ensures consistent logo/signature usage. |
| source_documents reference            | `case_data.contract_type_details[].source`, `processed.contracts.keys()`                                 | Stored in manifest for audit and Section 5 cross-reference. |

## Toolkit & AI Triggers
- OpenAI `contract_verification` (post_ocr) – compares contract fields with intake/cover data.
- OpenAI `name_normalization` (pre_render) – enforces consistent formatting of names and titles.

## UI Checklist
- Verify client/investigator names and licenses are current.
- Confirm case number matches contract date and naming convention.
- Approve logo, signature, and motto placement.

## Dependencies
- Disclosure, certification, and final report assembler reuse this cover profile and case number.
- Librarian archive stores cover metadata for search and retrieval.
