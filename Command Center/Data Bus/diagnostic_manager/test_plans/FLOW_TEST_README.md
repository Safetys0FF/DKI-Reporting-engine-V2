# Evidence Flow Test - Execution Guide

## Overview

End-to-end autonomous progression test that validates evidence flow from Evidence Locker through Mission Debrief without manual intervention.

**Test Flow:** Evidence Locker (1) → Warden Gateway (2-3) → Marshall (3-1) → Mission Debrief (5)

---

## Quick Start

### From PowerShell (Recommended)

```powershell
# Navigate to test_plans directory
cd "F:\The Central Command\Command Center\Data Bus\diagnostic_manager\test_plans"

# Run the test
python run_evidence_flow_test.py
```

### With Options

```powershell
# Verbose output
python run_evidence_flow_test.py --verbose

# Custom evidence file
python run_evidence_flow_test.py --evidence-file path\to\your_test.pdf
```

---

## Files Included

| File | Purpose |
|------|---------|
| `evidence_flow_test.md` | Complete test plan documentation |
| `run_evidence_flow_test.py` | Executable test runner script |
| `test_sample.pdf` | Sample evidence file for testing |
| `FLOW_TEST_README.md` | This file - execution instructions |
| `flow_test_results/` | Test results directory (auto-created) |

---

## Expected Output

```
======================================================================
EVIDENCE FLOW TEST - AUTONOMOUS PROGRESSION VALIDATION
======================================================================

[T+0.000s] [FLOW TEST] Test case ID: TEST-CASE-1728560420
[T+0.000s] [FLOW TEST] Evidence ID: TEST-EVIDENCE-1728560420

[T+0.150s] [SYSTEM] Initializing Unified Diagnostic System...
[T+0.280s] [SYSTEM] ✅ CANBUS operational - 64 systems registered
[T+0.290s] [SYSTEM] Verifying test systems registered...
[T+0.291s] [SYSTEM]   ✅ 1: Evidence Locker
[T+0.292s] [SYSTEM]   ✅ 2-3: Gateway Controller
[T+0.293s] [SYSTEM]   ✅ 3-1: Marshall Module
[T+0.294s] [SYSTEM]   ✅ 5: Mission Debrief Module

[T+0.300s] [FLOW TEST] Evidence file: test_sample.pdf

[T+0.300s] [1] Evidence intake started
[T+0.550s] [1] Classification in progress...
[T+0.800s] [1] Classification complete
[T+0.810s] [1] EMITTED: evidence.classified
[T+0.820s] [2-3] RECEIVED: evidence.classified
[T+0.830s] [2-3] Routing to Marshall...
[T+0.840s] [2-3] EMITTED: evidence.route.to_marshall
[T+0.850s] [3-1] RECEIVED: evidence.route.to_marshall
[T+1.000s] [3-1] Evidence processing in progress...
[T+1.150s] [3-1] Evidence processing complete
[T+1.160s] [3-1] EMITTED: evidence.ready_for_debrief
[T+1.170s] [5] RECEIVED: evidence.ready_for_debrief
[T+1.870s] [5] Report assembly in progress...
[T+1.900s] [5] Report assembly complete
[T+1.910s] [5] EMITTED: mission.report.assembled

[T+1.920s] [UDS] Checking for faults...
[T+1.921s] [UDS] ✅ No faults detected

======================================================================
FLOW TEST RESULTS
======================================================================

✅ AUTONOMOUS PROGRESSION SUCCESSFUL

Total flow time: 1.92 seconds
Signals emitted: 4/4
UDS faults detected: 0

Status: PASS

======================================================================
```

---

## Success Criteria

✅ **Test Passes If:**
- All 4 signals emitted successfully
- UDS reports zero faults
- Total flow time under 30 seconds
- All test systems respond correctly

❌ **Test Fails If:**
- Any signal missing
- UDS fault detected
- System timeout (>30s between hops)
- Manual intervention required

---

## Troubleshooting

### "CANBUS not available"
**Solution:** 
1. Verify UDS is running: `python __init__.py`
2. Check system registry: `system_registry.json`
3. Ensure all test systems registered

### "System not registered"
**Solution:**
1. Check address matches post-refactor addresses (1, 2-3, 3-1, 5)
2. Run UDS validation: `python __init__.py`
3. Review `system_registry.json` for missing entries

### Test hangs or times out
**Solution:**
1. Check if systems are operational
2. Review UDS logs for fault codes
3. Run with `--verbose` flag for detailed trace

---

## Results

Test results are automatically saved to:
```
F:\The Central Command\Command Center\Data Bus\diagnostic_manager\test_plans\flow_test_results\
```

**File format:** `flow_test_results_YYYYMMDD_HHMMSS.json`

**Contents:**
- Complete signal trace log
- Timing data for each hop
- Fault check results
- Success/fail status

---

## Next Steps After Test Passes

### Phase 2: Add Section Processing
Once core flow validated, add Section frameworks (4-x) into flow:
- Evidence Locker → Gateway → **Section 4-1** → Marshall → Mission Debrief

### Phase 3: Real Integration
Replace simulation with actual system calls:
- Real Evidence Locker intake
- Real Gateway routing
- Real Marshall processing
- Real Mission Debrief assembly

### Phase 4: Stress Testing
- Multiple evidence files
- Concurrent processing
- Load testing (50+ files)
- Fault recovery validation

---

## Notes

**Current Implementation:**
- Simulates signal flow (actual system integration pending)
- Uses timing delays to mimic processing
- Validates CANBUS architecture and signal routing

**Design Intent:**
- Prove autonomous progression capability
- Identify bottlenecks in flow architecture
- Validate UDS fault detection
- Establish baseline for performance metrics

**Memory Reference:** [[9730609]] - UDS validation via fault observation

---

## Contact

**Agent:** DEESCALATION (agent_3_DEESCALATION_CODING)  
**Location:** `F:\The Central Command\The War Room\dev_tracking\agent_3_DEESCALATION_CODING`  
**Logs:** `F:\The Central Command\The War Room\dev_tracking\logs`

---

**Test Status:** READY FOR EXECUTION  
**Last Updated:** 2025-10-10  
**Version:** 1.0


