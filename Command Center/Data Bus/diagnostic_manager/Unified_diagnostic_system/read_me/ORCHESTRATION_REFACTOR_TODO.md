# ORCHESTRATION REFACTOR - TODO LIST
**Date:** 2025-10-20  
**Objective:** Implement clean handshake architecture between main_application.py, CANBUS, DIAG-1, and parent modules

---

## ARCHITECTURE OVERVIEW

**New Flow:**
```
main_application.py (Ringmaster)
    ↓ creates
CANBUS (Network Manager)
    ↓ sends Bus-1 ready
main_application.py
    ↓ sends diag.initialize
DIAG-1 (Compliance & Health)
    ↓ sends diag.ready
main_application.py
    ↓ broadcasts system.initialize
Parent Modules (1, 2, 3, 5)
    ↓ run self-tests
    ↓ report to DIAG-1
DIAG-1
    ↓ compiles fault report
    ↓ sends diag.test_complete (pass/fail)
main_application.py
    ↓ launches GUI if pass
    ↓ primes case work
```

---

## PHASE 1: MAIN APPLICATION REFACTOR

### File: `Command Center/Start Menu/Run Time/main_application.py`

- [x] **1.1** Remove module imports (Warden, Evidence Locker, etc.) - no direct instantiation
- [x] **1.2** Restructure into 4 phases:
  - Phase 1: CANBUS initialization
  - Phase 2: DIAG-1 initialization  
  - Phase 3: Parent module initialization
  - Phase 4: System evaluation
- [x] **1.3** Add signal handlers: `diag.ready`, `diag.test_complete`
- [x] **1.4** Send `diag.initialize` signal to DIAG-1
- [ ] **1.5** Send `system.initialize` broadcast to parent modules
- [ ] **1.6** Add Phase 5: GUI launch (after pass)
- [ ] **1.7** Add Phase 6: Case work priming
- [ ] **1.8** Clean shutdown handlers for graceful UDS/module shutdown

---

## PHASE 2: DIAG-1 (UDS) SIGNAL HANDLERS

### File: `Command Center/Data Bus/diagnostic_manager/Unified_diagnostic_system/__init__.py`

- [x] **2.1** Add `_handle_diag_initialize_signal()` handler
- [x] **2.2** Call `_register_diagnostic_signals()` in `__init__()`
- [x] **2.3** Register `diag.initialize` handler
- [ ] **2.4** Add `system.initialize` listener to relay to CoreSystem
- [ ] **2.5** Remove duplicate/obsolete handlers

### File: `Command Center/Data Bus/diagnostic_manager/Unified_diagnostic_system/core.py`

- [x] **2.6** Replace `system.initialization_complete` with `diag.test_complete`
- [x] **2.7** Compile test results from system_registry
- [x] **2.8** Emit `diag.test_complete` with pass/fail/fault_report
- [ ] **2.9** Add handler for parent module test reports
- [ ] **2.10** Track which parent modules reported (1, 2, 3, 5)
- [ ] **2.11** Wait for all parent reports before emitting diag.test_complete

---

## PHASE 3: PARENT MODULE HANDLERS & CODE RESTRUCTURE

**CRITICAL REQUIREMENT:** All startup/initialize/self-test functions must be at the TOP of each module (lines 1-100), not buried thousands of lines deep.

### File: `Command Center/The Warden/warden_module.py`

- [ ] **3.1** **RESTRUCTURE:** Move all startup functions to TOP of file (lines 1-100)
- [ ] **3.2** **RESTRUCTURE:** Move signal handlers to TOP section (no large gaps)
- [ ] **3.3** Add `system.initialize` signal handler at TOP
- [ ] **3.4** Implement self-test sequence at TOP (startup, rollcall, health check)
- [ ] **3.5** Emit `system.initialization_complete` with results
- [ ] **3.6** Add timeout handling (30s max)
- [ ] **3.7** **AUDIT:** Ensure no functions buried >200 lines deep

### File: `Command Center/Evidence Locker/evidence_locker_module.py`

- [ ] **3.8** **RESTRUCTURE:** Move all startup functions to TOP of file (lines 1-100)
- [ ] **3.9** **RESTRUCTURE:** Move signal handlers to TOP section (no large gaps)
- [ ] **3.10** Add `system.initialize` signal handler at TOP
- [ ] **3.11** Implement self-test sequence at TOP (startup, rollcall, health check)
- [ ] **3.12** Emit `system.initialization_complete` with results
- [ ] **3.13** Add timeout handling (30s max)
- [ ] **3.14** **AUDIT:** Ensure no functions buried >200 lines deep

### File: `Command Center/The Marshall/marshall_module.py`

