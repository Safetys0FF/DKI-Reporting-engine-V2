# DKI ENGINE: MASTER COMMUNICATION MATRIX
**Version:** 1.0  
**Date:** 2025-10-11  
**Purpose:** Complete system communication flow reference

---

## QUICK REFERENCE: WHO TALKS TO WHOM

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CANBUS NETWORK                                  │
│  (Heavy Lifting: Evidence, Reports, Faults, UDS Monitoring)            │
└─────────────────────────────────────────────────────────────────────────┘
    ↕          ↕          ↕          ↕          ↕          ↕          ↕
┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐
│ GUI-1 │ │ EV-1  │ │ WARD-2│ │ MRSH-3│ │ SEC   │ │ MSND-5│ │ UDS   │
│       │ │ LOCKER│ │       │ │       │ │ 4-1:8 │ │ DEBRIEF│ │ DIAG-1│
└───────┘ └───────┘ └───────┘ └───┬───┘ └───────┘ └───────┘ └───────┘
                                   │
                                   │ Marshall = LINBUS Master
                                   │
┌──────────────────────────────────┼─────────────────────────────────────┐
│                         LINBUS NETWORK                                  │
│  (Coordination: Responses, Status, Sequencing)                         │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    ↕                             ↕
        ┌───────────────────────┐   ┌───────────────────────┐
        │  Sections 4-1 to 4-8  │   │ Parent Coordination   │
        │  (Analyst Deck)       │   │ (Warden, EV Locker,   │
        │                       │   │  Mission Debrief)     │
        └───────────────────────┘   └───────────────────────┘
