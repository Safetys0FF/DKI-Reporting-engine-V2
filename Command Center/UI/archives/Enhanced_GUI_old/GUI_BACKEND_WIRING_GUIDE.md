# GUI ? Backend Wiring Guide

## Purpose
Provide a step-by-step integration blueprint that reconnects the Enhanced GUI with the Central Command backend. This covers the signal/interface contracts, required import-path updates, data payload schemas, and the validation plan needed to turn the current backend-only successes into an end-to-end workflow available through the user interface.

## System Layers & Responsibilities
1. **GUI Layer (`enhanced_functional_gui.py`)**
   - Collects user actions (evidence upload, process, section generation, report export).
   - Must package payloads for bus delivery and render responses in both read-only and editable panes.
2. **Central Plugin Adapter (`central_plugin.py`)**
   - Bootstraps Warden, Evidence Locker, Evidence Manager, Narrative Assembler, Mission Debrief, and the Bus.
   - Exposes helper methods (`store_file`, `generate_narrative`, `send_to_bus`) that the GUI consumes.
3. **Data Bus (`bus_core.py`)**
   - Signal registry and event router. Maintains case context and event log.
   - Key topics already registered by subsystems: `evidence.scan`, `evidence.classify`, `evidence.index`, `evidence.process_comprehensive`, `narrative.generate`, `mission_debrief.*`.
4. **Backend Subsystems**
   - Evidence Locker: ingest, classify, index evidence, produce structured records.
   - Warden/Gateway & Marshall: orchestrate processing, manage dependencies.
   - Narrative Assembler: compile section narratives from structured data payloads.
   - Mission Debrief Manager: apply professional tooling and exports.

## Current Gaps Confirmed by Tests
- GUI sends raw `store_file` calls but does not construct section-aware payloads (`scanning_parsing_results_20250925.json` shows 100% backend readiness, yet zero narrative data reaches the GUI).
- No GUI registration for bus responses; panes remain empty (`NETWORK_COMPREHENSIVE_DISCOVERY_REPORT_20250925.md`).
- Import path mismatches block gateway discovery (`main_bus_connectivity_test_1_20250925.json`).
- Integration tests stall at bridge layer causing artificial 999000?ms timings (`scanning_performance_live_20250925.json`, `performance_test_results_20250925.json`).

## Integration Tasks

### 1. Import & Path Alignment
- Update GUI launcher/adapter to reference NEW architecture directories:
  - Evidence Locker: `F:\The Central Command\Evidence Locker`
  - Warden (ECC/Gateway): `F:\The Central Command\The Warden`
  - Marshall Evidence Manager: `F:\The Central Command\The Marshall`
  - Data Bus: `F:\The Central Command\Command Center\Data Bus\Bus Core Design`
  - Mission Debrief: `F:\The Central Command\Command Center\Mission Debrief`
- Fix hard-coded relative lookups (e.g. `./Gateway/gateway_controller.py`) uncovered in `main_bus_connectivity_test_1_20250925.json`.
- Ensure `sys.path` adjustments in `central_plugin.py` and launcher scripts mirror above.

### 2. GUI Structured Payload Builder
- Extend `EnhancedDKIGUI.process_evidence` to accumulate structured summaries instead of storing raw locker responses.
  - For each processed evidence record, capture: `file_path`, `file_type`, `file_size`, user classification, tags, timestamps.
  - Group by `section_id` to feed section-specific data.
- Suggested helper signature: `build_structured_section_data(processed_payload) -> Dict[str, Dict[str, Any]]`.
- Include case metadata (case number, client name, start/sign date) from GUI state.

### 3. Narrative Request Wiring
- After processing evidence, combine structured data with case context:
  ```python
  payload = {
      "case_id": self.current_case_id,
      "processed_data": processed_payload,
      "structured_sections": structured_data,
      "summary": summary_lines
  }
  response = self.central_plugin.send_to_bus("narrative.generate", payload)
  ```
