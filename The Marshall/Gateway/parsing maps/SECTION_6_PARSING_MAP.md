# Section 6 Parsing Map (Billing Summary)

## Purpose
Present a transparent cost breakdown—planning budget usage, surveillance hours, documentation labour, and retainer reconciliation—mirroring the template’s billing worksheet.

## Data Inputs
| Billing Element                          | Source Path(s)                                                                                         | Notes |
|------------------------------------------|--------------------------------------------------------------------------------------------------------|-------|
| Planning Budget ($500 default)           | `case_data.planning_budget` (defaults to 500), `processed.expenses.pre_investigation`                 | Covers background checks, reconnaissance, and pre-surveillance services. |
| Background report line items             | `processed.metadata.reports.background`, `processed.manual_notes.billing.reports[]`                  | Amount and report type populate “Client Background Report” etc. |
| Surveillance budget & contract total     | `case_data.contract_total`, `case_data.contract_surveillance_budget`, `case_data.retainers.applied`  | Source of “Contracted Amount”, “Surveillance Fieldwork Budget”, remaining balance. |
| Billed surveillance hours                | `section3.render_manifest.total_hours`, `processed.summary.time_entries`, toolkit billing validation | Populates per-day line items and subtotal for field work. |
| Documentation & reporting fee            | `case_data.documentation_hours`, `case_data.documentation_rate`, default 1 hr @ $100                 | Pulled into “Final documentation & report compilation”. |
| Expenses / Receipts                      | `processed.manual_notes.expenses`, `toolkit_results.receipt_verification`                             | Deducted from planning or surveillance budget depending on type. |
| Retainer ledger                          | `case_data.retainers.total`, `case_data.retainers.applied`, `case_data.retainers.remaining`          | Drives “Total Retainer Applied” and “Remaining Balance after Planning”. |
| Variance / overage flags                 | `toolkit_results.billing_validation.variance`, `toolkit_results.narrative_reconciliation.flags`      | Used for notes (e.g., overage requiring client approval). |
| Supporting document links                | `section5.document_summaries`, `processed.metadata.hashes`                                            | Back references to receipts and reports cited in Section 5. |

## Toolkit & AI Triggers
- OpenAI `narrative_reconciliation` (pre_render) – aligns billed hours with Section 3 timeline.
- OpenAI `receipt_verification` (pre_render) – summarises receipts and flags duplicates or missing docs.
- Billing validation toolkit ensures budgets and retainers balance against contract terms.

## UI Checklist
- Confirm planning budget deductions match background reports and reconnaissance inputs.
- Review surveillance hours vs contracted allowance; resolve overage warnings.
- Ensure retainer ledger totals equal contract amount and indicate any remaining balance owed.

## Dependencies
- Section 7 conclusion cites final billing posture.
- Disclosure page references total amounts and remaining balance.
- Debrief/Librarian export uses this breakdown for financial manifest.
