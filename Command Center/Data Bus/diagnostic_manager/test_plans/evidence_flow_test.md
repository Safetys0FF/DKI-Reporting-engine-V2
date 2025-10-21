# Evidence Flow Test — End-to-End Autonomous Progression
**Test ID:** FLOW-001  
**Date Created:** 2025-10-10  
**Agent:** DEESCALATION (agent_3_DEESCALATION_CODING)  
**Purpose:** Validate autonomous evidence progression through core pipeline

---

## OBJECTIVE

Prove that evidence can flow **autonomously and reliably** from intake through final report assembly without manual intervention. Test system's ability to self-orchestrate data movement across CANBUS addresses.

---

## TEST SCOPE

### **Systems Under Test**
- **Evidence Locker (1)** — Evidence intake, classification, manifest creation
- **Warden (2-3)** — Gateway Controller routing and orchestration
- **Marshall (3-1)** — Evidence management and processing handoff
- **Mission Debrief (5)** — Final report assembly

### **Out of Scope (Phase 2)**
- Section frameworks (4-x) — Will be added after core flow validated
- GUI integration (7-x) — Not tested in this phase
- API external systems — Not tested in this phase

---

## TEST ARCHITECTURE

### **Flow Path**
```
Evidence File (test_sample.pdf)
    ↓
[1] Evidence Locker
    └→ Intake processor
    └→ Classifier
    └→ Manifest builder
    └→ Emit: evidence.classified
    ↓
[2-3] Gateway Controller (Warden)
    └→ Receive: evidence.classified
    └→ Route to Marshall
    └→ Emit: evidence.route.to_marshall
    ↓
[3-1] Marshall (Evidence Manager)
    └→ Receive: evidence.route.to_marshall
    └→ Process evidence
    └→ Emit: evidence.ready_for_debrief
    ↓
[5] Mission Debrief Module
    └→ Receive: evidence.ready_for_debrief
    └→ Assemble report artifact
    └→ Emit: mission.report.assembled
```

### **Signal Trace Points**
| Address | System | Signal Emitted | Expected Payload |
|---------|--------|----------------|------------------|
| 1 | Evidence Locker | `evidence.classified` | `{case_id, evidence_id, classification, metadata}` |
| 2-3 | Gateway Controller | `evidence.route.to_marshall` | `{case_id, evidence_id, route_target: "3-1"}` |
| 3-1 | Marshall | `evidence.ready_for_debrief` | `{case_id, evidence_id, processed: true}` |
| 5 | Mission Debrief | `mission.report.assembled` | `{case_id, report_id, status: "complete"}` |

---

## TEST EXECUTION

### **Prerequisites**
1. UDS running (Unified Diagnostic System active)
2. CANBUS operational (Bus-1 responsive)
3. All test systems registered in `system_registry.json`
4. Test evidence file available: `test_sample.pdf`

### **Execution Steps**
1. **Initialize Test Environment**
   - Start CANBUS listener
   - Initialize signal tracer
   - Clear previous test artifacts

2. **Inject Test Evidence**
   - Load `test_sample.pdf` into Evidence Locker intake
   - Trigger classification workflow
   - Record timestamp: T0

3. **Monitor Signal Propagation**
   - Listen on CANBUS for all test signals
   - Log signal payload at each address
   - Record timing between hops

4. **Validate Autonomous Progression**
   - Confirm each system emits expected signal
   - Verify payload integrity (no data loss)
   - Check progression timing (no stalls)

5. **Generate Flow Report**
   - Output trace log with timestamps
   - Calculate total flow time (T0 → mission.report.assembled)
   - Report pass/fail status

### **Success Criteria**
✅ **PASS CONDITIONS:**
- Evidence classified at address 1 (signal emitted)
- Gateway routes evidence to Marshall (signal emitted)
- Marshall processes and forwards to Mission Debrief (signal emitted)
- Mission Debrief assembles report artifact (signal emitted)
- **UDS detects zero faults during flow**
- Total flow time < 30 seconds
- Payload data intact at each hop

❌ **FAIL CONDITIONS:**
- Any signal not emitted
- UDS fault code raised
- Flow stalls (timeout > 30 seconds between hops)
- Data corruption (payload mismatch)
- System requires manual intervention

---

## VALIDATION METHOD

### **UDS Observation Protocol**
**Per memory [[9730609]]:**
> "Repair process: save broken code, write repair into system folder, restart/trigger system, UDS observes. If NO fault code is emitted, repair succeeded. If fault code appears, repair failed - try again. The absence of a fault IS the pass condition."

**Applied to Flow Test:**
- Run test with UDS active
- Monitor for fault codes during flow
- **Absence of fault = autonomous progression successful**
- Any fault = flow broken, investigate address where fault emitted

### **Signal Integrity Check**
- Compare payload at each hop
- Verify `case_id` and `evidence_id` remain consistent
- Check for data loss or corruption

