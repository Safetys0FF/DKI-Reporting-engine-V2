# Central Command - Run Time

**Location:** `F:\The Central Command\Command Center\Start Menu\Run Time`  
**Entry Point:** `main_application.py` (Unified System Orchestrator)  
**Primary Launcher:** `DKI_ENGINE_LAUNCHER.bat`

## Overview
The Run Time directory contains the **Unified System Orchestrator** - the master controller that launches and coordinates all Central Command modules including Backend systems, UDS diagnostics, and GUI in a phased, synchronized startup sequence.

---

## Core Files

### Launcher Scripts
- **DKI_ENGINE_LAUNCHER.bat** - Primary system launcher (Windows)
  - Default: Full unified system (Backend + UDS + GUI)
  - Flags: `gui-only`, `backend-only`, `--no-gui`
- **START_HERE.bat** - Alias to DKI_ENGINE_LAUNCHER.bat

### Python Entry Point
- **main_application.py** - Unified System Orchestrator (547 lines)
  - Phased backend module initialization
  - UDS diagnostic system launcher (subprocess)
  - GUI launcher (subprocess)
  - Process monitoring and lifecycle management
  - Graceful shutdown coordination

### Documentation
- **SYSTEM_STARTUP_SUMMARY.md** - Launch modes and architecture
- **QUICK_START.md** - Quick reference guide

---

## Directory Structure

```
Run Time/
├── DKI_ENGINE_LAUNCHER.bat      # Primary launcher
├── START_HERE.bat               # Alias to launcher
├── main_application.py          # Unified orchestrator
├── SYSTEM_STARTUP_SUMMARY.md    # Documentation
├── QUICK_START.md               # Quick start guide
└── archives/                    # Legacy files
    ├── run_dki_engine.py           (old wrapper)
    ├── main_application_activation.py (old bootstrap)
    ├── basic_test.py               (test file)
    ├── central_plugin.py           (old plugin)
    ├── test_plans/                 (old tests)
    ├── INSTALL_DKI_ENGINE.bat      (installer)
    ├── UNINSTALL_DKI_ENGINE.bat    (uninstaller)
    ├── DKI_Engine_Installer_macOS.command
    └── api_keys.json               (moved to UI)
```

---

## Launch Modes

### 1. Unified System (Default)
```batch
DKI_ENGINE_LAUNCHER.bat
```
**Launches:**
- Phase 1: Backend modules (Warden, Evidence Locker, Marshall, Mission Debrief)
- Phase 2: UDS Diagnostic System
- Phase 3: Central Command GUI
- Monitoring: Process health checks and auto-restart

**Startup Sequence:**
```
1. Initialize Warden (ECC + Gateway Controller)
2. Initialize Evidence Locker (file indexing)
3. Initialize Marshall (Evidence Manager)
4. Initialize Mission Debrief (Narrative + Librarian)
5. Launch UDS (subprocess) → Wait for health signal
6. Launch GUI (subprocess) → Monitor for user exit
```

### 2. GUI Only (Testing)
```batch
DKI_ENGINE_LAUNCHER.bat gui-only
```
Launches only the GUI without backend systems or UDS.

### 3. Backend Only (Headless)
```batch
DKI_ENGINE_LAUNCHER.bat --no-gui
DKI_ENGINE_LAUNCHER.bat backend-only
```
Runs backend modules and UDS without GUI interface.

---

## System Architecture

### Unified System Orchestrator
**Class:** `UnifiedSystemOrchestrator`

#### Components
1. **Backend Orchestrator** (`InitializationOrchestrator`)
   - Phased startup prevents cascade failures
   - Module health checks (30-second intervals)
   - Fault isolation and reporting
   
2. **UDS Launcher**
   - Subprocess: `core.py` from diagnostic_manager
   - Health monitoring via CANBUS (Bus-1.5)
   - Automatic restart on failure

3. **GUI Launcher**
   - Subprocess: `gui_main_application.py`
   - User session management
   - Graceful shutdown on window close

4. **Process Monitor**
   - Daemon thread for subprocess health
   - Automatic cleanup on termination
   - Coordinated shutdown sequence

#### Lifecycle States
- **INITIALIZING** - Module startup in progress
- **ACTIVE** - Module running and responsive
- **SLEEPING** - Module paused (low power)
- **STOPPED** - Module cleanly terminated
- **FAULT** - Module error state

---

## Module Integration

### Backend Modules
All modules loaded via `main_application.py`:

```python
# The Warden (ECC + Gateway Controller)
sys.path.append(r"F:\The Central Command\The Warden")
from warden_main import Warden

# Evidence Locker (File Indexing)
sys.path.append(r"F:\The Central Command\Evidence Locker")
from evidence_locker_main import EvidenceLocker

# The Marshall (Evidence Manager)
sys.path.append(r"F:\The Central Command\The Marshall")
from evidence_manager import EvidenceManager

# Mission Debrief (Narrative + Librarian)
# Dynamically loaded from Mission Debrief directory
```