```

---

## SYSTEM-BY-SYSTEM COMMUNICATION MATRIX

### **GUI (GUI-1)**

| **Communicates With** | **Bus** | **Direction** | **Signal/Topic** | **Purpose** |
|----------------------|---------|---------------|------------------|-------------|
| CANBUS Core | CANBUS | Send/Receive | `user_authenticate` | User login |
| CANBUS Core | CANBUS | Send | `case_create` | Create new case |
| CANBUS Core | CANBUS | Send | `files_add` | Upload evidence files |
| Evidence Locker (1) | CANBUS | Receive | `locker.status` | Evidence processing status |
| Mission Debrief (5) | CANBUS | Receive | `mission.status` | Report generation status |
| UDS (DIAG-1) | CANBUS | Receive | `diagnostic.status` | System health display |
| **LINBUS** | N/A | N/A | N/A | **Not connected** |

---

### **Evidence Locker (1)**

| **Communicates With** | **Bus** | **Direction** | **Signal/Topic** | **Purpose** |
|----------------------|---------|---------------|------------------|-------------|
| GUI (GUI-1) | CANBUS | Send | `locker.status` | Processing status updates |
| Sections (4-1 to 4-8) | CANBUS | Receive | `evidence.request` | Section requests evidence |
| Sections (4-1 to 4-8) | CANBUS | Send | `evidence.deliver` | Deliver evidence to section |
| Sections (4-1 to 4-8) | CANBUS | Send | `evidence.updated` | Evidence metadata changed |
| Marshall (3) | CANBUS | Send | `evidence.new` | New evidence processed |
| Warden (2) | CANBUS | Receive | `warden.orchestrate` | Orchestration commands |
| UDS (DIAG-1) | CANBUS | Send | `communication` (SOS) | Fault reporting |
| Warden (2) | LINBUS | Send/Receive | `throttle.hold/release` | Evidence gating coordination |
| Marshall (3) | LINBUS | Send/Receive | `throttle.hold/release` | Section coordination |

---

### **Warden (2)**

| **Communicates With** | **Bus** | **Direction** | **Signal/Topic** | **Purpose** |
|----------------------|---------|---------------|------------------|-------------|
| Evidence Locker (1) | CANBUS | Send | `warden.orchestrate` | Control evidence processing |
| Marshall (3) | CANBUS | Send | `warden.orchestrate` | Control section orchestration |
| Mission Debrief (5) | CANBUS | Send | `warden.orchestrate` | Control report generation |
| UDS (DIAG-1) | CANBUS | Send | `communication` (SOS) | Fault reporting |
| Evidence Locker (1) | LINBUS | Send/Receive | `throttle.hold/release` | Throttle coordination |
| Marshall (3) | LINBUS | Send | `warden.orchestrate` | Sequencing commands |
| Mission Debrief (5) | LINBUS | Send/Receive | Ready state coordination | Workflow sync |

---

### **Marshall (3) - LINBUS MASTER**

| **Communicates With** | **Bus** | **Direction** | **Signal/Topic** | **Purpose** |
|----------------------|---------|---------------|------------------|-------------|
| **CANBUS COMMUNICATION** |
| Warden (2) | CANBUS | Receive | `warden.orchestrate` | Receive orchestration commands |
| Sections (4-1 to 4-8) | CANBUS | Send | `marshall.wake` | Wake section for processing |
| Sections (4-1 to 4-8) | CANBUS | Send | `marshall.sleep` | Put section to sleep |
| Evidence Locker (1) | CANBUS | Receive | `evidence.new` | New evidence available |
| Mission Debrief (5) | CANBUS | Send | Section progress reports | Report section completion |
| UDS (DIAG-1) | CANBUS | Send | `communication` (SOS) | Aggregated fault reporting |
| **LINBUS COMMUNICATION (MASTER)** |
| Sections (4-1 to 4-8) | LINBUS | Receive | `section.rollcall.response` | Section health responses |
| Sections (4-1 to 4-8) | LINBUS | Receive | `section.ready` | Section ready for work |
| Sections (4-1 to 4-8) | LINBUS | Receive | `section.complete` | Section work complete |
| Sections (4-1 to 4-8) | LINBUS | Receive | `section.fault` | Section fault codes |
| Warden (2) | LINBUS | Receive | `warden.orchestrate` | Sequencing instructions |
| Evidence Locker (1) | LINBUS | Send/Receive | `throttle.hold/release` | Throttle coordination |
| UDS (DIAG-1) | CANBUS | Send | `marshall.aggregate` | Aggregated section responses |

---

### **Sections 4-1 through 4-8 (Analyst Deck)**

| **Communicates With** | **Bus** | **Direction** | **Signal/Topic** | **Purpose** |
|----------------------|---------|---------------|------------------|-------------|
| **CANBUS COMMUNICATION (RECEIVE ALL SIGNALS)** |
| UDS (DIAG-1) | CANBUS | Receive | `ROLLCALL` | Health check from UDS |
| Marshall (3) | CANBUS | Receive | `marshall.wake` | Wake command |
| Marshall (3) | CANBUS | Receive | `marshall.sleep` | Sleep command |
| Evidence Locker (1) | CANBUS | Send | `evidence.request` | Request evidence |
| Evidence Locker (1) | CANBUS | Receive | `evidence.deliver` | Receive evidence |
| Gateway (3-3) | CANBUS | Send | `section_X.completed` | Publish results |
| Gateway (3-3) | CANBUS | Receive | Revision requests | Revision needed |
| UDS (DIAG-1) | CANBUS | Send | `communication` (SOS) | Fault fallback (Marshall down) |
| **LINBUS COMMUNICATION (RESPONSES TO MARSHALL)** |
| Marshall (3) | LINBUS | Send | `section.rollcall.response` | Respond to ROLLCALL |
| Marshall (3) | LINBUS | Send | `section.ready` | Ready to work |
| Marshall (3) | LINBUS | Send | `section.complete` | Work complete |
| Marshall (3) | LINBUS | Send | `section.fault` | Fault code (primary) |

---

### **Mission Debrief (5)**

| **Communicates With** | **Bus** | **Direction** | **Signal/Topic** | **Purpose** |
|----------------------|---------|---------------|------------------|-------------|
| Warden (2) | CANBUS | Receive | `warden.orchestrate` | Workflow commands |
| Marshall (3) | CANBUS | Receive | Section progress reports | Track section completion |
| Gateway (3-3) | CANBUS | Receive | All section results | Collect section outputs |
| GUI (GUI-1) | CANBUS | Send | `mission.status` | Report generation status |
| UDS (DIAG-1) | CANBUS | Send | `communication` (SOS) | Fault reporting |
| Warden (2) | LINBUS | Send/Receive | Ready state coordination | Workflow sync |

---

### **UDS (DIAG-1 / Bus-1)**

| **Communicates With** | **Bus** | **Direction** | **Signal/Topic** | **Purpose** |
|----------------------|---------|---------------|------------------|-------------|
| ALL Systems | CANBUS | Send | `ROLLCALL` | Health check ping |
| ALL Systems | CANBUS | Receive | `communication` (SOS) | Fault code reception |
| Sections (4-1 to 4-8) | CANBUS | Send | `ROLLCALL` | Direct section health check |
| Marshall (3) | CANBUS | Receive | `marshall.aggregate` | Aggregated section responses |
| ALL Systems | CANBUS | Receive | `diagnostic.ping` response | Connectivity validation |
| **LINBUS** | N/A | N/A | N/A | **Does not monitor LINBUS** |

---

## SIGNAL FLOW CHARTS

### **1. SYSTEM STARTUP SEQUENCE**

```
1. CANBUS Core initializes
2. UDS (DIAG-1) connects to CANBUS
3. Parent modules connect to CANBUS:
   ├─ Evidence Locker (1)
   ├─ Warden (2)
   ├─ Marshall (3)
   ├─ Mission Debrief (5)
   └─ GUI (GUI-1)
