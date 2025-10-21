# DKI ENGINE: DUAL-BUS COMMUNICATION ARCHITECTURE
**Version:** 1.0  
**Date:** 2025-10-11  
**System:** Central Command - Bus Core Design

---

## OVERVIEW

The DKI Engine uses a **dual-bus communication architecture** inspired by automotive CAN/LIN bus systems:

- **CANBUS** - High-throughput data network for evidence, reports, and fault monitoring
- **LINBUS** - Lightweight orchestration network for coordination, sequencing, and timing

**Design Philosophy:** "Two signals, one smooth operation"

---

## BUS DEFINITIONS

### **CANBUS (Controller Area Network - Heavy Lifting)**

**Purpose:** Primary data and fault network

**Traffic:**
- Evidence movement (requests/delivery)
- Report generation
- Section results publication
- Fault code emission (ALL systems)
- Data-intensive operations

**Connected Systems:**
- Evidence Locker (1)
- Warden (2)
- Marshall (3)
- Sections 1-8 (4-1 through 4-8)
- Mission Debrief (5)
- GUI (GUI-1)
- UDS (DIAG-1 / Bus-1)

**Characteristics:**
- Multi-master (peer-to-peer)
- High-throughput
- Priority-based message arbitration
- Monitored by UDS for fault detection

---

### **LINBUS (Local Interconnect Network - Coordination)**

**Purpose:** Orchestration and timing synchronization

**Traffic:**
- Wake/sleep commands (Marshall → Sections)
- Ready state signals (Sections → Marshall)
- Parent module coordination (Warden ↔ Marshall ↔ Evidence Locker)
- Sequencing instructions
- Throttle control signals

**Connected Systems:**
- Warden (2) - Master controller
- Marshall (3) - Section orchestrator
- Sections 1-8 (4-1 through 4-8) - Coordinated workers
- Evidence Locker (1) - Throttle coordination
- Mission Debrief (5) - Workflow coordination

**NOT Connected:**
- UDS (does not monitor LINBUS)
- GUI (does not participate in orchestration)

**Characteristics:**
- Master-slave architecture (Warden = master, Marshall = sub-master)
- Low-throughput, lightweight messages
- Time-triggered communication
- Prevents CANBUS congestion

---

## ORCHESTRATION HIERARCHY

```
┌─────────────────────────────────────────────────────────────────┐
│                      MISSION DEBRIEF (5)                        │
│                    [Final Report Output]                        │
└────────────────────────────▲────────────────────────────────────┘
                             │ CANBUS (Report delivery)
┌─────────────────────────────────────────────────────────────────┐
│                        WARDEN (2)                               │
│                  [System Controller]                            │
│  LINBUS: Controls Marshall, coordinates Evidence Locker         │
└─────────▼───────────────────────────────────────────────────────┘
          │ LINBUS (Orchestration commands)
┌─────────▼───────────────────────────────────────────────────────┐
│                       MARSHALL (3)                              │
│                 [Section Orchestrator]                          │
│  LINBUS: Sequences sections, manages wake/sleep                 │
│  CANBUS: Aggregates fault codes, reports progress               │
└─────────▼───────────────────────────────────────────────────────┘
          │ LINBUS (Wake/sleep commands)
          ├──► Section 1 (4-1) ◄──► CANBUS (Evidence + Faults)
          ├──► Section 2 (4-2) ◄──► CANBUS (Evidence + Faults)
          ├──► Section 3 (4-3) ◄──► CANBUS (Evidence + Faults)
          ├──► Section 4 (4-4) ◄──► CANBUS (Evidence + Faults)
          ├──► Section 5 (4-5) ◄──► CANBUS (Evidence + Faults)
          ├──► Section 6 (4-6) ◄──► CANBUS (Evidence + Faults)
          ├──► Section 7 (4-7) ◄──► CANBUS (Evidence + Faults)
          └──► Section 8 (4-8) ◄──► CANBUS (Evidence + Faults)
                     │
                     ▼ CANBUS (Evidence requests)
          ┌────────────────────────────────┐
          │   EVIDENCE LOCKER (1)          │
          │   [Data Provider]              │
          │   LINBUS: Throttle control     │
          │   CANBUS: Evidence delivery    │
          └────────────────────────────────┘
```

---

## SECTION DUAL-BUS OPERATION

### **"TWO SIGNALS, ONE SMOOTH OPERATION"**

Each section (4-1 through 4-8) operates on BOTH buses simultaneously:

