#!/usr/bin/env python3
"""
EvidenceLockerModule - orchestrator wrapper for the Evidence Locker.

The Evidence Locker already contains the heavy evidence processing toolchain.
This wrapper gives it a consistent CAN bus presence, exposes a compliance-
friendly API, and standardises inter-module signalling so the locker can be
managed like the Warden and Marshall modules.
"""

from __future__ import annotations

import logging
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

try:
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Command Center', 'Data Bus', 'Bus Core Design'))
    from universal_communicator import UniversalCommunicator  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    UniversalCommunicator = None  # type: ignore

from _init_evidence_locker import (
    init_case_manifest_builder,
    init_evidence_class_builder,
    init_evidence_classifier,
    init_evidence_index,
    init_evidence_locker,
    init_static_data_flow,
)


class EvidenceLockerModule:
    """Container for the Evidence Locker core and helper components."""

    MODULE_ADDRESS = "1"
    BROADCAST_SIGNAL = "locker.child.broadcast"

    def __init__(
        self,
        *,
        bus: Optional[Any] = None,
        communicator: Optional[Any] = None,
        locker: Optional[Any] = None,
    ) -> None:
        self.logger = logging.getLogger("EvidenceLockerModule")
        self.bus = bus
        self.communicator = communicator
        self.locker: Optional[Any] = locker
        self.helpers: Dict[str, Any] = {}
        self.initialized = False

        if self.bus:
            self._initialize_canbus(self.bus)

        if self.locker:
            self.attach_locker(self.locker)

    # ------------------------------------------------------------------ #
    # CAN bus plumbing
    # ------------------------------------------------------------------ #
    def _initialize_canbus(self, bus: Any) -> None:
        """Register the module on the CAN bus and bind signal handlers."""
        self.bus = bus
        if not self.communicator and UniversalCommunicator and bus:
            try:
                self.communicator = UniversalCommunicator(self.MODULE_ADDRESS, bus_connection=bus)
                self.logger.info("[%s] UniversalCommunicator created", self.MODULE_ADDRESS)
            except Exception as exc:  # pragma: no cover - defensive
                self.logger.warning("Unable to initialise communicator: %s", exc)
                self.communicator = None

        if bus:
            try:
                bus.register_system_address(self.MODULE_ADDRESS, {
                    "system_type": "evidence_locker",
                    "capabilities": [
                        "evidence_ingestion",
                        "classification",
                        "manifest_generation",
                        "gateway_handoff",
                    ],
                    "status": "active",
                    "mode": "primary",
                    "registered_at": datetime.utcnow().isoformat(),
                })
                self.logger.info("[%s] Evidence Locker registered with CAN bus", self.MODULE_ADDRESS)
            except Exception as exc:  # pragma: no cover - defensive
                self.logger.warning("Failed to register Evidence Locker on CAN bus: %s", exc)

        self._register_signal_handlers()
        self._register_linbus_handlers()

    def _register_signal_handlers(self) -> None:
        """Bind minimal control/status handlers for the locker."""
        if not self.bus or not hasattr(self.bus, "register_signal"):
            return
        try:
            self.bus.register_signal("locker.status", self._handle_status_signal)
            self.bus.register_signal("locker.shutdown", self._handle_shutdown_signal)
            self.bus.register_signal(self.BROADCAST_SIGNAL, self._handle_child_broadcast)
            self.bus.register_signal("auto_registration", self._handle_auto_registration)
            
            # UDS Protocol Handlers (COMM FIX - bidirectional communication)
            self.bus.register_signal("diagnostic.rollcall", self._handle_rollcall)
            self.bus.register_signal("diagnostic.radio_check", self._handle_radio_check)
            
            self.logger.info("[%s] Evidence Locker signal handlers registered (including UDS protocol)", self.MODULE_ADDRESS)
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.warning("Failed to register Evidence Locker signal handlers: %s", exc)
    
    def _register_linbus_handlers(self) -> None:
        """Register LINBUS signal handlers for throttle coordination."""
        if not self.bus:
            self.logger.warning("[%s] Cannot register LINBUS handlers - no bus connection", self.MODULE_ADDRESS)
            return
        try:
            # Evidence Locker receives throttle coordination from Warden
            self.bus.register_signal("throttle.hold", self._handle_throttle_hold)
            self.bus.register_signal("throttle.release", self._handle_throttle_release)
            self.logger.info("[%s] LINBUS throttle handlers registered", self.MODULE_ADDRESS)
        except Exception as exc:  # pragma: no cover
            self.logger.error("[%s] Failed to register LINBUS handlers: %s", self.MODULE_ADDRESS, exc)
    
    def _handle_throttle_hold(self, payload: Optional[Dict[str, Any]] = None) -> None:
        """Handle LINBUS throttle hold signal from Warden."""
        self.logger.info("[%s] Throttle hold signal received on LINBUS", self.MODULE_ADDRESS)
    
    def _handle_throttle_release(self, payload: Optional[Dict[str, Any]] = None) -> None:
        """Handle LINBUS throttle release signal from Warden."""
        self.logger.info("[%s] Throttle release signal received on LINBUS", self.MODULE_ADDRESS)
    
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
        
        self.logger.info("[%s] Auto-registration request received from UDS", self.MODULE_ADDRESS)
        
        if not self.communicator:
            self.logger.warning("[%s] Cannot respond - no communicator available", self.MODULE_ADDRESS)
            return
        
        # Build registration response payload
        response_payload = {
            "system_address": self.MODULE_ADDRESS,
            "system_type": "evidence_locker",
            "status": "OPERATIONAL" if self.initialized else "INITIALIZING",
            "capabilities": ["evidence_ingestion", "classification", "manifest_generation", "gateway_handoff"],
            "child_components": ["1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7", "1.8"],
            "compliance_status": "COMPLIANT",
            "protocol_version": "1.0.0",
            "timestamp": datetime.now().isoformat()
        }
        
        # Send registration response to UDS
        try:
            self.communicator.send_signal(
                target_address="DIAG-1",
                radio_code="10-4",
                message=f"{self.MODULE_ADDRESS} registration acknowledged",
                payload=response_payload
            )
            self.logger.info("[%s] Auto-registration response sent to UDS", self.MODULE_ADDRESS)
        except Exception as exc:
            self.logger.error("[%s] Auto-registration response failed: %s", self.MODULE_ADDRESS, exc)
    
    def _handle_rollcall(self, payload: Dict[str, Any]) -> None:
        """
        Handle UDS rollcall signal.
        Respond with current system status and compliance information.
        """
        self.logger.info("[%s] Rollcall received from UDS", self.MODULE_ADDRESS)
        
        if not self.communicator:
            self.logger.warning("[%s] Cannot respond to rollcall - no communicator available", self.MODULE_ADDRESS)
            return
        
        # Build rollcall response
        response_payload = {
            "system_address": self.MODULE_ADDRESS,
            "system_type": "evidence_locker",
            "status": "OPERATIONAL" if self.initialized else "INITIALIZING",
            "compliance_status": "COMPLIANT",
            "active_components": len(self.helpers),
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            self.communicator.send_signal(
                target_address="DIAG-1",
                radio_code="10-4",
                message=f"{self.MODULE_ADDRESS} rollcall response",
                payload=response_payload
            )
            self.logger.info("[%s] Rollcall response sent to UDS", self.MODULE_ADDRESS)
        except Exception as exc:
            self.logger.error("[%s] Rollcall response failed: %s", self.MODULE_ADDRESS, exc)
    
    def _handle_radio_check(self, payload: Dict[str, Any]) -> None:
        """
        Handle UDS radio check signal.
        Respond immediately to confirm communication link.
        
        LIFECYCLE FIX: Only responds to CALL_SENT messages.
        """
        # Check message lifecycle state
        message_state = payload.get('message_state', '')
        if message_state != "CALL_SENT":
            return
        
        self.logger.info("[%s] Radio check received from UDS", self.MODULE_ADDRESS)
        
        if not self.communicator:
            self.logger.warning("[%s] Cannot respond to radio check - no communicator available", self.MODULE_ADDRESS)
            return
        
        # Build radio check response with latency measurement
        request_time = payload.get('timestamp', datetime.now().isoformat())
        response_payload = {
            "system_address": self.MODULE_ADDRESS,
            "radio_code": "10-4",
            "signal_strength": "STRONG",
            "request_time": request_time,
            "response_time": datetime.now().isoformat(),
            "status": "OPERATIONAL"
        }
        
        try:
            self.communicator.send_signal(
                target_address="DIAG-1",
                radio_code="10-4",
                message=f"{self.MODULE_ADDRESS} radio check response",
                payload=response_payload
            )
            self.logger.info("[%s] Radio check response sent to UDS", self.MODULE_ADDRESS)
        except Exception as exc:
            self.logger.error("[%s] Radio check response failed: %s", self.MODULE_ADDRESS, exc)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def initialize_system(
        self,
        *,
        bus: Optional[Any] = None,
        locker_factory: Optional[Any] = None,
        locker_kwargs: Optional[Dict[str, Any]] = None,
        reinitialize: bool = False,
    ) -> Dict[str, Any]:
        """
        Initialise the Evidence Locker wrapper and (optionally) construct the core locker.
        Returns a status payload suitable for diagnostics.
        """
        if bus is not None:
            self.bus = bus
        if self.bus and (reinitialize or not self.communicator):
            self._initialize_canbus(self.bus)

        if locker_factory is None and self.locker is None:
            locker_factory = init_evidence_locker

        if locker_factory and self.locker is None:
            kwargs = dict(locker_kwargs or {})
            kwargs.setdefault("bus", self.bus)
            self.locker = locker_factory(**kwargs)
            self._log_subsystem_init("EvidenceLocker", "instantiated via factory")

        if self.locker:
            self.attach_locker(self.locker, reinitialize=reinitialize)
            if reinitialize:
                self.helpers.clear()
            self._initialize_helpers()

        # Run mandatory self-test per UDS protocol requirements
        operational = self._run_startup_self_test()

        self.initialized = True
        status = self.get_locker_status()
        status["self_test_passed"] = operational
        status["status"] = "SUCCESS" if operational else "DEGRADED"
        self.logger.info("[%s] Evidence Locker initialize_system -> %s", self.MODULE_ADDRESS, status)
        return status

    def attach_locker(self, locker: Any, *, reinitialize: bool = False) -> None:
        """Attach the primary locker implementation and ensure it is bus-aware."""
        self.locker = locker
        self._log_subsystem_init("EvidenceLocker", "attached to wrapper")

    def register_helper(self, name: str, helper: Any) -> None:
        """Record an auxiliary helper component for diagnostics."""
        self.helpers[name] = helper
        self._log_subsystem_init(name, "helper registered")
        if self.locker and not hasattr(self.locker, name):
            setattr(self.locker, name, helper)

    def _initialize_helpers(self) -> None:
        """Instantiate default helper subsystems if absent."""
        helper_defs = []
        helper_defs.append(("classifier", lambda: init_evidence_classifier()))
        helper_defs.append(("index", lambda: init_evidence_index()))
        helper_defs.append(("class_builder", lambda: init_evidence_class_builder()))
        helper_defs.append(("static_flow", lambda: init_static_data_flow()))
        helper_defs.append(("manifest_builder", lambda: init_case_manifest_builder()))

        for name, factory in helper_defs:
            if name in self.helpers:
                continue
            try:
                instance = factory()
                if instance is not None:
                    self.register_helper(name, instance)
            except Exception as exc:
                self.logger.warning("Helper '%s' initialisation failed: %s", name, exc)

    def ingest_evidence(self, file_path: str, section_id: Optional[str] = None) -> Dict[str, Any]:
        """Entry point for file ingestion."""
        locker = self._require_locker()
        classifier = self.helpers.get("classifier")
        class_builder = self.helpers.get("class_builder")
        index = self.helpers.get("index")
        static_flow = self.helpers.get("static_flow")

        if not file_path:
            raise ValueError("ingest_evidence requires a file path.")
        resolved = Path(file_path)
        if not resolved.exists():
            raise FileNotFoundError(f"Evidence file not found: {file_path}")

        if not classifier or not class_builder or not index:
            raise RuntimeError("Evidence tooling not initialised.")

        classification = classifier.classify(str(resolved), section_id)
        assigned_section = classification["assigned_section"]
        record = class_builder.build(str(resolved), assigned_section, classification.get("tags"))
        record.metadata.update(classification)

        locker.store_record(record)
        index.add_file(record)
        if static_flow:
            static_flow.announce(
                "ingest_evidence",
                {"evidence_id": record.evidence_id, "section_id": assigned_section},
            )

        payload = {
            "file_path": str(resolved),
            "section_id": assigned_section,
            "evidence_id": record.evidence_id,
            "confidence": classification.get("confidence"),
        }
        self._broadcast("ingest_evidence", payload)
        return asdict(record)

    def process_evidence(self, file_path: str) -> Dict[str, Any]:
        """Process evidence through the comprehensive pipeline."""
        return self.ingest_evidence(file_path)

    def process_evidence_batch(self, files: Iterable[str]) -> Dict[str, Any]:
        """Convenience helper for batch processing."""
        batch = {}
        for file_path in files:
            try:
                batch[file_path] = self.process_evidence(file_path)
            except Exception as exc:
                self.logger.error("Batch processing failed for %s: %s", file_path, exc)
                batch[file_path] = {"status": "ERROR", "error": str(exc)}
        self._broadcast("process_evidence_batch", {"count": len(batch)})
        return batch

    def classify_evidence(self, file_path: str) -> Dict[str, Any]:
        """Expose classification without routing the evidence."""
        classifier = self.helpers.get("classifier")
        if not classifier:
            raise RuntimeError("Evidence classifier not initialised.")
        return classifier.classify(file_path)

    def start_new_case(self, case_payload: Dict[str, Any]) -> Any:
        """Delegate case initialisation to the locker if available."""
        locker = self._require_locker()
        if not isinstance(case_payload, dict):
            raise ValueError("start_new_case expects a dictionary payload.")
        case_id = case_payload.get("case_id")
        locker.start_new_case(case_id)
        self._broadcast("start_new_case", {"case_id": case_id})
        return {"status": "SUCCESS", "case_id": case_id}

    def get_manifest(self) -> Dict[str, Any]:
        """Return the evidence manifest maintained by the locker."""
        locker = self._require_locker()
        manifest_builder = self.helpers.get("manifest_builder")
        if not manifest_builder:
            raise RuntimeError("Manifest builder not initialised.")
        return manifest_builder.build(locker.case_id, locker.records)

    def get_evidence(self, evidence_id: str) -> Dict[str, Any]:
        """Fetch a single evidence record from the manifest."""
        if not evidence_id:
            raise ValueError("get_evidence requires an evidence identifier.")
        locker = self._require_locker()
        record = locker.records.get(evidence_id)
        if record is None:
            raise KeyError(f"Evidence {evidence_id} not found.")
        return asdict(record)

    def clear_evidence_pool(self) -> None:
        """Clear the locker evidence store using the locker implementation if available."""
        locker = self._require_locker()
        locker.clear()
        self._broadcast("clear_evidence_pool", {})

    def get_locker_status(self) -> Dict[str, Any]:
        """Summarise the Evidence Locker state for diagnostics."""
        locker = self.locker
        status = {
            "locker_attached": locker is not None,
            "helpers_registered": list(self.helpers.keys()),
            "bus_connected": bool(self.bus),
            "initialized": self.initialized,
        }
        if locker:
            status["case_id"] = locker.case_id
            status["evidence_count"] = len(locker.records)
        return status

    # ------------------------------------------------------------------ #
    # Wildcard + fault helpers
    # ------------------------------------------------------------------ #
    def broadcast_signal(self, message_type: str, payload: Dict[str, Any]) -> None:
        """Emit a locker-child broadcast onto the CAN bus."""
        if not message_type:
            raise ValueError("broadcast_signal requires a message type.")
        broadcast_payload = dict(payload or {})
        broadcast_payload.setdefault("message_type", message_type)
        broadcast_payload.setdefault("source", "evidence_locker")
        broadcast_payload.setdefault("timestamp", None)
        self._broadcast(message_type, broadcast_payload)

    def raise_mayday(self, fault_code: str, description: str, *, details: Optional[Dict[str, Any]] = None) -> None:
        """Raise an SOS fault for the locker subsystem."""
        if not fault_code or not description:
            raise ValueError("raise_mayday requires fault_code and description.")
        if self.communicator:
            try:
                self.communicator.send_sos_fault(
                    fault_code=fault_code,
                    description=description,
                    details=details or {},
                )
            except Exception as exc:  # pragma: no cover - defensive
                self.logger.warning("Locker SOS fault transmission failed: %s", exc)
        if self.bus:
            try:
                self.bus.emit("locker.mayday", {
                    "fault_code": fault_code,
                    "description": description,
                    "details": details or {},
                })
            except Exception:
                pass

    # ------------------------------------------------------------------ #
    # Signal handlers
    # ------------------------------------------------------------------ #
    def _handle_status_signal(self, _payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.get_locker_status()

    def _handle_shutdown_signal(self, _payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self.stop()
        return {"status": "SUCCESS", "shutdown": True}

    def _handle_child_broadcast(self, payload: Dict[str, Any]) -> None:
        """Translate child broadcasts to specific CANBUS signals."""
        self.logger.debug("Locker child broadcast received: %s", payload)
        
        if not self.bus or not hasattr(self.bus, 'emit'):
            return
        
        message_type = payload.get('message_type')
        
        # Translate internal broadcasts to specific CANBUS signals
        try:
            if message_type == 'ingest_evidence':
                # Emit radio code 10-6 (Evidence Received)
                if self.communicator:
                    self.communicator.send_signal(
                        target_address="Bus-1",
                        radio_code="10-6",
                        message="Evidence received and processing"
                    )
                
                # Emit evidence.new signal
                self.bus.emit('evidence.new', {
                    'evidence_id': payload.get('evidence_id'),
                    'section_id': payload.get('section_id'),
                    'file_path': payload.get('file_path'),
                    'source': self.MODULE_ADDRESS,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Emit evidence.classified signal
                self.bus.emit('evidence.classified', {
                    'evidence_id': payload.get('evidence_id'),
                    'section_id': payload.get('section_id'),
                    'confidence': payload.get('confidence'),
                    'source': self.MODULE_ADDRESS,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Emit radio code 10-4 (Acknowledged/Ready)
                if self.communicator:
                    self.communicator.send_signal(
                        target_address="Bus-1",
                        radio_code="10-4",
                        message="Evidence classified and ready"
                    )
                
                self.logger.info("[%s] Translated ingest_evidence to evidence.new, evidence.classified", self.MODULE_ADDRESS)
            
            elif message_type == 'start_new_case':
                self.bus.emit('case.created', {
                    'case_id': payload.get('case_id'),
                    'source': self.MODULE_ADDRESS,
                    'timestamp': datetime.now().isoformat()
                })
                self.logger.info("[%s] Translated start_new_case to case.created", self.MODULE_ADDRESS)
            
            elif message_type == 'clear_evidence_pool':
                self.bus.emit('locker.cleared', {
                    'source': self.MODULE_ADDRESS,
                    'timestamp': datetime.now().isoformat()
                })
                self.logger.info("[%s] Translated clear_evidence_pool to locker.cleared", self.MODULE_ADDRESS)
        
        except Exception as exc:
            self.logger.warning("[%s] Signal translation failed: %s", self.MODULE_ADDRESS, exc)

    # ------------------------------------------------------------------ #
    # Lifecycle hooks
    # ------------------------------------------------------------------ #
    def start(self) -> None:
        self.logger.info("[%s] Evidence Locker module start invoked", self.MODULE_ADDRESS)

    def stop(self) -> None:
        self.logger.info("[%s] Evidence Locker module stop invoked", self.MODULE_ADDRESS)

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _broadcast(self, message_type: str, payload: Dict[str, Any]) -> None:
        if self.bus and hasattr(self.bus, "emit"):
            try:
                event = dict(payload or {})
                event.setdefault("message_type", message_type)
                event.setdefault("source", "evidence_locker")
                self.bus.emit(self.BROADCAST_SIGNAL, event)
            except Exception as exc:
                self.logger.debug("Broadcast emit failed: %s", exc)

    def _require_locker(self) -> Any:
        if not self.locker:
            raise RuntimeError("EvidenceLocker implementation not attached.")
        return self.locker

    def _log_subsystem_init(self, subsystem: str, message: str) -> None:
        self.logger.info("[%s::%s] %s", self.MODULE_ADDRESS, subsystem, message)
    
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
            ('1.1', 'Evidence Classifier', lambda: getattr(self.locker, 'classifier', None)),
            ('1.2', 'Evidence Identifier', lambda: getattr(self.locker, 'identifier', None)),
            ('1.3', 'Static Data Flow', lambda: self.helpers.get('static_data_flow')),
            ('1.4', 'Evidence Index', lambda: self.helpers.get('evidence_index')),
            ('1.5', 'Evidence Manifest', lambda: getattr(self.locker, 'manifest', None)),
            ('1.6', 'Evidence Class Builder', lambda: self.helpers.get('evidence_class_builder')),
            ('1.7', 'Case Manifest Builder', lambda: self.helpers.get('case_manifest_builder')),
            ('1.8', 'OCR Processor', lambda: getattr(self.locker, 'ocr_engine', None)),
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
                        "system_name": "Evidence Locker Module",
                        "test_result": "PASS" if operational else "FAIL",
                        "children_tested": 8,
                        "timestamp": datetime.now().isoformat()
                    }
                )
                self.logger.info("[%s] Self-test completion signal sent to UDS", self.MODULE_ADDRESS)
            except Exception as exc:
                self.logger.error("[%s] Failed to send self-test completion signal: %s", self.MODULE_ADDRESS, exc)
        
        return operational
