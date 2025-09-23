# CORE ENGINE RECOMMENDATIONS — 12 Numbered Files (Read-Only)

Scope
- This document lists proposed, surgical fixes to the 12 core engine configuration files only.
- No changes applied yet; awaiting your approval to implement.

Goals
- Remove duplicated header blocks within the same file.
- Fix section_id/labels/emitters to match each file’s section.
- Standardize emitter block names and payload origin/from.
- Correct obvious copy/paste description errors.

Conventions
- Emitter block name: `section_<id>_toolkit_signal_emitter`
- Payload fields: `origin: "section_<id>"` and `from: "section_<id>"`

Per-file recommendations
1) 1. Section CP.txt (section_cp)
- Rename emitter id to `section_cp_toolkit_signal_emitter`.
- In emitter payload, set `origin` and `from` to `section_cp`.

2) 2. Section TOC.txt (section_toc)
- Already fixed: removed duplicated top header block (gateway_section_control) in prior pass.
- Verify no other duplicate top-level blocks.

3) 3. Section 1=gateway controller.txt (section_1)
- Fix stray leading space before `action:` under the toolkit dispatch area.
- Ensure all toolkit/apply blocks are properly indented.
- Keep `section_sequence` as-is (assumed by gateway_controller), just correct formatting.

4) 4. Section 2.txt (section_2)
- Remove duplicated top header block (second repeated `Gateway interface for Section 2 ...`).
- Keep callbox_endpoints single (already single).

5) 5. Section 3.txt (section_3)
- Remove duplicated top header block.
- Correct `logic_switches` labels to reflect Section 3 intent (Investigation Details) instead of Section 2 variants.
- Rename emitter id to `section_3_toolkit_signal_emitter` and set payload `origin/from: section_3`.

6) 6. Section 4.txt (section_4)
- Fix description to "Gateway interface for Section 4" (currently says Section 3).
- Remove duplicated top header block.
- Rename emitter id to `section_4_toolkit_signal_emitter` and set payload `origin/from: section_4`.

7) 7. Section 5.txt (section_5)
- Remove duplicated top header block.
- Rename emitter id to `section_5_toolkit_signal_emitter` and set payload `origin/from: section_5`.

8) 8. Section 6 - Billing Summary.txt (section_6)
- Remove duplicated top header block.
- Emitter id and payload appear consistent; keep as-is after cleanup.

9) 9. Section 7.txt (section_7)
- Remove duplicated top header block.
- Rename emitter id to `section_7_toolkit_signal_emitter` (currently uses `section_3_...`).
- Payload fields already reference `section_7`; keep.

10) 10. Section 8.txt (section_8)
- Remove duplicated top header block.
- Rename emitter id to `section_8_toolkit_signal_emitter` (currently `section_3_...`).
- Payload fields reference `section_8`; keep.

11) 11. Section DP.txt (section_dp)
- Remove duplicated top header block.
- Emitter id/payload already aligned to `section_dp`; keep.

12) 12. Final Assembly.txt (section_fr)
- Remove duplicated top header block.
- Verify there are no repeated `logic_switches` blocks inside this file; keep only one logical set if duplicated.
- Ensure emitter id is `section_fr_toolkit_signal_emitter` and payload uses `section_fr`.

Cross-cutting
- Keep exactly one `callbox_endpoints` and one `logic_switches` block per file (no intra-file duplication).
- Do not change endpoint names (`section_X_response_handler`); only standardize casing if mixed.

Validation plan (post-approval)
- Parse pass (basic): ensure no duplicated top-level keys and consistent indent spacing.
- Cross-check: section_id aligns with emitter id and payload.
- Gateway alignment: spot-check against `gateway_controller.py` report type labels and ordering.

Status
- Waiting for approval to implement these low-risk, mechanical fixes across all 12 files.

Timestamp: 2025-09-14
Author: Core Functions Owner (AI)

