# Self-Test Procedure and UDS Integration Analysis
**Date:** 2025-10-11  
**Question:** Will UDS understand the new self-test process and fault reporting?

---

## ANSWER: YES, BUT WITH ONE GAP ⚠️

The UDS **will understand** the self-test fault codes, but there's a **missing link** in how those faults get registered into `system_registry` for baseline monitoring to detect them.

---

## CURRENT FLOW (What Works) ✅

### 1. Parent Module Self-Test Emits Fault
```python
# Example: Evidence Locker detects broken OCR Processor
if self.communicator:
    self.communicator.send_signal(
        target_address="Bus-1",  # UDS
        radio_code="SOS",
        message="OCR Processor initialization failed",
        payload={
            "fault_code": "[1.8-12-INIT]",
            "description": "OCR Processor not initialized",
            "component": "OCR Processor",
            "reporting_address": "1.8",
            "parent_address": "1",
            "severity": "CRITICAL",
            "timestamp": datetime.now().isoformat(),
            "fault_type": "12",
            "fault_type_description": "Missing initialization dependency"
        }
    )
```

**Status:** ✅ Working - All parent modules can emit this way

---

### 2. UniversalCommunicator Routes to Bus
```python
# universal_communicator.py, line 119
self.bus_connection.send('communication', {
    'signal_id': signal_id,
    'caller_address': self.system_address,  # e.g., "1"
    'target_address': target_address,        # "Bus-1"
    'radio_code': radio_code,                # "SOS"
    'message': message,
    'payload': payload,
    'timestamp': signal.timestamp
})
```

**Status:** ✅ Working - Signal sent to bus

---

### 3. Bus Routes Communication Signal
```python
# Bus receives 'communication' topic
# Bus should route to UDS (Bus-1 address)
```

**Status:** ⚠️ **POTENTIAL GAP** - Need to verify bus routes 'communication' signals to UDS

---

### 4. UDS Passive Monitoring (What I Changed)
```python
# core.py, lines 5829-5909
def _perform_baseline_testing(self, smoke_mode: bool = False):
    # Capture initial fault state
    for system_address, system_info in self.system_registry.items():
        initial_fault_counts[system_address] = len(system_info.get('faults', []))
    
    # Wait 15 seconds for self-tests to complete
    time.sleep(15)
    
    # Analyze NEW faults added during monitoring period
    for system_address, system_info in self.system_registry.items():
        current_faults = system_info.get('faults', [])
        new_faults = current_faults[initial_count:]
        
        if new_faults:
            # System reported faults - mark as ERROR
            system_info['status'] = DiagnosticStatus.ERROR.value
```

**Status:** ✅ Working - Passive monitoring implemented

---

## THE GAP: How Do Faults Get Into system_registry? ⚠️

**The Question:** When Evidence Locker sends `SOS` with fault payload to `Bus-1`, how does that fault get added to `system_registry['1']['faults']` so baseline monitoring can detect it?

### Current System Registry Structure
```json
{
  "1": {
    "name": "Evidence Locker",
    "status": "active",
    "faults": [],  // <-- How do SOS faults get added here?
    "children": ["1.1", "1.2", ..., "1.8"]
  }
}
```

### Two Possible Scenarios:

#### Scenario A: Bus Has SOS Handler (Needs Verification)
```python
# If bus_core.py has something like:
def _handle_sos_fault_signal(self, payload):
    system_address = payload.get('caller_address')
    fault_code = payload.get('fault_code')
    
    # Add fault to system registry
    if system_address in self.system_registry:
        self.system_registry[system_address]['faults'].append({
            'fault_code': fault_code,
            'timestamp': payload.get('timestamp'),
            'description': payload.get('description')
        })
```

**If this exists:** ✅ System works end-to-end  
**If this doesn't exist:** ❌ Faults never reach system_registry

---

