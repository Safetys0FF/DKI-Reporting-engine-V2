# Section 2 – Development Strategy & Runbook

## Mission Profile
- **Scope:** Pre-surveillance planning, subject dossiers, POI mapping, and operational briefings.
- **Primary Outputs:** Structured payload for `section_2_planning` plus geo/media artifacts consumed by Marshall, the Librarian, and Mission Debrief.
- **Signals:** publishes `section_2_planning.completed`, listens for `section.needs` categories `["geo"]`, relays faults via `section.fault.4-2`, mayday on `section.mayday.4-2`.

## Planned Dependency Map
| Artifact / Engine | Action Item | Notes |
| --- | --- | --- |
| EvidenceManager (Marshall) | ✅ reuse `_init_evidence_manager.py` pattern | Required for locker handoffs. |
| OCR stack (documents & imagery) | ✅ enforce Unstructured → Tesseract → EasyOCR cascade | Mirrors Section 1 baseline. |
| Geo enrichment toolkit | ⏳ create `_init_geo_context.py` | Needs GIS lookups, coordinate normalization. |
| Map/raster analyzers | ⏳ integrate OpenCV/PIL helpers for image overlays | Pre-work before route recommendations. |
| Subject analytics | ⏳ hard-import behaviour models (habits, POI clustering) | Source logic lives under `Tool kit`. |
| Narrative renderer | ⏳ author `_init_section2_renderer.py` | Generate planning statement/perimeter summary. |
| Media decoding (video/image EXIF) | ⏳ add metadata + visual tagging adapters | Feeds narrative + Section 8 cross-links. |

> *All new tooling must ship as `_init_<dependency>.py` modules so the section baseline test fails fast when a dependency is missing.*

## Lifecycle Expectations
1. `run_baseline_initialization()` – instantiate communicator + dependencies, log status to Marshall/UDS.
2. `enter_rest_state()` / `resume_from_rest()` – allow Warden to sequence sections while preserving state.
3. `soft_shutdown()` – release GIS/vision resources cleanly and report completion via `section.shutdown`.
4. Fault pathway identical to Section 1 (structured `emit_fault`, fall back to `emit_mayday` on relay failure).

## Development Workflow
1. **Refactor Framework**
   - Move logic from the legacy monolithic `section_2_framework.py` into the shared lifecycle base.
   - Replace inline tool imports with `_init_*.py` modules listed above.
2. **Implement Pipelines**
   - Build stage functions for acquisition, geo extraction, narrative planning.
   - Ensure OCR results + geo context bubble into the payload (`map_assets`, `subject_routes`, `ocr_results`).
3. **Testing**
   - Add targeted unit tests under `Analyst 2/Tests` (baseline init, geo planner, OCR fallback).
   - Later: create integration smoke covering rest/sleep cycles and Marshall orchestration.
4. **Documentation**
   - Update this strategy as new tools land; leave breadcrumbs in `dev_tracking` for dependency updates.

## Backlog & Coordination
- Source or author geo-context logic (likely under `Tool kit` or War Room analytics).
- Identify media/vision engines required for subject tracking (OpenCV, YOLO, etc.) and wrap in `_init_` adapters.
- Align with Section 8 to share media metadata so planning + evidence catalogue stay synchronized.
- Add real test fixtures (PDF briefings, map snapshots) to validate OCR + geo pipelines.

Use this document to keep cross-agent work aligned while the section migrates to the new lifecycle + dependency structure.***
