# Section 6 – Billing Summary Guide

## Overview
Section 6 converts operational data into a transparent billing statement. It combines contract structures, planning costs, field time, subcontractor expenses, mileage, and documentation labor into a defensible summary. The renderer adapts to Investigative, Surveillance, and Hybrid modes and produces both a data model for finance systems and formatted output for the report.

## Required Inputs & Extraction Workflow
- **Document Processor & Repository Manager**: ingest contract totals, retain contract chronology, and expose `processed_data['contract_total']`, `prep_cost`, and other financial inputs (either from intake documents or repository metadata).
- **Toolkit Modules**:
  - `mileage_tool_v_2.py` calculates mileage/time logs from Section 3 windows.
  - `northstar_protocol_tool.py` verifies travel claims align with actual movement.
  - `billing_tool_engine.py` applies rules for flat-rate, hourly, and hybrid contracts (including the $500 planning reservation and multi-contract stacking).
- **Section Metadata**: Section 1 determines report mode; Section 2 identifies planning scope; Sections 3/4 supply operational hours; Section 5 may add document retrieval costs. Voice transcription metadata corroborates time spent on audio review when applicable.

## Data Handling & Calculation
- Renderer builds a billing data model with:
  - Contract totals and prep/subcontractor costs.
  - Remaining operations budget and internal margin.
  - Billing sections (categories with descriptions) tuned per report type.
  - Notes highlighting special conditions (flat-rate transfers, multi-contract rules, planning fee removal when prior contracts exist).
- Totals and margins are recalculated on every run to include the latest toolkit adjustments.

## Cross-Reference & Validation
- Section 6 references Section 1’s contract mode to choose billing patterns.
- Mileage/time values cross-checked against Section 3 logs; toolkit flags anomalies before report approval.
- Billing notes indicate whether voice/media review exhausted part of the budget, ensuring transparency for clients.
- For hybrid cases, the billing summary documents each contract separately to match repository records.

## Reporting Expectations
- Provide a clear financial overview followed by detailed breakdowns and notes.
- Show how planning, field work, travel, documentation, and margin fit together.
- Align terminology with contracts and Statements of Work to avoid disputes.

## Inter-Section & Gateway Flow
- Output includes `billing_model` so finance exports can reuse calculations outside the rendered report.
- Gateway stores Section 6 data to validate final assembly before approving PDF/DOCX generation.
- If new contracts are added mid-case, `_ensure_gateway_case_initialized()` and toolkit passes re-run to update Section 6 automatically.

## Presentation Guidelines
- Use consistent headers (`CONTRACT OVERVIEW`, `BILLING BREAKDOWN`, `FINANCIAL SUMMARY`, `BILLING NOTES`).
- Monetary values formatted with currency and thousand separators.
- Notes should be bullet-style sentences describing triggers (planning fee applied, multi-contract mode active, etc.).

## Parsing Map Reference
The detailed parsing and validation map for this section is kept at F:\Report Engine\Gateway\parsing maps\SECTION_6_PARSING_MAP.md. Consult it for data sourcing, OpenAI trigger timing, and UI checklist expectations.