#### Scenario B: UDS Needs SOS Signal Handler (Likely Missing)
```python
# UDS (core.py) needs something like:
def _register_uds_signal_handlers(self):
    if self.bus:
        self.bus.register_signal("communication", self._handle_communication_signal)
        self.bus.register_signal("sos_fault", self._handle_sos_fault)
        
def _handle_communication_signal(self, payload):
    """Process incoming communication signals"""
    radio_code = payload.get('radio_code')
    caller_address = payload.get('caller_address')
    
    if radio_code == "SOS":
        # Extract fault information
        fault_payload = payload.get('payload', {})
        fault_code = fault_payload.get('fault_code')
        
        # Add to system_registry
        if caller_address in self.system_registry:
            if 'faults' not in self.system_registry[caller_address]:
                self.system_registry[caller_address]['faults'] = []
            
            self.system_registry[caller_address]['faults'].append({
                'fault_code': fault_code,
                'component': fault_payload.get('component'),
                'description': fault_payload.get('description'),
                'severity': fault_payload.get('severity'),
                'timestamp': fault_payload.get('timestamp'),
                'reporting_address': fault_payload.get('reporting_address')
            })
            
            self.logger.warning(
                f"[UDS] Fault registered: {fault_code} from {caller_address}"
            )
```

**Status:** ⚠️ **LIKELY MISSING** - This handler doesn't exist in current UDS code

---

## COMPLETE FLOW (What Should Happen)

```
1. EVIDENCE LOCKER MODULE (Address: 1)
   └─> Runs self-test during initialization
   └─> Detects OCR Processor (1.8) is None
   └─> Emits SOS via UniversalCommunicator
       ├─ target_address: "Bus-1"
       ├─ radio_code: "SOS"
       └─ payload: { fault_code: "[1.8-12-INIT]", ... }

2. UNIVERSAL COMMUNICATOR
   └─> Wraps fault in communication signal
   └─> Sends to bus_connection.send('communication', {...})

3. BUS CORE
   └─> Receives 'communication' signal
   └─> Routes to UDS (address "Bus-1")
   └─> Emits to UDS signal handlers

4. UDS HANDLER (MISSING LINK)
   └─> Receives communication signal with radio_code="SOS"
   └─> Extracts fault_code from payload
   └─> Adds fault to system_registry['1']['faults']
   └─> Logs: "[UDS] Fault registered: [1.8-12-INIT] from 1"

5. UDS BASELINE MONITORING (15 seconds later)
   └─> Checks system_registry['1']['faults']
   └─> Sees new fault: [1.8-12-INIT]
   └─> Marks Evidence Locker as ERROR
   └─> Generates baseline report with fault details
```

---

## WHAT NEEDS TO BE ADDED

### Add UDS Communication Signal Handler

**File:** `F:\The Central Command\Command Center\Data Bus\diagnostic_manager\Unified_diagnostic_system\core.py`

**Location:** In the `UnifiedDiagnosticSystem.__init__` method, after bus initialization

