# CENTRAL COMMAND - SYSTEM BLUEPRINT
## Technical Design Specifications

**Version:** 1.0 (Current Build 2025-10-12)  
**Status:** CURRENT  
**Audience:** Architects, Senior Developers  
**Document Type:** Technical Blueprint

---

## DESIGN PHILOSOPHY

Central Command implements a **loosely coupled, event-driven architecture** with the following core principles:

1. **Signal-Based Communication:** All inter-module communication via pub/sub signals
2. **Parent-Child Delegation:** Parents own children, test children, report for children
3. **Message Lifecycle:** Strict request/response semantics prevent infinite loops
4. **Fault-First Design:** Every error condition mapped to fault code
5. **Dual-Bus Separation:** Data (CANBUS) vs. orchestration (LINBUS)

---

## ARCHITECTURE PATTERNS

### Pattern 1: Parent Module Template

All parent modules follow this standardized structure:

```python
class ParentModule:
    """Base pattern for all parent modules"""
    
    def __init__(self, bus, communicator):
        self.bus = bus
        self.communicator = communicator
        self.system_address = "ADDRESS"
        self.bus_connected = False
        self.child_components = []
        
        self._initialize_children()
        self._register_handlers()
        self._initialize_canbus()
    
    def _initialize_children(self):
        """Create child component instances"""
        pass
    
    def _register_handlers(self):
        """Register signal handlers with bus"""
        self.bus.register_signal("auto_registration", self._handle_auto_registration)
        self.bus.register_signal("radio_check", self._handle_radio_check)
    
    def _handle_auto_registration(self, payload):
        """Respond only to CALL_SENT"""
        if payload.get('message_state') != 'CALL_SENT':
            return
        response = self._build_registration_response()
        self.communicator.send_auto_registration_response("DIAG-1", response)
    
    def _run_startup_self_test(self):
        """Test all children, emit fault codes, send completion"""
        for child in self.child_components:
            if not child.test():
                self._emit_fault_code(f"{child.address}.00")
        self._send_completion_signal()
```

---

### Pattern 2: Universal Communicator Protocol

Standardized communication layer for all modules:

```python
class UniversalCommunicator:
    """Standardized communication wrapper"""
    
    def __init__(self, bus_connection, system_address):
        self.bus = bus_connection
        self.address = system_address
    
    def _send_on_topic(self, topic, target, radio_code, message, payload, message_state="CALL_SENT"):
        """Core send method with lifecycle state"""
        data = {
            'source_address': self.address,
            'target_address': target,
            'radio_code': radio_code,
            'message': message,
            'payload': payload,
            'message_state': message_state,
            'timestamp': datetime.now().isoformat()
        }
        return self.bus.send(topic, data)
    
    def send_auto_registration_response(self, target, metadata):
        """Send registration response with CALL_ANSWERED state"""
        return self._send_on_topic(
            topic="auto_registration",
            target=target,
            radio_code="10-4",
            message="Auto-registration response",
            payload=metadata,
            message_state="CALL_ANSWERED"
        )
```

---

### Pattern 3: Signal-Based Bus Architecture

```python
class DKIReportBus:
    """CANBUS implementation"""
    
    def __init__(self):
        self.signal_registry = {}  # topic → [handlers]
        self.address_registry = {}  # address → metadata
        self.event_logger = EventLogger()
        self.state_manager = StateManager()
    
    def register_signal(self, topic, handler):
        """Subscribe handler to topic"""
        if topic not in self.signal_registry:
            self.signal_registry[topic] = []
        self.signal_registry[topic].append(handler)
    
    def send(self, topic, data):
        """Route signal to subscribers with parent filtering"""
        target_address = data.get('target_address')
        
        # Parent-only filtering
        if target_address and target_address not in PARENT_MODULES:
            logger.debug(f"Skipping child address {target_address}")
            return {}
        
        # Dispatch to handlers
        responses = []
        for handler in self.signal_registry.get(topic, []):
            try:
                response = handler(data)
                responses.append(response)
            except Exception as e:
                logger.error(f"Handler error: {e}")
                self._emit_fault(f"Bus-1.10", str(e))
        
        # Log transaction
        self.event_logger.log(topic, data, responses)
        
        return responses
```

