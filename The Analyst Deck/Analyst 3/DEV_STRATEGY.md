# Section 3 – Development Strategy & Runbook

## Mission Profile
- **Scope:** Field surveillance logs, chronological evidence synthesis, investigator annotations.
- **Primary Outputs:** Structured `section_3_surveillance` payload, timeline narrative, media references for Sections 6/8.
- **Signals:** publishes `section_3_surveillance.completed`, consumes `section.needs` categories `["field_notes", "media_audio"]`, faults via `section.fault.4-3`.

## Planned Dependency Map
| Artifact / Engine | Status | Notes |
| --- | --- | --- |
| EvidenceManager | 🔄 replicate `_init_evidence_manager.py` | Required handoffs. |
| OCR stack (docs/images) | 🔄 general cascade (Unstructured → Tesseract → EasyOCR) | Align with Section 1. |
| Audio transcription (Whisper) | ⏳ create `_init_whisper.py` pulling War Room processors | Mandatory for surveillance audio. |
| Video frame analyzer | ⏳ wrap `cv2`/YOLO detectors in `_init_video_analysis.py` | Extract key frames & objects. |
| GPS / telemetry parser | ⏳ add `_init_track_decoder.py` for tracker exports (CSV, NMEA). |
| Narrative renderer | ⏳ build `_init_section3_renderer.py` for field log output. |
| Continuity checks | ✅ reuse reverse continuity artifact. |

> Every heavy dependency (Whisper, CV models, trackers) must load via `_init_` modules and be validated during baseline initialization.

## Lifecycle & Fault Expectations
1. `run_baseline_initialization()` – ensure heavy models (Whisper, YOLO) are available; report failure to Marshall if missing.
2. `enter_rest_state()` – pause while map/doc sections execute; maintain pointer to active surveillance set.
3. `soft_shutdown()` – release GPU/audio/video handles.
4. Fault path via `emit_fault` / `emit_mayday` identical to other sections.

## Development Workflow
1. **Framework Migration**
   - Port logic from legacy `section_3_framework.py` into the lifecycle-aware base.
   - Replace direct imports with `_init_whisper.py`, `_init_video_analysis.py`, etc.
2. **Pipeline Implementation**
   - Stage order: intake → audio/video processing → note consolidation → validation → publish.
   - Output timeline segments with cross-links (`timeline`, `media_assets`, `ocr_results`, `transcripts`).
3. **Testing**
   - Add unit tests (baseline, audio transcript success/failure, video frame extraction).
   - Provide sample media fixtures (short WAV/MP4) under a `Tests/fixtures` folder.
4. **Documentation & Logging**
   - Update this strategy as engines land; coordinate GPU resource requirements with DevOps.

## Backlog
- Decide on frame sampling strategy (interval-based or event-based).
- Integrate GPS trail smoothing + POI alignment with Section 2 mapping.
- Add quality gates for investigator annotations (guardrails for manual edits).
- Plan integration smoke that streams a mini case through Marshall/Warden for end-to-end validation.

Keep this guide in sync as the surveillance engine matures so all agents can collaborate without re-discovering dependencies or pipeline expectations.***
