# Section FR Rebuild Playbook (Draft)

## 1. Mission & Theory of Operation
Compile approved sections into the final export package while enforcing order, completeness, and provenance tracking.

## 2. Functional Responsibilities
- Primary deliverable: Final Assembly output aligned with case governance.
- Evidence sources: Gateway section outputs, approval states, case snapshot.
- Quality focus: Ensure outputs remain admissible, consistent, and aligned with investigative objectives.

## 3. Engine Architecture & Data Flow
- Intake triggers: Gateway dispatches the section when required inputs are confirmed in the master case bundle.
- Processing stages:
  1. Pull structured inputs from gateway bundle (case data, prior sections, media manifests).
  2. Execute section-specific tooling under deterministic order (strongest engines first, fallbacks gated).
  3. Normalize results into `section_fr_payload` with `render_tree`, `manifest`, and validation flags.
- Output hand-off: Publish structured payload back to the gateway; mark stage completion with confirmation timestamp.

## 4. Tooling & Dependencies
- Core tooling: ReportGenerator, export templates, manifest validators.
- Optional accelerators: GPU-enabled OCR, external OSINT/AI APIs, geocoding services (enable via gateway policy).
- Configuration hooks: Section-specific feature flags, environment variables, and credential stores managed by the gateway.

## 5. Stage & Trigger Map
| Stage | Description | Trigger | Confirmation |
|-------|-------------|---------|--------------|
| Preparation | Verify prerequisite sections and toolkit caches are available. | Gateway `stage_ready` event. | Dependency checklist logged. |
| Extraction/Analysis | Run primary engines and transform data into section schema. | Section engine start. | Schema validation + sanity checks. |
| Enrichment | Invoke optional tools (AI, OSINT, QA) as requested by section logic. | Conditional, per field or directive. | Result availability + audit note. |
| Publication | Post payload to gateway and request approval. | Output ready. | Gateway records `completed` state. |

## 6. Fallback & Resilience Strategy
- Prioritise strongest engines; only fall back when confidence < threshold or data missing.
- Log every fallback with `fallback_attempts` for audit review.
- If all engines fail, raise `section_blocked` to the gateway so remediation (manual entry, reprocessing) can occur before final assembly.

## 7. Gateway & Cross-Section Communication
- Inputs pulled via `gateway.get_section_inputs('section_fr')`.
- Outputs pushed through `gateway.publish_section_result('section_fr', payload)`.
- Shared data contracts:
  - Provide digestible manifests for downstream sections (Relies on every section’s completion, publishes export status to UI, stores provenance for audits.).
  - Subscribe to status signals from related sections to handle sequencing without race conditions.

## 8. Operational SOP
1. Gateway marks prerequisites satisfied and issues `prepare_section_fr` command.
2. Section engine hydrates context, validates schema versions, and logs start event.
3. Execute primary extraction/analysis pipeline.
4. Run enrichment modules as required by configuration or detected flags.
5. Perform QA/continuity checks; embed confirmations in manifest.
6. Publish payload to gateway and request review/approval.
7. Respond to change requests or reruns via gateway-issued deltas.

## 9. README Refresh Outline
- Mission statement mirroring section overview.
- Input requirements and data sources.
- Tooling stack with version pinning.
- Data flow diagram (textual) highlighting gateway touchpoints.
- Fallback policies and manual override instructions.
- Approval workflow and sign-off expectations.

## 10. Implementation Checklist
- [ ] Refactor section engine to pull from gateway bundle and apply strongest-first tool ordering.
- [ ] Update schemas (`section_fr_payload`, manifests) to include confirmations, fallbacks, and provenance.
- [ ] Instrument gateway triggers/signals for preparation, completion, and rerun.
- [ ] Refresh section README and SOP using this playbook.
- [ ] Add regression tests covering primary flow, fallback flow, and gateway handshake.
- [ ] Coordinate with Final Assembly to consume the new payload shape.

