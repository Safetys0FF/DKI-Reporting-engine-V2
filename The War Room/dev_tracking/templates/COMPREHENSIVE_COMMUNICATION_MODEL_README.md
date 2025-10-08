# Comprehensive Communication Model Chart
## Date: October 5, 2025

## System-Wide Communication Architecture

### **Current State Analysis:**

## 1. **Evidence Locker Communication Model**

### **Current Callouts:**
```python
# Evidence Locker Signal Emissions
"evidence.stored"           # Evidence stored in locker
"evidence.tagged"           # Evidence tagged/classified
"evidence_locker.call_out"  # Permission requests to ECC
"evidence_locker.accept"    # Acceptance confirmations
"evidence_locker.send"      # Message sending
"evidence.scan"             # File scanning requests
"evidence.classify"         # Evidence classification
"evidence.index"            # Evidence indexing
"evidence.process_comprehensive" # Comprehensive processing
```

### **Communication Flow:**
```
Evidence Locker → ECC (direct) → Permission → Evidence Processing
Evidence Locker → Bus → evidence.stored → Other Components
Evidence Locker → Bus → evidence.tagged → Other Components
```

### **Problems:**
- **Direct ECC communication** bypasses CAN-bus
- **Mixed communication methods** (bus + direct)
- **Inconsistent signal names**

## 2. **Gateway Controller Communication Model**

### **Current Callouts:**
```python
# Gateway Controller Signal Emissions
"gateway.bottleneck_alert"  # Bottleneck alerts
"gateway_controller.call_out" # Call-out signals (WRONG NAME)
"gateway_controller.accept"   # Accept signals (WRONG NAME)
"evidence.new"              # New evidence announcements
"evidence.updated"          # Evidence updates
"section.data.updated"      # Section data updates
"section.needs"             # Section needs announcements
"case.snapshot"             # Case snapshots
```

### **Communication Flow:**
```
Gateway Controller → ECC (direct) → Section Validation → Processing
Gateway Controller → Bus → evidence.new → Other Components
Gateway Controller → Bus → section.needs → Other Components
```

### **Problems:**
- **Wrong signal names** (gateway_controller.* instead of gateway.*)
- **Direct ECC communication** bypasses CAN-bus
- **Inconsistent with CAN-bus registry**

## 3. **ECC (Ecosystem Controller) Communication Model**

### **Current Callouts:**
```python
# ECC Signal Emissions
"section.data.updated"      # Section data updates
"gateway.section.complete"  # Section completion
"mission.status"            # Mission status updates
"section.activate"          # Section activation
```

### **Communication Flow:**
```
ECC → Bus → section.data.updated → All Components
ECC → Bus → mission.status → All Components
ECC → Bus → section.activate → Target Sections
```

### **Problems:**
- **Limited signal emissions** (missing many handlers)
- **Not listening to component signals** (no handlers registered)
- **Missing CAN-bus integration** for component communication

## 4. **Mission Debrief Manager Communication Model**

### **Current Callouts:**
```python
# Mission Debrief Signal Emissions
"mission_debrief_manager.call_out" # Call-out signals (WRONG NAME)
"mission_debrief_manager.accept"   # Accept signals (WRONG NAME)
"mission_debrief.digital_sign"     # Digital signing
"mission_debrief.print_report"     # Report printing
"mission_debrief.apply_template"   # Template application
"mission_debrief.add_watermark"    # Watermark addition
"mission_debrief.osint_lookup"     # OSINT lookups
"mission_debrief.process_report"   # Report processing
"review.section_summary"           # Section summaries
"review.case_status"               # Case status
```

### **Communication Flow:**
```
Mission Debrief → ECC (direct) → Permission → Report Generation
Mission Debrief → Bus → review.section_summary → Analyst Deck
Mission Debrief → Bus → mission_debrief.* → Specific Handlers
```

### **Problems:**
- **Wrong signal names** (mission_debrief_manager.* instead of mission.*)
- **Direct ECC communication** bypasses CAN-bus
- **Inconsistent with CAN-bus registry**

## 5. **Analyst Deck Communication Model**

### **Current Callouts:**
```python
# Analyst Deck Signal Emissions
"section_8_evidence.completed"     # Section 8 completion
"section_8_ready"                  # Section 8 ready
"evidence_ready"                   # Evidence ready
"section_4_review.completed"       # Section 4 review completion
"evidence_revision_requested"      # Evidence revision requests
```