- Capture `response['full_narrative']` per section and render into the read-only pane while copying to the editable pane when first generated.
- Track dirty state to warn users if edits diverge from regenerated content.

### 4. Data Bus Signal Handlers (GUI Side)
- Subscribe to callbacks for relevant topics so GUI can display async notifications:
  - `narrative.assembled` ? section generation confirmation.
  - `evidence_locker.evidence_handoff` ? update audit trail/status bar.
  - `mission_debrief.processed` (if emitted) ? show professional tooling success.
- Implement lightweight handler registry in GUI (e.g., using `central_plugin.bus.register_signal(...)` if accessible or by extending `central_plugin` with callback registration wrappers).

### 5. Response Propagation & Logging
- Standardize status updates:
  - Success: update status bar, append to `audit_listbox`, refresh section pane.
  - Error: show message box with payload details, log to `enhanced_gui.log`.
- Ensure response metadata (queued dependencies, warnings) are surfaced to the user.

### 6. Mission Debrief Invocation
- On "Apply Professional Tools", include both generated narrative and user edits. Recommended payload additions:
  - `structured_sections` (for context)
  - `user_edits` (diff or full text)
  - `delivery_options` (e.g., `"apply_template": true`)
- Handle responses from `mission_debrief.process_report` to present export paths or warnings in the GUI.

### 7. Launcher & Runtime Adjustments
- Update `DKI_ENGINE_LAUNCHER.bat` and any helper scripts to CD into correct directories and to surface logging when Python exits early.
- Verify `.venv` path resolution to avoid reliance on global interpreters.

## Validation Plan
1. **Smoke Workflow**
   - Launch GUI via `DKI_ENGINE_LAUNCHER.bat`.
   - Create case ? add evidence (use files from `Evidence Locker/Test Plans`).
   - Run “Process Evidence” and ensure structured summary appears in read-only pane with editable copy populated.
   - Generate single section (`section_1`), verify narrative text matches structured data.
2. **Full Report Cycle**
   - Generate all sections.
   - Apply professional tools; confirm Mission Debrief response updates report pane and audit log.
   - Export report and confirm file creation.
3. **Regression Suites**
   - Rerun stress/performance JSON tests that previously stalled (`scanning_performance_live`, `performance_test_results`) to verify sub-100?ms locker responses.
   - Execute `main_bus_connectivity_test_1_20250925.json` to ensure gateway path resolves.
   - Re-run advanced parsing tests after enabling OCR/media support to push format coverage toward 100?%.
4. **Analyst Deck Confirmation**
   - Trigger functionality tests focusing on Analyst Deck tasks; ensure `module_status` upgrades from PARTIAL.
5. **Logging Review**
   - Inspect `enhanced_gui.log`, `dki_bus_core.log`, and subsystem logs for errors during integration tests.

## Implementation Checklist
- [ ] Align GUI import paths to new architecture directories.
- [ ] Implement structured payload builder and integrate into `process_evidence`.
- [ ] Wire bus requests/responses for narrative generation and professional tooling.
- [ ] Add GUI handlers for bus callbacks to update UI components.
- [ ] Update launcher scripts and diagnostics for new paths.
- [ ] Enable/validate OCR and media processors if available.
- [ ] Re-run stress/performance suites and capture new metrics.
- [ ] Document final metrics and close open issues (Analyst Deck partial status).

## Reference Artifacts
- `F:\The Central Command\Command Center\UI\enhanced_functional_gui.py`
- `F:\The Central Command\Command Center\UI\central_plugin.py`
- `F:\The Central Command\Command Center\Data Bus\Bus Core Design\bus_core.py`
- `F:\The Central Command\Command Center\Mission Debrief\The Librarian\narrative_assembler.py`
- `F:\The Central Command\Command Center\Mission Debrief\Debrief\README\mission_debrief_manager.py`
- Stress test outputs in `F:\The Central Command\Ops Center\Stress Tests\`

---
This guide can be expanded with code snippets as integration progresses; use the checklist to track completion and update the stress-test archive with post-fix metrics.