4. LINBUS network initializes
5. Marshall becomes LINBUS master
6. Sections 4-1 to 4-8 connect:
   ├─ CANBUS connection (evidence + monitoring)
   └─ LINBUS connection (Marshall coordination)
7. UDS sends ROLLCALL to all systems
8. Marshall aggregates section responses
9. System ready
```

---

### **2. EVIDENCE REQUEST FLOW**

```
Section 1 needs evidence:

1. Section 1 → CANBUS → Evidence Locker
   Signal: "evidence.request"
   Payload: {evidence_id, section_id, request_type}

2. Evidence Locker processes request

3. Evidence Locker → CANBUS → Section 1
   Signal: "evidence.deliver"
   Payload: {evidence_id, evidence_data, metadata}

4. Section 1 processes evidence

5. Section 1 → CANBUS → Gateway
   Signal: "section_1.completed"
   Payload: {section_results}

6. Section 1 → LINBUS → Marshall
   Signal: "section.complete"
   Payload: {section_id, status: "complete"}
```

---

### **3. FAULT REPORTING FLOW (PRIMARY PATH)**

```
Section 1 tool fails:

1. Section 1 detects fault (e.g., Tesseract engine = None)

2. Section 1 → LINBUS → Marshall
   Signal: "section.fault"
   Payload: {
     fault_code: "[4-1.8-12-INIT]",
     description: "Tesseract Engine not initialized",
     severity: "CRITICAL"
   }

3. Marshall receives fault from Section 1

4. Marshall aggregates faults (if multiple)

5. Marshall → CANBUS → UDS (DIAG-1)
   Signal: "communication"
   Radio Code: "SOS"
   Payload: {
     fault_code: "[4-1.8-12-INIT]",
     parent_address: "3",
     reporting_address: "4-1.8"
   }

6. UDS logs fault and generates diagnostic report
```

---

### **4. FAULT REPORTING FLOW (FALLBACK PATH)**

```
Section 1 tool fails + Marshall is down:

1. Section 1 detects fault

2. Section 1 → LINBUS → Marshall (TIMEOUT - no response)

3. Section 1 activates fallback

4. Section 1 → CANBUS → UDS (DIAG-1)
   Signal: "communication"
   Radio Code: "SOS"
   Payload: {
     fault_code: "[4-1.8-12-INIT]",
     description: "Tesseract Engine not initialized",
     severity: "CRITICAL",
     note: "Marshall unavailable - direct emission"
   }

5. UDS logs fault directly (no Marshall aggregation)
```

---

### **5. UDS ROLLCALL SEQUENCE**

```
UDS health check:

1. UDS → CANBUS → ALL SYSTEMS
   Signal: "ROLLCALL"
   Target: Broadcast to all registered addresses

2a. Parent modules respond directly:
   Evidence Locker → CANBUS → UDS: "10-4 operational"
   Warden → CANBUS → UDS: "10-4 operational"
   Mission Debrief → CANBUS → UDS: "10-4 operational"
   GUI → CANBUS → UDS: "10-4 operational"

2b. Sections respond via Marshall:
   Section 1 → LINBUS → Marshall: "10-4 operational"
   Section 2 → LINBUS → Marshall: "10-4 operational"
   Section 3 → LINBUS → Marshall: "10-4 operational"
   ... (all 8 sections)

3. Marshall aggregates section responses

4. Marshall → CANBUS → UDS
   Signal: "marshall.aggregate"
   Payload: {
     sections: {
       "4-1": "10-4 operational",
       "4-2": "10-4 operational",
       ... (all 8)
     }
   }

5. UDS compiles system health report
```

---

### **6. SECTION ORCHESTRATION SEQUENCE**

```
Marshall sequences section execution:

