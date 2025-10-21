# THE MARSHALL MODULE (Address: 3)
## Evidence Distribution and LINBUS Proxy

---

## MODULE OVERVIEW

The Marshall is the **evidence distribution engine and LINBUS sub-master** for Central Command. It manages evidence delivery to Analyst sections, serves as the LINBUS proxy between CANBUS and section workers, and coordinates section processing workflows.

**Module Address:** 3  
**Module Type:** Evidence Distribution and Orchestration Proxy  
**Parent Module:** Yes (owns 3 direct + 8 LINBUS-proxied components)  
**Bus Connections:** CANBUS (primary), LINBUS (sub-master for Analyst sections)

---

## RESPONSIBILITIES

### Primary Functions
1. **Evidence Management** - Distribution pipeline for evidence to sections
2. **LINBUS Sub-Master** - Proxy between CANBUS and Analyst sections (4-1 to 4-8)
3. **Section Coordination** - Wake/sleep control, sequencing, and timing
4. **Evidence Routing** - Section-specific evidence delivery
5. **Result Aggregation** - Collect section outputs and relay to CANBUS

### Communication Roles
- **Listens on CANBUS for:**
  - Evidence distribution commands
  - Section wake/sleep commands from Warden
  - Evidence request signals
  
- **Emits on CANBUS:**
  - Section status updates
  - Evidence delivery confirmations
  - Aggregated section results
  - Fault codes (3.00-3.99)

- **LINBUS Sub-Master:**
  - Wake/sleep commands to sections (4-1 to 4-8)
  - Evidence delivery via LINBUS
  - Collects section completion signals
  - Proxies LINBUS to CANBUS for UDS monitoring

---

## CHILD COMPONENTS

The Marshall manages 3 direct children + 8 LINBUS-proxied components:

### Direct Children

| Address | Component | Purpose |
|---------|-----------|---------|
| 3-1 | Evidence Manager | Evidence intake, validation, distribution logic |
| 3-2 | Section Processor (reserved) | Future: Direct section processing |
| 3-3 | Media Processor (reserved) | Future: Advanced media analysis |

### LINBUS-Proxied Components (Analyst Deck)

| Address | Component | Purpose |
|---------|-----------|---------|
| 4-1 | Analyst Section 1 | Table of Contents generation |
| 4-2 | Analyst Section 2 | Cover Page generation |
| 4-3 | Analyst Section 3 | Executive Summary |
| 4-4 | Analyst Section 4 | Evidence Analysis |
| 4-5 | Analyst Section 5 | Timeline Construction |
| 4-6 | Analyst Section 6 | Findings and Conclusions |
| 4-7 | Analyst Section 7 | Recommendations |
| 4-8 | Analyst Section 8 | Appendices |

**Note:** Marshall does NOT directly own Analyst sections - it proxies their LINBUS communication to/from CANBUS.

---

## FAULT CODES

**Range:** 3.00 - 3.99

### Critical Faults (3.00-3.09)
- `3.00` - Marshall initialization failure
- `3.01` - Evidence Manager initialization failure
- `3.02` - LINBUS sub-master failure
- `3.03` - CANBUS communication failure

### Evidence Distribution Faults (3.10-3.19)
- `3.10` - Evidence distribution failure
- `3.11` - Evidence validation error
- `3.12` - Distribution timeout
- `3.13` - Missing evidence file

### Section Coordination Faults (3.20-3.29)
- `3.20` - Section wake failure
- `3.21` - Section sleep timeout
- `3.22` - Section communication lost
- `3.23` - Section processing timeout

### LINBUS Proxy Faults (3.30-3.39)
- `3.30` - LINBUS proxy failure
- `3.31` - CANBUS-to-LINBUS translation error
- `3.32` - LINBUS-to-CANBUS relay failure
- `3.33` - Proxy timeout

### Child Component Faults (3.40-3.89)
- `3.41` - Component 3-1 (Evidence Manager) failure

### Analyst Section Faults (3.50-3.58) - Proxied
- `3.51` - Section 4-1 failure (proxied from LINBUS)
- `3.52` - Section 4-2 failure (proxied from LINBUS)
- *(continues for each Analyst section)*

---

## OPERATIONAL FLOW

### Evidence Distribution Flow

```
1. Distribution Command (from Warden via CANBUS)
   ↓
   Marshall receives evidence manifest + target sections
   ↓
2. Evidence Manager Preparation (3-1)
   ├─ Validate evidence files
   ├─ Load evidence into distribution queue
   └─ Prepare section-specific evidence packages
   ↓
3. Section Wake Sequence (LINBUS)
   ├─ Marshall sends wake command to target sections
   ├─ Wait for section "ready" signals
   └─ Confirm sections operational
   ↓
4. Evidence Delivery (LINBUS)
   ├─ Deliver evidence package to Section 4-1
   ├─ Deliver evidence package to Section 4-2
   └─ (continues for all target sections)
   ↓
5. Processing Monitoring
   ├─ Track section progress via LINBUS
   ├─ Relay status updates to CANBUS
   └─ Aggregate fault codes from sections
   ↓
6. Result Collection
   ├─ Receive section outputs via LINBUS
   ├─ Validate section completion
   ├─ Aggregate results
   └─ Emit to CANBUS for Mission Debrief (5)
   ↓
7. Section Sleep
   ├─ Send sleep command to completed sections
   └─ Free LINBUS resources
```

### LINBUS Proxy Operation

