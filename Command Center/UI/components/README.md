# UI Components

**Location:** `F:\The Central Command\Command Center\UI\components`  
**Date Organized:** October 10, 2025

---

## Overview

Modular, reusable tkinter widgets for the Central Command Enhanced GUI. Each component is self-contained and can be imported and embedded in the main application.

---

## Available Components

### Core Panels

**`case_management_panel.py`**  
Case creation, loading, and file management panel with controls for new case workflows.

**`evidence_panel.py`**  
Evidence intake, processing, and section generation panel with file upload and processing controls.

**`file_drop_zone.py`**  
Modern drag-and-drop file upload zone with visual feedback, file type detection, and progress tracking.

### Monitoring & Status

**`system_health_dashboard.py`**  
Real-time system performance monitoring with CPU, memory, disk usage, and process tracking using `psutil`.

**`api_status_panel.py`**  
API connectivity monitoring dashboard for OpenAI, Google Maps, Gemini, and other external services.

### Control Interfaces

**`section_control_panel.py`**  
Control panel for section operations and workflow management.

**`report_control_panel.py`**  
Report generation and export control panel.

### Setup & Configuration

**`setup_wizard.py`**  
First-time user setup wizard with multi-page onboarding for user info and API key configuration.

**`user_profile_dialog.py`**  
User profile management dialog for operator settings and preferences.

---

## Usage

Import components into the main GUI:

```python
from components import (
    SystemHealthDashboard,
    APIStatusPanel,
    CaseManagementPanel,
    EvidencePanel,
    FileDropZone
)

# Example: Add health dashboard to a frame
health_panel = SystemHealthDashboard(parent_frame)
health_panel.pack(fill='both', expand=True)
```

---

## Integration Notes

- All components are `ttk.Frame` or `tk.Frame` subclasses
- Components accept parent widget and optional callbacks
- Some components require additional dependencies (e.g., `tkinterdnd2` for drag-and-drop)
- Components use shared UI styling from parent application

---

## Dependencies

**Required:**
- `tkinter` (standard library)
- `ttk` (standard library)

**Optional:**
- `tkinterdnd2` - Drag-and-drop support in FileDropZone
- `psutil` - System metrics in SystemHealthDashboard
- `requests` - API testing in APIStatusPanel

---

## Migration History

**October 10, 2025:** Extracted from `Test Plans/gui support files/` and organized as modular components. Removed duplicate versions and cleaned up legacy test files.

