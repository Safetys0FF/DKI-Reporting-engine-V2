# CRITICAL: Dual Bus Architecture Bug
**Date:** 2025-10-11  
**Severity:** CRITICAL - ARCHITECTURE FLAW  
**Impact:** System creates TWO buses, nobody listens to the real one

---

## THE ROOT PROBLEM

**There are TWO CANBUS instances:**
1. **Bus #1** - Created by `__init__.py` (the REAL bus modules connect to)
2. **Bus #2** - Created by `comms.py` (a phantom bus nobody uses)

**Signal handlers are registered on Bus #2, but modules send to Bus #1.**

---

## THE FLOW (BROKEN)

```
__init__.py (__init__ method, line 60-173)
  │
  ├─ Line 124: self.bus = DKIReportBus()  ← Creates Bus #1
  ├─ Line 156: self.communicator = UniversalCommunicator("DIAG-1", Bus #1)
  ├─ Lines 188-198: Registers signals on Bus #1
  │   ├─ fault.report
  │   ├─ fault.sos
  │   └─ system.fault
  │
  └─ Line 82: self.core = CoreSystem(bus_connection=self.bus)  ← Passes Bus #1
      │
      └─ core.py (__init__, line 456-591)
          │
          ├─ Line 460: self.bus = bus_connection  ← Receives Bus #1
          │
          └─ Line 586: self.comms = pull_comms_module(self)
              │
              └─ core.py (pull_comms_module, line 323-340)
                  │
                  └─ Line 332: comms.CommsSystem(orchestrator=orchestrator)
                      │       ^^^^^ ONLY PASSES ORCHESTRATOR, NO BUS!
                      │
                      └─ comms.py (__init__, line 84-136)
                          │
                          ├─ Line 84-89: Gets orchestrator, bus_connection=None
                          ├─ Line 89: self.bus_connected = False
                          │
                          └─ Line 127: self._connect_to_bus()
                              │
                              └─ comms.py (_connect_to_bus, line 226-243)
                                  │
                                  ├─ Line 233: self.bus = DKIReportBus()  ← Creates Bus #2!
                                  ├─ Line 234: self.communicator = UniversalCommunicator("DIAG-1", Bus #2)
                                  │
                                  └─ Line 238: self._register_diagnostic_signals()
                                      │       Registers on Bus #2 (WRONG BUS!)
                                      │
                                      └─ Lines 252-258: Register 'fault.sos', 'fault.report', etc
                                                        ^^^^^^ Nobody listening on Bus #1!
```

---

## WHY IT FAILS

**Modules (Evidence Locker, etc):**
- Connect to **Bus #1** (the original bus from __init__.py)
- Send `'communication'` signals with `radio_code="SOS"`
- Signal goes to Bus #1

**__init__.py:**
- Registers handlers on **Bus #1**
- But only for `'fault.sos'`, `'fault.report'` (wrong topics)
- Never registers `'communication'` handler

**comms.py:**
- Creates its own **Bus #2** (phantom)
- Registers handlers on **Bus #2**
- But still only for `'fault.sos'`, `'fault.report'` (wrong topics)
- Also never registers `'communication'` handler

**Result:**
- Modules send `'communication'` to Bus #1
- __init__.py listening on Bus #1 but for wrong topics
- Comms listening on Bus #2 (phantom bus)
- **Nobody hears anything**

---

## THE COMPLETE FIX

### 1. Pass Bus to Comms (FIX BUS DUPLICATION)

**File:** `core.py`  
**Location:** Line 323-340 (pull_comms_module)

**Change from:**
```python
def pull_comms_module(orchestrator):
    """Pull communication module with fault isolation"""
    try:
        logger = logging.getLogger("ModulePuller")
        logger.info("Pulling communication module...")
        try:
            from . import comms
        except ImportError:
            import comms
        comms_instance = comms.CommsSystem(orchestrator=orchestrator)  # NO BUS PASSED!
        logger.info("Communication module pulled successfully")
        return comms_instance
```

