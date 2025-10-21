"""Section 1 engine (Investigation Objectives & Case Profile)."""

from __future__ import annotations

import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

_CURRENT_DIR = Path(__file__).resolve().parent
_ANALYST_ROOT = _CURRENT_DIR.parent
_BASE_PATH = _ANALYST_ROOT / "section revisions templates"

for path in (_BASE_PATH, _ANALYST_ROOT):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from section_framework_base import (
    CommunicationContract,
    FactGraphContract,
    LifecycleState,
    OrderContract,
    PersistenceContract,
    SectionFramework,
    StageDefinition,
)

try:
    from ._init_evidence_manager import init_evidence_manager
    from ._init_northstar_protocol import init_northstar_protocol
    from ._init_cochran_match import init_cochran_match
    from ._init_reverse_continuity import init_reverse_continuity
    from ._init_metadata_processor import init_metadata_processor
    from ._init_mileage_audit import init_mileage_audit
    from ._init_section_renderer import init_section_renderer
    from ._init_tesseract import init_tesseract
    from ._init_unstructured import init_unstructured
    from ._init_easyocr import init_easyocr
except ImportError:  # pragma: no cover
    from _init_evidence_manager import init_evidence_manager  # type: ignore
    from _init_northstar_protocol import init_northstar_protocol  # type: ignore
    from _init_cochran_match import init_cochran_match  # type: ignore
    from _init_reverse_continuity import init_reverse_continuity  # type: ignore
    from _init_metadata_processor import init_metadata_processor  # type: ignore
    from _init_mileage_audit import init_mileage_audit  # type: ignore
    from _init_section_renderer import init_section_renderer  # type: ignore
    from _init_tesseract import init_tesseract  # type: ignore
    from _init_unstructured import init_unstructured  # type: ignore
    from _init_easyocr import init_easyocr  # type: ignore

FAULT_LOAD_INPUTS = "4-1-LOAD-001"
FAULT_BUILD_PAYLOAD = "4-1-BUILD-001"
FAULT_PUBLISH = "4-1-PUBLISH-001"


class _NullGateway:
    """Fallback gateway used when none is supplied."""

    ecc: Optional[Any] = None

    def get_section_inputs(self, section_id: str) -> Dict[str, Any]:
        return {}

    def publish_section_result(self, section_id: str, result: Dict[str, Any]) -> None:
        pass

    def emit(self, signal: str, payload: Dict[str, Any]) -> None:
        pass

    def log_revision(self, section_id: str, reason: str, context: Dict[str, Any]) -> None:
        pass


