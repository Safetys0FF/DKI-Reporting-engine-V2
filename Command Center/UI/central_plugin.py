"""
central_plugin.py

Central Command GUI adapter around the shared bus/locker subsystems.
Exposes a thin facade so the GUI can store evidence, advertise category
needs, and request narratives without talking to legacy controllers.
"""
from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

# Ensure Central Command modules are importable
sys.path.append(r"F:\The Central Command\The Warden")
sys.path.append(r"F:\The Central Command\Evidence Locker")
sys.path.append(r"F:\The Central Command\The Marshall")
sys.path.append(r"F:\The Central Command\Command Center\Mission Debrief")
sys.path.append(r"F:\The Central Command\Command Center\Data Bus\Bus Core Design")

from warden_main import Warden
from evidence_locker_main import EvidenceLocker
from evidence_manager import EvidenceManager
from narrative_assembler import NarrativeAssembler
from mission_debrief_manager import MissionDebriefManager
from bus_core import DKIReportBus

from section_bus_adapter import SectionBusAdapter
from tag_taxonomy import TAG_TAXONOMY, resolve_tags


class CentralPlugin:
    """Base class for legacy plugin implementations (retained for compatibility)."""

    name: str = "UnnamedPlugin"
    version: str = "0.1"
    author: str = "Unknown"
    description: str = "No description provided."

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}

    # These hooks remain for backwards compatibility; no logic required here.
    def initialize(self) -> None:
        pass

    def shutdown(self) -> None:
        pass

    def handle_event(self, event_type: str, data: Any) -> None:
        pass


