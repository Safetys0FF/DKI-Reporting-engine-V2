# Central Command UI

**Location:** `F:\The Central Command\Command Center\UI`  
**Entry Point:** `gui_main_application.py`  
**Module Address:** GUI-1 (CANBUS Parent Module)

## Overview
Modern GUI for the Central Command DKI Engine. Integrates with CANBUS, LINBUS, and UDS diagnostic systems for comprehensive case management and evidence processing.

---

## Core Files

### Entry & Module
- **gui_main_application.py** - Application entry point
- **gui_module.py** - CANBUS parent module (GUI-1), lifecycle management
- **enhanced_functional_gui.py** - Main GUI implementation (3900+ lines)

### State & Communication
- **case_session.py** - Case state management, section tracking
- **section_bus_adapter.py** - LINBUS communication with Report Engine sections
- **component_loader.py** - Dynamic component loading system

### User Management
- **user_profile_manager.py** - User credentials, API keys (SQLite)
- **profile_registry.py** - Profile registry, operator profiles
- **profile_manager/** - Auth, operator management, audit logging

### Helpers
- **ui_components.py** - Shared UI widgets (StatusBar, etc.)
- **contracts/** - Contract detection system
- **intake/** - File intake processing

---

## Directory Structure

```
UI/
├── gui_main_application.py          # Entry point
├── enhanced_functional_gui.py       # Main GUI
├── gui_module.py                    # CANBUS parent
├── user_profile_manager.py          # User/auth
├── case_session.py                  # State
├── section_bus_adapter.py           # LINBUS
├── component_loader.py              # Dynamic loading
├── profile_registry.py              # Profiles
├── ui_components.py                 # Widgets
├── components/                      # Modular UI components
│   ├── setup_wizard.py
│   ├── case_management_panel.py
│   ├── evidence_panel.py
│   ├── system_health_dashboard.py
│   ├── api_status_panel.py
│   └── ... (9 components)
├── profile_manager/                 # Auth system
│   ├── operator_manager.py
│   ├── auth_manager.py
│   └── audit_log.py
├── contracts/                       # Contract detection
├── intake/                          # File processing
├── tests/                           # GUI tests
├── artifacts/                       # User documents
├── profile_pictures/                # User avatars
├── final_reports/                   # Generated reports
├── watermarks/                      # Report branding
├── user_profiles.db                 # SQLite database
├── user_profile.json                # Active user profile
├── api_keys.json                    # API configuration
└── archives/                        # Legacy/obsolete files
```

---

## Launch Instructions

### Standard Launch (Full System)
```batch
F:\The Central Command\Command Center\Start Menu\Run Time\DKI_ENGINE_LAUNCHER.bat
```
Launches: Backend modules + UDS + GUI (unified orchestration)

### GUI Only (Testing)
```batch
cd "F:\The Central Command\Command Center\UI"
python gui_main_application.py
```

### Headless (No GUI)
```batch
DKI_ENGINE_LAUNCHER.bat --no-gui
```

---

## Key Features

### User Management
- First-time setup wizard
- SQLite-backed user database
- Profile pictures (displayed on home page)
- Role-based access control (basic/analyst/supervisor/admin)
- API key management (OpenAI, Anthropic, etc.)

### Case Management
- Create/load cases with metadata
- Evidence intake (drag-drop supported with tkinterdnd2)
- Section-based workflow (metadata, OCR, analysis, etc.)
- Report generation and export

### System Integration
- **CANBUS:** Parent module (GUI-1) with 9 child components
- **LINBUS:** Section communication via `section_bus_adapter`
- **UDS:** Health monitoring, diagnostics, fault reporting
- **Report Engine:** Integration via Gateway and Marshall modules

### Dynamic Components
The `component_loader.py` system enables progressive disclosure:
- Basic users: Core tabs (Home, Cases, Workspace)
- Analysts: +Review, Assembly
- Supervisors: +System monitoring
- Admins: +Advanced settings

Components load dynamically based on:
- User role permissions
- Installed dependencies (psutil, requests, tkinterdnd2, etc.)
- System configuration

---

## Dependencies

### Required
- Python 3.10+
- tkinter (GUI framework)
- Pillow (PIL) - Image handling
- sqlite3 (User database)

### Optional (feature-dependent)
- psutil - System health monitoring
- requests - API status checks
- tkinterdnd2 - Drag-and-drop file upload

### Internal
- bus_core (CANBUS) - `F:\...\Data Bus\Bus Core Design`
- universal_communicator (LINBUS) - `F:\...\Data Bus`
- UDS diagnostic system - `F:\...\Data Bus\diagnostic_manager`

---

## CANBUS Architecture

**Module Address:** GUI-1  
**Type:** Parent Module  
**Children:** GUI-1.1 through GUI-1.9 (9 components)

### Responsibilities
- CANBUS registration and signal translation
- UDS health monitoring (30-sec heartbeats to Bus-1.5)
- Lifecycle management (start/stop/sleep/wake)
- Thread monitoring and recovery
- Communication with Evidence Locker (1), Warden (2-1), Marshall (3), Mission Debrief (5)

### Signal Flow
```
GUI-1 → DKIReportBus → Universal Signals
GUI-1 ← Bus responses ← Other parent modules
GUI-1 → UDS (Bus-1.5) → Health status
```

---

## Development Notes

### Import Path Setup
The GUI automatically adds required paths to `sys.path`:
```python
UI_ROOT = Path(__file__).parent.resolve()
COMMAND_CENTER_ROOT = UI_ROOT.parent
BUS_DIR = COMMAND_CENTER_ROOT / "Data Bus"
BUS_CORE_DIR = BUS_DIR / "Bus Core Design"
sys.path.insert(0, str(BUS_CORE_DIR))
```

### Known Issues Fixed
- ~~Missing `tag_taxonomy` import~~ ✓ Removed (unused)
- ~~Incorrect `bus_core` path~~ ✓ Fixed with BUS_CORE_DIR
- ~~Setup wizard completion tracking~~ ✓ Added callback system
- ~~Python 3.7 hashlib compatibility~~ ✓ Using hmac.compare_digest

### Testing
```bash
# Smoke test
python tests/gui_smoke_test.py

# Function test
python tests/gui_function_test.py
```

---

## File Change Log

### 2025-10-13 - Cleanup & Documentation
- Removed unused `tag_taxonomy` import
- Archived legacy docs to `archives/legacy_docs/`
- Removed empty `certificates/` and `templates/` folders
- Created comprehensive README
- Verified all import paths

### 2025-10-10 - Profile Picture Feature
- Added profile picture support to `user_profile_manager.py`
- Updated home page to display user avatar
- Added profile picture browser in ProfileEditor

### 2025-10-10 - Setup Wizard Rewrite
- Complete rewrite of `components/setup_wizard.py`
- Added completion callback tracking
- Mandatory wizard for new users (retry loop)
- Fixed window visibility issues

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    gui_main_application.py              │
│                    (Entry Point)                        │
└─────────────────────┬───────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
┌───────▼────────┐         ┌────────▼────────────┐
│   gui_module   │         │ enhanced_functional │
│   (GUI-1)      │◄────────┤      _gui           │
│ CANBUS Parent  │         │  (Main GUI Logic)   │
└────────┬───────┘         └──────────┬──────────┘
         │                            │
         │                  ┌─────────┴──────────┐
         │                  │                    │
    ┌────▼─────┐     ┌──────▼───────┐   ┌───────▼────────┐
    │ DKIReport│     │ ComponentLoader│   │ CaseSession   │
    │   Bus    │     │ (9 components) │   │ (State Mgmt)  │
    └──────────┘     └────────────────┘   └───────────────┘
         │
         ├─► Evidence Locker (1)
         ├─► Warden (2-1)
         ├─► Marshall (3)
         ├─► Mission Debrief (5)
         └─► UDS (Bus-1.5)
```

---

## Contact & Support
For issues or questions, check:
- System logs: `F:\The Central Command\Command Center\Data Bus\diagnostic_manager\Unified_diagnostic_system\library\system_logs`
- Dev tracking: `F:\dev_tracking\logs`
- UDS diagnostic dashboard (if running)

**Last Updated:** 2025-10-13  
**Status:** ✅ Operational - Ready for system testing
