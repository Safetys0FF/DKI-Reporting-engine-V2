# SMOKE TEST PLAN — 2025-09-15 (Read-Only)

Objective
- Validate clean startup and basic section generation after startup/logging fix and core-config standardization.

Prereqs
- Packages installed: python-docx, openpyxl, opencv-python, reportlab
- No hardcoded path issues; repository initialized

Steps
1) Launch
   - Run: `python run_dki_engine.py`
   - Expect: dependency summary, no Unicode errors, config validation passes
2) Initialize minimal case (manual or harness layer)
   - report_type: Investigative (explicit for smoke)
   - Ensure case_data has minimal fields for CP/TOC/Section 1
3) Generate CP, TOC, Section 1
   - Confirm toolkit run (10-6) and section complete (10-8) signals logged
   - Verify Section 1 renders with placeholders instead of crashing
4) Optional: Section 3 render (investigation details)
   - Confirm no emitter/payload routing errors

Pass Criteria
- Launcher runs without Unicode or syntax errors
- Dependency check OK or clear optional notes
- CP/TOC/Section 1 render models generated; logs show 10-6 and 10-8

Notes
- Known outstanding: sanitize a misencoded log string in `2. Section TOC.txt` (does not block smoke)

