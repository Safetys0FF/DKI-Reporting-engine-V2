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
CURRENT_FILE = Path(__file__).resolve()
CURRENT_DIR = CURRENT_FILE.parent
UI_ROOT = CURRENT_DIR.parent
COMMAND_CENTER_ROOT = UI_ROOT.parent
INSTALL_ROOT = COMMAND_CENTER_ROOT.parent
MISSION_DEBRIEF_ROOT = COMMAND_CENTER_ROOT / "Mission Debrief"
PATH_CANDIDATES = [
    INSTALL_ROOT / "The Warden",
    INSTALL_ROOT / "Evidence Locker",
    INSTALL_ROOT / "The Marshall",
    COMMAND_CENTER_ROOT / "Data Bus" / "Bus Core Design",
    MISSION_DEBRIEF_ROOT,
    MISSION_DEBRIEF_ROOT / "The Librarian",
    MISSION_DEBRIEF_ROOT / "Debrief" / "README",
    MISSION_DEBRIEF_ROOT / "report generator",
]
for candidate in PATH_CANDIDATES:
    if candidate.exists():
        candidate_str = str(candidate)
        if candidate_str not in sys.path:
            sys.path.insert(0, candidate_str)

try:
    from report_generator import ReportGenerator, create_report_generator
except ImportError:
    ReportGenerator = None
    create_report_generator = None

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
            librarian=self.assembler,
        )

        self.report_generator = getattr(self.debrief, "central_report_generator", None)
        if not self.report_generator:
            factory = create_report_generator or ReportGenerator
            if factory:
                try:
                    self.report_generator = factory(ecc=self.warden.ecc, bus=self.bus)
                except Exception as exc:
                    self.log_event(f"Report generator initialisation failed: {exc}")

        if self.bus and hasattr(self.bus, "register_signal"):
            try:
                self.bus.register_signal("narrative.assemble_and_broadcast", self.assembler.assemble_and_broadcast)
            except Exception as exc:
                self.log_event(f"Failed to register narrative broadcast handler: {exc}")

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
        case_id = (
            processed_data.get("case_id")
            or (processed_data.get("metadata") or {}).get("case_id")
            or (processed_data.get("structured_data") or {}).get("case_id")
            or getattr(self.bus, "current_case_id", None)
        )
        return self.assembler.assemble_and_broadcast(section_id, processed_data, case_id=case_id)

    def get_case_summary(self, case_id: str) -> Dict[str, Any]:
        return self.debrief.get_summary(case_id)

    def build_complete_report_payload(
        self,
        *,
        case_id: Optional[str] = None,
        report_type: str = "Investigative",
        title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Compile section narratives and metadata for downstream export."""
        active_case = case_id or getattr(self.bus, "current_case_id", None)
        sections: Dict[str, Any] = {}
        if self.debrief and hasattr(self.debrief, "build_section_payloads"):
            try:
                sections = self.debrief.build_section_payloads(case_id=active_case)
            except Exception as exc:
                self.log_event(f"Failed to build section payloads: {exc}")
                sections = {}
        generated_at = datetime.now().isoformat()
        report_title = title or "Central Command Report"
        payload: Dict[str, Any] = {
            "title": report_title,
            "generated_at": generated_at,
            "case_id": active_case,
            "report_type": report_type,
            "sections": sections,
        }
        lines: List[str] = [report_title, f"Generated at: {generated_at}"]
        if active_case:
            lines.append(f"Case ID: {active_case}")
        ordered_ids: List[str]
        if self.debrief and hasattr(self.debrief, "SECTION_REGISTRY"):
            ordered_ids = list(self.debrief.SECTION_REGISTRY.keys())
        else:
            ordered_ids = sorted(sections.keys())
        seen = set()
        for section_id in ordered_ids:
            entry = sections.get(section_id)
            if not entry:
                continue
            seen.add(section_id)
            title_text = entry.get("title") or section_id
            content_text = entry.get("content") or entry.get("narrative") or ""
            lines.append("")
            lines.append(f"## {title_text}")
            if content_text:
                lines.append(content_text)
            else:
                lines.append("[No narrative available]")
        for section_id, entry in sections.items():
            if section_id in seen:
                continue
            title_text = entry.get("title") or section_id
            content_text = entry.get("content") or entry.get("narrative") or ""
            lines.append("")
            lines.append(f"## {title_text}")
            if content_text:
                lines.append(content_text)
            else:
                lines.append("[No narrative available]")
        payload["report_text"] = "\n".join(lines).strip()
        return payload

    # ------------------------------------------------------------------
    # Reporting helpers
    # ------------------------------------------------------------------
    def list_scanned_evidence(self) -> List[Dict[str, Any]]:
        """Return a copy of scanned evidence records."""
        return list(self.scanned_evidence)

    def generate_full_report(
        self,
        *,
        title: Optional[str] = None,
        case_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Aggregate scanned evidence into a simple report payload."""
        generated_at = datetime.now().isoformat()
        report_title = title or "Central Command Report"
        active_case = case_id or getattr(self.bus, "current_case_id", None)
        report_lines: List[str] = [report_title, f"Generated at: {generated_at}"]
        if active_case:
            report_lines.append(f"Case ID: {active_case}")
        if not self.scanned_evidence:
            report_lines.append("")
            report_lines.append("No evidence has been scanned yet.")
            return {
                "title": report_title,
                "generated_at": generated_at,
                "case_id": active_case,
                "sections": {},
                "report_text": "\n".join(report_lines).strip(),
            }

        sections: Dict[str, List[str]] = {}
        for entry in self.scanned_evidence:
            label = entry.get("display_label") or entry.get("category") or "Uncategorized"
            line = f"- {entry.get('name', 'Unnamed evidence')} (tags: {', '.join(entry.get('tags', [])) or 'n/a'})"
            sections.setdefault(label, []).append(line)

        section_text: Dict[str, str] = {}
        for label, lines in sections.items():
            section_body = "\n".join(lines)
            section_text[label] = section_body
            report_lines.append("")
            report_lines.append(f"## {label}")
            report_lines.append(section_body)

        return {
            "title": report_title,
            "generated_at": generated_at,
            "case_id": active_case,
            "sections": section_text,
            "report_text": "\n".join(report_lines).strip(),
        }

    def export_report(
        self,
        report_data: Optional[Dict[str, Any]],
        *,
        directory: Optional[str] = None,
        file_path: Optional[str] = None,
        export_format: Optional[str] = None,
        case_id: Optional[str] = None,
    ) -> str:
        """Export a full report, delegating to Mission Debrief for PDF/DOCX when available."""
        target_path = Path(file_path) if file_path else None
        fmt_token = (export_format or (target_path.suffix if target_path else "")).upper().lstrip('.') if (export_format or target_path) else ''
        active_case = case_id or (report_data or {}).get('case_id') or getattr(self.bus, 'current_case_id', None)

        def _ensure_payload() -> Dict[str, Any]:
            base_payload = self.build_complete_report_payload(case_id=active_case)
            if report_data:
                merged = dict(base_payload)
                merged.update({k: v for k, v in report_data.items() if k not in {'sections', 'report_text'}})
                merged_sections = dict(base_payload.get('sections', {}))
                incoming_sections = report_data.get('sections')
                if isinstance(incoming_sections, dict):
                    merged_sections.update(incoming_sections)
                merged['sections'] = merged_sections
                return merged
            return base_payload

        if fmt_token in {'PDF', 'DOCX'} and self.debrief:
            payload = _ensure_payload()
            payload['case_id'] = active_case or payload.get('case_id')
            options = {
                'case_id': payload.get('case_id'),
                'export_report': True,
                'export_format': fmt_token,
                'report_type': payload.get('report_type'),
            }
            if target_path:
                options['export_dir'] = str(target_path.parent)
                options['export_filename'] = target_path.name
            elif directory:
                export_dir = Path(directory)
                export_dir.mkdir(parents=True, exist_ok=True)
                options['export_dir'] = str(export_dir)
            result = self.debrief.process_complete_report(payload, options)
            if isinstance(result, dict) and result.get('status') == 'error':
                raise RuntimeError(result.get('error') or 'Report processing failed')
            final_path = result.get('final_report_path') or result.get('print_version_path') or result.get('report_export', {}).get('output_path')
            if not final_path and target_path:
                final_path = str(target_path)
            return str(final_path)

        text_payload = _ensure_payload()
        report_text = text_payload.get('report_text')
        if not report_text:
            sections = text_payload.get('sections', {})
            lines: List[str] = []
            for entry in sections.values():
                title_text = entry.get('title') or entry.get('section_id')
                content_text = entry.get('content') or entry.get('narrative') or ''
                lines.append(f"## {title_text}")
                if content_text:
                    lines.append(content_text)
                lines.append('')
            report_text = "\n".join(lines).strip() or "No report content available."
        if target_path is None:
            export_dir = Path(directory) if directory else (Path(__file__).resolve().parent / 'final_reports')
            export_dir.mkdir(parents=True, exist_ok=True)
            target_path = export_dir / f"central_command_report_{datetime.now():%Y%m%d_%H%M%S}.txt"
        else:
            target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(report_text, encoding='utf-8')
        return str(target_path)

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




