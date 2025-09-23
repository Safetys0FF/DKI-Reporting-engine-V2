# Section CP Parsing Map (Cover Page)

## Purpose
Summarise case identity, client and investigator credentials, and branding assets before the report enters approval.

## Data Inputs
| Field | Origin | Notes |
|-------|--------|-------|
| client_info | `case_data.client_info`, `processed.metadata.client_info` | Intake and OCR-verified client contact details. |
| client_profile | `case_data.client_profile`, toolkit metadata | Preferred branding, signatures, profile photo overrides. |
| agency_profile | `toolkit_results.metadata.agency` | Agency licensing and contact information. |
| contract_snapshot | `processed.contracts` | Contract terms used for case identifiers and verification. |
| branding_assets | merged from profile & metadata | Logo, signature, photo paths for rendering. |
| case_number | computed via `_compute_case_number` | Derived from client name and contract date. |
| source_documents | `processed.contracts.keys()` | Tracks contract files backing the cover data. |

## Toolkit & AI Triggers
- OpenAI `contract_verification` (post_ocr) – compares OCR’d contract fields with intake data.
- OpenAI `name_normalization` (pre_render) – enforces consistent presentation of names/titles.

## UI Checklist
- Confirm client and investigator names.
- Verify licensing/contact data are current.
- Approve branding assets (logo, signature, photo).

## Dependencies
- Feeds: Sections DP and 9 reuse cover profile and case number.
- Shares: `cover_profile`, `case_number`, `branding_assets`.