### UDS Integration
```python
UDS_DIR = Path(r"F:/The Central Command/Command Center/Data Bus/diagnostic_manager/Unified_diagnostic_system")
subprocess.Popen([sys.executable, str(UDS_DIR / "core.py")])
```

### GUI Integration
```python
GUI_DIR = Path(r"F:/The Central Command/Command Center/UI")
subprocess.Popen([sys.executable, str(GUI_DIR / "gui_main_application.py")])
```

---

## Environment Setup

### Python Path
The launcher automatically configures `PYTHONPATH`:
```
%COMMAND_CENTER_DIR%
%COMMAND_CENTER_DIR%\UI
%COMMAND_CENTER_DIR%\Mission Debrief
%COMMAND_CENTER_DIR%\Data Bus
%COMMAND_CENTER_DIR%\Data Bus\Bus Core Design
%ROOT_DIR%\The Warden
%ROOT_DIR%\Evidence Locker
%ROOT_DIR%\The Marshall
%ROOT_DIR%\The War Room\Processors
```

### External Dependencies
Automatically configured paths for:
- **Poppler** (PDF processing): `poppler-25.07.0\Library\bin`
- **FFmpeg** (media processing): `ffmpeg-2025-09-18\bin`
- **Tesseract OCR**: Auto-detected from common install locations
- **Tessdata**: Language data for OCR

---

## Shutdown Sequence

### Graceful Shutdown
1. User closes GUI → Sets shutdown flag
2. GUI process terminates
3. UDS process terminates
4. Warden.stop() → Stops all backend modules
5. Cleanup: Close file handles, flush logs, save state

### Emergency Shutdown
- `Ctrl+C` → Immediate shutdown via KeyboardInterrupt
- Process monitoring detects unexpected termination
- Automatic cleanup of all subprocesses

---

## Logging & Diagnostics

### System Logs
- **UDS Logs**: `Data Bus\diagnostic_manager\Unified_diagnostic_system\library\system_logs`
- **Bus Core Logs**: `Data Bus\diagnostic_manager\...\system_logs\dki_bus_core.log`
- **Dev Tracking**: `F:\dev_tracking\logs` (summary logs per memory protocols)

### Health Monitoring
- Backend modules: 30-second heartbeat to CANBUS
- UDS: Continuous diagnostic monitoring
- GUI: Process monitor checks for unexpected termination

---

## Troubleshooting

### Common Issues

**1. Python Not Found**
```
ERROR: Unable to locate a Python interpreter.
```
**Fix:** Install Python 3.10+ or activate venv: `.venv\Scripts\activate`

**2. Module Import Error**
```
ModuleNotFoundError: No module named 'warden_main'
```
**Fix:** Verify directory structure - check The Warden exists at root level

**3. GUI Doesn't Launch**
```
ERROR: Central Command UI not found
```
**Fix:** Verify `F:\The Central Command\Command Center\UI\gui_main_application.py` exists

**4. UDS Launch Failure**
```
WARNING: UDS did not signal ready within timeout
```
**Fix:** Check UDS logs in diagnostic_manager system_logs

---

## Development Notes

### Adding New Modules
To integrate a new backend module:
1. Import in `main_application.py`
2. Add to `InitializationOrchestrator.execute_phased_startup()`
3. Implement health check method
4. Register with CANBUS if parent module

### Testing Individual Components
```bash
# Test backend only
python main_application.py --no-gui

# Test UDS only
cd "Command Center\Data Bus\diagnostic_manager\Unified_diagnostic_system"
python core.py

# Test GUI only
cd "Command Center\UI"
python gui_main_application.py
```

---

## Change Log

### 2025-10-13 - Cleanup & Documentation
- Archived legacy launchers (run_dki_engine.py, main_application_activation.py)
- Removed empty folders (certificates, templates, watermarks, README)
- Archived installers and test files
- Created comprehensive README
- Verified unified orchestration working

### 2025-10-10 - Unified System Implementation
- Created UnifiedSystemOrchestrator class
- Integrated UDS and GUI subprocess management
- Added process monitoring and health checks
- Updated DKI_ENGINE_LAUNCHER.bat with unified mode

---

## Quick Reference

| Command | Action |
|---------|--------|
| `DKI_ENGINE_LAUNCHER.bat` | Launch full system |
| `DKI_ENGINE_LAUNCHER.bat gui-only` | GUI only |
| `DKI_ENGINE_LAUNCHER.bat --no-gui` | Backend only |
| `START_HERE.bat` | Alias to main launcher |

---

## Contact & Support
For issues or questions:
- Review logs in UDS system_logs directory
- Check dev_tracking logs for agent handoff notes
- Verify all module directories exist at expected paths

**Last Updated:** 2025-10-13  
**Status:** ✅ Operational - Unified orchestration active

