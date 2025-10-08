# ECC Controller Architecture Analysis
## Date: October 5, 2025

## Executive Summary
The ECC (Ecosystem Controller) consists of two controllers working together:
1. **Ecosystem Controller** (`ecosystem_controller_og.txt`) - ROOT BOOT NODE
2. **Gateway Controller** (`gateway_controller.py`) - DEFERS TO ECOSYSTEM CONTROLLER

## Architecture Overview

### Ecosystem Controller (ROOT BOOT NODE)
**Role:** Master orchestrator for section lifecycle and execution order
**Key Responsibilities:**
- Manages section contracts and dependencies
- Controls execution order (topological sort)
- Validates section IDs and enforces gateway checks
- Tracks completed/failed ecosystems
- Manages revision requests and limits
- Freezes completed section data (immutable)

**Key Methods:**
- `can_run(section_id)` - Master permission gate
- `mark_complete(section_id)` - Finalizes section completion
- `is_case_exportable()` - Hard gate for report generation
- `execute_ecosystem()` - Runs individual sections
- `request_revision()` - Handles section revisions

### Gateway Controller (DEFERS TO ECC)
**Role:** Evidence pipeline orchestrator and section communication mediator
**Key Responsibilities:**
- Owns master evidence index
- Manages OCR processing and content classification
- Routes evidence through pipeline
- Mediates section-to-section communication
- Tracks Evidence Locker handoffs
- Processes document pipeline

**Key Methods:**
- `can_run(section_id)` - **DEFERS TO ECOSYSTEM CONTROLLER**
- `mark_complete(section_id)` - **DEFERS TO ECOSYSTEM CONTROLLER**
- `transfer_section_data()` - Section data publishing
- `process_document_pipeline()` - OCR and classification
- `orchestrate_section_processing()` - Section execution coordination

## Controller Relationship

### 1. **Ecosystem Controller is ROOT BOOT NODE**
```python
# Gateway Controller initialization
def __init__(self, ecosystem_controller=None, bus=None):
    # Reference to Ecosystem Controller (ROOT BOOT NODE)
    self.ecosystem_controller = ecosystem_controller
```

### 2. **Gateway DEFERS ALL SECTION EXECUTION PERMISSION TO ECC**
```python
def can_run(self, section_id: str) -> bool:
    """DEFERS TO ECOSYSTEM CONTROLLER - Only allows progression if logic passes"""
    if self.ecosystem_controller:
        return self.ecosystem_controller.can_run(section_id)
```

### 3. **ECC Validates Gateway Operations**
```python
def enforce_gateway_check(self, section_id: str, source: str):
    """Enforce Gateway validation for public entry points"""
    # Special case: "gateway" is the Marshall/Gateway Controller, not a section
    if section_id == "gateway":
        return  # Allow gateway access without validation
```

## Current Communication Flow

### Evidence Processing Flow
1. **Evidence Locker** scans evidence parcels
2. **ECC** designates whether tags/classifications are correct
3. **Gateway Controller** moves evidence through pipeline on section-aware path
4. **One section operates at a time** utilizing all evidence payloads

### Section Execution Flow
1. **Gateway** requests permission via `can_run(section_id)`
2. **ECC** validates dependencies and execution order
3. **ECC** grants/denies permission
4. **Gateway** orchestrates section processing if approved
5. **Gateway** reports completion via `mark_complete(section_id)`
6. **ECC** freezes section data and updates state

## Standardization Requirements

### Phase 1: Add ECC Bypass to Gateway Controller
Gateway Controller needs headless operation capability:

```python
def can_run(self, section_id: str) -> bool:
    """DEFERS TO ECOSYSTEM CONTROLLER with bypass"""
    try:
        # DEFER TO ECOSYSTEM CONTROLLER (ROOT BOOT NODE)
        if self.ecosystem_controller:
            return self.ecosystem_controller.can_run(section_id)
        
        # ECC bypass for headless operation
        self.logger.info(f"ECC not available - operating in headless mode for {section_id}")
        # Basic fallback logic for headless operation
        return section_id in self.section_cache and self.section_cache[section_id].get('data')
        
    except Exception as e:
        self.logger.error(f"Failed to check can_run for {section_id}: {e}")
        return False
```

