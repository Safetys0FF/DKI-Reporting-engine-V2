# Central Command Evidence & Section Integration Plan (2025 Q4)
## Objectives
- Ensure each report section automatically receives the correct evidence, metadata, and enrichment based on the latest routing rules.
- Close the request/deliver/enrichment loop so sections share updates over the bus and the Evidence Locker remains the source of truth.
- Provide deterministic final assembly (narratives, billing, disclosures) based on section outputs and locker manifest.
## Phase 1 � Evidence Classification & Metadata (Week 1)
1. **Locker Classification Enhancements**
   - Expand `classify_evidence` rules to explicitly map:
     - Intake forms, client questionnaires ? Section 1 & Section 2 queues.
     - Background packets, open-source reports ? Sections 1, 2, 3/4, 5.
     - Contracts, retainers, billing docs ? Section 5 & Section 6.
     - Multimedia (photos, videos) ? Section 2 (contextual), Section 8 (primary).
     - Investigator field notes, surveillance summaries ? Sections 3/4 & 6.
   - Add structured tags (`intake`, `background`, `contract`, `billing`, `media`, etc.) for downstream filtering.
2. **Metadata Extraction Pipeline**
   - Extend `process_evidence_comprehensive` to capture EXIF/FFprobe data, document metadata, geocoding lookups.
   - Normalize outputs into `classification` for use in `evidence.updated` payloads.
3. **Manifest Persistence**
   - Verify `bus_extensions` record complete manifest entries (including tag sets, geo details, billing fields).
   - Add regression tests to confirm new metadata fields persist through store ? scan ? comprehensive flow.
## Phase 2 � Bus Loop Completion (Week 2)
1. **Gateway Handoff Alignment**
   - Update GUI `central_plugin.process_evidence_comprehensive` handoff to use `operation="evidence_classification"` (or teach gateway to treat `evidence_handoff_gui` as classification).
   - Pass full locker `classification` + `section_hint` in the handoff payload.
2. **Gateway Handlers**
   - Wire `_handle_classification_handoff` to emit `section.needs` and prime `_pending_section_outputs`.
   - Ensure gateway publishes `section.data.updated` + `gateway.section.complete` with enriched context from locker metadata.
3. **Locker Request/Deliver**
   - Finish `_handle_evidence_request_signal` to support filters (tags, sections, priority) and targeted responses via `evidence.deliver`.
   - Add throttling/back-off for repeated requests to avoid duplicate deliveries.
## Phase 3 � Section Controllers & Enrichment (Weeks 3�4)
1. **Section Subscription Matrix**
   - Implement section controllers (or broker) that subscribe to relevant evidence signals per section requirements:
     - Section 1: intake forms, background summaries.
     - Section 2: intake + geo-tagged media.
     - Sections 3/4: field notes, surveillance documents, data reports.
     - Section 5: contracts, documents, communication logs.
     - Section 6: billing data, mileage/timestamps, Section 5 ledger.
     - Section 7: cross-section analytics (watch `section.data.updated` from 1,5,8).
     - Section 8: photo/video stream.
2. **Evidence Consumption Workflow**
   - For each section handler:
     - Issue `evidence.request` when new needs appear (`section.needs` or manual trigger).
     - Consume `evidence.deliver`, run section-specific processing/enrichment.
     - Emit `evidence.updated` with structured results (captions, billing line items, analytics, etc.).
3. **GUI Structured Section Data**
   - Modify `_build_structured_section_data` to merge locker manifest + section enrichments instead of relying purely on upload snapshot.
   - Cache per-section enriched data for editor previews and narrative generation.
## Phase 4 � Narrative & Final Assembly (Weeks 5�6)
1. **Mission Debrief Integration**
   - Subscribe `NarrativeAssembler` to `evidence.updated` and `case.snapshot` signals.
   - Rework narrative templates to draw from the enriched manifest (Section 1�8 data) rather than static payloads.
2. **Billing & Compliance (Section 6)**
   - Implement reconciliation service that aggregates time stamps, mileage, billing totals, and retainer data.
   - Validate congruence against Section 5 documents; emit discrepancies via `mission.status` warnings.
3. **Section 7 Analytical Layer**
   - Build analytics job to synthesize findings across sections 1, 5, 8, producing narrative summary + risk notes.
   - Publish results back as `evidence.updated` entries referencing `analysis_section_7`.
4. **Disclosures & Final Assembly**
   - Introduce disclosure library (JSON/YAML) with preset templates.
   - Update GUI to allow selection and inject chosen disclosures into final report pipeline.
   - Ensure final assembly pulls section narratives, Section 8 media index, Section 6 billing, Section 5 appendix, and disclosures sequentially.
## Phase 5 � Validation & Tooling (Weeks 7�8)
1. **Automated Tests**
   - Expand `test_gateway_wiring.py` to assert new signal operations.
   - Add locker regression tests for classification/metadata coverage.
   - Create end-to-end scenario in `Test Plans` that simulates ingest ? request ? deliver ? enrich ? narrative.
2. **Monitoring & Diagnostics**
   - Extend GUI dashboards to display active `section.needs`, pending evidence requests, and `evidence.updated` counts.
   - Add bus health check that ensures every evidence signal has at least one subscriber.
3. **Documentation Updates**
   - Refresh SYSTEM README files (Locker, Gateway, Analyst Deck, Librarian, Warden) to reflect new flows.
   - Publish sequence diagrams demonstrating request/deliver/enrich cycle and section dependencies.
