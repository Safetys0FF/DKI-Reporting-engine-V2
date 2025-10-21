# CRITICAL: Comms.py Signal Handler Fix
**Date:** 2025-10-11  
**File:** `F:\The Central Command\Command Center\Data Bus\diagnostic_manager\Unified_diagnostic_system\comms.py`  
**Issue:** Comms listens to `'fault.sos'` but modules send to `'communication'`

---

## THE PROBLEM

**Comms.py has the SOS handler** (line 452-458):
```python
def _handle_sos_fault(self, signal_data: Dict[str, Any]):
    """Handle SOS fault signal (emergency)"""
    self.logger.critical(f"Received SOS fault: {signal_data}")
    
    # Route to enforcement for immediate action
    if self.orchestrator and hasattr(self.orchestrator, 'enforcement'):
        self.orchestrator.enforcement.handle_sos_fault(signal_data)
```

**BUT it's registered to the wrong signal** (line 254):
```python
self.bus.register_signal('fault.sos', self._handle_sos_fault)
```

**Modules send to:** `'communication'` topic with `radio_code="SOS"`  
**Comms listens to:** `'fault.sos'` topic

**They never connect.**

---

## THE FIX

### 1. Register 'communication' Signal Handler

**File:** `comms.py`  
**Location:** Line 245-262 in `_register_diagnostic_signals()`

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
        self.bus.register_signal('fault.sos', self._handle_sos_fault)  # <-- WRONG TOPIC
        self.bus.register_signal('system.fault', self._handle_system_fault)
        self.bus.register_signal('error.report', self._handle_error_report)
        self.bus.register_signal('subscription.response', self._handle_subscription_response)
        self.bus.register_signal('diagnostic.subscription', self._handle_subscription_response)
        
        self.logger.info("Registered diagnostic signal handlers")
    except Exception as e:
        self.logger.error(f"Error registering signals: {e}")
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
        
        self.logger.info("Registered diagnostic signal handlers including 'communication' topic")
    except Exception as e:
        self.logger.error(f"Error registering signals: {e}")
```

---

### 2. Add Communication Signal Router

**File:** `comms.py`  
**Location:** After `_handle_error_report` (around line 475)

**Add new method:**
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
            # Emergency fault - route to SOS handler
            self.logger.critical(
                f"[Comms] SOS signal received from {caller_address} - routing to fault handler"
            )
            self._handle_sos_fault(signal_data)
        
        elif radio_code == "MAYDAY":
            # Critical system failure
            self.logger.critical(
                f"[Comms] MAYDAY signal received from {caller_address}"
            )
            self._handle_system_fault(signal_data)
        
        elif radio_code == "STATUS":
            # Status request
            self.logger.info(
                f"[Comms] Status request from {caller_address}"
            )
            # Could route to status handler if needed
        
        elif radio_code == "ROLLCALL":
            # Rollcall response
            self.logger.info(
                f"[Comms] Rollcall response from {caller_address}"
            )
            self._handle_rollcall(signal_data)
        
        elif radio_code in ["10-4", "10-6", "10-8", "10-9", "10-10"]:
            # Normal status codes - log only
            self.logger.debug(
                f"[Comms] Status code {radio_code} from {caller_address}"
            )
        
        else:
            self.logger.warning(
                f"[Comms] Unknown radio code: {radio_code} from {caller_address}"
            )
    
    except Exception as e:
        self.logger.error(f"[Comms] Error handling communication signal: {e}")
```

---

### 3. Update _handle_sos_fault to Process Payload

**File:** `comms.py`  
**Location:** Lines 452-458

**Current:**
```python
def _handle_sos_fault(self, signal_data: Dict[str, Any]):
    """Handle SOS fault signal (emergency)"""
    self.logger.critical(f"Received SOS fault: {signal_data}")
    
    # Route to enforcement for immediate action
    if self.orchestrator and hasattr(self.orchestrator, 'enforcement'):
        self.orchestrator.enforcement.handle_sos_fault(signal_data)
```

**Enhanced to extract fault_code:**
```python
def _handle_sos_fault(self, signal_data: Dict[str, Any]):
    """Handle SOS fault signal (emergency)"""
    caller_address = signal_data.get('caller_address', 'UNKNOWN')
    message_payload = signal_data.get('payload', {})
    fault_code = message_payload.get('fault_code', 'UNKNOWN')
    component = message_payload.get('component', 'Unknown')
    
    self.logger.critical(
        f"[Comms] SOS FAULT RECEIVED: {fault_code} from {caller_address} ({component})"
    )
    
    # Add fault to system registry via enforcement
    if self.orchestrator and hasattr(self.orchestrator, 'enforcement'):
        # Ensure fault data is properly formatted
        fault_data = {
            'fault_code': fault_code,
            'component': component,
            'description': message_payload.get('description', ''),
            'severity': message_payload.get('severity', 'CRITICAL'),
            'reporting_address': message_payload.get('reporting_address', caller_address),
            'parent_address': caller_address,
            'timestamp': message_payload.get('timestamp', datetime.now().isoformat()),
            'fault_type': message_payload.get('fault_type', 'UNKNOWN'),
            'fault_type_description': message_payload.get('fault_type_description', ''),
            'radio_code': 'SOS',
            'source': 'self_test'
        }
        
        self.orchestrator.enforcement.handle_sos_fault(fault_data)
        
        self.logger.info(
            f"[Comms] Fault forwarded to enforcement: {fault_code}"
        )
```

---

## FLOW AFTER FIX

```
1. MODULE (e.g., Evidence Locker)
   └─> Detects fault during self-test
   └─> UniversalCommunicator.send_signal(target="Bus-1", radio_code="SOS", payload={fault_code: "[1.8-12-INIT]"})
   
2. UNIVERSAL COMMUNICATOR
   └─> bus.send('communication', {...payload with radio_code="SOS"...})
   
3. BUS
   └─> Receives 'communication' signal
   └─> Routes to all handlers registered for 'communication'
   
4. COMMS.PY (_handle_communication_signal) ✅ NOW LISTENING
   └─> Receives signal
   └─> Checks: target_address == "Bus-1" ✅
   └─> Checks: radio_code == "SOS" ✅
   └─> Routes to: _handle_sos_fault(signal_data)
   
5. COMMS.PY (_handle_sos_fault)
   └─> Extracts fault_code from payload
   └─> Formats fault_data
   └─> Forwards to: enforcement.handle_sos_fault(fault_data)
   
6. ENFORCEMENT.PY
   └─> Receives fault_data
   └─> Adds to system_registry[parent_address]['faults']
   └─> Updates system status to ERROR
   
7. UDS BASELINE MONITORING (15 seconds later)
   └─> Checks system_registry faults
   └─> Detects new fault: [1.8-12-INIT]
   └─> Generates baseline report
```

---

## SUMMARY

**Comms.py's responsibility:**
- ✅ Listen to `'communication'` topic (where modules send)
- ✅ Route messages based on `radio_code` (SOS, MAYDAY, 10-4, etc.)
- ✅ Extract fault details from payload
- ✅ Forward to enforcement for registry update

**The fix:**
1. Register `'communication'` signal handler (1 line)
2. Add `_handle_communication_signal` router (50 lines)
3. Enhance `_handle_sos_fault` to extract fault_code (25 lines)

**Time:** 30 minutes  
**Impact:** Enables entire self-test fault reporting chain  
**Critical:** Without this, comms can't hear any module faults

---

**This is comms.py's job - you're absolutely right. The communication routing belongs in the communication module.**


