"""
central_plugin.py

Central Command GUI adapter around the shared bus/locker subsystems.
Exposes a thin facade so the GUI can store evidence, advertise category
needs, and request narratives without talking to legacy controllers.
"""
from __future__ import annotations

import json
import sys
import socket
from pathlib import Path
from datetime import datetime, date
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

# Ensure Central Command modules are importable
CURRENT_FILE = Path(__file__).resolve()
UI_ROOT = CURRENT_FILE.parent
COMMAND_CENTER_ROOT = UI_ROOT.parent
INSTALL_ROOT = COMMAND_CENTER_ROOT.parent
MISSION_DEBRIEF_ROOT = COMMAND_CENTER_ROOT / "Mission Debrief"
PATH_CANDIDATES = [
    INSTALL_ROOT / "The Warden",
    INSTALL_ROOT / "Evidence Locker",
    INSTALL_ROOT / "The Marshall",
    COMMAND_CENTER_ROOT / "Data Bus" / "Bus Core Design",
    COMMAND_CENTER_ROOT / "Start Menu" / "Run Time",
    MISSION_DEBRIEF_ROOT,
    MISSION_DEBRIEF_ROOT / "The Librarian",
    MISSION_DEBRIEF_ROOT / "Debrief" / "README",
    MISSION_DEBRIEF_ROOT / "report generator",
    INSTALL_ROOT / "The War Room" / "case_dev",
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

from case_session import CaseSession, EvidenceCardState, SectionState, ExportSettings
from case_catalog import (
    save_session as catalog_save_session,
    load_session as catalog_load_session,
    touch_case as catalog_touch_case,
    ensure_case_folder as catalog_ensure_folder,
    list_cases as catalog_list_cases,
    load_metadata as catalog_load_metadata,
    load_artifacts as catalog_load_artifacts,
    get_lock_info as catalog_get_lock_info,
    set_lock_info as catalog_set_lock_info,
    clear_lock as catalog_clear_lock,
)

DEFAULT_SECTION_SEQUENCE = [
    "section_1",
    "section_2",
    "section_3",
    "section_4",
    "section_5",
    "section_8",
    "section_7",
    "section_6",
    "section_9",
]


DEFAULT_EXPORT_ROOT = INSTALL_ROOT / "Generated Reports"


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

        self.operator_name = "Operator"
        self.host_identifier = socket.gethostname() or "host"

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
        self.operator_guard: Optional[Callable[[str, Optional[str]], bool]] = None
        self.section_adapter.register_bus_handlers()
        self.section_adapter.issue_default_requests()

        self.scanned_evidence: List[Dict[str, Any]] = []
        self.case_session: Optional[CaseSession] = None
        self._evidence_counter: int = 0
        self._register_internal_signal_handlers()

    # ------------------------------------------------------------------
    # Case session helpers
    # ------------------------------------------------------------------
    def _register_internal_signal_handlers(self) -> None:
        if not self.bus or not hasattr(self.bus, "register_signal"):
            return
        signal_map = {
            "section.data.updated": self._handle_section_data_updated_signal,
            "narrative.assembled": self._handle_narrative_assembled_signal,
            "mission_debrief.section.complete": self._handle_section_complete_signal,
        }
        for signal, handler in signal_map.items():
            try:
                self.bus.register_signal(signal, handler)
            except Exception as exc:  # pragma: no cover - defensive
                self.log_event(f"Failed to register handler for {signal}: {exc}")

    def _ensure_session(self) -> CaseSession:
        if not self.case_session:
            raise RuntimeError("No active case session")
        return self.case_session

    def start_case(
        self,
        case_id: str,
        investigator: str,
        *,
        subcontractor: bool = False,
        contract_signed: Optional[str] = None,
        export_root: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CaseSession:
        contract_date: Optional[date] = None
        if contract_signed:
            try:
                contract_date = date.fromisoformat(contract_signed)
            except ValueError:
                self.log_event(f"Invalid contract date '{contract_signed}' for case {case_id}")
        self._acquire_case_lock(case_id)
        session = CaseSession(
            case_id=case_id,
            investigator=investigator,
            subcontractor=subcontractor,
            contract_signed=contract_date,
            status="in_progress",
        )
        for section_id in DEFAULT_SECTION_SEQUENCE:
            session.ensure_section(section_id)
        if export_root:
            session.export_settings.export_root = export_root
        if metadata:
            session.extra.update(metadata)
        self.case_session = session
        catalog_ensure_folder(case_id)
        catalog_save_session(session)
        catalog_touch_case(case_id)
        return session

    def load_case(self, case_id: str) -> Optional[CaseSession]:
        session = catalog_load_session(case_id)
        if session:
            self.case_session = session
            catalog_touch_case(case_id)
        return session

    def save_case(self, *, status: Optional[str] = None) -> None:
        if not self.case_session:
            return
        if status:
            self.case_session.status = status  # type: ignore[assignment]
        catalog_save_session(self.case_session)
        catalog_touch_case(self.case_session.case_id)

    def update_export_settings(
        self,
        *,
        case_id: Optional[str] = None,
        export_root: Optional[str] = None,
        formats: Optional[Iterable[str]] = None,
        include_cover: Optional[bool] = None,
        include_toc: Optional[bool] = None,
        include_disclosure: Optional[bool] = None,
        disclosure_title: Optional[str] = None,
        disclosure_text: Optional[str] = None,
        disclosures: Optional[Iterable[str]] = None,
    ) -> ExportSettings:
        session = self.case_session
        if case_id and (not session or session.case_id != case_id):
            session = catalog_load_session(case_id)
            if not session:
                raise ValueError(f"Case {case_id} not found")
            self.case_session = session
        if not session:
            raise ValueError("No active case session available")

        updates: Dict[str, Any] = {}
        if export_root is not None:
            updates["export_root"] = str(export_root)

        normalized_formats: Optional[List[str]] = None
        if formats is not None:
            normalized_formats = []
            seen_formats = set()
            for fmt in formats:
                token = str(fmt).strip().upper()
                if not token or token in seen_formats:
                    continue
                normalized_formats.append(token)
                seen_formats.add(token)
            if not normalized_formats:
                existing = session.export_settings.formats
                normalized_formats = list(existing) if existing else ["PDF"]
            updates["formats"] = normalized_formats

        normalized_disclosures: Optional[List[str]] = None
        if disclosures is not None:
            normalized_disclosures = []
            seen_ids = set()
            for entry in disclosures:
                key = str(entry).strip()
                if not key or key in seen_ids:
                    continue
                normalized_disclosures.append(key)
                seen_ids.add(key)
            updates["disclosures"] = normalized_disclosures

        if include_cover is not None:
            updates["include_cover"] = bool(include_cover)
        if include_toc is not None:
            updates["include_toc"] = bool(include_toc)
        if include_disclosure is not None:
            updates["include_disclosure"] = bool(include_disclosure)

        if disclosure_title is not None:
            title_value = disclosure_title.strip() if isinstance(disclosure_title, str) else disclosure_title
            updates["disclosure_title"] = title_value or None
        if disclosure_text is not None:
            text_value = disclosure_text.strip() if isinstance(disclosure_text, str) else disclosure_text
            updates["disclosure_text"] = text_value or None

        if normalized_disclosures is not None:
            composed_title, composed_text, _ = self._compose_disclosure_content(
                session.export_settings,
                selection=normalized_disclosures,
                disclosure_title=updates.get("disclosure_title"),
                disclosure_text=updates.get("disclosure_text"),
            )
            if "disclosure_title" not in updates and composed_title is not None:
                updates["disclosure_title"] = composed_title
            if "disclosure_text" not in updates and composed_text is not None:
                updates["disclosure_text"] = composed_text

        settings = session.update_export_settings(**updates)
        catalog_save_session(session)
        catalog_touch_case(session.case_id)
        return settings

    def run_export_workflow(
        self,
        *,
        case_id: Optional[str] = None,
        export_root: Optional[str] = None,
        formats: Optional[Iterable[str]] = None,
    ) -> Dict[str, Any]:
        session = self.case_session
        if case_id and (not session or session.case_id != case_id):
            session = catalog_load_session(case_id)
            if not session:
                raise ValueError(f"Case {case_id} not found")
            self.case_session = session
        if not session:
            raise ValueError("No active case session available")

        configured_formats = formats if formats is not None else session.export_settings.formats
        normalized_formats: List[str] = []
        seen_formats = set()
        for fmt in configured_formats or ["PDF"]:
            token = str(fmt).strip().upper()
            if not token or token in seen_formats:
                continue
            normalized_formats.append(token)
            seen_formats.add(token)
        if not normalized_formats:
            normalized_formats = ["PDF"]

        export_root_path = Path(export_root or session.export_settings.export_root or DEFAULT_EXPORT_ROOT)
        export_root_path.mkdir(parents=True, exist_ok=True)
        safe_case_id = self._sanitize_case_id(session.case_id)
        case_folder = export_root_path / safe_case_id
        case_folder.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        artifacts: Dict[str, str] = {}
        for fmt in normalized_formats:
            fmt_token = fmt.upper()
            if fmt_token == "PDF":
                extension = "pdf"
            elif fmt_token == "DOCX":
                extension = "docx"
            elif fmt_token in {"TXT", "TEXT"}:
                extension = "txt"
            else:
                extension = fmt_token.lower()
            target_file = case_folder / f"{safe_case_id}_{timestamp}.{extension}"
            try:
                exported_path = self.export_report(
                    report_data=None,
                    file_path=str(target_file),
                    export_format=fmt_token,
                    case_id=session.case_id,
                )
            except Exception as exc:
                self.log_event(f"Export failed for format {fmt_token}: {exc}")
                raise
            artifacts[fmt_token] = exported_path

        audit_path = self._generate_audit_bundle(
            session=session,
            case_folder=case_folder,
            artifacts=dict(artifacts),
            formats=normalized_formats,
            timestamp=timestamp,
        )
        if audit_path:
            artifacts['AUDIT_TRAIL'] = audit_path

        session.export_settings.export_root = str(export_root_path)
        self._finalize_case_after_export(session, artifacts)
        self.log_event(
            f"Exported case {session.case_id} to {case_folder} in formats {', '.join(artifacts.keys())}"
        )
        return {
            "case_id": session.case_id,
            "export_root": str(case_folder),
            "artifacts": artifacts,
            "audit_trail": audit_path,
        }

    def _finalize_case_after_export(self, session: CaseSession, artifacts: Dict[str, Any]) -> None:
        for card in session.evidence.values():
            try:
                card.status = "exported"
            except AttributeError:
                continue
        session.mark_saved(status="completed")
        catalog_save_session(session, artifacts=artifacts)
        catalog_touch_case(session.case_id)
        self._release_case_lock(session.case_id)
        self.scanned_evidence.clear()
        self.case_session = None

    def list_cases(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            return catalog_list_cases(status=status)
        except Exception:
            return []

    def set_operator_guard(self, guard: Optional[Callable[[str, Optional[str]], bool]]) -> None:
        self.operator_guard = guard

    def _operator_permitted(self, action: str, case_id: Optional[str] = None) -> bool:
        if self.operator_guard is None:
            return True
        try:
            return bool(self.operator_guard(action, case_id))
        except Exception:
            return True

    def get_active_session(self) -> Optional[CaseSession]:
        return self.case_session

    def peek_case_session(self, case_id: str) -> Optional[CaseSession]:
        try:
            return catalog_load_session(case_id)
        except Exception:
            return None

    def register_evidence_card(self, payload: Dict[str, Any]) -> EvidenceCardState:
        session = self._ensure_session()
        file_path = payload.get("file_path", "")
        evidence_id = payload.get("evidence_id") or self._generate_evidence_id(file_path)
        card = EvidenceCardState(
            evidence_id=evidence_id,
            file_path=file_path,
            section_id=payload.get("section_id"),
            tags=list(payload.get("tags", [])),
            notes=payload.get("notes"),
            metadata=dict(payload.get("metadata", {})),
        )
        status_value = payload.get("status")
        if isinstance(status_value, str):
            card.status = status_value  # type: ignore[assignment]
        if not self._operator_permitted("upload_evidence", session.case_id):
            raise PermissionError("Operator not permitted to upload evidence")
        session.upsert_evidence(card)
        session.mark_saved(status="in_progress")
        catalog_save_session(session)
        return card

    def remove_evidence_card(self, evidence_id: Optional[str]) -> None:
        if not evidence_id or not self.case_session:
            return
        session = self.case_session
        if evidence_id in session.evidence:
            if not self._operator_permitted("delete_evidence", session.case_id):
                raise PermissionError("Operator not permitted to delete evidence")
            session.remove_evidence(evidence_id)
            session.mark_saved(status=session.status)
            catalog_save_session(session)
            catalog_touch_case(session.case_id)


    def process_evidence_batch(self, *, case_id: Optional[str] = None) -> List[Dict[str, Any]]:
        session = self.case_session
        if case_id and (not session or session.case_id != case_id):
            session = catalog_load_session(case_id)
            if session:
                self.case_session = session
        if not session:
            raise ValueError('No active case session available')
        if not session.evidence:
            return []
        if not self._operator_permitted('process_evidence', session.case_id):
            raise PermissionError('Operator not permitted to process evidence')
        results: List[Dict[str, Any]] = []
        for card in session.evidence.values():
            payload = {
                'case_id': session.case_id,
                'evidence_id': card.evidence_id,
                'file_path': card.file_path,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
            }
            try:
                response = self.send_to_bus('evidence.process_comprehensive', payload)
            except Exception as exc:
                response = {'status': 'error', 'error': str(exc)}
            results.append({
                'case_id': session.case_id,
                'evidence_id': card.evidence_id,
                'file_path': card.file_path,
                'response': response,
            })
        catalog_touch_case(session.case_id)
        return results

    def mark_section_approved(self, section_id: str) -> Optional[SectionState]:
        if not section_id:
            return None
        session = self.case_session
        if not session:
            return None
        state = session.ensure_section(section_id)
        if session.status in {"new", "paused"}:
            session.status = "in_progress"
        state.approve()
        self.save_case(status=session.status)
        return state

    def pause_case(self) -> Optional[CaseSession]:
        session = self.case_session
        if not session:
            return None
        session.status = "paused"
        self.save_case(status="paused")
        paused_session = session
        self._release_case_lock(session.case_id)
        self.case_session = None
        return paused_session

    def resume_case(self, case_id: str) -> Optional[CaseSession]:
        if not case_id:
            return None
        session = catalog_load_session(case_id)
        if session:
            self._acquire_case_lock(case_id)
            self.case_session = session
            catalog_touch_case(case_id)
        return session

    def reopen_case(self, case_id: str) -> CaseSession:
        if not case_id:
            raise ValueError('case_id is required to re-open a case')
        session = catalog_load_session(case_id)
        if not session:
            raise ValueError(f'Case {case_id} not found in catalog')
        self._acquire_case_lock(case_id)
        session.status = 'in_progress'
        session.mark_saved(status='in_progress')
        catalog_save_session(session)
        catalog_touch_case(case_id)
        self.case_session = session
        return session

    def _generate_evidence_id(self, file_path: Optional[str]) -> str:
        self._evidence_counter += 1
        if file_path:
            stem = Path(file_path).stem.replace(" ", "_")
        else:
            stem = "evidence"
        return f"{stem}_{self._evidence_counter:04d}"

    def _sanitize_case_id(self, case_id: str) -> str:
        token = "".join(ch if str(ch).isalnum() or ch in "-_" else "_" for ch in case_id.strip())
        return token or "case"

    def _handle_section_data_updated_signal(self, payload: Dict[str, Any]) -> None:
        if not isinstance(payload, dict) or not self.case_session:
            return
        section_id = payload.get("section_id") or payload.get("sectionId")
        if not section_id:
            return
        session = self.case_session
        state = session.ensure_section(section_id)
        narrative = payload.get("narrative") or payload.get("content")
        if narrative:
            state.narrative = narrative
        state.assembler_metadata = dict(payload)
        state.needs_review = True
        state.status = "ready"
        state.last_updated = datetime.utcnow()
        catalog_save_session(session)

    def _handle_narrative_assembled_signal(self, payload: Dict[str, Any]) -> None:
        if not isinstance(payload, dict) or not self.case_session:
            return
        section_id = payload.get("section_id")
        if not section_id:
            return
        session = self.case_session
        state = session.ensure_section(section_id)
        narrative = payload.get("narrative") or payload.get("draft")
        if narrative:
            state.narrative = narrative
        state.needs_review = True
        state.status = "ready"
        state.last_updated = datetime.utcnow()
        catalog_save_session(session)

    def _handle_section_complete_signal(self, payload: Dict[str, Any]) -> None:
        if not isinstance(payload, dict) or not self.case_session:
            return
        section_id = payload.get("section_id")
        if not section_id:
            return
        state = self.case_session.ensure_section(section_id)
        if state.status != "approved":
            state.status = "ready"
        state.last_updated = datetime.utcnow()
        catalog_save_session(self.case_session)

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
        response_data = response if isinstance(response, dict) else {}
        record: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "file_path": payload.get("file_path"),
            "name": payload.get("name"),
            "category": payload.get("category"),
            "tags": list(payload.get("tags", [])),
            "response": response if response_data == {} else response_data,
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
        if self.case_session:
            evidence_payload = {
                "evidence_id": payload.get("evidence_id") or response_data.get("evidence_id"),
                "file_path": payload.get("file_path") or record.get("file_path") or "",
                "section_id": payload.get("section_id"),
                "tags": record.get("tags", []),
                "notes": payload.get("notes"),
                "metadata": record,
                "status": "classified",
            }
            try:
                self.register_evidence_card(evidence_payload)
            except Exception as exc:
                self.log_event(f"Failed to register evidence card: {exc}")
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

    def generate_export_preview(
        self,
        *,
        case_id: Optional[str] = None,
        include_cover: Optional[bool] = None,
        include_toc: Optional[bool] = None,
        include_disclosure: Optional[bool] = None,
        disclosure_text: Optional[str] = None,
        disclosure_title: Optional[str] = None,
        sections: Optional[Dict[str, Any]] = None,
        disclosures: Optional[Iterable[str]] = None,
    ) -> Dict[str, Any]:
        if not self.debrief or not hasattr(self.debrief, "generate_export_preview"):
            return {}
        session = self.case_session
        if case_id and (not session or session.case_id != case_id):
            session = catalog_load_session(case_id)
            if session and (self.case_session is None or self.case_session.case_id == session.case_id):
                self.case_session = session
        settings = getattr(session, "export_settings", None)
        if include_cover is None:
            include_cover = settings.include_cover if settings else True
        if include_toc is None:
            include_toc = settings.include_toc if settings else True
        if include_disclosure is None:
            include_disclosure = settings.include_disclosure if settings else True

        selection = disclosures
        if selection is None and settings:
            selection = settings.disclosures

        resolved_title, resolved_text, resolved_entries = self._compose_disclosure_content(
            settings,
            selection=selection,
            disclosure_title=disclosure_title,
            disclosure_text=disclosure_text,
        )
        try:
            preview = self.debrief.generate_export_preview(
                case_id or (session.case_id if session else None),
                include_cover=include_cover,
                include_toc=include_toc,
                include_disclosure=include_disclosure,
                disclosure_text=resolved_text,
                disclosure_title=resolved_title,
                sections=sections,
            )
        except Exception as exc:
            self.log_event(f"Export preview failed: {exc}")
            return {"error": str(exc), "status": "error"}

        if not isinstance(preview, dict):
            return {"error": "Preview generator returned unexpected payload", "status": "error"}

        payload = dict(preview)
        payload.setdefault("include_cover", include_cover)
        payload.setdefault("include_toc", include_toc)
        payload.setdefault("include_disclosure", include_disclosure)
        payload["selected_disclosures"] = list(selection or [])
        payload["resolved_disclosures"] = resolved_entries
        if resolved_title is not None:
            payload["disclosure_title"] = resolved_title
        if resolved_text is not None:
            payload["disclosure_text"] = resolved_text
        return payload

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

    def get_disclosure_catalog(self) -> List[Dict[str, Any]]:
        """Expose the disclosure catalog loaded by the section adapter."""
        adapter = getattr(self, "section_adapter", None)
        if not adapter:
            return []
        catalog = getattr(adapter, "disclosures", None)
        if isinstance(catalog, list):
            return list(catalog)
        return []

    def _resolve_disclosure_entries(self, selections: Iterable[str]) -> List[Dict[str, Any]]:
        catalog_index: Dict[str, Dict[str, Any]] = {}
        for entry in self.get_disclosure_catalog():
            key = str(entry.get("id") or entry.get("slug") or entry.get("title") or "")
            if key:
                catalog_index[key] = entry
        results: List[Dict[str, Any]] = []
        for token in selections:
            lookup_key = str(token)
            entry = catalog_index.get(lookup_key)
            if entry:
                results.append(entry)
        return results

    def _compose_disclosure_content(
        self,
        settings: Optional[ExportSettings],
        *,
        selection: Optional[Iterable[str]] = None,
        disclosure_title: Optional[str] = None,
        disclosure_text: Optional[str] = None,
    ) -> Tuple[Optional[str], Optional[str], List[Dict[str, Any]]]:
        chosen_ids: List[str]
        if selection is not None:
            chosen_ids = []
            seen = set()
            for item in selection:
                token = str(item).strip()
                if token and token not in seen:
                    chosen_ids.append(token)
                    seen.add(token)
        elif settings and settings.disclosures:
            chosen_ids = list(settings.disclosures)
        else:
            chosen_ids = []
        resolved_entries = self._resolve_disclosure_entries(chosen_ids) if chosen_ids else []

        resolved_title = disclosure_title if disclosure_title is not None else (settings.disclosure_title if settings else None)
        resolved_text = disclosure_text if disclosure_text is not None else (settings.disclosure_text if settings else None)

        if not resolved_text and resolved_entries:
            parts = [
                str(entry.get("body") or entry.get("text") or "").strip()
                for entry in resolved_entries
                if entry.get("body") or entry.get("text")
            ]
            resolved_text = "\n\n".join(part for part in parts if part)

        if not resolved_title and resolved_entries:
            titles = [
                str(entry.get("title") or entry.get("name") or "").strip()
                for entry in resolved_entries
                if entry.get("title") or entry.get("name")
            ]
            filtered = [title for title in titles if title]
            if filtered:
                resolved_title = " / ".join(filtered)


        return resolved_title, resolved_text, resolved_entries

    def set_operator_name(self, name: str) -> None:
        if not name:
            return
        self.operator_name = name.strip()
        if self.case_session:
            try:
                self._acquire_case_lock(self.case_session.case_id)
            except PermissionError as exc:
                self.log_event(f"Lock refresh failed: {exc}")

    def _lock_owner_identifier(self) -> str:
        operator = self.operator_name or "Operator"
        host = self.host_identifier or socket.gethostname() or "host"
        return f"{operator}@{host}"

    def _acquire_case_lock(self, case_id: str) -> None:
        info = catalog_get_lock_info(case_id) or {}
        owner = info.get('owner')
        identifier = self._lock_owner_identifier()
        if owner and owner != identifier:
            locked_by = info.get('operator') or owner
            timestamp = info.get('timestamp') or info.get('updated') or 'unknown time'
            raise PermissionError(f"Case {case_id} is currently locked by {locked_by} (since {timestamp}).")
        lock_record = {
            'owner': identifier,
            'operator': self.operator_name,
            'host': self.host_identifier,
            'timestamp': datetime.now().isoformat(),
        }
        catalog_set_lock_info(case_id, lock_record)

    def _release_case_lock(self, case_id: Optional[str]) -> None:
        if not case_id:
            return
        info = catalog_get_lock_info(case_id)
        identifier = self._lock_owner_identifier()
        if not info or info.get('owner') == identifier:
            catalog_clear_lock(case_id)

    def get_case_lock_info(self, case_id: str) -> Optional[Dict[str, Any]]:
        info = catalog_get_lock_info(case_id)
        if not info:
            return None
        result = dict(info)
        result['owned_by_self'] = info.get('owner') == self._lock_owner_identifier()
        return result

    def get_activity_log(self, case_id: Optional[str] = None, *, limit: int = 40) -> List[Dict[str, Any]]:
        limit = max(limit, 1)
        entries: List[Dict[str, Any]] = []
        case_token = str(case_id) if case_id else None
        if self.bus and hasattr(self.bus, 'get_event_log'):
            try:
                raw_events = self.bus.get_event_log(limit=200)  # type: ignore[attr-defined]
            except Exception:
                raw_events = []
            for entry in reversed(raw_events):
                message = entry.get('message') or ''
                if case_token and case_token not in message:
                    continue
                entries.append({
                    'timestamp': entry.get('timestamp'),
                    'source': entry.get('source'),
                    'level': entry.get('level'),
                    'message': message,
                })
                if len(entries) >= limit:
                    break
        if case_id and len(entries) < limit:
            artifacts = catalog_load_artifacts(case_id) or {}
            audit_path = artifacts.get('AUDIT_TRAIL')
            if audit_path:
                audit_file = Path(audit_path)
                if audit_file.exists():
                    try:
                        payload = json.loads(audit_file.read_text(encoding='utf-8'))
                        manifest = payload.get('evidence_manifest') or []
                        for record in reversed(manifest[-10:]):
                            entries.append({
                                'timestamp': record.get('timestamp'),
                                'source': 'manifest',
                                'level': 'info',
                                'message': f"Evidence {record.get('evidence_id')} status={record.get('status')} section={record.get('section')}",
                            })
                            if len(entries) >= limit:
                                break
                    except Exception:
                        pass
        entries.sort(key=lambda item: item.get('timestamp') or '', reverse=True)
        return entries[:limit]

    def _generate_audit_bundle(
        self,
        *,
        session: CaseSession,
        case_folder: Path,
        artifacts: Dict[str, str],
        formats: List[str],
        timestamp: str,
    ) -> Optional[str]:
        manifest_entries = self._fetch_manifest_entries()
        manifest_snapshot: List[Dict[str, Any]] = []
        for entry in manifest_entries:
            manifest_snapshot.append(
                {
                    'evidence_id': entry.get('evidence_id') or entry.get('id'),
                    'file_path': entry.get('file_path') or entry.get('path'),
                    'status': entry.get('status') or entry.get('state'),
                    'section': entry.get('section_hint') or entry.get('assigned_section'),
                    'tags': entry.get('tags') or entry.get('classification', {}).get('tags'),
                    'timestamp': entry.get('timestamp') or entry.get('added_at') or entry.get('received_at'),
                }
            )

        bus_events: List[Dict[str, Any]] = []
        if self.bus and hasattr(self.bus, 'get_event_log'):
            try:
                raw_events = self.bus.get_event_log(limit=120)  # type: ignore[attr-defined]
                for event in raw_events or []:
                    bus_events.append(
                        {
                            'timestamp': event.get('timestamp') or event.get('generated_at') or event.get('time'),
                            'topic': event.get('topic') or event.get('event_type'),
                            'source': event.get('source') or event.get('origin'),
                            'summary': event.get('message') or event.get('summary'),
                        }
                    )
            except Exception:
                bus_events = []

        scanned_snapshot: List[Dict[str, Any]] = []
        for entry in self.scanned_evidence:
            scanned_snapshot.append(
                {
                    'evidence_id': entry.get('evidence_id'),
                    'name': entry.get('name') or entry.get('file_path'),
                    'category': entry.get('category') or entry.get('display_label'),
                    'tags': entry.get('tags'),
                    'status': entry.get('status'),
                    'timestamp': entry.get('timestamp') or entry.get('processed_at'),
                }
            )

        session_snapshot = {
            'case_id': session.case_id,
            'investigator': session.investigator,
            'status': session.status,
            'created_at': session.created_at.isoformat(),
            'last_saved': session.last_saved.isoformat(),
            'export_settings': session.export_settings.to_dict(),
            'section_status': {
                key: {
                    'status': state.status,
                    'last_updated': state.last_updated.isoformat() if state.last_updated else None,
                    'last_reviewed': state.last_reviewed.isoformat() if state.last_reviewed else None,
                }
                for key, state in session.sections.items()
            },
        }

        catalog_meta = catalog_load_metadata(session.case_id) or {}
        catalog_artifacts = catalog_load_artifacts(session.case_id) or {}

        audit_payload = {
            'version': '1.0',
            'label': 'OFFICIAL AUDIT TRAIL',
            'generated_at': datetime.now().isoformat(),
            'case': session_snapshot,
            'catalog_metadata': catalog_meta,
            'catalog_artifacts': catalog_artifacts,
            'export': {
                'export_root': str(case_folder),
                'formats': formats,
                'artifacts': artifacts,
                'timestamp': timestamp,
            },
            'evidence_manifest': manifest_snapshot,
            'scanned_evidence': scanned_snapshot,
            'bus_events': bus_events,
        }

        try:
            audit_filename = f"{self._sanitize_case_id(session.case_id)}_{timestamp}_audit.json"
            audit_path = case_folder / audit_filename
            audit_path.write_text(
                json.dumps(audit_payload, ensure_ascii=False, separators=(',', ':')),
                encoding='utf-8',
            )
            return str(audit_path)
        except Exception as exc:
            self.log_event(f"Failed to write audit bundle: {exc}")
            return None

    def _compose_audit_transcript(self, audit_payload: Dict[str, Any]) -> str:
        lines: List[str] = []
        header_label = audit_payload.get('label') or 'OFFICIAL AUDIT TRAIL'
        lines.append(header_label)
        lines.append('-' * len(header_label))
        lines.append(f"Generated: {audit_payload.get('generated_at')}")
        case_info = audit_payload.get('case') or {}
        lines.append(f"Case ID: {case_info.get('case_id')}")
        lines.append(f"Investigator: {case_info.get('investigator')}")
        lines.append(f"Status: {case_info.get('status')}")
        lines.append('')
        export_info = audit_payload.get('export') or {}
        lines.append("Export Details:")
        lines.append(f"  Export Root: {export_info.get('export_root')}")
        formats = export_info.get('formats') or []
        if formats:
            lines.append(f"  Formats: {', '.join(formats)}")
        artifacts = export_info.get('artifacts') or {}
        for fmt, path_str in artifacts.items():
            lines.append(f"    - {fmt}: {path_str}")
        lines.append('')
        manifest = audit_payload.get('evidence_manifest') or []
        if manifest:
            lines.append("Evidence Manifest Snapshot:")
            for entry in manifest[:25]:
                lines.append(
                    f"  - {entry.get('evidence_id')}: {entry.get('file_path')} (status={entry.get('status')}, section={entry.get('section')})"
                )
            if len(manifest) > 25:
                lines.append(f"  ... {len(manifest) - 25} additional manifest entries omitted")
            lines.append('')
        events = audit_payload.get('bus_events') or []
        if events:
            lines.append("Recent Bus Events:")
            for event in events[:20]:
                lines.append(
                    f"  [{event.get('timestamp')}] {event.get('topic')} from {event.get('source')}: {event.get('summary')}"
                )
            if len(events) > 20:
                lines.append(f"  ... {len(events) - 20} additional events omitted")
            lines.append('')
        scanned = audit_payload.get('scanned_evidence') or []
        if scanned:
            lines.append("Evidence Processing Summary:")
            for item in scanned[:20]:
                lines.append(
                    f"  - {item.get('evidence_id')} ({item.get('name')}) category={item.get('category')} status={item.get('status')}"
                )
            if len(scanned) > 20:
                lines.append(f"  ... {len(scanned) - 20} additional evidence records omitted")
            lines.append('')
        lines.append("End of OFFICIAL AUDIT TRAIL")
        return "\r\n".join(lines).strip()

    def render_audit_transcript(
        self,
        *,
        audit_path: Optional[str] = None,
        audit_payload: Optional[Dict[str, Any]] = None,
    ) -> str:
        payload = audit_payload
        if payload is None and audit_path:
            try:
                payload = json.loads(Path(audit_path).read_text(encoding='utf-8'))
            except Exception as exc:
                raise ValueError(f"Unable to load audit trail: {exc}")
        if payload is None:
            raise ValueError('Audit payload is required')
        return self._compose_audit_transcript(payload)

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
        include_cover: Optional[bool] = None,
        include_toc: Optional[bool] = None,
        include_disclosure: Optional[bool] = None,
        disclosure_text: Optional[str] = None,
        disclosure_title: Optional[str] = None,
        disclosures: Optional[Iterable[str]] = None,
        add_watermark: bool = False,
        watermark_text: Optional[str] = None,
        watermark_type: Optional[str] = None,
        digital_sign: bool = False,
        signature_options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Export a full report, delegating to Mission Debrief for PDF/DOCX when available."""
        target_path = Path(file_path) if file_path else None
        fmt_token = (export_format or (target_path.suffix if target_path else "")).upper().lstrip('.') if (export_format or target_path) else ''
        active_case = case_id or (report_data or {}).get('case_id') or getattr(self.bus, 'current_case_id', None)
        signature_options = signature_options or {}

        session = self.case_session
        if case_id and (not session or session.case_id != case_id):
            session = catalog_load_session(case_id)
            if session and (self.case_session is None or self.case_session.case_id == session.case_id):
                self.case_session = session
        settings = getattr(session, "export_settings", None)

        def _dedup(sequence: Optional[Iterable[Any]]) -> List[str]:
            if not sequence:
                return []
            result: List[str] = []
            seen_local = set()
            for item in sequence:
                token = str(item).strip()
                if not token or token in seen_local:
                    continue
                result.append(token)
                seen_local.add(token)
            return result

        selected_disclosures = _dedup(disclosures if disclosures is not None else (settings.disclosures if settings else []))

        if include_cover is None:
            include_cover = settings.include_cover if settings else True
        if include_toc is None:
            include_toc = settings.include_toc if settings else True
        if include_disclosure is None:
            include_disclosure = settings.include_disclosure if settings else True

        resolved_title, resolved_text, resolved_entries = self._compose_disclosure_content(
            settings,
            selection=selected_disclosures,
            disclosure_title=disclosure_title,
            disclosure_text=disclosure_text,
        )
        disclosure_title = resolved_title
        disclosure_text = resolved_text

        def _apply_preferences(payload: Dict[str, Any]) -> Dict[str, Any]:
            payload = dict(payload)
            sections_map = payload.get('sections')
            if isinstance(sections_map, dict):
                sections_copy = dict(sections_map)
                if not include_disclosure:
                    sections_copy.pop('section_dp', None)
                payload['sections'] = sections_copy
            if not include_cover:
                payload.pop('cover_page', None)
            if not include_toc:
                payload.pop('table_of_contents', None)
            if include_disclosure:
                disclosure_entry = payload.get('disclosure_page')
                if disclosure_text or disclosure_title:
                    if not isinstance(disclosure_entry, dict):
                        disclosure_entry = {}
                    if disclosure_text:
                        disclosure_entry['content'] = disclosure_text
                    if disclosure_title:
                        disclosure_entry.setdefault('metadata', {})['artifact'] = disclosure_title
                    payload['disclosure_page'] = disclosure_entry
            else:
                payload.pop('disclosure_page', None)
            payload['export_preferences'] = {
                'include_cover': include_cover,
                'include_toc': include_toc,
                'include_disclosure': include_disclosure,
                'disclosure_title': disclosure_title,
                'disclosure_text_provided': bool(disclosure_text),
                'disclosures': list(selected_disclosures),
            }
            payload['selected_disclosures'] = list(selected_disclosures)
            if resolved_entries:
                payload['resolved_disclosures'] = resolved_entries
            if disclosure_text is not None:
                payload['export_preferences']['disclosure_text'] = disclosure_text
            return payload

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
                return _apply_preferences(merged)
            return _apply_preferences(base_payload)

        if fmt_token in {'PDF', 'DOCX'} and self.debrief:
            payload = _ensure_payload()
            payload['case_id'] = active_case or payload.get('case_id')
            options = {
                'case_id': payload.get('case_id'),
                'export_report': True,
                'export_format': fmt_token,
                'report_type': payload.get('report_type'),
                'include_cover': include_cover,
                'include_table_of_contents': include_toc,
                'include_disclosure': include_disclosure,
                'disclosure_text': disclosure_text,
                'disclosure_title': disclosure_title,
                'add_watermark': add_watermark,
                'digital_sign': digital_sign,
            }
            if add_watermark:
                options['watermark_text'] = watermark_text or 'DRAFT'
                options['watermark_type'] = watermark_type or 'draft'
            if digital_sign:
                options.update(signature_options)
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

# Module-level helpers for legacy imports
def get_adapter() -> CentralPluginAdapter:
    return central_plugin


def pause_case() -> Optional[CaseSession]:
    return central_plugin.pause_case()


def resume_case(case_id: str) -> Optional[CaseSession]:
    return central_plugin.resume_case(case_id)


def save_case(*, status: Optional[str] = None) -> None:
    central_plugin.save_case(status=status)



__all__ = [
    "CentralPlugin",
    "CentralPluginAdapter",
    "central_plugin",
    "get_adapter",
    "pause_case",
    "resume_case",
    "save_case",
]







