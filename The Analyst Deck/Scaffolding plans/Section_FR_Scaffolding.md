# Section FR (Final Assembly) - Structured Rebuild Roadmap (Draft)

> **Order Lock:** Section 1/Gateway first. Section FR runs last, consuming all validated section outputs.

## 1. Mission Statement
Compile approved sections into the final export package while enforcing order, completeness, and provenance tracking.

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
- **Ingress:** Gateway bundle with outputs from Sections CP, 1, 2, 3, 4, 5, 6, 7, 8, 9, DP; approval states; case snapshot; configuration.
- **Egress:** Final assembly manifest, export-ready bundle (e.g., DOCX/PDF structure), QA flags, provenance, audit logs.
- **Scope:** Section ordering, completeness verification, final adjustments, export generation, audit record creation.

## 3. Gateway Communication Contract
- `gateway.prepare_section('section_fr')` – triggered when all required sections marked complete/approved.
- `gateway.get_section_inputs('section_fr')` – returns `{section_outputs, approval_states, case_snapshot, export_config}`.
- `gateway.publish_section_result('section_fr', payload)` – stores final manifest, QA flags, export metadata.
- `gateway.subscribe('section_revision', handler)` – listens for upstream reopens to regenerate final package.
- `gateway.emit('final_package_ready', manifest)` – notify UI and export pipeline when ready.

## 4. Stage Checklist & Checkpoints
| Stage | Description | Inputs | Checkpoint |
|-------|-------------|--------|------------|
| Intake | Validate all sections present + approved, load export config. | section outputs | `fr_intake_logged` |
| Verify | Check section order, completeness, hash outputs for integrity. | section outputs | `fr_verified` |
| Assemble | Run ReportGenerator to build final structure (DOCX/PDF). | verified outputs | `fr_assembled` |
| QA | Confirm attachments, numbering, table of contents, disclaimers; log issues. | assembled data | `fr_qc_passed` or `fr_requires_action` |
| Publish | Publish final manifest to gateway, emit readiness signal. | validated package | `section_fr_completed` |
| Monitor | Listen for upstream revisions; regenerate as needed while enforcing ``max_reruns`` and tracking ``revision_depth``. | signals | `fr_revision_processed` |

## 5. Guardrails & Failsafes
- Execution blocked until all required sections completed/approved.
- Hash each section payload to detect unexpected changes; mismatches block final assembly.
- Archive exact versions of section payloads used for export.
- Immutability: signed-off section payloads remain read-only; reopening requires authorization and new export cycle, preserving the archived version.
- Manual overrides logged with operator ID, justification, and dual approval.
- Maintain audit log for every regeneration.

## 6. Fallback Hierarchy
1. Use approved section outputs.
2. If a section missing, trigger rerun (`section_blocked`), wait until resolved.
3. Manual placeholder insertion only with documented justification; flagged in manifest.

## 7. Sectional Staging & Call-Out Procedures
- Runs last; triggers export pipeline.
- Emits `final_package_ready` with manifest, export hash, QA status.
- Subscribes to `request_final_revision` from stakeholders; regenerates after upstream updates.

## 8. Information Handlers
- **Final manifest:** section order, hashes, approvals, export metadata, QA flags.
- **Persistence:** Final manifest and export bundles are written to durable storage with versioned hashes.
- **Audit log:** record of generations, revisions, and operator actions.
- **Export bundle:** pointers to generated files and delivery status.

## 9. Narrative Blueprint
- No narrative creation; ensures inclusion of automated cover pages, TOC, disclaimers per configuration.

## 10. Dissemination & Intelligence Sharing
- Provide manifest/export to UI, delivery mechanisms, archives.
- Publish final fact graph snapshot for downstream analytics.
- Receive feedback (e.g., distribution failures) and flag for rerun.
- Maintain versioned archive for compliance.
## 11. Documentation Alignment & Enforcement
- Reference docs:
  - README/SOP: `Sections/section_readme/Section_FR_README.md`, `dev_tracking/templates/Section_FR_Rebuild_Playbook.md`, `CoreSystem/SOP.md`
  - Assembly logic: `ReportGenerator`, export configuration scripts
- Enforcement: document assembly rules; include doc version hash; tests verifying final manifest structure vs documentation; update README/SOP on change.

## 12. Implementation To-Do (Section FR)
- [ ] Integrate gateway inputs verifying Section 1 order lock and section approvals.
- [ ] Implement verification pipeline (order, completeness, hash checks) with persistence write-through.
- [ ] Define `section_fr_payload` schema (final manifest, QA flags, export metadata, audit log).
- [ ] Update assembly routine to consume structured section payloads, enforce templates, and log anomalies.
- [ ] Add signals for `final_package_ready`, revision handling, distribution tracking.
- [ ] Extend tests: completeness checks, hash verification, regeneration path, manual override logging, ``max_reruns`` guardrails.
- [ ] Refresh README/SOP with final architecture and note Section 1 order lock.