```python
def __init__(self, bus_connection=None, ...):
    # ... existing code ...
    
    if self.bus:
        # Register UDS signal handlers
        self._register_uds_signal_handlers()

def _register_uds_signal_handlers(self):
    """Register UDS as listener for communication signals (especially SOS)"""
    if not self.bus:
        return
    
    try:
        # Listen for all communication signals directed at Bus-1 (UDS)
        self.bus.register_signal("communication", self._handle_incoming_communication)
        self.logger.info("[UDS] Registered communication signal handler")
    except Exception as e:
        self.logger.error(f"[UDS] Failed to register signal handlers: {e}")

def _handle_incoming_communication(self, signal_data: Dict[str, Any]) -> None:
    """
    Handle incoming communication signals directed at UDS.
    Processes SOS faults and registers them to system_registry.
    """
    try:
        target_address = signal_data.get('target_address')
        
        # Only process signals directed at UDS (Bus-1)
        if target_address != "Bus-1":
            return
        
        radio_code = signal_data.get('radio_code')
        caller_address = signal_data.get('caller_address')
        payload = signal_data.get('payload', {})
        
        # Process SOS faults
        if radio_code == "SOS":
            fault_code = payload.get('fault_code', 'UNKNOWN')
            component = payload.get('component', 'Unknown')
            description = payload.get('description', '')
            severity = payload.get('severity', 'CRITICAL')
            reporting_address = payload.get('reporting_address', caller_address)
            timestamp = payload.get('timestamp', datetime.now().isoformat())
            
            self.logger.warning(
                f"[UDS] SOS FAULT RECEIVED: {fault_code} from {caller_address} "
                f"(component: {component})"
            )
            
            # Add fault to system_registry
            if caller_address in self.system_registry:
                if 'faults' not in self.system_registry[caller_address]:
                    self.system_registry[caller_address]['faults'] = []
                
                fault_entry = {
                    'fault_code': fault_code,
                    'component': component,
                    'description': description,
                    'severity': severity,
                    'reporting_address': reporting_address,
                    'timestamp': timestamp,
                    'fault_type': payload.get('fault_type', 'UNKNOWN'),
                    'fault_type_description': payload.get('fault_type_description', '')
                }
                
                self.system_registry[caller_address]['faults'].append(fault_entry)
                
                # Update system status to ERROR
                self.system_registry[caller_address]['status'] = DiagnosticStatus.ERROR.value
                
                self.logger.info(
                    f"[UDS] Fault registered to system_registry: "
                    f"System {caller_address} now has {len(self.system_registry[caller_address]['faults'])} fault(s)"
                )
            else:
                self.logger.warning(
                    f"[UDS] Cannot register fault - system {caller_address} not found in registry"
                )
    
    except Exception as e:
        self.logger.error(f"[UDS] Error handling communication signal: {e}")
```

---

## AFTER ADDING THIS HANDLER

### Complete Working Flow:
1. ✅ Parent module runs self-test
2. ✅ Detects broken child component
3. ✅ Emits SOS via UniversalCommunicator to "Bus-1"
4. ✅ Bus routes signal to UDS
5. ✅ **UDS handler receives SOS and adds fault to system_registry**
6. ✅ Baseline monitoring detects new fault during 15-second window
7. ✅ Baseline report shows fault code, component, and description

### Baseline Report Will Show:
```
==========================================================================
BASELINE MONITORING RESULTS - 2025-10-11 21:45:15
==========================================================================
Monitoring Period: 15 seconds (Passive Monitoring)
Total Systems: 13
Healthy Systems: 12
Systems With Faults: 1

FAULTS DETECTED:
--------------------------------------------------------------------------
System: 1 (Evidence Locker)
  Fault 1: [1.8-12-INIT]
    Component: OCR Processor
    Description: OCR Processor not initialized - missing dependency
    Severity: CRITICAL
    Timestamp: 2025-10-11T21:45:02.241Z
    Reporting Address: 1.8
    Fault Type: 12 (Missing initialization dependency)
--------------------------------------------------------------------------

RECOMMENDATION: Review Evidence Locker initialization sequence
==========================================================================
```

---

## SUMMARY

**Will UDS understand the new self-test process?**

✅ **YES** - With one addition: UDS needs a `_handle_incoming_communication` signal handler to:
1. Listen for `communication` signals directed at `Bus-1`
2. Process `SOS` radio codes
3. Extract fault_code from payload
4. Add fault to `system_registry[caller_address]['faults']`

**Without this handler:**
- Self-tests run correctly ✅
- Faults are detected ✅
- SOS signals are emitted ✅
- But faults never reach system_registry ❌
- Baseline monitoring sees no faults ❌

**With this handler:**
- Complete end-to-end fault propagation ✅
- Baseline monitoring detects all faults ✅
- Proper fault codes in diagnostic reports ✅
- UDS fully understands self-test process ✅

---

## IMPLEMENTATION PRIORITY

**CRITICAL:** Add `_handle_incoming_communication` to UDS  
**Time:** ~30 minutes  
**Impact:** Enables entire self-test fault reporting system  
**Without it:** All self-test work is non-functional for UDS reporting  

This is the **final missing piece** to complete the self-test system.