---

## DATA MODELS

### Case Manifest Schema

```json
{
  "case_id": "CASE-2025-001",
  "case_name": "Investigation Title",
  "created_date": "2025-10-12T14:30:00",
  "investigator": "Operator Name",
  "status": "processing",
  "evidence": [
    {
      "evidence_id": "EVD-001",
      "filename": "document.pdf",
      "file_type": "document",
      "file_size_bytes": 1048576,
      "upload_date": "2025-10-12T14:35:00",
      "classification": {
        "primary_type": "pdf_document",
        "keywords": ["contract", "agreement", "signature"],
        "section_relevance": {
          "4-3": 85,
          "4-4": 95,
          "4-6": 70
        }
      },
      "file_path": "intake/CASE-2025-001/document.pdf",
      "checksum_sha256": "abc123..."
    }
  ],
  "target_sections": ["4-1", "4-3", "4-4", "4-6"],
  "processing_start": "2025-10-12T14:40:00",
  "processing_end": null
}
```

### System Registry Schema

```json
{
  "systems": [
    {
      "system_address": "1",
      "system_name": "Evidence Locker Main",
      "system_type": "evidence_management",
      "parent_address": "1",
      "child_addresses": ["1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7", "1.8"],
      "communication_mode": "parent",
      "capabilities": ["evidence_ingestion", "classification", "indexing"],
      "fault_code_range": "1.00-1.99",
      "protocol_version": "1.0.0",
      "status": "OPERATIONAL",
      "last_registration": "2025-10-12T10:00:00"
    }
  ]
}
```

### Fault Code Schema

```json
{
  "fault_code": "1.10",
  "module_address": "1",
  "module_name": "Evidence Locker",
  "fault_description": "Evidence ingestion failure",
  "severity": "ERROR",
  "timestamp": "2025-10-12T15:00:00",
  "details": {
    "filename": "corrupted_file.pdf",
    "error_message": "File integrity check failed",
    "recovery_attempted": true,
    "recovery_successful": false
  }
}
```

---

## COMMUNICATION PROTOCOLS

### Message Lifecycle States

```python
class MessageState:
    CALL_SENT = "CALL_SENT"          # Request initiated
    CALL_RECEIVED = "CALL_RECEIVED"  # ACK received (optional)
    CALL_ANSWERED = "CALL_ANSWERED"  # Response data sent
    CALL_COMPLETED = "CALL_COMPLETED" # Confirmation (optional)
```

### Radio Codes (10-Code System)

| Code | Meaning | Usage |
|------|---------|-------|
| 10-4 | Acknowledged | Request received and understood |
| 10-6 | Busy | System busy, retry later |
| 10-20 | Location | Address/location information |
| 10-36 | Correct time | Timestamp validation |
| 10-77 | ETA | Estimated completion time |

### Signal Topics

| Topic | Purpose | Subscribers |
|-------|---------|-------------|
| `case_create` | New case initialization | Evidence Locker, Warden |
| `files_add` | Evidence upload | Evidence Locker |
| `evidence_ready` | Evidence classified | Warden, Marshall |
| `section.wake` | Wake Analyst section | Marshall |
| `section.complete` | Section finished | Marshall, Warden, Mission Debrief |
| `narrative.assembled` | Report complete | GUI, Library |
| `auto_registration` | UDS protocol | All parent modules |
| `radio_check` | Health check | All parent modules |
| `rollcall` | Presence check | All modules |
| `sos_fault` | Critical fault | UDS |

---

## API SPECIFICATIONS

### UniversalCommunicator API