### **Communication Flow:**
```
Analyst Deck → Gateway → section_8_ready → Other Components
Analyst Deck → Gateway → evidence_ready → Other Components
Analyst Deck → Gateway → evidence_revision_requested → Evidence Locker
```

### **Problems:**
- **Gateway communication** instead of direct CAN-bus
- **Section-specific signal names** (not standardized)
- **Inconsistent with CAN-bus registry**

## 6. **Narrative Assembler Communication Model**

### **Current Callouts:**
```python
# Narrative Assembler Signal Emissions
"narrative.assembled"       # Narrative assembly completion
```

### **Communication Flow:**
```
Narrative Assembler → Bus → narrative.assembled → Mission Debrief
```

### **Problems:**
- **Only one signal emission** (limited communication)
- **Missing integration** with other components

## **CAN-Bus Registry (Expected Signals):**

```python
# CAN-Bus Registry (bus_core.py)
default_handlers = {
    'case_create': '_handle_case_create_signal',
    'files_add': '_handle_files_add_signal',
    'evidence.new': '_handle_evidence_new_signal',
    'evidence.annotated': '_handle_evidence_annotated_signal',
    'evidence.request': '_handle_evidence_request_signal',
    'evidence.deliver': '_handle_evidence_deliver_signal',
    'evidence.updated': '_handle_evidence_updated_signal',
    'evidence.tagged': '_handle_evidence_tagged_signal',
    'evidence.stored': '_handle_evidence_stored_signal',
    'evidence_locker.call_out': '_handle_evidence_call_out_signal',
    'evidence_locker.accept': '_handle_evidence_accept_signal',
    'section.needs': '_handle_section_needs_signal',
    'case.snapshot': '_handle_case_snapshot_signal',
    'gateway.status': '_handle_gateway_status_signal',
    'locker.status': '_handle_locker_status_signal',
    'mission.status': '_handle_mission_status_signal',
    'narrative.assembled': '_handle_narrative_assembled_signal',
}
```

## **Communication Breakdown Analysis:**

### **Signal Name Mismatches:**
| Component | Uses | CAN-Bus Registry | Status |
|-----------|------|------------------|---------|
| Evidence Locker | `evidence_locker.call_out` | `evidence_locker.call_out` | ✅ MATCHES |
| Evidence Locker | `evidence_locker.accept` | `evidence_locker.accept` | ✅ MATCHES |
| Gateway Controller | `gateway_controller.call_out` | `gateway.status` | ❌ MISMATCH |
| Gateway Controller | `gateway_controller.accept` | `gateway.status` | ❌ MISMATCH |
| Mission Debrief | `mission_debrief_manager.call_out` | `mission.status` | ❌ MISMATCH |
| Mission Debrief | `mission_debrief_manager.accept` | `mission.status` | ❌ MISMATCH |
| ECC | `section.data.updated` | `section.needs` | ❌ MISMATCH |
| ECC | `gateway.section.complete` | `gateway.status` | ❌ MISMATCH |
| Analyst Deck | `section_8_ready` | `section.needs` | ❌ MISMATCH |
| Narrative Assembler | `narrative.assembled` | `narrative.assembled` | ✅ MATCHES |

### **Communication Method Mismatches:**
| Component | Method | Should Use |
|-----------|--------|------------|
| Evidence Locker | Direct ECC + Bus | `bus.emit()` only |
| Gateway Controller | Direct ECC + Bus | `bus.emit()` only |
| ECC | Bus only | `bus.emit()` + `bus.register_signal()` |
| Mission Debrief | Direct ECC + Bus | `bus.emit()` only |
| Analyst Deck | Gateway + Bus | `bus.emit()` only |
| Narrative Assembler | Bus only | ✅ CORRECT |

## **Unified Communication Model (Required):**

### **Standard Signal Names:**
```python
# UNIFIED SIGNAL NAMES (matching CAN-bus registry)
UNIFIED_SIGNALS = {
    # Evidence Signals
    'evidence.new': 'evidence.new',
    'evidence.updated': 'evidence.updated',
    'evidence.stored': 'evidence.stored',
    'evidence.tagged': 'evidence.tagged',
    'evidence.request': 'evidence.request',
    'evidence.deliver': 'evidence.deliver',
    
    # Component Status Signals
    'evidence_locker.call_out': 'evidence_locker.call_out',
    'evidence_locker.accept': 'evidence_locker.accept',
    'gateway.status': 'gateway.status',
    'mission.status': 'mission.status',
    'locker.status': 'locker.status',
    
    # Section Signals
    'section.needs': 'section.needs',
    'section.data.updated': 'section.data.updated',
    'section.activate': 'section.activate',
    
    # Case Signals
    'case.create': 'case_create',
    'case.snapshot': 'case.snapshot',
    
    # Narrative Signals
    'narrative.assembled': 'narrative.assembled',
    
    # File Signals
    'files.add': 'files_add',
    'files.process': 'files_process',
}
```

