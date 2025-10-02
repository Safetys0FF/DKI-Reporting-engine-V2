# Section 5 Parsing Map (Supporting Documents Review)

## Purpose
List every supporting artifact supplied to the client—contracts, intake forms, background reports, subpoenas, sheriff retrieval logs—with short descriptions and custody notes for the disclosure statement.

## Data Inputs
| Document Category                        | Source Path(s)                                                                                          | Notes |
|------------------------------------------|---------------------------------------------------------------------------------------------------------|-------|
| Client Intake Form                       | `processed.forms.client_intake`, `case_data.intake_form`                                               | Appears last in template to demonstrate contractual scope. |
| Client Contract(s)                       | `processed.contracts`, `case_data.contract_type_details`                                                | Include contract title, signed date, classification, and custody hash. |
| Background / Investigative Reports       | `processed.metadata.reports.background`, `processed.manual_notes.supporting_reports`                    | Populate template bullet “Background Report” lines with cost linkage. |
| Legal Filings / Court Documents          | `processed.forms.legal`, `case_data.legal_documents`                                                    | Display case number, filing date, associated authority. |
| Sheriff Retrieval / Service Reports      | `processed.manual_notes.sheriff_reports`, `processed.metadata.sheriff_logs`                              | Feed the “Sheriff Retrieval Report” slot with report IDs. |
| Additional Exhibits                      | `case_data.supporting_documents`, `appendix_candidates`                                                 | Items flagged for appendix inclusion (photos, recordings, transcripts). |
| Custody Chain                            | `processed.manual_notes.custody`, `processed.metadata.hashes`                                           | Used to note collection method, hash, and storage path. |

## Toolkit & AI Triggers
- OpenAI `doc_classification` (post_ocr) – categorises each document and suggests summary sentences.
- OpenAI `risk_highlight` (post_ocr) – flags liability clauses or missing signatures requiring investigator review.
- Toolkit hash validator records SHA256 and ingest timestamps for custody log.

## UI Checklist
- Confirm intake form, contract, and key reports are present and summarised.
- Verify custody notes and hashes for each critical document.
- Ensure appendix candidates align with disclosure requirements.

## Dependencies
- Section 6 billing references document costs (background checks, reports).
- Disclosure page cites this inventory when listing delivered documents.
- Final report export uses custody hashes for archive manifest.