**Change to:**
```python
def pull_comms_module(orchestrator):
    """Pull communication module with fault isolation"""
    try:
        logger = logging.getLogger("ModulePuller")
        logger.info("Pulling communication module...")
        try:
            from . import comms
        except ImportError:
            import comms
        
        # CRITICAL: Pass bus and communicator from orchestrator
        bus_connection = getattr(orchestrator, 'bus', None)
        communicator = getattr(orchestrator, 'communicator', None)
        
        comms_instance = comms.CommsSystem(
            orchestrator=orchestrator,
            bus_connection=bus_connection,      # Pass real bus
            communicator=communicator            # Pass real communicator
        )
        logger.info("Communication module pulled successfully (using shared bus)")
        return comms_instance
```

---

### 2. Fix Comms to NOT Create New Bus

**File:** `comms.py`  
**Location:** Line 126-136 (__init__)

**Change from:**
```python
# Initialize
self._connect_to_bus()  # This creates a NEW bus if none provided!
self._load_fault_code_protocol()
```

**Change to:**
```python
# Initialize
# Only connect if no bus was provided
if not self.bus_connected:
    self._connect_to_bus()  # Create bus only if needed (fallback)
else:
    # Use provided bus - register handlers on it
    self._register_diagnostic_signals()

self._load_fault_code_protocol()
```

---

### 3. Add 'communication' Handler to Comms

**File:** `comms.py`  
**Location:** Line 245-262 (_register_diagnostic_signals)

**Change from:**
```python
def _register_diagnostic_signals(self):
    """Register diagnostic signal handlers"""
    if not self.bus:
        return
    
    try:
        # Register signal handlers
        self.bus.register_signal('diagnostic.rollcall', self._handle_rollcall)
        self.bus.register_signal('fault.report', self._handle_fault_report)
        self.bus.register_signal('fault.sos', self._handle_sos_fault)  # WRONG TOPIC
        self.bus.register_signal('system.fault', self._handle_system_fault)
        self.bus.register_signal('error.report', self._handle_error_report)
        self.bus.register_signal('subscription.response', self._handle_subscription_response)
        self.bus.register_signal('diagnostic.subscription', self._handle_subscription_response)
        
        self.logger.info("Registered diagnostic signal handlers")
```

**Change to:**
```python
def _register_diagnostic_signals(self):
    """Register diagnostic signal handlers"""
    if not self.bus:
        return
    
    try:
        # CRITICAL: Register 'communication' handler (where modules actually send)
        self.bus.register_signal('communication', self._handle_communication_signal)
        
        # Register diagnostic signal handlers
        self.bus.register_signal('diagnostic.rollcall', self._handle_rollcall)
        self.bus.register_signal('fault.report', self._handle_fault_report)
        self.bus.register_signal('fault.sos', self._handle_sos_fault)  # Keep for legacy
        self.bus.register_signal('system.fault', self._handle_system_fault)
        self.bus.register_signal('error.report', self._handle_error_report)
        self.bus.register_signal('subscription.response', self._handle_subscription_response)
        self.bus.register_signal('diagnostic.subscription', self._handle_subscription_response)
        
        self.logger.info("Registered diagnostic signal handlers on SHARED BUS (including 'communication')")
```

---

### 4. Remove Duplicate Handlers from __init__.py

**File:** `__init__.py`  
**Location:** Lines 181-198 (_register_diagnostic_signals)

**REMOVE ENTIRELY:**
```python
def _register_diagnostic_signals(self):
    """Register diagnostic system signal handlers with CAN-BUS PRIMARY"""
    if not self.bus_connected:
        self.logger.warning("Cannot register signals - CAN-BUS not connected (SAFEMODE)")
        return
        
    # PRIMARY CAN-BUS: Register fault reporting signals
    self.bus.register_signal("fault.report", self._handle_fault_report_signal)
    self.bus.register_signal("fault.sos", self._handle_sos_fault_signal)
    self.bus.register_signal("system.fault", self._handle_system_fault_signal)
    self.bus.register_signal("error.report", self._handle_error_report_signal)
    
    # PRIMARY CAN-BUS: Register diagnostic control signals
    self.bus.register_signal("diagnostic.start", self._handle_diagnostic_start_signal)
    self.bus.register_signal("diagnostic.stop", self._handle_diagnostic_stop_signal)
    self.bus.register_signal("diagnostic.status", self._handle_diagnostic_status_signal)
    
    self.logger.info("Diagnostic signal handlers registered with CAN-BUS PRIMARY")
```

