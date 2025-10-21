# CENTRAL COMMAND - SYSTEM README
## Digital Knowledge Infrastructure for Investigative Reporting

**Version:** Current Build (2025-10-12)  
**Status:** OPERATIONAL (Validation Phase)  
**Architecture:** 7 Parent Modules, Dual-Bus (CANBUS + LINBUS)

---

## EXECUTIVE SUMMARY

Central Command is an **autonomous investigative report generation system** designed to ingest evidence, analyze content, and produce comprehensive investigative reports with minimal human intervention.

The system operates as a **7-module parent architecture** coordinated through a signal-based CANBUS communication infrastructure, with a secondary LINBUS for orchestration workflows.

---

## QUICK START

### Launch the System

**Windows (Recommended):**
```batch
F:\The Central Command\Command Center\Data Bus\diagnostic_manager\Unified_diagnostic_system\LAUNCH_DIAGNOSTIC_SYSTEM.bat
```

**Python Direct:**
```powershell
cd "F:\The Central Command"
python -m Command_Center.Data_Bus.diagnostic_manager.Unified_diagnostic_system
```

### Launch GUI Only (Standalone)

```powershell
cd "F:\The Central Command\Command Center\UI"
python enhanced_functional_gui.py
```

---

## SYSTEM ARCHITECTURE

### The 7 Parent Modules

| Address | Module | Primary Function | Documentation |
|---------|--------|------------------|---------------|
| **1** | Evidence Locker | Evidence ingestion, classification, manifest generation | `Evidence Locker/README.md` |
| **2-1** | The Warden | System orchestration, ecosystem control, gateway routing | `The Warden/README.md` |
| **3** | The Marshall | Evidence distribution, LINBUS proxy for Analyst sections | `The Marshall/README.md` |
| **5** | Mission Debrief | Report finalization, narrative assembly, library archival | `Command Center/Mission Debrief/README.md` |
| **Bus-1** | Central Command Bus | Signal-based communication infrastructure | `Command Center/Data Bus/README.md` |
| **GUI-1** | Enhanced GUI | Operator interface, case management, status monitoring | `Command Center/UI/README.md` |
| **DIAG-1** | Unified Diagnostic System | Health monitoring, protocol enforcement, system launch | `Command Center/Data Bus/diagnostic_manager/Unified_diagnostic_system/README.md` |

### Communication Architecture

**CANBUS** - Primary high-throughput data bus
- All 7 parent modules connected
- Signal-based pub/sub architecture
- Parent-only message filtering
- Message lifecycle enforcement (CALL_SENT → CALL_ANSWERED)

**LINBUS** - Secondary orchestration bus
- Master: Warden (2-1)
- Sub-Master: Marshall (3)
- Analyst Sections (4-1 to 4-8) connected via Marshall proxy
- Throttle coordination with Evidence Locker and Mission Debrief

---

## OPERATIONAL FLOW

### Complete Case Processing Workflow

```
1. Operator Action: Create Case + Upload Evidence
   ├─ GUI (GUI-1) receives user input
   └─ Emits: case_create, files_add signals on CANBUS

2. Evidence Processing (Module 1)
   ├─ Evidence Locker receives evidence files
   ├─ Classifies evidence by type and relevance
   ├─ Builds case manifest
   └─ Emits: evidence_ready signal

3. Orchestration (Module 2-1)
   ├─ Warden receives evidence_ready
   ├─ ECC validates system readiness
   ├─ Gateway (2-3) analyzes manifest
   └─ Commands Marshall via LINBUS

4. Evidence Distribution (Module 3)
   ├─ Marshall receives distribution command (LINBUS)
   ├─ Wakes target Analyst sections via LINBUS
   ├─ Delivers section-specific evidence packages
   └─ Monitors section processing

5. Section Processing (Analyst Deck 4-1 to 4-8)
   ├─ Each section generates its narrative
   ├─ Reports completion to Marshall (LINBUS)
   └─ Marshall relays to CANBUS

6. Report Finalization (Module 5)
   ├─ Mission Debrief collects section outputs
   ├─ Assembles final narrative
   ├─ Applies professional tooling (signatures, watermarks)
   ├─ Archives to Library
   └─ Emits: narrative.assembled signal

7. Operator Notification
   ├─ GUI receives narrative.assembled
   └─ Displays completed report to operator
```

---

## KEY DESIGN PRINCIPLES

### Parent-Child Hierarchy
- **Parent modules** (7 total) coordinate system-level operations
- **Child components** are tested and managed by their parents
- UDS only monitors parent modules, not children directly

### Message Lifecycle Protocol
- **CALL_SENT** - Request initiation
- **CALL_ANSWERED** - Response delivery
- **CALL_COMPLETED** - Optional confirmation
- Prevents infinite communication loops

### Fault Code System
- Each module owns a fault code range (e.g., 1.00-1.99 for Evidence Locker)
- Standardized severity levels (CRITICAL, ERROR, WARNING)
- Central registry in `system_protocol_registry.py`

---

## MODULE DESCRIPTIONS

### Evidence Locker (1)
**Function:** Evidence intake and classification  
**Children:** 8 components (1.1-1.8)  
**Key Files:**
- `Evidence Locker/evidence_locker_module.py` (main)
- `Evidence Locker/evidence_classifier.py`
- `Evidence Locker/case_manifest_builder.py`

