#!/usr/bin/env python3
"""
MissionDebriefModule - high level wrapper for the Mission Debrief control plane.

This is a lightweight scaffold that keeps references to the Debrief Manager and
The Librarian (Narrative Assembler) while exposing a single module boundary for
packaging. This module owns the CANBUS connection and passes it to driven components.

The wrapper intentionally defers instantiation to init helpers so that today's
bootstrapping logic remains intact while providing a clean module interface.
"""

from __future__ import annotations

import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Any, Dict, List

try:
    # Re-use the existing communicator implementation when available.
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'Data Bus', 'Bus Core Design'))
    from universal_communicator import UniversalCommunicator  # type: ignore
except ImportError:  # pragma: no cover - path not available in some contexts
    UniversalCommunicator = None  # type: ignore

# Ensure bus_core is importable.
CURRENT_DIR = Path(__file__).resolve().parent
COMMAND_CENTER_ROOT = CURRENT_DIR.parent
DATA_BUS_ROOT = COMMAND_CENTER_ROOT / "Data Bus"
BUS_CORE_PATH = DATA_BUS_ROOT / "Bus Core Design"
if str(BUS_CORE_PATH) not in sys.path:
    sys.path.insert(0, str(BUS_CORE_PATH))

try:
    from bus_core import DKIReportBus  # type: ignore
except ImportError:  # pragma: no cover - defensive
    DKIReportBus = None  # type: ignore

from _init_debrief_manager import init_debrief_manager
from _init_the_librarian import init_the_librarian


