# CENTRAL COMMAND SYSTEM ARCHITECTURE
## Current Build Status: October 12, 2025

---

## EXECUTIVE SUMMARY

Central Command is a modular investigation report generation ecosystem built on a **dual-bus communication architecture** (CANBUS/LINBUS) with **7 parent modules** orchestrating 65+ child components. The system uses a **message lifecycle protocol** (CALL_SENT → CALL_ANSWERED) to prevent infinite communication loops and ensure reliable inter-module signaling.

**Primary Entry Point:** Unified Diagnostic System (UDS)  
**Communication Protocol:** Universal Communicator with MessageState lifecycle  
**Architecture Pattern:** Parent modules own child component testing and fault reporting

---

## SYSTEM ARCHITECTURE OVERVIEW

### Parent Module Hierarchy (7 Core Systems)

```
┌─────────────────────────────────────────────────────────────────┐
│                     UNIFIED DIAGNOSTIC SYSTEM                    │
│                          (DIAG-1)                                │
│                    [System Health Monitor]                       │
└───────────────┬─────────────────────────────────────────────────┘
                │
                │ Monitors & Validates ↓
                │
    ┌───────────┴──────────────┬────────────────┬─────────────────┐
    │                          │                │                 │
┌───▼────┐  ┌────────▼────────┐  ┌───▼──────┐  ┌──────▼──────┐  │
│ Bus-1  │  │ Evidence Locker │  │  Warden  │  │  Marshall   │  │
│        │  │       (1)       │  │   (2-1)  │  │     (3)     │  │
└───┬────┘  └────────┬────────┘  └───┬──────┘  └──────┬──────┘  │
    │                │                │                │          │
    │ 5 children     │ 8 children     │ 2 children     │ 3 children
    │                │                │                │          │
    │            ┌───▼────┐      ┌────▼──────┐   ┌────▼──────┐  │
    │            │  1.1-  │      │ 2-2 ECC   │   │  3-1 Ev.  │  │
    │            │  1.8   │      │ 2-3 GW    │   │   Manager │  │
    │            └────────┘      └───────────┘   │  + LINBUS │  │
    │                                             │  Proxy    │  │
    │                                             └───┬───────┘  │
    │                                                 │          │
    │                                      ┌──────────▼────────┐ │
    │                                      │  Analyst Sections │ │
    │                                      │   (4-1 to 4-8)    │ │
    │                                      │  via LINBUS       │ │
    │                                      └───────────────────┘ │
    │                                                            │
┌───▼──────────┐                                   ┌────────▼───┐
│ Mission      │                                   │    GUI     │
│  Debrief     │                                   │   (GUI-1)  │
│    (5)       │                                   └────────────┘
└───┬──────────┘
    │
    │ 2 children
    │
┌───▼──────────┐
│  5-1 Debrief │
│  5-2 Library │
└──────────────┘
```

### System Component Count

| Parent Module | Address | Child Components | Total Managed |
|--------------|---------|------------------|---------------|
| Bus-1 (Central Command Bus) | Bus-1 | 5 (Bus-1.1 to Bus-1.5) | 6 |
| Evidence Locker | 1 | 8 (1.1 to 1.8) | 9 |
| Warden | 2-1 | 2 (2-2 ECC, 2-3 Gateway) | 3 |
| Marshall | 3 | 3 (3-1 + 8 Analysts via LINBUS) | 12 |
| Mission Debrief | 5 | 2 (5-1, 5-2) | 3 |
| GUI | GUI-1 | 9 (GUI-1.1 to GUI-1.9) | 10 |
| UDS | DIAG-1 | 0 (monitors all) | 1 |
| **TOTAL** | **7** | **29 direct + Analyst sections** | **65+** |

---

## COMMUNICATION ARCHITECTURE

### Dual-Bus Design

**CANBUS (Controller Area Network)**
- High-throughput data network
- Evidence movement, fault codes, report generation
- All modules connected
- Multi-master, peer-to-peer communication
- Monitored by UDS for fault detection

**LINBUS (Local Interconnect Network)**
- Lightweight orchestration network
- Wake/sleep commands, ready states, sequencing
- Warden → Marshall → Analyst Sections
- Master-slave architecture
- NOT monitored by UDS

### Message Lifecycle Protocol

To prevent infinite communication loops, all bus messages follow a strict lifecycle:

```
REQUEST FLOW:
┌──────────┐  CALL_SENT   ┌──────────┐
│ Sender   │ ────────────→│ Receiver │
│ (UDS)    │              │ (Module) │
└──────────┘              └────┬─────┘
                               │
                               │ Validates: message_state == "CALL_SENT"
                               │ Processes request
                               │
RESPONSE FLOW:                 │
┌──────────┐ CALL_ANSWERED┌───▼──────┐
│ Sender   │ ←───────────│ Receiver │
│ (UDS)    │              │ (Module) │
└──────────┘              └──────────┘
     │
     │ Validates: message_state == "CALL_ANSWERED"
     │ Processes response
     └─ Complete
```

