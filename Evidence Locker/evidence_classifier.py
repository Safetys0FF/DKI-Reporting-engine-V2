import json
#!/usr/bin/env python3
"""
EvidenceClassifier - Classification system for assigning evidence to sections.
Keeps extension rules, keyword heuristics, and ECC-aware signalling aligned with
shared SECTION_REGISTRY metadata.
"""

from __future__ import annotations

import os
import mimetypes
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set

from section_registry import SECTION_REGISTRY

logger = logging.getLogger(__name__)

CONFIG_PATH = r"F:\The Central Command\The Warden\section_tag_map.json"

try:
    with open(CONFIG_PATH, 'r', encoding='utf-8') as config_file:
        SECTION_TAGS = json.load(config_file)
except (OSError, json.JSONDecodeError):
    SECTION_TAGS = {}


# Default extension to section mapping. Users can override via config.
DEFAULT_FILE_TYPE_RULES: Dict[str, str] = {
    ".pdf": "section_5",
    ".doc": "section_5",
    ".docx": "section_5",
    ".rtf": "section_5",
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
    ".mp3": "section_3",
    ".wav": "section_3",
}

# Keyword hints used for filename / content heuristics.
CONTENT_KEYWORDS: Dict[str, List[str]] = {
    "section_1": ["intake", "subject", "profile", "client"],
    "section_2": ["plan", "route", "pre-surveillance", "brief"],
    "section_3": ["log", "surveillance", "daily", "observed", "followed"],
    "section_4": ["summary", "recap", "timeline", "continuity"],
    "section_5": ["contract", "agreement", "record", "report", "background"],
    "section_6": ["invoice", "billing", "payment", "hours"],
    "section_7": ["conclusion", "decision", "case closed"],
    "section_8": ["photo", "image", "video", "media"],
    "section_9": ["disclosure", "disclaimer", "license", "compliance"],
    "section_dp": ["certify", "authenticity", "signature"],
    "section_fr": ["final report", "assembly"],
}

NORMALIZE = {
    "supporting_documents": "supporting-documents",
    "evidence_index": "media-photo",
    "intakeform": "intake-form",
    "dailylog": "daily-log",
}


def normalize_tags(tags: List[str]) -> List[str]:
    return [NORMALIZE.get(tag, tag) for tag in tags]

LEGAL_MARKERS = {"agreement", "contract", "retainer", "terms", "payment", "consideration"}


