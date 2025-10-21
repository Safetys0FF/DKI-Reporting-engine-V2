# MISSION DEBRIEF MODULE (Address: 5)
## Report Finalization and Assembly

---

## MODULE OVERVIEW

The Mission Debrief is the **final report assembly and publication system** for Central Command. It collects completed section outputs, assembles the final narrative, applies professional tooling (signatures, watermarks, OSINT enrichments), and archives finished reports to the Library.

**Module Address:** 5  
**Module Type:** Report Finalization  
**Parent Module:** Yes (owns 2 child components)  
**Bus Connections:** CANBUS (primary)

---

## RESPONSIBILITIES

### Primary Functions
1. **Narrative Assembly** - Combine all section outputs into cohesive report
2. **Report Generation** - Apply templates, formatting, and professional styling
3. **Final Assembly** - Integrate signatures, watermarks, and metadata
4. **Library Archival** - Store completed reports in permanent archive
5. **Export Management** - Generate multiple format outputs (PDF, DOCX, etc.)

### Communication Roles
- **Listens on CANBUS for:**
  - Section completion signals
  - Narrative assembly requests
  - Report generation commands
  
- **Emits on CANBUS:**
  - Report assembly progress
  - Report completion signals
  - Fault codes (5.00-5.99)

---

## CHILD COMPONENTS

The Mission Debrief manages 2 child components:

| Address | Component | Purpose |
|---------|-----------|---------|
| 5-1 | Debrief Manager | Narrative assembly, report generation, output coordination |
| 5-2 | The Librarian | Report archival, library management, version control |

### Debrief Manager (5-1)
**File:** `Debrief/debrief_manager.py`

**Responsibilities:**
- Collect section outputs from Analyst Deck
- Assemble narrative structure
- Apply report templates
- Generate final reports
- Coordinate professional tooling

**Child Sub-Components:**
- 5-1.1 Narrative Engine
- 5-1.2 Template Manager

### The Librarian (5-2)
**File:** `The Librarian/librarian.py`

**Responsibilities:**
- Archive completed reports
- Manage library structure
- Version control for reports
- Metadata indexing
- Retrieval services

**Child Sub-Components:**
- 5-2.1 through 5-2.4 (archive management)

---

## FAULT CODES

**Range:** 5.00 - 5.99

### Critical Faults (5.00-5.09)
- `5.00` - Mission Debrief initialization failure
- `5.01` - Debrief Manager initialization failure
- `5.02` - Librarian initialization failure
- `5.03` - Database connection failure

### Narrative Assembly Faults (5.10-5.19)
- `5.10` - Narrative assembly failure
- `5.11` - Missing section output
- `5.12` - Section output validation error
- `5.13` - Narrative structure invalid

### Report Generation Faults (5.20-5.29)
- `5.20` - Report generation failure
- `5.21` - Template loading error
- `5.22` - Formatting error
- `5.23` - Export generation failure

### Library Faults (5.30-5.39)
- `5.30` - Library archival failure
- `5.31` - Storage quota exceeded
- `5.32` - Version control error
- `5.33` - Retrieval failure

### Child Component Faults (5.40-5.89)
- `5.41` - Component 5-1 (Debrief Manager) failure
- `5.42` - Component 5-2 (Librarian) failure

---

## OPERATIONAL FLOW

### Report Assembly Flow

```
1. Section Completion Signals (CANBUS)
   ↓
   Mission Debrief receives from Marshall (3)
   ↓
2. Output Collection (5-1)
   ├─ Validate all sections complete
   ├─ Collect section outputs
   └─ Verify output integrity
   ↓
3. Narrative Assembly (5-1.1)
   ├─ Order sections by template
   ├─ Combine narratives
   ├─ Apply cross-references
   └─ Validate structure
   ↓
4. Report Generation (5-1.2)
   ├─ Apply report template
   ├─ Format content
   ├─ Insert metadata
   └─ Apply professional tooling
   ↓
5. Final Assembly
   ├─ Add signatures
   ├─ Apply watermarks
   ├─ Generate table of contents
   └─ Create cover page
   ↓
6. Export Generation
   ├─ Generate PDF output
   ├─ Generate DOCX output
   └─ Create archive package
   ↓
7. Library Archival (5-2)
   ├─ Store in Library
   ├─ Index metadata
   ├─ Version control
   └─ Signal completion on CANBUS
```

