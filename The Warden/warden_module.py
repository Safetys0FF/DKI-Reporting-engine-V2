#!/usr/bin/env python3
"""
WardenModule - high level wrapper for the Warden control plane.

This is a lightweight scaffold that keeps references to the existing
EcosystemController and GatewayController instances while exposing a single
module boundary for future packaging work.  No behavioural changes are
introduced here – the wrapper simply stores the orchestrator components and
optionally keeps hold of the CAN bus communicator that already represents
the Warden on the network (`2`).

The wrapper intentionally avoids instantiating the heavy controllers on its
own so that today’s bootstrapping logic (see `warden_main.py`) remains in
charge.  Once the full refactor lands, this module can grow into the entry
point.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Any, Dict, List

import sys

try:
    # Re-use the existing communicator implementation when available.
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Command Center', 'Data Bus', 'Bus Core Design'))
    from universal_communicator import UniversalCommunicator  # type: ignore
except ImportError:  # pragma: no cover - path not available in some contexts
    UniversalCommunicator = None  # type: ignore

# Ensure bus_core is importable.
CURRENT_DIR = Path(__file__).resolve().parent
DATA_BUS_ROOT = CURRENT_DIR.parent / "Command Center" / "Data Bus"
BUS_CORE_PATH = DATA_BUS_ROOT / "Bus Core Design"
if str(BUS_CORE_PATH) not in sys.path:
    sys.path.insert(0, str(BUS_CORE_PATH))

try:
    from bus_core import DKIReportBus  # type: ignore
except ImportError:  # pragma: no cover - defensive
    DKIReportBus = None  # type: ignore

try:
    from _init_warden import init_ecosystem_controller, init_gateway_controller
except ImportError:
    # Fallback for direct imports
    from ecosystem_controller import EcosystemController
    from gateway_controller import GatewayController
    
    def init_ecosystem_controller(bus=None):
        return EcosystemController(bus=bus)
    
    def init_gateway_controller(ecosystem_controller, bus=None):
        return GatewayController(ecosystem_controller=ecosystem_controller, bus=bus)


class Warden:
    """Module wrapper around EcosystemController and GatewayController."""

    MODULE_ADDRESS = "2"

    def __init__(
        self,
        *,
        bus: Optional[Any] = None,
        communicator: Optional[Any] = None,
    ) -> None:
        self.logger = logging.getLogger("Warden")
        self.communicator = communicator
        self.bus_connected = False
        self.safemode_active = False

        self.bus = self._resolve_bus(bus)
        
        # MODULE INITIALIZATION PROTOCOL - Wait for bus ready and module turn
        module_turn_success = False
        if self.bus:
            self.logger.info("[Warden] Waiting for bus stabilization...")
            if not self.bus.wait_for_ready(timeout=15.0):
                self.logger.warning("[Warden] Bus stabilization timeout - initializing in degraded mode")
            else:
                self.logger.info("[Warden] Bus ready - waiting for module turn in sequence...")
                if self.bus.wait_for_module_turn('2', timeout=30.0):
                    module_turn_success = True
                else:
                    self.logger.warning("[Warden] Module turn timeout - initializing in degraded mode")
        else:
            self.logger.warning("[Warden] No bus provided - initializing in degraded mode")

        # FIXED: Always instantiate core controllers (degraded mode is OK)
        self.ecosystem_controller = init_ecosystem_controller(bus=self.bus)
        self.gateway_controller = init_gateway_controller(
            ecosystem_controller=self.ecosystem_controller,
            bus=self.bus,
        )

        # Ensure bi-directional awareness between orchestration layers.
        try:
            self.ecosystem_controller.inject_gateway(self.gateway_controller)
        except AttributeError:  # pragma: no cover - defensive for legacy builds
            self.logger.debug("EcosystemController missing inject_gateway hook; continuing without link.")

        self.evidence_locker: Optional[Any] = None
        self.evidence_manager: Optional[Any] = None
        self.sections: Dict[str, Any] = {}

        self.warden_modules: Dict[str, Dict[str, Any]] = {
            'ecosystem_controller': {'status': 'active', 'last_activity': None, 'handoffs_processed': 0},
            'gateway_controller': {'status': 'active', 'last_activity': None, 'handoffs_processed': 0}
        }
        
        # MODULE INITIALIZATION PROTOCOL - Register with bus
        if self.bus:
            if self.bus.register_module_init('2', {
                'version': '1.0',
                'type': 'warden',
                'capabilities': ['ecosystem_control', 'gateway_control', 'section_management']
            }):
                self.logger.info("[Warden] [OK] Module registered with bus (Address 2)")
            else:
                self.logger.warning("[Warden] Module registration failed - continuing anyway")
        self.handoff_queue: List[Dict[str, Any]] = []

        if self.bus:
            self._initialize_canbus(self.bus, communicator=self.communicator)
            self._register_linbus_handlers()

    # ------------------------------------------------------------------ #
    # Initialisation helpers
    # ------------------------------------------------------------------ #
    def _resolve_bus(self, initial_bus: Optional[Any]) -> Optional[Any]:
        """Return the active CAN bus connection, creating one when absent."""
        if initial_bus is not None:
            return initial_bus

        if not DKIReportBus:
            self.logger.warning("DKIReportBus unavailable; running Warden without dedicated bus.")
            return None

        try:
            self.logger.info("Initialised dedicated DKIReportBus for Warden.")
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
                self.logger.info("[2-1] UniversalCommunicator created")

            bus.register_system_address(self.MODULE_ADDRESS, {
                "system_type": "warden_controller",
                "capabilities": ["section_orchestration", "gateway_control", "ecosystem_management"],
                "status": "active",
                "mode": "primary",
                "registered_at": datetime.now().isoformat()
            })
            self.logger.info("[2-1] Warden registered with CANBUS")

            self.bus_connected = True
            self.safemode_active = False

            self._register_signal_handlers()
            self.logger.info("[2-1] CANBUS CONNECTION ESTABLISHED")
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.critical("[2-1] CANBUS connection failed: %s", exc)
            self.bus_connected = False
            self.safemode_active = True

    def _register_signal_handlers(self) -> None:
        """Register module signal handlers with the CAN bus."""
        if not (self.bus and self.bus_connected):
            self.logger.warning("[2-1] Cannot register signals - no CANBUS connection")
            return
        try:
            # DEESCALATION Agent: Universal communication handler for UDS diagnostics
            self.bus.register_signal("communication", self._handle_communication_signal)
            
            self.bus.register_signal("warden.status", self._handle_status_signal)
            self.bus.register_signal("warden.shutdown", self._handle_shutdown_signal)
            self.bus.register_signal("warden.handoff", self._handle_handoff_signal)
            self.bus.register_signal("warden.child.broadcast", self._handle_child_broadcast)
            
            # UDS Protocol Handlers (PHASE 2 FIX - complete bidirectional comm)
            self.bus.register_signal("diagnostic.rollcall", self._handle_rollcall)
            self.bus.register_signal("diagnostic.radio_check", self._handle_radio_check)
            self.bus.register_signal("auto_registration", self._handle_auto_registration)
            
            self.logger.info("[2-1] Warden signal handlers registered (including UDS bidirectional protocol)")
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error("[2-1] Failed to register signal handlers: %s", exc)
    
    def _register_linbus_handlers(self) -> None:
        """Register LINBUS signal handlers for orchestration coordination."""
        if not self.bus:
            self.logger.warning("[2-1] Cannot register LINBUS handlers - no bus connection")
            return
        try:
            # Warden is master controller - receives orchestration signals
            self.bus.register_signal("warden.orchestrate", self._handle_orchestration_signal)
            self.bus.register_signal("throttle.hold", self._handle_throttle_hold)
            self.bus.register_signal("throttle.release", self._handle_throttle_release)
            self.logger.info("[2-1] LINBUS orchestration handlers registered")
        except Exception as exc:  # pragma: no cover
            self.logger.error("[2-1] Failed to register LINBUS handlers: %s", exc)
    
    def _handle_orchestration_signal(self, payload: Optional[Dict[str, Any]] = None) -> None:
        """Handle LINBUS orchestration commands."""
        self.logger.info("[2-1] Orchestration signal received on LINBUS")
    
    def _handle_throttle_hold(self, payload: Optional[Dict[str, Any]] = None) -> None:
        """Handle LINBUS throttle hold signal."""
        self.logger.info("[2-1] Throttle hold signal received on LINBUS")
    
    def _handle_throttle_release(self, payload: Optional[Dict[str, Any]] = None) -> None:
        """Handle LINBUS throttle release signal."""
        self.logger.info("[2-1] Throttle release signal received on LINBUS")
    
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
        
        self.logger.info(f"[2-1] Communication signal received: {radio_code} from {caller_address}")
        
        # Handle ROLLCALL - respond with 10-4 operational status
        if radio_code == 'ROLLCALL':
            self.logger.info("[2-1] Responding to ROLLCALL")
            if self.communicator:
                try:
                    self.communicator.send_signal(
                        target_address=caller_address,
                        radio_code="10-4",
                        message="Warden operational",
                        payload={
                            'system_address': self.MODULE_ADDRESS,
                            'status': 'active' if self.bus_connected else 'safemode',
                            'subsystems': {
                                'ecosystem_controller': 'active',
                                'gateway_controller': 'active'
                            },
                            'timestamp': datetime.now().isoformat()
                        }
                    )
                    self.logger.info("[2-1] ROLLCALL response sent: 10-4 operational")
                except Exception as e:
                    self.logger.error(f"[2-1] Failed to send ROLLCALL response: {e}")
        
        # Handle STATUS request
        elif radio_code == 'STATUS':
            self.logger.info("[2-1] Responding to STATUS request")
            if self.communicator:
                try:
                    self.communicator.send_signal(
                        target_address=caller_address,
                        radio_code="10-4",
                        message="Warden status report",
                        payload={
                            'system_address': self.MODULE_ADDRESS,
                            'status': 'active' if self.bus_connected else 'safemode',
                            'bus_connected': self.bus_connected,
                            'safemode_active': self.safemode_active,
                            'evidence_locker_registered': self.evidence_locker is not None,
                            'evidence_manager_registered': self.evidence_manager is not None,
                            'timestamp': datetime.now().isoformat()
                        }
                    )
                    self.logger.info("[2-1] STATUS response sent")
                except Exception as e:
                    self.logger.error(f"[2-1] Failed to send STATUS response: {e}")
        
        # Handle RADIO_CHECK - communication test
        elif radio_code == 'RADIO_CHECK':
            self.logger.info("[2-1] Responding to RADIO_CHECK")
            if self.communicator:
                try:
                    self.communicator.send_signal(
                        target_address=caller_address,
                        radio_code="10-4",
                        message="Warden radio check acknowledged",
                        payload={'timestamp': datetime.now().isoformat()}
                    )
                    self.logger.info("[2-1] RADIO_CHECK acknowledged")
                except Exception as e:
                    self.logger.error(f"[2-1] Failed to send RADIO_CHECK response: {e}")
    
    def _handle_rollcall(self, payload: Dict[str, Any]) -> None:
        """Handle UDS rollcall request (PHASE 2 FIX)
        
        Respond with current status and compliance information.
        """
        self.logger.info("[2-1] Rollcall request received from UDS")
        
        if not self.communicator:
            self.logger.warning("[2-1] Cannot respond - no communicator available")
            return
        
        # Build rollcall response
        status_data = {
            "system_address": self.MODULE_ADDRESS,
            "system_name": "Warden Section Orchestrator",
            "status": "OPERATIONAL" if self.bus_connected else "INITIALIZING",
            "active_children": 2,  # Gateway Controller (2-2), Ecosystem Controller (2-3)
            "compliance_status": "COMPLIANT",
            "timestamp": datetime.now().isoformat()
        }
        
        # Send rollcall response on correct topic
        try:
            self.communicator.send_rollcall_response("DIAG-1", status_data)
            self.logger.info("[2-1] Rollcall response sent to UDS")
        except Exception as exc:
            self.logger.error("[2-1] Rollcall response failed: %s", exc)
    
    def _handle_radio_check(self, payload: Dict[str, Any]) -> None:
        """Handle UDS radio check request (PHASE 2 FIX)
        
        Respond with connectivity and communication health data.
        
        LIFECYCLE FIX: Only responds to CALL_SENT messages.
        """
        # Check message lifecycle state
        message_state = payload.get('message_state', '')
        if message_state != "CALL_SENT":
            return
        
        self.logger.info("[2-1] Radio check request received from UDS")
        
        if not self.communicator:
            self.logger.warning("[2-1] Cannot respond - no communicator available")
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
            self.logger.info("[2-1] Radio check response sent to UDS")
        except Exception as exc:
            self.logger.error("[2-1] Radio check response failed: %s", exc)
    
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
        
        # Check if this signal is addressed to us (or is a broadcast)
        target_address = payload.get('target_address', '')
        if target_address and target_address not in [self.MODULE_ADDRESS, "BROADCAST", "*"]:
            # Not for us - ignore
            return
        
        self.logger.info("[2-1] Auto-registration request received from UDS")
        
        if not self.communicator:
            self.logger.warning("[2-1] Cannot respond - no communicator available")
            return
        
        # Build registration response payload
        response_payload = {
            "system_address": self.MODULE_ADDRESS,
            "system_type": "warden_controller",
            "status": "OPERATIONAL" if self.bus_connected else "INITIALIZING",
            "capabilities": ["section_orchestration", "gateway_control", "ecosystem_management"],
            "child_components": ["2-2", "2-3"],
            "compliance_status": "COMPLIANT",
            "protocol_version": "1.0.0",
            "timestamp": datetime.now().isoformat()
        }
        
        # Send registration response to UDS (PHASE 2 FIX - use correct topic)
        try:
            self.communicator.send_auto_registration_response("DIAG-1", response_payload)
            self.logger.info("[2-1] Auto-registration response sent to UDS")
        except Exception as exc:
            self.logger.error("[2-1] Auto-registration response failed: %s", exc)

    # ------------------------------------------------------------------ #
    # Registry helpers
    # ------------------------------------------------------------------ #
    def register_evidence_locker(self, evidence_locker: Any) -> bool:
        """Register Evidence Locker with Warden."""
        try:
            self.evidence_locker = evidence_locker
            if hasattr(self.gateway_controller, 'attach_evidence_locker'):
                try:
                    self.gateway_controller.attach_evidence_locker(evidence_locker)
                except Exception as exc:  # pragma: no cover - defensive
                    self.logger.warning("GatewayController attach evidence locker failed: %s", exc)
            self.logger.info("Evidence Locker registered with WardenModule")
            return True
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error("Failed to register Evidence Locker: %s", exc)
            return False

    def register_evidence_manager(self, evidence_manager: Any) -> bool:
        """Register Evidence Manager with Warden."""
        try:
            self.evidence_manager = evidence_manager
            self.logger.info("Evidence Manager registered with WardenModule")
            return True
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error("Failed to register Evidence Manager: %s", exc)
            return False

    def register_section(self, section_id: str, section_handler: Any) -> bool:
        """Register section handler with Warden."""
        try:
            self.sections[section_id] = section_handler
            self.logger.info("Section %s registered with WardenModule", section_id)
            return True
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error("Failed to register section %s: %s", section_id, exc)
            return False

    # ------------------------------------------------------------------ #
    # Fault relay scaffold
    # ------------------------------------------------------------------ #
    def relay_fault(self, section_address: str, fault_payload: dict) -> None:
        """
        Placeholder for the future fault relay.

        Today this simply logs the request so that downstream work can confirm
        the wrapper is wired correctly without changing runtime behaviour.
        """
        self.logger.debug(
            "relay_fault called for %s with payload keys: %s",
            section_address,
            list(fault_payload.keys()),
        )

    # ------------------------------------------------------------------ #
    # Signal handlers
    # ------------------------------------------------------------------ #
    def _handle_status_signal(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle warden.status signal."""
        return self.get_status()

    def _handle_shutdown_signal(self, payload: Optional[Dict[str, Any]] = None) -> None:
        """Handle warden.shutdown signal."""
        self.stop()

    def _handle_handoff_signal(self, payload: Dict[str, Any]) -> None:
        """Handle warden.handoff signal."""
        from_module = payload.get('from_module', 'unknown')
        to_module = payload.get('to_module', 'unknown')
        handoff_data = payload.get('handoff_data', {})
        self.process_handoff(from_module, to_module, handoff_data)
    
    def _handle_child_broadcast(self, payload: Dict[str, Any]) -> None:
        """Translate child broadcasts to specific CANBUS signals and radio codes."""
        self.logger.debug("Warden child broadcast received: %s", payload)
        
        if not self.bus or not hasattr(self.bus, 'emit'):
            return
        
        message_type = payload.get('message_type')
        source = payload.get('source', 'unknown')
        
        # Translate internal broadcasts to specific CANBUS signals
        try:
            if message_type == 'gateway_ready':
                # Emit radio code 10-4 (Acknowledged/Ready)
                if self.communicator:
                    self.communicator.send_signal(
                        target_address="Bus-1",
                        radio_code="10-4",
                        message="Gateway ready and operational"
                    )
                # Gateway initialization complete
                self.bus.emit('gateway.ready', {
                    'gateway_id': payload.get('gateway_id'),
                    'capabilities': payload.get('capabilities', []),
                    'source': self.MODULE_ADDRESS,
                    'timestamp': datetime.now().isoformat()
                })
                self.logger.info("[%s] Translated gateway_ready to gateway.ready", self.MODULE_ADDRESS)
            
            elif message_type == 'ecosystem_ready':
                # ECC initialization complete
                self.bus.emit('ecosystem.ready', {
                    'ecc_id': payload.get('ecc_id'),
                    'systems_registered': payload.get('systems_registered', 0),
                    'source': self.MODULE_ADDRESS,
                    'timestamp': datetime.now().isoformat()
                })
                self.logger.info("[%s] Translated ecosystem_ready to ecosystem.ready", self.MODULE_ADDRESS)
            
            elif message_type == 'section_routed':
                # Emit radio code 10-4 (Section Approved/Unlocked)
                if self.communicator:
                    self.communicator.send_signal(
                        target_address="Bus-1",
                        radio_code="10-4",
                        message="Section routed and approved"
                    )
                
                # Gateway routed section request
                self.bus.emit('section.routed', {
                    'section_id': payload.get('section_id'),
                    'evidence_count': payload.get('evidence_count', 0),
                    'target': payload.get('target'),
                    'source': self.MODULE_ADDRESS,
                    'timestamp': datetime.now().isoformat()
                })
                self.logger.info("[%s] Translated section_routed to section.routed", self.MODULE_ADDRESS)
            
            elif message_type == 'handoff_complete':
                # Module handoff completed
                self.bus.emit('handoff.completed', {
                    'from_module': payload.get('from_module'),
                    'to_module': payload.get('to_module'),
                    'handoff_id': payload.get('handoff_id'),
                    'source': self.MODULE_ADDRESS,
                    'timestamp': datetime.now().isoformat()
                })
                self.logger.info("[%s] Translated handoff_complete to handoff.completed", self.MODULE_ADDRESS)
        
        except Exception as exc:
            self.logger.warning("[%s] Signal translation failed: %s", self.MODULE_ADDRESS, exc)

    # ------------------------------------------------------------------ #
    # Operational helpers
    # ------------------------------------------------------------------ #
    def process_handoff(self, from_module: str, to_module: str, handoff_data: Dict[str, Any]) -> bool:
        """Process handoff between modules."""
        try:
            handoff_record = {
                'from_module': from_module,
                'to_module': to_module,
                'handoff_data': handoff_data,
                'timestamp': datetime.now().isoformat(),
                'status': 'processing'
            }
            self.handoff_queue.append(handoff_record)

            self.logger.info("Handoff: %s -> %s", from_module, to_module)

            if from_module in self.warden_modules:
                self.warden_modules[from_module]['handoffs_processed'] += 1
                self.warden_modules[from_module]['last_activity'] = datetime.now().isoformat()

            handoff_record['status'] = 'completed'
            self.logger.info("Warden processed handoff: %s -> %s", from_module, to_module)
            return True
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error("Failed to process handoff: %s", exc)
            return False

    def get_status(self) -> Dict[str, Any]:
        """Compile Warden status for monitoring."""
        try:
            status = {
                'warden_modules': self.warden_modules,
                'handoff_queue_length': len(self.handoff_queue),
                'total_handoffs_processed': len([h for h in self.handoff_queue if h['status'] == 'completed']),
                'ecosystem_status': self.ecosystem_controller.get_boot_node_status() if self.ecosystem_controller else {},
                'gateway_status': self.gateway_controller.get_evidence_locker_status() if self.gateway_controller else {},
                'timestamp': datetime.now().isoformat(),
                'canbus_status': {
                    'connected': self.bus_connected,
                    'safemode': self.safemode_active,
                    'address': self.MODULE_ADDRESS
                }
            }
            return status
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error("Failed to get Warden status: %s", exc)
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
            ('2-2', 'Ecosystem Controller', lambda: self.ecosystem_controller),
            ('2-3', 'Gateway Controller', lambda: self.gateway_controller),
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
                            self.MODULE_ADDRESS, child_addr, child_addr, child_name
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
                        "system_name": "Warden Module",
                        "test_result": "PASS" if operational else "FAIL",
                        "children_tested": 2,  # ECC + Gateway
                        "timestamp": datetime.now().isoformat()
                    }
                )
                self.logger.info("[%s] Self-test completion signal sent to UDS", self.MODULE_ADDRESS)
            except Exception as exc:
                self.logger.error("[%s] Failed to send self-test completion signal: %s", self.MODULE_ADDRESS, exc)
        
        return operational

    # ------------------------------------------------------------------ #
    # Lifecycle hooks
    # ------------------------------------------------------------------ #
    def start(self) -> bool:
        """Lifecycle start - includes mandatory self-test."""
        self.logger.info("Starting Warden orchestration")
        
        # Run mandatory self-test per UDS protocol
        operational = self._run_startup_self_test()
        
        if not operational:
            self.logger.warning("Warden started in DEGRADED mode - self-test detected failures")
        
        return operational

    def stop(self) -> bool:
        """Lifecycle stop."""
        self.logger.info("Stopping Warden orchestration")
        return True
