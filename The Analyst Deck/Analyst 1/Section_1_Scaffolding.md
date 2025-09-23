# Section 1 (Investigation Objectives & Case Profile) - Structured Rebuild Roadmap (Draft)

> **Order Lock:** Section 1/Gateway must execute first and cannot be reordered. All downstream operations assume Section 1 is validated and published.

## 1. Mission Statement
Define the investigation mandate, subjects, and jurisdiction so every downstream section operates against the same legally and operationally sanctioned scope.

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
- **Ingress:** Intake packets (contracts, IDs, forms), manual entries, voice/media metadata, toolkit caches.
- **Egress:** `section_1_payload` containing case metadata, subject manifest, continuity flags, QA status, and narrative template.
- **Scope:** Intake normalization, subject validation, contract interpretation, section staging triggers, continuity enforcement.

## 3. Gateway Communication Contract
- `gateway.prepare_section('section_1')` - fired after initial case bundle initialization.
- `gateway.get_section_inputs('section_1')` - returns `{intake_bundle, extracted_metadata, toolkit_cache, manual_overrides}`.
- `gateway.publish_section_result('section_1', payload)` - posts structured output, QA flags, provenance, and stage confirmations.
- `gateway.emit('case_metadata_ready', manifest)` - triggers cover, planning, and other dependent sections.
- `gateway.subscribe('request_case_revision', handler)` - Section 1 listens for downstream conflict requests.

## 4. Stage Checklist & Checkpoints
| Stage | Description | Inputs | Checkpoint |
|-------|-------------|--------|------------|
| Acquire | Load intake docs, register evidence, verify file integrity. | uploads, repository | `s1_acquire_complete` |
| Extract | Run strongest-first extraction (Unstructured/Tesseract) for IDs, contracts, manifests. | evidence index | `s1_extraction_complete` |
| Normalize | Apply parsing maps, toolkit rules (alias dedupe, continuity). | extracted data, toolkit cache | `s1_normalized` |
| Validate | Enforce Cochran/North Star, legal compliance; capture QA issues. | normalized payload | `s1_validated` or `s1_requires_action` |
| Publish | Publish payload to gateway, emit dependency signals. | validated payload | `section_1_completed` |
| Monitor | Listen for revision requests, rerun with updated inputs while enforcing ``max_reruns`` and tracking ``revision_depth``. | downstream signals | `s1_revision_processed` |

## 5. Guardrails & Failsafes
- Reject if mandatory contract fields missing after fallback; push manual task queue entry.
- Confidence thresholds: fail extraction stage if OCR confidence below cutoff without fallback success.
- Strict schema validation on subject manifest, contract terms, jurisdiction fields.
- Change control: any post-publication edits require documented approval stored in payload provenance.
- Immutability: once Section 1 is signed off the payload is frozen; reopen requests require authorization and create a new archived version.
- Audit log: record every engine invocation, fallback, manual edit with timestamps and operator IDs.

## 6. Fallback Hierarchy
1. Unstructured parser (native PDFs/DOCX) + Tesseract OCR (images/scans).
2. EasyOCR/PaddleOCR for low-quality scans; log fallback attempts.
3. Manual confirmation via gateway change queue; section stays `pending_manual` until resolved.
4. Abort: raise `section_blocked` if legal identifiers still unresolved.

## 7. Sectional Staging & Call-Out Procedures
- Section 1 runs before any other section. No exceptions.
- On completion, emit `case_metadata_ready`, `subject_manifest_ready`, `contract_terms_ready` signals.
- Downstream sections request revisions via `request_case_revision`; Section 1 reopens, applies updates, reissues signals.

## 8. Information Handlers
- **Case manifest:** `{case_id, case_name, client_info, contract_scope, jurisdiction, subject_manifest, risk_flags}`.
- **Evidence index:** ties intake artifacts to subjects/contracts for cross-links.
- **Evidence persistence:** Mirror evidence index and section caches to durable storage after each mutation so crashes do not erase routing.
- **Toolkit snapshot:** continuity check results, alias resolutions, QA notes.
- **Fact graph:** Shared entity/timeline graph aligning subjects, evidence IDs, and events for downstream sections.
- **Manual queue:** outstanding tasks requiring reviewer input.

## 9. Narrative & Template Blueprint
- Generate structured narrative entries (objective, scope, subjects, jurisdiction) using sanitized data.
- Templates are hash-locked and run through style lint so unapproved phrasing is flagged; placeholders inserted only when manual acknowledgment recorded.
- Store both `draft_narrative` and `approved_narrative` with diff metadata.

## 10. Dissemination & Intelligence Sharing
- Feed manifest + toolkit results to Sections CP, 2, 3, 5, 6, 7, 8.
- Shared fact graph keeps subject identities and timelines consistent for all consuming sections.
- Receive discrepancy signals (e.g., Section 6 discovers billing scope mismatch) via gateway and reconcile.
- Maintain version history accessible to UI, final assembly, and audit tools.

## 11. Documentation Alignment & Enforcement
- Reference docs:
  - README: `Sections/section_readme/Section_1_README.md`
  - Engines/renderers: `Sections/section_engines/`, `Sections/section_renderers/section_1_renderer.py`
  - Toolkit logic: `MasterToolKitEngine`, `metadata_tool_v_5.py`, `cochran_match_tool.py`, `northstar_protocol_tool.py`
  - SOP: `dev_tracking/templates/Section_1_Rebuild_Playbook.md`, legacy hand-off docs, `CoreSystem/SOP.md`
- Enforcement: map parsing rules into normalization stage; embed doc version hash in payload; add regression tests comparing payload schema to documented contract; update README/SOP whenever schema or workflow changes.

## 12. Implementation To-Do (Section 1)
- [ ] Integrate strongest-first extraction + fallback logic for all intake artifact types.
- [ ] Build master evidence index + cross-linking integrated with gateway.
- [ ] Introduce async routing queues and separate persistence so gateway restarts recover cleanly.
- [ ] Implement normalization pipeline driven by parsing maps and toolkit validations while persisting evidence index caches to disk.
- [ ] Define `section_1_payload` schema (manifest, toolkit snapshot, QA flags, provenance, narrative).
- [ ] Update renderer to consume structured payload, enforce placeholders policy, and log approvals.
- [ ] Add monitoring for downstream revision requests with rerun support, enforcing ``revision_depth`` / ``max_reruns`` caps and immutable sign-off workflows.
- [ ] Build shared fact graph service for cross-section identity/timeline alignment.
- [ ] Extend tests: extraction confidence, fallback path, manual queue, revision loop, persistence reload, async queue scenarios, narrative style lint.
- [ ] Refresh README/SOP and align docs with final implementation; record Section 1 order lock explicitly.

