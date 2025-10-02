from __future__ import annotations

import sys
import json
import logging
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, TYPE_CHECKING

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tag_taxonomy import TAG_TAXONOMY, resolve_tags

if TYPE_CHECKING:  # pragma: no cover
    from central_plugin import CentralPlugin

logger = logging.getLogger(__name__)

DISCLOSURE_PATH = Path(__file__).with_name("disclosures_catalog.json")

SECTION_SUBSCRIPTIONS: Dict[str, Dict[str, Any]] = {
    "section_1": {
        "description": "Client intake and background context",
        "categories": ["intake", "background"],
    },
    "section_2": {
        "description": "Geo-tagged context and scene capture",
        "categories": ["geo"],
    },
    "section_3": {
        "description": "Field surveillance and notes",
        "categories": ["field_notes", "media_audio"],
    },
    "section_4": {
        "description": "Data and open-record findings",
        "categories": ["data_report"],
    },
    "section_5": {
        "description": "Contracts, correspondence, supporting docs",
        "categories": ["contract", "communication"],
    },
    "section_6": {
        "description": "Billing reconciliation and time logs",
        "categories": ["billing"],
    },
    "section_7": {
        "description": "Cross-section analytics",
        "categories": ["data_report"],
    },
    "section_8": {
        "description": "Media catalog (photos / video)",
        "categories": ["media_photo", "media_video"],
    },
}


