from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from datetime import datetime, timedelta
from tag_taxonomy import resolve_tags
from typing import Any, Dict, Iterable, Optional, Tuple
import threading

def inject_bus_extensions(cls) -> None:
    """Monkey-patch EvidenceLocker with bus-driven evidence flow helpers."""
    if getattr(cls, "_bus_extensions_applied", False):
        return

    setattr(cls, "_bus_extensions_applied", True)

    DEDUP_WINDOW_SECONDS = 12

    original_init = cls.__init__

    def __init__(self, *args, **kwargs):  # type: ignore[override]
        original_init(self, *args, **kwargs)
        if not hasattr(self, "_manifest_lock"):
            self._manifest_lock = threading.Lock()
        if not hasattr(self, "evidence_manifest"):
            self.evidence_manifest: Dict[str, Dict[str, Any]] = {}
        if not hasattr(self, "section_needs"):
            self.section_needs: Dict[str, Dict[str, Any]] = {}
        if not hasattr(self, "_recent_delivery_lock"):
            self._recent_delivery_lock = threading.Lock()
        if not hasattr(self, "_recent_evidence_deliveries"):
            self._recent_evidence_deliveries: Dict[Tuple[str, str], datetime] = {}
        self._bus_extension_handlers_registered = getattr(self, "_bus_extension_handlers_registered", False)

    cls.__init__ = __init__

    if hasattr(cls, "initialize_with_bus"):
        original_initialize_with_bus = cls.initialize_with_bus

        def initialize_with_bus(self, bus):  # type: ignore[override]
            result = original_initialize_with_bus(self, bus)
            self._register_bus_extensions(bus)
            return result

        cls.initialize_with_bus = initialize_with_bus

    if hasattr(cls, "initialize_with_ecc"):
        original_initialize_with_ecc = cls.initialize_with_ecc

        def initialize_with_ecc(self, ecc):  # type: ignore[override]
            result = original_initialize_with_ecc(self, ecc)
            bus = getattr(self, "bus", None)
            if bus:
                self._register_bus_extensions(bus)
            elif ecc and hasattr(ecc, "register_signal"):
                if not getattr(self, "_bus_extension_handlers_registered", False):
                    ecc.register_signal("evidence.request", self._handle_evidence_request_signal)
                    ecc.register_signal("section.needs", self._handle_section_needs_signal)
                    self._bus_extension_handlers_registered = True
            return result

        cls.initialize_with_ecc = initialize_with_ecc

    if hasattr(cls, "scan_file"):
        original_scan_file = cls.scan_file

        def scan_file(self, file_path, section_id: Optional[str] = None):  # type: ignore[override]
            before_len = len(getattr(self, "processing_log", []) or [])
            result = original_scan_file(self, file_path, section_id)
            entry = None
            try:
                if self.processing_log and len(self.processing_log) > before_len:
                    entry = self.processing_log[-1]
            except Exception:
                entry = None
            if entry:
                evidence_id = entry.get("evidence_id")
                if evidence_id:
                    timestamp = entry.get("timestamp") or datetime.now().isoformat()
                    manifest_payload = {
                        "evidence_id": evidence_id,
                        "file_path": entry.get("file_path"),
                        "classification": entry.get("classification"),
                        "section_hint": entry.get("section_hint"),
                        "dependencies_cleared": entry.get("dependencies_cleared"),
                        "timestamp": timestamp,
                        "source": "scan_file",
                    }
                    is_new = self._record_manifest_entry(manifest_payload, event="evidence.scan")
                    self._publish_bus_event("evidence.updated" if not is_new else "evidence.new", manifest_payload)
            return result

        cls.scan_file = scan_file

    if hasattr(cls, "process_evidence_comprehensive"):
        original_process = cls.process_evidence_comprehensive

        def process_evidence_comprehensive(self, file_path: str) -> Dict[str, Any]:  # type: ignore[override]
            result = original_process(self, file_path)
            if isinstance(result, dict):
                evidence_id = result.get("evidence_id")
                if evidence_id:
                    timestamp = result.get("processing_timestamp") or datetime.now().isoformat()
                    payload = {
                        "evidence_id": evidence_id,
                        "file_path": result.get("file_path", file_path),
                        "classification": result.get("classification"),
                        "tools_used": result.get("tools_used"),
                        "timestamp": timestamp,
                        "source": "process_evidence_comprehensive",
                    }
                    self._record_manifest_entry(payload, event="evidence.annotated")
                    self._publish_bus_event("evidence.annotated", payload)
            return result

        cls.process_evidence_comprehensive = process_evidence_comprehensive

    if hasattr(cls, "_handoff_to_gateway"):
        original_handoff = cls._handoff_to_gateway

        def _handoff_to_gateway(self, file_path, evidence_id, section_hint, classification):  # type: ignore[override]
            success = original_handoff(self, file_path, evidence_id, section_hint, classification)
            if success and evidence_id:
                payload = {
                    "evidence_id": evidence_id,
                    "file_path": file_path,
                    "section_hint": section_hint,
                    "classification": classification,
                    "timestamp": datetime.now().isoformat(),
                    "source": "handoff_to_gateway",
                }
                self._record_manifest_entry(payload, event="evidence.updated")
                self._publish_bus_event("evidence.updated", payload)
            return success

        cls._handoff_to_gateway = _handoff_to_gateway

    if not hasattr(cls, "_register_bus_extensions"):
        def _register_bus_extensions(self, bus) -> None:
            if not bus or not hasattr(bus, "register_signal"):
                return
            if getattr(self, "_bus_extension_handlers_registered", False):
                return
            bus.register_signal("evidence.request", self._handle_evidence_request_signal)
            bus.register_signal("section.needs", self._handle_section_needs_signal)
            self._bus_extension_handlers_registered = True

        cls._register_bus_extensions = _register_bus_extensions

    if not hasattr(cls, "_publish_bus_event"):
        def _publish_bus_event(self, signal: str, payload: Dict[str, Any]) -> None:
            bus = getattr(self, "bus", None)
            if not bus:
                return
            event_payload = dict(payload)
            event_payload.setdefault("timestamp", datetime.now().isoformat())
            event_payload.setdefault("module", "evidence_locker")
            try:
                bus.emit(signal, event_payload)
            except Exception:
                if hasattr(self, "logger"):
                    self.logger.warning("Bus emit failed for %s", signal)

        cls._publish_bus_event = _publish_bus_event

    if not hasattr(cls, "_record_manifest_entry"):
        def _record_manifest_entry(self, payload: Dict[str, Any], *, event: str) -> bool:
            evidence_id = payload.get("evidence_id")
            if not evidence_id:
                return False
            classification = dict(payload.get("classification") or {})
            tags = payload.get("tags") or classification.get("tags") or []
            category_hint = payload.get("category") or payload.get("tag_category")
            resolution = resolve_tags(category=category_hint, tags=tags)
            normalized_tags = resolution.get("tags") or []
            if normalized_tags:
                payload["tags"] = normalized_tags
                classification.setdefault("tags", normalized_tags)
            if resolution.get("category") and not payload.get("category"):
                payload["category"] = resolution.get("category")
            if not payload.get("section_hint"):
                primary_section = classification.get("assigned_section") or resolution.get("primary_section")
                if primary_section:
                    payload["section_hint"] = primary_section
                    classification.setdefault("assigned_section", primary_section)
            if not payload.get("related_sections"):
                payload["related_sections"] = resolution.get("related_sections") or []
            payload["classification"] = classification
            timestamp = payload.get("timestamp") or datetime.now().isoformat()
            with self._manifest_lock:
                existing = self.evidence_manifest.get(evidence_id)
                entry = dict(existing or {})
                entry.update(payload)
                history = list(entry.get("history", []))
                history.append({"event": event, "timestamp": timestamp})
                entry["history"] = history[-50:]
                entry["last_event"] = event
                entry["last_updated"] = timestamp
                self.evidence_manifest[evidence_id] = entry
                return existing is None


        cls._record_manifest_entry = _record_manifest_entry

    if not hasattr(cls, "_handle_evidence_request_signal"):
        def _handle_evidence_request_signal(self, payload: Dict[str, Any]) -> None:
            evidence_id = payload.get("evidence_id")
            filters = dict(payload.get("filters") or {})
            recipient = payload.get("section_id") or payload.get("requester") or "unspecified"
            priority = str(payload.get("priority", "normal")).lower()
            request_id = payload.get("request_id")
            if "tags" in filters and not isinstance(filters["tags"], (list, tuple, set)):
                filters["tags"] = [filters["tags"]]

            now = datetime.now()
            window_start = now - timedelta(seconds=DEDUP_WINDOW_SECONDS)

            with self._recent_delivery_lock:
                stale_keys = [key for key, ts in self._recent_evidence_deliveries.items() if ts < window_start]
                for key in stale_keys:
                    self._recent_evidence_deliveries.pop(key, None)

            with self._manifest_lock:
                if evidence_id:
                    entry = dict(self.evidence_manifest.get(evidence_id, {}))
                    entries: Iterable[Dict[str, Any]] = [entry] if entry else []
                else:
                    entries = [
                        dict(entry)
                        for entry in self.evidence_manifest.values()
                        if _manifest_matches(entry, filters)
                    ]

            for entry in entries:
                if not entry:
                    continue
                evidence_key = entry.get("evidence_id") or entry.get("id")
                if not evidence_key:
                    continue
                dedup_key = (recipient, evidence_key)

                skip_delivery = False
                with self._recent_delivery_lock:
                    last_sent = self._recent_evidence_deliveries.get(dedup_key)
                    if priority != "high" and last_sent and last_sent >= window_start:
                        skip_delivery = True
                    else:
                        self._recent_evidence_deliveries[dedup_key] = datetime.now()

                if skip_delivery:
                    continue

                deliver_payload = dict(entry)
                deliver_payload["evidence_id"] = evidence_key
                deliver_payload["recipient"] = recipient
                deliver_payload["request_id"] = request_id
                deliver_payload["priority"] = priority
                deliver_payload["filters"] = filters
                deliver_payload["timestamp"] = datetime.now().isoformat()
                self._publish_bus_event("evidence.deliver", deliver_payload)

        cls._handle_evidence_request_signal = _handle_evidence_request_signal

    if not hasattr(cls, "_handle_section_needs_signal"):
        def _handle_section_needs_signal(self, payload: Dict[str, Any]) -> None:
            section_id = payload.get("section_id") or payload.get("section") or "unspecified"
            record = dict(payload)
            record.setdefault("timestamp", datetime.now().isoformat())
            with self._manifest_lock:
                self.section_needs[section_id] = record
            if hasattr(self, "logger"):
                self.logger.info("[EVIDENCE] Section %s advertised needs", section_id)

        cls._handle_section_needs_signal = _handle_section_needs_signal

    if not hasattr(cls, "get_evidence_manifest"):
        def get_evidence_manifest(self) -> Dict[str, Dict[str, Any]]:
            with self._manifest_lock:
                return {eid: dict(entry) for eid, entry in self.evidence_manifest.items()}

        cls.get_evidence_manifest = get_evidence_manifest