**MessageState Enum:**
- `CALL_SENT` - Request initiated
- `CALL_RECEIVED` - Acknowledgment (optional)
- `CALL_ANSWERED` - Response data sent
- `CALL_COMPLETED` - Confirmation (optional)

**Implementation:**
- All requests sent with `message_state: "CALL_SENT"`
- Handlers check `message_state == "CALL_SENT"` before responding
- All responses sent with `message_state: "CALL_ANSWERED"`
- Response handlers check `message_state == "CALL_ANSWERED"` before processing

---

## UNIVERSAL COMMUNICATOR PROTOCOL

### Purpose
Standardized communication layer for all modules, providing:
- Radio code signaling (10-4, 10-9, SOS, MAYDAY, etc.)
- Message lifecycle management
- Signal-based architecture
- Fault reporting and emergency protocols

### Core Methods

**Sending Messages:**
```python
_send_on_topic(topic, target_address, radio_code, message, payload, message_state)
send_auto_registration_response(target_address, system_metadata)
send_radio_check_response(target_address, connectivity_data)
send_rollcall_response(target_address, status_data)
```

**Radio Codes:**
- `10-4` - Acknowledged
- `10-6` - Evidence received
- `10-8` - Processing complete
- `10-9` - Repeat request
- `10-10` - Standby
- `SOS` - Emergency fault
- `MAYDAY` - Critical failure

---

## DIAGNOSTIC SYSTEM (UDS)

### Purpose
Unified Diagnostic System monitors all parent modules, validates system health, and enforces protocol compliance.

### Launch Sequence

**Phase 1:** System Detection
- Detects if system is already running
- Joins existing operations OR initializes full system

**Phase 2:** Bus Initialization
- Starts CANBUS (Bus-1)
- Registers UDS (DIAG-1)

**Phase 3:** Parent Module Instantiation
- Creates 7 parent module instances
- Each parent owns its child components

**Phase 4:** Auto-Registration Protocol
- UDS sends `auto_registration` requests to 6 parent modules
- Each parent validates its operational state
- Responds with capabilities and child component list

**Phase 5:** Baseline Testing
- UDS commands parent modules to test their children
- Parents report fault codes for failures
- UDS waits for self-test completion signals
- Only parent modules report to UDS

**Phase 6:** System Launch
- All validated systems go operational
- UDS enters monitoring mode
- Dual-mode operation initialized

### Parent-Child Testing Responsibility

**Critical Design Pattern:**
- UDS does NOT test child components directly
- Parent modules own testing of their children
- Parents emit fault codes when children fail
- UDS only monitors parent module health

**Example Flow:**
```
UDS → Evidence Locker (1): "Run self-test"
Evidence Locker:
  ├─ Tests 1.1 (Classifier)
  ├─ Tests 1.2 (Indexer)
  ├─ Tests 1.3 (Manifest Builder)
  └─ Emits fault codes if any fail
Evidence Locker → UDS: "Self-test complete" + fault codes
```

---

## MODULE RESPONSIBILITIES

### 1. Bus-1 (Central Command Bus)
**Address:** Bus-1  
**Type:** Communication infrastructure

**Capabilities:**
- Message routing and signal distribution
- Event logging
- System state management
- Signal registry management

**Children:** Bus-1.1 to Bus-1.5 (internal bus components)

---

### 2. Evidence Locker (1)
**Address:** 1  
**Type:** Evidence management

**Capabilities:**
- Evidence ingestion and validation
- Classification and indexing
- Manifest generation
- Gateway handoff

**Children:**
- 1.1 Evidence Classifier
- 1.2 Evidence Indexer
- 1.3 Manifest Builder
- 1.4 Section Registry
- 1.5 Case Manifest Builder
- 1.6 Evidence Index Manager
- 1.7 Static Data Flow
- 1.8 Bus Extensions

---

### 3. Warden (2-1)
**Address:** 2-1  
**Type:** System orchestration

**Capabilities:**
- Ecosystem control
- Section lifecycle management
- Gateway orchestration
- LINBUS master control

**Children:**
- 2-2 Ecosystem Controller (ECC)
- 2-3 Gateway Controller

---

### 4. Marshall (3)
**Address:** 3  
**Type:** Evidence distribution and LINBUS proxy

**Capabilities:**
- Evidence management
- Section processing coordination
- LINBUS sub-master for Analyst sections
- Evidence distribution pipeline

**Children:**
- 3-1 Evidence Manager
- 4-1 to 4-8 Analyst Sections (via LINBUS proxy)

**Special Role:** Marshall proxies LINBUS communication between CANBUS and Analyst sections

---

### 5. Mission Debrief (5)
**Address:** 5  
**Type:** Report finalization

**Capabilities:**
- Narrative assembly
- Report generation
- Final assembly and export
- Library archival

**Children:**
- 5-1 Debrief Manager
- 5-2 Librarian

---

### 6. GUI (GUI-1)
**Address:** GUI-1  
**Type:** User interface

**Capabilities:**
- User interface rendering
- Case management UI
- Evidence visualization
- Operator interaction

**Children:** GUI-1.1 to GUI-1.9 (UI components)

---

### 7. UDS (DIAG-1)
**Address:** DIAG-1  
**Type:** System diagnostics and monitoring

