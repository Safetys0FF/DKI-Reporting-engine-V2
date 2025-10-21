# CENTRAL COMMAND BUS (Address: Bus-1)
## Signal-Based Communication Infrastructure

---

## MODULE OVERVIEW

The Central Command Bus (Bus-1) is the **communication backbone** for the entire Central Command ecosystem. It implements a signal-based architecture enabling loosely coupled communication between all modules, with support for both CANBUS (high-throughput data) and LINBUS (orchestration) protocols.

**Module Address:** Bus-1  
**Module Type:** Communication Infrastructure  
**Parent Module:** Yes (owns 5 child components)  
**Bus Connections:** Self (is the bus)

---

## RESPONSIBILITIES

### Primary Functions
1. **Message Routing** - Route signals between modules based on topic subscription
2. **Signal Distribution** - Broadcast or point-to-point signal delivery
3. **Event Logging** - Record all bus transactions for diagnostics
4. **System State Management** - Track case data, module status, and system health
5. **Module Registry** - Maintain registry of connected systems and their addresses

### Communication Roles
- **Provides:**
  - Signal registration and subscription services
  - Message sending and receiving APIs
  - Event logging and diagnostics
  - System address registry
  
- **Emits:**
  - Bus health status signals
  - Fault codes (Bus-1.00-Bus-1.99)
  - System state updates

---

## CHILD COMPONENTS

The Bus manages 5 internal child components:

| Address | Component | Purpose |
|---------|-----------|---------|
| Bus-1.1 | Signal Registry | Topic-to-handler mapping management |
| Bus-1.2 | Event Logger | Transaction logging and audit trail |
| Bus-1.3 | State Manager | Case and system state tracking |
| Bus-1.4 | Address Registry | System address and capability registration |
| Bus-1.5 | Health Monitor | Bus performance and health metrics |

---

## FAULT CODES

**Range:** Bus-1.00 - Bus-1.99

### Critical Faults (Bus-1.00-Bus-1.09)
- `Bus-1.00` - Bus initialization failure
- `Bus-1.01` - Signal registry corruption
- `Bus-1.02` - Event logger failure
- `Bus-1.03` - Critical threading error

### Routing Faults (Bus-1.10-Bus-1.19)
- `Bus-1.10` - Message routing failure
- `Bus-1.11` - Handler execution error
- `Bus-1.12` - Signal delivery timeout
- `Bus-1.13` - Unknown topic

### Registry Faults (Bus-1.20-Bus-1.29)
- `Bus-1.20` - System registration failure
- `Bus-1.21` - Address conflict
- `Bus-1.22` - Invalid address format
- `Bus-1.23` - Registry corruption

### Performance Faults (Bus-1.30-Bus-1.39)
- `Bus-1.30` - Bus overload
- `Bus-1.31` - Message queue overflow
- `Bus-1.32` - Handler timeout
- `Bus-1.33` - Memory exhaustion

---

## ARCHITECTURE

### Signal-Based Communication Pattern

The bus implements publish-subscribe architecture:

```
┌─────────────────────────────────────────────────────────────────┐
│                      CENTRAL COMMAND BUS (Bus-1)                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Signal Registry (Bus-1.1)                                │  │
│  │ Topic → [Handler1, Handler2, ...]                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Address Registry (Bus-1.4)                               │  │
│  │ Address → {capabilities, status, metadata}               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Message Router                                            │  │
│  │ - Parent module filtering (MessageState lifecycle)       │  │
│  │ - Topic-based handler dispatch                            │  │
│  │ - Error handling and logging                              │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
         │                    │                    │
         │ CANBUS             │ CANBUS             │ CANBUS
         ▼                    ▼                    ▼
   ┌─────────┐          ┌─────────┐          ┌─────────┐
   │  Mod 1  │          │  Mod 2-1│          │  Mod 3  │
   └─────────┘          └─────────┘          └─────────┘
```

### Message Lifecycle Integration

The bus enforces message lifecycle protocol to prevent infinite loops:

**Send Method - Parent Module Filtering:**
```python
def send(self, topic, data):
    # Check if message targets a child address
    target_address = data.get('target_address')
    if target_address and target_address not in PARENT_MODULES:
        # Skip delivery - parent handles children
        logger.debug(f"Skipping child address {target_address}")
        return {}
    
    # Deliver to registered handlers for this topic
    for handler in self.signal_registry.get(topic, []):
        response = handler(data)
```

**Handler Registration:**
```python
def register_signal(self, topic, handler):
    if topic not in self.signal_registry:
        self.signal_registry[topic] = []
    self.signal_registry[topic].append(handler)
```

---

## OPERATIONAL FLOW

### Module Communication Flow

```
1. Module Sends Signal
   ↓
   module.communicator.send_signal(topic, payload)
   ↓
2. Bus Receives Signal
   ↓
   bus.send(topic, data)
   ↓
3. Message Lifecycle Check
   ├─ Validate message_state
   ├─ Filter child addresses (parent-only delivery)
   └─ Continue if valid
   ↓
4. Handler Dispatch
   ├─ Look up handlers for topic in Signal Registry (Bus-1.1)
   ├─ Execute each subscribed handler
   └─ Collect responses
   ↓
5. Event Logging
   ├─ Log transaction to Event Logger (Bus-1.2)
   ├─ Record delivery status
   └─ Update metrics in Health Monitor (Bus-1.5)
   ↓
6. Return Response
   └─ Return aggregated handler responses to sender
```

### System Registration Flow

