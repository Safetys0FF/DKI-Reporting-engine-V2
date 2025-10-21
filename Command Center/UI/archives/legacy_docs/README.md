# GUI MODULE (Address: GUI-1)
## Enhanced Functional Graphical User Interface

---

## MODULE OVERVIEW

The GUI (Graphical User Interface) is the **primary operator interface** for Central Command. It provides case management, evidence upload, status monitoring, and report viewing capabilities through a desktop application built on Tkinter.

**Module Address:** GUI-1  
**Module Type:** User Interface  
**Parent Module:** Yes (owns 9 child components)  
**Bus Connections:** CANBUS (primary)

---

## RESPONSIBILITIES

### Primary Functions
1. **User Interface Rendering** - Desktop application window and widgets
2. **Case Management** - Create, open, and manage investigation cases
3. **Evidence Upload** - User-friendly evidence intake interface
4. **Status Monitoring** - Real-time system and case status display
5. **Report Viewing** - Display completed reports to operators

### Communication Roles
- **Listens on CANBUS for:**
  - System status updates
  - Case progress signals
  - Report completion signals
  
- **Emits on CANBUS:**
  - Evidence upload signals
  - Case creation signals
  - User interaction events
  - Fault codes (GUI-1.00-GUI-1.99)

---

## CHILD COMPONENTS

The GUI manages 9 child components:

| Address | Component | Purpose |
|---------|-----------|---------|
| GUI-1.1 | Case Manager UI | Case creation and management interface |
| GUI-1.2 | Evidence Upload UI | Evidence file selection and upload |
| GUI-1.3 | Status Dashboard | System health and progress display |
| GUI-1.4 | Report Viewer | Completed report display |
| GUI-1.5 | Section Monitor | Individual section status tracking |
| GUI-1.6 | Profile Manager | Operator profiles and authentication |
| GUI-1.7 | Settings Panel | Configuration and preferences |
| GUI-1.8 | Log Viewer | System log display and filtering |
| GUI-1.9 | Bus State Monitor | CANBUS connection status |

---

## FAULT CODES

**Range:** GUI-1.00 - GUI-1.99

### Critical Faults (GUI-1.00-GUI-1.09)
- `GUI-1.00` - GUI initialization failure
- `GUI-1.01` - Tkinter runtime error
- `GUI-1.02` - Window creation failure
- `GUI-1.03` - Bus connection failure

### UI Component Faults (GUI-1.10-GUI-1.19)
- `GUI-1.10` - Case Manager UI failure
- `GUI-1.11` - Evidence Upload UI failure
- `GUI-1.12` - Status Dashboard failure
- `GUI-1.13` - Report Viewer failure

### User Interaction Faults (GUI-1.20-GUI-1.29)
- `GUI-1.20` - File selection error
- `GUI-1.21` - Case creation error
- `GUI-1.22` - Evidence upload error
- `GUI-1.23` - Invalid user input

### Display Faults (GUI-1.30-GUI-1.39)
- `GUI-1.30` - Rendering error
- `GUI-1.31` - Widget layout error
- `GUI-1.32` - Status update error

---

## OPERATIONAL FLOW

### GUI Startup Flow

```
1. Application Launch
   ↓
   enhanced_functional_gui.py initializes
   ↓
2. Tkinter Initialization
   ├─ Create root window
   ├─ Configure theme and styling
   └─ Set window properties
   ↓
3. Profile & Authentication
   ├─ Check for existing profiles
   ├─ Run setup wizard if needed
   └─ Authenticate operator
   ↓
4. Bus Connection
   ├─ Connect to CANBUS (if available)
   ├─ Register signal handlers
   └─ Set operational mode (SAFEMODE if no bus)
   ↓
5. UI Component Loading
   ├─ Build main window layout
   ├─ Initialize all 9 child components
   └─ Subscribe to status signals
   ↓
6. Operational State
   ├─ Display main interface
   └─ Begin event loop
```

### Case Processing User Flow

```
1. Operator: Create New Case
   ↓
   GUI emits "case_create" signal on CANBUS
   ↓
2. Operator: Upload Evidence
   ↓
   GUI emits "files_add" signal with file paths
   ↓
3. System: Processing Updates
   ↓
   GUI receives status signals
   ├─ Update Status Dashboard (GUI-1.3)
   ├─ Update Section Monitor (GUI-1.5)
   └─ Update Bus State (GUI-1.9)
   ↓
4. System: Report Complete
   ↓
   GUI receives "narrative.assembled" signal
   ├─ Notify operator
   └─ Enable Report Viewer (GUI-1.4)
   ↓
5. Operator: View Report
   ↓
   Report Viewer displays final report
```

### Self-Test Protocol

When commanded by UDS, GUI performs:

1. **Component Health Check**
   - Verify Tkinter runtime operational
   - Test root window exists
   - Validate all 9 UI components loaded

2. **Functional Validation**
   - Test widget rendering
   - Verify CANBUS connection
   - Check file dialog functionality

3. **Fault Reporting**
   - Emit fault codes for any failures
   - Send completion signal to UDS
   - Report operational status