def _manifest_matches(entry: Dict[str, Any], filters: Dict[str, Any]) -> bool:
    if not filters:
        return True

    tags_filter_value = filters.get("tags")
    if tags_filter_value:
        if isinstance(tags_filter_value, (str, bytes)):
            tags_filter = {str(tags_filter_value)}
        else:
            tags_filter = {str(tag) for tag in tags_filter_value}
        entry_tags = entry.get("tags") or entry.get("classification", {}).get("tags", []) or []
        tags_normalized = {str(tag) for tag in entry_tags}
        if tags_filter and not tags_filter.issubset(tags_normalized):
            return False

    category_filter = filters.get("category")
    if category_filter:
        entry_category = entry.get("category")
        if isinstance(category_filter, (list, tuple, set)):
            normalized_categories = {resolve_tags(category=cat).get("category") or str(cat) for cat in category_filter}
            if normalized_categories and str(entry_category) not in normalized_categories:
                return False
        else:
            expected_category = resolve_tags(category=category_filter).get("category") or str(category_filter)
            if expected_category and str(entry_category) != expected_category:
                return False

    section_filter = filters.get("section_id") or filters.get("section")
    if section_filter:
        section_candidate = (
            entry.get("section_hint")
            or entry.get("assigned_section")
            or entry.get("classification", {}).get("assigned_section")
        )
        if str(section_candidate) != str(section_filter) and str(section_candidate) != "unassigned":
            return False

    evidence_type_filter = filters.get("evidence_type")
    if evidence_type_filter:
        candidate_type = (
            entry.get("evidence_type")
            or entry.get("classification", {}).get("evidence_type")
        )
        if isinstance(evidence_type_filter, (list, tuple, set)):
            if str(candidate_type) not in {str(v) for v in evidence_type_filter}:
                return False
        else:
            if str(candidate_type) != str(evidence_type_filter):
                return False

    return True






