r"""
GUI Module - Parent Module Wrapper for Enhanced Functional GUI
Address: GUI-1
Type: Parent Module (CANBUS-connected)
Date: October 10, 2025
Location: F:\The Central Command\Command Center\UI

RESPONSIBILITIES:
- CANBUS registration and communication
- Parent module signal translation (gui.child.broadcast → universal signals)
- UDS health monitoring and fault reporting
- Heartbeat broadcasting (30-second intervals)
- Startup/shutdown lifecycle management
- Thread monitoring and recovery
- State management and coordination
- Communication with Evidence Locker, Warden, Marshall, Mission Debrief

ARCHITECTURE:
Acts as parent for 9 child GUI components (GUI-1.1 through GUI-1.9).
Matches Evidence Locker, Warden, Marshall, Mission Debrief parent module pattern.
"""

import sys
import os
import time
import json
import logging
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from enum import Enum

# Pre-load all imports (FAST CANBUS - no lazy loading in signal path)
ROOT_DIR = Path(__file__).resolve().parents[2]

# Add Data Bus to path
DATA_BUS_PATH = ROOT_DIR / "Command Center" / "Data Bus"
BUS_CORE_PATH = DATA_BUS_PATH / "Bus Core Design"
for path in [DATA_BUS_PATH, BUS_CORE_PATH]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from universal_communicator import UniversalCommunicator, RadioCode
from bus_core import DKIReportBus

# Add diagnostic_manager to path for protocol registry
DIAGNOSTIC_PATH = DATA_BUS_PATH / "diagnostic_manager"
if str(DIAGNOSTIC_PATH) not in sys.path:
    sys.path.insert(0, str(DIAGNOSTIC_PATH))

from system_protocol_registry import SystemProtocolRegistry, SIGNAL_TRANSLATIONS

# Setup logging
logger = logging.getLogger("GUIModule")


# =============================================================================
# LIFECYCLE STATES
# =============================================================================

class GUIModuleState(Enum):
    """GUI module lifecycle states"""
    CREATED = "CREATED"
    INITIALIZING = "INITIALIZING"
    ACTIVE = "ACTIVE"
    IDLE = "IDLE"
    SHUTTING_DOWN = "SHUTTING_DOWN"
    SHUTDOWN = "SHUTDOWN"
    FAULTED = "FAULTED"


