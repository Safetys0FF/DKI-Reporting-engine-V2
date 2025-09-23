# Section 5 Parsing Map (Supporting Documents Review)

## Purpose
Catalogue non-media evidence (contracts, public records, legal filings) with custody notes and appendix candidates to support conclusions and disclosures.

## Data Inputs
| Field | Origin | Notes |
|-------|--------|-------|
| documents | `processed.contracts` + `processed.forms` | OCR-normalised documents for summary and categorisation. |
| metadata_reports | `processed.metadata.reports` | Auto-generated analytics (hashes, classifications, provenance). |
| custody | `processed.manual_notes.custody` | Chain-of-custody commentary for document sets. |
| appendix_candidates | `case_data.appendices` | User-selected documents flagged for inclusion in appendices. |

## Toolkit & AI Triggers
- OpenAI `doc_classification` (post_ocr) – categorises documents and extracts highlights.
- OpenAI `risk_highlight` (post_ocr) – flags clauses that introduce liability or compliance risk.

## UI Checklist
- Confirm custody trails for critical documents.
- Approve document summaries and appendix selections.

## Dependencies
- Feeds: Sections 7, 9, and DP consume document summaries and liabilities.
- Shares: `document_summaries`, `appendices`, `custody`.
