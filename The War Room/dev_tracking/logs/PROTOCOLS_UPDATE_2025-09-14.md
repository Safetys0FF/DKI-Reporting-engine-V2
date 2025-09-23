# PROTOCOLS UPDATE — 2025-09-14 (Read-Only)

Purpose
- Align operational protocols with the authoritative core-engine manifest.

Authority
- Authoritative manifest: `dev_tracking/archives/CORE_OPERATIONS_HANDBOOK.md`.
- The 12 numbered configuration files listed there are the engine manifest and source of truth.

Protocol Changes
- Startup: Always read `dev_tracking/archives/CORE_OPERATIONS_HANDBOOK.md` first to load the manifest and file addresses.
- Scope: Treat the 12 numbered files as the definitive core set for edits and validation.
- Indices: `CORE_ENGINE_INDEX_*.md` and related summaries are supplemental references only; defer to the archived handbook on conflicts.
- Handoffs: Reference the archived handbook path in all DAILY_HANDOFFS and handshake files when describing scope.
- Roles: Roles are fixed; any change requires submitting a root-level request file using `ROLE_CHANGE_REQUEST_TEMPLATE.md`, opening Handshakes to all agents, and awaiting ACKs before the change is effective.
 - Handshakes: All handshake requests and confirmations must be stored exclusively under `dev_tracking/Handshakes/`. Do not place handshake files in agent folders. Agents must review and respond using files in this folder only.

Operational Notes
- Fallback references and toolkit indices remain in use for behavior/structure guidance, but do not redefine the manifest.
- All future recommendations and change records will cite the archived handbook as the manifest authority.

Next Steps
- Realign open recommendations to explicitly reference the archived manifest.
- Continue Phase 1 standardization across the 12 core files upon approval, documenting each change.

Timestamp: 2025-09-14
Author: POWER Agent (Core Functions)