**Current Issue:** GUI responds to auto-registration even if window not fully initialized or shown. Validation should check `self.root` exists AND `self._root_shown` or GUI is ready for user interaction.

---

## COMMUNICATION PROTOCOL

### Universal Communicator Integration

GUI uses UniversalCommunicator for standardized messaging:

**Registered Signal Handlers:**
- `auto_registration` - UDS protocol compliance
- `radio_check` - Communication health validation
- `rollcall` - System presence confirmation
- `gui.status` - GUI status requests
- `gui.refresh` - Force refresh commands
- `gui.update_bus_state` - Bus state updates

**Message Lifecycle:**
- Only responds to `message_state: "CALL_SENT"`
- Sends responses with `message_state: "CALL_ANSWERED"`
- Uses radio codes for status communication

---

## FILE STRUCTURE

```
Command Center/UI/
├─ enhanced_functional_gui.py    # Main GUI class (Address: GUI-1)
├─ case_session.py               # Case management logic
├─ section_bus_adapter.py        # Section status adapter
├─ profile_registry.py           # User profile management
├─ ui_components.py              # Reusable UI widgets
├─ setup_wizard.py               # First-time setup
├─ profile_manager/
│  ├─ operator_manager.py        # Operator authentication
│  └─ auth_manager.py            # Token issuance
├─ components/                   # UI component library
│  └─ README.md
├─ archives/                     # Legacy UI versions
│  └─ README.md
├─ README.md                     # This file
└─ Test Plans/
   └─ ENHANCED_GUI_SYSTEM_SUMMARY.md
```

---

## INITIALIZATION

### Module Startup Sequence

**Standard Launch:**
```python
from enhanced_functional_gui import EnhancedDKIGUI

# Instantiate GUI
gui = EnhancedDKIGUI(gui_module=None, bus=bus_instance)

# Run event loop
gui.root.mainloop()
```

**Module Integration:**
```python
# When instantiated by GUI module wrapper
gui_module = GUIModule(bus=bus_instance)
gui = EnhancedDKIGUI(gui_module=gui_module, bus=None)
```

### Startup Requirements
1. Python 3.11+ with Tkinter support
2. Optional: tkinterdnd2 for drag-and-drop
3. CANBUS connection (or runs in SAFEMODE)
4. Profile registry database
5. Operator authentication

---

## OPERATIONAL MODES

### Normal Mode
- Connected to CANBUS
- Full system integration
- Real-time status updates
- All features operational

### SAFEMODE
- No CANBUS connection
- Standalone operation
- Limited functionality
- Local file management only

**Detection:**
```python
if gui.safemode_active:
    # Limited operations
else:
    # Full CANBUS integration
```

---

## INTEGRATION POINTS

### Upstream Dependencies
- **Bus-1 (CANBUS)** - Communication infrastructure
- **UDS (DIAG-1)** - Health monitoring

### System Interactions
- **Evidence Locker (1)** - Evidence upload handoff
- **Warden (2-1)** - Mission status updates
- **Marshall (3)** - Section progress tracking
- **Mission Debrief (5)** - Report retrieval

---

## OPERATIONAL STATUS

### Current Build Status
**Status:** PARTIALLY OPERATIONAL  
**Last Updated:** 2025-10-12

**✅ Confirmed Working:**
- Tkinter initialization
- UniversalCommunicator integration
- UDS auto-registration response
- Message lifecycle compliance
- Signal handler registration

**⚠️ Known Issues:**
- Auto-registration responds even if GUI not fully initialized
- Setup wizard may block operational launch
- Functional validation needed for UI rendering
- Bus connection status tracking incomplete

**❌ Requires Functional Testing:**
- Window rendering and display
- Case creation workflow
- Evidence upload functionality
- Status dashboard updates
- Report viewer operation

---

## TROUBLESHOOTING

### Common Issues

**Issue:** GUI responds to UDS but window doesn't appear  
**Solution:** Check `self.root` initialization, verify `self._root_shown` state, validate Tkinter runtime

**Issue:** Setup wizard blocks launch  
**Solution:** Investigate setup wizard trigger conditions, verify profile registry exists

**Issue:** CANBUS connection fails (SAFEMODE active)  
**Solution:** Verify bus instance passed to GUI constructor, check bus connectivity

**Issue:** Status updates not displaying  
**Solution:** Confirm signal handler subscriptions, validate GUI update methods

---

## RELATED DOCUMENTATION

- **System Architecture:** `The War Room\SOPs\READ FILES\Build Specs\CURRENT_SYSTEM_ARCHITECTURE_2025-10-12.md`
- **CANBUS Protocol:** `Command Center/Data Bus/diagnostic_manager/read_me/CANBUS_LINBUS_ARCHITECTURE.md`
- **UI Components:** `Command Center/UI/components/README.md`
- **Profile Management:** `Command Center/UI/profile_manager/`

---

**Document Type:** Module README  
**Module:** GUI (GUI-1)  
**Status:** CURRENT  
**Last Updated:** 2025-10-12
