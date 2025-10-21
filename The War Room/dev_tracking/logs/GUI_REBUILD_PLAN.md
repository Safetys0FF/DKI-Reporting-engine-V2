# GUI Complete Rebuild Plan
**Date:** October 10, 2025  
**Scope:** Full system integration with deduplication, CANBUS, UDS, lifecycle management

---

## Current State Analysis

**`enhanced_functional_gui.py` - 3408 lines:**
- 6 classes (InputPersistence, LoginDialog, CaseCreationDialog, ProfileEditor, EvidenceCard, EnhancedDKIGUI)
- 129 functions/methods
- Multiple dialog/window classes embedded
- No CANBUS parent module integration
- No heartbeat monitoring
- No startup/shutdown controllers
- No thread tracking

---

## Duplication Patterns Found

### 1. Dialog Classes (Windows within Windows)
- `LoginDialog` - Creates tk.Toplevel, builds form, handles validation
- `CaseCreationDialog` - Creates tk.Toplevel, builds form, handles validation
- `ProfileEditor` - Creates tk.Toplevel, builds form, handles validation
- **Pattern:** Same structure repeated 3 times (window creation, form building, validation)

### 2. Frame Building (Functions within Functions)
- `_build_home_tab()` - Creates frames, labels, buttons
- `_build_cases_tab()` - Creates frames, labels, buttons
- `_build_workspace_tab()` - Creates frames, labels, buttons
- `_build_review_tab()` - Creates frames, labels, buttons
- `_build_assembly_tab()` - Creates frames, labels, buttons
- **Pattern:** Same frame/grid setup repeated 5 times

### 3. State Management (Scattered Variables)
- `self.active_case_id`
- `self.operator_name`
- `self.current_report`
- `self.cards`
- `self.case_overview`
- Plus 15+ more StringVars
- **Pattern:** State scattered across 30+ instance variables

---

## Proposed Architecture - ONE Executable Module

### **File Structure (Clean)**
```
gui_module.py (Main executable - 1500 lines)
├── Startup Controller
├── CANBUS Integration
├── Parent Module Protocol
├── Thread Monitoring
├── Heartbeat System
├── Shutdown Controller
└── Enhanced GUI delegation

enhanced_functional_gui.py (Refactored - 1200 lines)
├── EnhancedDKIGUI (UI only, no bus logic)
└── Delegates to GUIModule for all communication

components/ (9 modular widgets)
└── Already organized ✓
```

---

## New Architecture - `gui_module.py`

