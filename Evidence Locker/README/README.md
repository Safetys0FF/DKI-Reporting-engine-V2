# EVIDENCE LOCKER MODULE (Address: 1)
## Evidence Management and Classification System

---

## MODULE OVERVIEW

The Evidence Locker is the **primary evidence ingestion and classification hub** for Central Command. It receives raw evidence files, classifies them by type and relevance, builds case manifests, and hands off processed evidence to the Gateway for section distribution.

**Module Address:** 1  
**Module Type:** Evidence Management  
**Parent Module:** Yes (owns 8 child components)  
**Bus Connections:** CANBUS (primary), LINBUS (throttle coordination)

---

## RESPONSIBILITIES

### Primary Functions
1. **Evidence Ingestion** - Accept and validate incoming evidence files
2. **Classification** - Categorize evidence by type, format, and section relevance
3. **Indexing** - Build searchable indexes for evidence retrieval
4. **Manifest Generation** - Create structured manifests for Gateway handoff
5. **Case Management** - Track evidence across case lifecycle

### Communication Roles
- **Listens on CANBUS for:**
  - Evidence upload signals
  - Evidence request signals
  - Case creation signals
  
- **Emits on CANBUS:**
  - Evidence ready signals
  - Manifest updates
  - Fault codes (1.00-1.99)

- **LINBUS Coordination:**
  - Throttle control with Warden
  - Processing rate synchronization

---

## CHILD COMPONENTS

The Evidence Locker manages 8 child components:

| Address | Component | Purpose |
|---------|-----------|---------|
| 1.1 | Evidence Classifier | Categorizes files by type and content |
| 1.2 | Evidence Indexer | Builds searchable indexes |
| 1.3 | Manifest Builder | Generates case manifests |
| 1.4 | Section Registry | Maps evidence to target sections |
| 1.5 | Case Manifest Builder | Assembles complete case manifests |
| 1.6 | Evidence Index Manager | Manages index storage and retrieval |
| 1.7 | Static Data Flow | Handles static asset processing |
| 1.8 | Bus Extensions | Custom bus signal handlers |

---

## FAULT CODES

**Range:** 1.00 - 1.99

### Critical Faults (1.00-1.09)
- `1.00` - Evidence Locker initialization failure
- `1.01` - Database connection failure
- `1.02` - File system access denied
- `1.03` - Critical component crash

### Evidence Processing Faults (1.10-1.19)
- `1.10` - Evidence ingestion failure
- `1.11` - File validation error
- `1.12` - Unsupported file format
- `1.13` - Corrupted evidence detected

### Classification Faults (1.20-1.29)
- `1.20` - Classifier unavailable
- `1.21` - Classification engine error
- `1.22` - Unknown evidence type

### Manifest Faults (1.30-1.39)
- `1.30` - Manifest generation failure
- `1.31` - Manifest validation error
- `1.32` - Missing required evidence

### Child Component Faults (1.40-1.89)
- `1.41` - Component 1.1 (Classifier) failure
- `1.42` - Component 1.2 (Indexer) failure
- `1.43` - Component 1.3 (Manifest Builder) failure
- *(continues for each child component)*

---

## OPERATIONAL FLOW

### Evidence Intake Flow

```
1. Evidence Upload
   ↓
   evidence_locker_module.py receives files
   ↓
2. Validation (1.1)
   ├─ Check file integrity
   ├─ Verify format support
   └─ Validate metadata
   ↓
3. Classification (1.1)
   ├─ Determine file type (image, document, video, etc.)
   ├─ Extract content metadata
   └─ Assign section relevance scores
   ↓
4. Indexing (1.2)
   ├─ Generate searchable index entries
   ├─ Store in evidence index
   └─ Link to case manifest
   ↓
5. Manifest Building (1.3, 1.5)
   ├─ Aggregate evidence metadata
   ├─ Build section-specific manifests
   └─ Generate case manifest
   ↓
6. Gateway Handoff
   ├─ Signal "evidence ready" on CANBUS
   ├─ Provide manifest to Gateway (2-3)
   └─ Await section processing requests
```

### Self-Test Protocol

When commanded by UDS, Evidence Locker performs:

1. **Component Health Check**
   - Test each child component (1.1 through 1.8)
   - Verify filesystem access
   - Check database connectivity

2. **Functional Validation**
   - Test evidence classification engine
   - Validate manifest generation
   - Verify bus communication

