#!/usr/bin/env python3
"""Central Command Section Controller.

Coordinates section-level evidence needs with the shared evidence pool.
Listens for `section.needs` and `evidence.deliver` bus traffic, builds
normalized payloads per section, and emits `section.data.updated` with
curated evidence context ready for narrative assembly.
"""

from __future__ import annotations

import logging
import sys
import threading
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

ROOT_DIR = Path(__file__).resolve().parents[2]
EVIDENCE_LOCKER_DIR = ROOT_DIR / "Evidence Locker"
if EVIDENCE_LOCKER_DIR.exists():
    locker_str = str(EVIDENCE_LOCKER_DIR)
    if locker_str not in sys.path:
        sys.path.insert(0, locker_str)
try:
    from section_registry import SECTION_REGISTRY
except ImportError:  # pragma: no cover - registry should be available in runtime
    SECTION_REGISTRY: Dict[str, Dict[str, Any]] = {}

logger = logging.getLogger("SectionController")


class SectionController:
    """Bridge between section intent signals and the evidence manifest."""

    def __init__(self, bus: Any, evidence_locker: Any = None) -> None:
        self.bus = bus
        self.evidence_locker = evidence_locker
        self.section_requests: Dict[str, Dict[str, Any]] = {}
        self.section_payloads: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()

        if not logger.handlers:
            logging.basicConfig(level=logging.INFO)

        if bus and hasattr(bus, "register_signal"):
            self._register_bus_handlers(bus)
        else:  # pragma: no cover - defensive guard
            logger.warning("SectionController initialized without bus registration")

    # ------------------------------------------------------------------
    # Bus registration & signal handlers
    # ------------------------------------------------------------------
    def _register_bus_handlers(self, bus: Any) -> None:
        bus.register_signal("section.needs", self._handle_section_needs)
        bus.register_signal("evidence.deliver", self._handle_evidence_deliver)
        bus.register_signal("case_reset", self._handle_case_reset)
        logger.info("[SECTION] SectionController handlers registered with bus")

    def _handle_case_reset(self, payload: Dict[str, Any]) -> None:
        with self.lock:
            self.section_requests.clear()
            self.section_payloads.clear()
        logger.info("[SECTION] Reset state for new case context")

    def _handle_section_needs(self, payload: Dict[str, Any]) -> None:
        section_id = (payload.get("section_id") or payload.get("section") or "").strip()
        if not section_id:
            logger.warning("[SECTION] section.needs missing section identifier: %s", payload)
            return

        tags = self._normalize_tags(payload.get("tags") or payload.get("tag_hints") or [])
        filters = payload.get("filters") or {}
        request_id = payload.get("request_id") or self._generate_request_id(section_id)
        priority = str(payload.get("priority", "normal")).lower()
        requested_at = payload.get("timestamp") or datetime.now().isoformat()

        request_record = {
            "request_id": request_id,
            "requested_at": requested_at,
            "priority": priority,
            "tags": tags,
            "filters": filters,
            "raw_payload": dict(payload),
            "last_refresh": None,
            "case_id": payload.get("case_id") or getattr(self.bus, "current_case_id", None),
        }
        with self.lock:
            self.section_requests[section_id] = request_record
        logger.info(
            "[SECTION] section.needs captured for %s (priority=%s, tags=%s)",
            section_id,
            priority,
            tags or "<none>",
        )

        self._fulfill_section_request(section_id, reason="section.needs")

    def _handle_evidence_deliver(self, payload: Dict[str, Any]) -> None:
        section_id = (
            payload.get("recipient")
            or payload.get("section_id")
            or payload.get("section")
            or ""
        ).strip()
        if not section_id:
            return

        evidence_id = payload.get("evidence_id")
        with self.lock:
            request_record = self.section_requests.get(section_id)
            if not request_record:
                # Create an ad-hoc request so downstream modules stay in sync
                request_record = {
                    "request_id": self._generate_request_id(section_id),
                    "requested_at": datetime.now().isoformat(),
                    "priority": str(payload.get("priority", "normal")).lower(),
                    "tags": self._normalize_tags(payload.get("tags") or []),
                    "filters": payload.get("filters") or {},
                    "raw_payload": {"source": "evidence.deliver", **payload},
                    "last_refresh": None,
                    "case_id": payload.get("case_id") or getattr(self.bus, "current_case_id", None),
                }
                self.section_requests[section_id] = request_record

        logger.info(
            "[SECTION] evidence.deliver received for %s (%s)",
            section_id,
            evidence_id or "unknown",
        )
        self._fulfill_section_request(section_id, reason="evidence.deliver")

    # ------------------------------------------------------------------
    # Core processing
    # ------------------------------------------------------------------
    def _fulfill_section_request(self, section_id: str, *, reason: str) -> None:
        request = self.section_requests.get(section_id)
        if not request:
            logger.warning("[SECTION] No stored request for %s; skip", section_id)
            return

        raw_entries = self._gather_evidence(section_id, request)
        normalized_entries = [self._normalize_entry(entry) for entry in raw_entries]
        deduped_entries, duplicate_entries = self._dedupe_entries(normalized_entries)
        payload = self._build_section_payload(
            section_id,
            request,
            deduped_entries,
            duplicate_entries,
            reason=reason,
        )

        with self.lock:
            self.section_payloads[section_id] = payload
            request["last_refresh"] = payload["metadata"]["generated_at"]

        self._emit_section_update(payload)

        if not deduped_entries:
            self._dispatch_evidence_request(section_id, request)

    def _dispatch_evidence_request(self, section_id: str, request: Dict[str, Any]) -> None:
        """Ask upstream evidence locker for additional material when the pool is empty."""
        bus = self.bus
        if not bus or not hasattr(bus, "emit"):
            return
        last_request = request.get("evidence_request_dispatched")
        if last_request:
            # Avoid flooding the bus; only dispatch once per request context.
            return
        filters = dict(request.get("filters") or {})
        if request.get("tags"):
            filters.setdefault("tags", list(request["tags"]))
        payload = {
            "section_id": section_id,
            "request_id": request.get("request_id"),
            "filters": filters,
            "priority": request.get("priority", "normal"),
            "timestamp": datetime.now().isoformat(),
            "source": "section_controller",
            "case_id": request.get("case_id") or getattr(self.bus, "current_case_id", None),
        }
        try:
            bus.emit("evidence.request", payload)
            request["evidence_request_dispatched"] = payload["timestamp"]
            logger.info("[SECTION] Dispatched evidence.request for %s", section_id)
        except Exception as exc:  # pragma: no cover - bus failures should not halt flow
            logger.error("[SECTION] Failed to emit evidence.request: %s", exc)

    def _gather_evidence(self, section_id: str, request: Dict[str, Any]) -> List[Dict[str, Any]]:
        tags = request.get("tags")
        filters = request.get("filters") or {}
        limit = filters.get("limit")
        entries: List[Dict[str, Any]] = []

        if self.evidence_locker and hasattr(self.evidence_locker, "get_common_pool"):
            try:
                entries = self.evidence_locker.get_common_pool(
                    section=section_id,
                    tags=tags,
                    include_related=True,
                    limit=limit,
                )
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.error("[SECTION] evidence_locker.get_common_pool failed: %s", exc)
                entries = []

        if not entries:
            entries = self._gather_from_bus_manifest(section_id, tags, limit)

        return entries

    def _gather_from_bus_manifest(
        self,
        section_id: str,
        tags: Optional[Iterable[str]],
        limit: Optional[int],
    ) -> List[Dict[str, Any]]:
        bus = self.bus
        if not bus or not hasattr(bus, "get_evidence_manifest"):
            return []
        manifest_entries = bus.get_evidence_manifest()
        if isinstance(manifest_entries, dict):
            manifest_entries = [manifest_entries]

        tag_filter = {str(tag).lower() for tag in (tags or [])}
        results: List[Dict[str, Any]] = []
        for entry in manifest_entries or []:
            if not isinstance(entry, dict):
                continue
            candidate_section = (
                entry.get("section_hint")
                or entry.get("assigned_section")
                or entry.get("classification", {}).get("assigned_section")
            )
            related_sections = entry.get("related_sections") or []
            if candidate_section != section_id and section_id not in {str(s) for s in related_sections}:
                continue
            if tag_filter:
                entry_tags = {
                    str(tag).lower()
                    for tag in entry.get("tags")
                    or entry.get("classification", {}).get("tags", [])
                }
                if not entry_tags.intersection(tag_filter):
                    continue
            results.append(entry)
            if limit and len(results) >= int(limit):
                break
        return results

    # ------------------------------------------------------------------
    # Payload construction helpers
    # ------------------------------------------------------------------
    def _normalize_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        evidence_id = entry.get("evidence_id") or entry.get("id")
        file_path = entry.get("file_path") or entry.get("path")
        file_name = Path(file_path).name if file_path else entry.get("file_name")
        classification = entry.get("classification") or {}
        tags = self._normalize_tags(entry.get("tags") or classification.get("tags") or [])
        related_sections = entry.get("related_sections") or classification.get("related_sections") or []
        evidence_type = entry.get("evidence_type") or classification.get("evidence_type")
        timestamp = (
            entry.get("last_updated")
            or entry.get("timestamp")
            or entry.get("processing_timestamp")
            or datetime.now().isoformat()
        )

        normalized = {
            "evidence_id": evidence_id,
            "file_name": file_name,
            "file_path": file_path,
            "file_type": entry.get("file_type") or classification.get("file_type"),
            "file_size": entry.get("file_size"),
            "tags": sorted(tags),
            "evidence_type": evidence_type,
            "section_hint": entry.get("section_hint") or classification.get("assigned_section"),
            "related_sections": related_sections,
            "classification": classification,
            "source": entry.get("source"),
            "timestamp": timestamp,
        }
        extras = {}
        for key in ("confidence", "routing_notes", "dependencies_cleared"):
            value = classification.get(key) if key in classification else entry.get(key)
            if value is not None:
                extras[key] = value
        if extras:
            normalized["metadata"] = extras
        return normalized

    def _dedupe_entries(
        self,
        entries: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        seen: Dict[str, Dict[str, Any]] = {}
        duplicates: List[Dict[str, Any]] = []
        for entry in entries:
            key = entry.get("file_path") or entry.get("evidence_id") or entry.get("file_name")
            if not key:
                duplicates.append(entry)
                continue
            if key in seen:
                duplicates.append(entry)
                continue
            seen[key] = entry
        return list(seen.values()), duplicates

    def _build_section_payload(
        self,
        section_id: str,
        request: Dict[str, Any],
        entries: List[Dict[str, Any]],
        duplicates: List[Dict[str, Any]],
        *,
        reason: str,
    ) -> Dict[str, Any]:
        metadata = SECTION_REGISTRY.get(section_id, {})
        generated_at = datetime.now().isoformat()
        summary = self._build_summary(entries, duplicates, request, generated_at, reason, metadata)
        case_id = request.get("case_id") or getattr(self.bus, "current_case_id", None)
        payload = {
            "section_id": section_id,
            "section_title": metadata.get("title") or section_id,
            "request_id": request.get("request_id"),
            "requested_at": request.get("requested_at"),
            "reason": reason,
            "evidence": entries,
            "duplicates": duplicates,
            "summary": summary,
            "metadata": {
                "generated_at": generated_at,
                "priority": request.get("priority"),
                "requested_tags": list(request.get("tags") or []),
                "filters": dict(request.get("filters") or {}),
            },
            "case_id": case_id,
        }
        if case_id:
            payload["metadata"]["case_id"] = case_id
        return payload

    def _build_summary(
        self,
        entries: List[Dict[str, Any]],
        duplicates: List[Dict[str, Any]],
        request: Dict[str, Any],
        generated_at: str,
        reason: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        tag_counter = Counter()
        evidence_type_counter = Counter()
        sources = Counter()
        latest_timestamp = None
        for entry in entries:
            tag_counter.update(entry.get("tags") or [])
            evidence_type = entry.get("evidence_type") or "unspecified"
            evidence_type_counter[evidence_type] += 1
            source = entry.get("source") or "manifest"
            sources[source] += 1
            entry_ts = entry.get("timestamp")
            if entry_ts and (latest_timestamp is None or entry_ts > latest_timestamp):
                latest_timestamp = entry_ts
        summary = {
            "reason": reason,
            "generated_at": generated_at,
            "section_category": metadata.get("category"),
            "section_order": metadata.get("default_order"),
            "total_items": len(entries),
            "duplicate_items": len(duplicates),
            "primary_tags": sorted(tag_counter.keys()),
            "tag_frequencies": dict(tag_counter),
            "evidence_types": dict(evidence_type_counter),
            "sources": dict(sources),
            "latest_timestamp": latest_timestamp,
            "requested_tags": list(request.get("tags") or []),
        }
        return summary

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    def _emit_section_update(self, payload: Dict[str, Any]) -> None:
        if not self.bus or not hasattr(self.bus, "emit"):
            return
        try:
            self.bus.emit("section.data.updated", payload)
            if hasattr(self.bus, "section_data"):
                self.bus.section_data[payload["section_id"]] = payload
            logger.info(
                "[SECTION] section.data.updated emitted for %s with %d items",
                payload["section_id"],
                len(payload.get("evidence") or []),
            )
        except Exception as exc:  # pragma: no cover
            logger.error("[SECTION] Failed to emit section.data.updated: %s", exc)

    @staticmethod
    def _normalize_tags(tags: Iterable[Any]) -> List[str]:
        normalized: List[str] = []
        for tag in tags or []:
            if tag is None:
                continue
            tag_str = str(tag).strip()
            if tag_str:
                normalized.append(tag_str)
        return sorted({tag.lower(): tag for tag in normalized}.values())

    @staticmethod
    def _generate_request_id(section_id: str) -> str:
        return f"sec_req_{section_id}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"


_controller_singleton: Optional[SectionController] = None


def _discover_evidence_locker(bus: Any) -> Any:
    """Attempt to locate an Evidence Locker instance already registered with the bus."""
    if not bus:
        return None
    active_modules = getattr(bus, "active_modules", {})
    if isinstance(active_modules, dict):
        for module in active_modules.values():
            for attr_name in ("EVIDENCE_LOCKER", "evidence_locker", "locker", "locker_instance", "instance"):
                candidate = getattr(module, attr_name, None)
                if candidate is not None and hasattr(candidate, "get_common_pool"):
                    return candidate
    fallback = getattr(bus, "evidence_locker", None)
    if fallback is not None and hasattr(fallback, "get_common_pool"):
        return fallback
    return None


def initialize(bus: Any, evidence_locker: Any = None) -> SectionController:
    """Factory used by the Central Command bootstrap sequence."""
    global _controller_singleton
    locker = evidence_locker or _discover_evidence_locker(bus)
    if locker is None:
        logger.warning("[SECTION] Evidence Locker not detected; relying on manifest snapshots only")
    _controller_singleton = SectionController(bus=bus, evidence_locker=locker)
    return _controller_singleton


__all__ = ["SectionController", "initialize"]


