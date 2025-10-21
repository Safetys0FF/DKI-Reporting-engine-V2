# Central Command UI Structure

## Entry Point
- `gui_main_application.py` - Main entry point, initializes GUI-1 module and launches Enhanced GUI

## Core Files
- `enhanced_functional_gui.py` - Main GUI implementation (3900+ lines)
- `gui_module.py` - CANBUS parent module (GUI-1)
- `user_profile_manager.py` - SQLite-backed user credential management
- `profile_registry.py` - Profile JSON management
- `case_session.py` - Case state and session management
- `section_bus_adapter.py` - Section/bus integration adapter
- `component_loader.py` - Dynamic component loading
- `ui_components.py` - Reusable UI components

## Subdirectories

### components/
Modular UI components loaded dynamically:
- `setup_wizard.py` - First-time user setup
- `api_status_panel.py` - API connectivity display
- `case_management_panel.py` - Case management UI
- `evidence_panel.py` - Evidence handling UI
- `file_drop_zone.py` - Drag-and-drop file handling
- `report_control_panel.py` - Report generation controls
- `section_control_panel.py` - Section management
- `system_health_dashboard.py` - System health monitoring
- `user_profile_dialog.py` - User profile editing

### profile_manager/
User authentication and access control:
- `operator_manager.py` - Operator profile management
- `auth_manager.py` - Authentication and token issuance
- `audit_log.py` - Activity auditing

### contracts/
Contract type detection and registry:
- `detector.py` - Contract detection logic
- `registry.py` - Contract registry

### intake/
Intake form processing:
- `processor.py` - Form processing logic

### tests/
Test suites:
- `gui_function_test.py` - Functional tests
- `gui_smoke_test.py` - Smoke tests

### archives/
Legacy and backup files:
- `Enhanced_GUI_old/` - Previous GUI implementation
- `Test Plans/` - Integration documentation

### Data Directories
- `profile_pictures/` - User profile images
- `artifacts/` - Company docs, contracts, intake forms
- `final_reports/` - Generated reports
- `watermarks/` - Watermark images
- `certificates/` - SSL certificates
- `templates/` - Report templates

## State Files
- `user_profile.json` - Current user profile
- `user_profiles.db` - User credentials database
- `gui_state.json` - GUI state persistence
- `api_keys.json` - API key storage

## Import Structure
```
gui_main_application.py
├── gui_module.GUIModule
└── enhanced_functional_gui.EnhancedDKIGUI
    ├── case_session.CaseSession
    ├── section_bus_adapter.SectionBusAdapter
    ├── profile_registry.ProfileRegistry
    ├── profile_manager.operator_manager.OperatorManager
    ├── profile_manager.auth_manager
    ├── ui_components.StatusBar
    ├── components.setup_wizard.run_setup_wizard
    ├── component_loader (dynamic)
    └── bus_core.DKIReportBus
```

## Launch Sequence
1. `gui_main_application.py` initializes GUIModule (GUI-1)
2. GUIModule sets up CANBUS integration
3. EnhancedDKIGUI launches and checks for user profile
4. If no profile exists, setup_wizard runs
5. Main GUI displays with home dashboard

## Cleanup Completed
- Removed temporary test files
- Removed backup component files
- Cleared __pycache__ directories
- Moved test documentation to archives
- Verified all imports and compilation

