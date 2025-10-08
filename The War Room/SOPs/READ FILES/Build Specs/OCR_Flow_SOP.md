# DKI Engine OCR & Evidence Flow SOP (Draft)

## 1. Purpose & Scope
This operating procedure defines how the DKI Engine ingests, extracts, validates, and distributes evidence across the reporting pipeline. It replaces the legacy "single text stream" model with an orchestrated flow that prioritises the strongest extraction engines (Tesseract OCR and the Unstructured parser) while keeping specialised tooling available on demand.

## 2. Guiding Principles
- **Strongest-first execution** – Always attempt the most accurate extractors before falling back to broad-spectrum engines.
- **Central orchestration** – The Gateway owns the master evidence bundle and mediates every tool invocation and section hand-off.
- **Deterministic stages** – Each stage has explicit triggers, required inputs, success criteria, and confirmation logging.
- **Structured outputs** – All engines publish into a shared schema (`text_blocks`, `tables`, `entities`, `media`, `metadata`, `ai_notes`).
- **Section autonomy** – Sections pull the data they need and publish structured results back, rather than overwriting shared state.
- **Fail fast, fall back gracefully** – Missing binaries or adapters surface immediately with actionable logs and controlled fallbacks.

## 3. Pipeline Overview
1. **Intake & Classification** – Normalise file descriptors; detect media type, language hints, and priority tags.
2. **Primary Extraction** – Run Tesseract (images/PDF scans) and Unstructured (native PDFs, DOCX, text) in parallel when supported.
3. **Fallback Extraction** – If primary engines return empty text, cascade to EasyOCR, PaddleOCR, or Azure OCR (when enabled).
4. **Media-Specific Processing** – Invoke Whisper (audio/video), MoviePy/OpenCV (frame sampling), EXIF/metadata readers as required.
5. **Enrichment & Validation** – Execute AI confirmation, OSINT lookups, and rule-based validators via the Gateway.
6. **Section Assembly** – Sections request the structured payload they require, perform specialised analysis, and post results.
7. **Final Report Compilation** – Aggregate section outputs, confirm completeness, and render export templates using live data.

## 4. Stage Detail
### 4.1 Intake & Classification
- Responsible module: `DocumentProcessor._process_single_file`
- Inputs: Uploaded file descriptors, user-specified tags
- Outputs: Normalised `file_info`, media classification, priority flags
- Confirmation: Classification logged to `processing_log`; unsupported types flagged before extraction

### 4.2 Primary Extraction (Tesseract & Unstructured)
- Trigger: File classified as image/PDF (Tesseract) or supported document (Unstructured)
- Tooling:
  - Tesseract binary resolved from packaged `Processors` directory, `%TESSERACT_CMD%`, or system path
  - Unstructured adapter invoked when `DKI_ENABLE_UNSTRUCTURED=1` and adapter health checks pass
- Output: Structured payload with `text_blocks`, `tables`, `entities`, `layout`, `confidence`
- Confirmation: `_tesseract_cmd_available()` and `unstructured_capabilities()` logged; failure escalates to fallback stage

### 4.3 Fallback Extraction (EasyOCR, PaddleOCR, Azure)
- Trigger: Primary extraction produced no text or confidence below threshold
- Tooling ordered by capability: EasyOCR -> PaddleOCR -> Azure OCR (when configured)
- Output: `ocr` block with fallback annotations (`fallback_attempts`, `engine_used`)
- Confirmation: Gateway records fallback usage for post-run review

### 4.4 Media-Specific Processing
- Audio/video: Whisper for transcripts, MoviePy/OpenCV for frame capture, resolved only when media type demands
- Images: EXIF/TIFF metadata, face/object detection when section tooling requests
- Confirmation: Each media tool logs start/finish and publishes artifacts under `media_analysis`

### 4.5 Enrichment & Validation
- Gateway triggers OSINT, OpenAI context checks, compliance validators on-demand from sections
- Results stored under `enrichment` with provenance metadata (tool, parameters, checksum)
- Confirmation: Each enrichment call requires success flag + short summary before sections can consume

## 5. Gateway Orchestration Model
- Maintains the master `case_bundle` containing all stage outputs
- Exposes APIs for sections to request data slices, trigger additional tooling, and publish results
- Enforces stage order: no section runs until primary extraction and required enrichment are confirmed
- Logs cross-section dependencies (e.g., Section 6 requesting Section 2 outputs) and ensures idempotent access

## 6. Section Responsibilities & Interactions
| Section | Primary Inputs | Optional Engines | Outputs Published |
|---------|----------------|------------------|-------------------|
| TOC / Case Summary | Gateway `text_blocks`, entities | OpenAI summariser | Overview narratives, key findings |
| Surveillance (Sec 2) | Tesseract text, frame OCR, EXIF | CV detection, Whisper (if audio) | Timeline, highlights, asset references |
| Data Logs (Sec 3) | Unstructured tables, metadata | AI Anomaly checks | Structured tables, anomaly notes |
| Supporting Docs (Sec 4/5) | Unstructured layout, OCR text | Validators | Document summaries, compliance notes |
| Billing (Sec 6) | Mileage/lookup tools | Cohcran match | Billing breakdowns, variances |
| Media / Attachments | Media analysis bundle | Face/object detection | Attachment summaries, confidence |

Sections communicate exclusively through the Gateway: requests for shared data or tool invocations are routed and logged centrally.

## 7. Final Assembly & Export
- Consume section outputs from the `case_bundle`
- Verify each section met mandatory confirmation gates before rendering
- Templates reference structured fields (no hard-coded copy)
- Export pipeline logs provenance (engines used, timestamps, fallback history)

## 8. Operational Triggers & Confirmations
- **Stage Start**: Gateway records timestamp, input set, tool versions
- **Stage Complete**: Structured payload validated against schema; results marked available
- **Stage Failure**: Immediate escalation with actionable error (missing binary, adapter failure)
- **Final Gate**: All mandatory stages confirmed; unresolved sections flagged in export summary

## 9. Monitoring & Testing
- Automated tests: `test_ocr_engines.py` extended for Tesseract-first + Unstructured flows; end-to-end report test validates section consumption
- Health scripts: Verify Tesseract executable, tessdata presence, Unstructured adapter readiness, fallback engine availability
- Runtime telemetry: Gateway emits JSON status snapshots for dev tracking dashboards

## 10. Rollout Checklist (Theoretical)
1. Implement DocumentProcessor refactor (engine order, structured outputs)
2. Update Gateway orchestration API and case bundle schema
3. Retrofit section renderers + docs to consume structured payloads
4. Rewrite final export module to honour new structure
5. Refresh SOP/handbook documentation, parsing maps, and training material
6. Run staged regression (unit -> integration -> full E2E)
7. Monitor initial cases for fallback frequency and adjust thresholds if needed

## 11. Appendix – Configuration Defaults
- `DKI_ENABLE_UNSTRUCTURED=1`
- `DKI_ENABLE_TESSERACT=1` with packaged binary path auto-detected
- `DKI_OCR_FALLBACKS="easyocr,paddleocr,azure"`
- `DKI_SECTION_CONFIRMATION=required`
- Logging level: `gateway=INFO`, `sections=INFO`, `engines=DEBUG`

*This draft SOP captures the agreed future-state architecture; it should be refined alongside implementation to reflect actual module names, confirmation hooks, and operational playbooks.*

