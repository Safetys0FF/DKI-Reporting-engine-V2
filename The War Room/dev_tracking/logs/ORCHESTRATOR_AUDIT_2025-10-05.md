# Orchestrator Communication Audit
## Date: October 5, 2025

## Executive Summary
Evidence Locker and Gateway Controller are the system's orchestrators. They manage evidence flow and section coordination but use inconsistent communication patterns. This audit identifies what needs standardization.

## Current Communication Patterns

### Gateway Controller (`gateway_controller.py`)
**Signal Emission Method:** `_emit_bus_event(signal: str, payload: Dict[str, Any])`
- Located at lines 263-272
- Emits signals via bus if available
- Adds source="gateway_controller" and timestamp to all signals

**Current Signals Emitted:**
1. `section.needs` - When evidence is classified for a section (line 796)
2. `section.data.updated` - When section output is finalized (line 570)
3. `gateway.section.complete` - When section completes (line 571)
4. `evidence.deliver` - When evidence is delivered to section (line 433)
5. `evidence.request` - When section requests evidence (line 471)

**ECC Communication:**
- Direct `self.ecosystem_controller.emit()` calls for bottleneck alerts (line 682)
- No ECC bypass mechanism - assumes ECC always available
- Hard dependency on ECC for section validation

### Evidence Locker (`evidence_locker_main.py`)
**Signal Emission Method:** Direct `self.ecc.emit()` calls
- No standardized wrapper method
- Scattered throughout codebase
- Example at line 3030: `self.ecc.emit("evidence_locker.send", {...})`

**Current Signals Emitted:**
1. `evidence_locker.send` - Generic operation signal
2. Direct handoffs to Gateway Controller via `_handoff_to_gateway()` (line 8071)

**ECC Communication:**
- Direct ECC emit calls throughout
- No ECC bypass mechanism - hard dependency
- Tight coupling to ECC availability

## Identified Issues

### 1. **No ECC Bypass in Orchestrators**
Both Gateway and Evidence Locker assume ECC is always available. If ECC is down or unavailable during initialization, they cannot function. This creates a single point of failure.

**Impact:** System crashes when ECC unavailable
**Solution:** Implement headless mode like Mission Debrief Manager

### 2. **Inconsistent Signal Formats**
- Gateway uses `_emit_bus_event` wrapper
- Evidence Locker uses direct `ecc.emit()` calls
- No standard payload structure
- No validation of signal contracts

**Impact:** Components receive unpredictable data formats
**Solution:** Use `shared_interfaces.py` for all signals

### 3. **No Standard Evidence Payload**
Evidence data is passed with varying structures:
- `evidence_id` vs `artifact_id`
- `file_path` vs `path`
- Inconsistent metadata fields

**Impact:** Components must handle multiple formats
**Solution:** Use `StandardEvidenceData` from shared_interfaces

### 4. **No Standard Section Communication**
Section data transfers use varying formats:
- `section_id` vs `section` vs `target`
- Different payload structures
- No status standardization

**Impact:** Section modules receive inconsistent data
**Solution:** Use `StandardSectionData` and `create_standard_section_signal`

### 5. **Handoff Protocol Complexity**
Gateway has elaborate Evidence Locker handoff system (lines 595-685) with:
- Module tracking
- Bottleneck detection
- Status management

But no standard format for handoff data.

**Impact:** Hard to extend or modify handoff logic
**Solution:** Standardize handoff payloads

## Standardization Requirements

### Phase 1: Add ECC Bypass (CRITICAL)
Both orchestrators need headless operation capability:

**Gateway Controller:**
```python
def _emit_bus_event(self, signal: str, payload: Dict[str, Any]) -> None:
    if not self.bus:
        self.logger.warning(f"Bus not available - cannot emit {signal}")
        return
    
    envelope = dict(payload or {})
    envelope.setdefault("source", "gateway_controller")
    envelope.setdefault("timestamp", datetime.now().isoformat())
    
    try:
        self.bus.emit(signal, envelope)
    except Exception as exc:
        self.logger.warning(f"Failed to emit {signal} via bus: {exc}")
        # Continue operation - don't crash

def _call_out_to_ecc(self, operation: str, data: Dict[str, Any]) -> bool:
    """Call out to ECC with bypass for headless mode"""
    if not self.ecosystem_controller:
        self.logger.info(f"ECC not available - operating in headless mode for {operation}")
        return True  # Allow operation to proceed
    
    # Normal ECC call-out logic...
```

**Evidence Locker:**
```python
def _emit_signal(self, signal: str, payload: Dict[str, Any]) -> None:
    """Emit signal with ECC bypass"""
    if not self.ecc:
        self.logger.info(f"ECC not available - operating in headless mode for {signal}")
        return
    
    envelope = dict(payload or {})
    envelope.setdefault("source", "evidence_locker")
    envelope.setdefault("timestamp", datetime.now().isoformat())
    
    try:
        self.ecc.emit(signal, envelope)
    except Exception as exc:
        self.logger.warning(f"Failed to emit {signal}: {exc}")
        # Continue operation
```

### Phase 2: Standardize Evidence Signals
Use `StandardEvidenceData` for all evidence communication:

```python
from shared_interfaces import StandardEvidenceData, create_standard_evidence_signal

# In Evidence Locker
evidence_payload = StandardEvidenceData(
    evidence_id=evidence_id,
    filename=filename,
    file_path=file_path,
    classification=classification,
    assigned_section=section_hint
).to_dict()

self._emit_signal("evidence.classified", evidence_payload)
```

### Phase 3: Standardize Section Signals
Use `create_standard_section_signal` for section communication:

```python
from shared_interfaces import create_standard_section_signal, SectionStatus

# In Gateway Controller
section_signal = create_standard_section_signal(
    section_id=section_id,
    case_id=case_id,
    payload=enriched_payload,
    status=SectionStatus.COMPLETE,
    source="gateway_controller"
)

self._emit_bus_event("section.data.updated", section_signal)
```

### Phase 4: Add Signal Validation
Validate all outgoing signals:

```python
from shared_interfaces import validate_signal_payload

def _emit_bus_event(self, signal: str, payload: Dict[str, Any]) -> None:
    # Validate before emitting
    if not validate_signal_payload(signal, payload):
        self.logger.error(f"Invalid payload for signal {signal}")
        return
    
    # Normal emit logic...
```

## Implementation Priority

1. **CRITICAL:** Add ECC bypass to both orchestrators
2. **HIGH:** Standardize evidence payload format  
3. **HIGH:** Standardize section payload format
4. **MEDIUM:** Add signal validation
5. **LOW:** Refactor handoff protocol

## Expected Benefits

- **Reliability:** System operates even if ECC unavailable
- **Consistency:** All components receive predictable data
- **Maintainability:** Single source of truth for data formats
- **Extensibility:** Easy to add new signal types
- **Debugging:** Validation catches format errors early

## Next Steps

1. Import `shared_interfaces` into both modules
2. Add `_call_out_to_ecc` bypass method to Gateway
3. Add `_emit_signal` wrapper to Evidence Locker
4. Refactor signal emissions to use standard payloads
5. Add validation to all signal emissions
6. Test headless operation mode
7. Document new communication contracts


