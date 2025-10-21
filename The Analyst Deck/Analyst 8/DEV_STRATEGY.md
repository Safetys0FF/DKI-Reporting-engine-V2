# Section 8 – Development Strategy & Runbook

## Mission Profile
- **Scope:** Media catalog (photos, video, audio), contextual tagging, asset readiness for Mission Debrief.
- **Primary Outputs:** `section_8_media` payload with indexed assets, captions, confidence scores, linkage to narratives.
- **Signals:** publishes `section_8_media.completed`, listens for `section.needs` categories `["media_photo", "media_video"]`, faults via `section.fault.4-8`.

## Planned Dependency Map
| Artifact / Engine | Status | Notes |
| --- | --- | --- |
| EvidenceManager | 🔄 `_init_evidence_manager.py`. |
| OCR stack | 🔄 Unstructured/Tesseract/EasyOCR for embedded text. |
| Computer vision tagging | ⏳ `_init_cv_detector.py` (YOLO/Detectron etc.). |
| Audio transcription | ⏳ `_init_whisper.py` (shared with Section 3). |
| Metadata extractor | ✅ reuse metadata tool initializer, extend for EXIF/video metadata. |
| Captioning/summary | ⏳ `_init_media_captioner.py` for narrative-ready captions. |
| Narrative renderer | ⏳ `_init_section8_renderer.py` for appendix/mission export integration. |

## Lifecycle Stages
1. Baseline: ensure CV/A/V models and metadata libraries load (fail fast if GPU/weights missing).
2. Rest: coordinate with Sections 2 & 3 to avoid double-processing; rely on `enter_rest_state`.
3. Shutdown: release GPU/audio handles, persist derived artifacts, emit `section.shutdown`.
4. Fault flow: categorize model failure vs. corrupt media to help Marshall triage.

## Development Workflow
1. Migrate existing framework to lifecycle base with `_init_` dependency pattern.
2. Implement pipeline:
   - Acquire media from locker.
   - Extract metadata (EXIF, codecs, timestamps).
   - Run CV/A/V models for tagging and transcription.
   - Generate captions + manifest entries.
   - Publish structured payload + narrative summary.
3. Testing:
   - Add unit tests (baseline, tagging pipeline, OCR fallback) under `Analyst 8/Tests`.
   - Provide sample media fixtures for repeatable automation.
4. Documentation:
   - Track model versions, inference parameters, GPU requirements here.
   - Update dev_tracking when media schemas or artifact formats change.

## Backlog
- Choose standard CV/ASR models and package them via `_init_` modules.
- Define canonical media manifest schema (thumbnails, derived assets, confidences).
- Integrate with Section 2 POI planning and Section 3 surveillance transcripts.
- Build integration smoke to confirm entire media pipeline under Marshall control.

Maintain this strategy to keep Section 8 development aligned across agents—hard imports, lifecycle behaviour, and testing expectations must stay consistent as the media engine grows.***
