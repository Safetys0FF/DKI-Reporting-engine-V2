# Communication Language Breakdown Analysis
## Date: October 5, 2025

## The Problem: Components Speaking Different Languages

### **CAN-Bus Registry Language (bus_core.py):**
```python
default_handlers = {
    'case_create': self._handle_case_create_signal,
    'files_add': self._handle_files_add_signal,
    'evidence.new': self._handle_evidence_new_signal,
    'evidence.annotated': self._handle_evidence_annotated_signal,
    'evidence.request': self._handle_evidence_request_signal,
    'evidence.deliver': self._handle_evidence_deliver_signal,
    'evidence.updated': self._handle_evidence_updated_signal,
    'evidence.tagged': self._handle_evidence_tagged_signal,
    'evidence.stored': self._handle_evidence_stored_signal,
    'evidence_locker.call_out': self._handle_evidence_call_out_signal,
    'evidence_locker.accept': self._handle_evidence_accept_signal,
    'section.needs': self._handle_section_needs_signal,
    'case.snapshot': self._handle_case_snapshot_signal,
    'gateway.status': self._handle_gateway_status_signal,
    'locker.status': self._handle_locker_status_signal,
    'mission.status': self._handle_mission_status_signal,
    'narrative.assembled': self._handle_narrative_assembled_signal,
}
```

### **Evidence Locker Language:**
```python
# Evidence Locker uses DIFFERENT signal names
def _call_out_to_ecc(self, operation: str, data: Dict[str, Any]) -> Dict[str, Any]:
    # Uses: "evidence_locker.call_out" (matches CAN-bus)
    # But calls ECC directly instead of using bus
    
def _wait_for_ecc_confirm(self, timeout: int = 30) -> bool:
    # Uses: "evidence_locker.accept" (matches CAN-bus)
    # But calls ECC directly instead of using bus
```

### **Gateway Controller Language:**
```python
# Gateway Controller uses DIFFERENT signal names
def _emit_bus_event(self, signal: str, payload: Dict[str, Any]) -> None:
    # Uses: "gateway_controller.call_out" (DOESN'T match CAN-bus)
    # Should be: "gateway.call_out" or "gateway.status"
    
def _call_out_to_ecc(self, operation: str, data: Dict[str, Any]) -> bool:
    # Uses: "gateway_controller.call_out" (DOESN'T match CAN-bus)
    # Should be: "gateway.call_out"
```

### **ECC Language:**
```python
# ECC uses DIFFERENT signal names
def _handle_bus_section_data_updated(self, signal_data: Dict[str, Any]) -> None:
    # Uses: "section.data.updated" (DOESN'T match CAN-bus)
    # Should be: "section.updated" or "section.data.updated"
    
def _handle_bus_gateway_section_complete(self, signal_data: Dict[str, Any]) -> None:
    # Uses: "gateway.section.complete" (DOESN'T match CAN-bus)
    # Should be: "gateway.status" or "section.complete"
```

### **Narrative Assembler Language:**
```python
# Narrative Assembler uses CORRECT signal names
def assemble_and_broadcast(self, section_id: str, structured_data: Dict[str, Any]) -> Dict[str, Any]:
    # Uses: "narrative.assembled" (matches CAN-bus)
    # This is CORRECT!
```

### **Mission Debrief Manager Language:**
```python
# Mission Debrief Manager uses DIFFERENT signal names
def _generate_direct_report(self, section_data: Dict[str, Any]) -> Dict[str, Any]:
    # Uses: "mission.debrief.complete" (DOESN'T match CAN-bus)
    # Should be: "mission.status" or "mission.complete"
```

## **The Language Breakdown:**

### **1. Signal Name Inconsistency:**
| Component | Uses | CAN-Bus Registry | Status |
|-----------|------|------------------|---------|
| Evidence Locker | `evidence_locker.call_out` | `evidence_locker.call_out` | ✅ MATCHES |
| Evidence Locker | `evidence_locker.accept` | `evidence_locker.accept` | ✅ MATCHES |
| Gateway Controller | `gateway_controller.call_out` | `gateway.status` | ❌ MISMATCH |
| Gateway Controller | `gateway_controller.accept` | `gateway.status` | ❌ MISMATCH |
| ECC | `section.data.updated` | `section.needs` | ❌ MISMATCH |
| ECC | `gateway.section.complete` | `gateway.status` | ❌ MISMATCH |
| Narrative Assembler | `narrative.assembled` | `narrative.assembled` | ✅ MATCHES |
| Mission Debrief | `mission.debrief.complete` | `mission.status` | ❌ MISMATCH |

