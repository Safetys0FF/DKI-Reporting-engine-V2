# UNIFIED DIAGNOSTIC SYSTEM (Address: DIAG-1)
## System Health Monitoring and Protocol Enforcement

---

## MODULE OVERVIEW

The Unified Diagnostic System (UDS) is the **system health monitoring and protocol enforcement engine** for Central Command. It validates all parent modules, monitors system health, enforces communication protocols, and manages system launch sequences.

**Module Address:** DIAG-1  
**Module Type:** Diagnostic and Monitoring  
**Parent Module:** Yes (monitors all 6 other parents, owns no children)  
**Bus Connections:** CANBUS (monitoring only, NOT on LINBUS)

---

## RESPONSIBILITIES

### Primary Functions
1. **System Health Monitoring** - Continuous monitoring of all 6 parent modules
2. **Protocol Validation** - Enforce Universal Communication Protocol compliance
3. **Fault Code Validation** - Verify fault codes against protocol registry
4. **Baseline Testing** - Command parent modules to test their children
5. **Launch Orchestration** - Manage system initialization sequence

### Communication Roles
- **Listens on CANBUS for:**
  - Auto-registration responses from parent modules
  - Fault code emissions from all systems
  - Self-test completion signals
  - Radio check and rollcall responses
  
- **Emits on CANBUS:**
  - Auto-registration requests (with `message_state: "CALL_SENT"`)
  - Radio check commands
  - Rollcall commands
  - Fault validation results
  - System health reports

---

## KEY ARCHITECTURAL PRINCIPLES

### Parent-Child Testing Delegation

**Critical Design Pattern:**
UDS does NOT test child components directly. Parent modules are responsible for testing their own children.

```
UDS Testing Flow:
┌──────────────────────────────────────────────────────────────┐
│ UDS (DIAG-1) Commands Parent Modules ONLY                    │
└───────────────┬──────────────────────────────────────────────┘
                │
                ├─ "Evidence Locker (1): Run self-test"
                ├─ "Warden (2-1): Run self-test"
                ├─ "Marshall (3): Run self-test"
                ├─ "Mission Debrief (5): Run self-test"
                ├─ "Bus-1: Run self-test"
                └─ "GUI-1: Run self-test"

Parent Module Response Flow:
┌──────────────────────────────────────────────────────────────┐
│ Each Parent Tests Its Own Children                           │
└───────────────┬──────────────────────────────────────────────┘
                │
                ├─ Evidence Locker tests 1.1-1.8
                ├─ Warden tests 2-2, 2-3
                ├─ Marshall tests 3-1 (+ proxies Analyst tests via LINBUS)
                ├─ Mission Debrief tests 5-1, 5-2
                ├─ Bus tests internal components
                └─ GUI tests GUI-1.1 to GUI-1.9

Reporting Flow:
┌──────────────────────────────────────────────────────────────┐
│ Parents Report to UDS with Fault Codes                       │
└───────────────┬──────────────────────────────────────────────┘
                │
                ├─ "Evidence Locker: Self-test complete, 0 faults"
                ├─ "Warden: Self-test complete, 1 fault (2.43)"
                └─ UDS validates fault codes and updates system health
```

### Message Lifecycle Enforcement

UDS enforces strict message lifecycle to prevent infinite loops:

**Sending Requests:**
- All requests sent with `message_state: "CALL_SENT"`
- Targets only 6 parent modules (not children)

**Processing Responses:**
- Only processes `message_state: "CALL_ANSWERED"`
- Ignores own requests and child module responses

---

## FAULT CODE REGISTRY

**Range:** DIAG-1.00 - DIAG-1.99

### Critical Faults (DIAG-1.00-DIAG-1.09)
- `DIAG-1.00` - UDS initialization failure
- `DIAG-1.01` - Bus connection failure
- `DIAG-1.02` - Protocol registry corruption
- `DIAG-1.03` - Enforcement module failure

### Protocol Faults (DIAG-1.10-DIAG-1.19)
- `DIAG-1.10` - Protocol violation detected
- `DIAG-1.11` - Message lifecycle violation
- `DIAG-1.12` - Invalid message format
- `DIAG-1.13` - Unknown radio code

