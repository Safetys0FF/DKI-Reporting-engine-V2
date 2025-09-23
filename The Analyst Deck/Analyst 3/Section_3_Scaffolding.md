# Section 3 (Surveillance Reports / Daily Logs) - Structured Rebuild Roadmap (Draft)

> **Order Lock:** Section 1/Gateway remains first. Section 3 depends on Sections 1 & 2 completion and must respect their order.

## 1. Mission Statement
Capture ground truth from field operations with time-aligned logs, GPS metadata, media references, and voice transcripts ready for audit.

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
- **Ingress:** Gateway bundle with `case_metadata`, `subject_manifest`, `planning_manifest` (Section 2), media/evidence index, toolkit cache, voice transcripts.
- **Egress:** `section_3_payload` containing structured daily logs, media references, GPS tracks, QA flags, narrative summaries, provenance.
- **Scope:** Surveillance log ingestion, metadata correlation, narrative synthesis, QA cross-checks with planning directives.

## 3. Gateway Communication Contract
- `gateway.prepare_section('section_3')` – triggered after Section 2 emits `planning_ready`.
- `gateway.get_section_inputs('section_3')` – returns `{case_metadata, subject_manifest, planning_manifest, media_index, voice_transcripts, toolkit_results}`.
- `gateway.publish_section_result('section_3', payload)` – stores structured output, QA flags, provenance, stage confirmations.
- `gateway.subscribe('planning_revision', handler)` – rerun when Section 2 updates routines/timelines.
- `gateway.emit('surveillance_ready', manifest)` – notify Sections 4, 6, 7, 8 when logs validated.

## 4. Stage Checklist & Checkpoints
| Stage | Description | Inputs | Checkpoint |
|-------|-------------|--------|------------|
| Intake | Pull inputs, verify Section 1/2 hashes, load media references. | gateway bundle | `s3_intake_logged` |
| Extract | Process field logs (OCR), ingest GPS/EXIF, transcribe audio (Whisper). | evidence index | `s3_extraction_complete` |
| Correlate | Align observations with planning timelines and media assets; build structured log entries. | planning manifest, media index | `s3_correlated` |
| Validate | Run QA (continuity checks, subject alignment, timestamp integrity, Cochran compliance). | correlated data | `s3_validated` or `s3_requires_action` |
| Publish | Publish payload to gateway, emit surveillance signal. | validated payload | `section_3_completed` |
| Monitor | Handle revision requests (from planning or evidence updates) while enforcing ``max_reruns`` and logging ``revision_depth``. | signals | `s3_revision_processed` |

## 5. Guardrails & Failsafes
- Execution blocked until Sections 1 and 2 validated.
- Strict schema for log entries (timestamp, subject, location, activity) enforced; missing critical fields routed to manual queue.
- Fallback policy for OCR/voice: if transcripts fail after fallback, mark entry with `requires_manual_review` and log in queue.
- Media correlation must succeed (image/video references cross-checked against planning timeline) or flagged.
- Change control: manual edits to logs recorded with operator ID and timestamp; narrative approvals tracked.
- Immutability: once Section 3 logs are approved the payload is frozen; reopening requires authorization and archives the prior version.

## 6. Fallback Hierarchy
1. OCR: Tesseract/Unstructured primary, then EasyOCR/PaddleOCR for poor scans.
2. Audio: Whisper primary; manual transcription if failure.
3. GPS metadata: EXIF primary; manual entry if missing.
4. Abort: if critical evidence missing, log `section_blocked` and halt.

## 7. Sectional Staging & Call-Out Procedures
- Runs after Section 2.
- Emits `surveillance_ready` with digest of validations, risk flags, media manifest.
- Subscribes to `request_surveillance_revision` from downstream sections (4,6,7,8).

## 8. Information Handlers
- **Log manifest:** list of entries with timestamps, subjects, activities, location, media refs, voice memo link, QA status.
- **Media cross-links:** mapping between log entries and media evidence IDs.
- **Evidence persistence:** Log manifest and media links are mirrored to durable storage after each update so restarts preserve routing.
- **Voice memo registry:** transcripts, confidence scores, QA status.
- **Fact graph integration:** Publish aligned subject/timeline nodes so downstream sections consume consistent identities and timestamps.
- **Manual queue:** outstanding log entries requiring review.

## 9. Narrative Blueprint
- Generate structured narrative from log manifest (facts-only, time-ordered).
- Template uses `subject`, `location`, `action` fields; placeholders only when manual review flagged.
- Store `draft_log_narrative` and `approved_log_narrative` with diff.

## 10. Dissemination & Intelligence Sharing
- Provide log manifest to Sections 4,6,7,8 and UI timeline view.
- Receive conflict reports (e.g., Section 4 narrative mismatch) via gateway and reconcile.
- Maintain version history for audit and final assembly.

## 11. Documentation Alignment & Enforcement
- Reference docs:
  - README: `Sections/section_readme/Section_3_README.md`
  - Engines/renderers: `Sections/section_engines/`, `section_renderers/section_3_renderer.py`
  - Toolkit logic: `mileage_tool_v_2.py`, `northstar_protocol_tool.py`, `cochran_match_tool.py`, `voice_transcription.py`
  - SOP: `dev_tracking/templates/Section_3_Rebuild_Playbook.md`, `CoreSystem/SOP.md`
- Enforcement: apply parsing maps in correlation stage, embed doc version hash in payload, add regression tests verifying log schema vs documentation, update README/SOP on any change.

## 12. Implementation To-Do (Section 3)
- [ ] Implement ingestion pipeline (OCR, metadata, voice) with strongest-first ordering, fallback logging, and persistence write-through.
- [ ] Build correlation engine aligning logs with planning data and media evidence.
- [ ] Define `section_3_payload` schema (log manifest, media cross-links, QA flags, narratives, provenance).
- [ ] Update renderer to consume structured payload, enforce templates, and track approvals.
- [ ] Add signals for `surveillance_ready` and revision handling.
- [ ] Extend tests: extraction delegations, media correlation, manual queue behaviour, revision loop, ``max_reruns`` guardrails, persistence reload, narrative style lint.
- [ ] Refresh README/SOP capturing order lock and new workflow.
