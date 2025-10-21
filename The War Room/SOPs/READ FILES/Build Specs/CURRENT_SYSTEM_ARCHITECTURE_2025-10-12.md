# CENTRAL COMMAND - SYSTEM ARCHITECTURE
## Current Build Analysis (2025-10-12)

**Document Type:** Technical Architecture Analysis  
**Status:** CURRENT  
**Version:** October 2025 Build  
**Audience:** System Architects, Developers, Operations

---

## TABLE OF CONTENTS

1. [Executive Summary](#executive-summary)
2. [System Overview](#system-overview)
3. [The 7 Parent Modules](#the-7-parent-modules)
4. [Communication Architecture](#communication-architecture)
5. [Parent-Child Relationships](#parent-child-relationships)
6. [Message Lifecycle Protocol](#message-lifecycle-protocol)
7. [Operational Flow](#operational-flow)
8. [Fault Code System](#fault-code-system)
9. [System Integration Points](#system-integration-points)
10. [Technical Implementation](#technical-implementation)
11. [Current Build Status](#current-build-status)
12. [Known Issues and Limitations](#known-issues-and-limitations)

---

## EXECUTIVE SUMMARY

Central Command is an autonomous investigative report generation system implementing a **7-module parent architecture** with dual-bus communication infrastructure (CANBUS + LINBUS). The system ingests raw evidence, performs automated analysis across 8 specialized sections, and produces professionally formatted investigative reports with minimal human intervention.

### Key Architectural Decisions

1. **Parent-Child Hierarchy:** 7 parent modules coordinate 65 total system components
2. **Dual-Bus Design:** CANBUS for data, LINBUS for orchestration
3. **Signal-Based Communication:** Pub/sub architecture with lifecycle enforcement
4. **Delegated Testing:** Parents test children, UDS monitors parents
5. **Fault Code System:** Standardized fault reporting and validation

---

## SYSTEM OVERVIEW

### System Purpose

**Primary Mission:** Automate investigative report generation from evidence intake to final publication.

**Target Users:**
- Investigators requiring comprehensive evidence analysis
- Legal professionals needing formatted reports
- Organizations processing large volumes of investigative data

### High-Level Architecture

```
┌───────────────────────────────────────────────────────────────────────┐
│                     CENTRAL COMMAND SYSTEM                             │
├───────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                  UNIFIED DIAGNOSTIC SYSTEM (DIAG-1)          │   │
│  │              Health Monitoring & Protocol Enforcement         │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                 │                                     │
│                                 │ monitors                            │
│                                 ▼                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │               CANBUS (Central Command Bus - Bus-1)           │   │
│  │           Signal-Based Communication Infrastructure          │   │
│  └───────────┬──────────┬──────────┬──────────┬──────────┬──────┘   │
│              │          │          │          │          │           │
│      ┌───────┴─┐   ┌───┴────┐  ┌─┴──────┐ ┌─┴────────┐ │           │
│      │ Module 1│   │Module  │  │Module 3│ │ Module 5 │ │           │
│      │Evidence │   │  2-1   │  │Marshall│ │ Mission  │ │           │
│      │ Locker  │   │ Warden │  │        │ │ Debrief  │ │           │
│      └─────────┘   └───┬────┘  └───┬────┘ └──────────┘ │           │
│                        │            │                    │           │
│                        │ LINBUS     │ LINBUS            ┌┴────────┐ │
│                        │ Master     │ Sub-Master        │  GUI-1  │ │
│                        │            │                   └─────────┘ │
│                        ▼            ▼                                │
│                   ┌─────────┐  ┌──────────────────────────┐        │
│                   │ECC(2-2) │  │  Analyst Deck (4-1...4-8)│        │
│                   │Gateway  │  │  (LINBUS connected)       │        │
│                   │ (2-3)   │  └──────────────────────────┘        │
│                   └─────────┘                                        │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### System Components Count

- **Parent Modules:** 7 (Bus-1, DIAG-1, 1, 2-1, 3, 5, GUI-1)
- **Total Registered Components:** 65 (as of 2025-10-12)
- **Analyst Sections:** 8 (4-1 through 4-8, LINBUS-connected)
- **Communication Buses:** 2 (CANBUS, LINBUS)

---

## THE 7 PARENT MODULES

### Module 1: Evidence Locker
**Address:** 1  
**Type:** Evidence Management  
**File:** `Evidence Locker/evidence_locker_module.py`

**Primary Responsibilities:**
- Evidence ingestion and validation
- File classification (image, document, video, etc.)
- Case manifest generation
- Section relevance scoring
- Evidence indexing

**Child Components (8):**
- 1.1: Evidence Classifier
- 1.2: Evidence Indexer
- 1.3: Manifest Builder
- 1.4: Section Registry
- 1.5: Case Manifest Builder
- 1.6: Evidence Index Manager
- 1.7: Static Data Flow
- 1.8: Bus Extensions

**Bus Connections:**
- CANBUS (primary communication)
- LINBUS (throttle coordination with Warden)

**Fault Code Range:** 1.00 - 1.99

---

### Module 2-1: The Warden
**Address:** 2-1  
**Type:** System Orchestration  
**File:** `The Warden/warden_module.py`

**Primary Responsibilities:**
- Master system orchestration
- Ecosystem control (boot order, dependencies, lifecycle)
- Gateway management (evidence routing to sections)
- LINBUS master control
- Mission status aggregation

**Child Components (2 + sub-components):**
- 2-2: Ecosystem Controller (ECC)
  - 2-2.1, 2-2.2, 2-2.3, 2-2.4: ECC internals
- 2-3: Gateway Controller
  - 2-3.1, 2-3.2, 2-3.3, 2-3.4: Gateway internals

**Bus Connections:**
- CANBUS (coordination)
- LINBUS (master controller)

**Fault Code Range:** 2.00 - 2.99

---

### Module 3: The Marshall
**Address:** 3  
**Type:** Evidence Distribution & LINBUS Proxy  
**File:** `The Marshall/marshall_module.py`

**Primary Responsibilities:**
- Evidence distribution to Analyst sections
- LINBUS sub-master (Analyst Deck proxy)
- Section wake/sleep coordination
- Section result aggregation
- LINBUS-to-CANBUS message translation

**Child Components (3 direct):**
- 3-1: Evidence Manager
- 3-2: Section Processor (reserved)
- 3-3: Media Processor (reserved)

**Proxied Components (8 via LINBUS):**
- 4-1: Analyst Section 1 (Table of Contents)
- 4-2: Analyst Section 2 (Cover Page)
- 4-3: Analyst Section 3 (Executive Summary)
- 4-4: Analyst Section 4 (Evidence Analysis)
- 4-5: Analyst Section 5 (Timeline Construction)
- 4-6: Analyst Section 6 (Findings and Conclusions)
- 4-7: Analyst Section 7 (Recommendations)
- 4-8: Analyst Section 8 (Appendices)

**Bus Connections:**
- CANBUS (primary communication)
- LINBUS (sub-master for Analyst sections)

**Fault Code Range:** 3.00 - 3.99

**Note:** Marshall does NOT own Analyst sections - it proxies LINBUS communication between them and CANBUS.

---

### Module 5: Mission Debrief
**Address:** 5  
**Type:** Report Finalization  
**File:** `Command Center/Mission Debrief/mission_debrief_module.py`

**Primary Responsibilities:**
- Narrative assembly from section outputs
- Report generation and formatting
- Professional tooling (signatures, watermarks, metadata)
- Library archival
- Multi-format export (PDF, DOCX)

**Child Components (2 + sub-components):**
- 5-1: Debrief Manager
  - 5-1.1: Narrative Engine
  - 5-1.2: Template Manager
- 5-2: The Librarian
  - 5-2.1, 5-2.2, 5-2.3, 5-2.4: Archive management

**Bus Connections:**
- CANBUS (primary communication)
- LINBUS (throttle coordination with Warden)

**Fault Code Range:** 5.00 - 5.99

---

### Module Bus-1: Central Command Bus
**Address:** Bus-1  
**Type:** Communication Infrastructure  
**File:** `Command Center/Data Bus/Bus Core Design/bus_core.py`

**Primary Responsibilities:**
- Message routing between modules
- Signal registration and distribution
- Event logging and audit trail
- System state management
- Module address registry

**Child Components (5 internal):**
- Bus-1.1: Signal Registry
- Bus-1.2: Event Logger
- Bus-1.3: State Manager
- Bus-1.4: Address Registry
- Bus-1.5: Health Monitor

**Bus Connections:**
- Is the CANBUS itself

**Fault Code Range:** Bus-1.00 - Bus-1.99

---

### Module GUI-1: Enhanced Functional GUI
**Address:** GUI-1  
**Type:** User Interface  
**File:** `Command Center/UI/enhanced_functional_gui.py`

**Primary Responsibilities:**
- Desktop application interface (Tkinter)
- Case management (create, open, manage)
- Evidence upload interface
- Real-time status monitoring
- Report viewing

**Child Components (9):**
- GUI-1.1: Case Manager UI
- GUI-1.2: Evidence Upload UI
- GUI-1.3: Status Dashboard
- GUI-1.4: Report Viewer
- GUI-1.5: Section Monitor
- GUI-1.6: Profile Manager
- GUI-1.7: Settings Panel
- GUI-1.8: Log Viewer
- GUI-1.9: Bus State Monitor

**Bus Connections:**
- CANBUS (primary communication)
- Can operate standalone (SAFEMODE) if bus unavailable

**Fault Code Range:** GUI-1.00 - GUI-1.99

---

### Module DIAG-1: Unified Diagnostic System
**Address:** DIAG-1  
**Type:** Health Monitoring & Protocol Enforcement  
**File:** `Command Center/Data Bus/diagnostic_manager/Unified_diagnostic_system/core.py`

**Primary Responsibilities:**
- System health monitoring (6 other parent modules)
- Protocol compliance validation
- Auto-registration orchestration
- Baseline testing coordination
- Fault code validation
- System launch orchestration

**Child Components:** 0 (monitors others, owns no children)

**Bus Connections:**
- CANBUS (monitoring only)
- NOT connected to LINBUS (cannot monitor LINBUS traffic)

**Fault Code Range:** DIAG-1.00 - DIAG-1.99

**Critical Architectural Note:** UDS commands ONLY parent modules. Parents test their own children and report aggregated results to UDS. UDS does NOT test child components directly.

---

## COMMUNICATION ARCHITECTURE

### Dual-Bus Design

**CANBUS (Primary Data Bus)**
- **Purpose:** High-throughput data communication
- **Protocol:** Signal-based pub/sub architecture
- **Connected Modules:** All 7 parent modules
- **Message Format:** Topic + Payload + Metadata
- **Features:**
  - Parent-only message filtering
  - Message lifecycle enforcement
  - Event logging
  - Fault code propagation

**LINBUS (Secondary Orchestration Bus)**
- **Purpose:** Workflow coordination and throttle control
- **Protocol:** Master-slave orchestration
- **Master:** Warden (2-1)
- **Sub-Master:** Marshall (3)
- **Connected Slaves:** Analyst Deck (4-1 to 4-8), Evidence Locker (throttle), Mission Debrief (throttle)
- **Features:**
  - Wake/sleep commands
  - Processing rate synchronization
  - Sequential workflow control

### CANBUS Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                       CANBUS (Bus-1)                                  │
│                    Signal Registry + Router                           │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Topic-Based Routing:                                                │
│  ├─ "case_create"      → [Evidence Locker, Warden]                  │
│  ├─ "evidence_ready"   → [Warden, Marshall]                         │
│  ├─ "section.complete" → [Marshall, Warden, Mission Debrief]        │
│  └─ "narrative.assembled" → [GUI, Library]                          │
│                                                                       │
│  Message Lifecycle Enforcement:                                      │
│  ├─ Validate message_state (CALL_SENT, CALL_ANSWERED, etc.)        │
│  ├─ Filter child addresses (parent-only delivery)                   │
│  └─ Log all transactions                                             │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
         │                │                │                │
         ▼                ▼                ▼                ▼
    Module 1         Module 2-1       Module 3         Module 5
   (Evidence)        (Warden)        (Marshall)      (Debrief)
```

### LINBUS Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                   LINBUS MASTER: Warden (2-1)                        │
│              Orchestration Commands & Timing Control                 │
└─────────────┬────────────────────────────────────────────────────────┘
              │
              ├─ Throttle Control → Evidence Locker (1)
              │                     Mission Debrief (5)
              │
              └─ Section Commands ─────────────┐
                                               ▼
                                ┌──────────────────────────────────────┐
                                │ LINBUS SUB-MASTER: Marshall (3)      │
                                │   Analyst Section Proxy               │
                                └───────────┬──────────────────────────┘
                                            │
                    ┌───────────────────────┼───────────────────────┐
                    │                       │                       │
                    ▼                       ▼                       ▼
              ┌─────────┐             ┌─────────┐           ┌─────────┐
              │ 4-1 TOC │             │ 4-4 Evd │           │ 4-8 App │
              └─────────┘             └─────────┘           └─────────┘
                 (and 4-2, 4-3, 4-5, 4-6, 4-7...)
```

---

## PARENT-CHILD RELATIONSHIPS

### Complete System Hierarchy

```
Bus-1 (Central Command Bus)
├─ Bus-1.1 (Signal Registry)
├─ Bus-1.2 (Event Logger)
├─ Bus-1.3 (State Manager)
├─ Bus-1.4 (Address Registry)
└─ Bus-1.5 (Health Monitor)

DIAG-1 (Unified Diagnostic System)
└─ (no children - monitors others)

1 (Evidence Locker)
├─ 1.1 (Evidence Classifier)
├─ 1.2 (Evidence Indexer)
├─ 1.3 (Manifest Builder)
├─ 1.4 (Section Registry)
├─ 1.5 (Case Manifest Builder)
├─ 1.6 (Evidence Index Manager)
├─ 1.7 (Static Data Flow)
└─ 1.8 (Bus Extensions)

2-1 (Warden)
├─ 2-2 (Ecosystem Controller)
│  ├─ 2-2.1
│  ├─ 2-2.2
│  ├─ 2-2.3
│  └─ 2-2.4
└─ 2-3 (Gateway Controller)
   ├─ 2-3.1
   ├─ 2-3.2
   ├─ 2-3.3
   └─ 2-3.4

3 (Marshall)
├─ 3-1 (Evidence Manager)
├─ 3-2 (Section Processor - reserved)
└─ 3-3 (Media Processor - reserved)

4-X (Analyst Deck - LINBUS connected, proxied by Marshall)
├─ 4-1 (Table of Contents)
├─ 4-2 (Cover Page)
├─ 4-3 (Executive Summary)
├─ 4-4 (Evidence Analysis)
├─ 4-5 (Timeline Construction)
├─ 4-6 (Findings and Conclusions)
├─ 4-7 (Recommendations)
└─ 4-8 (Appendices)

5 (Mission Debrief)
├─ 5-1 (Debrief Manager)
│  ├─ 5-1.1 (Narrative Engine)
│  └─ 5-1.2 (Template Manager)
├─ 5-2 (The Librarian)
│  ├─ 5-2.1
│  ├─ 5-2.2
│  ├─ 5-2.3
│  └─ 5-2.4
└─ (Additional debrief components: 5.1, 5.2, 5.3, 5.4)

GUI-1 (Enhanced Functional GUI)
├─ GUI-1.1 (Case Manager UI)
├─ GUI-1.2 (Evidence Upload UI)
├─ GUI-1.3 (Status Dashboard)
├─ GUI-1.4 (Report Viewer)
├─ GUI-1.5 (Section Monitor)
├─ GUI-1.6 (Profile Manager)
├─ GUI-1.7 (Settings Panel)
├─ GUI-1.8 (Log Viewer)
└─ GUI-1.9 (Bus State Monitor)
```

### Testing Hierarchy

**UDS Testing Model:**
```
UDS (DIAG-1) tests:
├─ Evidence Locker (1) → Evidence Locker tests 1.1-1.8
├─ Warden (2-1) → Warden tests 2-2, 2-3 (and their sub-components)
├─ Marshall (3) → Marshall tests 3-1, proxies tests for 4-1 to 4-8
├─ Mission Debrief (5) → Mission Debrief tests 5-1, 5-2 (and sub-components)
├─ Bus-1 → Bus tests Bus-1.1 to Bus-1.5
└─ GUI-1 → GUI tests GUI-1.1 to GUI-1.9

UDS does NOT test child components directly.
Parents are responsible for testing their children.
```

---

## MESSAGE LIFECYCLE PROTOCOL

### Purpose
Prevent infinite message loops and ensure clear request/response semantics.

### Lifecycle States

```python
class MessageState:
    CALL_SENT = "CALL_SENT"          # Initiator sends request
    CALL_RECEIVED = "CALL_RECEIVED"  # Receiver ACKs receipt (optional)
    CALL_ANSWERED = "CALL_ANSWERED"  # Receiver sends response data
    CALL_COMPLETED = "CALL_COMPLETED" # Initiator confirms completion (optional)
```

### Implementation

**Sending Requests:**
```python
# In universal_communicator.py or comms.py
def send_request(target_address, topic, payload):
    data = {
        'target_address': target_address,
        'message_state': 'CALL_SENT',  # Mark as request
        'payload': payload
    }
    bus.send(topic, data)
```

**Handling Requests:**
```python
# In module handlers (e.g., _handle_auto_registration)
def _handle_auto_registration(self, payload):
    # Only respond to requests
    if payload.get('message_state') != 'CALL_SENT':
        return  # Ignore responses or other states
    
    # Process request and generate response
    response_payload = {...}
    
    # Send response with CALL_ANSWERED state
    self.communicator.send_response('DIAG-1', response_payload)
```

**Sending Responses:**
```python
# In universal_communicator.py
def send_response(target_address, response_data):
    data = {
        'target_address': target_address,
        'message_state': 'CALL_ANSWERED',  # Mark as response
        'payload': response_data
    }
    bus.send(topic, data)
```

**Processing Responses:**
```python
# In UDS comms.py
def _handle_auto_registration_response(self, signal_data):
    # Only process responses
    if signal_data.get('message_state') != 'CALL_ANSWERED':
        return  # Ignore requests
    
    # Process response data
    system_address = signal_data.get('system_address')
    # ... validation logic ...
```

### Parent-Only Message Filtering

**In bus_core.py:**
```python
# Only deliver messages to parent modules
PARENT_MODULES = {'Bus-1', 'DIAG-1', '1', '2-1', '3', '5', 'GUI-1'}

def send(self, topic, data):
    target_address = data.get('target_address')
    if target_address and target_address not in PARENT_MODULES:
        # Child address - skip delivery (parent handles)
        logger.debug(f"Skipping child address {target_address}")
        return {}
    
    # Deliver to registered handlers
    for handler in self.signal_registry.get(topic, []):
        response = handler(data)
```

---

## OPERATIONAL FLOW

### Complete Case Processing Workflow

```
┌──────────────────────────────────────────────────────────────────────┐
│ PHASE 1: CASE INITIATION                                             │
└──────────────────────────────────────────────────────────────────────┘

1. Operator creates case via GUI (GUI-1)
   ├─ Enter case details (name, investigation type, etc.)
   └─ GUI emits: case_create signal on CANBUS
   
2. Evidence Locker (1) receives case_create
   ├─ Initializes case structure
   ├─ Creates case manifest
   └─ Emits: case_ready signal

3. GUI prompts operator for evidence upload

┌──────────────────────────────────────────────────────────────────────┐
│ PHASE 2: EVIDENCE PROCESSING                                         │
└──────────────────────────────────────────────────────────────────────┘

4. Operator uploads evidence files
   ├─ GUI emits: files_add signal with file paths
   └─ CANBUS delivers to Evidence Locker (1)

5. Evidence Locker (1) processes files
   ├─ Validates file integrity
   ├─ Classifies by type (1.1 - Evidence Classifier)
   │  ├─ Images (jpeg, png, etc.)
   │  ├─ Documents (pdf, docx, etc.)
   │  ├─ Videos (mp4, avi, etc.)
   │  └─ Audio (mp3, wav, etc.)
   ├─ Extracts metadata
   ├─ Builds searchable index (1.2 - Evidence Indexer)
   ├─ Scores section relevance (1.4 - Section Registry)
   ├─ Updates case manifest (1.5 - Case Manifest Builder)
   └─ Emits: evidence_ready signal with manifest

┌──────────────────────────────────────────────────────────────────────┐
│ PHASE 3: ORCHESTRATION                                               │
└──────────────────────────────────────────────────────────────────────┘

6. Warden (2-1) receives evidence_ready
   ├─ ECC (2-2) validates system readiness
   │  ├─ Check Marshall operational
   │  ├─ Check Analyst sections available
   │  └─ Validate dependencies satisfied
   ├─ Gateway (2-3) analyzes evidence manifest
   │  ├─ Determine target sections (e.g., 4-1, 4-3, 4-4, 4-6)
   │  ├─ Build section-specific evidence packages
   │  └─ Create distribution plan
   └─ Warden commands Marshall via LINBUS
      ├─ "Wake sections: 4-1, 4-3, 4-4, 4-6"
      └─ "Deliver evidence packages"

┌──────────────────────────────────────────────────────────────────────┐
│ PHASE 4: EVIDENCE DISTRIBUTION                                       │
└──────────────────────────────────────────────────────────────────────┘

7. Marshall (3) receives distribution command (LINBUS)
   ├─ Evidence Manager (3-1) prepares packages
   ├─ Marshall wakes target sections via LINBUS
   │  ├─ Send wake command to 4-1
   │  ├─ Send wake command to 4-3
   │  ├─ Send wake command to 4-4
   │  └─ Send wake command to 4-6
   ├─ Wait for "ready" signals from sections
   └─ Deliver evidence packages via LINBUS
      ├─ Package for 4-1 (Table of Contents): Full case structure
      ├─ Package for 4-3 (Executive Summary): Key evidence summary
      ├─ Package for 4-4 (Evidence Analysis): All evidence files
      └─ Package for 4-6 (Findings): Analysis-relevant evidence

8. Marshall monitors section progress
   ├─ Receives status updates from sections (LINBUS)
   ├─ Relays to CANBUS for system-wide visibility
   └─ GUI updates status dashboard

┌──────────────────────────────────────────────────────────────────────┐
│ PHASE 5: SECTION PROCESSING                                          │
└──────────────────────────────────────────────────────────────────────┘

9. Each Analyst section processes its evidence
   ├─ Section 4-1: Generates table of contents structure
   ├─ Section 4-3: Crafts executive summary narrative
   ├─ Section 4-4: Performs detailed evidence analysis
   └─ Section 4-6: Formulates findings and conclusions

10. Sections report completion
    ├─ Each section emits: section.complete signal (LINBUS)
    ├─ Includes section output (narrative text, data)
    └─ Marshall collects all outputs

11. Marshall aggregates results
    ├─ Validates all target sections complete
    ├─ Collects section outputs
    ├─ Relays to CANBUS: all_sections.complete
    └─ Sends outputs to Mission Debrief (5)

┌──────────────────────────────────────────────────────────────────────┐
│ PHASE 6: REPORT FINALIZATION                                         │
└──────────────────────────────────────────────────────────────────────┘

12. Mission Debrief (5) receives section outputs
    ├─ Debrief Manager (5-1) assembles narrative
    │  ├─ Order sections by template
    │  ├─ Combine narratives into cohesive report
    │  ├─ Apply cross-references
    │  └─ Validate structure integrity
    ├─ Narrative Engine (5-1.1) applies formatting
    │  ├─ Load report template
    │  ├─ Insert section content
    │  ├─ Apply styling (fonts, headers, etc.)
    │  └─ Generate table of contents
    ├─ Apply professional tooling
    │  ├─ Insert digital signature
    │  ├─ Apply watermarks
    │  ├─ Embed metadata
    │  └─ Add cover page
    └─ Generate exports
       ├─ PDF output
       ├─ DOCX output
       └─ Archive package

13. The Librarian (5-2) archives report
    ├─ Store in permanent library
    ├─ Index metadata for retrieval
    ├─ Apply version control
    └─ Emits: narrative.assembled signal

┌──────────────────────────────────────────────────────────────────────┐
│ PHASE 7: OPERATOR DELIVERY                                           │
└──────────────────────────────────────────────────────────────────────┘

14. GUI (GUI-1) receives narrative.assembled
    ├─ Notify operator (popup/alert)
    ├─ Enable Report Viewer (GUI-1.4)
    └─ Display completed report

15. Operator reviews report
    ├─ View in Report Viewer
    ├─ Download PDF/DOCX
    └─ Close case or request revisions

┌──────────────────────────────────────────────────────────────────────┐
│ PHASE 8: CLEANUP                                                     │
└──────────────────────────────────────────────────────────────────────┘

16. Marshall sends sleep commands
    ├─ Sleep 4-1, 4-3, 4-4, 4-6 (LINBUS)
    └─ Free LINBUS resources

17. System returns to idle state
    ├─ All modules monitoring for next case
    └─ UDS continues health monitoring
```

### System Startup Sequence

```
┌──────────────────────────────────────────────────────────────────────┐
│ UDS LAUNCH SEQUENCE                                                  │
└──────────────────────────────────────────────────────────────────────┘

1. UDS (DIAG-1) initialization
   ├─ Load core.py
   ├─ Initialize communication module (comms.py)
   ├─ Initialize enforcement module (enforcement.py)
   └─ Load protocol registry (system_protocol_registry.py)

2. Bus detection
   ├─ Check if CANBUS (Bus-1) already running
   ├─ If yes: Join existing bus
   └─ If no: Start new bus instance

3. Parent module instantiation
   ├─ Instantiate Evidence Locker (1)
   ├─ Instantiate Warden (2-1)
   ├─ Instantiate Marshall (3)
   ├─ Instantiate Mission Debrief (5)
   └─ Instantiate GUI (GUI-1)
   └─ Note: Bus-1 already running from step 2

4. Auto-registration protocol
   ├─ UDS → Evidence Locker (1): "auto_registration" (CALL_SENT)
   │  └─ Wait for response (CALL_ANSWERED)
   ├─ UDS → Warden (2-1): "auto_registration" (CALL_SENT)
   │  └─ Wait for response (CALL_ANSWERED)
   ├─ UDS → Marshall (3): "auto_registration" (CALL_SENT)
   │  └─ Wait for response (CALL_ANSWERED)
   ├─ UDS → Mission Debrief (5): "auto_registration" (CALL_SENT)
   │  └─ Wait for response (CALL_ANSWERED)
   ├─ UDS → Bus-1: "auto_registration" (CALL_SENT)
   │  └─ Wait for response (CALL_ANSWERED)
   └─ UDS → GUI-1: "auto_registration" (CALL_SENT)
      └─ Wait for response (CALL_ANSWERED)
   
   └─ Validation: Confirm all 6 modules registered

5. Baseline testing
   ├─ UDS → Each parent module: "Run self-test"
   ├─ Each parent tests its own children
   │  ├─ Evidence Locker tests 1.1-1.8
   │  ├─ Warden tests 2-2, 2-3
   │  ├─ Marshall tests 3-1, proxies 4-1 to 4-8
   │  ├─ Mission Debrief tests 5-1, 5-2
   │  ├─ Bus tests Bus-1.1 to Bus-1.5
   │  └─ GUI tests GUI-1.1 to GUI-1.9
   ├─ Parents emit fault codes for failures
   └─ UDS validates fault codes and aggregates health

6. System operational
   ├─ UDS transitions to monitoring mode
   ├─ All modules ready for case processing
   └─ GUI displays to operator

7. Continuous monitoring
   ├─ UDS monitors fault code emissions
   ├─ Validates protocol compliance
   ├─ Tracks system health metrics
   └─ Generates health reports
```

---

## FAULT CODE SYSTEM

### Fault Code Structure

**Format:** `MODULE_ADDRESS.SEVERITY_CODE`

**Examples:**
- `1.00` - Evidence Locker critical failure
- `2-1.23` - Warden section completion timeout
- `DIAG-1.20` - UDS auto-registration timeout

### Fault Code Ranges by Module

| Module | Address | Fault Range | Example Faults |
|--------|---------|-------------|----------------|
| Evidence Locker | 1 | 1.00 - 1.99 | 1.00 (init fail), 1.10 (ingestion fail), 1.20 (classifier error) |
| Warden | 2-1 | 2.00 - 2.99 | 2.00 (init fail), 2.10 (orchestration fail), 2.20 (gateway fail) |
| Marshall | 3 | 3.00 - 3.99 | 3.00 (init fail), 3.10 (distribution fail), 3.30 (LINBUS proxy fail) |
| Analyst Sections | 4-X | 4.00 - 4.99 | 4.10 (section fail), proxied via Marshall to CANBUS |
| Mission Debrief | 5 | 5.00 - 5.99 | 5.00 (init fail), 5.10 (narrative fail), 5.30 (library fail) |
| Bus | Bus-1 | Bus-1.00 - Bus-1.99 | Bus-1.00 (init fail), Bus-1.10 (routing fail), Bus-1.30 (overload) |
| GUI | GUI-1 | GUI-1.00 - GUI-1.99 | GUI-1.00 (init fail), GUI-1.10 (UI fail), GUI-1.20 (interaction error) |
| UDS | DIAG-1 | DIAG-1.00 - DIAG-1.99 | DIAG-1.00 (init fail), DIAG-1.20 (registration fail), DIAG-1.30 (test timeout) |

### Severity Levels

**Within each module's range:**
- **XX.00 - XX.09:** CRITICAL - System halt required
- **XX.10 - XX.89:** ERROR - Attempt recovery
- **XX.90 - XX.99:** WARNING - Log and continue

### Fault Validation Process

```
1. Fault Code Emission (any module)
   ├─ Module detects error condition
   ├─ Determines appropriate fault code
   └─ Emits on CANBUS

2. UDS Enforcement Module Receives
   ├─ Capture fault code emission
   ├─ Log to system logs
   └─ Validate against protocol registry

3. Validation Checks
   ├─ Fault code format valid? (XX.YY or XXX-X.YY)
   ├─ Module owns this fault range?
   ├─ Severity level appropriate?
   └─ Fault code registered in protocol?

4. Action Based on Severity
   ├─ CRITICAL (XX.00-XX.09)
   │  ├─ Log error
   │  ├─ Notify operators
   │  ├─ Halt affected systems
   │  └─ Await manual intervention
   ├─ ERROR (XX.10-XX.89)
   │  ├─ Log error
   │  ├─ Attempt recovery
   │  ├─ Retry operation (if applicable)
   │  └─ Escalate if recovery fails
   └─ WARNING (XX.90-XX.99)
      ├─ Log warning
      ├─ Continue operation
      └─ Include in health reports
```

---

## SYSTEM INTEGRATION POINTS

### External Dependencies

**Python Environment:**
- Python 3.11+
- Tkinter (GUI framework)
- Standard library modules (threading, queue, logging, pathlib, etc.)

**Optional Dependencies:**
- tkinterdnd2 (drag-and-drop support for GUI)
- PDF generation libraries (reportlab, weasyprint, etc.)
- DOCX generation libraries (python-docx)
- Image processing (PIL, opencv-python)
- OSINT tools (if external enrichments used)

### File System Integration

**Evidence Storage:**
- `intake/` - Raw evidence ingestion directory
- `Evidence Locker/evidence_manifest.json` - Case manifest tracking

**Report Outputs:**
- `Generated Reports/` - Final report exports
- `Command Center/Mission Debrief/Library/` - Archived reports

**Logs:**
- `Command Center/Data Bus/diagnostic_manager/Unified_diagnostic_system/library/system_logs/` - UDS logs
- `Command Center/Data Bus/dki_bus_core.log` - Bus transaction logs
- `Command Center/UI/enhanced_gui.log` - GUI logs

**Configuration:**
- `The War Room/dev_tracking/` - Development tracking and agent logs
- `Command Center/Data Bus/configs/` - Bus configuration files
- `The Warden/section_tag_map.json` - Gateway routing configuration

### Database Integration

**Current:** JSON-based flat file storage  
**Future Consideration:** SQL database for evidence indexing and case management

---

## TECHNICAL IMPLEMENTATION

### Universal Communicator Protocol

**File:** `Command Center/Data Bus/universal_communicator.py`

**Purpose:** Standardized communication layer for all modules.

**Key Methods:**
```python
class UniversalCommunicator:
    def __init__(self, bus_connection, system_address):
        """Initialize communicator with bus and address"""
        
    def send_signal(self, topic, payload, message_state="CALL_SENT"):
        """Send signal on specific topic"""
        
    def send_auto_registration_response(self, target, metadata):
        """Send auto-registration response (CALL_ANSWERED)"""
        
    def send_radio_check_response(self, target, connectivity_data):
        """Send radio check response"""
        
    def send_fault_code(self, fault_code, details):
        """Emit fault code on CANBUS"""
```

### Parent Module Template

**Standard structure for all parent modules:**

```python
class ParentModule:
    def __init__(self, bus, communicator):
        """
        Initialize parent module.
        
        Args:
            bus: CANBUS instance (or None)
            communicator: UniversalCommunicator instance (or None)
        """
        self.bus = bus
        self.communicator = communicator
        self.system_address = "MODULE_ADDRESS"
        self.bus_connected = False
        
        # Initialize child components
        self._initialize_children()
        
        # Register signal handlers
        self._register_handlers()
        
        # Connect to CANBUS
        self._initialize_canbus()
    
    def _initialize_children(self):
        """Initialize all child components"""
        # Instantiate child components
        pass
    
    def _register_handlers(self):
        """Register signal handlers with bus"""
        if self.bus:
            self.bus.register_signal("auto_registration", self._handle_auto_registration)
            self.bus.register_signal("radio_check", self._handle_radio_check)
            # ... other handlers ...
    
    def _handle_auto_registration(self, payload):
        """Handle UDS auto-registration request"""
        # Check message lifecycle
        if payload.get('message_state') != 'CALL_SENT':
            return
        
        # Build response
        response = {
            "system_address": self.system_address,
            "system_type": "module_type",
            "status": "OPERATIONAL",
            "capabilities": [...],
            "child_components": [...],
            "compliance_status": "COMPLIANT",
            "protocol_version": "1.0.0"
        }
        
        # Send response
        self.communicator.send_auto_registration_response("DIAG-1", response)
    
    def _handle_radio_check(self, payload):
        """Handle UDS radio check request"""
        # Check message lifecycle
        if payload.get('message_state') != 'CALL_SENT':
            return
        
        # Build response
        connectivity_data = {
            "system_address": self.system_address,
            "latency_ms": 0,
            "bus_connected": self.bus_connected
        }
        
        # Send response
        self.communicator.send_radio_check_response("DIAG-1", connectivity_data)
    
    def _run_startup_self_test(self):
        """Run self-test of all child components"""
        # Test each child component
        # Emit fault codes for failures
        # Send completion signal to UDS
        pass
```

---

## CURRENT BUILD STATUS

### Operational Status (2025-10-12)

**System State:** OPERATIONAL (Validation Phase)

**✅ Confirmed Working:**
- All 7 parent modules instantiate successfully
- CANBUS communication active
- Message lifecycle protocol enforced (CALL_SENT/CALL_ANSWERED)
- Parent-only message filtering active
- Auto-registration protocol functional (6/6 modules respond)
- UDS monitoring active
- Fault code capture and logging operational

**⚠️ Under Validation:**
- Parent module self-tests report "healthy" without strict functional validation
- Evidence processing pipeline (end-to-end testing incomplete)
- Section generation workflows (Analyst Deck functional status unknown)
- Report finalization and export (not functionally tested)
- GUI operational readiness (responds to UDS but window display not validated)

**🔧 Recent Fixes (2025-10-12):**
1. ✅ Added message lifecycle protocol to prevent infinite loops
2. ✅ Implemented parent-only communication filtering in bus_core
3. ✅ Updated all parent modules with lifecycle checks in handlers
4. ✅ Removed Unicode characters from log output (Windows compatibility)
5. ✅ Fixed Marshall `bus_connected` attribute initialization
6. ✅ Updated PARENT_CHILD_RELATIONSHIPS to include Bus-1 and DIAG-1
7. ✅ Restricted UDS to only command 6 parent modules (excluding self)

---

## KNOWN ISSUES AND LIMITATIONS

### Issue 1: Permissive Self-Test Validation
**Severity:** High  
**Impact:** UDS reports "all systems healthy" when they may not be

**Description:**
Parent module self-tests currently check for component existence and instantiation but do not perform functional validation. A module can respond "healthy" even if its processing logic is broken.

**Example:**
Evidence Locker (1) reports healthy if `evidence_classifier.py` exists, but does NOT test if classification actually works.

**Resolution Required:**
Implement functional validation in each parent's `_run_startup_self_test()`:
- Evidence Locker: Test classify a sample file
- Warden: Test ECC and Gateway initialization
- Marshall: Test LINBUS proxy to at least one Analyst section
- Mission Debrief: Test template loading and narrative engine
- GUI: Test window rendering and widget creation

---

### Issue 2: GUI Setup Wizard Blocking Launch
**Severity:** Medium  
**Impact:** Operational system blocked by first-time setup process

**Description:**
GUI may trigger setup wizard on first launch, preventing full system operation until wizard completed.

**Workaround:**
Complete setup wizard or run GUI in standalone mode (SAFEMODE).

**Resolution Required:**
Investigate setup wizard trigger conditions and provide bypass for operational mode.

---

### Issue 3: Incomplete End-to-End Testing
**Severity:** High  
**Impact:** Unknown operational readiness for complete case workflow

**Description:**
While diagnostics pass, the system has not been functionally tested end-to-end (case creation → evidence upload → section processing → report generation).

**User Feedback:** "i know everything is not right in these systems. your tests are showing 'all clear' but they arent."

**Resolution Required:**
Run complete case workflow with real evidence and validate each phase:
1. Create case via GUI
2. Upload evidence files
3. Monitor Evidence Locker classification
4. Verify Warden orchestration
5. Confirm Marshall distributes to sections
6. Validate section processing (Analyst Deck)
7. Check Mission Debrief report generation
8. View final report in GUI

---

### Issue 4: UDS Not Monitoring LINBUS
**Severity:** Low (by design)  
**Impact:** LINBUS traffic not visible to UDS

**Description:**
UDS is only connected to CANBUS, not LINBUS. It cannot directly monitor Analyst section (4-1 to 4-8) health or LINBUS traffic.

**Mitigation:**
Marshall (3) proxies LINBUS status to CANBUS, enabling UDS to receive fault codes from Analyst sections indirectly.

**Status:** This is architectural by design, not a bug. LINBUS is intentionally separate for orchestration.

---

### Issue 5: Analyst Section Functional Status Unknown
**Severity:** High  
**Impact:** Unknown if sections can generate narratives

**Description:**
Analyst sections (4-1 to 4-8) respond to LINBUS wake commands (per Marshall proxy), but their ability to process evidence and generate section outputs is untested.

**Resolution Required:**
Functional test each Analyst section:
- Wake section via LINBUS
- Deliver evidence package
- Monitor processing
- Validate section output
- Confirm completion signal

---

## CONCLUSION

Central Command represents a sophisticated autonomous system with a well-architected parent-child hierarchy, dual-bus communication infrastructure, and robust fault handling. The system's diagnostic framework (UDS) provides comprehensive monitoring, and recent fixes have resolved critical communication issues (infinite loops, message lifecycle).

**Next Steps:**
1. **Functional Testing:** Bypass diagnostics, run operational case workflow
2. **Stricter Validation:** Implement functional self-tests in all parent modules
3. **End-to-End Verification:** Complete case processing from evidence upload to report delivery
4. **Performance Tuning:** Monitor system under load, optimize bottlenecks

The architecture is sound. The focus now shifts to **operational validation and functional testing**.

---

**Document Type:** System Architecture Analysis  
**Status:** CURRENT  
**Version:** 2025-10-12 Build  
**Author:** DEESCALATION Agent  
**Last Updated:** 2025-10-12

**Related Documentation:**
- `SYSTEM_README.md` - Quick start and overview
- `PRD_Central_Command.md` - Product requirements
- `System_Blueprint_Central_Command.md` - Technical design
- `SOP_Central_Command.md` - Operational procedures

**Module Documentation:**
- `Evidence Locker/README.md`
- `The Warden/README.md`
- `The Marshall/README.md`
- `Command Center/Mission Debrief/README.md`
- `Command Center/UI/README.md`
- `Command Center/Data Bus/README.md`
- `Command Center/Data Bus/diagnostic_manager/Unified_diagnostic_system/README.md`