**Capabilities:**
- System health monitoring
- Fault code validation
- Protocol compliance enforcement
- Baseline testing orchestration

**Children:** None (monitors all other systems)

---

## OPERATIONAL FLOW

### Case Processing Flow

```
1. Evidence Intake
   ↓
   Evidence Locker (1)
   ├─ Classifies evidence
   ├─ Builds manifest
   └─ Signals "evidence ready" on CANBUS
   ↓
2. Gateway Handoff
   ↓
   Warden (2-1) → Gateway (2-3)
   ├─ Receives evidence manifest
   ├─ Routes to appropriate sections
   └─ Signals Marshall via LINBUS
   ↓
3. Section Processing
   ↓
   Marshall (3) → LINBUS → Analyst Sections (4-1 to 4-8)
   ├─ Wake sections as needed
   ├─ Distribute evidence
   ├─ Collect section outputs
   └─ Aggregate results to CANBUS
   ↓
4. Report Assembly
   ↓
   Mission Debrief (5)
   ├─ Collects all section outputs
   ├─ Assembles narrative
   ├─ Generates final report
   └─ Archives to Library (5-2)
   ↓
5. User Delivery
   ↓
   GUI (GUI-1)
   └─ Presents final report to operator
```

### Fault Handling Flow

```
1. Fault Detection (any component)
   ↓
2. Fault Code Emission to CANBUS
   ↓
3. UDS (DIAG-1) receives fault
   ↓
4. UDS validates fault against protocol
   ↓
5. UDS determines severity
   ├─ Warning: Log and continue
   ├─ Error: Attempt recovery
   └─ Critical: System halt
```

---

## SYSTEM REGISTRY

All modules register with the bus using standard metadata:

```json
{
  "system_address": "1",
  "system_type": "evidence_locker",
  "system_name": "Evidence Locker Main",
  "status": "OPERATIONAL",
  "capabilities": [
    "evidence_ingestion",
    "classification",
    "manifest_generation"
  ],
  "child_components": ["1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7", "1.8"],
  "parent_address": null,
  "communication_mode": "parent",
  "protocol_version": "1.0.0",
  "registered_at": "2025-10-12T18:00:00Z"
}
```

**Registry Location:** `Command Center/Data Bus/diagnostic_manager/system_registry.json`

---

## CURRENT BUILD STATUS

### ✅ Operational Components
- Message lifecycle protocol (CALL_SENT/CALL_ANSWERED)
- 7 parent module architecture
- Universal Communicator protocol
- UDS auto-registration
- Parent-child testing delegation
- CANBUS message routing
- Fault code framework

### ⚠️ Known Issues
- GUI not fully operational (responds to registration but may not render)
- Diagnostic tests too permissive (false positives)
- Functional validation needed for each module
- Setup wizard blocking main application launch

### 🔄 In Progress
- Tightening diagnostic validation
- GUI operational status verification
- End-to-end case processing testing

---

## ENTRY POINTS

### Primary Entry Point (Diagnostic Mode)
```
F:\The Central Command\Command Center\Data Bus\diagnostic_manager\Unified_diagnostic_system\LAUNCH_DIAGNOSTIC_SYSTEM.bat
```

**What it does:**
- Launches UDS
- Initializes all 7 parent modules
- Runs auto-registration
- Performs baseline testing
- Enters monitoring mode

### Application Entry Point (Operational Mode)
```
F:\The Central Command\Command Center\Start Menu\Run Time\DKI_ENGINE_LAUNCHER.bat
```

**Current Status:** Blocked by setup wizard (investigation needed)

---

## TECHNICAL SPECIFICATIONS

### Programming Language
Python 3.13+

### Key Dependencies
- tkinter (GUI framework)
- threading (concurrent operations)
- logging (diagnostics)
- json (configuration and messaging)
- pathlib (filesystem operations)

### File Locations
- **Bus Core:** `Command Center/Data Bus/Bus Core Design/bus_core.py`
- **Universal Communicator:** `Command Center/Data Bus/universal_communicator.py`
- **UDS Core:** `Command Center/Data Bus/diagnostic_manager/Unified_diagnostic_system/core.py`
- **System Registry:** `Command Center/Data Bus/diagnostic_manager/system_registry.json`
- **Protocol Registry:** `Command Center/Data Bus/diagnostic_manager/Unified_diagnostic_system/read_me/system_protocol_registry.py`

---

## DOCUMENTATION STRUCTURE

This architecture document represents the **current build as of October 12, 2025**.

**Related Documentation:**
- CANBUS_LINBUS_ARCHITECTURE.md - Detailed bus protocol specification
- DIAGNOSTIC_SYSTEM_README.md - UDS operation guide
- system_protocol_registry.py - Protocol definitions and fault codes
- Individual module README files (see each module directory)

**Legacy Documentation:**
- Documents dated before October 2025 may reference obsolete architecture
- All legacy docs should be archived to proof-of-concept storage
- Current operational procedures supersede all prior documentation

---

**Document Status:** CURRENT  
**Last Updated:** 2025-10-12  
**Version:** 1.0  
**Maintainer:** Central Command Architecture Team