### **Timing Analysis**
- Measure time between signal emissions
- Identify bottlenecks (>5 second gaps)
- Validate autonomous progression (no human wait states)

---

## TEST DATA

### **Sample Evidence File**
**Filename:** `test_sample.pdf`  
**Type:** PDF document  
**Size:** ~50KB  
**Content:** Simple text document with known content  
**Expected Classification:** Document type, text-based, no special processing

---

## EXPECTED RESULTS

### **Trace Log Output**
```
[FLOW TEST] Starting evidence flow test...
[FLOW TEST] Test case ID: TEST-CASE-001
[FLOW TEST] Evidence file: test_sample.pdf

[T+0.000s] [1] Evidence Locker: Evidence intake started
[T+0.250s] [1] Evidence Locker: Classification complete
[T+0.260s] [1] SIGNAL EMITTED: evidence.classified
[T+0.270s] [2-3] Gateway Controller: Signal received evidence.classified
[T+0.280s] [2-3] Gateway Controller: Routing to Marshall
[T+0.290s] [2-3] SIGNAL EMITTED: evidence.route.to_marshall
[T+0.300s] [3-1] Marshall: Signal received evidence.route.to_marshall
[T+0.450s] [3-1] Marshall: Evidence processing complete
[T+0.460s] [3-1] SIGNAL EMITTED: evidence.ready_for_debrief
[T+0.470s] [5] Mission Debrief: Signal received evidence.ready_for_debrief
[T+1.200s] [5] Mission Debrief: Report assembly complete
[T+1.210s] [5] SIGNAL EMITTED: mission.report.assembled

[FLOW TEST] ✅ AUTONOMOUS PROGRESSION SUCCESSFUL
[FLOW TEST] Total flow time: 1.21 seconds
[FLOW TEST] Signals emitted: 4/4
[FLOW TEST] UDS faults detected: 0
[FLOW TEST] Status: PASS
```

---

## FAILURE SCENARIOS

### **Scenario 1: Evidence Locker Stall**
**Symptom:** `evidence.classified` signal never emitted  
**Diagnosis:** Check Evidence Locker logs, verify intake processor operational  
**UDS Expected:** Fault code 1-XX emitted

### **Scenario 2: Gateway Routing Failure**
**Symptom:** `evidence.route.to_marshall` not emitted  
**Diagnosis:** Check Gateway routing table, verify Marshall registered  
**UDS Expected:** Fault code 2-3-XX emitted

### **Scenario 3: Marshall Processing Failure**
**Symptom:** `evidence.ready_for_debrief` not emitted  
**Diagnosis:** Check Marshall evidence manager, verify processing pipeline  
**UDS Expected:** Fault code 3-1-XX emitted

### **Scenario 4: Mission Debrief Assembly Failure**
**Symptom:** `mission.report.assembled` not emitted  
**Diagnosis:** Check Mission Debrief module, verify component initialization  
**UDS Expected:** Fault code 5-XX emitted

---

## EXECUTION COMMAND

```powershell
# From diagnostic_manager directory
python test_plans\run_evidence_flow_test.py

# With verbose logging
python test_plans\run_evidence_flow_test.py --verbose

# With custom test file
python test_plans\run_evidence_flow_test.py --evidence-file path\to\test.pdf
```

---

## POST-TEST ANALYSIS

### **Metrics to Collect**
- Total flow time (T0 → final signal)
- Time per hop (address-to-address latency)
- Signal payload size at each stage
- UDS fault count (target: 0)
- System resource usage during test

### **Success Indicators**
- **Reliability:** Test passes 10/10 consecutive runs
- **Speed:** Total flow time consistent (±10% variance)
- **Autonomy:** Zero manual interventions required
- **Fault-Free:** UDS reports clean (0 faults)

---

## NEXT PHASE (After Core Flow Validated)

### **Phase 2: Add Section Processing**
- Insert Section 4-x frameworks into flow
- Test path: 1 → 2-3 → **4-1** → 3-1 → 5
- Validate section framework execution
- Measure impact on total flow time

### **Phase 3: Multi-Evidence Test**
- Load multiple evidence files simultaneously
- Test parallel processing capability
- Validate CANBUS doesn't bottleneck
- Measure throughput (evidence per second)

### **Phase 4: Stress Test**
- Load 50+ evidence files
- Measure system degradation
- Identify breaking points
- Validate fault recovery

---

## COMPLIANCE

**Edit-in-Place Protocol:** ✅ No new system files created, only test assets  
**UDS Validation:** ✅ Test uses UDS observation as pass/fail criteria  
**CANBUS Address Alignment:** ✅ Uses post-refactor addresses (1, 2-3, 3-1, 5)  
**Registry Congruency:** ✅ All test addresses match system_registry.json

---

## TEST STATUS

**Status:** READY FOR EXECUTION  
**Dependencies:** All systems operational, test runner script pending  
**Execution Time:** Estimated 5-10 minutes (including setup)  
**Output Location:** `test_plans/flow_test_results/`

---

**END OF TEST PLAN**