## Deliverables
- Updated Evidence Locker classification & metadata modules.
- Gateway controller with aligned handoff operations and section dispatch.
- Section controllers/broker handling evidence requests and enrichments.
- Revised GUI structured section builder and disclosure picker.
- Mission Debrief narratives driven by enriched manifest data.
- Comprehensive automated test coverage and updated documentation.
## Risks & Mitigations
- **Signal Flooding**: Introduce debouncing or batching for high-frequency `evidence.updated` emissions.
- **Metadata Completeness**: Log missing metadata fields and surface via Analyst Deck anomaly checks.
- **Cross-section Coupling**: Maintain schema contracts for `evidence.updated` payloads to avoid downstream breakage.
- **Legacy Paths**: Audit for any residual direct file reads that bypass the bus; route them through locker requests instead.
## Milestones
- **M1 (End Week 2)**: Locker emits rich metadata; gateway recognises GUI handoffs; request/deliver loop functional in tests.
- **M2 (End Week 4)**: Sections 1�8 controllers generating enrichment via bus; GUI showing merged structured data.
- **M3 (End Week 6)**: Narrative assembler & final assembly consume enriched data; disclosures selectable.
- **M4 (End Week 8)**: Test suite green; documentation published; analyst dashboards reflect new telemetry.
## To-Do Checklist
- [x] Phase 1 - Evidence Classification & Metadata
- [x] Phase 2 - Bus Loop Completion
- [x] Phase 3 - Section Controllers & Enrichment
- [ ] Phase 4 - Narrative & Final Assembly
- [ ] Phase 5 - Validation & Tooling
- [x] Phase 2 - Bus Loop Completion
- [x] Phase 3 - Section Controllers & Enrichment
- [ ] Phase 4 - Narrative & Final Assembly
- [ ] Phase 5 - Validation & Tooling
## Phase 2 - Bus Loop Completion (Week 2)
  1. **Gateway Handoff Alignment**
     - Update GUI `central_plugin.process_evidence_comprehensive` handoff to use `operation="evidence_classification"` (or teach gateway to treat `evidence_handoff_gui` as classification).
     - Pass full locker `classification` + `section_hint` in the handoff payload.
  2. **Gateway Handlers**
     - Wire `_handle_classification_handoff` to emit `section.needs` and prime `_pending_section_outputs`.
     - Ensure gateway publishes `section.data.updated` + `gateway.section.complete` with enriched context from locker metadata.
  3. **Locker Request/Deliver**
     - Finish `_handle_evidence_request_signal` to support filters (tags, sections, priority) and targeted responses via `evidence.deliver`.
     - Add throttling/back-off for repeated requests to avoid duplicate deliveries.

## Phase 3 - Section Controllers & Enrichment (Weeks 3-4)
  1. **Section Subscription Matrix**
     - Implement section controllers (or broker) that subscribe to relevant evidence signals per section requirements:
       - Section 1: intake forms, background summaries.
       - Section 2: intake + geo-tagged media.
       - Sections 3/4: field notes, surveillance documents, data reports.
       - Section 5: contracts, documents, communication logs.
       - Section 6: billing data, mileage/timestamps, Section 5 ledger.
       - Section 7: cross-section analytics (watch `section.data.updated` from 1,5,8).
       - Section 8: photo/video stream.
  2. **Evidence Consumption Workflow**
     - For each section handler:
       - Issue `evidence.request` when new needs appear (`section.needs` or manual trigger).
       - Consume `evidence.deliver`, run section-specific processing/enrichment.
       - Emit `evidence.updated` with structured results (captions, billing line items, analytics, etc.).
  3. **GUI Structured Section Data**
     - Modify `_build_structured_section_data` to merge locker manifest + section enrichments instead of relying purely on upload snapshot.
     - Cache per-section enriched data for editor previews and narrative generation.

## Phase 4 - Narrative & Final Assembly (Weeks 5-6)
  1. **Mission Debrief Integration**
     - Subscribe `NarrativeAssembler` to `evidence.updated` and `case.snapshot` signals.
     - Rework narrative templates to draw from the enriched manifest (Section 1�8 data) rather than static payloads.
  2. **Billing & Compliance (Section 6)**
     - Implement reconciliation service that aggregates time stamps, mileage, billing totals, and retainer data.
     - Validate congruence against Section 5 documents; emit discrepancies via `mission.status` warnings.
  3. **Section 7 Analytical Layer**
     - Build analytics job to synthesize findings across sections 1, 5, 8, producing narrative summary + risk notes.
     - Publish results back as `evidence.updated` entries referencing `analysis_section_7`.
  4. **Disclosures & Final Assembly**
     - Introduce disclosure library (JSON/YAML) with preset templates.
     - Update GUI to allow selection and inject chosen disclosures into final report pipeline.
     - Ensure final assembly pulls section narratives, Section 8 media index, Section 6 billing, Section 5 appendix, and disclosures sequentially.

## Phase 5 - Validation & Tooling (Weeks 7-8)
  1. **Automated Tests**
     - Expand `test_gateway_wiring.py` to assert new signal operations.
     - Add locker regression tests for classification/metadata coverage.
     - Create end-to-end scenario in `Test Plans` that simulates ingest -> request -> deliver -> enrich -> narrative.
  2. **Monitoring & Diagnostics**
     - Extend GUI dashboards to display active `section.needs`, pending evidence requests, and `evidence.updated` counts.
     - Add bus health check that ensures every evidence signal has at least one subscriber.
  3. **Documentation Updates**
     - Refresh SYSTEM README files (Locker, Gateway, Analyst Deck, Librarian, Warden) to reflect new flows.
     - Publish sequence diagrams demonstrating request/deliver/enrich cycle and section dependencies.
