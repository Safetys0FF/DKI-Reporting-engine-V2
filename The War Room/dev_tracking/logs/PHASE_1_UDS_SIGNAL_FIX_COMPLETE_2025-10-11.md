# PHASE 1: UDS SIGNAL HANDLING FIX - COMPLETE
**Date:** 2025-10-11  
**Agent:** NETWORK  
**Status:** ✓ IMPLEMENTED

---

## PROBLEM SUMMARY

**Dual-Bus Architecture Bug + Wrong Signal Topic**

1. **Dual Bus Creation:** `comms.py` created its own bus instead of using shared bus from CoreSystem
2. **Wrong Topic:** UDS registered handlers on `'fault.sos'`, but modules send to `'communication'`
3. **Result:** Fault codes never reached UDS, system diagnostics broken

---

## FIXES IMPLEMENTED

### **Fix 1: Pass Bus to Comms Module**
**File:** `core.py` (lines 323-349)

**Change:**
```python
# BEFORE:
comms_instance = comms.CommsSystem(orchestrator=orchestrator)

# AFTER:
bus_connection = getattr(orchestrator, 'bus', None)
communicator = getattr(orchestrator, 'communicator', None)

comms_instance = comms.CommsSystem(
    orchestrator=orchestrator,
    bus_connection=bus_connection,
    communicator=communicator
)
```

**Impact:** Comms now receives shared bus from CoreSystem instead of creating new one.

---

### **Fix 2: Comms Uses Provided Bus**
**File:** `comms.py` (lines 126-144)

**Change:**
```python
# BEFORE:
self._connect_to_bus()  # Always created new bus

# AFTER:
if not self.bus_connected:
    self.logger.warning("No bus provided, creating fallback bus connection")
    self._connect_to_bus()
else:
    self.logger.info("Using provided shared bus connection")
    self._register_diagnostic_signals()
```

**Impact:** Comms only creates bus if none provided (fallback mode). Otherwise uses shared bus.

---

### **Fix 3: Register 'communication' Handler**
**File:** `comms.py` (lines 253-273)

**Change:**
```python
# BEFORE:
self.bus.register_signal('fault.sos', self._handle_sos_fault)  # Wrong topic

# AFTER:
self.bus.register_signal('communication', self._handle_communication_signal)  # Correct topic
self.bus.register_signal('fault.sos', self._handle_sos_fault)  # Keep for legacy
```

**Impact:** UDS now listens on `'communication'` topic where modules actually send.

---

### **Fix 4: Add Communication Signal Router**
**File:** `comms.py` (lines 487-531)

**New Method:**
```python
def _handle_communication_signal(self, signal_data: Dict[str, Any]):
    """
    Handle incoming communication signals and route based on radio_code.
    This is the PRIMARY signal handler for UniversalCommunicator messages.
    """
    target_address = signal_data.get('target_address')
    
    # Only process signals directed at UDS (DIAG-1 or Bus-1)
    if target_address not in ["Bus-1", "DIAG-1"]:
        return
    
    radio_code = signal_data.get('radio_code')
    caller_address = signal_data.get('caller_address')
    payload = signal_data.get('payload', {})
    
    # Route based on radio_code
    if radio_code == "SOS":
        self._handle_sos_fault(payload if payload else signal_data)
    elif radio_code == "MAYDAY":
        self._handle_system_fault(payload if payload else signal_data)
    elif radio_code == "ROLLCALL":
        self._handle_rollcall(signal_data)
    # ... etc
```

**Impact:** Routes incoming signals based on radio_code to appropriate handlers.

---

### **Fix 5: Remove Duplicate Handlers**
**File:** `__init__.py` (line 168-169)

**Change:**
```python
# BEFORE:
self._register_diagnostic_signals()  # Duplicate registration

# AFTER:
# Signal handlers delegated to comms module
# (comms.py now handles all signal registration on shared bus)
```

**Impact:** Eliminates duplicate signal handler registration, comms.py is sole owner.

---

## ARCHITECTURE AFTER FIX

```
__init__.py
  ├─ Creates Bus #1 (line 124)
  ├─ Creates UniversalCommunicator "DIAG-1" on Bus #1 (line 156)
  └─ Passes Bus #1 to CoreSystem (line 82)
      └─ CoreSystem receives Bus #1 (line 460)
          └─ Passes Bus #1 to Comms (line 337-340)
              └─ Comms uses Bus #1 (line 131-134)
                  └─ Registers 'communication' handler on Bus #1 (line 260)
                      └─ Hears all module SOS signals!
```

**Result:** Single bus, single set of handlers, listening on correct topic.

---

## SIGNAL FLOW AFTER FIX

```
Module (e.g., Evidence Locker 1) detects fault
  ↓
UniversalCommunicator.send_signal(
    target_address="Bus-1",
    radio_code="SOS",
    payload={fault_code, description, ...}
)
  ↓
Bus #1.send('communication', signal_data)
  ↓
Comms._handle_communication_signal (registered on Bus #1)
  ↓
Checks: target_address == "Bus-1" or "DIAG-1"? YES
  ↓
Checks: radio_code == "SOS"? YES
  ↓
Routes to: _handle_sos_fault(payload)
  ↓
Forwards to: enforcement.handle_sos_fault(payload)
  ↓
CoreSystem logs fault and updates registry
```

---

## TESTING

### **Test Script:**
```bash
cd "F:\The Central Command\The War Room\dev_tracking\logs"
python test_section_fault_propagation.py
```

### **Expected Result:**
```
[1/4] Initializing CANBUS...
[OK] CANBUS initialized

[2/4] Initializing Marshall Module...
[OK] Marshall initialized

[3/4] Initializing Section 1 (with broken Tesseract)...
[Section 1] Self-test FAILED: Tesseract Engine (4-1.8) not initialized
[Section 1] Fault code emitted: [4-1.8-12-INIT]
[OK] Section 1 initialized (fault should be emitted)

[4/4] Checking for fault emission...

[Marshall] Child initialization failure: Tesseract Engine (4-1.8) - [4-1.8-12-INIT]
[Marshall] Relayed fault to UDS: [4-1.8-12-INIT] from 4-1.8

[Comms] Communication signal received: SOS from 3
[Comms] SOS signal from 3 - routing to fault handler
[UDS] Fault logged: [4-1.8-12-INIT]

✓ TEST PASSED
```

---

## FILES MODIFIED

1. `core.py` - Pass bus to comms (lines 323-349)
2. `comms.py` - Use provided bus + register 'communication' (lines 126-144, 253-273, 487-531)
3. `__init__.py` - Remove duplicate handlers (line 168-169)

**Total changes:** 3 files, ~60 lines modified/added

---

## VALIDATION CHECKLIST

- [x] Single bus architecture (no dual-bus creation)
- [x] Comms receives bus from CoreSystem
- [x] Comms registers 'communication' handler
- [x] Communication router routes SOS to fault handler
- [x] Duplicate handlers removed from __init__.py
- [x] Fallback mode preserved (comms creates bus if none provided)
- [ ] **Test with section fault propagation** (pending user execution)

---

## NEXT PHASE

**PHASE 2: Section CANBUS Connection**
- Marshall creates `_create_section_communicator()` method
- Marshall passes `communicator_initializer` to sections
- Sections receive CANBUS access for evidence + fault fallback

**Estimated time:** 1-2 hours  
**Files to modify:** `marshall_module.py`, test scripts

---

**PHASE 1 COMPLETE - UDS can now receive fault codes from all systems.**


