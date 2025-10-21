#!/usr/bin/env python3
"""Initialiser helpers for Evidence Locker subsystems."""
from __future__ import annotations

import logging
import mimetypes
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Core Locker
# --------------------------------------------------------------------------- #

@dataclass
class EvidenceRecord:
    evidence_id: str
    file_path: str
    filename: str
    file_size: int
    mime_type: str
    section_id: str
    tags: List[str] = field(default_factory=list)
    ingested_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


class SimpleEvidenceLocker:
    """Compact evidence locker focused on ingestion and persistence."""

    def __init__(self, *, bus: Optional[Any] = None) -> None:
        self.bus = bus
        self.case_id: Optional[str] = None
        self.records: Dict[str, EvidenceRecord] = {}
        self.logger = logging.getLogger(__name__)
        self.logger.info("SimpleEvidenceLocker initialised (bus=%s)", bool(bus))

    def start_new_case(self, case_id: Optional[str]) -> None:
        self.case_id = case_id
        self.records.clear()
        self.logger.info("Evidence locker case reset -> %s", case_id)

    def store_record(self, record: EvidenceRecord) -> None:
        self.records[record.evidence_id] = record

    def clear(self) -> None:
        self.records.clear()

    def manifest(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "entries": {eid: asdict(record) for eid, record in self.records.items()},
            "updated_at": datetime.utcnow().isoformat(),
        }


def init_evidence_locker(*, bus: Optional[Any] = None, **_kwargs: Any) -> SimpleEvidenceLocker:
    """Instantiate the streamlined Evidence Locker."""
    return SimpleEvidenceLocker(bus=bus)


# --------------------------------------------------------------------------- #
# Tooling helpers
# --------------------------------------------------------------------------- #

class SimpleEvidenceClassifier:
    """Extension and keyword based classifier."""

    EXTENSION_MAP: Dict[str, str] = {
        ".pdf": "section_5",
        ".doc": "section_5",
        ".docx": "section_5",
        ".txt": "section_3",
        ".csv": "section_6",
        ".xlsx": "section_6",
        ".xls": "section_6",
        ".jpg": "section_8",
        ".jpeg": "section_8",
        ".png": "section_8",
        ".gif": "section_8",
        ".mp4": "section_3",
        ".mov": "section_3",
        ".avi": "section_3",
    }

    KEYWORDS: Dict[str, Iterable[str]] = {
        "section_1": ("intake", "subject", "profile"),
        "section_2": ("plan", "pre-surveillance", "brief"),
        "section_3": ("log", "surveillance", "daily"),
        "section_4": ("summary", "timeline"),
        "section_5": ("report", "contract", "record"),
        "section_6": ("invoice", "billing"),
        "section_7": ("decision", "conclusion"),
        "section_8": ("photo", "image", "video"),
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.logger = logging.getLogger(__name__)
        self.config = config or {}

    def classify(self, file_path: str, section_id: Optional[str] = None) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(file_path)

        resolved = Path(file_path)
        file_ext = resolved.suffix.lower()
        filename = resolved.name.lower()
        assigned = section_id or self.EXTENSION_MAP.get(file_ext)

        if not assigned:
            for candidate_section, keywords in self.KEYWORDS.items():
                if any(keyword in filename for keyword in keywords):
                    assigned = candidate_section
                    break

        if not assigned:
            assigned = "section_cp"

        confidence = 0.9 if assigned in self.EXTENSION_MAP.values() else 0.6 if assigned != "section_cp" else 0.3
        classification = {
            "assigned_section": assigned,
            "confidence": confidence,
            "classification_method": "extension" if file_ext in self.EXTENSION_MAP else "keyword",
            "keywords_found": [kw for kws in self.KEYWORDS.values() for kw in kws if kw in filename],
            "file_path": str(resolved),
            "tags": list({file_ext.strip(".") or "file", assigned}),
        }
        return classification


class SimpleEvidenceClassBuilder:
    """Builds EvidenceRecord objects."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def build(self, file_path: str, section_id: str, tags: Optional[Iterable[str]] = None) -> EvidenceRecord:
        resolved = Path(file_path)
        file_size = resolved.stat().st_size
        mime_type, _ = mimetypes.guess_type(str(resolved))
        evidence_id = f"{section_id}-{uuid.uuid4().hex[:12]}"
        record = EvidenceRecord(
            evidence_id=evidence_id,
            file_path=str(resolved),
            filename=resolved.name,
            file_size=file_size,
            mime_type=mime_type or "application/octet-stream",
            section_id=section_id,
            tags=list(tags or []),
        )
        return record


class SimpleEvidenceIndex:
    """Minimal evidence index keeping track of records per section."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.master: Dict[str, Dict[str, Any]] = {}
        self.by_section: Dict[str, Set[str]] = {}

    def add_file(self, record: EvidenceRecord) -> str:
        self.master[record.evidence_id] = {
            "file_path": record.file_path,
            "section_id": record.section_id,
            "tags": record.tags,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.by_section.setdefault(record.section_id, set()).add(record.evidence_id)
        return record.evidence_id


class SimpleStaticDataFlow:
    """Tracks data flow announcements for diagnostics."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.history: List[Dict[str, Any]] = []

    def announce(self, operation: str, payload: Dict[str, Any]) -> None:
        record = {
            "operation": operation,
            "payload": payload,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.history.append(record)
        self.logger.debug("DataFlow %s -> %s", operation, payload)


class SimpleManifestBuilder:
    """Derives a case manifest from current evidence records."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def build(self, case_id: Optional[str], records: Dict[str, EvidenceRecord]) -> Dict[str, Any]:
        manifest = {
            "case_id": case_id,
            "generated_at": datetime.utcnow().isoformat(),
            "entries": {eid: asdict(record) for eid, record in records.items()},
        }
        return manifest


# --------------------------------------------------------------------------- #
# Factory helpers exposed to the wrapper
# --------------------------------------------------------------------------- #

def init_evidence_classifier(*, config: Optional[Dict[str, Any]] = None) -> SimpleEvidenceClassifier:
    return SimpleEvidenceClassifier(config=config)


def init_evidence_index() -> SimpleEvidenceIndex:
    return SimpleEvidenceIndex()


def init_evidence_class_builder() -> SimpleEvidenceClassBuilder:
    return SimpleEvidenceClassBuilder()


def init_static_data_flow() -> SimpleStaticDataFlow:
    return SimpleStaticDataFlow()


def init_case_manifest_builder() -> SimpleManifestBuilder:
    return SimpleManifestBuilder()


__all__ = [
    "init_evidence_locker",
    "init_evidence_classifier",
    "init_evidence_index",
    "init_evidence_class_builder",
    "init_static_data_flow",
    "init_case_manifest_builder",
    "EvidenceRecord",
]
