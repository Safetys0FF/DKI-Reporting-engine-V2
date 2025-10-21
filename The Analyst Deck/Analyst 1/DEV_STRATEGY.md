# Section 1 – Development Strategy & Runbook

## Mission Profile
- **Scope:** Case intake, investigation objectives, subject roster, and agency credentials.
- **Primary Outputs:** Structured payload (`section_1_profile`) and narrative summary routed to Marshall → Librarian → Mission Debrief.
- **Signals:** publishes `section_1_profile.completed`, emits `case_metadata_ready`, relays faults via `section.fault.4-1`, mayday via `section.mayday.4-1`.

## Dependency Map (Hard Imports)
| Artifact | Initializer | Source |
| --- | --- | --- |
| EvidenceManager | `_init_evidence_manager.py` | `The Marshall/evidence_manager.py` |
| North Star protocol | `_init_northstar_protocol.py` | `Tool kit/tools.py/northstar_protocol_tool.py` |
| Cochran identity check | `_init_cochran_match.py` | `Tool kit/tools.py/cochran_match_tool.py` |
| Reverse Continuity | `_init_reverse_continuity.py` | `Tool kit/tools.py/reverse_continuity_tool.py` |
| Metadata processor | `_init_metadata_processor.py` | `Tool kit/tools.py/metadata_tool_v_5.py` |
| Mileage audit | `_init_mileage_audit.py` | `Tool kit/tools.py/mileage_tool_v_2.py` |
| Section renderer | `_init_section_renderer.py` | `Tool kit/tools.py/section_1_gateway.py` |
| OCR primary | `_init_unstructured.py` | `War Room/SOPs/READ FILES/Build Specs` (Unstructured) |
| OCR secondary | `_init_tesseract.py` | Tesseract binaries/tessdata |
| OCR fallback | `_init_easyocr.py` | EasyOCR models |

> All initializers are executed during `run_baseline_initialization()`. Missing imports surface as baseline failures so Marshall/UDS capture the fault before work begins.

## Lifecycle Hooks
1. **Startup:** instantiate communicator, call `run_baseline_initialization()` → transitions to `ACTIVE` on success.
2. **Rest/Sleep:** `enter_rest_state(reason)` to pause while other sections execute; `resume_from_rest()` returns to `ACTIVE`.
3. **Shutdown:** `soft_shutdown(reason)` closes dependencies, reports completion to Marshall, sets state `SHUTDOWN`.
4. **Faults:** use `emit_fault(code, …)` for structured issues; `emit_mayday()` when fault relay is unavailable.

## OCR Execution Order
1. `unstructured_engine.partition()` (documents/PDFs, highest fidelity).
2. `tesseract_engine.extract_text()` (images + PDF fallback).
3. `easyocr_engine.extract_text()` (final safety net).

The final payload records `ocr_results[evidence_id] = {engines_attempted, text_blocks, text}` for downstream narrative reasoning.

## Development Workflow
1. **Add/Modify Logic**
   - Implement stage behaviour inside `section_1_framework.py` (respect the `STAGES` guardrails).
   - Extend payload structure cautiously; downstream systems consume `northstar_result`, `cochran_result`, `reverse_continuity_result`, `mileage_audit`, and `ocr_results`.
2. **Update Dependencies**
   - Add new helpers via `_init_<dependency>.py`. Avoid inline imports inside the framework.
   - For artifacts stored elsewhere, reference the authoritative War Room / Marshall file and document the path.
3. **Testing**
   - Unit: `python -m unittest discover -s "Analyst 1/Tests" -p "test_*.py"`.
   - Smoke (manual for now): instantiate `Section1Framework` inside a REPL to review `baseline_report`, `dependencies`.
   - After integration with Marshall/Warden, execute deck-wide smokes once available.
4. **Logging**
   - Leave `self.logger` calls in place (baseline/logical errors use `self.emit_fault`).
   - Record work in `dev_tracking` and note any missing dependencies or test updates.

## Open Backlog
- Create higher-level integration tests that exercise rest/resume and publish paths under Marshall orchestration.
- Confirm OCR asset fixtures for consistent automated testing.
- Coordinate with Sections 2–8 so shared tooling (e.g., North Star updates) remains compatible.

Use this document when pairing on Section 1 to keep dependency loading, lifecycle behaviour, and testing consistent across agents.***
