# Section 9 Parsing Map (Certification & Disclaimers)

## Purpose
Deliver the investigator certification, disclosure of delivered documents, legal disclaimers, and advisory statements that finalize the report package.

## Data Inputs
| Element                                | Source Path(s)                                                                                         | Notes |
|----------------------------------------|--------------------------------------------------------------------------------------------------------|-------|
| investigator certification block       | `section_cp.manifest.cover_profile`, `case_data.assigned_investigator`, user profile signature assets | Populates name, license numbers, contact details, and signature line. |
| delivered documents disclosure         | `section5.document_summaries`, `section8.manifest`, `case_data.disclosure_documents`                  | Lists contract, intake form, final report, supporting reports per template text. |
| legal disclaimers / advisories         | `case_data.legal.disclaimers`, `config.templates.disclaimer_clauses`, `case_data.limitations`          | Contains statements about non-legal advice, handling of sensitive info, etc. |
| compliance_flags / limitations         | `section7.manifest.limitations`, `case_data.compliance_flags`, `toolkit_results.risk_highlight`        | Ensures caveats referenced earlier are repeated here. |
| evidence validation summary            | `section8.manifest.validation_summary`, `processed.metadata.hashes`                                     | Confirms custody and validation status of delivered media. |
| investigator attestation timestamp     | `case_data.certification_timestamp` (fallback `datetime.now`)                                           | Inserted into “statements are true and honest… recorded on (date)” line. |

## Toolkit & AI Triggers
- OpenAI `template_integrity` (pre_render) – confirms mandatory clauses for the jurisdiction are present.
- OpenAI `consistency_check` (pre_render) – aligns disclaimers with Section 7 limitations and Section 5 document list.

## UI Checklist
- Validate signature block contains current license numbers and contact info.
- Review the delivered-document list against Section 5 inventory.
- Confirm advisory statements match firm policy and jurisdictional language.

## Dependencies
- Disclosure Page (DP) mirrors these statements for standalone delivery.
- Final assembly bundles these clauses with the certification signature page.
- Librarian archive records certification timestamp and disclosure text for audit.
