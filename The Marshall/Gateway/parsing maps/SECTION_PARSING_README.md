# Section Parsing Reference – Evidence-Driven Report Workflow

This reference links the gateway payload builders, toolkit outputs, and parsing maps used to populate every report section. Use it when verifying data flows, refreshing documentation, or preparing regression fixtures.

## End-to-End Flow
1. **Intake & OCR** – `document_processor` and `evidence_pipeline` populate `processed_data` (contracts, forms, media, metadata, manual notes).
2. **Toolkit Augmentation** – `master_toolkit_engine` injects mileage, continuity, northstar, billing, cochran, metadata, and OSINT checks into `toolkit_results`.
3. **Gateway Context** – `gateway_controller` calls `section_parsing_dispatcher.build_section_context`, yielding structured inputs, AI triggers, UI checklists, and dependencies per section.
4. **Rendering** – Section renderers consume the curated payloads, while OpenAI checkpoints (from the plan) provide narrative or compliance assistance.
5. **Approval & Export** – UI checklists ensure user acknowledgement; Section FR composes approved sections, attachments, and export manifests.

## Validation Checklist
- **Docs Updated** – Ensure each markdown in `Gateway/parsing maps/` mirrors the dispatcher inputs and dependencies.
- **Fixtures** – Stage representative cases covering audio transcripts, mileage logs, legal notices, and manual notes to exercise every field.
- **Smoke Harness** – Run `dev_tracking/agent_1_POWER_CODING/smoke_harness.py`; confirm Section outputs align with the updated parsing expectations.
- **Toolkit Signals** – Verify mileage/audit JSONs and OSINT keys are present so toolkit_results populate their slots.
- **Logs** – Capture session and parsing review logs for DEESCALATION hand-off.

## Key Files
- `Gateway/section_parsing_dispatcher.py`
- `Processors/document_processor.py`
- `Processors/evidence_pipeline.py`
- `Tools/master_toolkit_engine.py` (+ individual tool modules)
- `Gateway/parsing maps/*.md`
- `dev_tracking/agent_1_POWER_CODING/smoke_harness.py`