```python
"""
GUI Module - Parent Module Wrapper for Enhanced Functional GUI
Address: GUI-1
Type: Parent Module (CANBUS-connected)

Responsibilities:
- CANBUS registration and communication
- Parent module signal translation
- UDS health monitoring and fault reporting
- Heartbeat broadcasting
- Startup/shutdown lifecycle management
- Thread monitoring and recovery
- State management and coordination
"""

import sys
import os
import time
import json
import logging
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum

# Pre-load all imports (FAST CANBUS - no lazy loading in signal path)
sys.path.insert(0, str(Path(__file__).parent.parent / "Data Bus"))
from universal_communicator import UniversalCommunicator, RadioCode
from bus_core import DKIReportBus

sys.path.insert(0, str(Path(__file__).parent.parent / "Data Bus" / "diagnostic_manager"))
from system_protocol_registry import SystemProtocolRegistry, SIGNAL_TRANSLATIONS

logger = logging.getLogger("GUIModule")


class GUIModuleState(Enum):
    """GUI module lifecycle states"""
    CREATED = "CREATED"
    INITIALIZING = "INITIALIZING"
    ACTIVE = "ACTIVE"
    IDLE = "IDLE"
    SHUTTING_DOWN = "SHUTTING_DOWN"
    SHUTDOWN = "SHUTDOWN"
    FAULTED = "FAULTED"


class GUIModule:
    """
    GUI-1 Parent Module - Full CANBUS integration wrapper
    
    Architecture:
    - Acts as parent for 9 child GUI components (GUI-1.1 through GUI-1.9)
    - Translates child broadcasts to universal signals
    - Coordinates with Evidence Locker, Warden, Marshall, Mission Debrief
    - Monitored by UDS via heartbeat and health checks
    - Manages startup, shutdown, and thread lifecycle
    """
    
    def __init__(self):
        """Initialize GUI module (CREATED state)"""
        self.module_address = "GUI-1"
        self.state = GUIModuleState.CREATED
        self.initialized = False
        self.shutting_down = False
        self.start_time = time.time()
        
        # CANBUS integration
        self.bus: Optional[DKIReportBus] = None
        self.communicator: Optional[UniversalCommunicator] = None
        
        # Thread monitoring dict
        self.threads: Dict[str, threading.Thread] = {
            "heartbeat": None,
            "gui_mainloop": None,
            "signal_processor": None,
            "health_monitor": None
        }
        self.thread_lock = threading.Lock()
        
        # Application state (centralized)
        self.app_state = {
            "active_case_id": None,
            "active_case": None,
            "operator_name": None,
            "operator_role": None,
            "evidence_pool": [],
            "last_heartbeat": None,
            "components_loaded": 0
        }
        self.state_lock = threading.Lock()
        
        # Component registry
        self.components: Dict[str, Dict[str, Any]] = {}
        
        # Enhanced GUI instance (UI layer)
        self.gui_instance = None
        
        # Protocol registry (for signal translations)
        self.protocol_registry = SystemProtocolRegistry()
        
        logger.info(f"[CREATED] GUI-1 module created")
    
    # =========================================================================
    # STARTUP CONTROLLER
    # =========================================================================
    
    def initialize_system(self) -> bool:
        """
        Startup controller - ordered initialization sequence
        
        Steps:
        1. Initialize CANBUS connection
        2. Register UniversalCommunicator
        3. Register to CANBUS as parent module
        4. Start heartbeat monitor thread
        5. Start health monitor thread
        6. Register signal handlers
        7. Load GUI components
        8. Start enhanced GUI
        
        Returns:
            True if initialization successful, False otherwise
        """
        self.state = GUIModuleState.INITIALIZING
        logger.info("[STARTUP] GUI-1 initialization sequence starting...")
        
        startup_steps = [
            ("Initialize CANBUS", self._init_canbus),
            ("Register to bus", self._register_to_canbus),
            ("Start heartbeat monitor", self._start_heartbeat_monitor),
            ("Start health monitor", self._start_health_monitor),
            ("Register signal handlers", self._register_signal_handlers),
            ("Load GUI components", self._load_gui_components),
            ("Initialize enhanced GUI", self._init_enhanced_gui)
        ]
        
        for step_num, (step_name, step_func) in enumerate(startup_steps, 1):
            logger.info(f"[STARTUP {step_num}/{len(startup_steps)}] {step_name}...")
            try:
                result = step_func()
                if result is False:
                    logger.error(f"[STARTUP ABORT] Step failed: {step_name}")
                    self.state = GUIModuleState.FAULTED
                    self._emit_fault("GUI-INIT-FAIL", f"Startup failed at: {step_name}")
                    return False
            except Exception as e:
                logger.error(f"[STARTUP ERROR] {step_name}: {e}")
                self.state = GUIModuleState.FAULTED
                self._emit_fault("GUI-INIT-ERROR", f"Exception in {step_name}: {str(e)}")
                return False
        
        self.initialized = True
        self.state = GUIModuleState.ACTIVE
        logger.info("[OK] GUI-1 system initialized successfully")
        
        # Announce readiness
        self._announce_ready()
        
        return True
    
    def _announce_ready(self):
        """Announce GUI-1 is ready to all systems"""
        if self.communicator:
            self.communicator.send_signal(
                target_address="Bus-1",
                signal_name="gui.ready",
                radio_code=RadioCode.TEN_FOUR,
                payload={
                    "module_address": self.module_address,
                    "operator": self.app_state.get("operator_name"),
                    "components_loaded": len(self.components),
                    "timestamp": datetime.now().isoformat()
                }
            )
    
    # =========================================================================
    # HEARTBEAT MONITOR
    # =========================================================================
    
    def _start_heartbeat_monitor(self) -> bool:
        """Start heartbeat monitor thread"""
        def heartbeat_loop():
            """Periodic heartbeat broadcast to UDS"""
            heartbeat_interval = 30  # seconds
            
            while not self.shutting_down:
                try:
                    # Check thread health
                    dead_threads = self._check_thread_health()
                    
                    # Send heartbeat
                    health_status = self._get_health_status()
                    
                    if self.communicator:
                        self.communicator.send_signal(
                            target_address="Bus-1.5",  # UDS
                            signal_name="module.heartbeat",
                            radio_code=RadioCode.STATUS,
                            payload={
                                "module_address": self.module_address,
                                "timestamp": datetime.now().isoformat(),
                                "state": self.state.value,
                                "uptime_seconds": time.time() - self.start_time,
                                "health_status": health_status,
                                "threads_active": len([t for t in self.threads.values() if t and t.is_alive()]),
                                "dead_threads": dead_threads
                            }
                        )
                    
                    with self.state_lock:
                        self.app_state["last_heartbeat"] = datetime.now().isoformat()
                    
                except Exception as e:
                    logger.error(f"[HEARTBEAT ERROR] {e}")
                
                time.sleep(heartbeat_interval)
        
        thread = threading.Thread(target=heartbeat_loop, daemon=True, name="GUI-Heartbeat")
        thread.start()
        
        with self.thread_lock:
            self.threads["heartbeat"] = thread
        
        logger.info("[OK] Heartbeat monitor thread started")
        return True
    
    def _check_thread_health(self) -> List[str]:
        """Check thread health and return list of dead threads"""
        dead_threads = []
        
        with self.thread_lock:
            for name, thread in self.threads.items():
                if thread is not None and not thread.is_alive():
                    dead_threads.append(name)
                    logger.warning(f"[THREAD DEAD] {name}")
        
        # Emit fault if critical thread died
        if dead_threads:
            self._emit_fault(
                "GUI-THREAD-DEAD",
                f"Thread(s) terminated: {', '.join(dead_threads)}"
            )
        
        return dead_threads
    
    # =========================================================================
    # SHUTDOWN CONTROLLER
    # =========================================================================
    
    def shutdown(self):
        """
        Shutdown controller - graceful cleanup sequence
        
        Steps:
        1. Set shutting_down flag (stops heartbeat)
        2. Close GUI components
        3. Stop all monitored threads
        4. Disconnect from CANBUS
        5. Save final state
        6. Emit shutdown signal to UDS
        """
        if self.shutting_down:
            return
        
        logger.info("[SHUTDOWN] GUI-1 shutdown sequence starting...")
        self.shutting_down = True
        self.state = GUIModuleState.SHUTTING_DOWN
        
        shutdown_steps = [
            ("Stopping heartbeat", self._stop_heartbeat),
            ("Closing GUI components", self._close_gui_components),
            ("Stopping threads", self._stop_all_threads),
            ("Disconnecting CANBUS", self._disconnect_canbus),
            ("Saving state", self._save_final_state),
            ("Announcing shutdown", self._announce_shutdown)
        ]
        
        for step_name, step_func in shutdown_steps:
            logger.info(f"[SHUTDOWN] {step_name}...")
            try:
                step_func()
            except Exception as e:
                logger.error(f"[SHUTDOWN ERROR] {step_name}: {e}")
        
        self.state = GUIModuleState.SHUTDOWN
        logger.info("[OK] GUI-1 shutdown complete")
    
    def _stop_all_threads(self):
        """Stop all monitored threads"""
        with self.thread_lock:
            for name, thread in self.threads.items():
                if thread and thread.is_alive():
                    logger.info(f"[SHUTDOWN] Waiting for thread: {name}")
                    thread.join(timeout=5.0)
                    if thread.is_alive():
                        logger.warning(f"[SHUTDOWN] Thread {name} did not stop gracefully")
    
    def _announce_shutdown(self):
        """Announce shutdown to UDS and other modules"""
        if self.communicator:
            self.communicator.send_signal(
                target_address="Bus-1",
                signal_name="module.shutdown",
                radio_code=RadioCode.TEN_FOUR,
                payload={
                    "module_address": self.module_address,
                    "timestamp": datetime.now().isoformat(),
                    "uptime_seconds": time.time() - self.start_time
                }
            )
    
    # =========================================================================
    # CANBUS & PARENT MODULE INTEGRATION
    # =========================================================================
    
    def _handle_child_broadcast(self, payload: Dict[str, Any]) -> None:
        """
        Parent module signal translation (FAST - no lazy imports)
        
        Children emit to gui.child.broadcast, parent translates to universal signals.
        Pre-loaded translation table from system_protocol_registry.
        """
        message_type = payload.get('message_type')
        if not message_type:
            return
        
        # Fast lookup from pre-loaded protocol
        translations = SIGNAL_TRANSLATIONS["gui"]["translations"]
        
        if message_type in translations:
            for sig_def in translations[message_type]:
                radio = RadioCode[sig_def["radio_code"].replace("-", "_").upper()] if sig_def.get("radio_code") else None
                self.communicator.send_signal(
                    target_address="Bus-1",
                    signal_name=sig_def["signal"],
                    radio_code=radio,
                    payload=payload
                )
        
        # Special handling for user actions that target other modules
        if message_type == "case_created":
            self._route_to_evidence_locker("case.new", payload, RadioCode.TEN_SIX)
        elif message_type == "evidence_uploaded":
            self._route_to_evidence_locker("evidence.ingest", payload, RadioCode.TEN_SIX)
        elif message_type == "report_requested":
            self._route_to_mission_debrief("report.generate", payload, RadioCode.TEN_FOUR)
    
    def _route_to_evidence_locker(self, signal: str, payload: Dict, radio: RadioCode):
        """Fast routing to Evidence Locker (1)"""
        self.communicator.send_signal(
            target_address="1",
            signal_name=signal,
            radio_code=radio,
            payload=payload
        )
    
    def _route_to_mission_debrief(self, signal: str, payload: Dict, radio: RadioCode):
        """Fast routing to Mission Debrief (5)"""
        self.communicator.send_signal(
            target_address="5",
            signal_name=signal,
            radio_code=radio,
            payload=payload
        )
    
    # =========================================================================
    # THREAD MONITORING
    # =========================================================================
    
    def register_thread(self, name: str, thread: threading.Thread):
        """Register thread for monitoring"""
        with self.thread_lock:
            self.threads[name] = thread
        logger.info(f"[THREAD] Registered: {name}")
    
    def get_thread_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all monitored threads"""
        with self.thread_lock:
            status = {}
            for name, thread in self.threads.items():
                if thread:
                    status[name] = {
                        "alive": thread.is_alive(),
                        "daemon": thread.daemon,
                        "name": thread.name
                    }
                else:
                    status[name] = {"alive": False, "daemon": None, "name": None}
            return status
    
    # =========================================================================
    # STATE MANAGEMENT (Centralized)
    # =========================================================================
    
    def update_state(self, key: str, value: Any):
        """Thread-safe state update"""
        with self.state_lock:
            self.app_state[key] = value
        
        # Notify GUI to refresh
        if self.gui_instance:
            self.gui_instance.on_state_changed(key, value)
    
    def get_state(self, key: str) -> Any:
        """Thread-safe state retrieval"""
        with self.state_lock:
            return self.app_state.get(key)
    
    # =========================================================================
    # SIGNAL HANDLERS (From Other Parent Modules)
    # =========================================================================
    
    def _on_evidence_classified(self, payload: Dict):
        """Evidence Locker classified evidence"""
        evidence_id = payload.get("evidence_id")
        logger.info(f"[SIGNAL] Evidence classified: {evidence_id}")
        self.update_state("last_evidence", payload)
    
    def _on_case_created(self, payload: Dict):
        """Evidence Locker created case"""
        case_id = payload.get("case_id")
        logger.info(f"[SIGNAL] Case created: {case_id}")
        self.update_state("active_case_id", case_id)
        self.update_state("active_case", payload)
    
    def _on_section_routed(self, payload: Dict):
        """Warden routed section"""
        section_id = payload.get("section_id")
        logger.info(f"[SIGNAL] Section routed: {section_id}")
    
    def _on_report_ready(self, payload: Dict):
        """Mission Debrief completed report"""
        report_id = payload.get("report_id")
        logger.info(f"[SIGNAL] Report ready: {report_id}")
        self.communicator.send_signal(
            target_address="Bus-1",
            radio_code=RadioCode.TEN_EIGHT,
            payload={"report_id": report_id}
        )
    
    # =========================================================================
    # UDS INTEGRATION
    # =========================================================================
    
    def _on_health_check(self, payload: Dict):
        """UDS health check - respond immediately"""
        health = self._get_health_status()
        
        self.communicator.send_signal(
            target_address="Bus-1.5",
            signal_name="module.health",
            radio_code=RadioCode.STATUS,
            payload={
                "module_address": self.module_address,
                "status": health["status"],
                "state": self.state.value,
                "uptime": health["uptime"],
                "components": health["components_active"],
                "threads": health["threads_alive"]
            }
        )
    
    def _get_health_status(self) -> Dict:
        """Calculate current health status"""
        threads_alive = sum(1 for t in self.threads.values() if t and t.is_alive())
        components_active = len([c for c in self.components.values() if c.get("active")])
        
        if not self.bus or not self.communicator:
            status = "SAFEMODE"
        elif self.state == GUIModuleState.FAULTED:
            status = "FAULTED"
        elif threads_alive < 2:  # Heartbeat + GUI mainloop minimum
            status = "DEGRADED"
        else:
            status = "OPERATIONAL"
        
        return {
            "status": status,
            "uptime": time.time() - self.start_time,
            "components_active": components_active,
            "threads_alive": threads_alive
        }
    
    def _emit_fault(self, fault_code: str, description: str):
        """Emit fault to UDS"""
        if self.communicator:
            self.communicator.send_signal(
                target_address="Bus-1.5",
                signal_name="module.fault",
                radio_code=RadioCode.SOS,
                payload={
                    "module_address": self.module_address,
                    "fault_code": fault_code,
                    "description": description,
                    "timestamp": datetime.now().isoformat()
                }
            )
        logger.error(f"[FAULT {fault_code}] {description}")
    
    # =========================================================================
    # DEDUPLICATION HELPERS
    # =========================================================================
    
    def create_dialog_window(self, parent, title: str, size: tuple = (400, 300)) -> tk.Toplevel:
        """
        Standardized dialog window creation (DEDUPLICATION)
        
        Replaces duplicated window creation in:
        - LoginDialog
        - CaseCreationDialog
        - ProfileEditor
        """
        window = tk.Toplevel(parent)
        window.title(title)
        window.geometry(f"{size[0]}x{size[1]}")
        window.transient(parent)
        window.resizable(False, False)
        
        # Center window
        window.update_idletasks()
        x = (window.winfo_screenwidth() // 2) - (size[0] // 2)
        y = (window.winfo_screenheight() // 2) - (size[1] // 2)
        window.geometry(f"{size[0]}x{size[1]}+{x}+{y}")
        
        return window
    
    def create_form_frame(self, parent, title: str) -> ttk.LabelFrame:
        """Standardized form frame creation (DEDUPLICATION)"""
        frame = ttk.LabelFrame(parent, text=title, padding=12)
        frame.columnconfigure(1, weight=1)
        return frame
    
    # =========================================================================
    # STUB METHODS (To be implemented)
    # =========================================================================
    
    def _init_canbus(self): pass
    def _register_to_canbus(self): pass
    def _start_health_monitor(self): pass
    def _register_signal_handlers(self): pass
    def _load_gui_components(self): pass
    def _init_enhanced_gui(self): pass
    def _stop_heartbeat(self): pass
    def _close_gui_components(self): pass
    def _disconnect_canbus(self): pass
    def _save_final_state(self): pass
```

