# Section 6 (Billing Summary) - Structured Rebuild Roadmap (Draft)

> **Order Lock:** Section 1/Gateway runs first. Section 6 depends on Sections 1-3 outputs (plus Section 5 for supporting docs) and must respect that order.

## 1. Mission Statement
Translate operational data into a transparent billing statement backed by validated scope, time, mileage, and expense records.

 - Information reference guide
         "F:\DKI-Report-Engine\Report Engine\Logic files\canvas logic for report"
         "F:\DKI-Report-Engine\Report Engine\Sections\section_readme"
         "F:\DKI-Report-Engine\Report Engine\Gateway"
         "F:\DKI-Report-Engine\Report Engine\Sections\section_engines"
         "F:\DKI-Report-Engine\Report Engine\Gateway\parsing maps"
         "F:\DKI-Report-Engine\Report Engine\Gateway\section_readme"
         "F:\DKI-Report-Engine\Report Engine\dev_tracking\templates"
      
      - Boot up sequences and testing procedures
         "F:\DKI-Report-Engine\Report Engine\Start Menu"

      - Tools sets and engines
         "F:\DKI-Report-Engine\Report Engine\Plugins"
 
## 2. System Context
- **Ingress:** Gateway bundle with `case_metadata`, `contract_terms`, `planning_manifest` (Section 2), `surveillance_manifest` (Section 3), mileage/time data, toolkit PA metrics, document inventory references.
- **Egress:** `section_6_payload` containing billing breakdown, cost tables, audit notes, QA flags, provenance.
- **Scope:** Cost aggregation, rate application, compliance validation, summary generation for client and finance systems.

## 3. Gateway Communication Contract
- `gateway.prepare_section('section_6')` – triggered after Sections 2 & 3 emit readiness signals (and optional doc references from Section 5).
- `gateway.get_section_inputs('section_6')` – returns `{case_metadata, contract_terms, planning_manifest, surveillance_manifest, mileage_data, toolkit_results, document_references}`.
- `gateway.publish_section_result('section_6', payload)` – posts billing output, QA flags, provenance, stage confirmations.
- `gateway.subscribe('surveillance_revision', handler)` – rerun if Section 3 updates time/mileage.
- `gateway.emit('billing_ready', manifest)` – notify UI, Section 7, FR when summary validated.

## 4. Stage Checklist & Checkpoints
| Stage | Description | Inputs | Checkpoint |
|-------|-------------|--------|------------|
| Intake | Pull billing inputs, confirm Section 1/2/3 hashes, load contract terms. | gateway bundle | `s6_intake_logged` |
| Aggregate | Compute mileage/time, subcontractor costs, prep costs, expenses using toolkit modules. | surveillance/planning, toolkit | `s6_aggregate_complete` |
| Validate | Enforce contract rules, scope compliance, continuity checks; record QA issues. | aggregated data | `s6_validated` or `s6_requires_action` |
| Publish | Publish billing payload to gateway, emit billing signal. | validated payload | `section_6_completed` |
| Monitor | Handle revisions (from Section 3 updates or manual adjustments) while enforcing ``max_reruns`` and tracking ``revision_depth``. | signals | `s6_revision_processed` |

## 5. Guardrails & Failsafes
- Execution blocked until Section 1 confirms contract scope and professional credentials.
- Cross-check hours/mileage against Section 3 logs; mismatches flagged.
- Validate expenses against contract constraints; out-of-scope charges require manual approval.
- Manual adjustments logged with operator ID and justification; dual sign-off for overrides.
- Immutability: once billing is approved the payload is frozen; reopen requests require authorization and archive prior versions.
- Chain-of-custody for cost entries (source logs, receipts) maintained.

## 6. Fallback Hierarchy
1. Toolkit-derived metrics (mileage_tool_v_2, planning manifest, surveillance logs).
2. Manual entry via gateway queue for missing data after fallback.
3. Abort with `section_blocked` if critical billing inputs absent.

## 7. Sectional Staging & Call-Out Procedures
- Runs after Sections 2 and 3.
- Emits `billing_ready` to Section 7, UI, FR.
- Receives `request_billing_revision` from conclusions, UI, or final assembly; reruns with adjustments.

## 8. Information Handlers
- **Billing manifest:** breakdown by category (prep, field time, mileage, expenses), approvals, QA status.
- **Persistence:** Billing manifest and source references are saved to durable storage after each update.
- **Source references:** links to logs, receipts, contract clauses.
- **Manual queue:** adjustments or pending approvals.
- **Audit log:** version history for cost entries.

## 9. Narrative Blueprint
- Provide structured billing summary (tables) with optional narrative note per category using hash-locked templates and style lint.
- Placeholder notes only when manual approval pending.

## 10. Dissemination & Intelligence Sharing
- Share billing summary with Section 7, final assembly, finance systems.
- Update shared fact graph nodes with billed effort to keep downstream analytics aligned.
- Receive feedback (e.g., conclusion indicates missing charges) and reconcile.
- Maintain version history for audit/exports.
## 11. Documentation Alignment & Enforcement
- Reference docs:
  - README: `Sections/section_readme/Section_6_README.md`
  - Engines/renderers: `Sections/section_engines/`, `section_renderers/section_6_renderer.py`
  - Toolkit logic: `billing_tool_engine.py`, `mileage_tool_v_2.py`, `northstar_protocol_tool.py`
  - SOP: `dev_tracking/templates/Section_6_Rebuild_Playbook.md`, `CoreSystem/SOP.md`
- Enforcement: apply parsing rules in aggregation stage; embed doc version hash; regression tests for billing schema vs documentation; update README/SOP on change.

## 12. Implementation To-Do (Section 6)
- [ ] Integrate gateway inputs with Section 1 order lock verification.
- [ ] Implement cost aggregation pipeline using toolkit modules and validations with persistence write-through.
- [ ] Define `section_6_payload` schema (billing manifest, references, QA flags, provenance).
- [ ] Update renderer to output structured summary, ensuring compliance notes logged.
- [ ] Add signals for `billing_ready`, revision handling, and conflict resolution.
- [ ] Extend tests: aggregation accuracy, contract rule enforcement, manual queue, revision loop, ``max_reruns`` guardrails, narrative style lint.
- [ ] Refresh README/SOP with final architecture and note Section 1 order lock.
