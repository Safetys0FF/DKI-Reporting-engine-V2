# HANDSHAKE: POWER → ALL AGENTS (Mandatory Handoff Protocol)
**Date**: 2025-09-15  
**From**: POWER Agent 1 — Core Engine  
**To**: ALL AGENTS (NETWORK, DEESCALATION)  
**Status**: POLICY UPDATE — EFFECTIVE IMMEDIATELY

---

## Summary
Standardizes handoff flow across agents and makes the Change Summary + Pre‑Confirm Protocol mandatory for every handoff.

---

## Mandatory Requirements (All Agents)
- Change Summary file must exist in the originating agent’s root folder and include:
  - What changed/updated/edited
  - How it changed (approach, rationale)
  - Where it changed (file paths)
- Pre‑Confirm Protocol steps must be followed before any control transfer is confirmed:
  1) ACK the handshake request with ETA
  2) READ the linked Change Summary in the request
  3) CONFIRM the handshake (accept control) after reading

---

## File Locations & Naming
- POWER: `dev_tracking/agent_1_POWER_CODING/CHANGE_SUMMARY_YYYY-MM-DD.md`
- NETWORK: `dev_tracking/agent_2_NETWORK_CODING/CHANGE_SUMMARY_YYYY-MM-DD.md`
- DEESCALATION: `dev_tracking/agent_3_DEESCALATION_CODING/CHANGE_SUMMARY_YYYY-MM-DD.md`

Reference example: `dev_tracking/agent_1_POWER_CODING/CHANGE_SUMMARY_2025-09-15.md`

---

## Templates & CLI
- Templates (already in repo):
  - `dev_tracking/templates/handshakes/request.md` (includes Pre‑Confirm Protocol)
  - `dev_tracking/templates/handshakes/ack.md` (ACK checklist includes reading summary)
  - `dev_tracking/templates/handshakes/confirm.md` (CONFIRM checklist includes summary reviewed)
  - `dev_tracking/templates/session_log.md` (optional session summary)
- CLI: `python dev_tracking/handshake_cli.py`
  - Request requires `--summary-path` and auto‑adds Pre‑Confirm Protocol to the request file.

---

## Compliance
- Effective immediately for all new handoffs.
- Requests without a `--summary-path` are invalid; receiving agents should not CONFIRM.
- Use the CLI and templates to ensure consistent formatting and auto‑linking in the daily handoffs file.

---

## Next Steps (Each Agent)
- Create or update today’s Change Summary in your root folder before sending or accepting a handoff.
- When issuing a handoff request, include the summary path via CLI `--summary-path`.
- When receiving a handoff request, follow the three Pre‑Confirm steps.

**Status**: POLICY POSTED — ACK required from NETWORK and DEESCALATION.