class SectionBusAdapter:
    """Coordinates section-level evidence requests and enrichment publishing."""

    def __init__(self, plugin: Any):
        self.plugin = plugin
        self.bus = getattr(plugin, "bus", None)
        self.logger = logging.getLogger("section_bus_adapter")
        self._handlers_registered = False
        self.disclosures = self._load_disclosures()

    def register_bus_handlers(self) -> None:
        if not self.bus or not hasattr(self.bus, "register_signal"):
            return
        if self._handlers_registered:
            return
        self.bus.register_signal("section.needs", self._handle_section_needs_signal)
        self.bus.register_signal("evidence.deliver", self._handle_evidence_deliver_signal)
        self._handlers_registered = True
        self.logger.debug("Section bus adapter handlers registered")

    def publish_category_need(
        self,
        category: str,
        *,
        tags: Optional[Iterable[str]] = None,
        case_id: Optional[str] = None,
        priority: str = "normal",
        requester: str = "section_adapter.gui",
    ) -> Dict[str, Any]:
        if not self.bus:
            raise RuntimeError("SectionBusAdapter requires a bus instance")
        resolution = resolve_tags(category=category, tags=tags)
        normalized_tags = resolution.get("tags") or []
        payload: Dict[str, Any] = {
            "category": resolution.get("category") or category,
            "tags": normalized_tags,
            "filters": {"tags": normalized_tags} if normalized_tags else {},
            "priority": priority,
            "case_id": case_id or getattr(self.bus, "current_case_id", None),
            "requested_at": datetime.now().isoformat(),
            "requester": requester,
        }
        primary_section = resolution.get("primary_section")
        if primary_section:
            payload["section_id"] = primary_section
        related_sections = resolution.get("related_sections") or []
        if related_sections:
            payload["related_sections"] = related_sections
        if not payload["filters"] and primary_section:
            payload["filters"] = {"section_id": primary_section}
        self.logger.debug("GUI advertised %s with tags %s", category, normalized_tags)
        self.bus.emit("section.needs", payload)
        return payload

    def issue_default_requests(self, *, case_id: Optional[str] = None) -> None:
        if not self.bus:
            return
        case_reference = case_id or getattr(self.bus, "current_case_id", None)
        for section_id, config in SECTION_SUBSCRIPTIONS.items():
            categories = config.get("categories") or []
            if not categories:
                categories = [section_id]
            for category in categories:
                resolution = resolve_tags(category=category)
                tags = resolution.get("tags") or []
                filters: Dict[str, Any] = {}
                if tags:
                    filters["tags"] = tags
                category_slug = resolution.get("category")
                if category_slug:
                    filters["category"] = category_slug
                else:
                    filters.setdefault("category", category)
                if not filters.get("tags"):
                    filters["section_id"] = section_id
                payload = {
                    "section_id": section_id,
                    "filters": filters,
                    "priority": "high" if section_id in {"section_3", "section_6", "section_8"} else "normal",
                    "case_id": case_reference,
                    "requested_at": datetime.now().isoformat(),
                    "requester": f"section_adapter.{section_id}",
                    "category": category_slug or category,
                    "tags": filters.get("tags"),
                }
                related = resolution.get("related_sections") or []
                if related:
                    payload["related_sections"] = related
                self.logger.debug("Priming evidence.request for %s with tags %s", section_id, filters.get("tags"))
                self.bus.emit("evidence.request", payload)
        self._publish_summary_sections()

    def publish_enriched_payload(self, section_id: str, evidence_payload: Dict[str, Any]) -> None:
        if not self.bus:
            return
        payload = dict(evidence_payload)
        payload.setdefault("section_id", section_id)
        payload.setdefault("timestamp", datetime.now().isoformat())
        payload.setdefault("source", f"section_adapter.{section_id}")
        self.logger.debug("Publishing evidence.updated for %s -> %s", section_id, payload.get("evidence_id"))
        self.bus.emit("evidence.updated", payload)

    def _handle_section_needs_signal(self, payload: Any) -> None:
        if not isinstance(payload, dict) or not self.bus:
            return
        if str(payload.get("source", "")).startswith("section_adapter"):
            return
        section_id = payload.get("section_id") or payload.get("section")
        if not section_id:
            return
        filters = dict(payload.get("filters") or {})
        raw_tags = payload.get("tags") or filters.get("tags")
        category_hint = payload.get("category") or payload.get("tag_category")
        resolution = resolve_tags(category=category_hint, tags=raw_tags)
        normalized_tags = resolution.get("tags") or []
        if normalized_tags:
            filters["tags"] = normalized_tags
        elif "tags" in filters and not filters.get("tags"):
            filters.pop("tags", None)
        evidence_type = payload.get("evidence_type")
        if evidence_type and "evidence_type" not in filters:
            filters["evidence_type"] = evidence_type
        if not filters.get("tags") and "section_id" not in filters:
            filters["section_id"] = section_id
        request_payload = {
            "section_id": section_id,
            "filters": filters,
            "priority": payload.get("priority", "normal"),
            "case_id": payload.get("case_id") or getattr(self.bus, "current_case_id", None),
            "requested_at": datetime.now().isoformat(),
            "request_id": payload.get("request_id"),
            "requester": f"section_adapter.{section_id}",
            "category": resolution.get("category") or category_hint,
            "tags": filters.get("tags"),
        }
        related_sections = resolution.get("related_sections") or payload.get("related_sections") or []
        if related_sections:
            request_payload["related_sections"] = related_sections
        self.logger.debug("Responding to section.needs for %s with filters %s", section_id, filters)
        self.bus.emit("evidence.request", request_payload)

    def _handle_evidence_deliver_signal(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        section_id = payload.get("recipient") or payload.get("section_id")
        evidence_id = payload.get("evidence_id")
        if not section_id or not evidence_id:
            return
        classification = payload.get("classification") or {}
        tags = payload.get("tags") or classification.get("tags") or []
        category_hint = payload.get("category") or payload.get("tag_category")
        resolution = resolve_tags(category=category_hint, tags=tags)
        normalized_tags = resolution.get("tags") or []
        if normalized_tags:
            classification["tags"] = normalized_tags
        summary_note = payload.get("summary") or classification.get("routing_notes")
        related_sections = payload.get("related_sections") or resolution.get("related_sections") or []
        enriched_payload = {
            "section_id": section_id,
            "case_id": payload.get("case_id") or getattr(self.bus, "current_case_id", None),
            "evidence_id": evidence_id,
            "file_path": payload.get("file_path"),
            "classification": classification,
            "tags": normalized_tags or tags,
            "category": resolution.get("category") or category_hint,
            "related_sections": related_sections,
            "filters": payload.get("filters") or {},
            "delivery_timestamp": payload.get("timestamp") or datetime.now().isoformat(),
            "status": "delivered",
            "summary": summary_note or f"Evidence {evidence_id} delivered to {section_id}",
            "priority": payload.get("priority", "normal"),
        }
        if payload.get("analysis"):
            enriched_payload["analysis"] = payload["analysis"]
        self.publish_enriched_payload(section_id, enriched_payload)

    def _publish_summary_sections(self) -> None:
        if not self.bus:
            return
        manifest_entries = self._fetch_manifest_entries()
        billing_summary, billing_items = self._build_billing_summary(manifest_entries)
        analytics_snapshot = self._build_analytics_snapshot(manifest_entries)
        if billing_summary:
            self.publish_enriched_payload(
                "section_6",
                {
                    "summary": billing_summary,
                    "items": billing_items,
                },
            )
        if analytics_snapshot:
            self.publish_enriched_payload("section_7", analytics_snapshot)
        if self.disclosures:
            self.publish_enriched_payload("section_dp", {"disclosures": self.disclosures})

    def _fetch_manifest_entries(self) -> List[Dict[str, Any]]:
        if not self.bus or not hasattr(self.bus, "get_evidence_manifest"):
            return []
        try:
            manifest = self.bus.get_evidence_manifest()
        except Exception:  # pragma: no cover - defensive
            return []
        if isinstance(manifest, list):
            return [dict(entry) for entry in manifest]
        if isinstance(manifest, dict):
            return [dict(entry) for entry in manifest.values()]
        return []

    def _build_billing_summary(self, entries: List[Dict[str, Any]]) -> (Dict[str, Any], List[Dict[str, Any]]):
        billing_entries: List[Dict[str, Any]] = []
        total_hours = 0.0
        total_mileage = 0.0
        total_amount = 0.0
        for entry in entries:
            tags = {
                str(tag).lower()
                for tag in entry.get("tags", [])
                or entry.get("classification", {}).get("tags", [])
            }
            assigned = str(entry.get("section_hint") or entry.get("assigned_section") or "").lower()
            if assigned == "section_6" or tags.intersection({"billing", "mileage", "expense"}):
                billing_entries.append(entry)
                details = (
                    entry.get("classification", {}).get("billing_details")
                    or entry.get("metadata", {}).get("billing_details")
                    or {}
                )
                try:
                    total_hours += float(details.get("hours", 0))
                except Exception:
                    pass
                try:
                    total_mileage += float(details.get("mileage", 0))
                except Exception:
                    pass
                amount = details.get("amount") or entry.get("billing_amount")
                try:
                    total_amount += float(amount)
                except Exception:
                    pass
        summary = {
            "count": len(billing_entries),
            "total_hours": round(total_hours, 2),
            "total_mileage": round(total_mileage, 2),
            "total_amount": round(total_amount, 2),
        }
        return summary, billing_entries

    def _build_analytics_snapshot(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not entries:
            return {}
        section_counter = Counter()
        tag_counter = Counter()
        enriched_counter = 0
        for entry in entries:
            assigned = entry.get("section_hint") or entry.get("assigned_section")
            if assigned:
                section_counter[str(assigned)] += 1
            tags = entry.get("tags") or entry.get("classification", {}).get("tags", []) or []
            tag_counter.update({str(tag).lower(): 1 for tag in tags})
            if entry.get("history"):
                enriched_counter += 1
        analytics = {
            "total_evidence": len(entries),
            "sections": dict(section_counter),
            "top_tags": tag_counter.most_common(5),
            "enriched_items": enriched_counter,
            "generated_at": datetime.now().isoformat(),
        }
        return {"analytics": analytics}

    def _load_disclosures(self) -> List[Dict[str, Any]]:
        if DISCLOSURE_PATH.exists():
            try:
                with DISCLOSURE_PATH.open("r", encoding="utf-8-sig") as fh:
                    data = json.load(fh)
                    if isinstance(data, list):
                        return data
            except Exception as exc:  # pragma: no cover - fallback for safety
                logger.warning("Failed to load disclosures catalog: %s", exc)
        return [
            {
                "id": "standard",
                "title": "Standard Investigative Disclosure",
                "body": (
                    "All investigative activities were conducted in compliance with state and "
                    "federal regulations, and findings are presented to the best of our professional knowledge."
                ),
            },
            {
                "id": "confidential",
                "title": "Confidentiality Notice",
                "body": (
                    "This report contains sensitive investigative material. Redistribution or disclosure is limited "
                    "to authorized recipients under the governing contract."
                ),
            },
        ]


__all__ = ["SectionBusAdapter", "SECTION_SUBSCRIPTIONS"]
