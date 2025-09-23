# HANDSHAKE — 2025-09-15 — POWER → ALL (Fallback Logic Policy)

From Agent: POWER
To Agents: NETWORK, DEESCALATION
Context: Core coding directive — use the fallback logic references as the authoritative guide for behavior and section semantics when coding.

Policy (effective immediately)
- Section 1 determines `report_type` (Investigative, Field/Surveillance, Hybrid); downstream sections MUST NOT override it.
- Fallback default: Field (Field ≡ Surveillance for internal mappings) when ambiguous; Hybrid when both clauses or escalation apply.
- Section semantics per fallback:
  - Section 2: Investigative → “Investigation Requirements”; Field → “Pre‑Surveillance Planning”; Hybrid → “Preliminary Case Review”.
  - Section 3: Field → “Daily Logs”; Investigative/Hybrid → “Investigation/Investigative Details”.
  - Section 4: Investigative → “Review of Details”; Field/Hybrid → “Review of Surveillance Sessions”.
  - Sections 5–FR: as defined; no override of core logic.
- Labels/mappings in controller and TOC must reflect the above.
- All core-config edits must preserve single `logic_switches` and single `callbox_endpoints` per file, correct emitter IDs, and ASCII‑safe logs.

Authoritative references (read‑only)
- Manifest: `dev_tracking/archives/CORE_OPERATIONS_HANDBOOK.md`
- Fallback Logic Index: `dev_tracking/CORE_ENGINE_FALLBACK_INDEX_2025-09-14.md`
- Specific fallbacks (examples):
  - `Section 1 - Investigation Objectives (updated).txt`
  - `Section 1 - Investigation Objectives with switches.txt`
  - `Section 2 - Presurveillance Logic.txt`
  - `section 2 - pres-urveillance.txt`
  - `section 3 - data logs.txt`
  - `Section 3 - Surveillance Reports - Dialy Logs.txt`
  - `Section 4 - Review of Surveillance Sessions.txt`
  - `Section 4 - review of surveillance.txt`
  - `Section 5 - review of documents Logic Overview.txt`
  - `Section 5 - Review of Supporting Docs.txt`
  - `section 6 - BILLING SUMMARY.txt`

Recent alignment (for context)
- gateway_controller: Surveillance `section_3` labeled “Daily Logs”.
- TOC: Investigative/Hybrid use “Investigation Objectives”; Surveillance `section_3` set to “Daily Logs”.
- Core configs de‑duplicated and emitters normalized.

Requests
- NETWORK: Adopt this policy for all integrations and avoid assumptions that conflict with fallback logic; ACK receipt.
- DEESCALATION: Incorporate this policy into risk/regression checks and quality gates; ACK receipt.

Due‑by: 2025-09-16
Status: SENT — Awaiting ACKs