### **2. Communication Method Inconsistency:**
| Component | Method | Should Use |
|-----------|--------|------------|
| Evidence Locker | Direct ECC calls | `bus.emit()` |
| Gateway Controller | Direct ECC calls | `bus.emit()` |
| ECC | Direct component calls | `bus.register_signal()` |
| Narrative Assembler | `bus.emit()` | ✅ CORRECT |
| Mission Debrief | Direct calls | `bus.emit()` |

### **3. Payload Format Inconsistency:**
| Component | Payload Format | Standard Format |
|-----------|----------------|-----------------|
| Evidence Locker | Custom dict | `shared_interfaces.StandardInterface` |
| Gateway Controller | Custom dict | `shared_interfaces.StandardInterface` |
| ECC | Custom dict | `shared_interfaces.StandardInterface` |
| Narrative Assembler | Custom dict | `shared_interfaces.StandardInterface` |
| Mission Debrief | Custom dict | `shared_interfaces.StandardInterface` |

## **The Large Break in the Process:**

### **1. Signal Name Mismatch:**
- **CAN-Bus expects:** `gateway.status`
- **Gateway Controller emits:** `gateway_controller.call_out`
- **Result:** Signal never reaches handlers

### **2. Communication Method Mismatch:**
- **CAN-Bus expects:** `bus.emit(signal, payload)`
- **Components use:** `self.ecc.emit(signal, payload)`
- **Result:** Signals bypass CAN-bus entirely

### **3. Payload Format Mismatch:**
- **CAN-Bus expects:** Standardized payload format
- **Components use:** Custom payload formats
- **Result:** Handlers can't process payloads

### **4. Handler Registration Mismatch:**
- **CAN-Bus has:** Default handlers for specific signals
- **ECC registers:** Different signal names
- **Result:** No handlers for actual signals

## **The Complete Communication Breakdown:**

```
Evidence Locker → Direct ECC Call → ECC → Direct Component Call → Gateway Controller
     ↓                                                              ↓
   CAN-Bus                                                      CAN-Bus
   (IGNORED)                                                    (IGNORED)
```

**Instead of:**
```
Evidence Locker → CAN-Bus → ECC Handler → CAN-Bus → Gateway Controller
```

## **Required Standardization:**

### **1. Unified Signal Names:**
```python
# STANDARD SIGNAL NAMES (matching CAN-bus registry)
STANDARD_SIGNALS = {
    'evidence.new': 'evidence.new',
    'evidence.updated': 'evidence.updated',
    'evidence_locker.call_out': 'evidence_locker.call_out',
    'evidence_locker.accept': 'evidence_locker.accept',
    'gateway.status': 'gateway.status',
    'section.needs': 'section.needs',
    'narrative.assembled': 'narrative.assembled',
    'mission.status': 'mission.status',
    'case.snapshot': 'case.snapshot',
}
```

### **2. Unified Communication Method:**
```python
# ALL components must use CAN-bus
def communicate(self, signal: str, payload: Dict[str, Any]) -> None:
    """Unified communication method"""
    if not self.bus:
        self.logger.warning(f"CAN-bus not available for signal: {signal}")
        return
    
    # Use shared_interfaces for standardized payloads
    from shared_interfaces import validate_signal_payload, create_standard_signal
    
    if not validate_signal_payload(signal, payload):
        self.logger.warning(f"Invalid payload for signal: {signal}")
        return
    
    envelope = create_standard_signal(signal, payload, self.component_name)
    self.bus.emit(signal, envelope)
```

### **3. Unified Payload Format:**
```python
# ALL components must use shared_interfaces
from shared_interfaces import (
    StandardInterface,
    create_standard_signal,
    validate_signal_payload,
    SIGNAL_CONTRACTS
)

# Standard payload creation
payload = StandardInterface.create_standard_payload(
    signal_type=signal,
    data=data,
    source=self.component_name,
    timestamp=datetime.now().isoformat()
)
```

## **Current State:**
- ❌ **Signal names don't match** CAN-bus registry
- ❌ **Communication methods inconsistent** across components
- ❌ **Payload formats different** for each component
- ❌ **No unified language** for inter-component communication
- ❌ **Large break in process** due to language mismatch

## **Impact:**
- **Signals never reach handlers** due to name mismatch
- **Components bypass CAN-bus** due to method mismatch
- **Handlers can't process payloads** due to format mismatch
- **No centralized communication** due to language mismatch
- **Process completely broken** due to communication breakdown

## **Fix Priority: CRITICAL**
The entire communication system is broken due to language inconsistency. All components must be standardized to use the same language, signal names, and communication methods.

## **Implementation Plan:**
1. **Standardize all signal names** to match CAN-bus registry
2. **Standardize all communication methods** to use CAN-bus
3. **Standardize all payload formats** using shared_interfaces
4. **Update all components** to use unified language
5. **Test end-to-end communication** with standardized language
6. **Verify all signals reach handlers** with correct names and formats

This will fix the **large break in the process** and restore **unified communication** across all components.