### Phase 2: Standardize Signal Emissions
Both controllers need standardized communication:

**Gateway Controller:**
```python
def _emit_bus_event(self, signal: str, payload: Dict[str, Any]) -> None:
    """Emit signal with validation and bypass"""
    if not self.bus:
        self.logger.warning(f"Bus not available - cannot emit {signal}")
        return
    
    # Validate signal payload
    if not validate_signal_payload(signal, payload):
        self.logger.error(f"Invalid payload for signal {signal}")
        return
    
    envelope = dict(payload or {})
    envelope.setdefault("source", "gateway_controller")
    envelope.setdefault("timestamp", datetime.now().isoformat())
    
    try:
        self.bus.emit(signal, envelope)
    except Exception as exc:
        self.logger.warning(f"Failed to emit {signal} via bus: {exc}")
```

**Ecosystem Controller:**
```python
def _emit_status_update(self, *, reason: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Emit status update with validation"""
    if not self.bus:
        self.logger.warning("Bus not available - cannot emit status update")
        return
    
    payload = {
        "reason": reason,
        "timestamp": datetime.now().isoformat(),
        "section_states": dict(self.section_states),
        "completed_sections": list(self.completed_ecosystems),
        "active_sections": list(self.active_sections),
    }
    if context:
        payload["context"] = context
    
    # Validate payload
    if not validate_signal_payload("mission.status", payload):
        self.logger.error("Invalid payload for mission.status")
        return
    
    self.latest_mission_status = payload
    try:
        self.bus.emit("mission.status", payload)
    except Exception as exc:
        logger.warning("Failed to emit mission.status: %s", exc)
```

### Phase 3: Add Standardized Evidence Signals
Use `StandardEvidenceData` for evidence communication:

```python
from shared_interfaces import StandardEvidenceData, create_standard_evidence_signal

# In Gateway Controller evidence processing
evidence_payload = StandardEvidenceData(
    evidence_id=evidence_id,
    filename=filename,
    file_path=file_path,
    classification=classification,
    assigned_section=section_hint
).to_dict()

self._emit_bus_event("evidence.classified", evidence_payload)
```

### Phase 4: Add Standardized Section Signals
Use `create_standard_section_signal` for section communication:

```python
from shared_interfaces import create_standard_section_signal, SectionStatus

# In Gateway Controller section completion
section_signal = create_standard_section_signal(
    section_id=section_id,
    case_id=case_id,
    payload=enriched_payload,
    status=SectionStatus.COMPLETE,
    source="gateway_controller"
)

self._emit_bus_event("section.data.updated", section_signal)
```

## Implementation Priority

1. **CRITICAL:** Add ECC bypass to Gateway Controller
2. **HIGH:** Standardize Gateway Controller signal emissions
3. **HIGH:** Standardize Ecosystem Controller signal emissions
4. **MEDIUM:** Add signal validation to both controllers
5. **LOW:** Refactor handoff protocols

## Expected Benefits

- **Reliability:** System operates even if ECC unavailable
- **Consistency:** All components receive predictable data
- **Maintainability:** Single source of truth for data formats
- **Extensibility:** Easy to add new signal types
- **Debugging:** Validation catches format errors early

## Next Steps

1. Add ECC bypass to Gateway Controller `can_run()` and `mark_complete()`
2. Import `shared_interfaces` into both controllers
3. Refactor signal emissions to use standard payloads
4. Add validation to all signal emissions
5. Test headless operation mode
6. Document new communication contracts

## Key Architecture Principle

**ECC is the ROOT BOOT NODE** - Gateway Controller DEFERS TO ECOSYSTEM CONTROLLER for all section execution decisions. ECC manages the master execution order and dependencies, while Gateway orchestrates the evidence pipeline and section communication.