```python
# Initialization
communicator = UniversalCommunicator(bus_connection, system_address)

# Send signal
communicator.send_signal(
    topic="evidence_ready",
    target_address="2-1",
    message="Evidence classification complete",
    payload={"case_id": "CASE-001", "evidence_count": 50}
)

# Send auto-registration response
communicator.send_auto_registration_response(
    target_address="DIAG-1",
    metadata={
        "system_address": "1",
        "system_type": "evidence_management",
        "status": "OPERATIONAL",
        "capabilities": [...],
        "child_components": [...]
    }
)

# Send radio check response
communicator.send_radio_check_response(
    target_address="DIAG-1",
    connectivity_data={
        "system_address": "1",
        "latency_ms": 5,
        "bus_connected": True
    }
)

# Send fault code
communicator.send_fault_code(
    fault_code="1.10",
    details={"error": "Ingestion failed", "file": "corrupt.pdf"}
)
```

### Bus Core API

```python
# Initialize bus
bus = DKIReportBus()

# Register signal handler
def my_handler(payload):
    print(f"Received: {payload}")
    return {"status": "processed"}

bus.register_signal("my_topic", my_handler)

# Send signal
bus.send("my_topic", {
    "target_address": "1",
    "message_state": "CALL_SENT",
    "payload": {"data": "value"}
})

# Register system address
bus.register_system_address("1", {
    "system_name": "Evidence Locker",
    "capabilities": [...]
})

# Get case state
case_data = bus.get_case_state("CASE-001")

# Update case state
bus.update_case_state("CASE-001", {"status": "processing"})
```

---

## THREADING MODEL

### Main Thread
- GUI event loop (Tkinter mainloop)
- User interaction handling

### Bus Thread
- Signal dispatching
- Handler execution
- Event logging

### Module Threads
- Evidence classification (Evidence Locker)
- Section processing (Analyst Deck)
- Report generation (Mission Debrief)

### Thread Safety
- Bus operations use thread-safe queues
- State manager uses locks for shared data
- Event logger uses thread-safe file I/O

---

## ERROR HANDLING STRATEGY

### Level 1: Component-Level Recovery
```python
def process_evidence(file_path):
    try:
        evidence = load_evidence(file_path)
        classify(evidence)
    except CorruptFileError:
        emit_fault_code("1.13", {"file": file_path})
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        emit_fault_code("1.03", {"error": str(e)})
        return None
```

### Level 2: Module-Level Recovery
```python
def _run_startup_self_test(self):
    failures = []
    for child in self.child_components:
        try:
            if not child.test():
                fault_code = f"{child.address}.00"
                self._emit_fault_code(fault_code)
                failures.append(child.address)
        except Exception as e:
            logger.error(f"Test failed: {e}")
            self._emit_fault_code("1.03", {"child": child.address})
    
    # Report aggregate status
    if failures:
        self._send_completion_signal(status="DEGRADED", failures=failures)
    else:
        self._send_completion_signal(status="OPERATIONAL")
```

### Level 3: System-Level Recovery
- UDS monitors fault codes
- Critical faults halt system
- ERROR-level faults trigger retry logic
- WARNING-level faults logged but continue

---

## SECURITY CONSIDERATIONS

### Authentication
- Operator profiles stored in `profile_registry.db`
- Token-based authentication (auth_manager.py)
- Session management

### Data Protection
- Evidence files stored with restricted permissions
- Case manifests encrypted at rest (future)
- Audit trail for all evidence access

### Network Security
- CANBUS/LINBUS internal-only (no external exposure)
- No remote access in current build
- File system access restricted to application

---

## PERFORMANCE SPECIFICATIONS

### Throughput
- Evidence upload: ≥ 10 MB/s
- CANBUS signal latency: ≤ 100 ms
- Evidence classification: ≤ 10 seconds per file

### Concurrency
- Concurrent cases: 10
- Concurrent evidence uploads: 5
- Concurrent section processing: 8 (all Analyst sections)

### Resource Limits
- Maximum evidence per case: 500 files
- Maximum evidence file size: 2 GB
- Memory footprint: ≤ 2 GB under normal load

---

## DEPLOYMENT ARCHITECTURE

### Current Build (Desktop)
```
Windows 10/11
├─ Python 3.11+
├─ Tkinter (GUI)
├─ CANBUS (in-process)
└─ LINBUS (in-process)
```