class CentralPluginAdapter:
    """Facade used by the GUI to interact with the Central Command stack."""

    def __init__(self) -> None:
        # Core bus + subsystem bootstrap
        self.bus = DKIReportBus()
        self.warden = Warden()
        self.warden.start_warden()

        self.evidence_locker = EvidenceLocker(
            ecc=self.warden.ecc,
            gateway=self.warden.gateway,
            bus=self.bus,
        )
        self.evidence_manager = EvidenceManager(
            ecc=self.warden.ecc,
            gateway=self.warden.gateway,
        )
        self.assembler = NarrativeAssembler(
            ecc=self.warden.ecc,
            bus=self.bus,
        )
        self.debrief = MissionDebriefManager(
            ecc=self.warden.ecc,
            bus=self.bus,
            gateway=self.warden.gateway,
        )

        # Section adapter keeps evidence requests in sync
        self.section_adapter = SectionBusAdapter(self)
        self.section_adapter.register_bus_handlers()
        self.section_adapter.issue_default_requests()

        self.scanned_evidence: List[Dict[str, Any]] = []

    def classify_evidence(self, file_path: str) -> Dict[str, Any]:
        """Run Evidence Locker classification without permanently storing the file."""
        try:
            return self.evidence_locker.classify_evidence(file_path)
        except Exception as exc:  # pragma: no cover - defensive
            self.log_event(f"Classification failed for {file_path}: {exc}")
            return {}

    def suggest_category_for_file(self, file_path: str) -> Dict[str, Any]:
        """Return a best-guess category/tags bundle for the provided file."""
        classification = self.classify_evidence(file_path) or {}
        tags = classification.get("tags") or []
        resolution = resolve_tags(tags=tags, file_path=file_path)
        slug = resolution.get("category")
        label = None
        if slug:
            profile = TAG_TAXONOMY.get(slug)
            if profile:
                label = profile.label
        suggestion = {
            "category": slug,
            "label": label,
            "tags": resolution.get("tags") or list({t.lower() for t in tags}),
            "related_sections": resolution.get("related_sections") or classification.get("related_sections") or [],
            "classification": classification,
        }
        suggestion["manual_tags"] = [t for t in suggestion["tags"] or []]
        return suggestion

    # ------------------------------------------------------------------
    # Evidence helpers
    # ------------------------------------------------------------------
    def store_file(self, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """Store evidence directly through the locker."""
        return self.evidence_locker.store(file_info)

    def scan_evidence(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send an evidence.scan request over the bus and record the evidence metadata."""
        response = self.send_to_bus("evidence.scan", payload)
        record: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "file_path": payload.get("file_path"),
            "name": payload.get("name"),
            "category": payload.get("category"),
            "tags": list(payload.get("tags", [])),
            "response": response,
        }
        slug = record.get("category")
        label = None
        if slug:
            for profile in TAG_TAXONOMY.values():
                if profile.slug == slug:
                    label = profile.label
                    break
        record["display_label"] = label or slug or "Uncategorized"
        self.scanned_evidence.append(record)
        if slug:
            try:
                self.advertise_category_need(slug, tags=record.get("tags"))
            except Exception as exc:
                self.log_event(f"Auto advertisement failed for {record.get('name')}: {exc}")
        return response

    # ------------------------------------------------------------------
    # Tagging helpers
    # ------------------------------------------------------------------
    def get_available_tag_categories(self) -> List[Dict[str, Any]]:
        """Return curated tag category metadata for GUI selectors."""
        catalog: List[Dict[str, Any]] = []
        for slug, profile in TAG_TAXONOMY.items():
            catalog.append(
                {
                    "slug": slug,
                    "label": profile.label,
                    "tags": list(profile.tags),
                    "aliases": list(profile.aliases),
                    "primary_section": profile.primary_section,
                    "related_sections": list(profile.related_sections),
                }
            )
        catalog.sort(key=lambda entry: entry["label"].lower())
        return catalog

    def advertise_category_need(
        self,
        category: str,
        *,
        tags: Optional[Iterable[str]] = None,
        priority: str = "normal",
        case_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Publish a section.needs message seeded with taxonomy data."""
        if not self.section_adapter:
            raise RuntimeError("Section adapter not initialised")
        return self.section_adapter.publish_category_need(
            category,
            tags=tags,
            case_id=case_id,
            priority=priority,
            requester="gui",
        )

    def get_section_updates(self, case_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return section update records captured by Mission Debrief."""
        updates = getattr(self.debrief, "section_updates", {})
        if isinstance(updates, dict):
            records = list(updates.values())
        elif isinstance(updates, list):
            records = list(updates)
        else:
            records = []
        case_key = str(case_id) if case_id else None
        if case_key:
            records = [
                record
                for record in records
                if (record.get("case_id") or (record.get("payload") or {}).get("case_id")) == case_key
            ]
        records.sort(key=lambda rec: rec.get("received_at") or (rec.get("payload") or {}).get("received_at") or "")
        return records

    def get_section_completion_log(self, case_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return section completion records emitted by the gateway."""
        log = getattr(self.debrief, "section_completion_log", [])
        records = list(log) if isinstance(log, list) else []
        case_key = str(case_id) if case_id else None
        if case_key:
            records = [
                record
                for record in records
                if (record.get("case_id") or (record.get("payload") or {}).get("case_id")) == case_key
            ]
        records.sort(key=lambda rec: rec.get("received_at") or (rec.get("payload") or {}).get("received_at") or "")
        return records

    # ------------------------------------------------------------------
    # Narrative / mission helpers
    # ------------------------------------------------------------------
    def generate_narrative(self, section_id: str, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a narrative for a section using the assembler."""
        return self.assembler.assemble(section_id, processed_data)

    def get_case_summary(self, case_id: str) -> Dict[str, Any]:
        return self.debrief.get_summary(case_id)

    # ------------------------------------------------------------------
    # Reporting helpers
    # ------------------------------------------------------------------
    def list_scanned_evidence(self) -> List[Dict[str, Any]]:
        """Return a copy of scanned evidence records."""
        return list(self.scanned_evidence)

    def generate_full_report(self, *, title: Optional[str] = None) -> Dict[str, Any]:
        """Aggregate scanned evidence into a simple report payload."""
        generated_at = datetime.now().isoformat()
        if not self.scanned_evidence:
            return {
                "title": title or "Central Command Report",
                "generated_at": generated_at,
                "sections": {},
                "report_text": "No evidence has been scanned yet.",
            }

        sections: Dict[str, List[str]] = {}
        for entry in self.scanned_evidence:
            label = entry.get("display_label") or entry.get("category") or "Uncategorized"
            line = f"- {entry.get('name', 'Unnamed evidence')} (tags: {', '.join(entry.get('tags', [])) or 'n/a'})"
            sections.setdefault(label, []).append(line)

        report_lines: List[str] = [title or "Central Command Report", f"Generated at: {generated_at}"]
        section_text: Dict[str, str] = {}
        for label, lines in sections.items():
            section_body = "\n".join(lines)
            section_text[label] = section_body
            report_lines.append("")
            report_lines.append(f"## {label}")
            report_lines.append(section_body)

        return {
            "title": title or "Central Command Report",
            "generated_at": generated_at,
            "sections": section_text,
            "report_text": "\n".join(report_lines),
        }

    def export_report(
        self,
        report_data: Dict[str, Any],
        *,
        directory: Optional[str] = None,
        file_path: Optional[str] = None,
    ) -> str:
        """Persist the report text to disk and return the file path."""
        if not report_data:
            raise ValueError("Report data is empty")
        report_text = report_data.get("report_text", "")
        if not report_text:
            raise ValueError("Report text is empty")

        if file_path:
            target = Path(file_path)
            target.parent.mkdir(parents=True, exist_ok=True)
        else:
            directory = directory or str(Path(__file__).resolve().parent / "final_reports")
            Path(directory).mkdir(parents=True, exist_ok=True)
            filename = f"central_command_report_{datetime.now():%Y%m%d_%H%M%S}.txt"
            target = Path(directory) / filename

        target.write_text(report_text, encoding="utf-8")
        return str(target)

    # ------------------------------------------------------------------
    # Bus helpers
    # ------------------------------------------------------------------
    def log_event(self, message: str) -> None:
        if self.bus:
            self.bus.log_event("GUI", message)

    def send_to_bus(self, topic: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send a payload through the DKI bus system and unwrap the response."""
        if not self.bus:
            return {"status": "error", "error": "Bus not available"}
        try:
            self.log_event(f"Sending to bus: {topic}")
            result = self.bus.send(topic=topic, data=payload)
            if isinstance(result, dict):
                if result.get("responses"):
                    last = result["responses"][-1]
                    if isinstance(last, dict):
                        return last
                return result
            return {"result": result}
        except Exception as exc:  # pragma: no cover - defensive
            self.log_event(f"Bus send error: {exc}")
            return {"status": "error", "error": str(exc)}
# Exportable object for convenience
central_plugin = CentralPluginAdapter()

__all__ = [
    "CentralPlugin",
    "CentralPluginAdapter",
    "central_plugin",
]