### Self-Test Protocol

When commanded by UDS, Mission Debrief performs:

1. **Component Health Check**
   - Test Debrief Manager (5-1) initialization
   - Test Librarian (5-2) initialization
   - Verify filesystem access

2. **Functional Validation**
   - Test template loading
   - Validate library storage
   - Check export engines

3. **Fault Reporting**
   - Emit fault codes for any failures
   - Send completion signal to UDS
   - Report operational status

---

## COMMUNICATION PROTOCOL

### Universal Communicator Integration

Mission Debrief uses UniversalCommunicator for standardized messaging:

**Registered Signal Handlers:**
- `auto_registration` - UDS protocol compliance
- `radio_check` - Communication health validation
- `rollcall` - System presence confirmation
- `narrative.assembled` - Narrative assembly completion
- `mission.status` - Mission progress updates

**Message Lifecycle:**
- Only responds to `message_state: "CALL_SENT"`
- Sends responses with `message_state: "CALL_ANSWERED"`
- Uses radio codes for status communication

---

## FILE STRUCTURE

```
Command Center/Mission Debrief/
├─ mission_debrief_module.py     # Main module entry point (Address: 5)
├─ debrief_module.py             # Legacy entry point
├─ Debrief/
│  ├─ debrief_manager.py         # Child component (5-1)
│  └─ (narrative engine files)
├─ The Librarian/
│  ├─ librarian.py               # Child component (5-2)
│  └─ (archive management files)
├─ Library/                      # Report archive storage
├─ templates/                    # Report templates
├─ tools/                        # Professional tooling
├─ _init_debrief_manager.py      # Initialization scripts
├─ _init_the_librarian.py
├─ README.md                     # This file
└─ Tests/
   └─ plans/
      └─ MISSION_DEBRIEF_SYSTEM_SUMMARY.md
```

---

## INITIALIZATION

### Module Startup Sequence

1. **Import and Setup**
   ```python
   from mission_debrief_module import MissionDebriefModule
   ```

2. **Instantiation**
   ```python
   mission_debrief = MissionDebriefModule(
       bus=bus_instance,
       communicator=communicator_instance
   )
   ```

3. **Bus Registration**
   - Registers with address "5"
   - Subscribes to required signal handlers
   - Initializes Debrief Manager (5-1) and Librarian (5-2)

4. **Self-Test Execution**
   - Validates both child components
   - Tests template loading
   - Reports health status to UDS
   - Transitions to operational state

---

## INTEGRATION POINTS

### Upstream Dependencies
- **Bus-1 (CANBUS)** - Communication infrastructure
- **UDS (DIAG-1)** - Health monitoring
- **Marshall (3)** - Section output aggregation

### Downstream Handoffs
- **GUI (GUI-1)** - Report delivery to operator
- **Library (5-2)** - Permanent archival

### External Tools
- **PDF Generators** - Report PDF creation
- **DOCX Generators** - Report DOCX creation
- **Signature Tools** - Digital signature application
- **Watermark Tools** - Document watermarking

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
- Debrief Manager (5-1) operational status
- Librarian (5-2) archival functionality
- Template loading and application
- Report generation engines
- Export functionality (PDF, DOCX)

---

## TROUBLESHOOTING

### Common Issues

**Issue:** Mission Debrief responds to UDS but report generation fails  
**Solution:** Validate Debrief Manager initialization, check template files exist

**Issue:** Section outputs not collected  
**Solution:** Verify CANBUS signal subscriptions, check Marshall completion signals

**Issue:** Library archival fails  
**Solution:** Check filesystem permissions, verify storage quota available

**Issue:** Export generation errors  
**Solution:** Confirm external tool dependencies installed (PDF/DOCX generators)

---

## RELATED DOCUMENTATION

- **System Architecture:** `The War Room\SOPs\READ FILES\Build Specs\CURRENT_SYSTEM_ARCHITECTURE_2025-10-12.md`
- **CANBUS Protocol:** `Command Center/Data Bus/diagnostic_manager/read_me/CANBUS_LINBUS_ARCHITECTURE.md`
- **Template Documentation:** `Command Center/Mission Debrief/templates/` (template-specific docs)

---

**Document Type:** Module README  
**Module:** Mission Debrief (5)  
**Status:** CURRENT  
**Last Updated:** 2025-10-12

