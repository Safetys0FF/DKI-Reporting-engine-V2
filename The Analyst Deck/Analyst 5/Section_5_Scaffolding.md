# Section 5 (Supporting Documents & Records) - Structured Rebuild Roadmap (Draft)

> **Order Lock:** Section 1/Gateway executes first. Section 5 depends on Sections 1 and 2 (and relevant evidence ingestion) and must respect that order.

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
 
## 1. Mission Statement
Catalogue and validate supplemental records so every evidentiary document aligns with investigative objectives and legal requirements.

## 2. System Context
- **Ingress:** Gateway bundle with `case_metadata`, `document_index` (from DocumentProcessor), toolkit relevance scores, repository metadata, Section 2 planning manifest.
- **Egress:** `section_5_payload` containing document inventory, metadata summaries, relevance notes, QA flags, chain-of-custody info.
- **Scope:** Document classification, metadata extraction, relevance validation, compliance tagging, inventory publication.

## 3. Gateway Communication Contract
- `gateway.prepare_section('section_5')` – triggered after Section 1/2 validation and document ingestion.
- `gateway.get_section_inputs('section_5')` – returns `{case_metadata, document_index, toolkit_results, repository_metadata, planning_manifest}`.
- `gateway.publish_section_result('section_5', payload)` – stores inventory output, QA flags, provenance, stage confirmations.
- `gateway.subscribe('document_reclassification', handler)` – rerun when evidence index updates.
- `gateway.emit('document_inventory_ready', manifest)` – notify Sections 7 and FR when records validated.

## 4. Stage Checklist & Checkpoints
| Stage | Description | Inputs | Checkpoint |
|-------|-------------|--------|------------|
| Intake | Pull document index, verify Section 1/2 hashes, load toolkit relevance results. | gateway bundle | `s5_intake_logged` |
| Extract | Ensure metadata (jurisdiction, parties, dates) available; run OCR fallback if missing. | document index | `s5_metadata_complete` |
| Validate | Apply relevance checks (Cochran, planning scope), classify documents, log risk flags. | metadata, toolkit | `s5_validated` or `s5_requires_action` |
| Publish | Publish inventory payload to gateway, emit inventory signal. | validated payload | `section_5_completed` |
| Monitor | Handle reclassification or new documents while enforcing ``max_reruns`` and logging ``revision_depth``. | signals | `s5_revision_processed` |

## 5. Guardrails & Failsafes
- Execution blocked until Section 1 validated; subject manifest required.
- Strict schema for document entries (id, title, type, jurisdiction, parties, relevance, custody, references).
- Fallback to OCR if metadata missing; if still absent, relevant entry flagged for manual review.
- Chain-of-custody entries mandatory for high-priority documents.
- Change control: manual edits logged with operator ID; approvals recorded in payload provenance.
- Immutability: once the inventory is approved it is locked; reopening requires authorization and archives the prior version.

## 6. Fallback Hierarchy
1. DocumentProcessor metadata + toolkit normalization.
2. OCR (Unstructured/Tesseract) or OSINT to fill missing fields; log fallback attempts.
3. Manual completion via gateway queue for unresolved metadata.
4. Abort: mark `section_blocked` if essential legal metadata absent.

## 7. Sectional Staging & Call-Out Procedures
- Runs after Section 1 and 2 (and once document ingestion complete).
- Emits `document_inventory_ready` to Sections 7, FR, and compliance tools.
- Responds to `request_document_revision` from downstream sections (e.g., Section 7, FR).

## 8. Information Handlers
- **Document inventory:** list of documents with metadata, relevance, evidence IDs, risk flags, custody notes.
- **Persistence:** Inventory and custody logs are written to durable storage after each update.
- **Custody log:** tracking of document source, storage, and approval state.
- **Relevance annotations:** output from toolkit checks linking documents to subjects/objectives.
- **Fact graph integration:** Publish document-to-subject relationships so downstream sections reference consistent entities.
- **Manual queue:** outstanding documents requiring review/completion.

## 9. Narrative Blueprint
- Provide structured registries (no narrative) with optional summary bullet per document using hash-locked templates.
- Placeholder tags only when manual review pending; flagged for QA.

## 10. Dissemination & Intelligence Sharing
- Share inventory with Sections 7 (conclusion), FR (final assembly), compliance dashboards.
- Receive discrepancy reports (e.g., planning scope mismatch) and reconcile.
- Maintain version history for audit and export.

## 11. Documentation Alignment & Enforcement
- Reference docs:
  - README: `Sections/section_readme/Section_5_README.md`
  - Engines/renderers: `Sections/section_engines/`, `section_renderers/section_5_renderer.py`
  - Toolkit logic: `metadata_tool_v_5.py`, `cochran_match_tool.py`, `repository_manager`
  - SOP: `dev_tracking/templates/Section_5_Rebuild_Playbook.md`, `CoreSystem/SOP.md`
- Enforcement: embed parsing rules in metadata extraction stage; include doc version hash; tests verifying inventory schema vs documentation; update README/SOP on change.

## 12. Implementation To-Do (Section 5)
- [ ] Integrate gateway inputs with Section 1 order lock verification.
- [ ] Implement metadata extraction/validation pipeline with fallbacks, manual queue, and persistence write-through.
- [ ] Define `section_5_payload` schema (inventory, relevance annotations, custody log, QA flags, provenance).
- [ ] Update renderer to output structured inventory and compliance notes.
- [ ] Add signals for `document_inventory_ready`, revision handling, and conflict resolution.
- [ ] Extend tests: metadata fallback, relevance checks, manual queue, revision loop, ``max_reruns`` guardrails.
- [ ] Refresh README/SOP with final architecture and note Section 1 order lock.
