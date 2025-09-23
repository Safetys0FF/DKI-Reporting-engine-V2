# Section 4 (Review of Surveillance Sessions) - Structured Rebuild Roadmap (Draft)

> **Order Lock:** Section 1/Gateway executes first. Section 4 depends on Sections 1, 2, and 3 completion and must respect that order.

## 1. Mission Statement
Convert structured surveillance logs and evidence into court-ready narratives tied to investigative objectives and planning directives.

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
- **Ingress:** Gateway bundle with `case_metadata`, `planning_manifest` (Section 2), `surveillance_manifest` (Section 3), toolkit continuity results, media cross-links, voice transcripts.
- **Egress:** `section_4_payload` containing analytical narratives, subject summaries, evidence references, QA flags, compliance notes, provenance.
- **Scope:** Interpret surveillance entries, enforce continuity checks, tie observations to objectives, produce compliant narratives.

## 3. Gateway Communication Contract
- `gateway.prepare_section('section_4')` – triggered after Section 3 emits `surveillance_ready`.
- `gateway.get_section_inputs('section_4')` – returns `{case_metadata, planning_manifest, surveillance_manifest, media_index, toolkit_results}`.
- `gateway.publish_section_result('section_4', payload)` – stores structured output, QA flags, provenance, stage confirmations.
- `gateway.subscribe('surveillance_revision', handler)` – respond to Section 3 updates.
- `gateway.emit('session_review_ready', manifest)` – notify Section 7 and final assembly of narrative availability.

## 4. Stage Checklist & Checkpoints
| Stage | Description | Inputs | Checkpoint |
|-------|-------------|--------|------------|
| Intake | Pull inputs, confirm upstream hashes, load toolkit continuity data. | gateway bundle | `s4_intake_logged` |
| Analyze | Map surveillance entries to planning objectives, generate narrative segments, link evidence. | surveillance + planning | `s4_analysis_complete` |
| Validate | Apply Cochran/North Star checks, ensure factual tone, log QA issues. | narratives, toolkit | `s4_validated` or `s4_requires_action` |
| Publish | Publish payload to gateway, emit session review signal. | validated payload | `section_4_completed` |
| Monitor | Handle revision requests from downstream sections (7, FR) or upstream corrections while enforcing ``max_reruns`` and logging ``revision_depth``. | signals | `s4_revision_processed` |

## 5. Guardrails & Failsafes
- Execution blocked until Sections 1-3 validated.
- Narrative templates enforce factual language; speculation flagged and requires manual approval.
- Evidence references must resolve to media IDs; missing links push entry to manual queue.
- Continuity failures (timeline gaps, unauthorized subject references) block publication until resolved.
- Manual edits logged with operator/timestamp; approvals recorded in payload provenance.
- Immutability: once session reviews are approved the payload is frozen; reopen requires authorization and archives the previous version.

## 6. Fallback Hierarchy
1. Use structured data from Section 3 + planning context from Section 2.
2. If data missing, pull from toolkit cache or OSINT log.
3. Manual annotation via gateway queue for unresolved narratives.
4. Abort: flag `section_blocked` when essential narrative inputs absent.

## 7. Sectional Staging & Call-Out Procedures
- Runs after Section 3.
- Emits `session_review_ready` with narrative manifest and QA status to Section 7, FR.
- Receives `request_session_revision` from Section 7 or final assembly; reprocesses and updates payload.

## 8. Information Handlers
- **Narrative manifest:** per-subject/session summaries, evidence references, risk notes, QA flags.
- **Evidence persistence:** Narrative manifest and evidence links are persisted to durable storage after each update.
- **Evidence linkage:** mapping between narrative paragraphs and media/log entries.
- **Continuity log:** outcomes of North Star/Cochran checks, flagged issues.
- **Fact graph integration:** Publish aligned subject/timeline facts so conclusions and billing reference the same identities and times.
- **Manual queue:** outstanding narrative items requiring review/approval.

## 9. Narrative Blueprint
- Structured template: session headline, objective linkage, observations, evidence references, risk/next steps.
- Placeholders used only when manual review pending.
- Maintain `draft_review` and `approved_review` narratives with change log.

## 10. Dissemination & Intelligence Sharing
- Provide narratives to Sections 7, 6 (for impacts), 8 (media context), FR.
- Receive feedback (e.g., conclusion disagreements) via gateway and reconcile.
- Maintain version history for audit and final report assembly.

## 11. Documentation Alignment & Enforcement
- Reference docs:
  - README: `Sections/section_readme/Section_4_README.md`
  - Engines/renderers: `Sections/section_engines/`, `section_renderers/section_4_renderer.py`
  - Toolkit logic: `MasterToolKitEngine`, `cochran_match_tool.py`, `northstar_protocol_tool.py`
  - SOP: `dev_tracking/templates/Section_4_Rebuild_Playbook.md`, `CoreSystem/SOP.md`
- Enforcement: embed parsing rules in analysis stage; include doc version hash; add regression tests comparing narrative schema against documentation; update README/SOP when workflow changes.

## 12. Implementation To-Do (Section 4)
- [ ] Integrate gateway inputs with order lock checks.
- [ ] Build analysis pipeline linking surveillance entries to planning objectives and evidence with persistence write-through.
- [ ] Define `section_4_payload` schema (narrative manifest, evidence links, QA flags, provenance).
- [ ] Update renderer to consume structured payload, enforce narrative templates, track approvals.
- [ ] Add signals for `session_review_ready`, revision handling, conflict resolution.
- [ ] Extend tests: continuity enforcement, evidence linkage, manual queue behaviour, revision loop, ``max_reruns`` guardrails, narrative style lint.
- [ ] Refresh README/SOP with final architecture and note Section 1 order lock.