### Registration Faults (DIAG-1.20-DIAG-1.29)
- `DIAG-1.20` - Auto-registration timeout
- `DIAG-1.21` - Registration compliance failure
- `DIAG-1.22` - Invalid system metadata
- `DIAG-1.23` - Duplicate address registration

### Testing Faults (DIAG-1.30-DIAG-1.39)
- `DIAG-1.30` - Baseline testing timeout
- `DIAG-1.31` - Self-test completion timeout
- `DIAG-1.32` - Fault code validation failure
- `DIAG-1.33` - System health check failure

---

## OPERATIONAL FLOW

### System Launch Sequence

```
Phase 1: System Detection
├─ Detect if system already running
├─ Join existing OR initialize new
└─ Determine operational mode

Phase 2: Bus Initialization
├─ Start CANBUS (Bus-1)
├─ Register UDS (DIAG-1)
└─ Verify bus operational

Phase 3: Parent Module Instantiation
├─ Create Evidence Locker (1) instance
├─ Create Warden (2-1) instance
├─ Create Marshall (3) instance
├─ Create Mission Debrief (5) instance
├─ Create GUI (GUI-1) instance
└─ Note: Bus-1 already running

Phase 4: Auto-Registration Protocol
├─ UDS → Evidence Locker (1): "auto_registration" (CALL_SENT)
├─ UDS → Warden (2-1): "auto_registration" (CALL_SENT)
├─ UDS → Marshall (3): "auto_registration" (CALL_SENT)
├─ UDS → Mission Debrief (5): "auto_registration" (CALL_SENT)
├─ UDS → Bus-1: "auto_registration" (CALL_SENT)
├─ UDS → GUI-1: "auto_registration" (CALL_SENT)
└─ Collect responses (only CALL_ANSWERED)

Phase 5: Baseline Testing
├─ UDS → Each Parent: "Run self-test"
├─ Wait for completion signals
├─ Validate fault codes
└─ Aggregate system health

Phase 6: System Launch
├─ All validated systems → OPERATIONAL
├─ UDS → Monitoring mode
└─ Dual-mode operation active

Phase 7: Continuous Monitoring
├─ Monitor fault code emissions
├─ Track system health metrics
├─ Validate protocol compliance
└─ Generate health reports
```

### Fault Validation Flow

```
1. Fault Code Emission (any module)
   ↓
   Module emits fault code on CANBUS
   ↓
2. UDS Receives Fault
   ↓
   UDS enforcement module captures fault
   ↓
3. Fault Validation
   ├─ Lookup in protocol registry
   ├─ Verify fault code format (XX.YY)
   ├─ Validate address ownership
   └─ Check severity level
   ↓
4. Severity Classification
   ├─ CRITICAL (XX.00-XX.09): System halt
   ├─ ERROR (XX.10-XX.89): Attempt recovery
   └─ WARNING (XX.90-XX.99): Log and continue
   ↓
5. Action Execution
   ├─ Log to system logs
   ├─ Update health metrics
   ├─ Execute recovery (if applicable)
   └─ Notify operators (if critical)
```

---

## FILE STRUCTURE

```
Command Center/Data Bus/diagnostic_manager/Unified_diagnostic_system/
├─ core.py                       # Main UDS logic (Address: DIAG-1)
├─ comms.py                      # Communication protocols
├─ enforcement.py                # Fault validation and enforcement
├─ __init__.py                   # UDS wrapper and launcher
├─ LAUNCH_DIAGNOSTIC_SYSTEM.bat # Windows launcher
├─ library/
│  └─ system_logs/               # UDS log output
├─ read_me/
│  ├─ README.md                  # This file
│  ├─ system_protocol_registry.py        # Fault codes and protocols
│  ├─ CANBUS_LINBUS_ARCHITECTURE.md
│  ├─ DIAGNOSTIC_SYSTEM_README.md
│  ├─ DIAGNOSTIC_SYSTEM_BLUEPRINT.md
│  └─ DIAGNOSTIC_SYSTEM_PRD.md
└─ backups/                      # Core system backups
```

