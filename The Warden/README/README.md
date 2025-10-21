# THE WARDEN MODULE (Address: 2)
## System Orchestration and Master Control

---

## MODULE OVERVIEW

The Warden is the **master orchestration and control system** for Central Command. It manages the Ecosystem Controller (ECC) and Gateway Controller, coordinates system-wide operations, and serves as the LINBUS master for inter-module synchronization.

**Module Address:** 2  
**Module Type:** System Orchestration  
**Parent Module:** Yes (owns 2 child components)  
**Bus Connections:** CANBUS (coordination), LINBUS (master control)

---

## RESPONSIBILITIES

### Primary Functions
1. **System Orchestration** - Master control of all Central Command operations
2. **Ecosystem Management** - Boot order, lifecycle, and dependency coordination (via ECC 2-2)
3. **Gateway Control** - Evidence routing and section generation management (via Gateway 2-3)
4. **LINBUS Master** - Master controller for orchestration bus
5. **Mission Status** - Consolidated system health and progress reporting

### Communication Roles
- **Listens on CANBUS for:**
  - Section completion signals
  - Evidence processing status
  - Mission status requests
  
- **Emits on CANBUS:**
  - Mission status updates
  - System health telemetry
  - Fault codes (2.00-2.99)

- **LINBUS Master:**
  - Commands Marshall for section wake/sleep
  - Coordinates Evidence Locker throttle
  - Manages processing workflow timing

---

## CHILD COMPONENTS

The Warden manages 2 child components:

| Address | Component | Purpose |
|---------|-----------|---------|
| 2-2 | Ecosystem Controller (ECC) | Boot order, system lifecycle, dependency management |
| 2-3 | Gateway Controller | Evidence routing, section generation, handoff management |

### Ecosystem Controller (2-2)
**File:** `ecosystem_controller.py`

**Responsibilities:**
- System initialization and bootstrap
- Module dependency resolution
- Execution order management
- Section state tracking
- Mission-wide coordination

**Child Sub-Components:**
- 2-2.1 through 2-2.4 (internal ECC components)

### Gateway Controller (2-3)
**File:** `gateway_controller.py`

**Responsibilities:**
- Evidence manifest reception
- Section-specific evidence routing
- Section generation commands
- Analyst Deck coordination
- Section completion validation

**Child Sub-Components:**
- 2-3.1 through 2-3.4 (internal Gateway components)

---

## FAULT CODES

**Range:** 2.00 - 2.99

### Critical Faults (2.00-2.09)
- `2.00` - Warden initialization failure
- `2.01` - ECC initialization failure
- `2.02` - Gateway initialization failure
- `2.03` - LINBUS master failure

### Orchestration Faults (2.10-2.19)
- `2.10` - Ecosystem coordination failure
- `2.11` - Boot order violation
- `2.12` - Dependency resolution error
- `2.13` - Module synchronization timeout

### Gateway Faults (2.20-2.29)
- `2.20` - Gateway routing failure
- `2.21` - Section generation error
- `2.22` - Evidence handoff timeout
- `2.23` - Section completion timeout

### LINBUS Faults (2.30-2.39)
- `2.30` - LINBUS communication failure
- `2.31` - Marshall coordination timeout
- `2.32` - Throttle control error

### Child Component Faults (2.40-2.89)
- `2.42` - Component 2-2 (ECC) failure
- `2.43` - Component 2-3 (Gateway) failure

---

## OPERATIONAL FLOW

### System Bootstrap Flow

```
1. Warden Initialization
   ↓
   warden_module.py instantiates
   ↓
2. Child Component Startup
   ├─ Initialize ECC (2-2)
   │  ├─ Load system registry
   │  ├─ Resolve dependencies
   │  └─ Determine boot order
   ├─ Initialize Gateway (2-3)
   │  ├─ Register section handlers
   │  ├─ Subscribe to evidence signals
   │  └─ Configure routing tables
   ↓
3. LINBUS Master Activation
   ├─ Establish master control
   ├─ Register sub-masters (Marshall)
   └─ Initialize coordination protocols
   ↓
4. Mission Control Ready
   ├─ Signal operational status
   └─ Begin monitoring mode
```

### Evidence Processing Orchestration

```
1. Evidence Ready Signal (CANBUS)
   ↓
   Warden receives from Evidence Locker (1)
   ↓
2. ECC Coordination
   ├─ Check system readiness
   ├─ Validate dependencies
   └─ Authorize Gateway processing
   ↓
3. Gateway Routing (2-3)
   ├─ Analyze evidence manifest
   ├─ Determine target sections
   └─ Route to appropriate Analyst sections
   ↓
4. LINBUS Orchestration
   ├─ Command Marshall (3) via LINBUS
   ├─ Marshall wakes target sections
   └─ Coordinate processing timing
   ↓
5. Section Processing Monitoring
   ├─ Track section progress
   ├─ Aggregate status updates
   └─ Emit mission.status on CANBUS
   ↓
6. Completion Validation
   ├─ Verify all sections complete
   ├─ Validate outputs
   └─ Signal Mission Debrief (5)
```