3. **Fault Reporting**
   - Emit fault codes for any failures
   - Send completion signal to UDS
   - Report operational status

---

## COMMUNICATION PROTOCOL

### Universal Communicator Integration

The Evidence Locker uses UniversalCommunicator for standardized messaging:

**Registered Signal Handlers:**
- `auto_registration` - UDS protocol compliance
- `radio_check` - Communication health validation
- `rollcall` - System presence confirmation
- `evidence.request` - Evidence retrieval requests
- `case_create` - New case initialization

**Message Lifecycle:**
- Only responds to `message_state: "CALL_SENT"`
- Sends responses with `message_state: "CALL_ANSWERED"`
- Uses radio codes (10-4, 10-6, etc.) for status

---

## FILE STRUCTURE

```
Evidence Locker/
├─ evidence_locker_module.py      # Main module entry point (Address: 1)
├─ evidence_classifier.py         # Child component (1.1)
├─ evidence_index.py              # Child component (1.2)
├─ case_manifest_builder.py      # Child component (1.3, 1.5)
├─ section_registry.py            # Child component (1.4)
├─ evidence_class_builder.py     # Classification logic
├─ static_data_flow.py           # Static asset handling (1.7)
├─ bus_extensions.py             # Custom bus handlers (1.8)
├─ evidence_manifest.json        # Active case manifests
├─ _init_evidence_locker.py      # Initialization script
├─ README.md                     # This file
└─ Test Plans/
   └─ EVIDENCE_LOCKER_SYSTEM_SUMMARY.md  # Test specifications
```

---

## INITIALIZATION

### Module Startup Sequence

1. **Import and Setup**
   ```python
   from evidence_locker_module import EvidenceLockerModule
   ```

2. **Instantiation**
   ```python
   evidence_locker = EvidenceLockerModule(
       bus=bus_instance,
       communicator=communicator_instance
   )
   ```

3. **Bus Registration**
   - Registers with address "1"
   - Subscribes to required signal handlers
   - Initializes child components

4. **Self-Test Execution**
   - Validates all 8 child components
   - Reports health status to UDS
   - Transitions to operational state

---

## INTEGRATION POINTS

### Upstream Dependencies
- **Bus-1 (CANBUS)** - Communication infrastructure
- **UDS (DIAG-1)** - Health monitoring and protocol validation

### Downstream Handoffs
- **Warden (2)** - Coordination and throttle control via LINBUS
- **Gateway (2-3)** - Evidence manifest delivery for section distribution

### Peer Interactions
- **GUI (GUI-1)** - Evidence upload interface
- **Mission Debrief (5)** - Final evidence archival

---

## OPERATIONAL STATUS

### Current Build Status
**Status:** OPERATIONAL (with validation warnings)  
**Last Updated:** 2025-10-12

**✅ Confirmed Working:**
- Module instantiation
- CANBUS registration
- UniversalCommunicator integration
- UDS auto-registration response
- Message lifecycle compliance

**⚠️ Requires Validation:**
- Evidence classification engine operational status
- Manifest generation functionality
- Child component (1.1-1.8) functional tests
- Filesystem I/O operations
- Database connectivity

---

## TROUBLESHOOTING

### Common Issues

**Issue:** Evidence Locker responds to UDS but processing fails  
**Solution:** Run functional validation tests on each child component (1.1-1.8)

**Issue:** Manifest generation incomplete  
**Solution:** Check `evidence_manifest.json` for errors, verify all required evidence present

**Issue:** Gateway not receiving manifests  
**Solution:** Verify CANBUS connectivity, check `evidence ready` signal emission

**Issue:** Child component failures not reported  
**Solution:** Confirm parent module's `_run_startup_self_test()` is testing all children

---

## RELATED DOCUMENTATION

- **System Architecture:** `Command Center/read_me_file/CURRENT_SYSTEM_ARCHITECTURE_2025-10-12.md`
- **CANBUS Protocol:** `Command Center/Data Bus/diagnostic_manager/read_me/CANBUS_LINBUS_ARCHITECTURE.md`
- **UDS Protocol:** `Command Center/Data Bus/diagnostic_manager/Unified_diagnostic_system/read_me/README.md`
- **Fault Code Registry:** `Command Center/Data Bus/diagnostic_manager/system_protocol_registry.py`

---

**Document Type:** Module README  
**Module:** Evidence Locker (1)  
**Status:** CURRENT  
**Last Updated:** 2025-10-12