class Section1Framework(SectionFramework):
    """Section 1 pipeline responsible for the case profile."""

    SECTION_ID = "section_1_profile"
    MODULE_ADDRESS = "4-1"
    BUS_SECTION_ID = "section_1"
    MAX_RERUNS = 2

    STAGES = (
        StageDefinition(
            name="acquire",
            description="Load intake docs, register evidence, verify file integrity.",
            checkpoint="s1_profile_acquire",
            guardrails=("order_lock", "async_queue", "persistence_snapshot"),
        ),
        StageDefinition(
            name="extract",
            description="Run strongest-first extraction for IDs, contracts, manifests.",
            checkpoint="s1_profile_extract",
            guardrails=("confidence_threshold", "fallback_logging"),
        ),
        StageDefinition(
            name="normalize",
            description="Apply parsing maps, toolkit rules (alias dedupe, continuity).",
            checkpoint="s1_profile_normalized",
            guardrails=("schema_validation", "fact_graph_sync"),
        ),
        StageDefinition(
            name="validate",
            description="Enforce Cochran/North Star, legal compliance; capture QA issues.",
            checkpoint="s1_profile_validated",
            guardrails=("continuity_checks", "manual_queue_routes"),
        ),
        StageDefinition(
            name="publish",
            description="Publish payload to gateway, emit dependency signals, record approvals.",
            checkpoint="section_1_profile_completed",
            guardrails=("durable_persistence", "signal_emission", "immutability"),
        ),
        StageDefinition(
            name="monitor",
            description="Handle revision requests while enforcing rerun guardrails.",
            checkpoint="s1_profile_revision_processed",
            guardrails=("max_reruns", "revision_depth_cap", "fact_graph_consistency"),
        ),
    )

    COMMUNICATION = CommunicationContract(
        prepare_signal="case_bundle.initialized",
        input_channels=(
            "intake_bundle",
            "extracted_metadata",
            "toolkit_cache",
            "manual_overrides",
        ),
        output_signal="section_1_profile.completed",
        revision_signal="case_metadata_revision",
    )

    ORDER = OrderContract(
        execution_after=("section_cp", "section_toc"),
        export_after=(),
        export_priority=10,
    )

    def __init__(
        self,
        gateway: Optional[Any] = None,
        *,
        bus: Optional[Any] = None,
        communicator: Optional[Any] = None,
        marshal_client: Optional[Any] = None,
        marshal_address: Optional[str] = None,
        warden_client: Optional[Any] = None,
        dependency_initializers: Optional[Dict[str, Callable[..., Any]]] = None,
        queue_client: Optional[Any] = None,
        storage: Optional[Any] = None,
        fact_graph: Optional[Any] = None,
    ) -> None:
        # CRITICAL: Initialize logger FIRST so CANBUS init errors can be logged
        self.logger = logging.getLogger(self.__class__.__name__)
        self.MODULE_ADDRESS = "4-1"
        
        # ------------------------------------------------------------------ #
        # CANBUS CONNECTION (SECTION MODULE - INLINE)
        # ------------------------------------------------------------------ #
        self.bus = bus
        self.communicator = communicator
        self.bus_connected = False
        
        if self.bus:
            # MODULE INITIALIZATION PROTOCOL - Wait for bus ready and module turn
            self.logger.info("[%s] Waiting for bus stabilization...", self.MODULE_ADDRESS)
            if not self.bus.wait_for_ready(timeout=15.0):
                self.logger.warning("[%s] Bus stabilization timeout - initializing in degraded mode", self.MODULE_ADDRESS)
                self.bus_connected = False
            else:
                self.logger.info("[%s] Bus ready - waiting for module turn in sequence...", self.MODULE_ADDRESS)
                if not self.bus.wait_for_module_turn('4-1', timeout=30.0):
                    self.logger.warning("[%s] Module turn timeout - initializing in degraded mode", self.MODULE_ADDRESS)
                    self.bus_connected = False
                else:
                    self._initialize_canbus(self.bus, communicator=self.communicator)
        else:
            self.logger.warning("[%s] CANBUS initialization skipped - no bus provided", self.MODULE_ADDRESS)
            self.bus_connected = False
        
        # ------------------------------------------------------------------ #
        # Tool initialization
        # ------------------------------------------------------------------ #
        initializers = {
            "evidence_manager": init_evidence_manager,
            "northstar_protocol": init_northstar_protocol,
            "cochran_match": init_cochran_match,
            "reverse_continuity": init_reverse_continuity,
            "metadata_processor": init_metadata_processor,
            "mileage_audit": init_mileage_audit,
            "section_renderer": init_section_renderer,
            "tesseract_engine": init_tesseract,
            "unstructured_engine": init_unstructured,
            "easyocr_engine": init_easyocr,
        }
        if dependency_initializers:
            initializers.update(dependency_initializers)

        super().__init__(
            gateway or _NullGateway(),
            module_address=self.MODULE_ADDRESS,
            communicator_initializer=None,  # Using direct bus connection instead
            marshal_client=marshal_client,
            marshal_address=marshal_address,
            warden_client=warden_client,
            dependency_initializers=initializers,
            queue_client=queue_client,
            storage=storage,
            fact_graph=fact_graph,
        )
        
        # Override base class communicator with our direct connection
        if self.bus_connected:
            self.communicator = self.communicator
            self.bus = self.bus

        self.baseline_report = self.run_baseline_initialization()
        self.evidence_manager = self.get_dependency("evidence_manager")
        self.northstar_process = self.get_dependency("northstar_protocol")
        self.cochran_match = self.get_dependency("cochran_match")
        self.reverse_continuity_tool = self.get_dependency("reverse_continuity")
        self.metadata_processor = self.get_dependency("metadata_processor")
        self.mileage_audit = self.get_dependency("mileage_audit")
        self.section_renderer = self.get_dependency("section_renderer")
        self.tesseract_engine = self.get_dependency("tesseract_engine")
        self.unstructured_engine = self.get_dependency("unstructured_engine")
        self.easyocr_engine = self.get_dependency("easyocr_engine")
        
        # Run mandatory self-test per UDS protocol
        self._run_startup_self_test()

    # ------------------------------------------------------------------ #
    # CANBUS initialization
    # ------------------------------------------------------------------ #
    def _initialize_canbus(self, bus: Any, *, communicator: Optional[Any] = None) -> None:
        """Set up CANBUS connectivity and register signal handlers."""
        try:
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Command Center', 'Data Bus', 'Bus Core Design'))
            from universal_communicator import UniversalCommunicator
        except ImportError:
            UniversalCommunicator = None
        
        self.bus = bus
        try:
            if communicator:
                self.communicator = communicator
            elif UniversalCommunicator:
                self.communicator = UniversalCommunicator(self.MODULE_ADDRESS, bus_connection=bus)
                self.logger.info("[%s] UniversalCommunicator created", self.MODULE_ADDRESS)

            bus.register_system_address(self.MODULE_ADDRESS, {
                "system_type": "section_engine",
                "capabilities": ["evidence_request", "evidence_processing", "section_rendering", "fault_reporting"],
                "status": "active",
                "mode": "primary",
                "registered_at": datetime.now().isoformat(),
                "section_name": "Investigation Objectives",
                "tools": ["evidence_manager", "northstar_protocol", "cochran_match", 
                         "reverse_continuity", "metadata_processor", "mileage_audit", 
                         "section_renderer", "tesseract_engine", "unstructured_engine", "easyocr_engine"]
            })
            self.logger.info("[%s] Section 1 registered with CANBUS", self.MODULE_ADDRESS)

            self._register_signal_handlers()
            self.bus_connected = True
            self.logger.info("[%s] CANBUS CONNECTION ESTABLISHED", self.MODULE_ADDRESS)
            
            # MODULE INITIALIZATION PROTOCOL - Register with bus
            if self.bus.register_module_init('4-1', {
                'version': '1.0',
                'type': 'analyst_section',
                'capabilities': ['case_profile', 'investigation_objectives', 'metadata_extraction']
            }):
                self.logger.info("[%s] [OK] Module registered with bus (Address 4-1)", self.MODULE_ADDRESS)
            else:
                self.logger.warning("[%s] Module registration failed - continuing anyway", self.MODULE_ADDRESS)
        except Exception as exc:
            self.logger.critical("[%s] CANBUS connection failed: %s", self.MODULE_ADDRESS, exc)
            self.bus_connected = False

    def _register_signal_handlers(self) -> None:
        """Register section signal handlers with the CANBUS."""
        if not self.bus:
            self.logger.warning("[%s] Cannot register signals - no CANBUS connection", self.MODULE_ADDRESS)
            return
        try:
            self.bus.register_signal("section_1.evidence_request", self._handle_evidence_request)
            self.bus.register_signal("section_1.wake", self._handle_wake_signal)
            self.bus.register_signal("section_1.sleep", self._handle_sleep_signal)
            self.bus.register_signal("section_1.status", self._handle_status_signal)
            
            # UDS Protocol Handlers (PHASE 2C FIX - complete bidirectional comm)
            self.bus.register_signal("diagnostic.rollcall", self._handle_rollcall)
            self.bus.register_signal("diagnostic.radio_check", self._handle_radio_check)
            self.bus.register_signal("auto_registration", self._handle_auto_registration)
            
            self.logger.info("[%s] Section signal handlers registered (including UDS bidirectional protocol)", self.MODULE_ADDRESS)
        except Exception as exc:
            self.logger.error("[%s] Failed to register signal handlers: %s", self.MODULE_ADDRESS, exc)

    def _handle_evidence_request(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle evidence request signal."""
        return {"status": "evidence_request_received", "section": self.MODULE_ADDRESS}

    def _handle_wake_signal(self, payload: Optional[Dict[str, Any]] = None) -> None:
        """Handle wake signal from Marshall."""
        self.logger.info("[%s] Wake signal received", self.MODULE_ADDRESS)

    def _handle_sleep_signal(self, payload: Optional[Dict[str, Any]] = None) -> None:
        """Handle sleep signal from Marshall."""
        self.logger.info("[%s] Sleep signal received", self.MODULE_ADDRESS)

    def _handle_status_signal(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle status signal."""
        return {
            "module_address": self.MODULE_ADDRESS,
            "status": "active",
            "bus_connected": self.bus_connected,
            "tools_operational": self.baseline_report.get("status") == "passed"
        }
    
    def _handle_rollcall(self, payload: Dict[str, Any]) -> None:
        """Handle UDS rollcall request (PHASE 2C FIX)
        
        Respond with current status and compliance information.
        """
        self.logger.info("[%s] Rollcall request received from UDS", self.MODULE_ADDRESS)
        
        if not self.communicator:
            self.logger.warning("[%s] Cannot respond - no communicator available", self.MODULE_ADDRESS)
            return
        
        # Build rollcall response
        status_data = {
            "system_address": self.MODULE_ADDRESS,
            "system_name": "Section 1 - Investigation Objectives",
            "status": "OPERATIONAL" if self.bus_connected else "INITIALIZING",
            "tools_count": len(self.tool_dependencies),
            "compliance_status": "COMPLIANT",
            "timestamp": datetime.now().isoformat()
        }
        
        # Send rollcall response on correct topic
        try:
            self.communicator.send_rollcall_response("DIAG-1", status_data)
            self.logger.info("[%s] Rollcall response sent to UDS", self.MODULE_ADDRESS)
        except Exception as exc:
            self.logger.error("[%s] Rollcall response failed: %s", self.MODULE_ADDRESS, exc)
    
    def _handle_radio_check(self, payload: Dict[str, Any]) -> None:
        """Handle UDS radio check request (PHASE 2C FIX)
        
        Respond with connectivity and communication health data.
        """
        self.logger.info("[%s] Radio check request received from UDS", self.MODULE_ADDRESS)
        
        if not self.communicator:
            self.logger.warning("[%s] Cannot respond - no communicator available", self.MODULE_ADDRESS)
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
            self.logger.info("[%s] Radio check response sent to UDS", self.MODULE_ADDRESS)
        except Exception as exc:
            self.logger.error("[%s] Radio check response failed: %s", self.MODULE_ADDRESS, exc)
    
    def _handle_auto_registration(self, payload: Dict[str, Any]) -> None:
        """Handle UDS auto-registration request (PHASE 2C FIX)
        
        Respond with section capabilities and compliance status.
        """
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
        system_metadata = {
            "system_address": self.MODULE_ADDRESS,
            "system_name": "Section 1 - Investigation Objectives",
            "system_type": "analyst_section",
            "parent_address": "3",  # Marshall
            "status": "OPERATIONAL" if self.bus_connected else "INITIALIZING",
            "capabilities": ["evidence_request", "evidence_processing", "section_rendering", "fault_reporting"],
            "tool_dependencies": list(self.tool_dependencies.keys()),
            "compliance_status": "COMPLIANT",
            "protocol_version": "1.0.0",
            "timestamp": datetime.now().isoformat()
        }
        
        # Send auto-registration response on correct topic
        try:
            self.communicator.send_auto_registration_response("DIAG-1", system_metadata)
            self.logger.info("[%s] Auto-registration response sent to UDS", self.MODULE_ADDRESS)
        except Exception as exc:
            self.logger.error("[%s] Auto-registration response failed: %s", self.MODULE_ADDRESS, exc)

    # ------------------------------------------------------------------
    # Self-Test Protocol (UDS Compliance)
    # ------------------------------------------------------------------
    def _run_startup_self_test(self) -> bool:
        """
        Validate all tool dependencies per UDS self-test protocol.
        Emit fault codes for failed tools to Marshall (3).
        
        Returns True if all tools operational, False if any failed.
        """
        self.logger.info("[%s] Running mandatory startup self-test per UDS protocol", self.MODULE_ADDRESS)
        operational = True
        
        # Define tool dependencies to validate
        tools_to_validate = [
            ('4-1.1', 'Evidence Manager', lambda: self.evidence_manager),
            ('4-1.2', 'Northstar Protocol', lambda: self.northstar_process),
            ('4-1.3', 'Cochran Match', lambda: self.cochran_match),
            ('4-1.4', 'Reverse Continuity', lambda: self.reverse_continuity_tool),
            ('4-1.5', 'Metadata Processor', lambda: self.metadata_processor),
            ('4-1.6', 'Mileage Audit', lambda: self.mileage_audit),
            ('4-1.7', 'Section Renderer', lambda: self.section_renderer),
            ('4-1.8', 'Tesseract Engine', lambda: self.tesseract_engine),
            ('4-1.9', 'Unstructured Engine', lambda: self.unstructured_engine),
            ('4-1.10', 'EasyOCR Engine', lambda: self.easyocr_engine),
        ]
        
        for tool_addr, tool_name, get_tool_ref in tools_to_validate:
            try:
                tool_ref = get_tool_ref()
                
                if tool_ref is None:
                    # Tool dependency failed to initialize - emit fault code
                    self.logger.error(
                        "[%s] Self-test FAILED: %s (%s) not initialized - emitting fault code",
                        self.MODULE_ADDRESS, tool_name, tool_addr
                    )
                    
                    # Emit fault code to Marshall via LINBUS (primary path)
                    fault_payload = {
                        "fault_code": f"[{tool_addr}-12-INIT]",
                        "description": f"{tool_name} not initialized - missing dependency or initialization failure",
                        "component": tool_name,
                        "reporting_address": tool_addr,
                        "parent_address": self.MODULE_ADDRESS,
                        "severity": "CRITICAL",
                        "timestamp": datetime.now().isoformat(),
                        "fault_type": "12",
                        "fault_type_description": "Missing initialization dependency",
                        "message_type": "initialization_failure"
                    }
                    
                    linbus_success = False
                    if self.bus and self.bus_connected:
                        try:
                            # Primary: LINBUS emission to Marshall
                            self.bus.emit('section.fault', fault_payload)
                            self.logger.warning(
                                "[%s] Fault code emitted via LINBUS: [%s-12-INIT] - %s",
                                self.MODULE_ADDRESS, tool_addr, tool_name
                            )
                            linbus_success = True
                        except Exception as linbus_exc:
                            self.logger.error(
                                "[%s] LINBUS fault emission failed: %s - attempting CANBUS fallback",
                                self.MODULE_ADDRESS, linbus_exc
                            )
                    
                    # Fallback: CANBUS direct emission to UDS if LINBUS fails
                    if not linbus_success:
                        if hasattr(self, 'communicator') and self.communicator:
                            try:
                                self.communicator.send_signal(
                                    target_address="DIAG-1",
                                    radio_code="SOS",
                                    message=f"{tool_name} initialization failed (CANBUS fallback)",
                                    payload=fault_payload
                                )
                                self.logger.warning(
                                    "[%s] Fault code emitted via CANBUS fallback: [%s-12-INIT] - %s",
                                    self.MODULE_ADDRESS, tool_addr, tool_name
                                )
                            except Exception as canbus_exc:
                                self.logger.error(
                                    "[%s] CANBUS fallback also failed: %s",
                                    self.MODULE_ADDRESS, canbus_exc
                                )
                        else:
                            self.logger.error(
                                "[%s] Cannot emit fault code - no bus connection available",
                                self.MODULE_ADDRESS
                            )
                    
                    operational = False
                else:
                    # Tool validated successfully
                    self.logger.info(
                        "[%s] Self-test PASSED: %s (%s) operational",
                        self.MODULE_ADDRESS, tool_name, tool_addr
                    )
                    
            except Exception as exc:
                # Unexpected error during validation
                self.logger.error(
                    "[%s] Self-test ERROR: Failed to validate %s (%s): %s",
                    self.MODULE_ADDRESS, tool_name, tool_addr, exc
                )
                operational = False
        
        if operational:
            self.logger.info("[%s] PASS - Self-test COMPLETE - All tool dependencies operational", self.MODULE_ADDRESS)
        else:
            self.logger.warning("[%s] FAIL - Self-test COMPLETE - One or more tool dependencies FAILED", self.MODULE_ADDRESS)
        
        return operational

    # ------------------------------------------------------------------
    # Input / payload lifecycle
    # ------------------------------------------------------------------
    def load_inputs(self) -> Dict[str, Any]:
        """Load inputs from Gateway & Evidence Manager."""
        try:
            if self.lifecycle_state() == LifecycleState.RESTING:
                self.resume_from_rest()

            evidence_data: Dict[str, Any] = {}
            if self.evidence_manager and hasattr(self.evidence_manager, "processed_evidence"):
                processed_evidence = getattr(self.evidence_manager, "processed_evidence", {})
                evidence_data = {
                    "processed_evidence": processed_evidence,
                    "evidence_count": len(processed_evidence),
                }

            gateway_inputs: Dict[str, Any] = {}
            if hasattr(self.gateway, "get_section_inputs"):
                gateway_inputs = self.gateway.get_section_inputs(self.bus_section_id() or "section_1")

            combined_inputs = {**gateway_inputs, **evidence_data}
            return self._augment_with_bus_context(combined_inputs)

        except Exception as exc:  # pragma: no cover - runtime error path
            self.logger.exception("Failed to load inputs for %s: %s", self.SECTION_ID, exc)
            self.emit_fault(FAULT_LOAD_INPUTS, detail=str(exc))
            return self._augment_with_bus_context({})

    def build_payload(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Build the structured payload for Section 1."""
        try:
            sources: Iterable[Dict[str, Any]] = (
                context.get("section_payload", {}),
                context.get("case_data", {}),
                context.get("intake_bundle", {}),
                context.get("toolkit_cache", {}),
                context.get("manual_overrides", {}),
            )

            def first_nonempty(key: str) -> Optional[Any]:
                for source in sources:
                    value = source.get(key)
                    if value:
                        return value
                return None

            whitelist = [
                "client_name",
                "client_address",
                "client_phone",
                "contract_date",
                "investigation_goals",
                "subject_primary",
                "subject_secondary",
                "subject_tertiary",
                "subject_employers",
                "subject_employer_address",
                "agency_name",
                "agency_license",
                "assigned_investigator",
                "investigator_license",
                "location_of_investigation",
            ]

            payload: Dict[str, Any] = {}
            for key in whitelist:
                payload[key] = first_nonempty(key) or "Unknown"

            profile = context.get("profile_settings", {})
            subcontractor = context.get("subcontractor_agreement", {})
            if subcontractor.get("exists"):
                payload["assigned_investigator"] = subcontractor.get("assigned_investigator")
                payload["investigator_license"] = subcontractor.get("investigator_license")
            elif profile.get("employee_name") and profile.get("employee_license"):
                payload["assigned_investigator"] = profile["employee_name"]
                payload["investigator_license"] = profile["employee_license"]
            else:
                payload["assigned_investigator"] = "David Krashin"
                payload["investigator_license"] = "0163814-C000480"

            payload["agency_name"] = profile.get("agency_name", "DKI Services LLC")
            payload["agency_license"] = profile.get("agency_license", "0200812-IA000307")

            processed_evidence = context.get("processed_evidence") or {}
            evidence_assets = [
                {
                    "id": evidence_id,
                    "file_path": record.get("file_path"),
                    "filename": record.get("filename"),
                    "evidence_type": record.get("metadata", {}).get("evidence_type", "unknown"),
                    "field_time": record.get("metadata", {}).get("field_time"),
                    "received_time": record.get("ingested_at"),
                }
                for evidence_id, record in processed_evidence.items()
                if record.get("section_id") in {self.BUS_SECTION_ID, "section_1"}
            ]

            if callable(self.northstar_process):
                payload["northstar_result"] = self.northstar_process(evidence_assets)
            else:
                payload["northstar_result"] = {"status": "not_available"}

            if callable(self.cochran_match):
                payload["cochran_result"] = self.cochran_match(
                    context.get("subject", {}),
                    context.get("intake_candidate", {}),
                )
            else:
                payload["cochran_result"] = {"status": "not_available"}

            if self.reverse_continuity_tool:
                try:
                    ok, log = self.reverse_continuity_tool.run_validation(
                        context.get("intake_summary", "") or "",
                        context.get("docs", []) or [],
                        context.get("assets_text", []) or [],
                    )
                    payload["reverse_continuity_result"] = {"ok": bool(ok), "log": log}
                except Exception as exc:  # pragma: no cover
                    payload["reverse_continuity_result"] = {"status": "error", "detail": str(exc)}
            else:
                payload["reverse_continuity_result"] = {"status": "not_available"}

            metadata_zip = context.get("metadata_zip")
            if callable(self.metadata_processor) and metadata_zip:
                output_dir = context.get("metadata_output_dir", "./metadata_out")
                try:
                    self.metadata_processor(metadata_zip, output_dir)
                    payload.setdefault("metadata_output_dir", output_dir)
                except Exception as exc:  # pragma: no cover
                    payload.setdefault("metadata_processor_error", str(exc))

            if callable(self.mileage_audit):
                try:
                    payload["mileage_audit"] = self.mileage_audit()
                except Exception as exc:  # pragma: no cover
                    payload["mileage_audit"] = {"status": "error", "detail": str(exc)}
            else:
                payload["mileage_audit"] = {"status": "not_available"}

            ocr_results = self._run_ocr_pipeline(evidence_assets)
            if ocr_results:
                payload["ocr_results"] = ocr_results

            case_id = context.get("case_id") or context.get("bus_state", {}).get("case_id")
            if case_id:
                payload["case_id"] = case_id

            payload["section_id"] = self.bus_section_id() or "section_1"
            for key in ("manifest_context", "section_needs", "evidence", "bus_state"):
                if context.get(key) is not None:
                    payload.setdefault(key, context[key])

            return payload

        except Exception as exc:  # pragma: no cover
            self.logger.exception("Failed to build payload for %s: %s", self.SECTION_ID, exc)
            self.emit_fault(FAULT_BUILD_PAYLOAD, detail=str(exc), context=context)
            return {"error": str(exc)}

    def publish(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Publish results to Gateway and emit section signals."""
        try:
            renderer = self.section_renderer
            narrative = ""
            if renderer:
                try:
                    render_model = renderer.render_model(section_payload=payload, case_sources={})
                    render_tree = render_model.get("render_tree", [])
                    lines = []
                    for block in render_tree:
                        if block.get("type") == "field":
                            label = block.get("label") or block.get("text")
                            lines.append(f"{label}: {block.get('value')}")
                        else:
                            text = block.get("text")
                            if text:
                                lines.append(str(text))
                    narrative = "\n".join(lines)
                except Exception as exc:  # pragma: no cover
                    self.logger.warning("Section renderer failed: %s", exc)
            if not narrative:
                narrative = f"Section 1 Profile: {payload.get('client_name', 'Unknown Client')}"

            section_bus_id = self.bus_section_id() or "section_1"
            timestamp = datetime.now().isoformat()
            summary = (narrative.splitlines() or [""])[0][:320]

            result = {
                "section_id": section_bus_id,
                "case_id": payload.get("case_id"),
                "payload": payload,
                "manifest": payload,
                "narrative": narrative,
                "summary": summary,
                "metadata": {
                    "published_at": timestamp,
                    "section": self.SECTION_ID,
                },
                "source": "section_1_framework",
            }

            if hasattr(self.gateway, "publish_section_result"):
                self.gateway.publish_section_result(section_bus_id, result)
            if hasattr(self.gateway, "emit"):
                emit_payload = dict(payload)
                emit_payload.setdefault("published_at", timestamp)
                emit_payload.setdefault("section_id", section_bus_id)
                self.gateway.emit("case_metadata_ready", emit_payload)

            return {"status": "published", "narrative": narrative, "manifest": payload}

        except Exception as exc:  # pragma: no cover
            self.logger.exception("Failed to publish for %s: %s", self.SECTION_ID, exc)
            self.emit_fault(FAULT_PUBLISH, detail=str(exc), context=payload)
            self.emit_mayday("Section 1 publish failure", fault_code=FAULT_PUBLISH, context=payload)
            return {"error": str(exc)}

    def _run_ocr_pipeline(self, evidence_assets: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute hierarchical OCR across evidence assets."""

        results: Dict[str, Any] = {}
        if not evidence_assets:
            return results

        for asset in evidence_assets:
            evidence_id = asset.get("id")
            file_path = asset.get("file_path")
            file_type = (asset.get("evidence_type") or "").lower()
            if not evidence_id or not file_path:
                continue

            path_obj = Path(file_path)
            if not path_obj.exists():
                results[evidence_id] = {"status": "not_found"}
                continue

            engine_sequence: List[str] = []
            text_blocks: List[Dict[str, Any]] = []
            aggregate_text: List[str] = []

            # Primary: Unstructured for documents/PDFs
            if self.unstructured_engine:
                try:
                    partitions = self.unstructured_engine.partition(str(path_obj))
                    if partitions:
                        engine_sequence.append("unstructured")
                        for entry in partitions:
                            text = entry.get("text")
                            if not text:
                                continue
                            text_blocks.append(
                                {
                                    "text": text,
                                    "category": entry.get("category"),
                                    "engine": "unstructured",
                                }
                            )
                            aggregate_text.append(text)
                except Exception as exc:  # pragma: no cover
                    self.logger.warning("Unstructured OCR failed for %s: %s", path_obj, exc)

            image_types = {"jpg", "jpeg", "png", "tif", "tiff", "bmp"}

            # Secondary: Tesseract for image assets or if unstructured produced nothing
            if not text_blocks and self.tesseract_engine and (file_type in image_types or path_obj.suffix.lower().lstrip(".") in image_types):
                try:
                    tesseract_output = self.tesseract_engine.extract_text(str(path_obj))
                    engine_sequence.append("tesseract")
                    text_blocks.extend(
                        {
                            "text": block.get("text"),
                            "confidence": block.get("confidence"),
                            "engine": "tesseract",
                        }
                        for block in tesseract_output.get("text_blocks", [])
                        if block.get("text")
                    )
                    aggregate_text.append(tesseract_output.get("text", ""))
                except Exception as exc:  # pragma: no cover
                    self.logger.warning("Tesseract OCR failed for %s: %s", path_obj, exc)

            # Fallback: EasyOCR if still nothing
            if not text_blocks and self.easyocr_engine and path_obj.is_file():
                try:
                    easy_output = self.easyocr_engine.extract_text(str(path_obj))
                    engine_sequence.append("easyocr")
                    text_blocks.extend(
                        {
                            "text": block.get("text"),
                            "confidence": block.get("confidence"),
                            "engine": "easyocr",
                        }
                        for block in easy_output.get("text_blocks", [])
                        if block.get("text")
                    )
                    aggregate_text.append(easy_output.get("text", ""))
                except Exception as exc:  # pragma: no cover
                    self.logger.warning("EasyOCR failed for %s: %s", path_obj, exc)

            results[evidence_id] = {
                "engines_attempted": engine_sequence,
                "text_blocks": text_blocks,
                "text": " ".join(text for text in aggregate_text if text),
                "file_path": str(path_obj),
            }

        return results

    # ------------------------------------------------------------------
    # Revision handling
    # ------------------------------------------------------------------
    def handle_revision(self, reason: str, context: Dict[str, Any]) -> None:
        super().handle_revision(reason, context)
        if hasattr(self.gateway, "log_revision"):
            self.gateway.log_revision(self.SECTION_ID, reason, context)
