# Section 6 Parsing Map (Billing Summary)

## Purpose
Provide transparent accounting for billable work by reconciling investigative activity, expenses, and toolkit billing validation.

## Data Inputs
| Field | Origin | Notes |
|-------|--------|-------|
| time_entries | `processed.summary.time_entries` | Hourly logs mapped to timeline events.
| expense_receipts | `processed.manual_notes.expenses` | Receipt metadata, amounts, links to supporting documents.
| contract_terms | `case_data.contract` or first `processed.contracts` entry | Baseline rates, retainers, reimbursement limits.
| subcontractor_invoices | `processed.manual_notes.subcontractor_invoices` | External vendor costs awaiting approval.
| billing_validation | `toolkit_results.billing_validation` | Toolkit anomalies, warnings, and variance metrics.

## Toolkit & AI Triggers
- OpenAI `narrative_reconciliation` (pre_render) – aligns billed hours with Section 3 timeline.
- OpenAI `receipt_verification` (pre_render) – summarises receipts and detects duplicates.

## UI Checklist
- Link every line item to supporting evidence.
- Confirm totals match contract terms and retainers.

## Dependencies
- Feeds: Sections 7 and FR incorporate billing totals and notes.
- Shares: `billing_totals`, `variance_notes`, `supporting_links`.
