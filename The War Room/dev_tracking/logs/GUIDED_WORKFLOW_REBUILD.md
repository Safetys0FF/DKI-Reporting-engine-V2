# Central Command Guided Workflow Rebuild

## Purpose
Blueprint and implementation checklist for transforming the Central Command workstation into a guided, semi-autonomous workflow that carries investigators from login through final report export while keeping backend services synchronized.

---

## Lifecycle Overview
1. **Operator Login & Profile Guardrails**
   - Authenticate operator, load profile, surface missing essentials (signature image, licensing, preferred disclosure set).
   - Cache branding assets for use in cover/disclosure pages.

2. **Case Creation Wizard**
   - Modal triggered by "Start New Case" capturing minimal fields:
     - `Case Number` → canonical `case_id`.
     - `Investigator Assigned` → seeded to Section 1 metadata.
     - `Subcontractor?` (Y/N) → Section 1 metadata.
     - `Contract Signed Date` → case metadata & downstream reminders.
   - Register case on bus, store metadata in Mission Debrief, create export repo `<export_root>/<case_id>/`.

3. **Evidence Intake**
   - Drag-and-drop zone with fallback file picker.
   - Each file becomes an evidence card with auto-classification, section suggestion, editable tags/notes, preview modal.
   - Section assignment emits `section.needs` so later stages reference the doc; cards maintain shared ordering state.
   - Checklist of required evidence updates dynamically; "Process Evidence" unlocks once thresholds met (or investigator overrides).

4. **Evidence Processing Trigger**
   - Button click fires background jobs: narrative assembly, PDF/text extraction, metadata sync.
   - UI auto-advances to section review pane; per-section status indicators show assembling → ready → awaiting approval.

5. **Section Review & Approval Loop**
   - Fixed review sequence: 1 → 2 → 3 → 4 → 5 → 8 → 7 → 6 → 9.
   - Only active section editable; others locked to prevent context switching.
   - Evidence/tag changes trigger reassembly; UI surfaces "refresh available" prompts and marks previously approved sections as "needs review".
   - Investigator approves each section; approved text sent via `section.data.updated` and state advanced automatically.
   - Section re-sequencing (if investigator adjusts order) updates `section_sequence`, reruns narratives, and requeues impacted sections for approval while preserving controlled step flow.

6. **Save & Pause Support**
   - "Save & Exit" captures full session (evidence assignments, section states, approvals) and catalogs case as `in_progress`.
   - Case hub lists In Progress vs Completed; resuming restores progression context.

7. **Export Manager**
   - After final approval, confirmation modal leads to export screen.
   - Screen shows case summary, disclosures checklist (seeded from profile), live previews of cover page, TOC, disclosure page.
   - Updates to disclosures or report titles regenerate artifacts instantly (background tasks).

8. **Report Export & Cataloging**
   - Export options default to profile preferences (PDF/DOCX/Text); target folder auto-resolves to `<export_root>/<case_id>/`.
   - Mission Debrief writes final payloads; results logged to case catalog with artifact paths and timestamps.
   - Post-export: evidence locker and session caches cleared; UI returns home with confirmation toast.

9. **Case Recall**
   - Completed cases visible in Case Hub; selecting one reloads narratives/evidence in read-only mode.
   - "Reopen" duplicates/unlocks case and requires re-approval for sections touched thereafter.

---

## Implementation Map (Repo Locations)
| Concern | Primary Files/Modules |
| --- | --- |
| GUI shell & screens | `Command Center/UI/enhanced_functional_gui.py`, supporting widgets under `Command Center/UI/Test Plans/gui support files/` |
| Central plugin facade | `Command Center/UI/Enhanced GUI/central_plugin.py` (and mirrored adapters) |
| Bus interactions | `Command Center/Data Bus/Bus Core Design/bus_core.py` |
| Evidence pipeline | `Command Center/Mission Debrief/tools/` adapters + `Evidence Locker` modules |
| Mission orchestration | `Command Center/Mission Debrief/Debrief/README/mission_debrief_manager.py` |
| Narrative assembly | `Command Center/Mission Debrief/The Librarian/narrative_assembler.py` |
| Report generation | `Command Center/Mission Debrief/report generator/` |
| Case catalog service (new) | `The War Room/dev_tracking/` (persistent catalog & helpers) |

---

## Stage-by-Stage Build Plan

### Phase 1 – Scaffold & State Management
1. Create case session model (UI layer) capturing case metadata, evidence cards, section states, export prefs.
2. Implement case catalog persistence module (`case_catalog.py`) storing `in_progress` and `completed` states (JSON/SQLite under `The War Room/dev_tracking/`).
3. Extend central plugin to:
   - Expose case start API (create repo folder, emit case metadata).
   - Maintain evidence registry synced with Mission Debrief.
   - Listen to bus signals (`section.data.updated`, `narrative.assembled`, `gateway.section.complete`, etc.) and update session state.

