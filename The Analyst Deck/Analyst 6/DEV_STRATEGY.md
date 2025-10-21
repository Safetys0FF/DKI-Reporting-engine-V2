# Section 6 – Development Strategy & Runbook

## Mission Profile
- **Scope:** Billing reconciliation, time/mileage validation, expense ledgers, compliance with retainers.
- **Primary Outputs:** `section_6_billing` payload with reconciled line items, variance reports, compliance flags.
- **Signals:** publishes `section_6_billing.completed`, consumes `section.needs` categories `["billing"]`, faults via `section.fault.4-6`.

## Planned Dependency Map
| Artifact / Engine | Status | Notes |
| --- | --- | --- |
| EvidenceManager | 🔄 `_init_evidence_manager.py`. |
| OCR stack | 🔄 Unstructured → Tesseract → EasyOCR (for scanned invoices). |
| Billing calculator | ✅ existing `section_6_billing.py` logic → wrap in `_init_billing_calculator.py`. |
| Mileage audit | ✅ reuse `_init_mileage_audit.py` (Section 1). |
| Ledger validator | ⏳ implement `_init_ledger_validator.py` (retainer vs. expense rules). |
| Narrative renderer | ⏳ `_init_section6_renderer.py` for billing summary. |
| Currency/timezone normalizer | ⏳ create `_init_financial_formatter.py`. |

## Lifecycle Checklist
1. Baseline: verify all calculators + rule definitions load; fail if configuration missing (e.g., thresholds).
2. Rest: coordinate with Sections 5 & 7 (shared data) to avoid concurrent writes; use `enter_rest_state`.
3. Shutdown: ensure data snapshots persist, emit `section.shutdown` summary.
4. Faults: differentiate between data inconsistencies (variance) vs. technical failures (parser crash).

## Development Workflow
1. Port legacy framework into lifecycle base, swapping inline imports for `_init_*` adapters above.
2. Pipeline outline:
   - Acquire evidence (time logs, invoices, retainers).
   - Extract data (OCR, CSV parsing).
   - Normalize amounts/timezones.
   - Reconcile vs. retainers/contracts, flag variances.
   - Publish structured ledger + narrative summary.
3. Testing:
   - Unit: baseline init, billing calculator accuracy, variance detection.
   - Provide sample CSV/PDF fixtures in `Analyst 6/Tests/fixtures`.
   - Future: integration smoke verifying cross-talk with Section 5 and Section 7 analytics.
4. Documentation:
   - Record formulae, tolerance thresholds, currency conversions in this README.
   - Update dev logs with any rule changes to keep analysts aligned.

## Backlog
- Define canonical schema for `billing_line_items`.
- Integrate mileage/time audit results from Section 1 to avoid duplicate calculations.
- Add support for multi-currency cases and tax handling.
- Plan dataset for automated regression (retainer overage, missing receipts).

Keep this strategy current so agents can extend Section 6 in unison, using the same dependency model and lifecycle expectations.***