- [ ] **3.15** **RESTRUCTURE:** Move all startup functions to TOP of file (lines 1-100)
- [ ] **3.16** **RESTRUCTURE:** Move signal handlers to TOP section (no large gaps)
- [ ] **3.17** Add `system.initialize` signal handler at TOP
- [ ] **3.18** Implement self-test sequence at TOP (startup, rollcall, health check)
- [ ] **3.19** Emit `system.initialization_complete` with results
- [ ] **3.20** Add timeout handling (30s max)
- [ ] **3.21** **AUDIT:** Ensure no functions buried >200 lines deep

### File: `Command Center/Mission Debrief/mission_debrief_module.py`

- [ ] **3.22** **RESTRUCTURE:** Move all startup functions to TOP of file (lines 1-100)
- [ ] **3.23** **RESTRUCTURE:** Move signal handlers to TOP section (no large gaps)
- [ ] **3.24** Add `system.initialize` signal handler at TOP
- [ ] **3.25** Implement self-test sequence at TOP (startup, rollcall, health check)
- [ ] **3.26** Emit `system.initialization_complete` with results
- [ ] **3.27** Add timeout handling (30s max)
- [ ] **3.28** **AUDIT:** Ensure no functions buried >200 lines deep

### File: `Command Center/Mission Debrief/mission_debrief_module.py`

- [ ] **3.16** Add signal handler for `system.initialize`
- [ ] **3.17** Implement `_perform_self_test()` method
- [ ] **3.18** Report test results to DIAG-1 via `self_test.report` signal
- [ ] **3.19** Include fault codes if self-test fails
- [ ] **3.20** Test: Mission Debrief receives initialize, runs test, reports back

---

## PHASE 4: DIAG-1 RESULT COLLECTION

### File: `Command Center/Data Bus/diagnostic_manager/Unified_diagnostic_system/core.py`

- [ ] **4.1** Add `_handle_self_test_report()` handler
- [ ] **4.2** Register handler for `self_test.report` signal
- [ ] **4.3** Track received reports in dict: `{address: result}`
- [ ] **4.4** Check if all parents reported (1, 2, 3, 5)
- [ ] **4.5** Compile fault codes from all reports
- [ ] **4.6** Emit `diag.test_complete` when all reports received OR timeout (30s)
- [ ] **4.7** Include pass count, fail count, fault list in signal

---

## PHASE 5: REMOVE REDUNDANT CODE & CONSOLIDATION

### File: `Command Center/Data Bus/diagnostic_manager/Unified_diagnostic_system/core.py`

- [ ] **5.1** Remove `_instantiate_parent_modules()` function (line ~6100) - redundant with new flow
- [ ] **5.2** Remove `_initialize_safe_mode_modules()` function (line ~374) - obsolete with shared bus
- [ ] **5.3** Remove `main()` launcher function (line 77-236) - move to separate launcher.py or keep minimal in core.py
- [ ] **5.4** Remove duplicate `_perform_startup_rollcall()` logic - consolidate with new orchestration
- [ ] **5.5** Remove `_force_system_startup()` - parent modules self-start on signal
- [ ] **5.6** Audit all `_handle_*` functions - ensure no duplicates with comms.py
- [ ] **5.7** Remove orphaned imports and unused helper functions
- [ ] **5.8** Consolidate scattered communication logic into delegation wrappers only
- [ ] **5.9** Remove dual-mode switching code if obsolete (WATCHER vs DIAGNOSTIC modes)
- [ ] **5.10** Clean up `_select_system_addresses()` smoke mode logic

### File: `Command Center/Data Bus/diagnostic_manager/Unified_diagnostic_system/__init__.py`

- [ ] **5.11** Remove `_connect_to_canbus_primary()` method (lines 163-257) - duplicate of `_connect_to_existing_bus()`
- [ ] **5.12** Remove unused signal handler stubs
- [ ] **5.13** Consolidate bus connection logic into single method

### File: `Command Center/Data Bus/diagnostic_manager/Unified_diagnostic_system/comms.py`

- [ ] **5.14** Remove duplicate `transmit_rollcall()` functions (appears twice: line 364 and 849)
- [ ] **5.15** Audit `_handle_*` signal handlers - ensure no logic duplication
- [ ] **5.16** Consolidate signal transmission methods

### File: `Command Center/Data Bus/diagnostic_manager/Unified_diagnostic_system/enforcement.py`

- [ ] **5.17** Audit for communication code that belongs in comms.py
- [ ] **5.18** Remove any bus.emit() calls - delegate to comms module
- [ ] **5.19** Consolidate fault tracking dictionaries (multiple overlapping trackers)