**REMOVE the call from __init__ (line 169):**
```python
# PRIMARY OPERATION: Register diagnostic signal handlers
self._register_diagnostic_signals()  # <-- DELETE THIS LINE
```

**Why remove:** Comms.py owns signal handling. __init__.py should only create bus and pass it down.

---

### 5. Add Communication Signal Router to Comms

**File:** `comms.py`  
**Location:** After `_handle_error_report` (around line 475)

**Add method:**
```python
def _handle_communication_signal(self, signal_data: Dict[str, Any]):
    """
    Handle incoming communication signals and route based on radio_code.
    This is the PRIMARY signal handler for UniversalCommunicator messages.
    """
    try:
        target_address = signal_data.get('target_address')
        
        # Only process signals directed at UDS (DIAG-1 or Bus-1)
        if target_address not in ["Bus-1", "DIAG-1"]:
            return
        
        radio_code = signal_data.get('radio_code')
        caller_address = signal_data.get('caller_address')
        
        self.logger.debug(
            f"[Comms] Communication signal received: {radio_code} from {caller_address}"
        )
        
        # Route based on radio_code
        if radio_code == "SOS":
            self.logger.critical(
                f"[Comms] SOS signal from {caller_address} - routing to fault handler"
            )
            self._handle_sos_fault(signal_data)
        
        elif radio_code == "MAYDAY":
            self.logger.critical(f"[Comms] MAYDAY from {caller_address}")
            self._handle_system_fault(signal_data)
        
        elif radio_code == "ROLLCALL":
            self._handle_rollcall(signal_data)
        
        elif radio_code in ["10-4", "10-6", "10-8", "10-9", "10-10"]:
            self.logger.debug(f"[Comms] Status: {radio_code} from {caller_address}")
        
        else:
            self.logger.warning(f"[Comms] Unknown radio_code: {radio_code}")
    
    except Exception as e:
        self.logger.error(f"[Comms] Error handling communication: {e}")
```

---

## AFTER THE FIX

**Single Bus Architecture:**
```
__init__.py
  ├─ Creates Bus #1 (ONLY bus)
  ├─ Passes Bus #1 to CoreSystem
  └─ CoreSystem passes Bus #1 to Comms
      └─ Comms uses Bus #1 (doesn't create new one)
          └─ Registers 'communication' handler on Bus #1
              └─ Hears all module SOS signals!
```

**Signal Flow:**
```
Module → UniversalCommunicator.send_signal(radio_code="SOS")
  ↓
Bus #1.send('communication', {...})
  ↓
Comms._handle_communication_signal (registered on Bus #1)
  ↓
Checks: radio_code == "SOS"
  ↓
Routes to: _handle_sos_fault
  ↓
Forwards to: enforcement.handle_sos_fault
  ↓
Updates: system_registry[address]['faults']
```

---

## SUMMARY

**Three Critical Bugs:**
1. **Dual Bus:** Comms creates its own bus instead of using shared one
2. **Wrong Topic:** Both __init__ and comms listen to `'fault.sos'` instead of `'communication'`
3. **Duplicate Handlers:** Both __init__ and comms try to register same handlers

**The Fixes:**
1. Pass bus from CoreSystem to Comms (3 lines)
2. Comms uses provided bus instead of creating new one (5 lines)
3. Add `'communication'` handler to comms (1 line + 40 line method)
4. Remove duplicate handlers from __init__.py (delete 20 lines)

**Result:** One bus, one set of handlers, listening on correct topic.

**Time:** 1 hour  
**Impact:** Enables entire self-test fault reporting system

---

**This is the actual root cause. All the self-test work is correct - the bus architecture was broken.**


