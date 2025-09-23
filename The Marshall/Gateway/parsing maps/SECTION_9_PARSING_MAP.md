# Section 9 Parsing Map (Certification & Disclaimers)

## Purpose
Compile investigator certifications, statutory disclaimers, and evidence validation summaries to satisfy jurisdictional requirements before final assembly.

## Data Inputs
| Field | Origin | Notes |
|-------|--------|-------|
| cover_profile | `section_outputs.section_cp.manifest.cover_profile` | Investigator/agency details and branding for signature blocks. |
| compliance_flags | `case_data.compliance_flags` | Outstanding compliance notes requiring disclosure. |
| disclaimer_templates | `case_data.legal.disclaimers` | Jurisdiction-specific statement templates. |
| evidence_validation | `section_outputs.section_8.manifest.validation_summary` | Confirms chain integrity and validation outcomes. |
| limitations | `section_outputs.section_7.manifest.limitations` | Carries forward caveats from conclusions. |

## Toolkit & AI Triggers
- OpenAI `template_integrity` (pre_render) – ensures mandatory clauses appear for the jurisdiction.
- OpenAI `consistency_check` (pre_render) – aligns limitation statements with Section 7 findings.

## UI Checklist
- Confirm investigator certification wording.
- Verify required disclaimers and signature blocks.

## Dependencies
- Feeds: Sections DP and FR reuse disclaimer and certification data.
- Shares: `disclaimers`, `certification`, `limitations`.