1. Warden → LINBUS → Marshall: "Begin case processing"

2. Marshall → CANBUS → Section 1: "Wake"
   Signal: "marshall.wake"
   Payload: {case_id, operation: "wake"}

3. Section 1 → LINBUS → Marshall: "Ready"
   Signal: "section.ready"

4. Section 1 requests evidence (CANBUS flow)

5. Section 1 processes evidence

6. Section 1 publishes results (CANBUS)

7. Section 1 → LINBUS → Marshall: "Complete"
   Signal: "section.complete"

8. Marshall → CANBUS → Section 1: "Sleep"
   Signal: "marshall.sleep"

9. Marshall → CANBUS → Section 2: "Wake"
   [Repeat for Sections 2-8]

10. Marshall → CANBUS → Mission Debrief: "All sections complete"
```

---

### **7. THROTTLE COORDINATION FLOW**

```
Evidence Locker throttle management:

1. Evidence Locker processes batch of evidence

2. Evidence Locker → LINBUS → Warden: "Ready to gate next batch"
   Signal: "throttle.release"

3. Warden checks Marshall status via LINBUS

4. Marshall → LINBUS → Warden: "Sections still processing"
   Signal: "throttle.hold"

5. Warden → LINBUS → Evidence Locker: "Hold gate"
   Signal: "throttle.hold"

6. Evidence Locker holds processing

[... time passes ...]

7. Marshall → LINBUS → Warden: "All sections complete"

8. Warden → LINBUS → Evidence Locker: "Release gate"
   Signal: "throttle.release"

