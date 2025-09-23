# AUTO REPORT-TYPE DETECTION PLAN — 2025-09-14 (Read-Only)

Findings
- Fallback logic docs state Section 1 determines `report_type` (Investigative, Field, Hybrid) based on contract type, intake goals, field-work clauses, and contract count. Default fallback: Field.
- Current Python code does not auto-detect report type. `gateway_controller.initialize_case()` expects an explicit `report_type`. Renderers read `section_payload['report_type']` but do not infer it.
- Naming mismatch exists: core configs and Section 6 renderer reference "Field", while `gateway_controller` uses "Surveillance". A synonym mapping is needed.

Proposal
- Add autonomous report-type inference into `gateway_controller` with a backward-compatible path.

Design
- Entry point: `GatewayController.initialize_case(report_type: Optional[str], case_data: Dict[str, Any])`
  - If `report_type` is None or in {"auto", "Auto", "AUTO"} → call `_infer_report_type(case_data)`.
  - Else, accept provided report_type (after alias normalization), e.g., "Field" → "Surveillance".
- Alias normalization: accept {"Field", "Surveillance"} as the same variant; standardize internally to "Surveillance" while preserving original for outputs if needed.
- `_infer_report_type(case_data: Dict[str, Any], extras: Optional[Dict[str, Any]] = None) -> str`:
  - Signals:
    - contract_type, contract_name, or case_data['contract_type'] textual cues
    - intake goals text (investigation_goals)
    - presence of field-work clauses/flags (case_data['field_work'] / 'field_ops')
    - evidence of field artifacts (surveillance logs/section_3, section_4, media with field timestamps)
    - multiple active contracts → consider Hybrid
  - Heuristics:
    - explicit terms: "Investigative" → Investigative; "Field"/"Surveillance" → Surveillance; "Hybrid" → Hybrid
    - goals contain {surveillance, field, observe, tail, follow} → Surveillance cue
    - goals contain {desk, records, background, analysis, intake only} → Investigative cue
    - both cues present or contract mix → Hybrid
    - fallback when ambiguous → Field (per fallback guide) → map to Surveillance internally
- Persistence and propagation:
  - Set `self.current_report_type` to normalized type
  - Stamp `processing_log` with inference rationale
  - Inject into `section_payload` for CP/TOC and subsequent sections
  - Allow per-run override via provided `report_type` argument

Back-compat
- Existing callers that pass explicit report_type continue to work unchanged.
- Components that expect "Field" continue to receive acceptable values through alias mapping.

Validation
- Unit-like scenarios in a harness:
  - Case with only intake/desk goals → Investigative
  - Case with surveillance goals or field flags/media → Surveillance
  - Case with both (or two contracts) → Hybrid
  - No contract match → default Field (normalized to Surveillance)

Next Steps (upon approval)
1) Implement `_infer_report_type` and call it from `initialize_case()` when report_type not provided/auto.
2) Add alias normalization and guardrails (strict value set).
3) Log rationale to `processing_log` and propagate type to section payloads.
4) Document change in read-only change record and notify agents in Handshakes.

References
- dev_tracking/archives/CORE_OPERATIONS_HANDBOOK.md
- Section 4 - Review of Surveillance Sessions.txt (Section 1 logic + fallbacks)

Timestamp: 2025-09-14
Author: POWER Agent (Core Functions)

