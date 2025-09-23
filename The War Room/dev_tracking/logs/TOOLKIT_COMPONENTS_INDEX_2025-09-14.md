# TOOLKIT COMPONENTS INDEX (Read-Only)

Purpose
- Summarize the toolkit modules and section renderers used by the engine, including inputs/outputs and typical usage in the unified toolkit dispatch.

Core renderers
- section_cp_renderer.py: SectionCPRenderer — Builds cover preview; consumes case_data, client_profile; emits render_tree + manifest.
- section_toc_renderer.py: SectionTOCRenderer — Generates TOC based on ordered sections; estimates pagination using CHARS_PER_PAGE.
- section_7_renderer.py: Section7Renderer — Conclusion; summarizes sections 1–5 and 8; honors continuity flags; excludes billing.
- section_8_renderer.py: Section8Renderer — Evidence index; filters/chronologizes images/videos; relies on geocoding_util if keys present.
- section_9_renderer.py: Section9Renderer — Certification & Disclaimers; builds certification and agency attestation blocks.

Toolkit modules
- billing_tool_engine.py: BillingTool
  - Inputs: contract_total, prep_cost, subcontractor_rate, subcontractor_hours
  - Methods: calculate() -> sets field_ops_budget, subcontractor_total, company_margin; summary() -> dict
  - Notes: uses fixed hourly_rate and retainer_offset; no I/O side effects; simple arithmetic + notes

- cochran_match_tool.py: verify_identity(subject, candidate)
  - Inputs: subject {full_name, dob, address}, candidate {full_name, dob, address, address_days_overlap, source}
  - Output: dict {status: ACCEPT/REVIEW/REJECT, booleans, reasoning[]}
  - Notes: strict similarity (SequenceMatcher > 0.92), requires 60+ days address overlap, trusted sources set

- metadata_tool_v_5.py: process_zip(zip_path, output_dir)
  - Pipeline: chooses toolchain by file extension; runs simulated tool functions in order; first non-empty metadata wins
  - Output: metadata_report_YYYYMMDD_HHMMSS.json in output_dir
  - Notes: emits md5/sha256 hashes; prints a success line; uses placeholder tool fns (Pillow/piexif/exifread/etc.)

- mileage_tool_v_2.py: audit_mileage()
  - Inputs: JSON files in ./artifacts/mileage; per-entry expected_miles, actual_miles, flags
  - Output: audit_report_YYYYMMDD_HHMMSS.json with PASS/FAIL per entry
  - Policy: ±10% tolerance or ≤0.5 mi absolute diff; requires subcontractor_charge + case_manager_approval when billed_to_client

- northstar_protocol_tool.py: process_assets(assets)
  - Logic: classifies assets by field_time across anchors (PRE-INVESTIGATIVE, PRE-SURVEILLANCE, SURVEILLANCE RETURN)
  - Output: {classified[], deadfile_registry[]}; validate_asset() adds issues for missing timestamps

How they are invoked
- The unified toolkit is triggered via the ‘unified_toolkit_dispatch’ block (see TOOLBOX.txt:1) and by Gateway Controller/tooling.
- Typical inputs: section_id, text_data, report_meta, documents, assets; outputs are stored as section_context.unified_results.
- Section renderers read section_payload {toolkit_results, previous_sections, case_data, api_keys} and return a render_tree.

Integration notes
- Gateway Controller runs toolkit first, then section renderers, emitting 10-6 (toolkit ready) and 10-8 (section completed) signals.
- Section 8 renderer benefits from media_processing_engine outputs if present; geocoding requires API key extraction.
- Section 7 renderer intentionally excludes Section 6 (billing) from its evidentiary summary.

Recommended usage patterns
- Keep tool outputs deterministic and side-effect-light; persist reports via engine, not from tools directly.
- Pass only required inputs in section_payload; avoid embedding large blobs.
- When updating tool behavior, mirror any requirement changes in the 12 core config files and document in dev_tracking.

Timestamp: 2025-09-14
Author: Core Functions Owner (AI)

