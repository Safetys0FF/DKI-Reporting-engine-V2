# HANDSHAKE: POWER → POWER (Request)
**Date**: 2025-10-09  
**From**: agent_1_POWER_CODING  
**To**: agent_1_POWER_CODING  
**Subject**: Warden/ECC Refactor & OCR Orchestration  
**Status**: SUBMITTED

---

## Summary
- Refactor the Warden shell to initialise the ecosystem controller (ECC) and gateway controller via _init_warden helpers while owning CAN address 2-1.
- Rework the ECC so it loads the OCR Flow Engine, tags evidence as it arrives from the locker, and manages section gating plus API callouts without archiving frozen snapshots.
- Ensure every stage continues to communicate over the CAN bus so the UDS monitoring layer remains satisfied.

---

## Tasks Requested
1. Update _init_warden.py to expose init_ecosystem_controller / init_gateway_controller helpers; adjust the Warden wrapper to rely on them and to bootstrap DKIReportBus when no bus is supplied.
2. Refactor ecosystem_controller.py:
   - Import OCR tooling from War Room (ocr_flow_engine), preload engines, and maintain a lightweight persistence pool.
   - Replace frozen snapshot archives with live section state tracking (section_release_flags, completed_sections, revision counts).
   - Implement evidence event handling (evidence.new, evidence.updated) that runs OCR tagging and evaluates release gates in the order 1 → 2 → 3 → 4 → 5 → 7 → 8 → 6.
   - Coordinate API/enrichment callouts and authorise Gateway hand-offs to Mission Debrief only when ECC requirements are met.
3. Wire ECC logging/status updates to reflect the new behaviour and remove obsolete frozen-section references.
4. Extend integration tests / diagnostics to exercise the new gating flow (e.g., mock evidence payload → OCR tagging → section authorisation) while keeping existing tests green.
5. Run UDS compliance checks after wiring is complete to confirm CAN registration, signal usage, and operational health.

---

## Due / Timing
- Refactor and local verification targeted for the next coding session.
- UDS compliance run immediately after tests pass.

---

## Success Criteria
- Warden wrapper initialises ECC/Gateway through the new helpers and owns the parent communicator without duplicating logic.
- ECC class processes evidence events, applies OCR tagging, gates sections in the mandated order, and stops storing frozen snapshots.
- Section authorisation events and API callouts emit the correct CAN signals; UDS reports no new fault codes.
- Updated tests (and any new ECC gating checks) pass.

---

## Notes
- OCR tooling resides under The War Room/SOPs/READ FILES/Build Specs; ensure imports resolve even when running from the Warden package.
- Mission Debrief handles final assembly; ECC only authorises the hand-off once Gateway is clear.

---

## Pre-Confirm Protocol (Required)
- [ ] ACK: Confirm receipt of this request and ETA.
- [ ] READ: Review change summary before coding begins.
- [ ] CONFIRM: Post-confirmation once the plan is accepted and work starts.