class MissionDebriefModule:
    """Module wrapper around Debrief Manager and The Librarian."""

    MODULE_ADDRESS = "5"

    def __init__(
        self,
        *,
        bus: Optional[Any] = None,
        communicator: Optional[Any] = None,
        ecc: Optional[Any] = None,
        gateway: Optional[Any] = None,
    ) -> None:
        self.logger = logging.getLogger("MissionDebrief")
        self.communicator = communicator
        self.bus_connected = False
        self.safemode_active = False

        self.bus = self._resolve_bus(bus)
        
        # MODULE INITIALIZATION PROTOCOL - Wait for bus ready and module turn
        if self.bus:
            self.logger.info("[Mission Debrief] Waiting for bus stabilization...")
            if not self.bus.wait_for_ready(timeout=15.0):
                self.logger.error("[Mission Debrief] Bus stabilization timeout - initialization may be unstable")
                return
            
            self.logger.info("[Mission Debrief] Bus ready - waiting for module turn in sequence...")
            if not self.bus.wait_for_module_turn('5', timeout=30.0):
                self.logger.error("[Mission Debrief] Module turn timeout - cannot initialize")
                return

        # Instantiate The Librarian first (Debrief Manager depends on it)
        self.librarian = init_the_librarian(ecc=ecc, bus=self.bus)
        
        # Instantiate Debrief Manager
        self.debrief_manager = init_debrief_manager(
            ecc=ecc,
            bus=self.bus,
            gateway=gateway,
            librarian=self.librarian
        )

        # Mission state tracking
        self.mission_modules: Dict[str, Dict[str, Any]] = {
            'debrief_manager': {'status': 'active', 'last_activity': None, 'reports_processed': 0},
            'librarian': {'status': 'active', 'last_activity': None, 'narratives_assembled': 0}
        }
        self.report_queue: List[Dict[str, Any]] = []

        if self.bus:
            self._initialize_canbus(self.bus, communicator=self.communicator)
            
        # Self-validation of driven components
        self._validate_mission_debrief_components()

    # ------------------------------------------------------------------ #
    # Initialisation helpers
    # ------------------------------------------------------------------ #
    def _resolve_bus(self, initial_bus: Optional[Any]) -> Optional[Any]:
        """Return the active CAN bus connection, creating one when absent."""
        if initial_bus is not None:
            return initial_bus

        if not DKIReportBus:
            self.logger.warning("DKIReportBus unavailable; running Mission Debrief without dedicated bus.")
            return None

        try:
            self.logger.info("Initialised dedicated DKIReportBus for Mission Debrief.")
            return DKIReportBus()
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error("Failed to bootstrap DKIReportBus: %s", exc)
            return None

    def _initialize_canbus(self, bus: Any, *, communicator: Optional[Any] = None) -> None:
        """Set up CAN bus connectivity and register signal handlers."""
        self.bus = bus
        try:
            if communicator:
                self.communicator = communicator
            elif UniversalCommunicator:
                self.communicator = UniversalCommunicator(self.MODULE_ADDRESS, bus_connection=bus)
                self.logger.info("[3-1] UniversalCommunicator created")

            bus.register_system_address(self.MODULE_ADDRESS, {
                "system_type": "mission_debrief",
                "capabilities": ["narrative_assembly", "report_generation", "final_assembly"],
                "status": "active",
                "mode": "primary",
                "registered_at": datetime.now().isoformat()
            })
            self.logger.info("[3-1] Mission Debrief Module registered with CANBUS")

            self.bus_connected = True
            self.safemode_active = False

            self._register_signal_handlers()
            self._register_linbus_handlers()
            self.logger.info("[5] CANBUS CONNECTION ESTABLISHED")
            
            # MODULE INITIALIZATION PROTOCOL - Register with bus
            if self.bus.register_module_init('5', {
                'version': '1.0',
                'type': 'mission_debrief',
                'capabilities': ['narrative_assembly', 'report_generation', 'final_assembly']
            }):
                self.logger.info("[5] [OK] Module registered with bus (Address 5)")
            else:
                self.logger.warning("[5] Module registration failed - continuing anyway")
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.critical("[5] CANBUS connection failed: %s", exc)
            self.bus_connected = False
            self.safemode_active = True

    def _register_signal_handlers(self) -> None:
        """Register module signal handlers with the CAN bus."""
        if not (self.bus and self.bus_connected):
            self.logger.warning("[5] Cannot register signals - no CANBUS connection")
            return
        try:
            self.bus.register_signal("mission.status", self._handle_status_signal)
            self.bus.register_signal("mission.report", self._handle_report_signal)
            self.bus.register_signal("mission.shutdown", self._handle_shutdown_signal)
            self.bus.register_signal("mission.child.broadcast", self._handle_child_broadcast)
            
            # UDS Protocol Handlers (PHASE 2B FIX - complete bidirectional comm)
            self.bus.register_signal("diagnostic.rollcall", self._handle_rollcall)
            self.bus.register_signal("diagnostic.radio_check", self._handle_radio_check)
            self.bus.register_signal("auto_registration", self._handle_auto_registration)
            
            # DEESCALATION Agent: Universal communication handler for UDS diagnostics
            self.bus.register_signal("communication", self._handle_communication_signal)
            self.logger.info("[5] Mission Debrief signal handlers registered (including UDS bidirectional protocol)")
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error("[5] Failed to register signal handlers: %s", exc)
    
    def _register_linbus_handlers(self) -> None:
        """Register LINBUS signal handlers for workflow coordination."""
        if not self.bus:
            self.logger.warning("[5] Cannot register LINBUS handlers - no bus connection")
            return
        try:
            # Mission Debrief receives workflow coordination signals
            self.bus.register_signal("workflow.ready", self._handle_workflow_ready)
            self.bus.register_signal("workflow.complete", self._handle_workflow_complete)
            self.logger.info("[5] LINBUS workflow handlers registered")
        except Exception as exc:  # pragma: no cover
            self.logger.error("[5] Failed to register LINBUS handlers: %s", exc)
    
    def _handle_workflow_ready(self, payload: Optional[Dict[str, Any]] = None) -> None:
        """Handle LINBUS workflow ready signal."""
        self.logger.info("[5] Workflow ready signal received on LINBUS")
    
    def _handle_workflow_complete(self, payload: Optional[Dict[str, Any]] = None) -> None:
        """Handle LINBUS workflow complete signal."""
        self.logger.info("[5] Workflow complete signal received on LINBUS")
    
    def _handle_communication_signal(self, payload: Dict[str, Any]) -> None:
        """
        DEESCALATION Agent: Universal communication signal handler.
        Responds to UDS diagnostic signals (ROLLCALL, STATUS, RADIO_CHECK).
        Per MASTER_DIAGNOSTIC_PROTOCOL lines 201-216.
        """
        if not payload:
            return
        
        radio_code = payload.get('radio_code', '')
        caller_address = payload.get('caller_address', 'UNKNOWN')
        signal_id = payload.get('signal_id', '')
        
        self.logger.info(f"[5] Communication signal received from {caller_address}: {radio_code}")
        
        # Build response payload
        response = {
            'responder_address': '5',
            'responder_name': 'Mission_Debrief',
            'signal_id': signal_id,
            'timestamp': datetime.now().isoformat()
        }
        
        if radio_code == 'ROLLCALL':
            # Report operational status
            debrief_ok = self.debrief_manager is not None
            librarian_ok = self.librarian is not None
            
            response['status'] = '10-4' if (debrief_ok and librarian_ok) else '10-7'
            response['subsystems'] = {
                'debrief_manager': 'operational' if debrief_ok else 'failed',
                'librarian': 'operational' if librarian_ok else 'failed',
                'report_queue': len(self.report_queue)
            }
            self.logger.info(f"[5] ROLLCALL response sent - Debrief: {debrief_ok}, Librarian: {librarian_ok}")
            
        elif radio_code in ['STATUS', 'RADIO_CHECK']:
            response['status'] = '10-4'  # Available
            self.logger.info(f"[5] {radio_code} acknowledged")
        
        # Transmit response on CANBUS
        if self.bus and hasattr(self.bus, 'emit'):
            self.bus.emit('diagnostic_response', response)
    
    def _handle_rollcall(self, payload: Dict[str, Any]) -> None:
        """Handle UDS rollcall request (PHASE 2B FIX)
        
        Respond with current status and compliance information.
        """
        self.logger.info("[5] Rollcall request received from UDS")
        
        if not self.communicator:
            self.logger.warning("[5] Cannot respond - no communicator available")
            return
        
        # Build rollcall response
        status_data = {
            "system_address": self.MODULE_ADDRESS,
            "system_name": "Mission Debrief Assembly",
            "status": "OPERATIONAL" if (self.debrief_manager and self.librarian) else "INITIALIZING",
            "active_children": 2,  # Debrief Manager (5-1), The Librarian (5-2)
            "compliance_status": "COMPLIANT",
            "timestamp": datetime.now().isoformat()
        }
        
        # Send rollcall response on correct topic
        try:
            self.communicator.send_rollcall_response("DIAG-1", status_data)
            self.logger.info("[5] Rollcall response sent to UDS")
        except Exception as exc:
            self.logger.error("[5] Rollcall response failed: %s", exc)
    
    def _handle_radio_check(self, payload: Dict[str, Any]) -> None:
        """Handle UDS radio check request (PHASE 2B FIX)
        
        Respond with connectivity and communication health data.
        
        LIFECYCLE FIX: Only responds to CALL_SENT messages.
        """
        # Check message lifecycle state
        message_state = payload.get('message_state', '')
        if message_state != "CALL_SENT":
            return
        
        self.logger.info("[5] Radio check request received from UDS")
        
        if not self.communicator:
            self.logger.warning("[5] Cannot respond - no communicator available")
            return
        
        # Build radio check response
        connectivity_data = {
            "system_address": self.MODULE_ADDRESS,
            "latency_ms": 0,  # Real-time response
            "signal_strength": "STRONG",
            "bus_connected": self.bus_connected,
            "communicator_active": True,
            "timestamp": datetime.now().isoformat()
        }
        
        # Send radio check response on correct topic
        try:
            self.communicator.send_radio_check_response("DIAG-1", connectivity_data)
            self.logger.info("[5] Radio check response sent to UDS")
        except Exception as exc:
            self.logger.error("[5] Radio check response failed: %s", exc)
    
    def _handle_auto_registration(self, payload: Dict[str, Any]) -> None:
        """
        Handle UDS auto-registration demand.
        Respond with module capabilities and status per diagnostic protocol.
        
        LIFECYCLE FIX: Only responds to CALL_SENT messages to prevent infinite loops.
        """
        # Check message lifecycle state - only respond to requests
        message_state = payload.get('message_state', '')
        if message_state != "CALL_SENT":
            # Ignore responses, only process requests
            return
        
        self.logger.info("[5] Auto-registration request received from UDS")
        
        if not self.communicator:
            self.logger.warning("[5] Cannot respond - no communicator available")
            return
        
        # Build registration response payload
        response_payload = {
            "system_address": self.MODULE_ADDRESS,
            "system_type": "mission_debrief",
            "status": "OPERATIONAL" if (self.debrief_manager and self.librarian) else "INITIALIZING",
            "capabilities": ["narrative_assembly", "report_generation", "final_assembly"],
            "child_components": ["5-1", "5-2"],
            "compliance_status": "COMPLIANT",
            "protocol_version": "1.0.0",
            "timestamp": datetime.now().isoformat()
        }
        
        # Send registration response to UDS (PHASE 2B FIX - use correct topic)
        try:
            self.communicator.send_auto_registration_response("DIAG-1", response_payload)
            self.logger.info("[5] Auto-registration response sent to UDS")
        except Exception as exc:
            self.logger.error("[5] Auto-registration response failed: %s", exc)

    # ------------------------------------------------------------------ #
    # Signal handlers
    # ------------------------------------------------------------------ #
    def _handle_status_signal(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle mission.status signal."""
        return self.get_status()

    def _handle_report_signal(self, payload: Dict[str, Any]) -> None:
        """Handle mission.report signal."""
        report_id = payload.get('report_id', 'unknown')
        self.report_queue.append({
            'report_id': report_id,
            'payload': payload,
            'timestamp': datetime.now().isoformat(),
            'status': 'queued'
        })
        self.logger.info(f"Report {report_id} queued for processing")

    def _handle_shutdown_signal(self, payload: Optional[Dict[str, Any]] = None) -> None:
        """Handle mission.shutdown signal."""
        self.stop()
    
    def _handle_child_broadcast(self, payload: Dict[str, Any]) -> None:
        """Translate child broadcasts to specific CANBUS signals and radio codes."""
        self.logger.debug("Mission Debrief child broadcast received: %s", payload)
        
        if not self.bus or not hasattr(self.bus, 'emit'):
            return
        
        message_type = payload.get('message_type')
        
        # Translate internal broadcasts to specific CANBUS signals
        try:
            if message_type == 'report_assembled':
                # Emit radio code 10-8 (Section Complete)
                if self.communicator:
                    self.communicator.send_signal(
                        target_address="Bus-1",
                        radio_code="10-8",
                        message="Report assembly complete"
                    )
                # Report assembly complete
                self.bus.emit('mission.report.assembled', {
                    'report_id': payload.get('report_id'),
                    'case_id': payload.get('case_id'),
                    'sections_count': payload.get('sections_count'),
                    'evidence_count': payload.get('evidence_count'),
                    'source': self.MODULE_ADDRESS,
                    'timestamp': datetime.now().isoformat()
                })
                self.logger.info("[%s] Translated report_assembled to mission.report.assembled", self.MODULE_ADDRESS)
            
            elif message_type == 'narrative_assembled':
                # Narrative assembly complete
                self.bus.emit('narrative.assembled', {
                    'narrative_id': payload.get('narrative_id'),
                    'case_id': payload.get('case_id'),
                    'narrative_length': payload.get('narrative_length'),
                    'source': self.MODULE_ADDRESS,
                    'timestamp': datetime.now().isoformat()
                })
                self.logger.info("[%s] Translated narrative_assembled to narrative.assembled", self.MODULE_ADDRESS)
            
            elif message_type == 'artifacts_generated':
                # Artifacts (Cover Page, TOC, Disclosure) generated
                self.bus.emit('artifacts.generated', {
                    'case_id': payload.get('case_id'),
                    'artifacts': payload.get('artifacts', []),
                    'artifact_count': payload.get('artifact_count'),
                    'source': self.MODULE_ADDRESS,
                    'timestamp': datetime.now().isoformat()
                })
                self.logger.info("[%s] Translated artifacts_generated to artifacts.generated", self.MODULE_ADDRESS)
            
            elif message_type == 'final_report_ready':
                # Final report ready for delivery
                self.bus.emit('report.ready', {
                    'report_id': payload.get('report_id'),
                    'case_id': payload.get('case_id'),
                    'file_path': payload.get('file_path'),
                    'source': self.MODULE_ADDRESS,
                    'timestamp': datetime.now().isoformat()
                })
                self.logger.info("[%s] Translated final_report_ready to report.ready", self.MODULE_ADDRESS)
        
        except Exception as exc:
            self.logger.warning("[%s] Signal translation failed: %s", self.MODULE_ADDRESS, exc)

    # ------------------------------------------------------------------ #
    # Operational helpers
    # ------------------------------------------------------------------ #
    def get_status(self) -> Dict[str, Any]:
        """Compile Mission Debrief status for monitoring."""
        try:
            status = {
                'mission_modules': self.mission_modules,
                'report_queue_length': len(self.report_queue),
                'total_reports_processed': sum(m['reports_processed'] for m in self.mission_modules.values()),
                'debrief_status': self.debrief_manager.get_status() if hasattr(self.debrief_manager, 'get_status') else {},
                'librarian_status': {'active': True, 'bootstrap_time': self.librarian.bootstrap_time} if hasattr(self.librarian, 'bootstrap_time') else {},
                'timestamp': datetime.now().isoformat(),
                'canbus_status': {
                    'connected': self.bus_connected,
                    'safemode': self.safemode_active,
                    'address': self.MODULE_ADDRESS
                }
            }
            return status
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error("Failed to get Mission Debrief status: %s", exc)
            return {}

    # ------------------------------------------------------------------ #
    # Self-Test Protocol (UDS Compliance)
    # ------------------------------------------------------------------ #
    def _run_startup_self_test(self) -> bool:
        """
        Validate all child components per UDS self-test protocol.
        Emit fault codes for failed children to Bus-1.
        
        Returns True if all children operational, False if any failed.
        """
        self.logger.info("[%s] Running mandatory startup self-test per UDS protocol", self.MODULE_ADDRESS)
        operational = True
        
        # Define child components to validate per system_registry.json
        children_to_validate = [
            ('5-1', 'Debrief Manager', lambda: self.debrief_manager),
            ('5-2', 'Librarian', lambda: self.librarian),
        ]
        
        for child_addr, child_name, get_child_ref in children_to_validate:
            try:
                child_ref = get_child_ref()
                
                if child_ref is None:
                    # Child component failed to initialize - emit fault code
                    self.logger.error(
                        "[%s] Self-test FAILED: %s (%s) not initialized - emitting fault code",
                        self.MODULE_ADDRESS, child_name, child_addr
                    )
                    
                    # Emit fault code to UDS per protocol requirements
                    if self.communicator:
                        self.communicator.send_signal(
                            target_address="DIAG-1",
                            radio_code="SOS",
                            message=f"{child_name} initialization failed",
                            payload={
                                "fault_code": f"[{child_addr}-12-INIT]",
                                "description": f"{child_name} not initialized - missing dependency or initialization failure",
                                "component": child_name,
                                "reporting_address": child_addr,
                                "parent_address": self.MODULE_ADDRESS,
                                "severity": "CRITICAL",
                                "timestamp": datetime.now().isoformat(),
                                "fault_type": "12",
                                "fault_type_description": "Missing initialization dependency"
                            }
                        )
                        self.logger.warning(
                            "[%s] Fault code emitted: [%s-12-INIT] - %s",
                            self.MODULE_ADDRESS, child_addr, child_name
                        )
                    else:
                        self.logger.error(
                            "[%s] Cannot emit fault code - UniversalCommunicator not available",
                            self.MODULE_ADDRESS
                        )
                    
                    operational = False
                else:
                    # Child component validated successfully
                    self.logger.info(
                        "[%s] Self-test PASSED: %s (%s) operational",
                        self.MODULE_ADDRESS, child_name, child_addr
                    )
                    
            except Exception as exc:
                # Unexpected error during validation
                self.logger.error(
                    "[%s] Self-test ERROR: Failed to validate %s (%s): %s",
                    self.MODULE_ADDRESS, child_name, child_addr, exc
                )
                operational = False
        
        if operational:
            self.logger.info("[%s] PASS - Self-test COMPLETE - All child components operational", self.MODULE_ADDRESS)
        else:
            self.logger.warning("[%s] FAIL - Self-test COMPLETE - One or more child components FAILED", self.MODULE_ADDRESS)
        
        # Send self-test complete signal to UDS
        if self.communicator:
            try:
                self.communicator.send_signal(
                    target_address="DIAG-1",
                    radio_code="10-4",
                    message=f"{self.MODULE_ADDRESS} self-test complete",
                    payload={
                        "operation": "self_test_complete",
                        "system_address": self.MODULE_ADDRESS,
                        "system_name": "Mission Debrief Module",
                        "test_result": "PASS" if operational else "FAIL",
                        "children_tested": 2,  # Debrief Manager + Librarian
                        "timestamp": datetime.now().isoformat()
                    }
                )
                self.logger.info("[%s] Self-test completion signal sent to UDS", self.MODULE_ADDRESS)
            except Exception as exc:
                self.logger.error("[%s] Failed to send self-test completion signal: %s", self.MODULE_ADDRESS, exc)
        
        return operational
    
    def _validate_mission_debrief_components(self) -> bool:
        """
        DEPRECATED: Legacy validation method - replaced by _run_startup_self_test().
        Kept for backward compatibility.
        """
        return self._run_startup_self_test()
    
    def force_component_validation(self) -> bool:
        """Force re-validation of Mission Debrief components."""
        return self._run_startup_self_test()

    # ------------------------------------------------------------------ #
    # Lifecycle hooks
    # ------------------------------------------------------------------ #
    def start(self) -> bool:
        """Lifecycle start."""
        self.logger.info("Starting Mission Debrief orchestration")
        return True

    def stop(self) -> bool:
        """Lifecycle stop."""
        self.logger.info("Stopping Mission Debrief orchestration")
        return True

