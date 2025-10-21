# HANDSHAKE: POWER → NETWORK (Request)
**Date**: 2025-10-08  
**From**: agent_1_POWER_CODING  
**To**: agent_2_NETWORK_CODING  
**Subject**: CAN Fault Relay & Parent Mapping Schema  
**Status**: SUBMITTED

---

## Summary
- Generated can_fault_parent_schema_1759980842.json outlining current vs target parent mappings for CAN fault orchestration.
- Highlights investigative sections (4-1…4-8) retaining direct bus access while routing faults through Gateway (2-2).
- Reassigns report assembly sections (4-CP, 4-TOC, 4-DP) under Mission Debrief Manager (3-1) for fault handling.
- Documents fault relay contract, evidence request flow, and specific implementation tasks.

---

## Tasks Requested
1. Update system_registry.json parents: map 4-1…4-8 → 2-2; map 4-CP / 4-TOC / 4-DP → 3-1.
2. Add Gateway fault relay (gateway.report_child_fault) that enriches payloads and preserves original_target_address + payload['target_subsystem'].
3. Add Mission Debrief fault relay for cover / TOC / disclosure sections in coordination with Librarian/Narrative pipeline.
4. Update section controllers to call the appropriate parent relay instead of issuing raw ault.report frames (retain SOS fallback).
5. Extend 	est_routing_logic.py to simulate a section fault through the relay and verify consolidated outputs.

---

## Due / Timing
- Initial registry + relay implementation requested within next maintenance window.
- Regression update scheduled immediately after relay endpoints are available.

---

## Success Criteria
- system_registry.json reflects the new parent mappings (verified via CommsSystem parent map).
- Gateway/Mission Debrief relays emit faults that preserve child metadata and appear in ault_vault consolidated reports.
- Updated routing regression passes, logging consolidated fault report filenames.
- Evidence request flow remains direct (sections ↔ Evidence Locker) with relay only affecting fault reporting.

---

## Notes
- Sections remain individualized CAN nodes for tooling and evidence traffic.
- Cover/TOC/Disclosure are now explicitly owned by Mission Debrief Manager while Librarian consumes the outputs.
- SOS (ault.sos) direct path stays available; parent must log bypass events.

---

## Pre-Confirm Protocol (Required)
- [ ] ACK: Receiving agent acknowledges this request and provides ETA
- [ ] READ: Review the change summary at $summaryPath
- [ ] CONFIRM: After reading, post a CONFIRM handshake to accept control