#### **CANBUS (Work Channel - RECEIVES ALL SIGNALS)**
**What sections RECEIVE on CANBUS:**
- UDS → Section: `ROLLCALL` signals (health checks)
- Marshall → Section: Wake/sleep commands (nudge awake)
- Evidence Locker → Section: Evidence deliveries
- Gateway → Section: Revision requests

**What sections SEND on CANBUS:**
- Section → Evidence Locker: Evidence requests
- Section → Gateway: Section results publication
- Section → UDS: Fault codes (fallback if Marshall unavailable)

**Example CANBUS traffic:**
```
UDS → CANBUS: "ROLLCALL to Section 1" (health check)
Marshall → CANBUS: "Wake Section 1" (nudge awake signal)
Section 1 → CANBUS: "evidence.request" (Section 1 needs contract data)
Evidence Locker → CANBUS: "evidence.deliver" (Delivering to Section 1)
Section 1 → CANBUS: "section_1_profile.completed" (Results published)
```

---

#### **LINBUS (Talk Channel - RESPONSES TO MARSHALL)**
**What sections SEND on LINBUS:**
- Section → Marshall: `ROLLCALL` responses
- Section → Marshall: "Ready" status
- Section → Marshall: "Complete" status
- Section → Marshall: Fault codes (primary path)
- Section → Marshall: Wake acknowledgments

**Example LINBUS traffic:**
```
[Section receives ROLLCALL on CANBUS from UDS]
Section 1 → LINBUS: "ROLLCALL response: 10-4 operational"
Section 1 → LINBUS: "Ready to work"
Section 1 → LINBUS: "Work complete, ready to sleep"
Marshall aggregates responses → CANBUS to UDS
```

---

### **TRAFFIC SEPARATION BENEFIT:**

**Without LINBUS (everything on CANBUS):**
```
❌ CANBUS congested with:
   - UDS → 8 sections: ROLLCALL signals
   - 8 sections → UDS: ROLLCALL responses (8 separate messages)
   - 8 sections × wake/sleep acknowledgments
   - 8 sections × "ready" status pings
   - PLUS evidence data + fault codes
   = BOTTLENECK (16+ coordination messages flooding CANBUS)
```

**With LINBUS separation:**
```
✓ CANBUS carries:
   - UDS → Sections: ROLLCALL signals (inbound only)
   - Marshall → Sections: Wake/sleep commands (inbound only)
   - Evidence data (bidirectional)
   - Fault codes (outbound fallback only)
   - Report results (outbound)
   = CONTROLLED TRAFFIC

✓ LINBUS carries section responses:
   - 8 sections → Marshall: ROLLCALL responses
   - 8 sections → Marshall: Status updates
   - Marshall → UDS: Aggregated response (1 message)
   = NO CANBUS RESPONSE FLOOD
```

**Key Benefit:** UDS can monitor sections directly on CANBUS, but section responses don't flood the network - they route through Marshall on LINBUS.

---

## FAULT CODE ROUTING

### **Primary Path (Normal Operation):**
```
Section detects fault
  ↓ LINBUS (primary)
Marshall receives fault
  ↓ Aggregates faults from all 8 sections
  ↓ CANBUS (single message)
UDS monitors CANBUS
  ↓ Logs fault
  ↓ Generates diagnostic report
```

**Why:** Prevents 8 sections from flooding CANBUS with individual fault messages.

---

### **Fallback Path (Marshall Unavailable):**
```
Section detects fault
  ↓ LINBUS to Marshall - TIMEOUT
  ↓ CANBUS (direct emission)
UDS monitors CANBUS
  ↓ Logs fault directly
```

**Why:** Maintains system fault visibility even if Marshall is down.

---

### **Other System Faults (Non-Section):**
```
Evidence Locker / Warden / Mission Debrief / GUI
  ↓ CANBUS (direct emission)
UDS monitors CANBUS
  ↓ Logs fault
```

**Why:** Parent modules report directly; no aggregation needed.

---

## PARENT MODULE RESPONSIBILITIES

Each parent module (Evidence Locker, Warden, Marshall, Mission Debrief, GUI) is responsible for:

### **1. Health Monitoring**
- Initialize and monitor ALL child components
- Detect faults in child relationships
- Generate fault codes for each subsystem
- Report faults to UDS via CANBUS

### **2. Bus Ownership**
- Create and own ONE CANBUS connection
- Pass CANBUS reference to child/driven components
- Create LINBUS connection (if participating in orchestration)

### **3. Fault Reporting**
- Emit faults with proper identification:
  - `[PARENT_ADDRESS.CHILD_ADDRESS-FAULT_TYPE-LINE_NUMBER]`
  - Example: `[1.8-12-1345]` = Evidence Locker, OCR Processor, Missing dependency, Line 1345