### Future: Distributed Architecture
```
Server Layer
├─ CANBUS Server
├─ Evidence Locker Service
├─ Processing Service (Analyst Deck)
└─ Database Server

Client Layer
├─ Web GUI (React)
└─ API Gateway
```

---

## EXTENSIBILITY

### Adding New Parent Module

1. Create module class following Parent Module Template
2. Implement required handlers (`_handle_auto_registration`, `_handle_radio_check`)
3. Implement `_run_startup_self_test()`
4. Assign unique address (coordinate with registry)
5. Define fault code range
6. Update `PARENT_CHILD_RELATIONSHIPS` in `system_protocol_registry.py`
7. Update `PARENT_MODULES` set in `bus_core.py`
8. Update UDS `expected_modules` and `parent_modules` lists

### Adding New Signal Type

1. Define signal topic name (e.g., `my_new_signal`)
2. Register handler in modules that should receive it
3. Document signal payload schema
4. Update signal registry documentation

### Adding New Child Component

1. Create component class
2. Assign address under parent (e.g., 1.9 for Evidence Locker child)
3. Parent instantiates child in `_initialize_children()`
4. Parent tests child in `_run_startup_self_test()`
5. Update parent's `PARENT_CHILD_RELATIONSHIPS` entry
6. Define child fault code range

---

## TESTING STRATEGY

### Unit Testing
- Each module tested in isolation
- Mock bus and communicator dependencies
- Test all handler functions

### Integration Testing
- Test module-to-module communication
- Validate signal routing
- Test fault code propagation

### System Testing
- End-to-end case processing
- UDS baseline testing
- Performance testing under load

### Acceptance Testing
- User workflow validation
- Report quality verification
- Operator training validation

---

## TECHNICAL DEBT AND FUTURE IMPROVEMENTS

### Known Technical Debt
1. **Permissive Self-Tests:** Tests check existence, not functionality
2. **JSON-Based Registry:** Should migrate to SQL database for scalability
3. **Synchronous Processing:** Sections process sequentially (should be parallel)
4. **Limited Error Recovery:** Many operations don't retry on failure
5. **Hard-Coded Paths:** File paths not fully configurable

### Planned Improvements
1. Implement functional validation in all self-tests
2. Migrate to PostgreSQL for evidence indexing
3. Implement async section processing (parallel Analyst sections)
4. Add retry logic with exponential backoff
5. Externalize configuration to YAML files
6. Implement comprehensive logging framework
7. Add performance metrics collection
8. Implement distributed tracing for signal flow

---

## CONCLUSION

Central Command's technical architecture is **sound and operational**. The 7-module parent architecture with dual-bus communication provides a robust, extensible foundation. Message lifecycle protocol prevents communication issues, and fault code system ensures comprehensive error tracking.

**Key Technical Strengths:**
- Clear separation of concerns (7 parent modules)
- Standardized communication (UniversalCommunicator)
- Robust error handling (fault code system)
- Extensible architecture (easy to add modules)

**Next Technical Steps:**
1. Implement functional self-test validation
2. Optimize section processing (parallel execution)
3. Migrate evidence index to SQL database
4. Add comprehensive unit test coverage

The architecture is production-ready pending functional validation.

---

**Document Type:** Technical Blueprint  
**Version:** 1.0  
**Status:** CURRENT  
**Last Updated:** 2025-10-12

**Related Documentation:**
- `SYSTEM_README.md` - Quick start and overview
- `CURRENT_SYSTEM_ARCHITECTURE_2025-10-12.md` - Detailed architecture
- `PRD_Central_Command.md` - Product requirements
- `SOP_Central_Command.md` - Operating procedures

**Module Documentation:**
- `Evidence Locker/README.md`
- `The Warden/README.md`
- `The Marshall/README.md`
- `Command Center/Mission Debrief/README.md`
- `Command Center/UI/README.md`
- `Command Center/Data Bus/README.md`
- `Command Center/Data Bus/diagnostic_manager/Unified_diagnostic_system/README.md`
