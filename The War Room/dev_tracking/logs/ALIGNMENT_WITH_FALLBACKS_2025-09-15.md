# ALIGNMENT WITH FALLBACK LOGIC — 2025-09-15 (Read-Only)

Summary
- Brought core configuration labels and mappings into line with the fallback logic references and gateway_controller.

Changes
- gateway_controller.py
  - Surveillance: `section_3` label set to "Daily Logs" (per surveillance/daily logs guidance).
- 2. Section TOC.txt
  - Investigative/Hybrid: `section_1` → "Investigation Objectives" (plural).
  - Surveillance: `section_3` → "Daily Logs".
- 5. Section 3.txt
  - Confirmed investigative vs field semantics in logic block. Labels now reflected via TOC and controller.

Validation
- Ran core_config_validator.py: 0 files with duplicate blocks or emitter mismatches.
- normalize_core_configs.py updated remaining files with duplicated `logic_switches`/`callbox_endpoints`.

Fallback alignment (key points enforced)
- Section 1 controls `report_type` (sole authority). Downstream uses it; does not override.
- Section 2 labels: Requirements (Investigative) / Pre‑Surveillance Planning (Field) / Preliminary Case Review (Hybrid).
- Section 3 labels & semantics: "Daily Logs" for Field/Surveillance; "Investigation/Investigative Details" for Investigative/Hybrid.
- Section 4 labels: Review of Details (Investigative) vs Review of Surveillance Sessions (Field/Hybrid).

Next
- Proceed to smoke test when deps are installed (CP/TOC + Section 1) to observe clean startup and 10‑6/10‑8 signaling.
- Continue sanitizing any stray misencoded strings found during runtime logs.

Timestamp: 2025-09-15
Author: POWER Agent (Core Functions)