### Phase 2 – UI Flow
4. Login/profile review dialog (profile validation + branding cache) in `enhanced_functional_gui.py`.
5. Case hub redesign: tabs for In Progress / Completed / New Case; integrate "Start New Case" wizard.
6. Evidence intake screen with drag-and-drop, card components, preview modal, and requirements checklist.
7. Wire evidence card actions to central plugin methods (classification, retagging, reordering).
8. Add "Process Evidence" trigger to send aggregator job and transition to section review.

### Phase 3 – Section Review Engine
9. Section review view controller enforcing fixed sequence and approval state machine.
10. UI bindings for assembler progress, refresh prompts, approval locking, and automatic next-step advance.
11. Support section resequencing UI (drag handle or sequence dialog) that updates `section_sequence` and requeues sections.
12. Implement "Save & Exit" (snapshot session state, catalog as `in_progress`, return home).

### Phase 4 – Export Manager & Finalization
13. Export manager screen: case summary, disclosures toggles, live previews (cover/TOC/disclosure).
14. Hook disclosure toggles & titles into Mission Debrief/report generator to regenerate artifacts on change.
15. Export workflow (multi-format) writing to `<export_root>/<case_id>/`; record artifact paths in catalog.
16. Post-export cleanup: evidence locker purge, session reset, auto-return to home hub.
17. Case recall path (read-only view, re-open workflow).

### Phase 5 – Polish & Resilience
18. Background job status indicator & retry controls.
19. Error-handling banner framework (service offline, export failure, etc.).
20. Audit trail/log view for investigators (summary of auto-actions).
21. Multi-user safeguards (case locking) if required.
22. Documentation & onboarding guides.

---

## To-Do Checklist (Granular)
- [ ] Draft case session data model and persistence interfaces.
- [ ] Implement case catalog storage in `The War Room/dev_tracking/`.
- [ ] Update central plugin path bootstrap to include mission/report directories (already in progress).
- [ ] Add case creation wizard (UI + plugin integration).
- [ ] Build evidence card component with drag & preview.
- [ ] Connect evidence actions to bus + Mission Debrief updates (`section.needs`).
- [ ] Create workflow state machine controller (evidence → sections → export).
- [ ] Implement section review UI with approval locks and reassembly hooks.
- [ ] Add resequencing controls triggering narrative reruns.
- [ ] Build save/pause mechanism and resume flow.
- [ ] Implement export manager screen, disclosures configuration, preview generation.
- [ ] Wire report export pipeline (PDF/DOCX/Text) to new export manager.
- [ ] Catalog completed cases; implement recall + read-only view.
- [ ] Post-export cleanup routine (evidence locker, session reset).
- [ ] Add error/notification framework and background job dashboard.
- [ ] QA checklist: stage transitions, reassembly triggers, catalog integrity, export paths.

---

## Signal & Data Considerations
- Subscribe to: `section.data.updated`, `narrative.assembled`, `mission_debrief.section.complete`, `gateway.section.complete`, `section.sequence.updated` (new), `report.exported` (optional).
- Emit on: case creation, evidence updates (`evidence.scan`, `section.needs`), section approvals (`section.data.updated`), export requests, catalog events.
- Maintain mapping between evidence cards and bus payloads to keep locker, mission, and UI aligned.

---

## Catalog & Persistence Strategy
- **Format**: JSON or SQLite under `The War Room/dev_tracking/case_catalog` (include schema versioning).
- **Fields**: `case_id`, status, timestamps, investigator, subcontractor flag, contract date, export root, artifact list, section approval states, evidence summary.
- **Backups**: Optionally mirror catalog to export root for disaster recovery.
- **Cleanup**: On case completion, purge temp evidence from locker, archive raw files into export folder if needed.

---

## Validation & QA Plan
1. Unit tests around session state transitions and catalog persistence.
2. Integration tests simulating evidence intake → section approvals → export.
3. Manual exploratory runs focusing on:
   - Evidence reorder/retag flow and reassembly.
   - Resequencing sections mid-review.
   - Save & resume accuracy.
   - Export toggles and branding assets.
   - Catalog recall and read-only view fidelity.
4. Regression watchlist: ensure legacy bus consumers handle the new signals gracefully.

---

## Open Questions / Decisions Needed
- Will multiple investigators run concurrently? If yes, design case locking or shared catalog sync.
- Should evidence files be copied into export folders or referenced in place? (Impacts cleanup chores.)
- Do we need automated notifications (email/SMS) on case completion?
- Preferred storage engine for catalog (simple JSON vs SQLite) given deployment constraints.

---

## Next Steps
1. Confirm catalog format and persistence strategy.
2. Green-light UI flow wireframes (login, case hub, evidence intake, section review, export manager).
3. Begin Phase 1 implementation using above To-Do list, committing incremental slices (session model, catalog, plugin updates).
4. Schedule regular demos to validate each stage before moving to the next.

---

*Document owner: [Update with primary developer]*
*Last updated: $(Get-Date -Format 'yyyy-MM-dd')*

---

## Codex Progress Log (2025-10-04)

