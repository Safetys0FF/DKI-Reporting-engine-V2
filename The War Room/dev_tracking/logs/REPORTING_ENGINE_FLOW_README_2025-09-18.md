# Reporting Engine Flow Blueprint - 2025-09-18

## Purpose
- Document the tunnel-style processing plan so evidence intake ("Load Documents") feeds the full reporting pipeline instead of terminating at the cache.
- Align the plan with existing section READMEs and parsing maps to keep governance consistent across the engine.

## Current Symptoms
- Evidence cache accumulates uploads but does not hand them to the OCR/context/reporting chain.
- Engines run independently; outputs overwrite or bypass each other, leaving sections empty.
- Section-level READMEs are not being exercised, so validation and rendering steps stall.

## Proposed Tunnel Flow
1. Intake Manifests
   - Normalize metadata, compute hashes, and emit manifest entries per upload (mirrors intake README guidance).
   - Store manifests alongside the evidence cache for downstream traceability.
2. Media Routing
   - Inspect each manifest entry and map it to a section-specific parser (per parsing map).
   - Choose the preferred OCR/decoder for that asset type before moving on to context.
3. OCR Stack Execution
   - Run prioritized engines (image -> EasyOCR/Paddle/Tesseract, PDF -> pdfplumber + OCR, video -> frame OCR, charts -> Paddle tables).
   - Capture fallback attempts and confidence so merges never silently overwrite text.
4. Context Enrichment and AI Calls
   - Apply the section README rules (NER, regex extraction, table normalization) to produce structured JSON.
   - Trigger configured enrichment APIs (OpenAI/ChatGPT, Google services, other LLM/NLP helpers) using section-specific prompts and safeguards; capture responses alongside the OCR payload.
   - Persist outputs in per-section context directories for validation, including references to the AI calls that contributed data.
5. Validation Guardrails
   - Execute validation routines defined in each section README (totals balance, TOC cross-links, metadata checks).
   - Flag anomalies and route them to remediation queues without blocking the rest of the train.
6. Section Assembly
   - Render section templates with enriched data, tables, and referenced media.
   - Track processing methods and evidence IDs for later audits.
7. Report Synthesis
   - Combine section outputs into final DOCX/PDF packages, apply watermarks, and log completion in the evidence bus.
8. Post-Run Ledger
   - Store the manifest -> OCR -> context -> report lineage so regression harnesses can replay the full tunnel.

## External Enrichment APIs
- Central registry tracks available AI providers (OpenAI, Google, internal models) with required credentials and rate limits.
- Section READMEs specify when to invoke each provider and the prompts/payload expected.
- All responses are logged with request/response IDs so validation and auditing can trace external contributions.
- Fallback paths are defined when an API is unavailable, ensuring the tunnel still moves data forward.

## Governance Touchpoints
- Section READMEs define required fields, validation rules, and rendering expectations; the flow above references them at routing, enrichment, and assembly stages.
- Parsing maps control how raw OCR text is segmented for each section, preventing cross-section overwrites.
- Log updates (change summaries, progression logs) capture every structural adjustment for investigatory traceability.

## Implementation Steps
1. Wire the evidence cache to emit manifests and push assets into the routing queue.
2. Embed the media routing table inside `DocumentProcessor` so each file is assigned to the correct engine and section handler.
3. Harden `_perform_ocr` merges and populate scan summaries so provenance survives every hop.
4. Invoke section parsers/validators immediately after OCR and persist structured outputs in context folders, including enrichment API responses.
5. Trigger section renderers and final report builders once validations succeed; publish ledger entries to logs/evidence bus.
6. Add regression tests that drive a mixed batch through the tunnel and compare artifacts against known-good baselines.

## Expected Benefits
- Evidence cache becomes the train station, not the terminus; every upload progresses through OCR, context, validation, and reporting.
- Section READMEs stay authoritative, ensuring uniform processing across TOC, billing, final assembly, and beyond.
- Provenance is preserved (processing methods, fallback attempts, manifests, enrichment API traces), enabling audits and downstream analytics.
- Modular routing allows the OCR stack to evolve (swap engines, add adapters) without reworking the entire pipeline.

## Next Actions
- Draft the routing/priority table and review it against current section parsing maps.
- Patch `DocumentProcessor` to honor the merge safeguards recorded in the OCR review log entry.
- Schedule regression harness work once the tunnel flow is wired end to end.