```
1. Module Initialization
   ↓
   module connects to bus
   ↓
2. Address Registration
   ↓
   bus.register_system_address(address, metadata)
   ↓
3. Address Registry Update (Bus-1.4)
   ├─ Validate address format
   ├─ Check for conflicts
   ├─ Store system metadata
   └─ Record registration timestamp
   ↓
4. Capability Publication
   ├─ Module declares capabilities
   ├─ Child component list
   └─ Protocol version
   ↓
5. Signal Handler Subscription
   ├─ Module registers handlers for topics
   └─ Handlers added to Signal Registry (Bus-1.1)
```

### Self-Test Protocol

When commanded by UDS, Bus performs:

1. **Component Health Check**
   - Validate all 5 child components operational
   - Test signal registry integrity
   - Verify event logger functional

2. **Functional Validation**
   - Test signal send/receive cycle
   - Validate message routing
   - Check handler execution

3. **Fault Reporting**
   - Emit fault codes for any failures
   - Send completion signal to UDS
   - Report operational status

---

## COMMUNICATION PROTOCOL

### Universal Communicator Integration

Bus uses UniversalCommunicator for self-registration with UDS:

**Registered Signal Handlers:**
- `auto_registration` - UDS protocol compliance
- `radio_check` - Communication health validation
- `rollcall` - System presence confirmation
- `sos_fault` - Emergency fault signals
- `case_create`, `files_add`, `evidence.*` - Core operational signals

**Message Lifecycle:**
- Enforces `message_state` filtering for parent-only delivery
- Only responds to `message_state: "CALL_SENT"`
- Sends responses with `message_state: "CALL_ANSWERED"`

---

## FILE STRUCTURE

```
Command Center/Data Bus/
├─ Bus Core Design/
│  ├─ bus_core.py                # Main bus implementation (Address: Bus-1)
│  ├─ main_application.py        # Bus standalone entry point
│  └─ README/
│     ├─ DATA_BUS_SYSTEM_SUMMARY.md
│     └─ CANBUS_LINBUS_ARCHITECTURE.md
├─ universal_communicator.py     # Communication protocol layer
├─ ecosystem_integration_portal.py
├─ api_manager.py
├─ pdf_manager.py
├─ plugin_manager.py
├─ plugin_lifecycle_manager.py
├─ case_library_manager.py
├─ diagnostic_manager/           # UDS system (DIAG-1)
│  └─ Unified_diagnostic_system/
├─ README.md                     # This file
└─ configs/                      # Bus configuration files
```

---

## INITIALIZATION

### Bus Startup Sequence

**Standalone Launch:**
```python
from bus_core import DKIReportBus

# Initialize bus
bus = DKIReportBus()

# Bus automatically:
# - Creates signal registry
# - Initializes event logger
# - Sets up default handlers
# - Begins accepting connections
```

**Module Integration:**
```python
# Modules receive bus reference during initialization
module = SomeModule(bus=bus_instance)

# Module registers with bus
bus.register_system_address("MODULE_ADDR", metadata)

# Module subscribes to signals
bus.register_signal("topic.name", module._handler_method)
```

---

## INTEGRATION POINTS

### Connected Systems
All 6 other parent modules connect to Bus-1:
- Evidence Locker (1)
- Warden (2-1)
- Marshall (3)
- Mission Debrief (5)
- GUI (GUI-1)
- UDS (DIAG-1)

### Bus Services Provided
- **Signal Routing** - All inter-module communication
- **State Management** - Case data, evidence manifests, snapshots
- **Event Logging** - Full transaction audit trail
- **Health Monitoring** - Bus performance metrics
- **Plugin Management** - Dynamic plugin discovery and lifecycle

---

## OPERATIONAL STATUS

### Current Build Status
**Status:** OPERATIONAL  
**Last Updated:** 2025-10-12

**✅ Confirmed Working:**
- Bus initialization
- Signal registry management
- Message routing with parent-only filtering
- Message lifecycle protocol enforcement
- UniversalCommunicator integration
- UDS auto-registration response
- Event logging

**⚠️ Monitoring:**
- Message queue performance under load
- Handler execution timeout handling
- Memory management for long-running sessions

---

## TROUBLESHOOTING

### Common Issues

**Issue:** Messages not delivered to target module  
**Solution:** Verify module registered handlers for topic, check address in PARENT_MODULES set

**Issue:** Infinite message loops  
**Solution:** Confirm message_state lifecycle enforcement active, verify handler checks message_state

**Issue:** Handler execution errors  
**Solution:** Check Event Logger (Bus-1.2) for exception details, validate handler signature

**Issue:** Bus performance degradation  
**Solution:** Review Health Monitor (Bus-1.5) metrics, check for handler timeouts or memory leaks

---

## RELATED DOCUMENTATION

- **System Architecture:** `The War Room\SOPs\READ FILES\Build Specs\CURRENT_SYSTEM_ARCHITECTURE_2025-10-12.md`
- **CANBUS/LINBUS Protocol:** `Command Center/Data Bus/Bus Core Design/README/CANBUS_LINBUS_ARCHITECTURE.md`
- **Universal Communicator:** `Command Center/Data Bus/universal_communicator.py` (inline documentation)
- **Message Lifecycle:** `The War Room\SOPs\READ FILES\Build Specs\CURRENT_SYSTEM_ARCHITECTURE_2025-10-12.md` (Communication Architecture section)

---

**Document Type:** Module README  
**Module:** Central Command Bus (Bus-1)  
**Status:** CURRENT  
**Last Updated:** 2025-10-12