---

## INITIALIZATION

### UDS Launch

**Standard Launch:**
```batch
F:\The Central Command\Command Center\Data Bus\diagnostic_manager\Unified_diagnostic_system\LAUNCH_DIAGNOSTIC_SYSTEM.bat
```

**Python Direct:**
```python
from core import CoreSystem

# Initialize UDS
uds = CoreSystem()

# Launch diagnostic system
result = uds.launch_diagnostic_system(smoke_mode=False)
```

### Launch Modes

**Normal Mode:**
- Full system initialization
- All 6 parent modules tested
- Comprehensive baseline testing

**Smoke Mode:**
- Minimal testing
- Faster startup
- Validation testing only

---

## INTEGRATION POINTS

### Monitored Systems
UDS monitors all 6 other parent modules:
- Evidence Locker (1)
- Warden (2-1)
- Marshall (3)
- Mission Debrief (5)
- Bus-1
- GUI-1

**Note:** UDS does NOT monitor:
- LINBUS traffic (not connected to LINBUS)
- Child components directly (parents test children)

### Dependencies
- **Bus-1 (CANBUS)** - Required for all communication
- **system_protocol_registry.py** - Fault code definitions
- **Universal Communicator** - Message lifecycle enforcement

---

## OPERATIONAL STATUS

### Current Build Status
**Status:** OPERATIONAL  
**Last Updated:** 2025-10-12

**✅ Confirmed Working:**
- UDS initialization
- CANBUS connection
- Auto-registration protocol
- Message lifecycle enforcement (CALL_SENT/CALL_ANSWERED)
- Parent-only communication (skips child addresses)
- Fault code capture
- System launch orchestration

**⚠️ Known Issues:**
- Diagnostic tests too permissive (false positives)
- Parent modules report "healthy" without functional validation
- Need stricter self-test validation logic

**🔧 Recent Fixes (2025-10-12):**
- ✅ Added message lifecycle protocol to prevent infinite loops
- ✅ Implemented parent-only communication filtering
- ✅ Updated all parent modules with lifecycle checks
- ✅ Removed Unicode characters from log output

---

## CONFIGURATION

### Parent Module List
**File:** `core.py` (lines ~6180, ~6079, ~6295)

```python
# Only these 6 parent modules receive UDS commands
parent_modules = ['1', '2-1', '3', '5', 'Bus-1', 'GUI-1']

# DIAG-1 (self) is explicitly excluded from:
# - Auto-registration (doesn't register with itself)
# - Self-testing (cannot test itself)
# - Baseline monitoring (is the monitor)
```

### Expected Modules for Baseline Testing
**File:** `core.py` line ~6299

```python
# UDS waits for these 6 parent modules to complete self-tests
expected_modules = ['1', '2-1', '3', '5', 'Bus-1', 'GUI-1']
```

---

## TROUBLESHOOTING

### Common Issues

**Issue:** UDS reports "all systems healthy" but they're not  
**Solution:** Parent module self-tests too permissive. Need functional validation, not just existence checks.

**Issue:** Infinite loop / recursion errors  
**Solution:** Verify message_state lifecycle checks present in all handlers, confirm parent-only filtering active

**Issue:** Auto-registration timeout  
**Solution:** Check parent module auto-registration handlers, verify message_state == "CALL_SENT" check present

**Issue:** UDS not receiving self-test completion  
**Solution:** Confirm parent modules emit completion signal after testing children

---

## RELATED DOCUMENTATION

- **System Architecture:** `The War Room\SOPs\READ FILES\Build Specs\CURRENT_SYSTEM_ARCHITECTURE_2025-10-12.md`
- **Message Lifecycle:** `Command Center/Data Bus/Bus Core Design/bus_core.py` (MessageState class)
- **Fault Code Registry:** `read_me/system_protocol_registry.py`
- **Protocol Architecture:** `read_me/CANBUS_LINBUS_ARCHITECTURE.md`

---

**Document Type:** Module README  
**Module:** Unified Diagnostic System (DIAG-1)  
**Status:** CURRENT  
**Last Updated:** 2025-10-12


