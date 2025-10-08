"""Case session models used by the Central Command GUI."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Literal

SectionStatus = Literal["pending", "assembling", "ready", "approved"]
EvidenceStatus = Literal["pending", "classified", "review", "approved", "exported"]
CaseStatus = Literal["new", "in_progress", "paused", "completed"]

SECTION_TITLES: Dict[str, str] = {
    "section_cp": "Cover Page",
    "section_toc": "Table of Contents",
    "section_1": "Case Objectives & Intake",
    "section_2": "Requirements & Pre-Surveillance Planning",
    "section_3": "Daily Surveillance Logs",
    "section_4": "Surveillance Session Review",
    "section_5": "Supporting Documents Review",
    "section_6": "Billing Summary",
    "section_7": "Conclusion & Case Decision",
    "section_8": "Photo & Video Evidence Index",
    "section_9": "Certifications & Disclaimers",
    "section_dp": "Disclosure & Authenticity Page",
    "section_fr": "Final Report Assembly",
}



@dataclass
class EvidenceCardState:
    """Represents a single evidence item tracked inside the UI."""

    evidence_id: str
    file_path: str
    section_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    status: EvidenceStatus = "pending"
    added_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "file_path": self.file_path,
            "section_id": self.section_id,
            "tags": list(self.tags),
            "notes": self.notes,
            "status": self.status,
            "added_at": self.added_at.isoformat(),
            "metadata": self.metadata,
        }

    @staticmethod
    def from_dict(payload: Dict[str, Any]) -> "EvidenceCardState":
        instance = EvidenceCardState(
            evidence_id=payload["evidence_id"],
            file_path=payload["file_path"],
            section_id=payload.get("section_id"),
            tags=list(payload.get("tags", [])),
            notes=payload.get("notes"),
            status=payload.get("status", "pending"),
            metadata=dict(payload.get("metadata", {})),
        )
        added_at = payload.get("added_at")
        if added_at:
            try:
                instance.added_at = datetime.fromisoformat(added_at)
            except ValueError:
                pass
        return instance


@dataclass
class SectionState:
    """Tracks narrative status for a mission section."""

    section_id: str
    title: Optional[str] = None
    status: SectionStatus = "pending"
    narrative: Optional[str] = None
    last_updated: Optional[datetime] = None
    last_reviewed: Optional[datetime] = None
    needs_review: bool = False
    assembler_metadata: Dict[str, Any] = field(default_factory=dict)

    def mark_status(self, status: SectionStatus, narrative: Optional[str] = None) -> None:
        self.status = status
        if narrative is not None:
            self.narrative = narrative
        self.last_updated = datetime.utcnow()
        if status == "approved":
            self.last_reviewed = self.last_updated
        self.needs_review = status != "approved"

    def approve(self) -> None:
        self.status = "approved"
        self.needs_review = False
        self.last_updated = datetime.utcnow()
        self.last_reviewed = self.last_updated

    def to_dict(self) -> Dict[str, Any]:
        return {
            "section_id": self.section_id,
            "title": self.title,
            "status": self.status,
            "narrative": self.narrative,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "last_reviewed": self.last_reviewed.isoformat() if self.last_reviewed else None,
            "needs_review": self.needs_review,
            "assembler_metadata": self.assembler_metadata,
        }

    @staticmethod
    def from_dict(payload: Dict[str, Any]) -> "SectionState":
        instance = SectionState(
            section_id=payload["section_id"],
            title=payload.get("title"),
            status=payload.get("status", "pending"),
            narrative=payload.get("narrative"),
            needs_review=payload.get("needs_review", False),
            assembler_metadata=dict(payload.get("assembler_metadata", {})),
        )
        last_updated = payload.get("last_updated")
        if last_updated:
            try:
                instance.last_updated = datetime.fromisoformat(last_updated)
            except ValueError:
                pass
        last_reviewed = payload.get("last_reviewed")
        if last_reviewed:
            try:
                instance.last_reviewed = datetime.fromisoformat(last_reviewed)
            except ValueError:
                pass
        return instance


@dataclass
class ExportSettings:
    """User/export configuration for the active case."""

    export_root: Optional[str] = None
    formats: List[str] = field(default_factory=lambda: ["PDF"])
    disclosures: List[str] = field(default_factory=list)
    include_cover: bool = True
    include_toc: bool = True
    include_disclosure: bool = True
    disclosure_title: Optional[str] = None
    disclosure_text: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "export_root": self.export_root,
            "formats": list(self.formats),
            "disclosures": list(self.disclosures),
            "include_cover": self.include_cover,
            "include_toc": self.include_toc,
            "include_disclosure": self.include_disclosure,
            "disclosure_title": self.disclosure_title,
            "disclosure_text": self.disclosure_text,
        }

    @staticmethod
    def from_dict(payload: Dict[str, Any]) -> "ExportSettings":
        return ExportSettings(
            export_root=payload.get("export_root"),
            formats=list(payload.get("formats", ["PDF"])),
            disclosures=list(payload.get("disclosures", [])),
            include_cover=bool(payload.get("include_cover", True)),
            include_toc=bool(payload.get("include_toc", True)),
            include_disclosure=bool(payload.get("include_disclosure", True)),
            disclosure_title=payload.get("disclosure_title"),
            disclosure_text=payload.get("disclosure_text"),
        )


@dataclass
class CaseSession:
    """Top-level state container for a case inside the GUI."""

    case_id: str
    investigator: str
    subcontractor: bool = False
    contract_signed: Optional[date] = None
    status: CaseStatus = "new"
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_saved: datetime = field(default_factory=datetime.utcnow)
    evidence: Dict[str, EvidenceCardState] = field(default_factory=dict)
    sections: Dict[str, SectionState] = field(default_factory=dict)
    export_settings: ExportSettings = field(default_factory=ExportSettings)
    extra: Dict[str, Any] = field(default_factory=dict)

    def ensure_section(self, section_id: str) -> SectionState:
        state = self.sections.get(section_id)
        if state is None:
            state = SectionState(section_id=section_id)
            self.sections[section_id] = state
        if not state.title:
            state.title = SECTION_TITLES.get(section_id)
        return state

    def upsert_evidence(self, card: EvidenceCardState) -> None:
        self.evidence[card.evidence_id] = card

    def remove_evidence(self, evidence_id: str) -> None:
        self.evidence.pop(evidence_id, None)

    def update_export_settings(self, **updates: Any) -> ExportSettings:
        """Merge export configuration overrides and refresh timestamps."""
        settings = self.export_settings
        changed = False
        for key, value in updates.items():
            if value is None or not hasattr(settings, key):
                continue
            current_value = getattr(settings, key)
            if isinstance(current_value, list):
                if isinstance(value, str):
                    candidate = [value]
                else:
                    try:
                        candidate = list(value)
                    except TypeError:
                        candidate = [value]
                cleaned: List[Any] = []
                seen = set()
                for item in candidate:
                    if item in seen:
                        continue
                    cleaned.append(item)
                    seen.add(item)
                if current_value != cleaned:
                    setattr(settings, key, cleaned)
                    changed = True
            else:
                if current_value != value:
                    setattr(settings, key, value)
                    changed = True
        if changed:
            self.mark_saved(status=self.status)
        return settings

    def mark_saved(self, status: Optional[CaseStatus] = None) -> None:
        if status:
            self.status = status
        self.last_saved = datetime.utcnow()

    def approval_counts(self) -> tuple[int, int]:
        total = len(self.sections)
        approved = sum(1 for state in self.sections.values() if state.status == "approved")
        return approved, total

    def to_dict(self) -> Dict[str, Any]:
        contract_value: Optional[str] = None
        if self.contract_signed:
            contract_value = self.contract_signed.isoformat()
        return {
            "case_id": self.case_id,
            "investigator": self.investigator,
            "subcontractor": self.subcontractor,
            "contract_signed": contract_value,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "last_saved": self.last_saved.isoformat(),
            "evidence": {key: card.to_dict() for key, card in self.evidence.items()},
            "sections": {key: state.to_dict() for key, state in self.sections.items()},
            "export_settings": self.export_settings.to_dict(),
            "extra": self.extra,
        }

    @staticmethod
    def from_dict(payload: Dict[str, Any]) -> "CaseSession":
        contract_value = payload.get("contract_signed")
        contract_signed: Optional[date] = None
        if contract_value:
            try:
                contract_signed = date.fromisoformat(contract_value)
            except ValueError:
                contract_signed = None
        session = CaseSession(
            case_id=payload["case_id"],
            investigator=payload.get("investigator", ""),
            subcontractor=payload.get("subcontractor", False),
            contract_signed=contract_signed,
            status=payload.get("status", "new"),
            extra=dict(payload.get("extra", {})),
        )
        created_at = payload.get("created_at")
        last_saved = payload.get("last_saved")
        if created_at:
            try:
                session.created_at = datetime.fromisoformat(created_at)
            except ValueError:
                pass
        if last_saved:
            try:
                session.last_saved = datetime.fromisoformat(last_saved)
            except ValueError:
                pass
        evidence_payload = payload.get("evidence", {})
        for key, value in evidence_payload.items():
            session.evidence[key] = EvidenceCardState.from_dict(value)
        sections_payload = payload.get("sections", {})
        for key, value in sections_payload.items():
            state = SectionState.from_dict(value)
            if not state.title:
                state.title = SECTION_TITLES.get(key)
            session.sections[key] = state
        session.export_settings = ExportSettings.from_dict(payload.get("export_settings", {}))
        return session


__all__ = [
    "CaseSession",
    "EvidenceCardState",
    "SectionState",
    "ExportSettings",
    "CaseStatus",
    "SectionStatus",
    "EvidenceStatus",
    "SECTION_TITLES",
]







