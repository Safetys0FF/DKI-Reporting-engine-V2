# Central Command – System Analysis

## Current Architecture Snapshot
- **Evidence Locker** now persists the manifest via `_persist_manifest` / `_load_persisted_manifest`, exposing `get_structured_manifest()` and `get_common_pool()` so every subsystem can query the full evidence pool even after restarts.
- **Evidence Checkout (Marshall)** runs as `The Marshall\Evidence_Checkout\section_controller.py`, subscribing to `section.needs` / `evidence.deliver`, translating manifest entries into section-ready payloads, deduping deliveries, and dispatching enriched `section.data.updated` events.
- **Gateway Runtime** dynamically loads Evidence Checkout and the new Analyst Deck bridge during startup (see `main_application.py`, `main_application_activation.py`, `central_plugin.py`), ensuring the bus wiring is present in every launch mode.
- **Weighed Bus Enhancements** in `bus_core.py`:    - Added `get_section_data()` accessor and a `narrative.assembled` handler which merges assembled narratives back into `section_data`.    - Event log now captures narrative completions for audit/history.
- **NarrativeAssembler** pulls section payloads enriched by Evidence Checkout, generates evidence highlights, and emits canonical `narrative.assembled` payloads (case-aware, section-aware).
- **Deck Bus Listener** (`deck_bus_listener.py`) subscribes to `section.data.updated`, `narrative.assembled`, `case.snapshot`, `mission.status`, persisting a JSON snapshot (`deck_state.json`) so analyst tooling and dashboards can consume live bus data without reinventing wiring.
- **Section Framework Base** now exposes `get_bus_state()` / `_augment_with_bus_context()`, giving every section a consistent way to merge manifest snapshots and CAN-bus context into their tooling pipeline.
- **Section Frame­works (Analyst 1–9, CP, DP, TOC)** were updated to invoke `_augment_with_bus_context()` inside `load_inputs()`, so future enrichment work has direct access to the manifest payload, case IDs, and Evidence Checkout metadata.

## Outstanding Integration Gaps
1. **Per-Section Enrichment Pipeline**     Each section still needs to:     - Execute its unique tooling (OCR, billing, compliance, etc.) against the merged payload.     - Hand the enriched result back to the Marshall Gateway (`publish_section_result`) so the Evidence Locker, Librarian, and Debrief receive synchronized updates.
2. **Marshall Handoff Hooks**     Ensure the Gateway controller commits enriched payloads back into the locker and fires `section.data.updated` / `gateway.section.complete` for the new context (currently only stubs exist).
3. **Execution Ordering Enforcement**     Implement guardrails so the sections run sequentially: 1 → 2 → 5 → 3 → 4 → 8 → 7 → 6, before Librarian/Debrief handle TOC, DP, CP.
4. **Reporting Surface**     GUI Review tab and Mission Debrief need to render the enriched payload fields coming from the new flow (currently they log/queue data but don’t display every field).

## Reliability Considerations
- Ensure manifest persistence writes are atomic (already using temp files).
- Evidence Checkout dedupe window is currently 12 seconds; verify that’s sufficient when sections re-request evidence during revisions.
- Deck bus listener state file can grow; consider log rotation or limiting snapshots once dashboards consume data.

## Risks
- Without completing the per-section tooling + publish integration, the system still produces skeleton narratives only.
- Gateway controller needs richer error handling so locker updates don’t silently fail.
- We must avoid tight coupling between section frameworks and bus internals—Gateway remains the canonical interface.
