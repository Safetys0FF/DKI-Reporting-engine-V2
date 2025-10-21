#!/usr/bin/env python3
"""
DKI Bus Core - Central Command Architecture
100% new Central Command design - no old architecture
Enhanced with Universal Communication Protocol
"""

import os
import sys
import json
import time
from datetime import datetime
import threading
import logging
from typing import Dict, List, Any, Optional, Callable
from universal_communicator import UniversalCommunicator, CommunicationSignal

# Import parent module registry for routing
try:
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / "diagnostic_manager" / "Unified_diagnostic_system" / "read_me"))
    from system_protocol_registry import PARENT_CHILD_RELATIONSHIPS
    PARENT_MODULES = set(PARENT_CHILD_RELATIONSHIPS.keys())
except ImportError:
    # Fallback if registry not available
    PARENT_MODULES = {'Bus-1', 'DIAG-1', '1', '2-1', '3', '5', 'GUI-1'}

# Message Lifecycle States for Universal Communication Protocol
class MessageState:
    """Defines the lifecycle states of bus messages to prevent infinite loops."""
    CALL_SENT = "CALL_SENT"           # Initiator sends request
    CALL_RECEIVED = "CALL_RECEIVED"   # Receiver ACKs receipt (optional)
    CALL_ANSWERED = "CALL_ANSWERED"   # Receiver sends response data
    CALL_COMPLETED = "CALL_COMPLETED" # Initiator confirms completion (optional)

# Configure logging - redirect to diagnostic system's system_logs directory
import pathlib
diagnostic_logs_path = pathlib.Path(__file__).parent.parent / "diagnostic_manager" / "Unified_diagnostic_system" / "library" / "system_logs"
diagnostic_logs_path.mkdir(parents=True, exist_ok=True)
bus_log_file = diagnostic_logs_path / "dki_bus_core.log"