class EvidenceClassifier:
    """Evidence classification system for assigning files to appropriate sections."""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        ecc: Any = None,
        text_extractor: Optional[Any] = None,
    ) -> None:
        self.config = config or {}
        self.ecc = ecc
        self.text_extractor = text_extractor  # callable: (file_path) -> str | None
        self.logger = logging.getLogger(__name__)

        overrides = self.config.get("file_type_rules", {})
        self.file_type_rules = {ext.lower(): sec for ext, sec in DEFAULT_FILE_TYPE_RULES.items()}
        self.file_type_rules.update({ext.lower(): sec for ext, sec in overrides.items()})

        self.classification_history: List[Dict[str, Any]] = []
        self.logger.info("EvidenceClassifier initialized")

    # ------------------------------------------------------------------
    # ECC signalling helpers
    # ------------------------------------------------------------------
    def _call_out_to_ecc(self, operation: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Announce upcoming work to the ECC if available."""
        if not self.ecc or not hasattr(self.ecc, "emit"):
            return {"permission_granted": True, "request_id": None}

        request_id = f"classify_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        payload = {
            "operation": operation,
            "request_id": request_id,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "module": "evidence_classifier",
        }
        try:
            self.ecc.emit("evidence_locker.call_out", payload)
            self.logger.info("ECC call-out for %s (request %s)", operation, request_id)
            return {"permission_granted": True, "request_id": request_id}
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error("ECC call-out failed: %s", exc)
            return {"permission_granted": False, "error": str(exc)}

    def _wait_for_ecc_confirm(self, operation: str, request_id: Optional[str]) -> Dict[str, Any]:
        """Stub confirmation hook; real implementation would await ECC response."""
        if not self.ecc or not request_id:
            return {"confirmed": True}
        self.logger.debug("ECC confirmation assumed for %s (%s)", operation, request_id)
        return {"confirmed": True, "request_id": request_id}

    def _send_message(self, operation: str, data: Dict[str, Any]) -> bool:
        if not self.ecc or not hasattr(self.ecc, "emit"):
            return True
        try:
            self.ecc.emit(
                "evidence_locker.send",
                {
                    "operation": operation,
                    "data": data,
                    "timestamp": datetime.now().isoformat(),
                    "module": "evidence_classifier",
                },
            )
            self.logger.debug("Sent ECC message for %s", operation)
            return True
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error("ECC send failed: %s", exc)
            return False

    def _send_accept_signal(self, operation: str, data: Dict[str, Any]) -> bool:
        if not self.ecc or not hasattr(self.ecc, "emit"):
            return True
        try:
            self.ecc.emit(
                "evidence_locker.accept",
                {
                    "operation": operation,
                    "data": data,
                    "timestamp": datetime.now().isoformat(),
                    "module": "evidence_classifier",
                },
            )
            self.logger.debug("Sent ECC accept for %s", operation)
            return True
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error("ECC accept failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Classification pipeline
    # ------------------------------------------------------------------
    def classify(self, file_path: str, section_id: Optional[str] = None) -> Dict[str, Any]:
        """Classify a file and return section assignment with confidence."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(file_path)

        call_out = self._call_out_to_ecc(
            "classify",
            {"file_path": file_path, "section_id": section_id},
        )
        confirm = self._wait_for_ecc_confirm("classify", call_out.get("request_id"))
        if not confirm.get("confirmed", False):
            raise RuntimeError("ECC confirmation failed for classification")

        classification = {
            "assigned_section": None,
            "confidence": 0.0,
            "classification_method": "unknown",
            "keywords_found": [],
            "file_path": file_path,
        }

        filename = os.path.basename(file_path)
        file_ext = Path(filename).suffix.lower()
        mime_type, _ = mimetypes.guess_type(file_path)

        if self._classify_by_extension(file_ext, classification):
            pass
        elif self._classify_by_mime_type(mime_type, classification):
            pass
        elif self._classify_by_filename(filename, classification):
            pass
        elif self._classify_by_content(file_path, classification):
            pass

        if not classification["assigned_section"]:
            classification["assigned_section"] = section_id or "section_cp"
            classification["confidence"] = max(classification["confidence"], 0.3)
            classification["classification_method"] = "fallback"

        classification["assigned_section"] = self._normalize_section(
            classification["assigned_section"]
        )

        classification["tags"] = self._derive_tags(file_ext, filename, classification["assigned_section"])

        self.classification_history.append(classification.copy())
        self._send_message("classified", classification)
        self._send_accept_signal("classified", classification)
        return classification

    def _classify_by_extension(self, file_ext: str, classification: Dict[str, Any]) -> bool:
        if not file_ext:
            return False
        target = self.file_type_rules.get(file_ext)
        if not target:
            return False
        classification["assigned_section"] = target
        classification["confidence"] = 0.9
        classification["classification_method"] = "file_extension"
        return True

    def _classify_by_mime_type(self, mime_type: Optional[str], classification: Dict[str, Any]) -> bool:
        if not mime_type:
            return False
        if mime_type.startswith("image/"):
            classification["assigned_section"] = "section_8"
            classification["confidence"] = 0.85
            classification["classification_method"] = "mime_type"
            return True
        if mime_type.startswith("video/") or mime_type in {"application/octet-stream"}:
            classification["assigned_section"] = "section_3"
            classification["confidence"] = 0.75
            classification["classification_method"] = "mime_type"
            return True
        if mime_type.startswith("audio/"):
            classification["assigned_section"] = "section_3"
            classification["confidence"] = 0.7
            classification["classification_method"] = "mime_type"
            return True
        return False

    def _classify_by_filename(self, filename: str, classification: Dict[str, Any]) -> bool:
        lowered = filename.lower()
        hits = self._keyword_hits(lowered)
        if not hits:
            return False
        best_section, keywords = hits
        classification["assigned_section"] = best_section
        classification["confidence"] = max(classification["confidence"], 0.7)
        classification["classification_method"] = "filename_keywords"
        classification["keywords_found"] = keywords
        return True

    def _classify_by_content(self, file_path: str, classification: Dict[str, Any]) -> bool:
        text_blob = self._extract_text(file_path)
        if not text_blob:
            return False

        hits = self._keyword_hits(text_blob)
        if hits:
            best_section, keywords = hits
            classification["assigned_section"] = best_section
            classification["confidence"] = max(classification["confidence"], 0.8)
            classification["classification_method"] = "content_keywords"
            classification["keywords_found"] = keywords

        if LEGAL_MARKERS.intersection(text_blob.split()) and best_section != "section_5":
            classification["assigned_section"] = "section_5"
            classification["confidence"] = max(classification["confidence"], 0.9)
            classification["classification_method"] = "legal_heuristic"

        return classification["classification_method"] == "content_keywords" or \
            classification["classification_method"] == "legal_heuristic"

    def _derive_tags(self, file_ext: Optional[str], filename: str, section_id: str) -> List[str]:
        tags: Set[str] = set()
        profile = SECTION_REGISTRY.get(section_id, {})
        tags.update(SECTION_TAGS.get(section_id, []))
        tags.update(profile.get("tags", []))

        ext = (file_ext or "").lower()
        lowered = filename.lower()

        if ext in {".pdf", ".docx"}:
            tags.add("supporting-documents")
            if "intake" in lowered:
                tags.add("intake-form")
            if "contract" in lowered:
                tags.add("contract")
            if "agreement" in lowered:
                tags.add("subcontractor-agreement")
            if any(word in lowered for word in ["billing", "hours", "mileage", "expense", "receipt", "invoice"]):
                tags.add("billing-record")

        return normalize_tags(sorted(tags))

    def _keyword_hits(self, text: str) -> Optional[Tuple[str, List[str]]]:
        scores: Dict[str, List[str]] = {}
        for section, keywords in CONTENT_KEYWORDS.items():
            hits = [kw for kw in keywords if kw in text]
            if hits:
                scores[section] = hits
        if not scores:
            return None
        best_section = max(scores.items(), key=lambda item: len(item[1]))[0]
        return best_section, scores[best_section]

    def _extract_text(self, file_path: str) -> Optional[str]:
        if self.text_extractor:
            try:
                return (self.text_extractor(file_path) or "").lower()
            except Exception as exc:  # pragma: no cover - defensive
                self.logger.debug("Custom text extractor failed: %s", exc)
        if not self._is_text_file(file_path):
            return None
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as handle:
                return handle.read().lower()
        except Exception:
            return None

    def _is_text_file(self, file_path: str) -> bool:
        ext = Path(file_path).suffix.lower()
        if ext in {".txt", ".md", ".log", ".csv", ".json", ".xml", ".html", ".htm"}:
            return True
        mime_type, _ = mimetypes.guess_type(file_path)
        return bool(mime_type and mime_type.startswith("text/"))

    def _normalize_section(self, section_id: str) -> str:
        if section_id in SECTION_REGISTRY:
            return section_id
        self.logger.debug("Unknown section %s, defaulting to section_cp", section_id)
        return "section_cp"

    # ------------------------------------------------------------------
    # Public helper operations
    # ------------------------------------------------------------------
    def validate_section_assignment(self, file_path: str, section_id: str) -> bool:
        classification = self.classify(file_path, section_id)
        assigned = classification["assigned_section"]
        return assigned == section_id or assigned == "section_cp"

    def batch_classify(
        self,
        file_paths: List[str],
        section_id: Optional[str] = None,
    ) -> Dict[str, Dict[str, Any]]:
        results: Dict[str, Dict[str, Any]] = {}
        for file_path in file_paths:
            try:
                results[file_path] = self.classify(file_path, section_id)
            except Exception as exc:  # pragma: no cover - defensive
                self.logger.error("Batch classify failed for %s: %s", file_path, exc)
                results[file_path] = {
                    "assigned_section": "section_cp",
                    "confidence": 0.0,
                    "classification_method": "error",
                    "error": str(exc),
                }
        return results

    def get_classification_stats(self) -> Dict[str, Any]:
        total = len(self.classification_history)
        if not total:
            return {"total_classifications": 0}
        section_counts: Dict[str, int] = {}
        method_counts: Dict[str, int] = {}
        for record in self.classification_history:
            section = record.get("assigned_section", "section_cp")
            method = record.get("classification_method", "unknown")
            section_counts[section] = section_counts.get(section, 0) + 1
            method_counts[method] = method_counts.get(method, 0) + 1
        avg_conf = sum(r.get("confidence", 0.0) for r in self.classification_history) / total
        return {
            "total_classifications": total,
            "section_distribution": section_counts,
            "method_distribution": method_counts,
            "average_confidence": round(avg_conf, 3),
        }

    def update_classification_rules(self, file_extension: str, section: str) -> bool:
        section = self._normalize_section(section)
        self.file_type_rules[file_extension.lower()] = section
        self.logger.info("Updated classification rule: %s -> %s", file_extension, section)
        return True

    def export_classification_rules(self) -> Dict[str, Any]:
        return {
            "file_type_rules": self.file_type_rules.copy(),
            "keyword_map": CONTENT_KEYWORDS,
            "export_timestamp": datetime.now().isoformat(),
        }


def validate_registry() -> None:
    """Warn if CONTENT_KEYWORDS references sections missing from the registry."""
    missing = [sec for sec in CONTENT_KEYWORDS if sec not in SECTION_REGISTRY]
    if missing:
        logger.warning("Keywords mapped to unknown sections: %s", ", ".join(missing))


validate_registry()