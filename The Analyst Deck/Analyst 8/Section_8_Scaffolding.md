# Section 8 (Photo / Evidence Index) - Structured Rebuild Roadmap (Draft)

> **Order Lock:** Section 1/Gateway remains first. Section 8 depends on Sections 1-3 outputs and must respect that order.

## 1. Mission Statement
Index all media artifacts with quality, timestamp, and geolocation context tied to surveillance events, ready for audit and narrative use.

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
- **Ingress:** Gateway bundle with `case_metadata`, `planning_manifest` (Section 2), `surveillance_manifest` (Section 3), media processing results, voice transcripts, toolkit quality flags.
- **Egress:** `section_8_payload` containing media inventory, metadata summaries, OCR/voice transcripts, QA flags, provenance.
- **Scope:** Media metadata aggregation, quality thresholds, timeline alignment, transcription summary, relevance tagging.

## 3. Gateway Communication Contract
- `gateway.prepare_section('section_8')` – triggered after Section 3 emits `surveillance_ready` and media processing completes.
- `gateway.get_section_inputs('section_8')` – returns `{case_metadata, planning_manifest, surveillance_manifest, media_processing_results, voice_transcripts, toolkit_results}`.
- `gateway.publish_section_result('section_8', payload)` – stores evidence index, QA flags, provenance, stage confirmations.
- `gateway.subscribe('surveillance_revision', handler)` – rerun when Section 3 adjusts timelines.
- `gateway.emit('media_inventory_ready', manifest)` – notify Sections 4, 7, and FR when evidence index validated.

## 4. Stage Checklist & Checkpoints
| Stage | Description | Inputs | Checkpoint |
|-------|-------------|--------|------------|
| Intake | Pull inputs, verify Section 1/2/3 hashes, load media results. | gateway bundle | `s8_intake_logged` |
| Process | Validate media metadata, apply quality thresholds, run OCR/voice summary if missing. | media results, transcripts | `s8_processed` |
| Correlate | Align media with surveillance timeline and planning objectives; add cross-links. | surveillance manifest, planning | `s8_correlated` |
| Validate | Run QA (quality checks, timestamp alignment, subject relevance); log issues. | correlated data | `s8_validated` or `s8_requires_action` |
| Publish | Publish payload to gateway, emit media inventory signal. | validated payload | `section_8_completed` |
| Monitor | Handle revision requests (from Section 3/4/7/FR) while enforcing ``max_reruns`` and tracking ``revision_depth``. | signals | `s8_revision_processed` |

## 5. Guardrails & Failsafes
- Execution blocked until Sections 1-3 validated.
- Quality thresholds enforced (resolution, clarity); failing media flagged for manual review.
- Timestamp alignment must match surveillance logs; mismatches flagged.
- OCR/voice transcripts required for media containing text/audio; fallback to manual queue if automation fails.
- Manual edits logged with operator ID; provenance records transcription approvals.
- Immutability: once the media inventory is approved it is locked; reopen requires authorization and archives the prior version.

## 6. Fallback Hierarchy
1. MediaProcessingEngine outputs (metadata, OCR/voice results).
2. Manual review transcriptions via gateway queue for unresolved items.
3. Abort with `section_blocked` if critical evidence cannot be processed.

## 7. Sectional Staging & Call-Out Procedures
- Runs after Section 3.
- Emits `media_inventory_ready` with manifest and QA status.
- Receives `request_media_revision` from narrative sections or final assembly; reruns as required.

## 8. Information Handlers
- **Media inventory:** list of media items with metadata (timestamp, subject, location, quality, transcripts).
- **Persistence:** Inventory, transcripts, and quality flags are written to durable storage after each update.
- **Cross-links:** mapping between media and surveillance entries/planning objectives.
- **Fact graph integration:** Publish media-to-event nodes so downstream sections reference consistent identities and times.
- **Transcript registry:** extracted text/audio summaries with confidence and QA status.
- **Manual queue:** outstanding media requiring review.

## 9. Narrative Blueprint
- Provide structured entries (no narrative) with optional summary snippet per media item using hash-locked templates.
- Placeholders only when manual review pending.

## 10. Dissemination & Intelligence Sharing
- Share media inventory with Sections 4, 7, FR, and UI evidence dashboards.
- Receive feedback (e.g., mismatch flags) and reconcile updates.
- Maintain version history for audit.

## 11. Documentation Alignment & Enforcement
- Reference docs:
  - README: `Sections/section_readme/Section_8_README.md`
  - Engines/renderers: `Sections/section_engines/`, `section_renderers/section_8_renderer.py`
  - Toolkit logic: `MediaProcessingEngine`, `voice_transcription.py`, `smart_lookup`
  - SOP: `dev_tracking/templates/Section_8_Rebuild_Playbook.md`, `CoreSystem/SOP.md`
- Enforcement: integrate parsing rules; include doc version hash; tests verifying media schema vs documentation; update README/SOP on change.

## 12. Implementation To-Do (Section 8)
- [ ] Integrate gateway inputs with Section 1 order lock verification.
- [ ] Implement processing pipeline for media metadata, quality, OCR/voice fallback with persistence write-through.
- [ ] Define `section_8_payload` schema (media inventory, cross-links, transcripts, QA flags, provenance).
- [ ] Update renderer to output structured evidence index, ensuring compliance with templates.
- [ ] Add signals for `media_inventory_ready`, revision handling, conflict resolution.
- [ ] Extend tests: quality thresholds, timeline alignment, manual queue, revision loop, ``max_reruns`` guardrails.
- [ ] Refresh README/SOP with final architecture and note Section 1 order lock.
