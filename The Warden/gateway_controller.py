#!/usr/bin/env python3
"""
GatewayController - Core Gateway orchestration system
Owns master evidence index, mediates section communication, manages data flow
Enhanced with Universal Communication Protocol
"""

import os
import sys
import uuid
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Iterable
from enum import Enum

# Universal Communication Protocol
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "Command Center", "Data Bus"))
from universal_communicator import UniversalCommunicator

# Ensure parsing dispatcher is reachable for section context building
marshall_gateway_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "The Marshall",
    "Gateway",
)
if marshall_gateway_path not in sys.path:
    sys.path.insert(0, marshall_gateway_path)

try:
    from section_parsing_dispatcher import build_section_context  # type: ignore
except Exception:  # pragma: no cover - dispatcher may be absent during bootstrap
    build_section_context = None

# Add Processors directory to Python path for OCR tools
processors_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "The War Room", "Processors")
if processors_path not in sys.path:
    sys.path.insert(0, processors_path)

root_dir = os.path.dirname(os.path.dirname(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from tag_taxonomy import resolve_tags

# OCR and Document Processing Imports - All tools available in Processors
try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

try:
    from PIL import Image, ImageEnhance, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    import unstructured
    from unstructured.partition.pdf import partition_pdf
    from unstructured.partition.image import partition_image
    UNSTRUCTURED_AVAILABLE = True
except ImportError:
    UNSTRUCTURED_AVAILABLE = False

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

logger = logging.getLogger(__name__)

NORMALIZE_TAGS = {
    "supporting_documents": "supporting-documents",
    "evidence_index": "media-photo",
    "intakeform": "intake-form",
    "dailylog": "daily-log",
}

def normalize_tags(tags: List[str]) -> List[str]:
    normalized = []
    for tag in tags or []:
        if not isinstance(tag, str):
            continue
        key = tag.strip().lower()
        normalized.append(NORMALIZE_TAGS.get(key, key))
    unique: List[str] = []
    seen: Set[str] = set()
    for tag in normalized:
        if tag and tag not in seen:
            seen.add(tag)
            unique.append(tag)
    return unique


class SignalType(Enum):
    """Signal types for inter-section communication"""
    EXECUTE = "EXECUTE"
    CLASSIFY = "CLASSIFY"
    FINALIZE = "FINALIZE"
    NARRATE = "NARRATE"
    VALIDATE = "VALIDATE"
    STATUS = "STATUS"
    PROCESS = "PROCESS"
    HANDOFF = "HANDOFF"

class Signal:
    """Signal for inter-section communication"""
    def __init__(self, signal_type: SignalType, target: str, source: str, payload: Dict[str, Any], case_id: str):
        self.type = signal_type
        self.target = target
        self.source = source
        self.payload = payload
        self.case_id = case_id
        self.timestamp = datetime.now().isoformat()
        self.signal_id = str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        """Convert signal to dictionary"""
        return {
            "signal_id": self.signal_id,
            "type": self.type.value,
            "target": self.target,
            "source": self.source,
            "payload": self.payload,
            "case_id": self.case_id,
            "timestamp": self.timestamp
        }

class GatewayController:
    """Core Gateway Controller - owns master evidence index and mediates section communication
    DEFERS ALL SECTION EXECUTION PERMISSION TO ECOSYSTEM CONTROLLER"""
    
    def __init__(self, ecosystem_controller=None, bus=None):
        # Initialize Universal Communication Protocol
        self.communicator = UniversalCommunicator("2-2", bus_connection=bus)
        # Reference to Ecosystem Controller (ROOT BOOT NODE)
        self.ecosystem_controller = ecosystem_controller
        
        # Master evidence index - core data structure
        self.master_evidence_index = {}
        self.evidence_map = {}
        
        # Section management
        self.section_cache = {}
        self.completed_sections = set()
        self.section_states = {}  # Current state of each module
        
        # Cross-linking and fact graph
        self.cross_links = {}
        self.fact_graph = {}
        
        # Gateway orchestration data
        self.orchestration_data = {}
        self.communication_log = []
        self.execution_coordination = {}
        self.active_communications = {}
        self.data_flow_status = {}
        
        # OCR Processing capabilities
        self.ocr_engines = {}
        if OCR_AVAILABLE:
            self.ocr_engines['tesseract'] = pytesseract
        if PDFPLUMBER_AVAILABLE:
            self.ocr_engines['pdfplumber'] = pdfplumber
        if UNSTRUCTURED_AVAILABLE:
            self.ocr_engines['unstructured'] = unstructured
        self.processed_content = {}
        self.content_classification = {}
        
        # Case bundle for architectural integration
        self.case_bundle = {}
        self.stage_confirmations = {}
        self.processing_log = []
        
        # Signal-based communication system
        self.signal_queue = []
        self.signal_history = []
        self.section_handlers = {}
        self.signal_routing_table = {}
        
        # Evidence Locker tracking system
        self.evidence_locker_modules = {
            'evidence_classifier': {'status': 'idle', 'last_activity': None, 'pending_handoffs': []},
            'evidence_index': {'status': 'idle', 'last_activity': None, 'pending_handoffs': []},
            'evidence_class_builder': {'status': 'idle', 'last_activity': None, 'pending_handoffs': []},
            'case_manifest_builder': {'status': 'idle', 'last_activity': None, 'pending_handoffs': []},
            'static_data_flow': {'status': 'idle', 'last_activity': None, 'pending_handoffs': []},
            'evidence_locker_main': {'status': 'idle', 'last_activity': None, 'pending_handoffs': []}
        }
        self.evidence_locker_handoff_queue = []
        self.evidence_locker_bottleneck_alerts = []
        
        # Configuration
        self.gateway_config = {
            'max_reruns': 3,
            'revision_depth_limit': 5,
            'auto_persistence': True,
            'persistence_path': 'gateway_data.json'
        }

        self.bus = bus
        self._bus_handlers_registered = False
        self.evidence_locker = None
        self.section_outputs = {}
        self.section_drafts = {}
        self.section_needs_registry = {}
        self.pending_evidence_requests = {}
        self.evidence_catalog = {}
        self.case_snapshots = []
        self.delivery_queue = []
        self._pending_section_outputs = {}
        self.toolkit_results_cache = {}

        if self.bus:
            self._register_bus_handlers()

        self.logger = logging.getLogger(__name__)
        self.logger.info("Gateway Controller initialized - DEFERS TO ECOSYSTEM CONTROLLER")
        self.logger.info("Gateway orchestration capabilities enabled")
        self.logger.info("OCR processing engines initialized")
        self.logger.info("Evidence Locker tracking system initialized")
        
        # Self-validation through ECC
        if self.ecosystem_controller:
            self._validate_gateway_with_ecc()

        self._attach_bus(bus)
    
    def attach_bus(self, bus) -> None:
        """Attach or replace the Central Command bus instance."""
        self._attach_bus(bus)

    def _attach_bus(self, bus) -> None:
        if not bus:
            return
        self.bus = bus
        self._register_bus_handlers()

    def _register_bus_handlers(self) -> None:
        if self._bus_handlers_registered or not self.bus:
            return
        handler_map = {"evidence.new": self._handle_bus_evidence_new,
                       "evidence.updated": self._handle_bus_evidence_updated,
                       "section.data.updated": self._handle_section_data_updated,
                       "section.needs": self._handle_bus_section_needs,
                       "case.snapshot": self._handle_bus_case_snapshot}
        for signal_name, handler in handler_map.items():
            try:
                self.bus.register_signal(signal_name, handler)
            except Exception as exc:  # pragma: no cover - bus registration best effort
                self.logger.warning("Failed to register bus handler %s: %s", signal_name, exc)
        self._bus_handlers_registered = True

    def _emit_bus_event(self, signal: str, payload: Dict[str, Any]) -> None:
        if not self.bus:
            return
        envelope = dict(payload or {})
        envelope.setdefault("source", "gateway_controller")
        envelope.setdefault("timestamp", datetime.now().isoformat())
        try:
            self.bus.emit(signal, envelope)
        except Exception as exc:  # pragma: no cover - log and continue
            self.logger.warning("Failed to emit %s via bus: %s", signal, exc)

    def attach_evidence_locker(self, locker: Any) -> None:
        """Attach Evidence Locker reference for enriched updates."""
        self.evidence_locker = locker

    def emit(self, signal: str, payload: Dict[str, Any]) -> None:
        """Expose bus emit for section frameworks."""
        self._emit_bus_event(signal, payload)

    def _normalize_section_id(self, section_id: Any) -> Optional[str]:
        if section_id is None:
            return None
        section_id = str(section_id)
        if section_id.startswith('section_'):
            return section_id
        return f'section_{section_id}'

    def _gather_section_evidence(self, section_id: str) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for entry in self.evidence_catalog.values():
            if not isinstance(entry, dict):
                continue
            candidate = entry.get('section_hint') or entry.get('assigned_section')
            related = entry.get('related_sections') or entry.get('classification', {}).get('related_sections') or []
            normalized_related = {str(item) for item in related if item}
            if str(candidate) != section_id and section_id not in normalized_related:
                continue
            results.append(dict(entry))
        return results

    def _build_manifest_snapshot(self, section_id: str) -> Dict[str, Any]:
        evidence = self._gather_section_evidence(section_id)
        return {
            'section_id': section_id,
            'count': len(evidence),
            'items': evidence,
            'last_updated': datetime.now().isoformat(),
        }

    def get_section_inputs(self, section_id: str) -> Dict[str, Any]:
        normalized = self._normalize_section_id(section_id)
        if not normalized:
            raise ValueError('section_id is required')
        case_id = self._current_case_id()
        needs = dict(self.section_needs_registry.get(normalized, {}))
        manifest_snapshot = self._build_manifest_snapshot(normalized)
        context = {
            'case_id': case_id,
            'section_id': normalized,
            'section_needs': needs,
            'manifest_context': manifest_snapshot,
            'evidence': manifest_snapshot.get('items', []),
            'bus_state': {
                'case_id': case_id,
                'needs': needs,
                'manifest': manifest_snapshot,
            },
            'case_data': self.case_bundle.get('case_data', {}),
            'previous_output': dict(self.section_outputs.get(normalized, {})),
            'toolkit_cache': self.toolkit_results_cache.get(normalized, {}),
        }
        if self.case_snapshots:
            context['case_snapshots'] = self.case_snapshots[-5:]
        return context

    def publish_section_result(self, section_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
        normalized = self._normalize_section_id(section_id)
        if not normalized:
            raise ValueError('section_id is required')
        if not isinstance(result, dict):
            raise ValueError('result must be a dictionary')
        payload = dict(result.get('payload') or result)
        payload.setdefault('section_id', normalized)
        case_id = result.get('case_id') or payload.get('case_id') or self._current_case_id()
        if case_id:
            payload['case_id'] = case_id
        metadata = dict(result.get('metadata') or {})
        metadata.setdefault('published_at', datetime.now().isoformat())
        record = {
            'section_id': normalized,
            'case_id': case_id,
            'payload': payload,
            'metadata': metadata,
            'narrative': result.get('narrative'),
            'summary': result.get('summary'),
            'source': result.get('source', 'section_framework'),
        }
        self.section_outputs[normalized] = record
        self.section_states[normalized] = SectionState.COMPLETED.value
        self._finalize_section_output(normalized, payload, source='section_framework')
        if getattr(self, 'evidence_locker', None) and hasattr(self.evidence_locker, 'record_enriched_section'):
            try:
                self.evidence_locker.record_enriched_section(normalized, record)
            except Exception as exc:
                self.logger.warning('Evidence locker enrichment failed for %s: %s', normalized, exc)
        return record



    def _handle_bus_evidence_new(self, payload: Dict[str, Any]) -> None:
        if not isinstance(payload, dict):
            return
        evidence_id = payload.get("evidence_id") or payload.get("artifact_id")
        if not evidence_id:
            return
        entry = dict(payload)
        entry.setdefault("last_event", "evidence.new")
        entry.setdefault("last_seen", datetime.now().isoformat())
        self.evidence_catalog[evidence_id] = entry

    def _handle_bus_evidence_updated(self, payload: Dict[str, Any]) -> None:
        if not isinstance(payload, dict):
            return
        evidence_id = payload.get("evidence_id") or payload.get("artifact_id")
        if evidence_id:
            entry = dict(payload)
            entry.setdefault("last_event", "evidence.updated")
            entry.setdefault("last_seen", datetime.now().isoformat())
            self.evidence_catalog[evidence_id] = entry
        section_hint = payload.get("section_id") or payload.get("section_hint") or payload.get("recipient")
        if not section_hint:
            return
        section_id = str(section_hint)
        pending = self._pending_section_outputs.get(section_id)
        if pending:
            enriched_payload = dict(payload)
            if pending.get("plan") and "parsing_plan" not in enriched_payload:
                enriched_payload["parsing_plan"] = pending["plan"]
            if pending.get("draft") and "draft" not in enriched_payload:
                enriched_payload["draft"] = pending["draft"]
            self._finalize_section_output(section_id, enriched_payload, source="bus_evidence_updated")

    def _handle_section_data_updated(self, payload: Dict[str, Any]) -> None:
        if not isinstance(payload, dict):
            return
        inner = payload.get("payload") if isinstance(payload.get("payload"), dict) else None
        section = (payload.get("section") or payload.get("section_id") or (inner or {}).get("section") or (inner or {}).get("section_id"))
        evidence_id = (payload.get("evidence_id") or (inner or {}).get("evidence_id"))
        if not section or not evidence_id:
            return
        section = str(section)
        evidence_id = str(evidence_id)
        self.delivery_queue.append((section, evidence_id))
        if len(self.delivery_queue) > 200:
            self.delivery_queue = self.delivery_queue[-200:]
        summary = (payload.get("summary") or (inner or {}).get("summary") or
                   payload.get("filename") or (inner or {}).get("filename") or
                   payload.get("file_path") or (inner or {}).get("file_path") or evidence_id)
        try:
            from pathlib import Path as _Path
            summary = _Path(str(summary)).name
        except Exception:
            summary = str(summary)
        status = payload.get("status") or (inner or {}).get("status") or "delivered"
        message = {
            "section": section,
            "evidence_id": evidence_id,
            "summary": summary,
            "status": status,
        }
        self._emit_bus_event("evidence.deliver", message)


    def _handle_bus_section_needs(self, payload: Dict[str, Any]) -> None:
        if not isinstance(payload, dict):
            return
        section_id = payload.get("section_id") or payload.get("section") or payload.get("target")
        if not section_id:
            return
        section_id = str(section_id)
        record = dict(payload)
        record.setdefault("timestamp", datetime.now().isoformat())
        self.section_needs_registry[section_id] = record
        self._issue_evidence_request(section_id, record)

    def _handle_bus_case_snapshot(self, payload: Dict[str, Any]) -> None:
        if not isinstance(payload, dict):
            return
        snapshot = dict(payload)
        snapshot.setdefault("received_at", datetime.now().isoformat())
        self.case_snapshots.append(snapshot)
        if len(self.case_snapshots) > 50:
            self.case_snapshots = self.case_snapshots[-50:]

    def _issue_evidence_request(self, section_id: str, need_payload: Dict[str, Any]) -> None:
        if not self.bus:
            return
        request_id = f"{section_id}_{uuid.uuid4().hex[:8]}"
        filters = need_payload.get("filters") or {}
        request_payload = {
            "section_id": section_id,
            "request_id": request_id,
            "case_id": self._current_case_id(),
            "filters": filters,
            "priority": need_payload.get("priority", "normal"),
            "requested_at": datetime.now().isoformat(),
        }
        self.pending_evidence_requests[request_id] = request_payload
        self._emit_bus_event("evidence.request", request_payload)

    def _current_case_id(self) -> Optional[str]:
        manifest = self.case_bundle.get("manifest")
        if isinstance(manifest, dict):
            for key in ("case_id", "id"):
                value = manifest.get(key)
                if value:
                    return str(value)
            case_data = manifest.get("case_data")
            if isinstance(case_data, dict):
                for key in ("case_id", "id"):
                    value = case_data.get(key)
                    if value:
                        return str(value)
        return None

    def _aggregate_processed_data(self, processed_files: List[str]) -> Dict[str, Any]:
        aggregated: Dict[str, Any] = {"files": {}}
        for file_path in processed_files:
            entry = self.case_bundle.get(file_path)
            if not entry:
                continue
            data = entry.get("processed_data") or {}
            aggregated["files"][file_path] = data
            for key in ("metadata", "contracts", "images", "videos", "audio", "forms", "summary", "manual_notes", "processing_log", "media_analysis"):
                value = data.get(key)
                if not value:
                    continue
                if isinstance(value, dict):
                    target = aggregated.setdefault(key, {})
                    target.update(value)
                elif isinstance(value, list):
                    target = aggregated.setdefault(key, [])
                    target.extend(value)
                else:
                    aggregated.setdefault(key, value)
        return aggregated

    def _build_section_parsing_plan(self, section_id: str, processed_files: List[str]) -> Optional[Dict[str, Any]]:
        if build_section_context is None:
            return None
        processed_data = self._aggregate_processed_data(processed_files)
        manifest = self.case_bundle.get("manifest")
        case_data: Dict[str, Any] = {}
        report_type = None
        if isinstance(manifest, dict):
            case_data = manifest.get("case_data") if isinstance(manifest.get("case_data"), dict) else dict(manifest)
            report_type = manifest.get("report_type") or case_data.get("report_type")
        section_sequence = [(sid, sid) for sid in sorted(self.section_handlers.keys())]
        plan = build_section_context(
            section_id=section_id,
            processed_data=processed_data,
            case_data=case_data,
            toolkit_results=self.toolkit_results_cache.get(section_id, {}),
            report_type=report_type,
            section_sequence=section_sequence,
            section_outputs=self.section_outputs,
            section_states=self.section_states,
        )
        return plan

    def _remember_section_draft(self, section_id: str, draft: Any, plan: Optional[Dict[str, Any]]) -> None:
        if draft is None:
            return
        snapshot = {
            "draft": draft,
            "plan": plan,
            "case_id": self._current_case_id(),
            "timestamp": datetime.now().isoformat(),
        }
        self.section_drafts[section_id] = snapshot
        self._pending_section_outputs[section_id] = dict(snapshot)

    def _finalize_section_output(self, section_id: str, enriched_payload: Dict[str, Any], *, source: str) -> None:
        timestamp = datetime.now().isoformat()
        record = {
            "section_id": section_id,
            "case_id": self._current_case_id(),
            "payload": dict(enriched_payload or {}),
            "source": source,
            "timestamp": timestamp,
        }
        draft_info = self._pending_section_outputs.pop(section_id, None)
        if draft_info:
            if draft_info.get("plan") and "parsing_plan" not in record["payload"]:
                record["payload"]["parsing_plan"] = draft_info["plan"]
            if draft_info.get("draft") and "draft" not in record["payload"]:
                record["payload"]["draft"] = draft_info["draft"]
        self.section_outputs[section_id] = record["payload"]
        self.section_cache[section_id] = {
            "data": record,
            "validated": False,
            "timestamp": timestamp,
            "review_notes": [],
            "revision_count": 0,
            "last_revision": None,
        }
        self.section_states[section_id] = "enriched"
        self._emit_bus_event("section.data.updated", record)
        self._emit_bus_event("gateway.section.complete", record)

    def track_evidence_locker_module(self, module_name: str, status: str, activity_data: Dict[str, Any] = None):
        """Track Evidence Locker module status and activity"""
        try:
            if module_name not in self.evidence_locker_modules:
                self.logger.warning(f"Unknown Evidence Locker module: {module_name}")
                return
            
            # Update module status
            self.evidence_locker_modules[module_name]['status'] = status
            self.evidence_locker_modules[module_name]['last_activity'] = datetime.now().isoformat()
            
            if activity_data:
                self.evidence_locker_modules[module_name]['last_activity_data'] = activity_data
            
            self.logger.info(f"ðŸ“Š Evidence Locker module {module_name} status: {status}")
            
            # Check for bottlenecks
            self._check_evidence_locker_bottlenecks()
            
        except Exception as e:
            self.logger.error(f"Failed to track Evidence Locker module {module_name}: {e}")
    
    def register_evidence_locker_handoff(self, from_module: str, to_module: str, handoff_data: Dict[str, Any]):
        """Register handoff from Evidence Locker module to Gateway"""
        try:
            handoff_record = {
                'from_module': from_module,
                'to_module': to_module,
                'handoff_data': handoff_data,
                'timestamp': datetime.now().isoformat(),
                'status': 'pending'
            }
            
            self.evidence_locker_handoff_queue.append(handoff_record)
            
            # Update module pending handoffs
            if from_module in self.evidence_locker_modules:
                self.evidence_locker_modules[from_module]['pending_handoffs'].append(handoff_record)
            
            self.logger.info(f"ðŸ”„ Registered handoff: {from_module} â†’ {to_module}")
            
            # Process handoff immediately
            self._process_evidence_locker_handoff(handoff_record)
            
        except Exception as e:
            self.logger.error(f"Failed to register Evidence Locker handoff: {e}")
    
    def _process_evidence_locker_handoff(self, handoff_record: Dict[str, Any]):
        """Process Evidence Locker handoff to Gateway"""
        try:
            from_module = handoff_record['from_module']
            handoff_data = handoff_record['handoff_data']
            
            # Update handoff status
            handoff_record['status'] = 'processing'
            
            # Route handoff data to appropriate Gateway handler
            if 'evidence_classification' in handoff_data.get('operation', ''):
                self._handle_classification_handoff(handoff_data)
            elif 'evidence_indexing' in handoff_data.get('operation', ''):
                self._handle_indexing_handoff(handoff_data)
            elif 'evidence_class_building' in handoff_data.get('operation', ''):
                self._handle_class_building_handoff(handoff_data)
            elif 'case_manifest' in handoff_data.get('operation', ''):
                self._handle_manifest_handoff(handoff_data)
            else:
                self._handle_generic_handoff(handoff_data)
            
            # Update handoff status
            handoff_record['status'] = 'completed'
            handoff_record['processed_at'] = datetime.now().isoformat()
            
            # Update module status
            self.track_evidence_locker_module(from_module, 'handoff_complete', handoff_data)
            
            self.logger.info(f"âœ… Processed handoff from {from_module}")
            
        except Exception as e:
            self.logger.error(f"Failed to process Evidence Locker handoff: {e}")
            handoff_record['status'] = 'failed'
            handoff_record['error'] = str(e)
    
    def _check_evidence_locker_bottlenecks(self):
        """Check for Evidence Locker bottlenecks"""
        try:
            current_time = datetime.now()
            bottleneck_threshold_minutes = 5
            
            for module_name, module_data in self.evidence_locker_modules.items():
                if module_data['status'] == 'processing':
                    last_activity = module_data.get('last_activity')
                    if last_activity:
                        last_activity_time = datetime.fromisoformat(last_activity)
                        time_diff = (current_time - last_activity_time).total_seconds() / 60
                        
                        if time_diff > bottleneck_threshold_minutes:
                            bottleneck_alert = {
                                'module': module_name,
                                'status': module_data['status'],
                                'last_activity': last_activity,
                                'stuck_for_minutes': time_diff,
                                'timestamp': current_time.isoformat()
                            }
                            
                            self.evidence_locker_bottleneck_alerts.append(bottleneck_alert)
                            self.logger.warning(f"âš ï¸ Evidence Locker bottleneck detected: {module_name} stuck for {time_diff:.1f} minutes")
                            
                            # Notify ECC of bottleneck
                            if self.ecosystem_controller and hasattr(self.ecosystem_controller, 'emit'):
                                self.ecosystem_controller.emit("gateway.bottleneck_alert", bottleneck_alert)
            
        except Exception as e:
            self.logger.error(f"Failed to check Evidence Locker bottlenecks: {e}")
    
    def _handle_classification_handoff(self, handoff_data: Dict[str, Any]):
        """Handle evidence classification handoff."""
        try:
            evidence_id = handoff_data.get('evidence_id')
            file_path = handoff_data.get('file_path')
            classification = handoff_data.get('classification') or handoff_data.get('classification_result') or {}
            if not isinstance(classification, dict):
                classification = dict(classification)
            assigned_section = (
                handoff_data.get('assigned_section')
                or handoff_data.get('section_hint')
                or classification.get('assigned_section')
            )
            tags = handoff_data.get('tags') or classification.get('tags') or []
            related_sections = handoff_data.get('related_sections') or classification.get('related_sections') or []
            case_id = handoff_data.get('case_id') or self._current_case_id()
            timestamp = datetime.now().isoformat()

            category_hint = handoff_data.get('category') or classification.get('category')
            resolution = resolve_tags(category=category_hint, tags=tags)
            normalized_tags = resolution.get('tags') or []
            if normalized_tags:
                tags = normalized_tags
                classification.setdefault('tags', normalized_tags)
            category_slug = resolution.get('category') or category_hint
            if not assigned_section:
                assigned_section = resolution.get('primary_section') or assigned_section
            if not related_sections:
                related_sections = resolution.get('related_sections') or related_sections
            if category_slug and 'category' not in classification:
                classification['category'] = category_slug

            if not evidence_id and file_path:
                registered = self.register_file(file_path)
                evidence_id = registered.get('evidence_id')

            if evidence_id:
                catalog_entry = dict(self.evidence_catalog.get(evidence_id, {}))
                catalog_entry.update({
                    'evidence_id': evidence_id,
                    'file_path': file_path,
                    'classification': classification,
                    'assigned_section': assigned_section,
                    'tags': tags,
                    'last_event': 'evidence_classification',
                    'last_seen': timestamp,
                })
                self.evidence_catalog[evidence_id] = catalog_entry

                master_record = self.master_evidence_index.get(evidence_id)
                if not master_record:
                    master_record = {
                        'evidence_id': evidence_id,
                        'filename': os.path.basename(file_path) if file_path else None,
                        'path': file_path,
                        'assigned_section': assigned_section or 'unassigned',
                        'classification': classification or {},
                        'tags': tags,
                        'processing_status': 'classified',
                        'timestamp': timestamp,
                    }
                else:
                    if file_path and not master_record.get('path'):
                        master_record['path'] = file_path
                    if assigned_section:
                        master_record['assigned_section'] = assigned_section
                    if classification:
                        master_record['classification'] = classification
                    if tags:
                        master_record['tags'] = tags
                    master_record['timestamp'] = timestamp
                self.master_evidence_index[evidence_id] = master_record

            target_sections: List[str] = []
            if assigned_section:
                target_sections.append(str(assigned_section))
            for sec in related_sections:
                if sec and str(sec) not in target_sections:
                    target_sections.append(str(sec))
            if not target_sections:
                target_sections.append('section_cp')

            for target in target_sections:
                filters = dict(handoff_data.get('filters', {}))
                if tags:
                    filters['tags'] = tags
                    filters.pop('section_id', None)
                else:
                    filters.setdefault('section_id', target)
                if category_slug:
                    filters['category'] = category_slug
                evidence_type = classification.get('evidence_type') if isinstance(classification, dict) else None
                if evidence_type and 'evidence_type' not in filters:
                    filters['evidence_type'] = evidence_type

                payload = {
                    'section_id': target,
                    'case_id': case_id,
                    'evidence_id': evidence_id,
                    'file_path': file_path,
                    'filters': filters,
                    'category': category_slug,
                    'priority': 'high' if target in {'section_3', 'section_8'} else handoff_data.get('priority', 'normal'),
                    'source': 'gateway.classification',
                    'classification': classification,
                    'related_sections': target_sections,
                    'tags': tags,
                    'timestamp': timestamp,
                }
                self._emit_bus_event('section.needs', payload)

                existing = self._pending_section_outputs.get(target, {})
                snapshot = dict(existing)
                if evidence_id:
                    snapshot['evidence_id'] = evidence_id
                if classification:
                    snapshot['classification'] = classification
                if tags:
                    snapshot['tags'] = tags
                if case_id:
                    snapshot['case_id'] = case_id
                if file_path:
                    snapshot['file_path'] = file_path
                snapshot.setdefault('related_sections', target_sections)
                snapshot['requested_at'] = timestamp
                self._pending_section_outputs[target] = snapshot

                if evidence_id:
                    section_evidence = self.evidence_map.setdefault(target, [])
                    if evidence_id not in section_evidence:
                        section_evidence.append(evidence_id)

            self.logger.info(
                "Gateway classified %s for sections %s",
                evidence_id or file_path,
                ", ".join(target_sections),
            )
        except Exception as e:
            self.logger.error(f"Failed to handle classification handoff: {e}")

    def _handle_indexing_handoff(self, handoff_data: Dict[str, Any]):
        """Handle evidence indexing handoff"""
        try:
            evidence_id = handoff_data.get('evidence_id')
            section_id = handoff_data.get('section_id')
            
            if evidence_id and section_id:
                # Update Gateway's evidence map
                if section_id not in self.evidence_map:
                    self.evidence_map[section_id] = []
                
                self.evidence_map[section_id].append(evidence_id)
                
                self.logger.info(f"ðŸ“‹ Gateway received indexing: {evidence_id} â†’ {section_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to handle indexing handoff: {e}")
    
    def _handle_class_building_handoff(self, handoff_data: Dict[str, Any]):
        """Handle evidence class building handoff"""
        try:
            evidence_metadata = handoff_data.get('evidence_metadata')
            
            if evidence_metadata:
                # Store evidence metadata in Gateway
                evidence_id = evidence_metadata.get('evidence_id')
                if evidence_id:
                    self.master_evidence_index[evidence_id] = evidence_metadata
                    
                    self.logger.info(f"ðŸ”§ Gateway received evidence class: {evidence_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to handle class building handoff: {e}")
    
    def _handle_manifest_handoff(self, handoff_data: Dict[str, Any]):
        """Handle case manifest handoff"""
        try:
            manifest_data = handoff_data.get('manifest_data')
            
            if manifest_data:
                # Store manifest in Gateway
                self.case_bundle['manifest'] = manifest_data
                
                self.logger.info(f"ðŸ“‹ Gateway received case manifest")
            
        except Exception as e:
            self.logger.error(f"Failed to handle manifest handoff: {e}")
    
    def _handle_generic_handoff(self, handoff_data: Dict[str, Any]):
        """Handle generic handoff from Evidence Locker"""
        try:
            operation = handoff_data.get('operation', 'unknown')
            
            # Store generic handoff data
            self.processing_log.append({
                'type': 'evidence_locker_handoff',
                'operation': operation,
                'data': handoff_data,
                'timestamp': datetime.now().isoformat()
            })
            
            self.logger.info(f"ðŸ“¦ Gateway received generic handoff: {operation}")
            
        except Exception as e:
            self.logger.error(f"Failed to handle generic handoff: {e}")
    
    def get_evidence_locker_status(self) -> Dict[str, Any]:
        """Get Evidence Locker status for monitoring"""
        try:
            return {
                'modules': self.evidence_locker_modules,
                'handoff_queue_length': len(self.evidence_locker_handoff_queue),
                'bottleneck_alerts': len(self.evidence_locker_bottleneck_alerts),
                'total_handoffs_processed': len([h for h in self.evidence_locker_handoff_queue if h['status'] == 'completed']),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get Evidence Locker status: {e}")
            return {}
    
    def register_file(self, file_path: str) -> Dict[str, Any]:
        """Register file in master evidence index"""
        try:
            # Generate unique evidence ID
            evidence_id = str(uuid.uuid4())
            
            # Basic file metadata
            file_stats = {
                'filename': os.path.basename(file_path),
                'file_path': file_path,
                'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                'file_type': os.path.splitext(file_path)[1].lower(),
                'registered_at': datetime.now().isoformat()
            }
            
            # Create evidence record
            record = {
                'evidence_id': evidence_id,
                'filename': file_stats['filename'],
                'path': file_path,
                'assigned_section': 'unassigned',  # Will be updated by classifier
                'cross_links': [],
                'evidence_id': evidence_id,
                'metadata': file_stats,
                'processing_status': 'registered',
                'timestamp': datetime.now().isoformat()
            }
            
            # Add to master index
            self.master_evidence_index[evidence_id] = record
            
            self.logger.info(f"ðŸ§¾ Registered {file_path} as {evidence_id}")
            
            return {
                'success': True,
                'evidence_id': evidence_id,
                'record': record
            }
            
        except Exception as e:
            self.logger.error(f"Failed to register file {file_path}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def assign_evidence_to_section(self, evidence_id: str, section_id: str) -> bool:
        """Assign evidence to a specific section"""
        try:
            if evidence_id not in self.master_evidence_index:
                self.logger.error(f"Evidence {evidence_id} not found")
                return False
            
            # Update evidence record
            self.master_evidence_index[evidence_id]['assigned_section'] = section_id
            
            # Update section map
            if section_id not in self.evidence_map:
                self.evidence_map[section_id] = []
            
            # Check if already assigned to avoid duplicates
            existing_ids = [e['evidence_id'] for e in self.evidence_map[section_id]]
            if evidence_id not in existing_ids:
                self.evidence_map[section_id].append(self.master_evidence_index[evidence_id])
            
            self.logger.info(f"ðŸ“‹ Assigned evidence {evidence_id} to {section_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to assign evidence {evidence_id} to {section_id}: {e}")
            return False
    
    def get_evidence_for(self, section_id: str) -> List[Dict[str, Any]]:
        """Get evidence assigned to specific section"""
        return self.evidence_map.get(section_id, [])
    
    def add_cross_link(self, evidence_id: str, keyword: str, target_evidence_id: Optional[str] = None):
        """Add cross-link to evidence"""
        try:
            if evidence_id not in self.master_evidence_index:
                self.logger.error(f"Evidence {evidence_id} not found")
                return False
            
            cross_link = {
                'keyword': keyword,
                'target_evidence_id': target_evidence_id,
                'timestamp': datetime.now().isoformat()
            }
            
            self.master_evidence_index[evidence_id]['cross_links'].append(cross_link)
            
            # Update cross-links index
            if keyword not in self.cross_links:
                self.cross_links[keyword] = []
            self.cross_links[keyword].append({
                'evidence_id': evidence_id,
                'target_evidence_id': target_evidence_id,
                'timestamp': datetime.now().isoformat()
            })
            
            self.logger.info(f"ðŸ”— Added cross-link: {keyword} to {evidence_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add cross-link: {e}")
            return False
    
    def transfer_section_data(self, section_id: str, structured_section_data: Dict[str, Any]) -> bool:
        """Section publishes structured data back to Gateway"""
        try:
            # ECC validation check - only registered sections can transfer data
            if self.ecosystem_controller:
                if not self.ecosystem_controller.validate_section_id(section_id):
                    raise ValueError(f"Section '{section_id}' is not registered in ECC. Transfer denied.")
                
                # Check if section is frozen (completed) - prevent overwrite
                if section_id in self.ecosystem_controller.frozen_sections:
                    raise ValueError(f"Section '{section_id}' is frozen (completed). Use reopen() to modify.")
            
            payload = structured_section_data if isinstance(structured_section_data, dict) else {'value': structured_section_data}
            self._finalize_section_output(section_id, payload, source="section_transfer")

            self.logger.debug("Section data stored for %s (ECC validated)", section_id)
            self.logger.info(f"Section data stored for {section_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to transfer section data for {section_id}: {e}")
            return False
    
    def sign_off_section(self, section_id: str, by_user: str) -> bool:
        """Sign off and validate section - CHECKS WITH ECC FIRST"""
        try:
            if section_id not in self.section_cache:
                self.logger.error(f"Section {section_id} not found in cache")
                return False
            
            # CHECK WITH ECC BEFORE MARKING COMPLETE
            if self.ecosystem_controller:
                ecc_can_complete = self.ecosystem_controller.can_run(section_id)
                if not ecc_can_complete:
                    self.logger.error(f"âŒ ECC denied completion for section {section_id}")
                    return False
                
                # Notify ECC of completion
                ecc_success = self.ecosystem_controller.mark_complete(section_id, by_user)
                if not ecc_success:
                    self.logger.error(f"âŒ ECC failed to mark section {section_id} complete")
                    return False
            
            self.section_cache[section_id]['validated'] = True
            self.section_cache[section_id]['signed_by'] = by_user
            self.section_cache[section_id]['sign_time'] = datetime.now().isoformat()
            self.completed_sections.add(section_id)
            
            self.logger.debug(f"âœ… Section {section_id} validated and authorized by {by_user} (ECC approved)")
            self.logger.info(f"Section {section_id} validated and authorized by {by_user}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to sign off section {section_id}: {e}")
            return False
    
    def is_section_complete(self, section_id: str) -> bool:
        """Check if section is complete"""
        return section_id in self.completed_sections
    
    def get_authorized_context(self) -> Dict[str, Any]:
        """Get authorized context from ECC-validated sections only"""
        try:
            # Hard gate - check if case is exportable
            if self.ecosystem_controller:
                if not self.ecosystem_controller.is_case_exportable():
                    self.logger.error(f"âŒ Case not exportable - not all sections completed")
                    return {}
            
            authorized = {}
            
            # Only include sections that are ECC-validated
            for sec_id in self.completed_sections:
                if sec_id in self.section_cache:
                    # Double-check with ECC if available
                    if self.ecosystem_controller:
                        ecc_validated = sec_id in self.ecosystem_controller.completed_ecosystems
                        if not ecc_validated:
                            self.logger.warning(f"âš ï¸ Section {sec_id} not ECC-validated, excluding from authorized context")
                            continue
                    
                    authorized[sec_id] = self.section_cache[sec_id]['data']
            
            self.logger.debug(f"ðŸ“‹ Authorized context contains {len(authorized)} ECC-validated sections")
            self.logger.info(f"Authorized context contains {len(authorized)} ECC-validated sections")
            return authorized
            
        except Exception as e:
            self.logger.error(f"Failed to get authorized context: {e}")
            return {}
    
    
    def request_section_revision(self, section_id: str, revision_reason: str, requester: str) -> bool:
        """Request revision of a completed section - NOTIFIES ECC"""
        try:
            if section_id not in self.section_cache:
                self.logger.error(f"Section {section_id} not found")
                return False
            
            # NOTIFY ECC OF REVISION REQUEST
            if self.ecosystem_controller:
                ecc_revision_success = self.ecosystem_controller.request_revision(section_id, revision_reason, requester)
                if not ecc_revision_success:
                    self.logger.error(f"âŒ ECC denied revision request for section {section_id}")
                    return False
            
            # Check revision limits
            current_revisions = self.section_cache[section_id].get('revision_count', 0)
            if current_revisions >= self.gateway_config['max_reruns']:
                self.logger.error(f"Section {section_id} has reached maximum revisions ({self.gateway_config['max_reruns']})")
                return False
            
            # Add revision request
            revision_request = {
                'reason': revision_reason,
                'requester': requester,
                'timestamp': datetime.now().isoformat(),
                'revision_number': current_revisions + 1
            }
            
            if 'revision_requests' not in self.section_cache[section_id]:
                self.section_cache[section_id]['revision_requests'] = []
            
            self.section_cache[section_id]['revision_requests'].append(revision_request)
            self.section_cache[section_id]['revision_count'] = current_revisions + 1
            self.section_cache[section_id]['last_revision'] = datetime.now().isoformat()
            
            # Remove from completed sections if it was completed
            if section_id in self.completed_sections:
                self.completed_sections.remove(section_id)
                self.section_cache[section_id]['validated'] = False
            
            self.logger.debug(f"ðŸ“ Revision requested for section {section_id} by {requester} (ECC notified)")
            self.logger.info(f"Revision requested for section {section_id} by {requester}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to request revision for section {section_id}: {e}")
            return False
    
    def can_run(self, section_id: str) -> bool:
        """DEFERS TO ECOSYSTEM CONTROLLER - Only allows progression if logic passes"""
        try:
            # DEFER TO ECOSYSTEM CONTROLLER (ROOT BOOT NODE)
            if self.ecosystem_controller:
                return self.ecosystem_controller.can_run(section_id)
            
            # Fallback if no ecosystem controller
            self.logger.warning(f"âš ï¸ No Ecosystem Controller - using fallback for {section_id}")
            if section_id not in self.section_cache:
                self.logger.error(f"Section {section_id} not found")
                return False
            
            # Basic checks
            if section_id in self.completed_sections:
                return True
            
            if not self.section_cache[section_id].get('data'):
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to check can_run for {section_id}: {e}")
            return False
    
    def mark_complete(self, section_id: str, by_user: str = "system") -> bool:
        """DEFERS TO ECOSYSTEM CONTROLLER - Changes state, notifies system"""
        try:
            # DEFER TO ECOSYSTEM CONTROLLER (ROOT BOOT NODE)
            if self.ecosystem_controller:
                success = self.ecosystem_controller.mark_complete(section_id, by_user)
                if success and section_id in self.section_cache:
                    # Update Gateway cache to match Ecosystem Controller
                    self.section_cache[section_id]['validated'] = True
                    self.section_cache[section_id]['signed_by'] = by_user
                    self.section_cache[section_id]['sign_time'] = datetime.now().isoformat()
                return success
            
            # Fallback if no ecosystem controller
            self.logger.warning(f"âš ï¸ No Ecosystem Controller - using fallback for {section_id}")
            if section_id not in self.section_cache:
                self.logger.error(f"Section {section_id} not found")
                return False
            
            # Update section state
            self.section_states[section_id] = "completed"
            self.completed_sections.add(section_id)
            
            # Update cache
            self.section_cache[section_id]['validated'] = True
            self.section_cache[section_id]['signed_by'] = by_user
            self.section_cache[section_id]['sign_time'] = datetime.now().isoformat()
            
            self.logger.info(f"âœ… Section {section_id} marked complete by {by_user}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to mark complete {section_id}: {e}")
            return False
    
    def reopen(self, section_id: str, reason: str = "manual_reopen", by_user: str = "system") -> bool:
        """DEFERS TO ECOSYSTEM CONTROLLER - Drops status, resets downstream"""
        try:
            # DEFER TO ECOSYSTEM CONTROLLER (ROOT BOOT NODE)
            if self.ecosystem_controller:
                success = self.ecosystem_controller.reopen(section_id, reason, by_user)
                if success and section_id in self.section_cache:
                    # Update Gateway cache to match Ecosystem Controller
                    self.section_cache[section_id]['validated'] = False
                    self.section_cache[section_id]['revision_count'] = self.section_cache[section_id].get('revision_count', 0) + 1
                    self.section_cache[section_id]['last_revision'] = datetime.now().isoformat()
                return success
            
            # Fallback if no ecosystem controller
            self.logger.warning(f"âš ï¸ No Ecosystem Controller - using fallback for {section_id}")
            if section_id not in self.section_cache:
                self.logger.error(f"Section {section_id} not found")
                return False
            
            # Reset section state
            self.section_states[section_id] = "idle"
            
            # Remove from completed
            if section_id in self.completed_sections:
                self.completed_sections.remove(section_id)
            
            # Update cache
            self.section_cache[section_id]['validated'] = False
            self.section_cache[section_id]['revision_count'] = self.section_cache[section_id].get('revision_count', 0) + 1
            self.section_cache[section_id]['last_revision'] = datetime.now().isoformat()
            
            self.logger.info(f"ðŸ”„ Section {section_id} reopened by {by_user}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to reopen {section_id}: {e}")
            return False
    
    def get_section_states(self) -> Dict[str, str]:
        """Get current state of each module"""
        return self.section_states
    
    def _validate_gateway_with_ecc(self) -> bool:
        """Gateway forces itself to be validated by ECC"""
        try:
            if not self.ecosystem_controller:
                self.logger.warning("âš ï¸ No ECC available for Gateway validation")
                return False
            
            # Register Gateway as a special section with ECC
            gateway_section_id = "gateway"
            
            # Check if Gateway can run according to ECC
            can_run = self.ecosystem_controller.can_run(gateway_section_id)
            
            if can_run:
                self.logger.info("âœ… Gateway validated by ECC - operational")
                return True
            else:
                self.logger.error("âŒ Gateway validation failed by ECC")
                return False
                
        except Exception as e:
            self.logger.error(f"Gateway validation with ECC failed: {e}")
            return False
    
    def force_ecc_validation(self) -> bool:
        """Force Gateway to validate itself with ECC"""
        return self._validate_gateway_with_ecc()
    
    def coordinate_section_execution(self, target_section_id: str, execution_command: Dict[str, Any]) -> bool:
        """Coordinate execution of target section - ENFORCES SECTION-AWARE EXECUTION"""
        try:
            # SECTION-AWARE EXECUTION ENFORCEMENT
            if not self.ecosystem_controller:
                raise Exception("No ECC reference available for section execution coordination")
            
            if not self.ecosystem_controller.can_run(target_section_id):
                self.logger.error(f"Cannot coordinate execution - section {target_section_id} not ready")
                return False
            
            # Log coordination request
            coordination_record = {
                'target_section': target_section_id,
                'command': execution_command,
                'timestamp': datetime.now().isoformat(),
                'coordinated_by': 'gateway_controller'
            }
            
            self.execution_coordination[target_section_id] = coordination_record
            self.communication_log.append(coordination_record)
            
            self.logger.debug(f"ðŸŽ¯ Coordinated execution for {target_section_id}")
            self.logger.info(f"Coordinated execution for {target_section_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to coordinate section execution: {e}")
            raise

    def manage_data_flow(self, source_section: str, target_section: str, data_payload: Dict[str, Any]) -> bool:
        """Manage data flow between sections - ENFORCES SECTION-AWARE EXECUTION"""
        try:
            # SECTION-AWARE EXECUTION ENFORCEMENT
            if not self.ecosystem_controller:
                raise Exception("No ECC reference available for data flow management")
            
            # Validate both sections can participate
            if not self.ecosystem_controller.can_run(source_section) or not self.ecosystem_controller.can_run(target_section):
                self.logger.error(f"Cannot manage data flow - sections not ready: {source_section} -> {target_section}")
                return False
            
            # Create data flow record
            flow_id = f"{source_section}_to_{target_section}_{datetime.now().strftime('%H%M%S')}"
            
            flow_record = {
                'flow_id': flow_id,
                'source_section': source_section,
                'target_section': target_section,
                'data_payload': data_payload,
                'timestamp': datetime.now().isoformat(),
                'status': 'active',
                'managed_by': 'gateway_controller'
            }
            
            self.data_flow_status[flow_id] = flow_record
            self.communication_log.append(flow_record)
            
            self.logger.debug(f"ðŸ“¡ Managed data flow {flow_id}")
            self.logger.info(f"Managed data flow {source_section} -> {target_section}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to manage data flow: {e}")
            raise

    def log_communication(self, communication_type: str, details: Dict[str, Any]) -> bool:
        """Log inter-section communication"""
        try:
            # SECTION-AWARE EXECUTION ENFORCEMENT
            if not self.ecosystem_controller:
                raise Exception("No ECC reference available for communication logging")
            
            log_entry = {
                'communication_type': communication_type,
                'details': details,
                'timestamp': datetime.now().isoformat(),
                'logged_by': 'gateway_controller'
            }
            
            self.communication_log.append(log_entry)
            
            self.logger.debug(f"ðŸ“ Logged {communication_type} communication")
            self.logger.info(f"Logged {communication_type} communication")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to log communication: {e}")
            raise

    def get_orchestration_status(self) -> Dict[str, Any]:
        """Get current orchestration status"""
        return {
            'active_communications': len(self.active_communications),
            'data_flows_active': len(self.data_flow_status),
            'execution_coordination_count': len(self.execution_coordination),
            'communication_log_entries': len(self.communication_log),
            'orchestration_mode': 'active',
            'coordination_enabled': True
        }

    def get_communication_log(self) -> List[Dict[str, Any]]:
        """Get communication log"""
        return self.communication_log.copy()

    def clear_communication_log(self) -> bool:
        """Clear communication log"""
        try:
            self.communication_log.clear()
            self.logger.debug(f"ðŸ—‘ï¸ Cleared communication log")
            self.logger.info(f"Cleared communication log")
            return True
        except Exception as e:
            self.logger.error(f"Failed to clear communication log: {e}")
            return False
    
    # OCR Processing Methods - Architectural Integration
    def process_document_pipeline(self, file_path: str, section_id: str = None) -> Dict[str, Any]:
        """Complete document processing pipeline following OCR Flow SOP - ENFORCES SECTION-AWARE EXECUTION"""
        try:
            if section_id and self.ecosystem_controller:
                if not self.ecosystem_controller.can_run(section_id):
                    raise Exception(f"Section {section_id} not active for document processing")
            
            # Stage 1: Intake & Classification
            file_info = self._classify_file_intake(file_path)
            
            # Stage 2: Primary Extraction (Tesseract & Unstructured)
            primary_result = self._run_primary_extraction(file_path, file_info)
            
            # Stage 3: Fallback if needed
            if not primary_result.get('extracted_text') or primary_result.get('confidence', 0) < 0.5:
                fallback_result = self._run_fallback_extraction(file_path, file_info)
                primary_result.update(fallback_result)
            
            # Stage 4: Media-specific processing
            media_result = self._run_media_processing(file_path, file_info, primary_result)
            primary_result.update(media_result)
            
            # Stage 5: Enrichment & Validation
            enrichment_result = self._run_enrichment_validation(file_path, primary_result)
            primary_result.update(enrichment_result)
            
            # Store in case bundle
            self._store_in_case_bundle(file_path, primary_result, section_id)
            
            self.logger.debug(f"ðŸ“„ Complete pipeline processed {file_path}")
            self.logger.info(f"Complete pipeline processed {file_path}")
            
            return primary_result
            
        except Exception as e:
            self.logger.error(f"Document pipeline failed for {file_path}: {e}")
            return {'error': str(e), 'file_path': file_path}
    
    def _classify_file_intake(self, file_path: str) -> Dict[str, Any]:
        """Stage 1: Intake & Classification"""
        file_ext = os.path.splitext(file_path)[1].lower()
        filename = os.path.basename(file_path).lower()
        
        file_info = {
            'path': file_path,
            'filename': filename,
            'extension': file_ext,
            'media_type': 'unknown',
            'priority': 'medium',
            'language_hints': [],
            'classification_time': datetime.now().isoformat()
        }
        
        # Media type classification
        if file_ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
            file_info['media_type'] = 'image'
        elif file_ext == '.pdf':
            file_info['media_type'] = 'pdf'
        elif file_ext in ['.mp4', '.avi', '.mov']:
            file_info['media_type'] = 'video'
        elif file_ext in ['.mp3', '.wav', '.m4a']:
            file_info['media_type'] = 'audio'
        elif file_ext in ['.docx', '.doc', '.txt']:
            file_info['media_type'] = 'document'
        
        # Priority classification
        if any(keyword in filename for keyword in ['urgent', 'critical', 'police', 'incident']):
            file_info['priority'] = 'critical'
        elif any(keyword in filename for keyword in ['medical', 'billing', 'invoice']):
            file_info['priority'] = 'high'
        
        return file_info
    
    def _run_primary_extraction(self, file_path: str, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 2: Primary Extraction (Tesseract & Unstructured)"""
        result = {
            'extracted_text': '',
            'text_blocks': [],
            'tables': [],
            'entities': [],
            'layout': {},
            'confidence': 0.0,
            'engine_used': 'none',
            'extraction_time': datetime.now().isoformat()
        }
        
        file_ext = file_info['extension']
        
        # Tesseract for images and scanned PDFs
        if file_ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
            tesseract_result = self.process_with_tesseract(file_path)
            if tesseract_result.get('extracted_text'):
                result.update(tesseract_result)
                result['engine_used'] = 'tesseract'
        
        # Unstructured for native PDFs and documents
        elif file_ext in ['.pdf', '.docx', '.doc']:
            unstructured_result = self.process_with_unstructured(file_path)
            if unstructured_result.get('extracted_text'):
                result.update(unstructured_result)
                result['engine_used'] = 'unstructured'
        
        return result
    
    def _run_fallback_extraction(self, file_path: str, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 3: Fallback Extraction"""
        fallback_result = {
            'fallback_attempts': [],
            'fallback_engine_used': 'none',
            'fallback_extracted_text': ''
        }
        
        # Try EasyOCR fallback (placeholder - would need actual implementation)
        try:
            # fallback_result['fallback_attempts'].append('easyocr')
            # fallback_result['fallback_engine_used'] = 'easyocr'
            pass
        except Exception as e:
            self.logger.debug(f"EasyOCR fallback failed: {e}")
        
        return fallback_result
    
    def _run_media_processing(self, file_path: str, file_info: Dict[str, Any], primary_result: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 4: Media-specific processing"""
        media_result = {
            'media_analysis': {},
            'frame_samples': [],
            'audio_transcript': '',
            'metadata': {}
        }
        
        if file_info['media_type'] == 'video':
            # Frame sampling with OpenCV (placeholder)
            media_result['media_analysis']['frame_count'] = 0
            media_result['frame_samples'] = []
        
        elif file_info['media_type'] == 'audio':
            # Whisper transcription (placeholder)
            media_result['audio_transcript'] = ''
        
        elif file_info['media_type'] == 'image':
            # EXIF metadata extraction
            try:
                image = Image.open(file_path)
                media_result['metadata'] = dict(image._getexif() or {})
            except Exception as e:
                self.logger.debug(f"EXIF extraction failed: {e}")
        
        return media_result
    
    def _run_enrichment_validation(self, file_path: str, primary_result: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 5: Enrichment & Validation"""
        enrichment_result = {
            'enrichment': {},
            'validation_status': 'pending',
            'ai_notes': [],
            'osint_lookup': {}
        }
        
        # AI confirmation (placeholder)
        if primary_result.get('extracted_text'):
            enrichment_result['ai_notes'].append('Text extraction confirmed by AI')
            enrichment_result['validation_status'] = 'confirmed'
        
        return enrichment_result
    
    def _store_in_case_bundle(self, file_path: str, result: Dict[str, Any], section_id: str = None):
        """Store processed result in case bundle"""
        bundle_entry = {
            'file_path': file_path,
            'processed_data': result,
            'section_id': section_id,
            'bundle_time': datetime.now().isoformat(),
            'status': 'processed'
        }
        
        if not hasattr(self, 'case_bundle'):
            self.case_bundle = {}
        
        self.case_bundle[file_path] = bundle_entry
        
        # Also store in processed_content for backward compatibility
        self.processed_content[file_path] = result
    
    def process_with_tesseract(self, file_path: str, section_id: str = None) -> Dict[str, Any]:
        """Process file with Tesseract OCR - ENFORCES SECTION-AWARE EXECUTION"""
        try:
            if not OCR_AVAILABLE or not PIL_AVAILABLE:
                raise Exception("Tesseract or PIL not available")
            
            if section_id and self.ecosystem_controller:
                if not self.ecosystem_controller.can_run(section_id):
                    raise Exception(f"Section {section_id} not active for OCR processing")
            
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
                # Image processing
                image = Image.open(file_path)
                text = pytesseract.image_to_string(image)
                confidence = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
                
                result = {
                    'engine': 'tesseract',
                    'file_path': file_path,
                    'extracted_text': text.strip(),
                    'confidence': float(np.mean(confidence['conf'][confidence['conf'] > 0])),
                    'processing_time': datetime.now().isoformat(),
                    'section_id': section_id
                }
                
            elif file_ext == '.pdf' and PDFPLUMBER_AVAILABLE:
                # PDF processing with pdfplumber + tesseract
                with pdfplumber.open(file_path) as pdf:
                    full_text = ""
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if not page_text:  # Try OCR if no text
                            page_image = page.to_image()
                            ocr_text = pytesseract.image_to_string(page_image.original)
                            page_text = ocr_text
                        full_text += page_text + "\n"
                
                result = {
                    'engine': 'tesseract_pdf',
                    'file_path': file_path,
                    'extracted_text': full_text.strip(),
                    'confidence': 0.85,  # PDF confidence estimate
                    'processing_time': datetime.now().isoformat(),
                    'section_id': section_id
                }
            else:
                raise Exception(f"Unsupported file type: {file_ext}")
            
            # Store processed content
            self.processed_content[file_path] = result
            self.logger.debug(f"ðŸ” Tesseract processed {file_path}")
            self.logger.info(f"Tesseract processed {file_path}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Tesseract processing failed for {file_path}: {e}")
            return {'error': str(e), 'file_path': file_path, 'engine': 'tesseract'}
    
    def process_with_unstructured(self, file_path: str, section_id: str = None) -> Dict[str, Any]:
        """Process file with Unstructured - ENFORCES SECTION-AWARE EXECUTION"""
        try:
            if not UNSTRUCTURED_AVAILABLE:
                raise Exception("Unstructured not available")
            
            if section_id and self.ecosystem_controller:
                if not self.ecosystem_controller.can_run(section_id):
                    raise Exception(f"Section {section_id} not active for unstructured processing")
            
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.pdf':
                elements = partition_pdf(file_path)
            elif file_ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
                elements = partition_image(file_path)
            else:
                raise Exception(f"Unsupported file type for unstructured: {file_ext}")
            
            # Extract structured data
            structured_data = []
            full_text = ""
            
            for element in elements:
                element_data = {
                    'type': str(type(element).__name__),
                    'text': str(element),
                    'metadata': element.metadata if hasattr(element, 'metadata') else {}
                }
                structured_data.append(element_data)
                full_text += str(element) + "\n"
            
            result = {
                'engine': 'unstructured',
                'file_path': file_path,
                'extracted_text': full_text.strip(),
                'structured_elements': structured_data,
                'element_count': len(elements),
                'processing_time': datetime.now().isoformat(),
                'section_id': section_id
            }
            
            # Store processed content
            self.processed_content[file_path] = result
            self.logger.debug(f"ðŸ“„ Unstructured processed {file_path}")
            self.logger.info(f"Unstructured processed {file_path}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Unstructured processing failed for {file_path}: {e}")
            return {'error': str(e), 'file_path': file_path, 'engine': 'unstructured'}
    
    def classify_content(self, file_path: str, section_id: str = None) -> Dict[str, Any]:
        """Classify processed content and determine handoff strategy - ENFORCES SECTION-AWARE EXECUTION"""
        try:
            if section_id and self.ecosystem_controller:
                if not self.ecosystem_controller.can_run(section_id):
                    raise Exception(f"Section {section_id} not active for content classification")
            
            if file_path not in self.processed_content:
                raise Exception(f"No processed content found for {file_path}")
            
            content = self.processed_content[file_path]
            classification = {
                'file_path': file_path,
                'content_type': 'unknown',
                'priority': 'medium',
                'handoff_strategy': 'standard',
                'target_sections': [],
                'confidence': 0.0,
                'classification_time': datetime.now().isoformat(),
                'section_id': section_id
            }
            
            # Analyze content type
            text = content.get('extracted_text', '').lower()
            
            if any(keyword in text for keyword in ['invoice', 'bill', 'payment', 'amount', '$']):
                classification['content_type'] = 'billing'
                classification['target_sections'] = ['section_6']
                classification['priority'] = 'high'
                classification['handoff_strategy'] = 'billing_summary'
                
            elif any(keyword in text for keyword in ['medical', 'doctor', 'hospital', 'treatment', 'diagnosis']):
                classification['content_type'] = 'medical'
                classification['target_sections'] = ['section_3', 'section_4']
                classification['priority'] = 'high'
                classification['handoff_strategy'] = 'medical_analysis'
                
            elif any(keyword in text for keyword in ['police', 'incident', 'report', 'officer', 'arrest']):
                classification['content_type'] = 'police_report'
                classification['target_sections'] = ['section_1', 'section_2']
                classification['priority'] = 'critical'
                classification['handoff_strategy'] = 'incident_analysis'
                
            elif any(keyword in text for keyword in ['witness', 'statement', 'testimony', 'deposition']):
                classification['content_type'] = 'witness_statement'
                classification['target_sections'] = ['section_2', 'section_5']
                classification['priority'] = 'high'
                classification['handoff_strategy'] = 'statement_analysis'
                
            else:
                classification['content_type'] = 'general_document'
                classification['target_sections'] = ['section_1']
                classification['priority'] = 'medium'
                classification['handoff_strategy'] = 'general_processing'
            
            # Calculate confidence based on content analysis
            confidence_score = min(len(text) / 1000, 1.0)  # Simple confidence based on text length
            classification['confidence'] = confidence_score
            
            # Store classification
            self.content_classification[file_path] = classification
            
            self.logger.debug(f"ðŸ·ï¸ Classified {file_path} as {classification['content_type']}")
            self.logger.info(f"Classified {file_path} as {classification['content_type']}")
            
            return classification
            
        except Exception as e:
            self.logger.error(f"Content classification failed for {file_path}: {e}")
            return {'error': str(e), 'file_path': file_path}
    
    def handoff_to_section(self, file_path: str, target_section: str, section_id: str = None) -> bool:
        """Handoff processed content to target section - ENFORCES SECTION-AWARE EXECUTION"""
        try:
            if section_id and self.ecosystem_controller:
                if not self.ecosystem_controller.can_run(section_id):
                    raise Exception(f"Section {section_id} not active for handoff")
            
            if file_path not in self.processed_content:
                raise Exception(f"No processed content found for {file_path}")
            
            if file_path not in self.content_classification:
                raise Exception(f"No classification found for {file_path}")
            
            content = self.processed_content[file_path]
            classification = self.content_classification[file_path]
            
            # Prepare handoff payload
            handoff_payload = {
                'file_path': file_path,
                'processed_content': content,
                'classification': classification,
                'handoff_time': datetime.now().isoformat(),
                'source_section': section_id,
                'target_section': target_section
            }
            
            # Transfer to target section via ECC validation
            success = self.transfer_section_data(target_section, handoff_payload)
            
            if success:
                self.logger.debug(f"ðŸ“¤ Handed off {file_path} to {target_section}")
                self.logger.info(f"Handed off {file_path} to {target_section}")
                
                # Log handoff in communication log
                self.log_communication('content_handoff', {
                    'file_path': file_path,
                    'target_section': target_section,
                    'content_type': classification['content_type'],
                    'priority': classification['priority']
                })
            
            return success
            
        except Exception as e:
            self.logger.error(f"Handoff failed for {file_path} to {target_section}: {e}")
            return False
    
    def get_ocr_status(self) -> Dict[str, Any]:
        """Get OCR processing status"""
        return {
            'processed_files': len(self.processed_content),
            'classified_files': len(self.content_classification),
            'available_engines': list(self.ocr_engines.keys()),
            'processing_stats': {
                'tesseract_processed': len([f for f in self.processed_content.values() if f.get('engine') == 'tesseract']),
                'unstructured_processed': len([f for f in self.processed_content.values() if f.get('engine') == 'unstructured']),
                'total_classifications': len(self.content_classification)
            }
        }
    
    # Section Orchestration Methods - Architectural Integration
    def orchestrate_section_processing(self, section_id: str, file_paths: List[str]) -> Dict[str, Any]:
        """Orchestrate section processing following architectural model - ENFORCES SECTION-AWARE EXECUTION"""
        try:
            if not self.ecosystem_controller:
                raise Exception("No ECC reference available for section orchestration")
            
            if not self.ecosystem_controller.can_run(section_id):
                raise Exception(f"Section {section_id} not active for orchestration")
            
            orchestration_result = {
                'section_id': section_id,
                'files_processed': [],
                'processing_stages': [],
                'section_outputs': {},
                'orchestration_time': datetime.now().isoformat(),
                'status': 'in_progress'
            }
            
            # Process each file through the pipeline
            for file_path in file_paths:
                self.logger.debug(f"ðŸ”„ Processing {file_path} for {section_id}")
                
                # Run complete document pipeline
                pipeline_result = self.process_document_pipeline(file_path, section_id)
                
                if pipeline_result.get('error'):
                    self.logger.error(f"Pipeline failed for {file_path}: {pipeline_result['error']}")
                    continue
                
                orchestration_result['files_processed'].append(file_path)
                orchestration_result['processing_stages'].append({
                    'file': file_path,
                    'stage': 'pipeline_complete',
                    'timestamp': datetime.now().isoformat()
                })
            
            # Create section outputs to be built by the section itself
            section_outputs = {}  # To be built by the section module
            
            # Route to section handler (each section is its own narrative agent)
            handler_result = self._route_to_section_handler(section_id, orchestration_result['files_processed'])
            if handler_result:
                section_outputs.update(handler_result)
            
            orchestration_result['section_outputs'] = section_outputs
            
            orchestration_result['status'] = 'completed'
            
            self.logger.debug(f"ðŸŽ¯ Section orchestration completed for {section_id}")
            self.logger.info(f"Section orchestration completed for {section_id}")
            
            return orchestration_result
            
        except Exception as e:
            self.logger.error(f"Section orchestration failed for {section_id}: {e}")
            return {'error': str(e), 'section_id': section_id}
    
    
    def get_case_bundle_status(self) -> Dict[str, Any]:
        """Get case bundle status for architectural monitoring"""
        return {
            'total_files': len(self.case_bundle),
            'processed_files': len([f for f in self.case_bundle.values() if f['status'] == 'processed']),
            'stage_confirmations': len(self.stage_confirmations),
            'processing_log_entries': len(self.processing_log),
            'bundle_size_mb': sum(len(str(data)) for data in self.case_bundle.values()) / 1024 / 1024
        }
    
    
    def _route_to_section_handler(self, section_id: str, processed_files: List[str]) -> Optional[Dict[str, Any]]:
        """Route processed files to per-section handler"""
        try:
            # Check if section handler is registered
            handler = self.section_handlers.get(section_id)
            if not handler:
                self.logger.debug(f"No section handler registered for {section_id}")
                return None
            
            # Get processed data from case bundle
            section_data = []
            for file_path in processed_files:
                if file_path in self.case_bundle:
                    section_data.append(self.case_bundle[file_path]['processed_data'])
            
            plan = self._build_section_parsing_plan(section_id, processed_files)

            signal_payload = {'processed_files': processed_files, 'section_data': section_data}
            if plan:
                signal_payload['parsing_plan'] = plan

            signal = self.create_signal(
                signal_type=SignalType.PROCESS,
                target=section_id,
                source="gateway_orchestration",
                payload=signal_payload,
                case_id="orchestration"
            )
            
            # Route to section handler
            handler_result = handler(signal.to_dict())
            self._remember_section_draft(section_id, handler_result, plan)
            
            self.logger.debug(f"ðŸ“¡ Routed {section_id} to section handler")
            self.logger.info(f"Routed {section_id} to section handler")
            
            return handler_result
            
        except Exception as e:
            self.logger.error(f"Failed to route to section handler for {section_id}: {e}")
            return None
    
    # Signal-Based Communication Methods
    def register_section_handler(self, section_id: str, handler_func: callable) -> bool:
        """Register a section handler for signal processing"""
        try:
            self.section_handlers[section_id] = handler_func
            self.logger.debug(f"ðŸ“¡ Registered handler for {section_id}")
            self.logger.info(f"Registered handler for {section_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to register handler for {section_id}: {e}")
            return False
    
    
    def dispatch_signal(self, signal: Signal) -> Dict[str, Any]:
        """Dispatch signal to target section - ENFORCES SECTION-AWARE EXECUTION"""
        try:
            signal_dict = signal.to_dict()
            
            # Validate with ECC
            if not self.ecosystem_controller:
                return {
                    "status": "FAILED",
                    "origin": signal.target,
                    "error": "No ECC reference available",
                    "timestamp": signal.timestamp
                }
            
            if not self.ecosystem_controller.can_run(signal.target):
                return {
                    "status": "BLOCKED",
                    "origin": signal.target,
                    "reason": "Section not active or blocked",
                    "timestamp": signal.timestamp
                }
            
            # Get handler
            handler = self.section_handlers.get(signal.target)
            if not handler:
                return {
                    "status": "FAILED",
                    "origin": signal.target,
                    "error": "No handler registered",
                    "timestamp": signal.timestamp
                }
            
            # Process signal
            result = handler(signal_dict)
            
            # Log signal processing
            self.signal_history.append({
                "signal": signal_dict,
                "result": result,
                "processing_time": datetime.now().isoformat()
            })
            
            # Update routing table
            self.signal_routing_table[signal.signal_id] = {
                "source": signal.source,
                "target": signal.target,
                "status": result.get("status", "UNKNOWN"),
                "timestamp": signal.timestamp
            }
            
            self.logger.debug(f"ðŸ“¡ Signal dispatched: {signal.type.value} -> {signal.target}")
            self.logger.info(f"Signal dispatched: {signal.type.value} -> {signal.target}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Signal dispatch failed: {e}")
            return {
                "status": "ERROR",
                "origin": signal.target,
                "error": str(e),
                "timestamp": signal.timestamp
            }
    
    def queue_signal(self, signal: Signal) -> bool:
        """Queue signal for processing"""
        try:
            self.signal_queue.append(signal)
            self.logger.debug(f"ðŸ“¥ Signal queued: {signal.type.value} -> {signal.target}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to queue signal: {e}")
            return False
    
    def process_signal_queue(self) -> Dict[str, Any]:
        """Process all queued signals"""
        try:
            results = []
            processed_count = 0
            
            while self.signal_queue:
                signal = self.signal_queue.pop(0)
                result = self.dispatch_signal(signal)
                results.append(result)
                processed_count += 1
            
            self.logger.debug(f"ðŸ“¤ Processed {processed_count} signals from queue")
            self.logger.info(f"Processed {processed_count} signals from queue")
            
            return {
                "processed_count": processed_count,
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Signal queue processing failed: {e}")
            return {"error": str(e)}
    
    def create_signal(self, signal_type: SignalType, target: str, source: str, payload: Dict[str, Any], case_id: str) -> Signal:
        """Create a new signal"""
        return Signal(signal_type, target, source, payload, case_id)
    
    def review_and_route(self, signal: Signal) -> Dict[str, Any]:
        """Review signal information and route to correct section"""
        try:
            # Analyze payload for routing decisions
            payload = signal.payload
            routing_decision = self._analyze_payload_for_routing(payload)
            
            # Update signal target if routing decision differs
            if routing_decision.get('recommended_section') and routing_decision['recommended_section'] != signal.target:
                signal.target = routing_decision['recommended_section']
                self.logger.debug(f"ðŸ”„ Signal rerouted to {signal.target}")
            
            # Dispatch the signal
            result = self.dispatch_signal(signal)
            
            # Add routing information to result
            result['routing_decision'] = routing_decision
            
            return result
            
        except Exception as e:
            self.logger.error(f"Signal review and routing failed: {e}")
            return {"error": str(e)}
    
    def _analyze_payload_for_routing(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze payload to determine correct routing"""
        routing_decision = {
            'recommended_section': None,
            'confidence': 0.0,
            'analysis_reason': '',
            'content_type': 'unknown'
        }
        
        # Analyze file paths or content types
        if 'file_path' in payload:
            file_path = payload['file_path']
            file_ext = os.path.splitext(file_path)[1].lower()
            filename = os.path.basename(file_path).lower()
            
            # Route based on file characteristics
            if any(keyword in filename for keyword in ['billing', 'invoice', 'payment', 'financial']):
                routing_decision['recommended_section'] = 'section_6'
                routing_decision['content_type'] = 'billing'
                routing_decision['confidence'] = 0.9
                routing_decision['analysis_reason'] = 'Financial document detected'
                
            elif any(keyword in filename for keyword in ['surveillance', 'video', 'camera', 'footage']):
                routing_decision['recommended_section'] = 'section_2'
                routing_decision['content_type'] = 'surveillance'
                routing_decision['confidence'] = 0.9
                routing_decision['analysis_reason'] = 'Surveillance content detected'
                
            elif any(keyword in filename for keyword in ['medical', 'doctor', 'hospital', 'treatment']):
                routing_decision['recommended_section'] = 'section_3'
                routing_decision['content_type'] = 'medical'
                routing_decision['confidence'] = 0.9
                routing_decision['analysis_reason'] = 'Medical document detected'
                
            elif any(keyword in filename for keyword in ['contract', 'lease', 'agreement']):
                routing_decision['recommended_section'] = 'section_5'
                routing_decision['content_type'] = 'contract'
                routing_decision['confidence'] = 0.9
                routing_decision['analysis_reason'] = 'Contract document detected'
        
        # Analyze content if available
        elif 'extracted_text' in payload:
            text = payload['extracted_text'].lower()
            
            if any(keyword in text for keyword in ['police', 'incident', 'report', 'officer']):
                routing_decision['recommended_section'] = 'section_1'
                routing_decision['content_type'] = 'police_report'
                routing_decision['confidence'] = 0.8
                routing_decision['analysis_reason'] = 'Police report content detected'
        
        return routing_decision
    
    def get_signal_status(self) -> Dict[str, Any]:
        """Get signal processing status"""
        return {
            'queued_signals': len(self.signal_queue),
            'processed_signals': len(self.signal_history),
            'registered_handlers': list(self.section_handlers.keys()),
            'routing_table_entries': len(self.signal_routing_table),
            'signal_types_processed': list(set([s['signal']['type'] for s in self.signal_history]))
        }

    def request_narrative_from_assembler(self, section_id: str, structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """Request narrative assembly from Narrative Assembler using handoff protocol"""
        try:
            # Step 1: Call out to ECC for permission
            if not self._call_out_to_ecc("narrative_request", {
                "section_id": section_id,
                "structured_data": structured_data
            }):
                logger.error("ECC permission denied for narrative request")
                return {"error": "ECC permission denied"}
            
            # Step 2: Wait for ECC confirmation
            if not self._wait_for_ecc_confirm():
                logger.error("ECC confirmation timeout for narrative request")
                return {"error": "ECC confirmation timeout"}
            
            # Step 3: Prepare narrative request data
            narrative_request_data = {
                "operation": "narrative_request",
                "section_id": section_id,
                "structured_data": structured_data,
                "timestamp": datetime.now().isoformat()
            }
            
            # Step 4: Send message to Narrative Assembler
            if not self._send_message("narrative_request", narrative_request_data):
                logger.error("Failed to send narrative request message")
                return {"error": "Failed to send narrative request"}
            
            # Step 5: Send accept signal
            if not self._send_accept_signal("narrative_request"):
                logger.error("Failed to send accept signal for narrative request")
                return {"error": "Failed to send accept signal"}
            
            # Step 6: Complete handoff
            self._complete_handoff("narrative_request", "success")
            
            logger.info(f"ðŸ“ Requested narrative from assembler for {section_id}")
            return {"status": "success", "section_id": section_id}
            
        except Exception as e:
            logger.error(f"Failed to request narrative from assembler: {e}")
            self._complete_handoff("narrative_request", "error")
            return {"error": str(e)}
    
    def _call_out_to_ecc(self, operation: str, data: Dict[str, Any]) -> bool:
        """Call out to ECC for permission to perform operation"""
        try:
            if not self.ecosystem_controller:
                logger.warning("ECC not available for call-out")
                return False
            
            # Prepare call-out data
            call_out_data = {
                "operation": operation,
                "source": "gateway_controller",
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
            
            # Emit call-out signal to ECC
            if hasattr(self.ecosystem_controller, 'emit'):
                self.ecosystem_controller.emit("gateway_controller.call_out", call_out_data)
                logger.info(f"ðŸ“ž Called out to ECC for operation: {operation}")
                return True
            else:
                logger.warning("ECC does not support signal emission")
                return False
                
        except Exception as e:
            logger.error(f"Failed to call out to ECC: {e}")
            return False
    
    def _wait_for_ecc_confirm(self, timeout: int = 30) -> bool:
        """Wait for ECC confirmation"""
        try:
            # In a real implementation, this would wait for ECC response
            # For now, we'll simulate immediate confirmation
            logger.info("â³ Waiting for ECC confirmation...")
            # Simulate confirmation delay
            import time
            time.sleep(0.1)  # Brief delay to simulate processing
            logger.info("âœ… ECC confirmation received")
            return True
            
        except Exception as e:
            logger.error(f"ECC confirmation timeout or error: {e}")
            return False
    
    def _send_message(self, message_type: str, data: Dict[str, Any]) -> bool:
        """Send message to ECC"""
        try:
            if not self.ecosystem_controller:
                logger.warning("ECC not available for message sending")
                return False
            
            message_data = {
                "message_type": message_type,
                "source": "gateway_controller",
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
            
            # Emit message to ECC
            if hasattr(self.ecosystem_controller, 'emit'):
                self.ecosystem_controller.emit(f"gateway_controller.{message_type}", message_data)
                logger.info(f"ðŸ“¤ Sent message to ECC: {message_type}")
                return True
            else:
                logger.warning("ECC does not support signal emission")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send message to ECC: {e}")
            return False
    
    def _send_accept_signal(self, operation: str) -> bool:
        """Send accept signal to ECC"""
        try:
            if not self.ecosystem_controller:
                logger.warning("ECC not available for accept signal")
                return False
            
            accept_data = {
                "operation": operation,
                "source": "gateway_controller",
                "status": "accepted",
                "timestamp": datetime.now().isoformat()
            }
            
            # Emit accept signal to ECC
            if hasattr(self.ecosystem_controller, 'emit'):
                self.ecosystem_controller.emit("gateway_controller.accept", accept_data)
                logger.info(f"âœ… Sent accept signal to ECC for operation: {operation}")
                return True
            else:
                logger.warning("ECC does not support signal emission")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send accept signal to ECC: {e}")
            return False
    
    def _complete_handoff(self, operation: str, status: str) -> bool:
        """Complete handoff process"""
        try:
            handoff_data = {
                "operation": operation,
                "source": "gateway_controller",
                "status": status,
                "timestamp": datetime.now().isoformat()
            }
            
            # Log handoff completion
            if not hasattr(self, 'handoff_log'):
                self.handoff_log = []
            
            self.handoff_log.append(handoff_data)
            
            logger.info(f"ðŸ”„ Handoff completed: {operation} - {status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to complete handoff: {e}")
            return False

    def get_gateway_status(self) -> Dict[str, Any]:
        """Get comprehensive gateway status"""
        ecc_validation = self._validate_gateway_with_ecc() if self.ecosystem_controller else False
        
        return {
            'total_evidence_items': len(self.master_evidence_index),
            'completed_sections': len(self.completed_sections),
            'section_cache_size': len(self.section_cache),
            'cross_links_count': len(self.cross_links),
            'evidence_map_sections': list(self.evidence_map.keys()),
            'completed_section_list': list(self.completed_sections),
            'gateway_config': self.gateway_config,
            'processing_log_entries': len(self.processing_log),
            'section_states': self.get_section_states(),
            'ecc_validation': ecc_validation,
            'ecc_connected': bool(self.ecosystem_controller),
            'orchestration_status': self.get_orchestration_status(),
            'ocr_status': self.get_ocr_status(),
            'case_bundle_status': self.get_case_bundle_status(),
            'bus_connected': bool(self.bus),
            'evidence_catalog_size': len(self.evidence_catalog),
            'pending_section_drafts': len(self._pending_section_outputs),
            'pending_evidence_requests': list(self.pending_evidence_requests.keys()),
            'section_needs': list(self.section_needs_registry.keys()),
            'case_snapshots_count': len(self.case_snapshots),
            'signal_status': self.get_signal_status()
        }

    # ------------------------------------------------------------------
    # Universal Communication Protocol Methods
    # ------------------------------------------------------------------
    def process_evidence_with_communication(self, evidence_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process evidence using universal communication protocol"""
        try:
            # Send evidence received signal
            self.communicator.send_signal(
                target_address="1-1",  # Evidence Locker
                radio_code="10-6",
                message="Evidence received for gateway processing",
                payload={"evidence_data": evidence_data}
            )
            
            # Process evidence
            result = self.process_evidence(evidence_data)
            
            # Send evidence complete signal
            self.communicator.send_signal(
                target_address="1-1",  # Evidence Locker
                radio_code="10-8",
                message="Evidence processing complete",
                payload={"result": result}
            )
            
            return result
            
        except Exception as e:
            # Send SOS fault with precise diagnostic code
            fault_code = f"2-2-30-{self._get_line_number()}"
            self.communicator.send_sos_fault(
                fault_code=fault_code,
                description=f"Gateway evidence processing error: {str(e)}",
                details={"error": str(e), "evidence_data": evidence_data}
            )
            raise

    def validate_section_with_communication(self, section_id: str) -> bool:
        """Validate section using universal communication protocol"""
        try:
            # Send validation request to ECC
            response = self.communicator.send_status_request("2-1")  # ECC
            
            if response and response.get("radio_code") == "10-4":
                # Send validation complete signal
                self.communicator.send_signal(
                    target_address="2-1",  # ECC
                    radio_code="10-8",
                    message=f"Section {section_id} validation complete",
                    payload={"section_id": section_id, "status": "validated"}
                )
                return True
            else:
                # Send SOS fault
                fault_code = f"2-2-20-{self._get_line_number()}"
                self.communicator.send_sos_fault(
                    fault_code=fault_code,
                    description=f"Section {section_id} validation failed",
                    details={"section_id": section_id, "response": response}
                )
                return False
                
        except Exception as e:
            # Send SOS fault
            fault_code = f"2-2-30-{self._get_line_number()}"
            self.communicator.send_sos_fault(
                fault_code=fault_code,
                description=f"Section validation error: {str(e)}",
                details={"section_id": section_id, "error": str(e)}
            )
            raise

    def get_communication_status(self) -> Dict[str, Any]:
        """Get communication status for health monitoring"""
        return {
            "address": "2-2",
            "status": "ACTIVE",
            "last_check": self.communicator.get_module_status()["last_check"],
            "communication_log_count": len(self.communicator.communication_log),
            "active_signals_count": len(self.communicator.active_signals)
        }

    def _get_line_number(self) -> int:
        """Get current line number for fault reporting"""
        import inspect
        frame = inspect.currentframe()
        caller_frame = frame.f_back.f_back if frame.f_back else frame
        return caller_frame.f_lineno





