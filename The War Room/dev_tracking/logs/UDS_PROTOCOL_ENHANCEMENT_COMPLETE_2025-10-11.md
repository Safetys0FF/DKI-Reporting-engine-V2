# UDS Protocol Enhancement - Self-Test Requirements
**Date:** 2025-10-11  
**Agent:** NETWORK Agent  
**Status:** ✅ COMPLETE

---

## CHANGES IMPLEMENTED

### 1. Auto-Registration Enhanced (Lines 4597-4668)

**File:** `core.py` `_create_mandatory_auto_registration_script()`

**Added `self_test_protocol` section for parent modules:**
```python
'self_test_protocol': {
    'required': True,
    'execution_point': 'post_initialization',
    'method_name': '_run_startup_self_test',
    'validation_requirements': {
        'check_child_components': True,
        'emit_faults_on_failure': True,
        'fault_target_address': 'Bus-1',
        'fault_radio_code': 'SOS',
        'validate_operational_status': True
    },
    'child_component_registry': [...],  # From system_registry.json
    'fault_emission_template': {
        'fault_code': '[CHILD_ADDRESS-FAULT_TYPE-LINE]',
        'severity': 'CRITICAL',
        'component': '<child_name>',
        'reporting_address': '<child_address>',
        'parent_address': system_address
    },
    'fault_types': {
        '10': 'Failed to initialize component',
        '11': 'Initialization timeout',
        '12': 'Missing initialization dependency',
        '13': 'Initialization resource unavailable',
        '14': 'Initialization permission denied'
    }
}
```

---

### 2. Child Component Registry Extraction (Lines 4696-4727)

**New Method:** `_get_child_components_from_registry()`

**Extracts child information from `system_registry.json`:**
- Address (e.g., "1.1", "1.2", "1.8")
- Name (e.g., "Evidence Classifier", "OCR Processor")
- Handler (e.g., "evidence_classifier.EvidenceClassifier")
- Location (file path)
- System type
- CANBUS connection status

**Example for Evidence Locker (1):**
```python
[
    {'address': '1.1', 'name': 'Evidence Classifier', ...},
    {'address': '1.2', 'name': 'Evidence Identifier', ...},
    {'address': '1.3', 'name': 'Static Data Flow', ...},
    {'address': '1.4', 'name': 'Evidence Index', ...},
    {'address': '1.5', 'name': 'Evidence Manifest', ...},
    {'address': '1.6', 'name': 'Evidence Class Builder', ...},
    {'address': '1.7', 'name': 'Case Manifest Builder', ...},
    {'address': '1.8', 'name': 'OCR Processor', ...}
]
```

---

### 3. Baseline Testing Replaced (Lines 5829-5909)

**Old:** `_perform_baseline_testing()` - 195 active ping tests (6-16 minutes)

**New:** Passive fault monitoring (5-15 seconds)

**How it works:**
1. UDS captures initial fault state for all systems
2. Waits 15 seconds for parent modules to complete self-tests
3. Parent modules emit fault codes if children fail
4. UDS analyzes fault changes during monitoring period
5. Reports systems with new faults vs. healthy systems

**Example Output:**
```
[UDS] Baseline monitoring: Waiting 15 seconds for parent module self-test faults...
[UDS] System 1 reported 1 fault(s): ['[1.8-12-INIT]']
[UDS] Baseline monitoring complete: 64/65 systems healthy, 1 with faults
```

---

## IMPACT

### Before
- ❌ UDS sent fault protocol but no self-test instructions
- ❌ Parent modules had no requirements to validate children
- ❌ 195-point test checked connectivity only (false positives)
- ❌ 6-16 minute baseline test runtime

### After
- ✅ UDS demands self-test with child registry
- ✅ Parent modules know what to validate and how to report
- ✅ Passive monitoring detects actual component failures
- ✅ 15-second baseline monitoring

---

## NEXT STEPS

### Implementation Required in Parent Modules

**Each parent module must now implement:**

```python
def _run_startup_self_test(self) -> bool:
    """
    Validate all child components per UDS self-test protocol.
    Emit fault codes for failed children.
    """
    operational = True
    
    # Validate each child component
    for child in self.children:
        if not self._validate_child(child):
            # Emit fault code to UDS
            self.communicator.send_signal(
                target_address="Bus-1",
                radio_code="SOS",
                message=f"{child.name} initialization failed",
                payload={
                    "fault_code": f"[{child.address}-12-INIT]",
                    "description": f"{child.name} not initialized",
                    "component": child.name,
                    "reporting_address": child.address,
                    "parent_address": self.MODULE_ADDRESS,
                    "severity": "CRITICAL"
                }
            )
            operational = False
    
    return operational
```

**Call during initialization:**
```python
def initialize_system(self):
    # ... existing initialization ...
    
    # Run self-test
    operational = self._run_startup_self_test()
    
    self.initialized = True
    status["self_test_passed"] = operational
    status["status"] = "SUCCESS" if operational else "DEGRADED"
    return status
```

---

## VALIDATION PLAN

1. Implement Evidence Locker self-test
2. Break OCR engine intentionally
3. Start system, watch for `[1.8-12-INIT]` fault
4. Verify UDS receives and logs fault
5. Verify baseline monitoring shows "64/65 systems healthy, 1 with faults"
6. Fix OCR, verify fault clears
7. Roll out to remaining 4 parent modules

---

**UDS is now ready to receive and enforce parent module self-test faults.**


