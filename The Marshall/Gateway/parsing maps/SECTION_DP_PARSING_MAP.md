# Section DP Parsing Map (Disclosure Page)

## Purpose
Present disclosure statements, distribution controls, and acknowledgment steps derived from the cover profile and compliance data.

## Data Inputs
| Field | Origin | Notes |
|-------|--------|-------|
| cover_profile | `section_outputs.section_cp.manifest.cover_profile` | Base branding and agency contact info. |
| disclosures | `case_data.legal.disclosures` | Jurisdiction-required disclosure text. |
| distribution_list | `case_data.distribution_list` | Recipients for packaged reports and evidence. |
| delivery_instructions | `case_data.delivery_instructions` | Special handling, secure transfer guidance. |
| acknowledgment | `case_data.acknowledgment` | Client sign-off or receipt requirements. |

## Toolkit & AI Triggers
- OpenAI `clause_verification` (pre_render) – validates confidentiality and client responsibility clauses.

## UI Checklist
- Approve disclosure clauses and distribution list.
- Ensure acknowledgment instructions are complete.

## Dependencies
- Feeds: Section FR references distribution/delivery instructions during export.
- Shares: `disclosures`, `distribution_list`, `delivery_instructions`.
