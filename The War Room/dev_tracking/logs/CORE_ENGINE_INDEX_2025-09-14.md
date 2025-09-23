# CORE ENGINE INDEX — 12 Numbered Configuration Files (Read-Only)

Authority Note
- The authoritative manifest for the core engine is maintained at `dev_tracking/archives/CORE_OPERATIONS_HANDBOOK.md`. This index supplements, but does not replace, that manifest. Any discrepancy defers to the archived handbook.

Purpose
- Identify each core engine configuration file, its functional role, and its Python implementation mapping.

Index (by file order)
1) 1. Section CP.txt — Cover Page
   - Section ID: `section_cp`
   - Python: `section_cp_renderer.py: SectionCPRenderer`
   - Role: Cover page composition, case metadata entry point.

2) 2. Section TOC.txt — Table of Contents
   - Section ID: `section_toc`
   - Python: `section_toc_renderer.py: SectionTOCRenderer`
   - Role: Generate TOC labels/structure based on report type.

3) 3. Section 1=gateway controller.txt — Investigation Objectives (Gateway)
   - Section ID: `section_1`
   - Python: `section_1_gateway.py: Section1Renderer`
   - Role: Gateway/ingress and objectives; orchestrates early flow.

4) 4. Section 2.txt — Requirements / Planning
   - Section ID: `section_2`
   - Python: `section_2_renderer.py: Section2Renderer`
   - Role: Pre‑surveillance/case prep and requirements capture.

5) 5. Section 3.txt — Investigation Details
   - Section ID: `section_3`
   - Python: `section_3_renderer.py: Section3Renderer`
   - Role: Core investigative narrative and details.

6) 6. Section 4.txt — Review of Sessions/Details
   - Section ID: `section_4`
   - Python: `section_4_renderer.py: Section4Renderer`
   - Role: Review and analysis of surveillance/details.

7) 7. Section 5.txt — Supporting Documents Review
   - Section ID: `section_5`
   - Python: `section_5_renderer.py: Section5Renderer`
   - Role: Attached documents and audit trail linkage.

8) 8. Section 6 - Billing Summary.txt — Billing Summary
   - Section ID: `section_6`
   - Python: `section_6_renderer.py: Section6BillingRenderer`
   - Role: Billing summary and cost breakdown.

9) 9. Section 7.txt — Conclusion
   - Section ID: `section_7`
   - Python: `section_7_renderer.py: Section7Renderer`
   - Role: Conclusions and findings.

10) 10. Section 8.txt — Evidence Review (Media)
    - Section ID: `section_8`
    - Python: `section_8_renderer.py: Section8Renderer`
    - Role: Media/evidence review; integrates media processing pipeline.

11) 11. Section DP.txt — Disclosure Page
    - Section ID: `section_dp`
    - Python: (no dedicated renderer found) — content routed in pipeline; final assembly consumes approved sections.
    - Role: Disclosures and legal boilerplate.

12) 12. Final Assembly.txt — Final Report Assembly
    - Section ID: `section_fr`
    - Python: `final_assembly.py: FinalAssemblyManager`
    - Role: Aggregate approved sections; generate final deliverables.

Gateway Linkage
- Orchestrator: `gateway_controller.py` maps report types to section order and dispatches each renderer.
- Toolkit: `master_toolkit_engine.py` runs per-section analysis before rendering.
- Media: `media_processing_engine.py` augments Section 8 with analysis results.

Notes
- Known issues addressed: duplicate header block at top of `2. Section TOC.txt` removed. Further standardization (handler naming and duplicate blocks) queued.
- Use this index to align section IDs in configs with Python entrypoints.

Timestamp: 2025-09-14
Author: Core Functions Owner (AI)