### **Unified Communication Flow:**
```
Evidence Locker → CAN-Bus → evidence.stored → All Components
Evidence Locker → CAN-Bus → evidence_locker.call_out → ECC Handler
ECC → CAN-Bus → section.activate → Target Sections
Gateway Controller → CAN-Bus → gateway.status → All Components
Mission Debrief → CAN-Bus → mission.status → All Components
Analyst Deck → CAN-Bus → section.needs → All Components
Narrative Assembler → CAN-Bus → narrative.assembled → Mission Debrief
```

### **Unified Communication Method:**
```python
# ALL components must use this pattern
def communicate(self, signal: str, payload: Dict[str, Any]) -> None:
    """Unified communication method for all components"""
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

## **Implementation Requirements:**

### **1. Evidence Locker:**
- ✅ Keep: `evidence.stored`, `evidence.tagged`
- ✅ Keep: `evidence_locker.call_out`, `evidence_locker.accept`
- ❌ Remove: Direct ECC communication
- ✅ Add: `locker.status` signal

### **2. Gateway Controller:**
- ❌ Change: `gateway_controller.call_out` → `gateway.status`
- ❌ Change: `gateway_controller.accept` → `gateway.status`
- ❌ Remove: Direct ECC communication
- ✅ Keep: `evidence.new`, `evidence.updated`, `section.needs`

### **3. ECC:**
- ✅ Keep: `section.data.updated`, `mission.status`
- ✅ Add: Signal handlers for all component signals
- ✅ Add: `section.activate` signal

### **4. Mission Debrief:**
- ❌ Change: `mission_debrief_manager.call_out` → `mission.status`
- ❌ Change: `mission_debrief_manager.accept` → `mission.status`
- ❌ Remove: Direct ECC communication
- ✅ Keep: `mission_debrief.*` signals

### **5. Analyst Deck:**
- ❌ Change: `section_8_ready` → `section.needs`
- ❌ Change: `evidence_ready` → `evidence.deliver`
- ❌ Remove: Gateway communication
- ✅ Add: Direct CAN-bus communication

### **6. Narrative Assembler:**
- ✅ Keep: `narrative.assembled`
- ✅ Add: More signal emissions for better integration

## **Current State:**
- ❌ **Signal names inconsistent** across components
- ❌ **Communication methods mixed** (direct + bus)
- ❌ **No unified language** for inter-component communication
- ❌ **Large break in process** due to communication mismatch

## **Impact:**
- **Signals never reach handlers** due to name mismatch
- **Components bypass CAN-bus** due to method mismatch
- **No centralized communication** due to language mismatch
- **Process completely broken** due to communication breakdown

## **Fix Priority: CRITICAL**
The entire communication system is broken due to language inconsistency. All components must be standardized to use the same language, signal names, and communication methods.

## **Implementation Plan:**
1. **Standardize all signal names** to match CAN-bus registry
2. **Standardize all communication methods** to use CAN-bus only
3. **Standardize all payload formats** using shared_interfaces
4. **Update all components** to use unified language
5. **Test end-to-end communication** with standardized language
6. **Verify all signals reach handlers** with correct names and formats

This will fix the **large break in the process** and restore **unified communication** across all components.

---

## **Usage Instructions:**

This README serves as the **master communication architecture document** for the Central Command system. All developers and system integrators should:

1. **Reference this document** before implementing any new communication patterns
2. **Follow the unified signal names** exactly as specified
3. **Use only CAN-bus communication** methods
4. **Implement standardized payload formats** using shared_interfaces
5. **Test all communication** against this model

## **Maintenance:**

This document should be updated whenever:
- New components are added to the system
- New signal types are introduced
- Communication patterns change
- CAN-bus registry is modified

## **Related Documents:**

- `shared_interfaces.py` - Standardized payload formats
- `bus_core.py` - CAN-bus implementation
- `COMPONENT_COMMUNICATION_STANDARDS_2025-10-04.md` - Implementation details
- `COMMUNICATION_ARCHITECTURE_ANALYSIS_2025-10-05.md` - Detailed analysis