```
CANBUS → LINBUS Translation:
┌──────────────┐
│ Warden (2-1) │ ──CANBUS──→ ┌──────────────┐
│ "Wake 4-1"   │             │ Marshall (3) │
└──────────────┘             └──────┬───────┘
                                    │
                                    │ Translates to LINBUS
                                    ↓
                             ┌──────────────┐
                             │ Section 4-1  │ ←─LINBUS─
                             │ "Wake signal"│
                             └──────────────┘

LINBUS → CANBUS Relay:
┌──────────────┐
│ Section 4-1  │ ──LINBUS──→ ┌──────────────┐
│ "Complete"   │             │ Marshall (3) │
└──────────────┘             └──────┬───────┘
                                    │
                                    │ Relays to CANBUS
                                    ↓
                             ┌──────────────┐
                             │ Warden (2-1) │ ←─CANBUS─
                             │ UDS (DIAG-1) │
                             └──────────────┘
```

### Self-Test Protocol

When commanded by UDS, Marshall performs:

1. **Component Health Check**
   - Test Evidence Manager (3-1) initialization
   - Verify CANBUS connectivity
   - Verify LINBUS sub-master status

2. **Functional Validation**
   - Test evidence validation engine
   - Test LINBUS proxy functionality
   - Validate section wake/sleep commands

3. **LINBUS Proxy Test**
   - Send test signals to Analyst sections
   - Collect responses from sections
   - Proxy responses back to UDS

4. **Fault Reporting**
   - Emit fault codes for any failures
   - Include proxied Analyst section faults
   - Send completion signal to UDS
   - Report operational status

---

## COMMUNICATION PROTOCOL

### Universal Communicator Integration

The Marshall uses UniversalCommunicator for CANBUS messaging:

**Registered Signal Handlers:**
- `auto_registration` - UDS protocol compliance
- `radio_check` - Communication health validation
- `rollcall` - System presence confirmation
- `evidence.deliver` - Evidence distribution commands
- `section.wake` - Section wake commands
- `section.sleep` - Section sleep commands

**Message Lifecycle:**
- Only responds to `message_state: "CALL_SENT"`
- Sends responses with `message_state: "CALL_ANSWERED"`
- Proxies LINBUS messages to CANBUS with appropriate state

---

## FILE STRUCTURE

```
The Marshall/
├─ marshall_module.py            # Main module entry point (Address: 3)
├─ Evidence_Checkout/
│  └─ evidence_manager.py        # Child component (3-1)
├─ Gateway/
│  ├─ section_readme/            # Analyst section documentation
│  ├─ parsing maps/              # Evidence routing maps
│  └─ SECTION_PARSING_README.md
├─ _init_marshall.py             # Initialization script
├─ README.md                     # This file
└─ Test Plans/
   └─ MARSHALL_SYSTEM_SUMMARY.md # Test specifications
```

**Note:** Analyst Deck sections (4-1 to 4-8) are located in `The Analyst Deck/` directory but are coordinated by Marshall via LINBUS.

---

## INITIALIZATION

### Module Startup Sequence

1. **Import and Setup**
   ```python
   from marshall_module import MarshallModule
   ```

2. **Instantiation**
   ```python
   marshall = MarshallModule(
       bus=bus_instance,
       communicator=communicator_instance
   )
   ```

3. **Bus Registration**
   - Registers with address "3"
   - Subscribes to required CANBUS handlers
   - Initializes Evidence Manager (3-1)

4. **LINBUS Sub-Master Setup**
   - Establishes LINBUS sub-master control
   - Registers Analyst section addresses (4-1 to 4-8)
   - Sets up LINBUS-to-CANBUS proxy

5. **Self-Test Execution**
   - Validates Evidence Manager (3-1)
   - Tests LINBUS proxy to Analyst sections
   - Reports health status to UDS
   - Transitions to operational state

---

## INTEGRATION POINTS

### Upstream Dependencies
- **Bus-1 (CANBUS)** - Communication infrastructure
- **Warden (2-1)** - Coordination commands via LINBUS
- **UDS (DIAG-1)** - Health monitoring

### Downstream Handoffs
- **Analyst Sections (4-1 to 4-8)** - Evidence delivery via LINBUS
- **Mission Debrief (5)** - Aggregated section results via CANBUS

### Peer Interactions
- **Evidence Locker (1)** - Evidence file retrieval
- **GUI (GUI-1)** - Section status updates

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
- `bus_connected` attribute tracking

**⚠️ Requires Validation:**
- Evidence Manager (3-1) operational status
- LINBUS sub-master functionality
- Section wake/sleep commands
- LINBUS proxy to Analyst sections
- Evidence distribution pipeline

---

## TROUBLESHOOTING

### Common Issues

**Issue:** Marshall responds to UDS but sections don't wake  
**Solution:** Validate LINBUS sub-master status, check Analyst section connectivity

**Issue:** Evidence distribution fails  
**Solution:** Verify Evidence Manager (3-1) initialization, check file access permissions

**Issue:** Section results not reaching Mission Debrief  
**Solution:** Check LINBUS-to-CANBUS proxy, verify aggregation logic

**Issue:** Proxied faults not reporting to UDS  
**Solution:** Confirm fault code translation from LINBUS to CANBUS

---

## RELATED DOCUMENTATION

- **System Architecture:** `Command Center/read_me_file/CURRENT_SYSTEM_ARCHITECTURE_2025-10-12.md`
- **LINBUS Protocol:** `Command Center/Data Bus/diagnostic_manager/read_me/CANBUS_LINBUS_ARCHITECTURE.md`
- **Analyst Deck:** `The Analyst Deck/` (section-specific documentation)
- **Section Parsing:** `The Marshall/Gateway/SECTION_PARSING_README.md`

---

**Document Type:** Module README  
**Module:** The Marshall (3)  
**Status:** CURRENT  
**Last Updated:** 2025-10-12

