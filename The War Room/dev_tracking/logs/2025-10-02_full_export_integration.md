# Central Command Export Pipeline Integration — 2025-10-02

## Overview
- Evidence Locker common pool broadcasts remain the upstream source for section data; the new caches and export pipeline rely on those pool emissions (no pool contract changes were required).
- Wired Librarian, Mission Debrief, and the bus together so GUI-driven exports produce narrative-rich PDF/DOCX/TXT reports.
- Captured cover/TOC/disclosure artifacts from CAN signals and propagate them into final assemblies.
- Upgraded GUI workflow (Enhanced Functional GUI + central plugin) to surface the new report builder and pass case context through export routines.

## Key Changes by Component
- **Command Center/Mission Debrief/The Librarian/narrative_assembler.py**
  - Added section_artifacts cache and get_artifact_payload() helper so CP/TOC/DP bus payloads persist for downstream use.
  - Cleaned ECC log noise, ensured 
arrative.assembled emissions include draft, status, timestamps, and auto-narrative support.
  - Narrative requests now funnel through _assemble_and_emit() to keep case metadata / summaries synchronized.
- **Command Center/Data Bus/Bus Core Design/bus_core.py**
  - Registered native 
arrative.assembled handler that merges draft text, summary, auto-narrative, and timing into section_data.
  - Introduced get_section_data() accessor so Mission Debrief (and dashboards) can fetch cached section payloads.
- **Command Center/Mission Debrief/Debrief/README/mission_debrief_manager.py**
  - Accepted a librarian reference, added rtifact_updates, and subscribed to mission_debrief.section.draft / mission_debrief.artifact.updated signals for local caching.
  - New helpers (_render_section_content, uild_section_payloads, _apply_bus_artifacts) aggregate Librarian + bus payloads, build readable content, and emit refreshed artifact events.
  - process_complete_report() now default-populates 
eport_data, applies CAN artifacts, records an rtifacts_synchronized step, and continues with export logic.
- **Command Center/UI/central_plugin.py** (mirrored to Enhanced GUI & runtime copies)
  - Added uild_complete_report_payload() to assemble case narratives using Mission Debrief caches.
  - generate_full_report() routes through the new builder; export_report() now supports TXT/PDF/DOCX, calling process_complete_report() when PDF/DOCX is requested and raising on ECC-denied runs.
- **Command Center/UI/enhanced_functional_gui.py**
  - Report preview leverages generate_full_report(case_id=active_case_id) for CAN-backed text.
  - Export dialog offers PDF/DOCX/TXT; delegates format + case details to central_plugin.export_report().
  - Minor cleanup (summary split regex); existing quick document scan button now normalizes summary output (unchanged functionality otherwise).

## Signals & Data Flow
- Registered listeners for mission_debrief.section.draft and mission_debrief.artifact.updated (Mission Debrief caches these without re-emitting duplicates).
- 
arrative.assembled now updates both the bus (section_data) and Mission Debrief caches, enabling GUI review + export to consume the same payloads.
- Artifact updates emit mission_debrief.artifact.updated with structured payload + metadata so future consumers can subscribe without polling.

## Validation
- python -m compileall on:
  - Command Center/Mission Debrief/Debrief/README/mission_debrief_manager.py
  - Command Center/Mission Debrief/The Librarian/narrative_assembler.py
  - Command Center/UI/central_plugin.py (synced copies in Enhanced GUI + runtime)
  - Command Center/UI/enhanced_functional_gui.py
- Ad-hoc harness (__exercise_artifacts.py, removed) pushed CAN section.data.updated for CP/TOC/DP + section narratives:
  - Verified uild_section_payloads() returns section summaries with narrative text.
  - TXT export succeeded via central_plugin.export_report(..., export_format='TXT').
- PDF export attempt raised RuntimeError('ECC permission denied for report processing') because Mission Debrief still requires a live ECC approval path. Production export must run with Warden/ECC active or introduce a non-ECC fallback.

## Operational Notes
- GUI export now drives Mission Debrief’s process_complete_report() pipeline. Ensure ECC/warden stack is up before attempting PDF/DOCX.
- mission_debrief.artifact.updated currently has no subscribers; expect INFO logs until downstream listeners are implemented.
- TXT export uses locally rendered section text; PDF/DOCX rely on the War Room report generator. Confirm dependencies (reportlab, docx) remain installed on operator machines.
- Command Center/UI/final_reports/ may contain locally generated TXT exports from smoke tests—clean up if not needed.

## Follow-up / Future Work
1. Provide a headless export path when ECC is unavailable (optional bypass or mocked approval for local testing).
2. Hook GUI status panel or notifications to mission_debrief.artifact.updated so analysts can review artifact refresh events in real time.
3. Consider persisting uild_section_payloads() output per case to avoid recomputation on large investigations.

---
Generated automatically by Codex agent on 2025-10-02.