### **4. Child Component Initialization**
- Pass `communicator_initializer` to children
- Ensure children have CANBUS access for operations
- Ensure children have LINBUS access (if orchestrated)

---

## EVIDENCE GATING & THROTTLING

**Problem:** If all 8 sections request evidence simultaneously, Evidence Locker becomes overwhelmed.

**Solution:** Marshall sequences section execution via LINBUS.

### **Flow:**
```
1. Warden → LINBUS → Marshall: "Begin case processing"
2. Marshall → LINBUS → Section 1: "Wake, process case"
3. Section 1 → CANBUS → Evidence Locker: "Request evidence"
4. Evidence Locker → CANBUS → Section 1: "Deliver evidence"
5. Section 1 processes data
6. Section 1 → CANBUS → Gateway: "Publish results"
7. Section 1 → LINBUS → Marshall: "Complete, ready to sleep"
8. Marshall → LINBUS → Section 1: "Sleep"
9. Marshall → LINBUS → Section 2: "Wake, process case"
10. [Repeat for Sections 2-8]
```

**Result:** Only 1-2 sections active at a time, Evidence Locker handles sequential requests smoothly.

---

## PARENT MODULE COORDINATION (LINBUS)

Parent modules use LINBUS to coordinate "ready for next step" states:

### **Example Scenario:**
```
Evidence Locker → LINBUS: "Evidence processed, ready to gate"
Marshall → LINBUS: "Hold, sections still processing previous batch"
Evidence Locker → LINBUS: "Acknowledged, holding gate"

[... time passes ...]

Marshall → LINBUS: "All sections complete, ready for next batch"
Evidence Locker → LINBUS: "Gate open, delivering next batch"
```

**Purpose:** Prevents race conditions and ensures synchronized workflow.

---

## UDS MONITORING

### **What UDS Monitors:**
- **CANBUS only** (fault codes, system health)
- Receives fault emissions from all systems
- Logs faults to diagnostic reports
- Generates system-wide health status

### **What UDS Does NOT Monitor:**
- **LINBUS** (orchestration traffic)
- Wake/sleep commands
- Ready state signals
- Parent coordination messages

**Why:** UDS focuses on fault detection, not operational orchestration.

---

## COMMUNICATION STANDARDS

### **CANBUS Signal Topics:**
- `'evidence.request'` - Section requesting evidence
- `'evidence.deliver'` - Evidence Locker delivering evidence
- `'evidence.updated'` - Evidence metadata updated
- `'section_X.completed'` - Section finished processing
- `'communication'` - Universal signal topic (radio codes embedded)
- `'case.snapshot'` - Case state snapshot
- `'gateway.status'` - Gateway status update

### **CANBUS Radio Codes (on 'communication' topic):**
- `'SOS'` - Critical fault requiring immediate attention
- `'MAYDAY'` - System-wide emergency
- `'ROLLCALL'` - System status check
- `'10-4'` - Acknowledgment
- `'10-9'` - Repeat/clarification needed
- `'10-10'` - Out of service / sleeping

### **LINBUS Signal Topics:**
- `'section.rollcall.response'` - Section ROLLCALL response to Marshall
- `'section.ready'` - Section ready for work
- `'section.complete'` - Section finished work
- `'section.fault'` - Section fault code (primary path to Marshall)
- `'marshall.aggregate'` - Marshall aggregated responses to UDS
- `'warden.orchestrate'` - System orchestration command
- `'throttle.hold'` - Hold evidence gating
- `'throttle.release'` - Release evidence gate

**Note:** Wake/sleep commands are sent on CANBUS (from Marshall to sections), not LINBUS. Sections respond on LINBUS.

---

## MESSAGE PAYLOAD STANDARDS

### **Fault Report Payload (CANBUS):**
```python
{
    "fault_code": "[1.8-12-1345]",  # Format: [ADDRESS-TYPE-LINE]
    "description": "OCR Processor not initialized",
    "component": "OCR Processor",
    "reporting_address": "1.8",
    "parent_address": "1",
    "severity": "CRITICAL",  # CRITICAL | ERROR | WARNING
    "timestamp": "2025-10-11T14:30:00",
    "fault_type": "12",
    "fault_type_description": "Missing initialization dependency"
}
```

### **Evidence Request Payload (CANBUS):**
```python
{
    "section_id": "4-1",
    "evidence_id": "EV-12345-001",
    "request_type": "contract_data",
    "timestamp": "2025-10-11T14:30:00",
    "priority": "normal"  # normal | high | urgent
}
```

