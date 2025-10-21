# HANDSHAKE: agent_1_POWER_CODING ?+' agent_1_POWER_CODING (Request)
**Date**: 2025-10-09  
**From**: agent_1_POWER_CODING  
**To**: agent_1_POWER_CODING  
**Subject**: Enhanced GUI & UDS Integration Follow-Up  
**Status**: SUBMITTED

---

## Summary
Core persistence and UDS wiring are in place, including inline InputPersistence helpers, nav-bar refactor, new unit tests, and improved UDS disk cleanup. Review Command Center/UI/README_HANDOFF.md for full notes, remaining polish items, and the current test matrix.

---

## Tasks Requested
- Polish the home screen into a cleaner landing experience (remove nested frames, align typography).
- Wire the case/evidence overview to live bus signals in _collect_case_overview and _refresh_review_view.
- Highlight the active view in the new nav bar without relying on disabled-state styling.
- Address the missing _stop_dependency_systems hook so UDS shutdown stays graceful.
- Run the GUI locally to validate operator persistence, new-case defaults, and nav UX.

---

## Due / Timing
Next POWER coding session / before the GUI ships to operators.

---

## Success Criteria
- GUI launches with a single header + nav flow and polished home card.
- Case overview reflects live bus data with no TODO placeholders.
- Active tab highlight works regardless of disabled button styles.
- UDS smoke diagnostic completes without falling back to emergency shutdown.
- Manual GUI run confirms persistence and navigation behave as expected.

---

## Notes
- Summary & details: Command Center/UI/README_HANDOFF.md
- Tests already passing: python -m unittest discover -s "Command Center/UI/tests" -p "gui_*test.py", python baseline_system_smoke.py
- Legacy GUI copies marked in Command Center/UI/archives/README.md

---

## Pre-Confirm Protocol (Required)
- [ ] ACK: Receiving agent acknowledges this request and provides ETA
- [ ] READ: Review the change summary at Command Center/UI/README_HANDOFF.md
- [ ] CONFIRM: After reading, post a CONFIRM handshake to accept control