9. Evidence Locker processes next batch
```

---

## RADIO CODE REFERENCE

| **Radio Code** | **Meaning** | **Used By** | **Bus** | **Context** |
|---------------|-------------|-------------|---------|-------------|
| `SOS` | Critical fault | All systems | CANBUS | Fault reporting to UDS |
| `MAYDAY` | System-wide emergency | Parent modules | CANBUS | Catastrophic failure |
| `ROLLCALL` | Health check request | UDS | CANBUS | System status validation |
| `10-4` | Acknowledged / OK | All systems | CANBUS/LINBUS | Acknowledgment |
| `10-9` | Repeat message | All systems | CANBUS | Request clarification |
| `10-10` | Out of service | Sections | CANBUS/LINBUS | Section sleeping |
| `10-8` | In service | Sections | CANBUS/LINBUS | Section active |
| `10-6` | Busy | All systems | CANBUS/LINBUS | Processing, standby |

---

## SIGNAL TOPIC DIRECTORY

### **CANBUS Topics:**

| **Topic** | **Sender** | **Receiver** | **Purpose** |
|-----------|-----------|--------------|-------------|
| `'communication'` | All systems | UDS, targets | Universal signal transport (radio codes embedded) |
| `'evidence.request'` | Sections | Evidence Locker | Request evidence |
| `'evidence.deliver'` | Evidence Locker | Sections | Deliver evidence |
| `'evidence.new'` | Evidence Locker | Marshall | New evidence processed |
| `'evidence.updated'` | Evidence Locker | Sections | Evidence metadata changed |
| `'section_X.completed'` | Section X | Gateway | Section results |
| `'case.snapshot'` | Any | Any | Case state snapshot |
| `'gateway.status'` | Gateway | Mission Debrief | Gateway status |
| `'locker.status'` | Evidence Locker | GUI | Processing status |
| `'mission.status'` | Mission Debrief | GUI | Report status |
| `'diagnostic.status'` | UDS | GUI | System health |
| `'warden.orchestrate'` | Warden | Marshall, Evidence Locker, Mission Debrief | Orchestration commands |
| `'marshall.wake'` | Marshall | Sections | Wake section |
| `'marshall.sleep'` | Marshall | Sections | Sleep section |

### **LINBUS Topics:**

| **Topic** | **Sender** | **Receiver** | **Purpose** |
|-----------|-----------|--------------|-------------|
| `'section.rollcall.response'` | Sections | Marshall | ROLLCALL response |
| `'section.ready'` | Sections | Marshall | Section ready |
| `'section.complete'` | Sections | Marshall | Section complete |
| `'section.fault'` | Sections | Marshall | Section fault code |
| `'marshall.aggregate'` | Marshall | UDS (via CANBUS) | Aggregated responses |
| `'throttle.hold'` | Warden, Marshall | Evidence Locker | Hold evidence gating |
| `'throttle.release'` | Warden, Marshall | Evidence Locker | Release evidence gate |
| `'warden.orchestrate'` | Warden | Marshall | Sequencing instructions |

---

## CONNECTION SUMMARY TABLE

| **System** | **Address** | **CANBUS** | **LINBUS** | **Role** |
|-----------|-------------|-----------|-----------|----------|
| GUI | GUI-1 | ✓ Connected | ✗ Not connected | User interface |
| Evidence Locker | 1 | ✓ Connected | ✓ Connected | Data provider + throttle coordination |
| Warden | 2 | ✓ Connected | ✓ Master | System controller |
| Marshall | 3 | ✓ Connected | ✓ Sub-master | Section orchestrator + LINBUS master for sections |
| Section 1 | 4-1 | ✓ Connected | ✓ Connected | Worker (receives CANBUS, responds LINBUS) |
| Section 2 | 4-2 | ✓ Connected | ✓ Connected | Worker (receives CANBUS, responds LINBUS) |
| Section 3 | 4-3 | ✓ Connected | ✓ Connected | Worker (receives CANBUS, responds LINBUS) |
| Section 4 | 4-4 | ✓ Connected | ✓ Connected | Worker (receives CANBUS, responds LINBUS) |
| Section 5 | 4-5 | ✓ Connected | ✓ Connected | Worker (receives CANBUS, responds LINBUS) |
| Section 6 | 4-6 | ✓ Connected | ✓ Connected | Worker (receives CANBUS, responds LINBUS) |
| Section 7 | 4-7 | ✓ Connected | ✓ Connected | Worker (receives CANBUS, responds LINBUS) |
| Section 8 | 4-8 | ✓ Connected | ✓ Connected | Worker (receives CANBUS, responds LINBUS) |
| Mission Debrief | 5 | ✓ Connected | ✓ Connected | Final output + workflow coordination |
| UDS | DIAG-1 (Bus-1) | ✓ Connected | ✗ Does not monitor | Fault monitoring and diagnostics |

---

## TRAFFIC ANALYSIS

### **CANBUS Load Estimate (per case):**

| **Traffic Type** | **Message Count** | **Notes** |
|-----------------|------------------|-----------|
| UDS ROLLCALL (outbound) | ~15 messages | 1 broadcast to all systems |
| Parent module responses | ~5 messages | Direct responses to UDS |
| Section wake/sleep | ~16 messages | Marshall → 8 sections × 2 |
| Evidence requests | ~8 messages | 1 per section |
| Evidence deliveries | ~8 messages | 1 per section |
| Section results | ~8 messages | 1 per section |
| Fault codes (normal) | ~0-5 messages | Only on faults |
| Case/status updates | ~10-20 messages | Various status updates |
| **TOTAL** | **~70-80 messages** | **Per case, normal operation** |

### **LINBUS Load Estimate (per case):**

| **Traffic Type** | **Message Count** | **Notes** |
|-----------------|------------------|-----------|
| Section ROLLCALL responses | ~8 messages | 1 per section |
| Section ready signals | ~8 messages | 1 per section |
| Section complete signals | ~8 messages | 1 per section |
| Section fault codes | ~0-10 messages | Only on faults |
| Marshall aggregate to UDS | ~1 message | Single aggregated report |
| Throttle coordination | ~2-5 messages | Hold/release signals |
| **TOTAL** | **~27-40 messages** | **Per case, normal operation** |

**Traffic separation benefit:** Without LINBUS, CANBUS would handle ~97-120 messages per case instead of ~70-80.

---

## IMPLEMENTATION CHECKLIST

### **For CANBUS Implementation:**
- [ ] All parent modules create CANBUS connection
- [ ] Sections receive CANBUS connection from Marshall
- [ ] UDS monitors `'communication'` topic on CANBUS
- [ ] All systems emit faults on CANBUS with SOS radio code
- [ ] Evidence requests/deliveries use CANBUS
- [ ] Wake/sleep commands use CANBUS

### **For LINBUS Implementation:**
- [ ] Marshall creates LINBUS master connection
- [ ] Sections receive LINBUS connection for responses
- [ ] Sections send ROLLCALL responses on LINBUS
- [ ] Sections send status updates on LINBUS
- [ ] Marshall aggregates section responses
- [ ] Parent modules use LINBUS for throttle coordination
- [ ] UDS does NOT monitor LINBUS

---

**This master matrix provides complete visibility into all system communication flows.**

