# Section 8 Media Catalog — Build Plan (2025-10-10)

## Context & Current Behaviour
- The existing `Section8Framework` still subclasses the legacy `SectionFramework` base. It handles intake, filtering, validation, and publish stages directly without lifecycle state management (`run_baseline_initialization`, rest/shutdown, dependency tracking).
- Media ingestion relies on a `media_index` bundle containing `images`, `videos`, and `audio`. Records are normalized via `_normalize_media_record`, which assigns IDs, preserves timestamps, and keeps simple labels/locations.
- `_build_media_payload` aggregates normalized media, section manifests (sections 3 & 4), toolkit output, and manual notes. QA flags currently only check for the absence of images/videos.
- `_run_inline_tools` executes in-process helper classes (`NorthstarProtocolTool`, `CochranMatchTool`, `ReverseContinuityTool`, `MetadataToolV5`, `MileageToolV2`). These helpers are defined in the same module and use synchronous, best-effort logic; there is no dependency injection or lifecycle-aware resource management.
- Publishing renders the payload through `Section8Renderer`, emits gateway results, and broadcasts `section_8_ready`. There is no baseline report or structured dependency status returned to ECC/Marshall.
- No `_init_*.py` modules or unit tests exist for Section 8. The DEV strategy calls for computer vision tagging, audio transcription, captioning, and metadata extraction, but these are not yet modularised or validated.

## Gaps & Risks
- **Lifecycle coverage**: Without the lifecycle wrapper, Section 8 cannot declare dependency readiness, rest states, or clean shutdown of GPU/audio handles.
- **Dependency injection**: Heavy engines (CV detector, Whisper, captioner) are referenced conceptually but not wired. Everything runs through stubbed helpers, making it hard to swap implementations or track failures.
- **Data enrichment**: Normalisation captures only basic metadata; there is no consolidation of EXIF/video details, thumbnails, or cross-links to narratives and POIs as promised by the mission profile.
- **Error handling & QA**: QA flags are minimal; corrupt assets, CV failures, or missing metadata do not surface distinct codes. Toolkit results intermingle success/error dictionaries with no schema.
- **Testing**: Absence of unit tests or fixtures means regressions in media indexing or renderer output will go unnoticed.

## Implementation Strategy
1. **Introduce Lifecycle Wrapper**
   - Rename the current class to `LegacySection8Framework` and encapsulate existing logic.
   - Implement a new `Section8Framework(LifecycleSectionFramework)` mirroring Sections 3–6, injecting dependencies via `_init_` modules and capturing baseline reports.
   - Add lifecycle hooks for rest/shutdown to release GPU/audio resources and persist derived artifacts.

2. **Modularise Dependencies**
   - Create `_init_` modules for: evidence/media manager, CV detector, audio transcription (shared Whisper), caption generator, metadata extractor (EXIF/video), OCR pipeline, and renderer factory.
   - Refactor `_run_inline_tools` to delegate into injected dependencies with structured responses (`status`, `details`, `timings`).
   - Capture dependency outcomes in the baseline report and promote them into QA flags when they fail.

3. **Media Orchestration Enhancements**
   - Build a dedicated media catalog orchestrator to ingest assets, perform deduplication, timeline alignment, and create enriched manifests (people/objects detected, GPS alignment, thumbnails).
   - Expand `_build_media_payload` to include annotation bundles (`who/what/where/when`, confidences, derived thumbnails) and link back to Section 3 narratives.
   - Support configurable policies driven by contract/ecc whitelists (e.g., redact certain media categories).

4. **Publishing & Fault Handling**
   - Ensure publish step logs provenance, attaches derived manifests, and emits structured signals (`section_8_media.completed`).
   - Harden fault codes for model load failures, corrupt assets, metadata extraction issues, and ensure they route through ECC/Marshall.

5. **Testing & Fixtures**
   - Add `Analyst 8/Tests` with unit coverage for baseline initialisation, media normalisation, dependency failure surfacing, and publish outputs.
   - Provide lightweight fixtures: sample image/video metadata stubs, transcripts, and manifests to validate orchestration logic offline.
   - Include golden snapshots for renderer output (manifest summary, narrative text).

## Next Steps
- Confirm available CV/audio/captioning engines (model weights, GPU requirements) and decide on stub vs. real integrations for the initial migration.
- Outline dependency interface contracts (`MediaTagger`, `Captioner`, `MetadataExtractor`) before refactoring legacy helpers.
- Draft the lifecycle migration tasks based on this plan and schedule implementation in the next build session.
