# PROPOSED CHANGES — 2025-09-14 (Read-Only)

Scope
- Propose mechanical standardization across the 12 core configuration files and add autonomous report-type detection (design only).

References
- Manifest authority: dev_tracking/archives/CORE_OPERATIONS_HANDBOOK.md
- Per-file recs: dev_tracking/CORE_ENGINE_RECOMMENDATIONS_2025-09-14.md
- Auto-detect design: dev_tracking/agent_1_POWER_CODING/AUTO_REPORT_TYPE_DETECTION_PLAN_2025-09-14.md

Phase 1 — Mechanical Standardization (low risk)
- Remove duplicated `gateway_section_control` header blocks (Sections 2–8, DP, FR where present).
- Normalize emitter IDs to `section_<id>_toolkit_signal_emitter` for each file.
- Set emitter payload `origin` and `from` to the hosting section id.
- Fix description copy errors (e.g., Section 4 description saying Section 3).
- Ensure exactly one `logic_switches` and one `callbox_endpoints` block per file.

Phase 2 — Syntax/Format Validation
- Resolve YAML-like anomalies (quotes/colons/indent) flagged in prior error reports.
- Add a lightweight validator to scan the 12 core configs pre-run.

Phase 3 — Integration Alignment
- Cross-check section IDs/labels with gateway_controller.py and fallback files; correct mismatches.
- Spot-check TOC/CP label coherence.

Autonomous Report-Type Detection (design for review)
- Accept `report_type=None/"auto"` in gateway_controller.initialize_case and infer from case_data (contract type, goals, field flags, artifacts). Map alias: Field ≡ Surveillance internally.
- Retain explicit overrides if provided; log rationale and propagate to section payloads.

Rollout Plan
1) Await NETWORK and DEESCALATION ACKs on this proposal.
2) Apply Phase 1 changes with a detailed change log per file.
3) Run syntax validator; iterate fixes.
4) If approved, implement auto-detect in gateway_controller (no behavior change when explicit type provided).

Requested Review
- NETWORK: Confirm Field/Surveillance aliasing has no downstream conflicts; highlight API/transport constraints.
- DEESCALATION: Validate risk profile, propose regression checks for config standardization and auto-detect paths.

Timestamp: 2025-09-14
Author: POWER Agent (Core Functions)

