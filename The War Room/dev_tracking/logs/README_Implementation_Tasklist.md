# Central Command – Section Integration Task Plan

## Objectives
1. Wire each section framework (1, 2, 5, 3, 4, 8, 7, 6, then CP/DP/TOC) to:
   - Pull CAN-bus context via the Gateway.
   - Execute section-specific enrichment tooling.
   - Publish enriched payloads back through Marshall so Evidence Locker, Librarian, Debrief, and GUI stay in sync.
2. Confirm Gateway propagates enriched payloads via `section.data.updated` / `gateway.section.complete` and updates the manifest.
3. Surface enriched data in the Review tab, Mission Debrief, TOC/Disclosure/Cover Page.

## Implementation Checklist
### 1. Gateway Enhancements
- [ ] Extend `gateway_controller` with `publish_section_result(section_id, payload)` that:
  - Updates the Evidence Locker manifest (new locker method).
  - Emits bus signals (`section.data.updated`, `gateway.section.complete`, optional `section.data.enriched`).
  - Logs to gateway status for GUI/Deck visibility.
- [ ] Ensure Gateway exposes `get_section_inputs(section_id)` enriched by Evidence Checkout to sections.

### 2. Section Framework Wiring (repeat per section)
For each of Section 1 → 2 → 5 → 3 → 4 → 8 → 7 → 6 → CP → DP → TOC:
- [ ] Replace raw gateway pulls with `self._augment_with_bus_context(self.gateway.get_section_inputs(...))`.
- [ ] Execute section-specific tooling (OCR, metadata, compliance, billing, narrative fragments).
- [ ] Build canonical enriched payload (evidence, analytics, QA flags, timestamps, tool signatures).
- [ ] Call `self.gateway.publish_section_result(section_key, payload)`; ensure payload includes case ID, evidence IDs, stage metadata.
- [ ] Handle revision flow: re-run tooling when revisions arrive, re-publish enriched result.

### 3. Evidence Locker Updates
- [ ] Add `update_enriched_payload(evidence_id, payload)` (or similar) so sections can replace manifest entries.
- [ ] Validate enriched payload persists via the manifest writer and is available to downstream sections.

### 4. Narrative / Debrief Alignment
- [ ] NarrativeAssembler consumes enriched payload fields (auto-summary, QA findings, highlights already in place).
- [ ] Mission Debrief manager stores enriched context for TOC/Disclosure/CP generation.

### 5. Review Tab & Analyst Deck
- [ ] Enhanced GUI Review panel renders new fields from `section.data.updated`.
- [ ] Analyst deck dashboards read from `deck_state.json` or a live API, showing section status, QA flags, narrative summaries.

### 6. Validation & Ordering
- [ ] Implement guard code (ORDER contracts or ECC rules) so sections execute in prescribed order.
- [ ] Add smoke tests: ingest sample evidence → confirm sections publish enriched payloads sequentially → final export matches expectations.
- [ ] Document revision scenarios: re-run Section 1 → verify downstream sections consume revised data.

## Deliverables
- Updated section frameworks with CAN-bus aware workflows.
- Gateway controller enhancements + Evidence Locker enriched update support.
- GUI/Librarian/Debrief views reflecting enriched payloads.
- Smoke/regression tests covering end-to-end report generation.

## Notes
- Keep each section modular—no direct cross-section calls; everything routes via Gateway/CAN bus.
- Enriched payload schema should remain backwards compatible so downstream consumers degrade gracefully.