---

## Deduplication Strategy

### Before (Duplicated)
```python
# LoginDialog.__init__
self.window = tk.Toplevel(parent)
self.window.title("Login")
self.window.geometry("400x300")
self.window.transient(parent)
self.window.resizable(False, False)

# CaseCreationDialog.__init__
self.window = tk.Toplevel(parent)
self.window.title("New Case")
self.window.geometry("500x400")
self.window.transient(parent)
self.window.resizable(False, False)

# ProfileEditor.__init__
self.window = tk.Toplevel(parent)
self.window.title("Edit Profile")
self.window.geometry("600x500")
self.window.transient(parent)
self.window.resizable(False, False)
```

### After (Unified)
```python
# All dialogs use:
self.window = gui_module.create_dialog_window(parent, "Login", size=(400, 300))
```

---

## Performance Requirements

### Fast CANBUS Passages
- ✓ All imports pre-loaded (no lazy imports in signal path)
- ✓ Translation table cached in memory
- ✓ Direct dictionary lookups (no function calls)
- ✓ Minimal allocations in signal handlers

### Thread Safety
- ✓ Thread monitoring dict with locks
- ✓ State updates protected by locks
- ✓ Signal queue thread-safe

### Clean Architecture
- ✓ Single entry point: `gui_module.py`
- ✓ Clear separation: GUIModule (integration) + EnhancedDKIGUI (UI)
- ✓ No circular dependencies
- ✓ All executable code (no lazy file stacks)

---

## Complete Build Checklist

- [ ] Create `gui_module.py` with all infrastructure
- [ ] Implement startup controller (7 ordered steps)
- [ ] Implement heartbeat monitor (30s intervals)
- [ ] Implement thread monitoring dict with health checks
- [ ] Implement shutdown controller (6 ordered steps)
- [ ] Implement `_handle_child_broadcast()` with fast translation
- [ ] Add signal handlers for all parent modules
- [ ] Add UDS health check response
- [ ] Create deduplication helpers (dialog, form, frame builders)
- [ ] Refactor `enhanced_functional_gui.py` to use GUIModule
- [ ] Remove duplicated window creation code
- [ ] Centralize state in GUIModule
- [ ] Register GUI-1 to system_registry.json
- [ ] Test: Startup sequence
- [ ] Test: Heartbeat broadcasts
- [ ] Test: Thread monitoring
- [ ] Test: Shutdown sequence
- [ ] Test: Signal translation
- [ ] Test: UDS integration

**Total: 18 tasks, ~4-6 hours, ONE executable module**

---

**This is the COMPLETE plan. Proceed with build?**