# Use rotating file handler to prevent disk-full errors
from logging.handlers import RotatingFileHandler
logging.basicConfig(
    level=logging.WARNING,  # Reduced from INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(str(bus_log_file), maxBytes=10*1024*1024, backupCount=2),  # 10MB max
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class DKIReportBus:
    """Central Command Bus - Signal-based architecture with Universal Communication Protocol"""

    def __init__(self) -> None:
        self.signal_registry: Dict[str, List[Callable[[Dict[str, Any]], Optional[Any]]]] = {}
        self.module_log: List[str] = []
        self.active_modules: Dict[str, Any] = {}
        self.event_log: List[Dict[str, Any]] = []
        self.lock = threading.Lock()

        # Bus stabilization state
        self.bus_ready = False
        self.stabilization_time = 10  # seconds
        self.ready_event = threading.Event()
        
        # Registry file for UDS detection
        self.registry_path = Path(__file__).parent / "bus_registry.json"
        self.registry_update_interval = 5  # seconds
        self.last_registry_update = 0
        
        # Module initialization orchestration
        # NOTE: DIAG-1 and GUI-1 removed from sequence - launch after backend
        # Modules can initialize without waiting for optional components
        self.initialization_sequence = [
            'Bus-1',           # Central bus (self)
            # 'DIAG-1',        # Diagnostic system (launches later as subprocess)
            # 'GUI-1',         # User interface (optional, launches later)
            '1',               # Evidence Locker
            '2',               # The Warden
            '3',               # The Marshall
            '5',               # Mission Debrief
        ]
        self.initialized_modules: Dict[str, Dict[str, Any]] = {}
        self.initialization_complete = False

        # Central Command state
        self.current_case_id: Optional[str] = None
        self.current_case: Optional[Dict[str, Any]] = None
        self.case_metadata: Dict[str, Any] = {}
        self.uploaded_files: List[Any] = []
        self.section_data: Dict[str, Any] = {}
        self.report_type: str = "Investigative"
        self.evidence_manifest: Dict[str, Dict[str, Any]] = {}
        self.section_interests: Dict[str, Dict[str, Any]] = {}
        self.latest_status: Dict[str, Any] = {}
        self.case_snapshots: List[Dict[str, Any]] = []

        # Universal Communication Protocol
        self.communicator = UniversalCommunicator("Bus-1", bus_connection=self)
        self.system_addresses: Dict[str, Dict[str, Any]] = {}
        self.fault_log: List[Dict[str, Any]] = []
        self.active_faults: Dict[str, Dict[str, Any]] = {}

        # Health monitoring metrics
        self.start_time = datetime.now()
        self.message_count = 0
        self.failed_deliveries = 0
        self.processing_times: List[float] = []
        
        logger.info("Central Command Bus initializing - starting stabilization sequence")

        # Register default signal handlers for core events
        self._register_default_handlers()
        
        # Start stabilization sequence in background thread
        self.stabilization_thread = threading.Thread(target=self._stabilize, daemon=True)
        self.stabilization_thread.start()

    def _stabilize(self) -> None:
        """Stabilization sequence - allows bus to fully initialize before accepting connections."""
        logger.warning(f"[BUS-1] STABILIZATION IN PROGRESS - {self.stabilization_time}s countdown started")
        logger.warning(f"[BUS-1] All module connections will be gated until bus is ready")
        
        for remaining in range(self.stabilization_time, 0, -1):
            logger.info(f"[BUS-1] Stabilizing... {remaining}s remaining")
            time.sleep(1)
        
        # Set ready state
        self.bus_ready = True
        self.ready_event.set()
        
        # Mark Bus-1 as initialized
        self.initialized_modules['Bus-1'] = {
            'address': 'Bus-1',
            'status': 'initialized',
            'timestamp': datetime.now().isoformat()
        }
        
        # Update registry file
        self._update_registry_file()
        
        logger.warning("[BUS-1] [OK] STABILIZATION COMPLETE - Bus is now READY for connections")
        logger.info(f"[BUS-1] Ready state achieved at {datetime.now().isoformat()}")
        logger.info(f"[BUS-1] Module initialization sequence: {' -> '.join(self.initialization_sequence)}")
    
    def wait_for_ready(self, timeout: Optional[float] = 30.0) -> bool:
        """Block until bus is ready. Returns True if ready, False if timeout."""
        if self.bus_ready:
            return True
        
        logger.info(f"[BUS-1] Module waiting for bus ready state (timeout: {timeout}s)")
        ready = self.ready_event.wait(timeout=timeout)
        
        if ready:
            logger.info("[BUS-1] Bus ready confirmed - module can proceed")
        else:
            logger.error(f"[BUS-1] Bus ready timeout after {timeout}s - connection may be unstable")
        
        return ready
    
    def is_ready(self) -> bool:
        """Check if bus is ready without blocking."""
        return self.bus_ready
    
    def register_module_init(self, module_address: str, module_info: Optional[Dict[str, Any]] = None) -> bool:
        """Register a module as initialized in the orchestrated sequence.
        
        Returns True if module is allowed to initialize (its turn in sequence),
        False if it should wait for previous modules.
        """
        if not self.bus_ready:
            logger.warning(f"[BUS-1] Module {module_address} attempted registration before bus ready")
            return False
        
        # Find module position in sequence
        try:
            module_index = self.initialization_sequence.index(module_address)
        except ValueError:
            # Module not in sequence - allow immediate registration
            logger.info(f"[BUS-1] Module {module_address} not in sequence - allowing immediate registration")
            with self.lock:
                self.initialized_modules[module_address] = {
                    'address': module_address,
                    'status': 'initialized',
                    'timestamp': datetime.now().isoformat(),
                    'info': module_info or {}
                }
            # Update registry file
            self._update_registry_file()
            return True
        
        # Check if all previous modules in sequence are initialized
        with self.lock:
            for i in range(module_index):
                predecessor = self.initialization_sequence[i]
                if predecessor not in self.initialized_modules:
                    logger.warning(
                        f"[BUS-1] Module {module_address} must wait for {predecessor} to initialize first"
                    )
                    logger.info(f"[BUS-1] Initialization order: {' -> '.join(self.initialization_sequence[:module_index + 1])}")
                    return False
            
            # All predecessors ready - register this module
            self.initialized_modules[module_address] = {
                'address': module_address,
                'status': 'initialized',
                'timestamp': datetime.now().isoformat(),
                'sequence_position': module_index,
                'info': module_info or {}
            }
        
        # Update registry file
        self._update_registry_file()
        
        logger.warning(f"[BUS-1] [OK] Module {module_address} initialized (position {module_index + 1}/{len(self.initialization_sequence)})")
        
        # Check if all modules in sequence are now initialized
        if len(self.initialized_modules) >= len(self.initialization_sequence):
            self.initialization_complete = True
            logger.warning("[BUS-1] [OK] ALL CORE MODULES INITIALIZED - System ready for operation")
        
        return True
    
    def wait_for_module_turn(self, module_address: str, timeout: float = 60.0) -> bool:
        """Block until it's this module's turn to initialize in the sequence.
        
        Returns True when ready to initialize, False on timeout.
        """
        if not self.bus_ready:
            logger.info(f"[{module_address}] Waiting for bus stabilization...")
            if not self.wait_for_ready(timeout=timeout):
                return False
        
        try:
            module_index = self.initialization_sequence.index(module_address)
        except ValueError:
            # Not in sequence - can initialize immediately
            return True
        
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            # Check if all predecessors are initialized
            all_ready = True
            with self.lock:
                for i in range(module_index):
                    predecessor = self.initialization_sequence[i]
                    if predecessor not in self.initialized_modules:
                        all_ready = False
                        break
            
            if all_ready:
                logger.info(f"[{module_address}] All predecessors initialized - ready to proceed")
                return True
            
            # Wait and check again
            time.sleep(0.5)
        
        logger.error(f"[{module_address}] Timeout waiting for initialization turn after {timeout}s")
        return False
    
    def get_initialization_status(self) -> Dict[str, Any]:
        """Get current initialization status for all modules in sequence."""
        with self.lock:
            status = {
                'bus_ready': self.bus_ready,
                'initialization_complete': self.initialization_complete,
                'sequence': self.initialization_sequence,
                'initialized_count': len(self.initialized_modules),
                'total_count': len(self.initialization_sequence),
                'modules': {}
            }
            
            for module_addr in self.initialization_sequence:
                if module_addr in self.initialized_modules:
                    status['modules'][module_addr] = self.initialized_modules[module_addr]
                else:
                    status['modules'][module_addr] = {
                        'address': module_addr,
                        'status': 'waiting',
                        'timestamp': None
                    }
        
        return status

    def _register_default_handlers(self) -> None:
        """Ensure core signals always have at least a logging stub."""
        default_handlers = {
            'case_create': self._handle_case_create_signal,
            'files_add': self._handle_files_add_signal,
            'evidence.new': self._handle_evidence_new_signal,
            'evidence.annotated': self._handle_evidence_annotated_signal,
            'evidence.request': self._handle_evidence_request_signal,
            'evidence.deliver': self._handle_evidence_deliver_signal,
            'evidence.updated': self._handle_evidence_updated_signal,
            'evidence.tagged': self._handle_evidence_tagged_signal,
            'evidence.stored': self._handle_evidence_stored_signal,
            'evidence_locker.call_out': self._handle_evidence_call_out_signal,
            'evidence_locker.accept': self._handle_evidence_accept_signal,
            'section.needs': self._handle_section_needs_signal,
            'case.snapshot': self._handle_case_snapshot_signal,
            'gateway.status': self._handle_gateway_status_signal,
            'locker.status': self._handle_locker_status_signal,
            'mission.status': self._handle_mission_status_signal,
            'narrative.assembled': self._handle_narrative_assembled_signal,
            # Universal Communication Protocol handlers
            'sos_fault': self._handle_sos_fault_signal,
            'radio_check': self._handle_radio_check_signal,
            'rollcall': self._handle_rollcall_signal,
            'status_request': self._handle_status_request_signal,
            'auto_registration': self._handle_auto_registration_signal,
            'communication': self._handle_communication_signal,  # FIX: Register generic communication handler
        }
        for signal_name, handler in default_handlers.items():
            self.register_signal(signal_name, handler)
    
    def _register_universal_protocol_handlers(self) -> None:
        """Register Universal Communication Protocol handlers on THIS bus instance."""
        # These handlers MUST be registered on every bus instance
        # because modules create their own bus instances
        protocol_handlers = {
            'communication': self._handle_communication_signal,
            'report.generate': self._handle_report_generate_signal,
            'report.status': self._handle_report_status_signal,
        }
        for signal_name, handler in protocol_handlers.items():
            self.register_signal(signal_name, handler)

    # ------------------------------------------------------------------
    # Default signal handlers
    # ------------------------------------------------------------------
    def _handle_case_create_signal(self, payload: Dict[str, Any]) -> None:
        case_id = payload.get('case_id') or payload.get('id')
        case_info = payload.get('case_info') or {}
        if case_id:
            self.current_case_id = case_id
        if isinstance(case_info, dict):
            self.case_metadata.update(case_info)
        self.log_event('bus.case_create', f"Case created via signal: {case_id or '<unknown>'}")

    def _handle_files_add_signal(self, payload: Dict[str, Any]) -> None:
        files = payload.get('files')
        if isinstance(files, dict):
            files_iter = list(files.values())
        elif isinstance(files, (list, tuple, set)):
            files_iter = list(files)
        elif files:
            files_iter = [files]
        else:
            files_iter = []
        if files_iter:
            self.uploaded_files = files_iter
        self.log_event('bus.files_add', f"{len(files_iter)} file(s) announced via signal")

    def _handle_evidence_new_signal(self, payload: Dict[str, Any]) -> None:
        evidence_id = payload.get('evidence_id') or payload.get('artifact_id') or payload.get('id')
        timestamp = payload.get('timestamp') or datetime.now().isoformat()
        if evidence_id:
            self._upsert_manifest(evidence_id, payload, 'evidence.new', timestamp)
        self.log_event('bus.evidence_new', f"Evidence announced: {evidence_id or '<unknown>'}")

    def _handle_evidence_annotated_signal(self, payload: Dict[str, Any]) -> None:
        evidence_id = payload.get('evidence_id') or payload.get('artifact_id') or payload.get('id')
        timestamp = payload.get('timestamp') or datetime.now().isoformat()
        if evidence_id:
            self._upsert_manifest(evidence_id, payload, 'evidence.annotated', timestamp)
        self.log_event('bus.evidence_annotated', f"Evidence annotated: {evidence_id or '<unknown>'}")

    def _handle_evidence_request_signal(self, payload: Dict[str, Any]) -> None:
        evidence_id = payload.get('evidence_id') or payload.get('artifact_id') or payload.get('id')
        requester = payload.get('section_id') or payload.get('requester') or 'unspecified'
        timestamp = payload.get('timestamp') or datetime.now().isoformat()
        if evidence_id:
            with self.lock:
                entry = dict(self.evidence_manifest.get(evidence_id, {'evidence_id': evidence_id}))
                requests = entry.setdefault('requests', [])
                requests.append({'requester': requester, 'timestamp': timestamp})
                entry['last_event'] = 'evidence.request'
                entry['last_updated'] = timestamp
                self.evidence_manifest[evidence_id] = entry
        self.log_event('bus.evidence_request', f"Evidence {evidence_id or '<unknown>'} requested by {requester}")

    def _handle_evidence_deliver_signal(self, payload: Dict[str, Any]) -> None:
        evidence_id = payload.get('evidence_id') or payload.get('artifact_id') or payload.get('id')
        recipient = payload.get('section_id') or payload.get('recipient') or 'unspecified'
        timestamp = payload.get('timestamp') or datetime.now().isoformat()
        if evidence_id:
            with self.lock:
                entry = dict(self.evidence_manifest.get(evidence_id, {'evidence_id': evidence_id}))
                deliveries = entry.setdefault('deliveries', [])
                deliveries.append({'recipient': recipient, 'timestamp': timestamp})
                entry['last_event'] = 'evidence.deliver'
                entry['last_updated'] = timestamp
                self.evidence_manifest[evidence_id] = entry
        self.log_event('bus.evidence_deliver', f"Evidence {evidence_id or '<unknown>'} delivered to {recipient}")
        try:
            section_hint = payload.get('section_id') or payload.get('section_hint') or recipient
            if section_hint:
                request_payload = {
                    'section_id': section_hint,
                    'section': section_hint,
                    'case_id': payload.get('case_id') or self.current_case_id,
                    'evidence_id': evidence_id,
                    'timestamp': timestamp,
                }
                self.send('narrative.generate', request_payload)
        except Exception as exc:
            logger.warning(f"Narrative request failed for evidence {evidence_id}: {exc}")

    def _handle_evidence_updated_signal(self, payload: Dict[str, Any]) -> None:
        evidence_id = payload.get('evidence_id') or payload.get('artifact_id') or payload.get('id')
        timestamp = payload.get('timestamp') or datetime.now().isoformat()
        if evidence_id:
            self._upsert_manifest(evidence_id, payload, 'evidence.updated', timestamp)
        self.log_event('bus.evidence_updated', f"Evidence updated: {evidence_id or '<unknown>'}")

    def _handle_evidence_tagged_signal(self, payload: Dict[str, Any]) -> None:
        evidence_id = payload.get('evidence_id') or payload.get('artifact_id')
        evidence_type = payload.get('artifact_type')
        timestamp = payload.get('timestamp') or datetime.now().isoformat()
        if evidence_id:
            self._upsert_manifest(evidence_id, payload, 'evidence.tagged', timestamp)
        message = f"Evidence tagged: {evidence_id or '<unknown>'}"
        if evidence_type:
            message += f" ({evidence_type})"
        self.log_event('bus.evidence_tagged', message)

    def _handle_evidence_stored_signal(self, payload: Dict[str, Any]) -> None:
        evidence_id = payload.get('evidence_id') or payload.get('artifact_id')
        inbox = payload.get('inbox')
        timestamp = payload.get('timestamp') or datetime.now().isoformat()
        if evidence_id:
            self._upsert_manifest(evidence_id, payload, 'evidence.stored', timestamp)
        message = f"Evidence stored: {evidence_id or '<unknown>'}"
        if inbox:
            message += f" -> {inbox}"
        self.log_event('bus.evidence_stored', message)

    def _handle_evidence_call_out_signal(self, payload: Dict[str, Any]) -> None:
        operation = payload.get('operation') or 'unspecified'
        request_id = payload.get('request_id') or f"auto_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        timestamp = payload.get('timestamp') or datetime.now().isoformat()
        self.log_event('bus.evidence_call_out', f"Call-out '{operation}' acknowledged (request {request_id})", level='warning')
        payload = dict(payload)
        payload.setdefault('request_id', request_id)
        payload.setdefault('timestamp', timestamp)
        self.latest_status['locker_call_out'] = payload

    def _handle_evidence_accept_signal(self, payload: Dict[str, Any]) -> None:
        operation = payload.get('operation') or 'unspecified'
        request_id = payload.get('request_id')
        timestamp = payload.get('timestamp') or datetime.now().isoformat()
        message = f"Accept signal received for operation '{operation}'"
        if request_id:
            message += f" (request {request_id})"
        self.log_event('bus.evidence_accept', message)
        payload = dict(payload)
        payload.setdefault('timestamp', timestamp)
        self.latest_status['locker_accept'] = payload

    def _handle_section_needs_signal(self, payload: Dict[str, Any]) -> None:
        section_id = payload.get('section_id') or payload.get('section') or 'unspecified'
        timestamp = payload.get('timestamp') or datetime.now().isoformat()
        record = dict(payload)
        record.setdefault('timestamp', timestamp)
        with self.lock:
            self.section_interests[section_id] = record
        needs_desc = record.get('topics') or record.get('tags') or record.get('filters') or 'requirements posted'
        self.log_event('bus.section_needs', f"Section {section_id} advertised needs: {needs_desc}")

    def _handle_case_snapshot_signal(self, payload: Dict[str, Any]) -> None:
        timestamp = payload.get('timestamp') or datetime.now().isoformat()
        snapshot = dict(payload)
        snapshot.setdefault('timestamp', timestamp)
        with self.lock:
            self.case_snapshots.append(snapshot)
        case_id = snapshot.get('case_id') or self.current_case_id or '<unknown>'
        self.log_event('bus.case_snapshot', f"Snapshot recorded for case {case_id}")

    def _record_status(self, component: str, payload: Dict[str, Any]) -> None:
        timestamp = payload.get('timestamp') or datetime.now().isoformat()
        status = dict(payload)
        status.setdefault('timestamp', timestamp)
        with self.lock:
            self.latest_status[component] = status
        summary = status.get('status') or status.get('state') or 'updated'
        self.log_event(f'bus.{component}_status', f"{component.title()} status: {summary}")

    def _handle_gateway_status_signal(self, payload: Dict[str, Any]) -> None:
        self._record_status('gateway', payload)

    def _handle_locker_status_signal(self, payload: Dict[str, Any]) -> None:
        self._record_status('locker', payload)

    def _handle_mission_status_signal(self, payload: Dict[str, Any]) -> None:

        self._record_status('mission', payload)
    def _handle_narrative_assembled_signal(self, payload: Dict[str, Any]) -> None:
        if not isinstance(payload, dict):
            return
        section_id = payload.get('section_id')
        if not section_id:
            self.log_event('bus.narrative', 'narrative.assembled missing section_id', 'warning')
            return
        case_id = payload.get('case_id')
        timestamp = payload.get('assembled_at') or payload.get('timestamp') or datetime.now().isoformat()
        with self.lock:
            existing = self.section_data.get(section_id) if isinstance(self.section_data, dict) else None
            merged = dict(existing) if isinstance(existing, dict) else {'section_id': section_id}
            structured = payload.get('structured_data')
            if isinstance(structured, dict):
                merged['structured_data'] = structured
            narrative_text = payload.get('narrative')
            if narrative_text is not None:
                merged['narrative'] = narrative_text
            draft_text = payload.get('draft') if payload.get('draft') is not None else narrative_text
            if draft_text is not None:
                merged['draft'] = draft_text
            summary = payload.get('summary')
            if summary is not None:
                merged['narrative_summary'] = summary
                if summary and not merged.get('summary'):
                    merged['summary'] = summary
            auto_narrative = payload.get('auto_narrative')
            if auto_narrative is not None:
                merged['auto_narrative'] = auto_narrative
            merged['narrative_id'] = payload.get('narrative_id')
            merged['case_id'] = case_id or merged.get('case_id') or self.current_case_id
            merged['priority'] = payload.get('priority') or merged.get('priority')
            merged['narrative_generated_at'] = timestamp
            merged['draft_generated_at'] = payload.get('draft_generated_at') or timestamp
            status = payload.get('status')
            if status:
                merged['status'] = status
            elif narrative_text and not merged.get('status'):
                merged['status'] = 'Draft Ready'
            source = payload.get('source')
            if source:
                merged['source'] = source
            self.section_data[section_id] = merged
        self.log_event('bus.narrative', f"Narrative assembled for {section_id}")

    # ------------------------------------------------------------------
    # Universal Communication Protocol handlers
    # ------------------------------------------------------------------
    def _handle_sos_fault_signal(self, payload: Dict[str, Any]) -> None:
        """Handle SOS fault signals"""
        fault_code = payload.get('fault_code', 'UNKNOWN')
        description = payload.get('description', 'Unknown fault')
        reporting_address = payload.get('caller_address', 'UNKNOWN')
        
        # Log fault
        fault_entry = {
            'fault_code': fault_code,
            'description': description,
            'reporting_address': reporting_address,
            'timestamp': datetime.now().isoformat(),
            'status': 'active'
        }
        
        with self.lock:
            self.fault_log.append(fault_entry)
            self.active_faults[reporting_address] = fault_entry
        
        # Route to GUI Error Display Interface
        self.send('gui_error_alert', {
            'fault_code': fault_code,
            'description': description,
            'reporting_address': reporting_address,
            'timestamp': datetime.now().isoformat()
        })
        
        self.log_event('bus.sos_fault', f"SOS fault from {reporting_address}: {fault_code} - {description}", 'error')

    def _handle_radio_check_signal(self, payload: Dict[str, Any]) -> None:
        """Handle radio check signals
        
        LIFECYCLE FIX: Only responds to CALL_SENT messages.
        """
        # Check message lifecycle state
        message_state = payload.get('message_state', '')
        if message_state != "CALL_SENT":
            return
        
        target_address = payload.get('target_address', 'UNKNOWN')
        caller_address = payload.get('caller_address', 'UNKNOWN')
        
        self.log_event('bus.radio_check', f"Radio check from {caller_address} to {target_address}")
        
        # Send acknowledgment response with CALL_ANSWERED state
        if self.communicator:
            connectivity_data = {
                "system_address": "Bus-1",
                "latency_ms": 0,
                "bus_connected": True,
                "timestamp": datetime.now().isoformat()
            }
            try:
                self.communicator.send_radio_check_response(caller_address, connectivity_data)
                logger.info(f"[Bus-1] Radio check response sent to {caller_address}")
            except Exception as exc:
                logger.error(f"[Bus-1] Radio check response failed: {exc}")

    def _handle_auto_registration_signal(self, payload: Dict[str, Any]) -> None:
        """Handle UDS auto-registration demand.
        
        LIFECYCLE FIX: Only responds to CALL_SENT messages to prevent infinite loops.
        """
        # Check message lifecycle state - only respond to requests
        message_state = payload.get('message_state', '')
        if message_state != "CALL_SENT":
            return
        
        logger.info("[Bus-1] Auto-registration request received from UDS")
        
        if not self.communicator:
            logger.warning("[Bus-1] Cannot respond - no communicator available")
            return
        
        # Build registration response payload
        response_payload = {
            "system_address": "Bus-1",
            "system_type": "central_command_bus",
            "status": "OPERATIONAL",
            "capabilities": ["message_routing", "signal_distribution", "event_logging", "system_state_management"],
            "child_components": ["Bus-1.1", "Bus-1.2", "Bus-1.3", "Bus-1.4", "Bus-1.5"],
            "compliance_status": "COMPLIANT",
            "protocol_version": "1.0.0",
            "timestamp": datetime.now().isoformat()
        }
        
        # Send response using UniversalCommunicator
        try:
            self.communicator.send_auto_registration_response("DIAG-1", response_payload)
            logger.info("[Bus-1] Auto-registration response sent to UDS")
        except Exception as exc:
            logger.error(f"[Bus-1] Auto-registration response failed: {exc}")
    
    def _handle_communication_signal(self, payload: Dict[str, Any]) -> None:
        """Handle generic communication signals from Universal Communicator.
        
        This is the main handler for inter-module messages sent via UniversalCommunicator.
        Routes messages based on radio_code and target_address.
        """
        radio_code = payload.get('radio_code', '10-4')
        caller_address = payload.get('caller_address', 'UNKNOWN')
        target_address = payload.get('target_address', 'ALL')
        message = payload.get('message', '')
        
        # Log communication
        logger.debug(f"[BUS] Communication: {caller_address} -> {target_address} [{radio_code}]: {message}")
        
        # Route to specific handlers based on radio code or just log
        # Future: Add routing logic here for specific message types
        return
    
    def _handle_report_generate_signal(self, payload: Dict[str, Any]) -> None:
        """Handle report generation requests."""
        # Stub handler - actual report generation handled by Mission Debrief module
        logger.debug(f"[BUS] Report generation request received: {payload}")
        return
    
    def _handle_report_status_signal(self, payload: Dict[str, Any]) -> None:
        """Handle report status requests."""
        # Stub handler - actual status provided by Mission Debrief module
        logger.debug(f"[BUS] Report status request received: {payload}")
        return
    
    def _handle_rollcall_signal(self, payload: Dict[str, Any]) -> None:
        """Handle rollcall signals"""
        caller_address = payload.get('caller_address', 'UNKNOWN')
        
        self.log_event('bus.rollcall', f"Rollcall initiated by {caller_address}")
        
        # Send status response
        self.send('rollcall_response', {
            'target_address': caller_address,
            'caller_address': 'Bus-1',
            'radio_code': '10-4',
            'message': 'Bus-1 operational',
            'timestamp': datetime.now().isoformat()
        })

    def _handle_status_request_signal(self, payload: Dict[str, Any]) -> None:
        """Handle status request signals"""
        caller_address = payload.get('caller_address', 'UNKNOWN')
        
        self.log_event('bus.status_request', f"Status request from {caller_address}")
        
        # Send status response
        self.send('status_response', {
            'target_address': caller_address,
            'caller_address': 'Bus-1',
            'radio_code': '10-4',
            'message': 'Bus-1 status: operational',
            'timestamp': datetime.now().isoformat(),
            'status': 'ACTIVE'
        })

    def route_signal(self, signal: CommunicationSignal) -> Dict[str, Any]:
        """Route signal using universal communication protocol"""
        try:
            # Log signal
            self.communicator.communication_log.append(signal)
            
            # Route to target
            if signal.target_address == "Bus-1":
                return self._handle_bus_signal(signal)
            else:
                return self._route_to_target(signal)
                
        except Exception as e:
            # Send SOS fault
            fault_code = f"Bus-1-20-{self._get_line_number()}"
            self.communicator.send_sos_fault(
                fault_code=fault_code,
                description=f"Signal routing error: {str(e)}",
                details={"signal": signal, "error": str(e)}
            )
            raise

    def broadcast_rollcall(self) -> Dict[str, Any]:
        """Broadcast rollcall to all systems"""
        rollcall_results = {}
        
        for address in self.system_addresses.keys():
            if address != "Bus-1":
                response = self.communicator.send_signal(
                    target_address=address,
                    radio_code="ROLLCALL",
                    message=f"Rollcall to {address}",
                    payload={"operation": "rollcall"},
                    timeout=60
                )
                rollcall_results[address] = response
        
        return rollcall_results

    def register_system_address(self, address: str, system_info: Dict[str, Any]) -> None:
        """Register system address for communication"""
        with self.lock:
            self.system_addresses[address] = system_info
        self.log_event('bus.register_address', f"Registered system address: {address}")
        
        # Update registry file for UDS detection
        self._update_registry_file()

    def get_registered_addresses(self) -> List[str]:
        """Get list of registered system addresses"""
        with self.lock:
            return list(self.system_addresses.keys())
    
    def _update_registry_file(self) -> None:
        """Update registry file for UDS detection (throttled)"""
        current_time = time.time()
        if current_time - self.last_registry_update < self.registry_update_interval:
            return
        
        self.last_registry_update = current_time
        
        try:
            with self.lock:
                registry_data = {
                    'timestamp': datetime.now().isoformat(),
                    'systems': {}
                }
                
                # Add all registered systems
                for address, info in self.system_addresses.items():
                    registry_data['systems'][address] = {
                        'address': address,
                        'status': 'active',
                        'registered_at': info.get('registered_at', datetime.now().isoformat()),
                        'system_type': info.get('system_type', 'unknown')
                    }
                
                # Add initialized modules
                for address, info in self.initialized_modules.items():
                    if address not in registry_data['systems']:
                        registry_data['systems'][address] = {
                            'address': address,
                            'status': info.get('status', 'initialized'),
                            'initialized_at': info.get('timestamp', datetime.now().isoformat()),
                            'system_type': 'module'
                        }
            
            # Write to file atomically
            import tempfile
            temp_path = str(self.registry_path) + '.tmp'
            with open(temp_path, 'w') as f:
                json.dump(registry_data, f, indent=2)
            
            # Atomic rename
            import os
            os.replace(temp_path, str(self.registry_path))
            
            logger.debug(f"Registry file updated with {len(registry_data['systems'])} systems")
            
        except Exception as e:
            logger.warning(f"Failed to update registry file: {e}")

    def _get_line_number(self) -> int:
        """Get current line number for fault reporting"""
        import inspect
        frame = inspect.currentframe()
        caller_frame = frame.f_back.f_back if frame.f_back else frame
        return caller_frame.f_lineno

    def _handle_bus_signal(self, signal: CommunicationSignal) -> Dict[str, Any]:
        """Handle signals directed to the bus itself"""
        return {
            "signal_id": f"response_{signal.signal_id}",
            "caller_address": "Bus-1",
            "target_address": signal.caller_address,
            "radio_code": "10-4",
            "message": "Bus-1 acknowledged",
            "timestamp": datetime.now().isoformat()
        }

    def _route_to_target(self, signal: CommunicationSignal) -> Dict[str, Any]:
        """Route signal to target system"""
        # This would route to the actual target system
        # For now, return a simulated response
        return {
            "signal_id": f"response_{signal.signal_id}",
            "caller_address": signal.target_address,
            "target_address": signal.caller_address,
            "radio_code": "10-4",
            "message": f"{signal.target_address} acknowledged",
            "timestamp": datetime.now().isoformat()
        }

    def _upsert_manifest(self, evidence_id: str, payload: Dict[str, Any], event: str, timestamp: str) -> None:
        with self.lock:
            entry = dict(self.evidence_manifest.get(evidence_id, {'evidence_id': evidence_id}))
            entry.update(payload or {})
            entry['evidence_id'] = evidence_id
            entry['last_event'] = event
            entry['last_updated'] = timestamp
            self.evidence_manifest[evidence_id] = entry
    # ------------------------------------------------------------------
    # Core bus mechanics
    # ------------------------------------------------------------------
    def register_signal(self, signal: str, handler: Callable[[Dict[str, Any]], Optional[Any]]) -> None:
        signal_key = signal.strip()
        if not signal_key:
            raise ValueError('Signal name cannot be empty')
        if not callable(handler):
            raise TypeError('Handler must be callable')
        with self.lock:
            self.signal_registry.setdefault(signal_key, []).append(handler)
        logger.info(f"[BUS] Signal '{signal_key}' bound to {getattr(handler, '__name__', repr(handler))}")

    def subscribe(self, topic: str, handler: Callable[[Dict[str, Any]], Optional[Any]]) -> None:
        self.register_signal(topic, handler)

    def log_event(self, source: str, message: str, level: str = 'info') -> None:
        entry = {
            'timestamp': datetime.now().isoformat(),
            'source': source,
            'message': message,
            'level': level,
        }
        with self.lock:
            self.event_log.append(entry)
        log_fn = getattr(logger, level.lower(), logger.info)
        log_fn(f"[BUS][{source}] {message}")

    def get_event_log(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        with self.lock:
            if limit is None or limit >= len(self.event_log):
                return list(self.event_log)
            return self.event_log[-limit:]

    def send(self, topic: str, data: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()
        self.message_count += 1
        
        handlers = self.signal_registry.get(topic)
        if not handlers:
            logger.warning(f"[BUS] No handlers for topic: {topic}")
            self.failed_deliveries += 1
            return {}
        
        # Check if message has target address - only deliver to parent modules
        target_address = data.get('target_address')
        if target_address and target_address not in PARENT_MODULES:
            # Child address targeted - skip delivery (parent will handle)
            logger.debug(f"[BUS] Skipping delivery to child address {target_address} - parent handles")
            return {}
        
        responses: List[Any] = []
        for handler in handlers:
            try:
                response = handler(data)
            except Exception as exc:  # pragma: no cover
                logger.error(f"[BUS] Error running handler '{getattr(handler, '__name__', handler)}' for topic '{topic}': {exc}")
                self.failed_deliveries += 1
            else:
                if response is not None:
                    responses.append(response)
        
        # Track processing time
        processing_time = (time.time() - start_time) * 1000  # ms
        self.processing_times.append(processing_time)
        if len(self.processing_times) > 1000:
            self.processing_times = self.processing_times[-1000:]
        
        if not responses:
            return {}
        if len(responses) == 1 and isinstance(responses[0], dict):
            return responses[0]
        return {'responses': responses}

    def emit(self, signal: str, payload: Dict[str, Any]) -> None:
        handlers = self.signal_registry.get(signal)
        if not handlers:
            logger.warning(f"[BUS] No handlers for signal: {signal}")
            return
        for handler in handlers:
            try:
                handler(payload)
            except Exception as exc:  # pragma: no cover
                logger.error(f"[BUS] Error running handler '{getattr(handler, '__name__', handler)}': {exc}")

    def inject_module(self, module: Any) -> None:
        if hasattr(module, 'initialize'):
            module.initialize(self)
            self.module_log.append(module.__name__)
            self.active_modules[module.__name__] = module
            logger.info(f"[BUS] Module '{module.__name__}' initialized")
        else:
            logger.warning(f"[BUS] Module '{module.__name__}' missing 'initialize()'")

    # ------------------------------------------------------------------
    # Convenience helpers used by Central Command workflows
    # ------------------------------------------------------------------
    def authenticate_user(self, username: str, password: str) -> bool:
        self.emit('user_authenticate', {
            'username': username,
            'password': password,
            'timestamp': datetime.now().isoformat(),
        })
        return True

    def create_user(self, username: str, password: str, role: str = 'agent') -> bool:
        self.emit('user_create', {
            'username': username,
            'password': password,
            'role': role,
            'timestamp': datetime.now().isoformat(),
        })
        return True

    def new_case(self, case_info: Dict[str, Any]) -> str:
        self.current_case_id = f"CASE_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.case_metadata = case_info.copy()
        self.report_type = case_info.get('report_type', 'Investigative')
        self.uploaded_files = []
        self.section_data = {}
        self.emit('case_create', {
            'case_id': self.current_case_id,
            'case_info': case_info,
            'timestamp': datetime.now().isoformat(),
        })
        logger.info(f"New case created: {self.current_case_id}")
        return self.current_case_id

    def add_files(self, files: List[str]) -> bool:
        self.uploaded_files = list(files)
        self.emit('files_add', {
            'case_id': self.current_case_id,
            'files': list(files),
            'timestamp': datetime.now().isoformat(),
        })
        logger.info(f"Added {len(files)} files to case")
        return True

    def process_files(self) -> Dict[str, Any]:
        if not self.uploaded_files:
            logger.warning('No files to process')
            return {}
        self.emit('files_process', {
            'case_id': self.current_case_id,
            'files': list(self.uploaded_files),
            'timestamp': datetime.now().isoformat(),
        })
        processed_data = {
            'files_processed': len(self.uploaded_files),
            'processing_timestamp': datetime.now().isoformat(),
            'status': 'completed',
        }
        self.section_data['processed_files'] = processed_data
        logger.info(f"Processed {len(self.uploaded_files)} files")
        return processed_data

    def generate_section(self, section_name: str) -> Dict[str, Any]:
        self.emit('section_generate', {
            'case_id': self.current_case_id,
            'section_name': section_name,
            'report_type': self.report_type,
            'timestamp': datetime.now().isoformat(),
        })
        section_result = {
            'section_name': section_name,
            'content': f"Generated content for {section_name}",
            'timestamp': datetime.now().isoformat(),
            'status': 'completed',
        }
        self.section_data[section_name] = section_result
        logger.info(f"{section_name} generated successfully")
        return section_result

    def generate_full_report(self) -> Dict[str, Any]:
        if not self.section_data:
            logger.warning('No section data available')
            return {}
        self.emit('report_generate_full', {
            'case_id': self.current_case_id,
            'sections': list(self.section_data.keys()),
            'report_type': self.report_type,
            'timestamp': datetime.now().isoformat(),
        })
        report_result = {
            'case_id': self.current_case_id,
            'sections': self.section_data,
            'report_type': self.report_type,
            'generated_timestamp': datetime.now().isoformat(),
            'status': 'completed',
        }
        logger.info('Full report generated successfully')
        return report_result

    def export_report(self, report_data: Dict[str, Any], filename: str, format_type: str) -> bool:
        self.emit('report_export', {
            'case_id': self.current_case_id,
            'filename': filename,
            'format_type': format_type,
            'timestamp': datetime.now().isoformat(),
        })
        logger.info(f"Report exported: {filename}")
        return True

    def get_status(self) -> Dict[str, Any]:
        return {
            'current_case_id': self.current_case_id,
            'report_type': self.report_type,
            'uploaded_files_count': len(self.uploaded_files),
            'sections_generated': len(self.section_data),
            'active_modules': list(self.active_modules.keys()),
            'registered_signals': list(self.signal_registry.keys()),
            'event_log_size': len(self.event_log),
            'bus_status': 'online',
        }
    
    def get_health_metrics(self) -> Dict[str, Any]:
        """Get Bus-1 health monitoring metrics."""
        uptime = (datetime.now() - self.start_time).total_seconds()
        avg_processing = sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0
        msg_per_sec = self.message_count / uptime if uptime > 0 else 0
        
        return {
            'bus_address': 'Bus-1',
            'status': 'ready' if self.bus_ready else 'stabilizing',
            'bus_ready': self.bus_ready,
            'initialization_complete': self.initialization_complete,
            'initialized_modules': len(self.initialized_modules),
            'total_modules': len(self.initialization_sequence),
            'uptime_seconds': int(uptime),
            'message_count': self.message_count,
            'failed_deliveries': self.failed_deliveries,
            'messages_per_second': round(msg_per_sec, 2),
            'avg_processing_ms': round(avg_processing, 2),
            'connected_systems': len(self.system_addresses),
            'active_signals': len(self.signal_registry),
            'event_log_size': len(self.event_log)
        }

    def get_evidence_manifest(self, evidence_id: Optional[str] = None) -> Any:
        with self.lock:
            if evidence_id:
                entry = self.evidence_manifest.get(evidence_id)
                return dict(entry) if entry else {}
            return [dict(entry) for entry in self.evidence_manifest.values()]

    def get_section_data(self, section_id: Optional[str] = None) -> Any:
        with self.lock:
            if section_id:
                entry = self.section_data.get(section_id)
                if isinstance(entry, dict):
                    return dict(entry)
                return entry
            return {sid: (dict(data) if isinstance(data, dict) else data) for sid, data in self.section_data.items()}

    def get_section_interests(self) -> Dict[str, Any]:
        with self.lock:
            return {section: dict(data) for section, data in self.section_interests.items()}

    def get_latest_status(self) -> Dict[str, Any]:
        with self.lock:
            return {component: dict(status) for component, status in self.latest_status.items()}

    def get_case_snapshots(self) -> List[Dict[str, Any]]:
        with self.lock:
            return [dict(snapshot) for snapshot in self.case_snapshots]

    def reset_for_new_case(self) -> None:
        self.emit('case_reset', {
            'timestamp': datetime.now().isoformat(),
        })
        self.current_case_id = None
        self.uploaded_files = []
        self.section_data = {}
        self.evidence_manifest.clear()
        self.section_interests.clear()
        self.latest_status.clear()
        self.case_snapshots.clear()
        logger.info('Reset for new case')

# Central Command Module Injection Functions
def inject_gateway_controller(bus):
    """Inject gateway controller module"""
    bus.register_signal("gateway_initialize", lambda p: logger.info(f"[GATEWAY] Initialized: {p}"))
    bus.register_signal("gateway_reset", lambda p: logger.info(f"[GATEWAY] Reset: {p}"))
    logger.info("[CENTRAL COMMAND] Gateway controller injected")

def inject_evidence_manager(bus):
    """Inject evidence manager module"""
    bus.register_signal("evidence_process", lambda p: logger.info(f"[EVIDENCE] Processed: {p}"))
    bus.register_signal("evidence_validate", lambda p: logger.info(f"[EVIDENCE] Validated: {p}"))
    logger.info("[CENTRAL COMMAND] Evidence manager injected")

def inject_evidence_index(bus):
    """Inject evidence index module"""
    bus.register_signal("index_update", lambda p: logger.info(f"[INDEX] Updated: {p}"))
    bus.register_signal("index_search", lambda p: logger.info(f"[INDEX] Search: {p}"))
    logger.info("[CENTRAL COMMAND] Evidence index injected")


if __name__ == "__main__":
    # Test the Central Command bus with stabilization and orchestration
    print("=" * 80)
    print("CENTRAL COMMAND BUS - STABILIZATION & ORCHESTRATION TEST")
    print("=" * 80)
    
    bus = DKIReportBus()
    
    print("\n[TEST] Bus created - checking ready state...")
    print(f"[TEST] Bus ready: {bus.is_ready()}")
    print(f"[TEST] Health metrics: {bus.get_health_metrics()}")
    
    print("\n[TEST] Waiting for bus to stabilize...")
    if bus.wait_for_ready(timeout=15.0):
        print("\n[TEST] [OK] Bus stabilization confirmed")
        print(f"\n[TEST] Initialization sequence: {' -> '.join(bus.initialization_sequence)}")
        
        # Simulate module initialization in sequence
        print("\n[TEST] Simulating module initialization sequence...")
        
        # DIAG-1 initializes
        print("\n[TEST] DIAG-1 requesting initialization...")
        if bus.register_module_init('DIAG-1', {'version': '1.0', 'type': 'diagnostic'}):
            print("[TEST] [OK] DIAG-1 initialized")
        
        # GUI-1 initializes
        print("\n[TEST] GUI-1 requesting initialization...")
        if bus.register_module_init('GUI-1', {'version': '1.0', 'type': 'interface'}):
            print("[TEST] [OK] GUI-1 initialized")
        
        # The Warden initializes
        print("\n[TEST] The Warden (3) requesting initialization...")
        if bus.register_module_init('3', {'version': '1.0', 'type': 'warden'}):
            print("[TEST] [OK] The Warden initialized")
        
        # Evidence Locker initializes
        print("\n[TEST] Evidence Locker (2-1) requesting initialization...")
        if bus.register_module_init('2-1', {'version': '1.0', 'type': 'evidence_locker'}):
            print("[TEST] [OK] Evidence Locker initialized")
        
        # Mission Debrief initializes
        print("\n[TEST] Mission Debrief (5) requesting initialization...")
        if bus.register_module_init('5', {'version': '1.0', 'type': 'mission_debrief'}):
            print("[TEST] [OK] Mission Debrief initialized")
        
        # The Marshall initializes
        print("\n[TEST] The Marshall (1) requesting initialization...")
        if bus.register_module_init('1', {'version': '1.0', 'type': 'marshall'}):
            print("[TEST] [OK] The Marshall initialized")
        
        # Check initialization status
        print("\n[TEST] Initialization Status:")
        init_status = bus.get_initialization_status()
        print(f"  Complete: {init_status['initialization_complete']}")
        print(f"  Modules: {init_status['initialized_count']}/{init_status['total_count']}")
        
        # Inject Central Command signal handlers
        inject_gateway_controller(bus)
        inject_evidence_manager(bus)
        inject_evidence_index(bus)
        
        # Test signals
        bus.emit("boot_check", {"status": "online"})
        
        print("\n[TEST] Central Command Bus fully operational")
        print(f"[TEST] Health: {bus.get_health_metrics()}")
    else:
        print("\n[TEST] [ERROR] Bus stabilization timeout - check logs")
    
    print("\n" + "=" * 80)