### Work Completed
- **Path Realignment (2025-10-04 morning)** – Updated central_plugin.py import bootstrap to resolve modules inside F:\The Central Command so the adapter no longer searches legacy DKI-Report-Engine paths. Result: Warden/Evidence subsystems initialize without manual PYTHONPATH tweaks.
- **Session Lifecycle Hardening (2025-10-04 afternoon)** – Extended case_session.py with canonical SECTION_TITLES, enriched SectionState with 	itle, and ensured CaseSession.ensure_section/rom_dict hydrate that metadata. GUI review tables now display human-readable titles, while the catalog continues to persist full state.
- **Pause/Resume & Adapter Helpers (2025-10-04 afternoon)** – Added module-level wrappers (pause_case, esume_case, save_case) in central_plugin.py so existing scripts can import workflow controls directly. GUI pause/resume buttons call into the adapter, guaranteeing catalog_save_session runs on every transition.
- **Case Creation Safeguards (2025-10-04 evening)** – Introduced sanitize_case_id in enhanced_functional_gui.py, wired to CaseCreationDialog and _prompt_new_case. Duplicate IDs are rejected via self.plugin.list_cases(), and contract dates are validated with date.fromisoformat, preventing malformed entries from reaching the catalog.
- **UI Feedback Improvements** – _set_review_readiness and _prepare_review_rows now rely on session titles and state to present status consistently after section approvals.

### System Impact
- **Reliability** – Catalog writes are now protected from invalid IDs or duplicate sessions, reducing the risk of clobbering existing case folders.
- **Traceability** – Section titles flow from a single source of truth, aligning review UI, session persistence, and mission tooling.
- **Compatibility** – Legacy scripts regain the ability to import pause_case/esume_case, easing migration away from the retired engine.

### Milestone Comparison vs. Guided Workflow Plan
- **Phase 1 (Scaffold & State Management)** – Case session model now tracks section titles and respects catalog hygiene, moving this milestone toward completion.
- **Phase 2 (UI Flow)** – Case creation wizard now enforces guardrails specified in the plan (canonical case_id, investigator, subcontractor flag, contract date validation). Section review pane reflects the controlled sequence with accurate titles.
- **Phase 3 (Workflow Automations)** – Pause/resume persistence and duplicate protection lay groundwork for Save & Pause support and the Case Hub’s integrity goals noted in the README.

### Recommended Next Steps
1. **Catalog Testing** – Run integration tests that create, pause, resume, and reopen cases to confirm sanitized IDs survive the full lifecycle and metadata renders correctly in the Case Hub.
2. **Section Title Adoption** – Propagate SectionState.title into export payloads (Mission Debrief / report generator) so document headers match the GUI.
3. **Concurrent Access Strategy** – Revisit the README’s open question on multi-investigator locking; now that IDs are deterministic, design a locking or merge strategy.
4. **Automated QA** – Add unit tests for sanitize_case_id, duplicate detection, and contract date parsing to prevent regressions.


---

## Codex Progress Log (2025-10-04, evening)

### Work Completed
- **Operator Scaffold (GUI)** – Introduced dormant operator-management wiring in enhanced_functional_gui.py. The Profile Editor now includes an Operator Management panel with password-protected enable/disable controls, writing to profile_manager/profile_access_rules.json. A new scaffold initializer logs status, updates the home dashboard, and exposes an "Operators" menu entry with a "coming soon" preview.
- **Case Creation Guardrails** – Replaced the raw popup with CaseCreationDialog that sanitizes case_id, blocks duplicates via plugin.list_cases(), and validates contract dates before passing data to start_case.
- **Evidence lifecycle cleanup** – Register/remove evidence cards through the plugin so GUI card state stays synchronized and counts refresh immediately.
- **Report generation/refresh tweaks** – generate_full_report now always requests data for the active case, preventing cross-case content leakage.
- **Profile Manager package setup** – Added profile_manager/__init__.py and modernized operator_manager.py paths so the scaffold works from within the Central Command tree without legacy references.

### System Impact
- The GUI now surfaces the future operator-management capability without enabling it. Flags remain disabled, but the wiring is in place for a controlled activation.
- Case creation is safer: IDs are canonical, duplicates rejected, and malformed dates no longer reach the catalog.
- Evidence and report flows stay in sync with plugin state, reducing drift between the GUI and the underlying case session.

### Alignment With Guided Workflow Plan
- Progress on **Phase 1**: Session state scaffolding now includes operator metadata hooks and safer persistence.
- Progress on **Phase 2**: Case creation wizard enforces the blueprint’s guardrails and preps for multi-operator support noted in the README.
- Sets the stage for **Phase 3**: Operator scaffolding and audit stubs satisfy prerequisites for multi-investigator workflows.

### Next Steps
1. Define the final admin-secret handling (e.g., secure env var) before enabling the controls in production.
2. When ready, route evidence locker operations through OperatorManager.is_allowed and append audit events via log_case_event.
3. Expand the Profile Manager interface with operator CRUD tools for onboarding field operators.
4. Add automated tests for sanitize_case_id, duplicate detection, and operator toggle behaviours.