### Self-Test Protocol

When commanded by UDS, Warden performs:

1. **Component Health Check**
   - Test ECC (2-2) initialization
   - Test Gateway (2-3) initialization
   - Verify LINBUS master control

2. **Functional Validation**
   - Test bus connectivity (CANBUS + LINBUS)
   - Validate signal handlers
   - Check coordination protocols

3. **Fault Reporting**
   - Emit fault codes for any failures
   - Send completion signal to UDS
   - Report operational status

---

## COMMUNICATION PROTOCOL

### Universal Communicator Integration

The Warden uses UniversalCommunicator for standardized messaging:

**Registered Signal Handlers:**
- `auto_registration` - UDS protocol compliance
- `radio_check` - Communication health validation
- `rollcall` - System presence confirmation
- `section.data.updated` - Section progress tracking
- `gateway.section.complete` - Section completion validation

**Message Lifecycle:**
- Only responds to `message_state: "CALL_SENT"`
- Sends responses with `message_state: "CALL_ANSWERED"`
- Uses radio codes for status communication

---

## FILE STRUCTURE

```
The Warden/
├─ warden_module.py              # Main module entry point (Address: 2)
├─ warden_main.py                # Bootstrap entry point
├─ ecosystem_controller.py       # Child component (2-2)
├─ gateway_controller.py         # Child component (2-3)
├─ section_tag_map.json         # Section routing configuration
├─ _init_warden.py              # Initialization script
├─ README.md                    # This file
├─ Test Plans/
│  └─ WARDEN_SYSTEM_SUMMARY.md  # Test specifications
└─ Gateway/
   ├─ section_readme/           # Section-specific documentation
   └─ parsing maps/             # Evidence routing maps
```

---

## INITIALIZATION

### Module Startup Sequence

1. **Import and Setup**
   ```python
   from warden_module import WardenModule
   ```

2. **Instantiation**
   ```python
   warden = WardenModule(
       bus=bus_instance,
       communicator=communicator_instance
   )
   ```

3. **Bus Registration**
   - Registers with address "2"
   - Subscribes to required signal handlers
   - Initializes ECC (2-2) and Gateway (2-3)

4. **LINBUS Master Setup**
   - Establishes master control
   - Registers sub-masters
   - Begins coordination protocols

5. **Self-Test Execution**
   - Validates both child components (2-2, 2-3)
   - Reports health status to UDS
   - Transitions to operational state

---

## INTEGRATION POINTS

### Upstream Dependencies
- **Bus-1 (CANBUS)** - Communication infrastructure
- **UDS (DIAG-1)** - Health monitoring and protocol validation

### Controlled Systems (via LINBUS)
- **Marshall (3)** - Section orchestration sub-master
- **Evidence Locker (1)** - Throttle coordination
- **Mission Debrief (5)** - Workflow synchronization

### Downstream Handoffs
- **Analyst Sections (4-1 to 4-8)** - Via Marshall LINBUS proxy
- **GUI (GUI-1)** - Mission status updates

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
- ECC (2-2) operational status
- Gateway (2-3) routing functionality
- LINBUS master control operations
- Section coordination workflows
- Mission status aggregation

---

## TROUBLESHOOTING

### Common Issues

**Issue:** Warden responds to UDS but orchestration fails  
**Solution:** Validate ECC and Gateway initialization, check LINBUS master status

**Issue:** Sections not waking up  
**Solution:** Verify LINBUS communication to Marshall, check coordination protocol

**Issue:** Mission status not updating  
**Solution:** Confirm section.data.updated signal subscriptions, validate ECC tracking

**Issue:** Gateway routing errors  
**Solution:** Check `section_tag_map.json`, verify evidence manifest format

---

## RELATED DOCUMENTATION

- **System Architecture:** `Command Center/read_me_file/CURRENT_SYSTEM_ARCHITECTURE_2025-10-12.md`
- **LINBUS Protocol:** `Command Center/Data Bus/diagnostic_manager/read_me/CANBUS_LINBUS_ARCHITECTURE.md`
- **UDS Protocol:** `Command Center/Data Bus/diagnostic_manager/Unified_diagnostic_system/read_me/README.md`
- **Gateway Operations:** `The Warden/Gateway/` (section-specific docs)

---

**Document Type:** Module README  
**Module:** The Warden (2)  
**Status:** CURRENT  
**Last Updated:** 2025-10-12