### **Wake Command Payload (CANBUS):**
```python
{
    "target_section": "4-1",
    "case_id": "CASE-12345",
    "operation": "wake",
    "timestamp": "2025-10-11T14:30:00"
}
```

### **ROLLCALL Response Payload (LINBUS):**
```python
{
    "section_id": "4-1",
    "radio_code": "10-4",
    "status": "operational",
    "timestamp": "2025-10-11T14:30:00",
    "target": "3"  # Marshall address
}
```

### **Ready Status Payload (LINBUS):**
```python
{
    "section_id": "4-1",
    "status": "ready",  # ready | working | complete | sleeping
    "timestamp": "2025-10-11T14:30:00"
}
```

---

## IMPLEMENTATION REQUIREMENTS

### **Parent Module Initialization:**
```python
class ParentModule:
    def __init__(self, bus_connection=None):
        # CANBUS connection (required)
        self.bus = bus_connection or DKIReportBus()
        self.communicator = UniversalCommunicator(
            system_address=self.MODULE_ADDRESS,
            bus_connection=self.bus
        )
        
        # LINBUS connection (if orchestrated)
        if self.participates_in_orchestration():
            self.linbus = self._initialize_linbus()
        
        # Child component initialization
        self._initialize_children()
    
    def _create_child_communicator(self, child_address):
        """Factory for child communicators (shares parent's bus)"""
        return UniversalCommunicator(
            system_address=child_address,
            bus_connection=self.bus  # Share CANBUS
        )
    
    def _initialize_children(self):
        """Pass communicator_initializer to all children"""
        self.child = ChildComponent(
            communicator_initializer=lambda addr: self._create_child_communicator(addr)
        )
```

---

### **Section Initialization (Dual-Bus):**
```python
class Section1Framework:
    def __init__(
        self,
        gateway=None,
        marshal_client=None,
        communicator_initializer=None,  # CANBUS
        linbus_initializer=None,        # LINBUS
        **kwargs
    ):
        # CANBUS (for evidence + fault fallback)
        if communicator_initializer:
            self.communicator = communicator_initializer(self.MODULE_ADDRESS)
            self.bus = getattr(self.communicator, "bus_connection", None)
        
        # LINBUS (for wake/sleep coordination)
        if linbus_initializer:
            self.linbus = linbus_initializer(self.MODULE_ADDRESS)
        
        # Marshall reference (for primary fault reporting)
        self.marshal_client = marshal_client
```

---

## SYSTEM BENEFITS

### **1. Traffic Separation**
- Heavy data on CANBUS
- Lightweight coordination on LINBUS
- No congestion or bottlenecks

### **2. Orchestration Control**
- Marshall sequences section execution
- Evidence Locker handles requests sequentially
- No overwhelming of data providers

### **3. Fault Redundancy**
- Sections report to Marshall (primary)
- Sections report to CANBUS (fallback)
- UDS always receives faults

### **4. Scalability**
- Add more sections without CANBUS congestion
- LINBUS handles coordination overhead
- CANBUS stays clean for data

### **5. Clear Separation of Concerns**
- CANBUS = Data & faults (what UDS monitors)
- LINBUS = Orchestration (what UDS ignores)
- Each bus has defined purpose

---

## TROUBLESHOOTING

### **Section cannot request evidence:**
- **Check:** Section has CANBUS communicator initialized
- **Check:** Evidence Locker registered on CANBUS
- **Check:** Section using correct signal topic (`'evidence.request'`)

### **Section faults not reaching UDS:**
- **Check:** Marshall aggregating faults to CANBUS
- **Check:** Section emitting to CANBUS if Marshall down
- **Check:** UDS monitoring `'communication'` topic

### **Sections not waking/sleeping:**
- **Check:** Section has LINBUS connection initialized
- **Check:** Marshall sending commands on LINBUS
- **Check:** Section listening to correct LINBUS topics

### **Evidence bottleneck:**
- **Check:** Marshall sequencing sections (not all awake simultaneously)
- **Check:** LINBUS orchestration functioning
- **Check:** Evidence Locker throttle coordination

---

## RELATED DOCUMENTATION

- `MASTER_DIAGNOSTIC_PROTOCOL_2025-10-05.md` - Fault code definitions
- `system_registry.json` - System address registry
- `universal_communicator.py` - CANBUS communication implementation
- `COMPLETE_ARCHITECTURE_FIX_REQUIRED_2025-10-11.md` - Implementation fixes needed

---

**This architecture ensures "two signals, one smooth operation" - CANBUS for heavy lifting, LINBUS for coordination.**

