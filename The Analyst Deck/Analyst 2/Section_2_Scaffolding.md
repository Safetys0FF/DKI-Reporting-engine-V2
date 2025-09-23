# Section 2 (Pre-Surveillance / Case Preparation) - Structured Rebuild Roadmap (Draft)

> **Order Lock:** Section 1/Gateway must execute first and must not be reordered. Section 2 runs only after Section 1 confirmation.

## 1. Mission Statement
Transform intake and toolkit intelligence into operational plans describing subjects, routines, locations, and directives for field teams.

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
- **Ingress:** Gateway bundle with `case_metadata`, `subject_manifest`, `planning_docs`, OSINT cache, toolkit results, Section 1 manifest.
- **Egress:** `section_2_payload` containing planning narratives, subject verification tables, geospatial anchors, risk flags, QA notes.
- **Scope:** Subject verification, routine synthesis, geospatial prep, OSINT validation, directive staging.

## 3. Gateway Communication Contract
- `gateway.prepare_section('section_2')` – triggered after Section 1 sign-off and Section CP readiness.
- `gateway.get_section_inputs('section_2')` – returns `{case_metadata, subject_manifest, planning_docs, osint_cache, toolkit_results}`.
- `gateway.publish_section_result('section_2', payload)` – posts structured output, QA flags, provenance, stage confirmations.
- `gateway.subscribe('case_metadata_revision', handler)` – rehydrate if Section 1 manifests change.
- `gateway.emit('planning_ready', manifest)` – signals Sections 3/4/6/8 when planning directives validated.

## 4. Stage Checklist & Checkpoints
| Stage | Description | Inputs | Checkpoint |
|-------|-------------|--------|------------|
| Intake | Pull gateway bundle, confirm Section 1 hash, load planning documents. | case bundle | `s2_intake_logged` |
| Verify | Confirm subject identities (aliases, IDs) via toolkit/OSINT. | subject_manifest, osint | `s2_subjects_verified` |
| Analyze | Derive routines, timelines, geospatial anchors using parsing maps/tooling. | planning docs, toolkit cache | `s2_analysis_complete` |
| Validate | Apply policy checks (North Star, Cochran continuity), risk scoring, compliance. | analysis output | `s2_validated` or `s2_requires_action` |
| Publish | Publish payload to gateway, emit planning signals. | validated payload | `section_2_completed` |
| Monitor | Handle revision requests (planning conflicts, subject updates) while enforcing ``max_reruns`` and logging ``revision_depth``. | downstream signals | `s2_revision_processed` |

## 5. Guardrails & Failsafes
- Block execution if Section 1 status != validated or subject manifest missing required fields.
- Enforce structured schema for planning narratives and geospatial entries; no free text beyond templates.
- Require dual confirmation for high-risk directives; provenance must capture reviewers.
- Freeze OSINT-derived data; log confidence scores and sources.
- Manual queue entry required for unresolved identity conflicts or missing addresses.
- Immutability: once Section 2 is signed off the planning manifest is locked; reopen requests require authorization and create a new archived version.

## 6. Fallback Hierarchy
1. Toolkit-normalized values (subject aliases, addresses, routines).
2. OSINT lookup (smart_lookup) for missing fields; log `fallback_attempts` with confidence.
3. Manual confirmation via gateway task queue.
4. Abort with `section_blocked` if critical operational data absent.

## 7. Sectional Staging & Call-Out Procedures
- Runs after Section 1 and Section CP.
- Emits `planning_ready` (subject directives, geospatial anchors) to Sections 3, 4, 6, 8.
- Handles `request_planning_revision` signals; reprocesses analysis, updates payload, reissues signals.

## 8. Information Handlers
- **Planning manifest:** subjects, verified identities, routines, POIs, timelines, risk flags, compliance notes.
- **Geospatial index:** coordinates, maps, sources; hash map to media assets.
- **OSINT log:** queries, results, confidence, timestamps.
- **Manual queue:** outstanding tasks (identity confirmation, address validation).

## 9. Narrative Blueprint
- Structured sections: case summary, subject verification, patterns/timelines, geospatial prep, directives.
- Template enforces factual tone; placeholders only when manual tasks open.
- Store `draft_planning` and `approved_planning` with change log.

## 10. Dissemination & Intelligence Sharing
- Provide planning manifest to Sections 3, 4, 6, 8 and UI briefing views.
- Share agreed subject/timeline facts via the fact graph so downstream sections stay aligned.
- Receive feedback (e.g., Section 3 logs conflict) and reconcile updates.
- Maintain version history for audit and final assembly.
## 11. Documentation Alignment & Enforcement
- Reference docs:
  - README: `Sections/section_readme/Section_2_README.md`
  - Engines/renderers: `Sections/section_engines/`, `section_renderers/section_2_renderer.py`
  - Toolkit logic: `metadata_tool_v_5.py`, `northstar_protocol_tool.py`, `cochran_match_tool.py`, `smart_lookup.py`
  - SOP: `dev_tracking/templates/Section_2_Rebuild_Playbook.md`, `CoreSystem/SOP.md`
- Enforcement: map parsing logic into analysis stage; embed doc version hash; regression tests for payload schema vs documented contract; updates require README/SOP sync.

## 12. Implementation To-Do (Section 2)
- [ ] Wire gateway input handling with Section 1 order lock checks.
- [ ] Implement subject verification using toolkit + OSINT, with fallbacks and manual queue integration.
- [ ] Build analysis pipeline (routines, timelines, geospatial) using parsing maps.
- [ ] Define `section_2_payload` schema (planning manifest, geospatial index, risk flags, QA status).
- [ ] Update renderer to consume structured payload, enforce templates, and log approvals.
- [ ] Add signals for `planning_ready`, `request_planning_revision`, and rerun flow.
- [ ] Extend tests: verification fallbacks, OSINT integration, manual queue, revision loop, ``max_reruns`` guardrails, narrative style lint.
- [ ] Refresh README/SOP and record Section 1 order lock note.
