# HANDSHAKE: POWER → POWER (Request)
**Date:** 2025-10-10  
**From:** POWER  
**To:** POWER  
**Subject:** GUI Controller Refresh & Librarian Delegation  
**Status:** SUBMITTED

---

## Summary
Restore the Central Command GUI’s controller responsibilities while letting Librarian/Evidence Locker own persistence. Current launcher run halts with `AttributeError: 'EnhancedDKIGUI' object has no attribute 'case_session'` and double-instantiates the CANBUS. A focused refactor plus smoke verification is required.

---

## Tasks Requested
1. Reintroduce the GUI workspace scratchpad (`case_session`, `current_case_id`, related string vars) so SectionBusAdapter and evidence flows stop throwing `AttributeError`.
2. Update `_initialize_plugin()` to reuse the live GUIModule bus; guard the legacy fallback for standalone mode.
3. (Optional) Prep a lightweight `CentralPluginAdapter` wrapper that accepts an external bus if deeper evidence/report tooling is still needed.
4. Run launcher smoke (`DKI_ENGINE_LAUNCHER.bat`) to confirm GUI stays open, emits signals, and shuts down cleanly.
5. Log findings in `README_HANDOFF.md` and prepare commit notes once validated.

---

## Due / Timing
Next available coding block (same-day preferred).

---

## Success Criteria
- GUI launches and remains active with no `case_session` or CANBUS duplication errors.
- Heartbeat/log output stabilises (`Bus: Connected`, no emergency shutdown on startup).
- New Case / Report Summary actions complete without uncaught exceptions.
- Updated instructions recorded in `TODO_GUI_CONTROLLER_REFOCUS_2025-10-10.md` and handoff logged.

---

## Notes
- Root cause and to-do list documented in `The War Room\dev_tracking\logs\TODO_GUI_CONTROLLER_REFOCUS_2025-10-10.md`.
- Librarian is expected to retain archives; GUI should operate purely as a controller with minimal temporary state.

---

## Pre-Confirm Checklist
- [ ] ACK by receiving agent (self) with ETA  
- [ ] READ the referenced TODO log  
- [ ] CONFIRM control before starting implementation

