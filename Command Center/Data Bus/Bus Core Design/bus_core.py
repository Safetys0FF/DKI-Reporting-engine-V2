#!/usr/bin/env python3
"""
DKI Bus Core - Central Command Architecture
100% new Central Command design - no old architecture
"""

import os
import sys
import json
from datetime import datetime
import threading
import logging
from typing import Dict, List, Any, Optional, Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dki_bus_core.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class DKIReportBus:
    """Central Command Bus - Signal-based architecture"""

    def __init__(self) -> None:
        self.signal_registry: Dict[str, List[Callable[[Dict[str, Any]], Optional[Any]]]] = {}
        self.module_log: List[str] = []
        self.active_modules: Dict[str, Any] = {}
        self.event_log: List[Dict[str, Any]] = []
        self.lock = threading.Lock()

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

        logger.info("Central Command Bus initialized")

        # Register default signal handlers for core events
        self._register_default_handlers()

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
        }
        for signal_name, handler in default_handlers.items():
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
        handlers = self.signal_registry.get(topic)
        if not handlers:
            logger.warning(f"[BUS] No handlers for topic: {topic}")
            return {}
        responses: List[Any] = []
        for handler in handlers:
            try:
                response = handler(data)
            except Exception as exc:  # pragma: no cover
                logger.error(f"[BUS] Error running handler '{getattr(handler, '__name__', handler)}' for topic '{topic}': {exc}")
            else:
                if response is not None:
                    responses.append(response)
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

    def get_evidence_manifest(self, evidence_id: Optional[str] = None) -> Any:
        with self.lock:
            if evidence_id:
                entry = self.evidence_manifest.get(evidence_id)
                return dict(entry) if entry else {}
            return [dict(entry) for entry in self.evidence_manifest.values()]

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
    # Test the Central Command bus
    bus = DKIReportBus()
    
    # Inject Central Command modules
    inject_gateway_controller(bus)
    inject_evidence_manager(bus)
    inject_evidence_index(bus)
    
    # Test signals
    bus.emit("boot_check", {"status": "online"})
    
    print("Central Command Bus initialized successfully")
    print(f"Status: {bus.get_status()}")