# =============================================================================
# MAIN GUI MODULE CLASS
# =============================================================================

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
        self.threads: Dict[str, Optional[threading.Thread]] = {
            "heartbeat": None,
            "gui_mainloop": None,
            "signal_processor": None,
            "health_monitor": None
        }
        self.thread_lock = threading.Lock()
        
        # Application state (centralized)
        self.app_state: Dict[str, Any] = {
            "active_case_id": None,
            "active_case": None,
            "operator_name": None,
            "operator_role": None,
            "evidence_pool": [],
            "last_heartbeat": None,
            "components_loaded": 0,
            "bus_connected": False
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
    # LOGGING HELPER
    # =========================================================================
    
    def log(self, message: str, level: str = "info"):
        """Centralized logging helper"""
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(message)
    
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
        
        Returns:
            True if initialization successful, False otherwise
        """
        self.state = GUIModuleState.INITIALIZING
        self.log("[STARTUP] GUI-1 initialization sequence starting...")
        
        startup_steps = [
            ("Initialize CANBUS", self._init_canbus),
            ("Register to CANBUS", self._register_to_canbus),
            ("Start heartbeat monitor", self._start_heartbeat_monitor),
            ("Start health monitor", self._start_health_monitor),
            ("Register signal handlers", self._register_signal_handlers),
            ("Load component registry", self._load_gui_components),
            ("Announce readiness", self._announce_ready)
        ]
        
        for step_num, (step_name, step_func) in enumerate(startup_steps, 1):
            self.log(f"[STARTUP {step_num}/{len(startup_steps)}] {step_name}...")
            try:
                result = step_func()
                if result is False:
                    self.log(f"[STARTUP ABORT] Step failed: {step_name}", "error")
                    self.state = GUIModuleState.FAULTED
                    self._emit_fault("GUI-INIT-FAIL", f"Startup failed at: {step_name}")
                    return False
            except Exception as e:
                self.log(f"[STARTUP ERROR] {step_name}: {e}", "error")
                self.state = GUIModuleState.FAULTED
                self._emit_fault("GUI-INIT-ERROR", f"Exception in {step_name}: {str(e)}")
                return False
        
        self.initialized = True
        self.state = GUIModuleState.ACTIVE
        self.log("[OK] GUI-1 system initialized successfully")
        
        return True
    
    def _init_canbus(self) -> bool:
        """Initialize CANBUS connection"""
        try:
            # Initialize DKIReportBus
            self.bus = DKIReportBus()
            
            # MODULE INITIALIZATION PROTOCOL - Wait for bus ready and module turn
            self.log("[GUI] Waiting for bus stabilization...")
            if not self.bus.wait_for_ready(timeout=15.0):
                self.log("[GUI] Bus stabilization timeout - initializing in degraded mode", "warning")
                return True  # Continue in degraded mode
            
            self.log("[GUI] Bus ready - waiting for module turn in sequence...")
            if not self.bus.wait_for_module_turn('GUI-1', timeout=30.0):
                self.log("[GUI] Module turn timeout - initializing in degraded mode", "warning")
                return True  # Continue in degraded mode
            
            # Initialize UniversalCommunicator (positional address arg, not kwarg)
            self.communicator = UniversalCommunicator(
                self.module_address,
                bus_connection=self.bus
            )
            
            with self.state_lock:
                self.app_state["bus_connected"] = True
            
            self.log("[OK] CANBUS initialized")
            return True
            
        except Exception as e:
            self.log(f"[WARN] CANBUS init failed: {e} - Running in SAFEMODE", "warning")
            # Allow graceful degradation
            return True  # Don't abort startup
    
    def _register_to_canbus(self) -> bool:
        """Register GUI-1 as parent module on CANBUS"""
        if not self.bus or not self.communicator:
            self.log("No bus connection - skipping registration (SAFEMODE)", "warning")
            return True
        
        try:
            # Register system address with bus
            self.bus.register_system_address(self.module_address, {
                "system_type": "gui_parent",
                "capabilities": ["user_interface", "case_management", "system_monitoring"],
                "status": "active",
                "mode": "primary",
                "registered_at": datetime.now().isoformat()
            })
            
            # MODULE INITIALIZATION PROTOCOL - Register with bus
            if self.bus.register_module_init('GUI-1', {
                'version': '1.0',
                'type': 'gui',
                'capabilities': ['user_interface', 'case_management', 'system_monitoring']
            }):
                self.log("[OK] GUI-1 registered with bus (Address GUI-1)")
            else:
                self.log("[WARN] GUI-1 registration failed - continuing anyway", "warning")
            
            # Emit ROLLCALL signal to announce presence
            self.communicator.send_rollcall()
            
            self.log("[OK] Registered to CANBUS as GUI-1 parent module")
            return True
            
        except Exception as e:
            self.log(f"[WARN] CANBUS registration failed: {e} - Continuing in SAFEMODE", "warning")
            return True  # Continue even if registration fails
    
    def _start_heartbeat_monitor(self) -> bool:
        """Start heartbeat monitor thread"""
        def heartbeat_loop():
            """Periodic heartbeat broadcast to UDS"""
            heartbeat_interval = 30  # seconds
            
            while not self.shutting_down:
                try:
                    # Check thread health
                    dead_threads = self._check_thread_health()
                    
                    # Get health status
                    health = self._get_health_status()
                    
                    # Send heartbeat to UDS
                    if self.communicator:
                        self.communicator.send_signal(
                            target_address="Bus-1.5",  # UDS
                            radio_code=RadioCode.STATUS.value,
                            message="GUI-1 heartbeat",
                            payload={
                                "module_address": self.module_address,
                                "timestamp": datetime.now().isoformat(),
                                "state": self.state.value,
                                "uptime_seconds": time.time() - self.start_time,
                                "health_status": health["status"],
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
        
        self.log("[OK] Heartbeat monitor thread started")
        return True
    
    def _start_health_monitor(self) -> bool:
        """Start health monitor thread (monitors thread health)"""
        # Health monitoring is done within heartbeat loop
        # This is a placeholder for future expansion
        self.log("[OK] Health monitor integrated with heartbeat")
        return True
    
    def _check_thread_health(self) -> List[str]:
        """
        Monitor thread health, return list of dead threads
        
        Called by heartbeat loop to detect dead threads
        """
        dead_threads = []
        
        with self.thread_lock:
            for name, thread in self.threads.items():
                if thread is not None and not thread.is_alive():
                    dead_threads.append(name)
        
        # Emit fault if critical thread died
        if dead_threads:
            self.log(f"[THREAD DEAD] {', '.join(dead_threads)}", "warning")
            self._emit_fault(
                "GUI-THREAD-DEAD",
                f"Thread(s) terminated: {', '.join(dead_threads)}"
            )
        
        return dead_threads
    
    def _register_signal_handlers(self) -> bool:
        """Register all signal handlers for CANBUS communication"""
        if not self.bus:
            self.log("No bus connection - skipping signal registration (SAFEMODE)", "warning")
            return True
        
        try:
            # Use bus.register_signal (not communicator.register_handler)
            # Child broadcast handler (wildcard from GUI children)
            self.bus.register_signal("gui.child.broadcast", self._handle_child_broadcast)
            
            # Evidence Locker signals
            self.bus.register_signal("evidence.classified", self._on_evidence_classified)
            self.bus.register_signal("case.created", self._on_case_created)
            
            # Warden signals
            self.bus.register_signal("section.routed", self._on_section_routed)
            self.bus.register_signal("gateway.ready", self._on_gateway_ready)
            
            # Marshall signals
            self.bus.register_signal("evidence.processed", self._on_evidence_processed)
            self.bus.register_signal("evidence.ready_for_debrief", self._on_evidence_ready)
            
            # Mission Debrief signals
            self.bus.register_signal("report.ready", self._on_report_ready)
            self.bus.register_signal("narrative.assembled", self._on_narrative_ready)
            
            # UDS signals
            self.bus.register_signal("uds.health_check", self._on_health_check)
            
            self.log("[OK] Signal handlers registered (10 handlers)")
            return True
        
        except Exception as e:
            self.log(f"[FAIL] Signal handler registration: {e}", "error")
            return False
    
    def _load_gui_components(self) -> bool:
        """Load component registry (components managed by ComponentLoader)"""
        # Component loading will be handled by ComponentLoader
        # This is a placeholder for component registry initialization
        with self.state_lock:
            self.app_state["components_loaded"] = 0
        
        self.log("[OK] Component registry initialized")
        return True
    
    def _announce_ready(self) -> bool:
        """Announce GUI-1 is ready to all systems"""
        if self.communicator:
            self.communicator.send_signal(
                target_address="Bus-1",
                radio_code=RadioCode.ACKNOWLEDGED.value,
                message="GUI-1 ready",
                payload={
                    "module_address": self.module_address,
                    "operator": self.app_state.get("operator_name"),
                    "components_loaded": len(self.components),
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        self.log("[OK] GUI-1 readiness announced")
        return True
    
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
        
        self.log("[SHUTDOWN] GUI-1 shutdown sequence starting...")
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
            self.log(f"[SHUTDOWN] {step_name}...")
            try:
                step_func()
            except Exception as e:
                self.log(f"[SHUTDOWN ERROR] {step_name}: {e}", "error")
        
        self.state = GUIModuleState.SHUTDOWN
        self.log("[OK] GUI-1 shutdown complete")
    
    def _stop_heartbeat(self):
        """Stop heartbeat monitor thread"""
        # Thread will stop when shutting_down flag is set
        self.log("[OK] Heartbeat monitor stopping")
    
    def _close_gui_components(self):
        """Close all GUI components"""
        if self.gui_instance:
            try:
                self.gui_instance.root.quit()
                self.log("[OK] GUI instance closed")
            except Exception as e:
                self.log(f"[WARN] GUI close error: {e}", "warning")
    
    def _stop_all_threads(self):
        """Stop all monitored threads"""
        with self.thread_lock:
            for name, thread in self.threads.items():
                if thread and thread.is_alive():
                    self.log(f"[SHUTDOWN] Waiting for thread: {name}")
                    thread.join(timeout=5.0)
                    if thread.is_alive():
                        self.log(f"[SHUTDOWN WARN] Thread {name} did not stop gracefully", "warning")
    
    def _disconnect_canbus(self):
        """Disconnect from CANBUS"""
        if self.communicator:
            try:
                # Cleanup communicator
                self.communicator = None
                self.log("[OK] CANBUS disconnected")
            except Exception as e:
                self.log(f"[WARN] CANBUS disconnect error: {e}", "warning")
    
    def _save_final_state(self):
        """Save final state before shutdown"""
        try:
            state_file = Path(__file__).parent / "gui_final_state.json"
            with self.state_lock:
                state_snapshot = dict(self.app_state)
            
            state_snapshot["shutdown_timestamp"] = datetime.now().isoformat()
            state_snapshot["uptime_seconds"] = time.time() - self.start_time
            
            with open(state_file, 'w') as f:
                json.dump(state_snapshot, f, indent=2)
            
            self.log("[OK] Final state saved")
        except Exception as e:
            self.log(f"[WARN] State save error: {e}", "warning")
    
    def _announce_shutdown(self):
        """Announce shutdown to UDS and other modules"""
        if self.communicator:
            try:
                self.communicator.send_signal(
                    target_address="Bus-1",
                    radio_code=RadioCode.ACKNOWLEDGED.value,
                    message="GUI-1 shutting down",
                    payload={
                        "module_address": self.module_address,
                        "timestamp": datetime.now().isoformat(),
                        "uptime_seconds": time.time() - self.start_time
                    }
                )
                self.log("[OK] Shutdown announced")
            except Exception as e:
                self.log(f"[WARN] Shutdown announcement error: {e}", "warning")

    def emit_child_event(self, message_type: str, payload: Optional[Dict[str, Any]] = None) -> None:
        """
        Receive child component event from Enhanced GUI and relay through parent module.

        Args:
            message_type: Identifier describing the event (matches protocol registry)
            payload: Optional additional event data
        """
        event_payload = dict(payload or {})
        event_payload["message_type"] = message_type

        # Mirror bus broadcast for tooling that listens to raw channel
        if self.bus:
            try:
                self.bus.emit("gui.child.broadcast", event_payload)
            except Exception as exc:
                self.log(f"[WARN] Unable to emit gui.child.broadcast: {exc}", "warning")

        # Route through standard translation pipeline
        self._handle_child_broadcast(event_payload)

    # =========================================================================
    # PARENT MODULE SIGNAL TRANSLATION
    # =========================================================================

    def _handle_child_broadcast(self, payload: Dict[str, Any]) -> None:
        """
        Parent module signal translation (FAST - pre-loaded tables)
        
        Children emit to gui.child.broadcast, parent translates to universal.
        Uses SIGNAL_TRANSLATIONS from system_protocol_registry (pre-loaded).
        """
        message_type = payload.get('message_type')
        if not message_type:
            self.log("[WARN] Child broadcast missing message_type", "warning")
            return
        
        self.log(f"[SIGNAL] GUI-1 received child broadcast: {message_type}")
        
        # Fast lookup from pre-loaded protocol
        translations = SIGNAL_TRANSLATIONS["gui"]["translations"]
        
        if message_type in translations:
            for sig_def in translations[message_type]:
                # Get radio code value (string)
                radio_code = sig_def.get("radio_code") or "10-4"
                
                # Emit universal signal using bus.emit (not communicator.send_signal)
                if self.bus:
                    self.bus.emit(sig_def["signal"], payload)
                
                self.log(f"[OK] Translated {message_type} to {sig_def['signal']}")
        
        # Route to specific parent modules based on intent
        self._route_child_message(message_type, payload)
    
    def _route_child_message(self, message_type: str, payload: Dict):
        """Route child messages to appropriate parent modules"""
        if not self.communicator or not self.bus:
            return
        
        # Case creation -> Evidence Locker
        if message_type == "case_created":
            self.communicator.send_signal(
                target_address="1",
                radio_code=RadioCode.EVIDENCE_RECEIVED.value,
                message="Case created by GUI",
                payload=payload
            )
            self.bus.emit("case.new", payload)
            self.log("[OK] Routed case_created to Evidence Locker")
        
        # Evidence upload -> Evidence Locker
        elif message_type == "evidence_uploaded":
            self.communicator.send_signal(
                target_address="1",
                radio_code=RadioCode.EVIDENCE_RECEIVED.value,
                message="Evidence uploaded by GUI",
                payload=payload
            )
            self.bus.emit("evidence.ingest", payload)
            self.log("[OK] Routed evidence_uploaded to Evidence Locker")
        
        # Report request -> Mission Debrief
        elif message_type == "report_requested":
            self.communicator.send_signal(
                target_address="5",
                radio_code=RadioCode.ACKNOWLEDGED.value,
                message="Report requested by GUI",
                payload=payload
            )
            self.bus.emit("report.generate", payload)
            self.log("[OK] Routed report_requested to Mission Debrief")
        
        # Report export -> Mission Debrief + bus distribution
        elif message_type == "report_exported":
            self.communicator.send_signal(
                target_address="5",
                radio_code=RadioCode.ACKNOWLEDGED.value,
                message="Report exported by GUI",
                payload=payload
            )
            self.bus.emit("report.export", payload)
            self.log("[OK] Routed report_exported to Mission Debrief")
    
    # =========================================================================
    # SIGNAL HANDLERS (From Other Parent Modules)
    # =========================================================================
    
    def _on_evidence_classified(self, payload: Dict):
        """Evidence Locker classified evidence - update GUI"""
        evidence_id = payload.get("evidence_id")
        self.log(f"[SIGNAL] Evidence classified: {evidence_id}")
        
        self.update_state("last_evidence", payload)
        
        # Add to evidence pool
        with self.state_lock:
            self.app_state["evidence_pool"].append(payload)
    
    def _on_case_created(self, payload: Dict):
        """Evidence Locker created case - update GUI"""
        case_id = payload.get("case_id")
        self.log(f"[SIGNAL] Case created: {case_id}")
        
        self.update_state("active_case_id", case_id)
        self.update_state("active_case", payload)
    
    def _on_section_routed(self, payload: Dict):
        """Warden routed section for processing"""
        section_id = payload.get("section_id")
        self.log(f"[SIGNAL] Section routed: {section_id}")
    
    def _on_gateway_ready(self, payload: Dict):
        """Warden gateway ready"""
        self.log("[SIGNAL] Gateway ready")
    
    def _on_evidence_processed(self, payload: Dict):
        """Marshall processed evidence"""
        evidence_id = payload.get("evidence_id")
        self.log(f"[SIGNAL] Evidence processed: {evidence_id}")
    
    def _on_evidence_ready(self, payload: Dict):
        """Marshall evidence ready for debrief"""
        evidence_id = payload.get("evidence_id")
        self.log(f"[SIGNAL] Evidence ready for debrief: {evidence_id}")
    
    def _on_report_ready(self, payload: Dict):
        """Mission Debrief completed report"""
        report_id = payload.get("report_id")
        self.log(f"[SIGNAL] Report ready: {report_id}")
        
        # Emit completion radio code to UDS
        if self.communicator:
            self.communicator.send_signal(
                target_address="Bus-1",
                radio_code=RadioCode.EVIDENCE_COMPLETE.value,
                message="Report generation complete",
                payload={"report_id": report_id}
            )
    
    def _on_narrative_ready(self, payload: Dict):
        """Mission Debrief assembled narrative"""
        self.log("[SIGNAL] Narrative assembled")
    
    # =========================================================================
    # UDS INTEGRATION
    # =========================================================================
    
    def _on_health_check(self, payload: Dict):
        """UDS health check - respond immediately"""
        health = self._get_health_status()
        
        if self.communicator:
            self.communicator.send_signal(
                target_address="Bus-1.5",  # UDS
                radio_code=RadioCode.STATUS.value,
                message=f"GUI-1 health: {health['status']}",
                payload={
                    "module_address": self.module_address,
                    "status": health["status"],
                    "state": self.state.value,
                    "uptime": health["uptime"],
                    "components_active": health["components_active"],
                    "threads_alive": health["threads_alive"],
                    "operator": self.app_state.get("operator_name")
                }
            )
        
        self.log(f"[UDS] Health check response: {health['status']}")
    
    def _get_health_status(self) -> Dict:
        """Calculate comprehensive health status"""
        threads_alive = sum(1 for t in self.threads.values() if t and t.is_alive())
        components_active = len([c for c in self.components.values() if c.get("active", False)])
        
        # Determine status
        if not self.bus or not self.communicator:
            status = "SAFEMODE"
        elif self.state == GUIModuleState.FAULTED:
            status = "FAULTED"
        elif threads_alive < 1:  # At least heartbeat should be alive
            status = "DEGRADED"
        elif components_active == 0:
            status = "IDLE"
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
            try:
                self.communicator.send_sos_fault(fault_code, description)
            except Exception as e:
                self.log(f"[ERROR] Fault emission failed: {e}", "error")
        
        self.log(f"[FAULT {fault_code}] {description}", "error")
    
    # =========================================================================
    # STATE MANAGEMENT (Centralized, Thread-Safe)
    # =========================================================================
    
    def update_state(self, key: str, value: Any):
        """Thread-safe state update with notification"""
        with self.state_lock:
            old_value = self.app_state.get(key)
            self.app_state[key] = value
        
        logger.debug(f"[STATE] {key} updated: {old_value} -> {value}")
        
        # Notify GUI to refresh
        if self.gui_instance and hasattr(self.gui_instance, 'on_state_changed'):
            try:
                self.gui_instance.on_state_changed(key, value)
            except Exception as e:
                self.log(f"[WARN] GUI state notification error: {e}", "warning")
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """Thread-safe state retrieval"""
        with self.state_lock:
            return self.app_state.get(key, default)
    
    def get_all_state(self) -> Dict[str, Any]:
        """Get complete state snapshot"""
        with self.state_lock:
            return dict(self.app_state)
    
    # =========================================================================
    # THREAD MONITORING
    # =========================================================================
    
    def register_thread(self, name: str, thread: threading.Thread):
        """Register thread for monitoring"""
        with self.thread_lock:
            self.threads[name] = thread
        self.log(f"[THREAD] Registered: {name}")
    
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
    # DEDUPLICATION HELPERS
    # =========================================================================
    
    def create_dialog_window(self, parent, title: str, size: tuple = (400, 300)):
        """
        Standardized dialog window creation (DEDUPLICATION)
        
        Replaces duplicated window creation in:
        - LoginDialog
        - CaseCreationDialog
        - ProfileEditor
        """
        import tkinter as tk
        
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
    
    def create_form_frame(self, parent, title: str):
        """Standardized form frame creation (DEDUPLICATION)"""
        from tkinter import ttk
        
        frame = ttk.LabelFrame(parent, text=title, padding=12)
        frame.columnconfigure(1, weight=1)
        return frame
    
    def create_labeled_field(self, parent, row: int, label: str, var, **kwargs):
        """Standardized labeled entry field (DEDUPLICATION)"""
        import tkinter as tk
        from tkinter import ttk
        
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w")
        entry = ttk.Entry(parent, textvariable=var, **kwargs)
        entry.grid(row=row, column=1, sticky="ew", pady=(6, 0))
        return entry
    
    # =========================================================================
    # COMPONENT REGISTRATION
    # =========================================================================
    
    def register_component(self, component_id: str, component_data: Dict[str, Any]):
        """Register a GUI component for tracking"""
        self.components[component_id] = component_data
        
        with self.state_lock:
            self.app_state["components_loaded"] = len(self.components)
        
        self.log(f"[COMPONENT] Registered: {component_id}")
    
    # =========================================================================
    # ENHANCED GUI INTEGRATION
    # =========================================================================
    
    def set_gui_instance(self, gui_instance):
        """Set reference to EnhancedDKIGUI instance"""
        self.gui_instance = gui_instance
        
        # Extract operator info from GUI
        if hasattr(gui_instance, 'operator_name'):
            self.update_state("operator_name", gui_instance.operator_name)
        if hasattr(gui_instance, 'operator_profile'):
            role = getattr(gui_instance.operator_profile, 'role', 'basic')
            self.update_state("operator_role", role)
        
        self.log("[OK] GUI instance registered")


# =============================================================================
# MODULE INFO (for introspection)
# =============================================================================

__version__ = "1.0.0"
__author__ = "Central Command System"
__module_address__ = "GUI-1"
__module_type__ = "parent_module"