### File: `Command Center/Data Bus/diagnostic_manager/Unified_diagnostic_system/recovery.py`

- [ ] **5.20** Audit for communication code that belongs in comms.py
- [ ] **5.21** Remove any signal handlers - delegate to comms module
- [ ] **5.22** Consolidate repair/restore logic scattered across methods

### File: `Command Center/Start Menu/Run Time/main_application.py`

- [x] **5.23** Remove Warden, Evidence Locker, Evidence Manager imports (lines 16-26)
- [x] **5.24** Remove NarrativeAssembler, MissionDebriefManager imports (lines 28-49)
- [ ] **5.25** Remove `_load_class()` helper function (lines 36-45) - no longer needed
- [x] **5.26** Remove subprocess.Popen code - using in-process UDS now

### File: `Command Center/Data Bus/Bus Core Design/bus_core.py`

- [ ] **5.27** Verify no redundant signal handlers
- [ ] **5.28** Check initialization_sequence logic - ensure clean handoff to modules
- [ ] **5.29** Remove obsolete comments about "subprocess" UDS (line 80)

---

## PHASE 6: GUI LAUNCH INTEGRATION

### File: `Command Center/Start Menu/Run Time/main_application.py`

- [ ] **6.1** Add Phase 5: GUI Launch after system pass
- [ ] **6.2** Import GUI entry point
- [ ] **6.3** Launch GUI in thread with shared bus reference
- [ ] **6.4** Add signal handler for GUI ready confirmation

---

## PHASE 7: TESTING & VALIDATION

- [ ] **7.1** Test: main_application → CANBUS → DIAG-1 handshake
- [ ] **7.2** Test: DIAG-1 → Parent modules broadcast
- [ ] **7.3** Test: Parent modules → DIAG-1 reporting
- [ ] **7.4** Test: DIAG-1 → main_application results
- [ ] **7.5** Test: Full startup with all phases (no failures)
- [ ] **7.6** Test: Startup with intentional fault (verify failure path)
- [ ] **7.7** Test: GUI launches after successful initialization
- [ ] **7.8** Verify no duplicate bus instances created
- [ ] **7.9** Verify signal flow on correct channels (CANBUS vs LINBUS)
- [ ] **7.10** Performance test: Startup time < 45 seconds

---

## PHASE 8: DOCUMENTATION

- [ ] **8.1** Generate change report in systems_amendments
- [ ] **8.2** Document new signal protocol: diag.initialize, diag.ready, diag.test_complete, system.initialize, self_test.report
- [ ] **8.3** Update system_registry.json with new signal definitions
- [ ] **8.4** Update MASTER_DIAGNOSTIC_PROTOCOL with handshake flow
- [ ] **8.5** Create startup sequence diagram

---

## FILES TO MODIFY

1. `Command Center/Start Menu/Run Time/main_application.py` (CRITICAL)
2. `Command Center/Data Bus/diagnostic_manager/Unified_diagnostic_system/__init__.py` (CRITICAL)
3. `Command Center/Data Bus/diagnostic_manager/Unified_diagnostic_system/core.py` (CRITICAL)
4. `The Warden/warden_module.py` (REQUIRED)
5. `Evidence Locker/evidence_locker_module.py` (REQUIRED)
6. `The Marshall/marshall_module.py` (REQUIRED)
7. `Command Center/Mission Debrief/mission_debrief_module.py` (REQUIRED)
8. `Command Center/UI/gui_main_application.py` (OPTIONAL - Phase 6)

---

## ESTIMATED EFFORT

- Phase 1: 100% complete (main_application restructured)
- Phase 2: 60% complete (DIAG-1 handlers added, result collection incomplete)
- Phase 3: 0% complete (parent module handlers)
- Phase 4: 0% complete (result collection logic)
- Phase 5: 0% complete (29 redundancy removal tasks)
- Phase 6: 0% complete (GUI integration)
- Phase 7: 0% complete (testing)
- Phase 8: 0% complete (documentation)

**Total Tasks:** 75 tasks across 8 files
**Completed:** 8 tasks (11%)
**Remaining:** 67 tasks (89%)

---

## CRITICAL DEPENDENCIES

- Parent modules MUST have `_perform_self_test()` methods
- DIAG-1 MUST track all 4 parent reports before emitting diag.test_complete
- Timeout handling: If parent doesn't report within 30s, count as failure
- Fault code aggregation: Collect ALL fault codes from failed modules

---

## ROLLBACK PLAN

If refactor fails:
1. Archive current core.py, __init__.py, main_application.py to backups/
2. Restore from last working state
3. Document failure points in systems_amendments