### The Warden (2-1)
**Function:** Master orchestration and control  
**Children:** Ecosystem Controller (2-2), Gateway Controller (2-3)  
**Key Files:**
- `The Warden/warden_module.py` (main)
- `The Warden/ecosystem_controller.py`
- `The Warden/gateway_controller.py`

### The Marshall (3)
**Function:** Evidence distribution and LINBUS proxy  
**Children:** Evidence Manager (3-1) + proxies Analyst Deck (4-1 to 4-8)  
**Key Files:**
- `The Marshall/marshall_module.py` (main)
- `The Marshall/Evidence_Checkout/evidence_manager.py`

### Mission Debrief (5)
**Function:** Report finalization and archival  
**Children:** Debrief Manager (5-1), The Librarian (5-2)  
**Key Files:**
- `Command Center/Mission Debrief/mission_debrief_module.py` (main)
- `Command Center/Mission Debrief/Debrief/debrief_manager.py`
- `Command Center/Mission Debrief/The Librarian/librarian.py`

### Central Command Bus (Bus-1)
**Function:** Communication infrastructure  
**Key Files:**
- `Command Center/Data Bus/Bus Core Design/bus_core.py` (main)
- `Command Center/Data Bus/universal_communicator.py`

### Enhanced GUI (GUI-1)
**Function:** Operator interface  
**Children:** 9 UI components (GUI-1.1 to GUI-1.9)  
**Key Files:**
- `Command Center/UI/enhanced_functional_gui.py` (main)

### Unified Diagnostic System (DIAG-1)
**Function:** Health monitoring and protocol enforcement  
**Key Files:**
- `Command Center/Data Bus/diagnostic_manager/Unified_diagnostic_system/core.py` (main)
- `Command Center/Data Bus/diagnostic_manager/Unified_diagnostic_system/comms.py`
- `Command Center/Data Bus/diagnostic_manager/Unified_diagnostic_system/enforcement.py`

---

## CONFIGURATION

### System Registry
**File:** `Command Center/Data Bus/diagnostic_manager/Unified_diagnostic_system/read_me/system_protocol_registry.py`

Contains:
- Parent-child relationship definitions
- Fault code registry
- Protocol version information
- System address mappings

### Bus Configuration
**File:** `Command Center/Data Bus/configs/`

Bus operation parameters, signal registry defaults, logging levels.

---

## TROUBLESHOOTING

### System Won't Launch
1. Check Python 3.11+ installed
2. Verify CANBUS initialization (Bus-1)
3. Review UDS logs in `diagnostic_manager/Unified_diagnostic_system/library/system_logs/`

### GUI Not Responding
1. Check if setup wizard blocking launch
2. Verify bus connection (`gui.bus_connected`)
3. Run GUI in standalone mode (SAFEMODE)

### Evidence Not Processing
1. Verify Evidence Locker (1) operational
2. Check Gateway Controller (2-3) routing
3. Validate Marshall (3) LINBUS proxy active

### Sections Not Generating
1. Confirm Marshall (3) waking sections via LINBUS
2. Check Analyst section handlers registered
3. Verify section evidence delivery

---

## DOCUMENTATION INDEX

### Module Documentation
- `Evidence Locker/README.md` - Module 1
- `The Warden/README.md` - Module 2-1
- `The Marshall/README.md` - Module 3
- `Command Center/Mission Debrief/README.md` - Module 5
- `Command Center/UI/README.md` - GUI-1
- `Command Center/Data Bus/README.md` - Bus-1
- `Command Center/Data Bus/diagnostic_manager/Unified_diagnostic_system/README.md` - DIAG-1

### System Documentation (This Folder)
- **SYSTEM_README.md** (this file) - Quick start and overview
- **CURRENT_SYSTEM_ARCHITECTURE_2025-10-12.md** - Complete architectural analysis
- **PRD_Central_Command.md** - Product requirements document
- **System_Blueprint_Central_Command.md** - Technical design specifications
- **SOP_Central_Command.md** - Standard operating procedures

### Protocol Documentation
- `Command Center/Data Bus/Bus Core Design/README/CANBUS_LINBUS_ARCHITECTURE.md`
- `Command Center/Data Bus/diagnostic_manager/Unified_diagnostic_system/read_me/system_protocol_registry.py`

---

## SYSTEM STATUS

**Current Build Status:** OPERATIONAL (Validation Phase)  
**Last System Update:** 2025-10-12

**✅ Operational:**
- All 7 parent modules instantiate successfully
- CANBUS communication active
- Message lifecycle protocol enforced
- UDS monitoring active

**⚠️ Under Validation:**
- Parent module self-tests too permissive (false positives)
- Functional validation needed beyond initialization checks
- GUI setup wizard may block operational launch

**🎯 Next Steps:**
- Functional testing of complete case workflow
- Stricter self-test validation logic
- Performance optimization under load

---

## SUPPORT

### Log Files
- **UDS Logs:** `Command Center/Data Bus/diagnostic_manager/Unified_diagnostic_system/library/system_logs/`
- **Bus Logs:** `Command Center/Data Bus/dki_bus_core.log`
- **GUI Logs:** `Command Center/UI/enhanced_gui.log`

### Key Contacts
- **System Architect:** [User]
- **Dev Tracking:** `The War Room/dev_tracking/`

---

**Document Type:** System README  
**Status:** CURRENT  
**Last Updated:** 2025-10-12


