#!/usr/bin/env python3
"""Intake processing helpers for Enhanced Central Command."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class IntakeProcessingResult:
    case_context: Dict[str, Any]
    missing_required: List[str]


class IntakeManager:
    """Parses intake artifacts and derives case context."""

    def __init__(self, profile) -> None:
        self.profile = profile
        self.logger = logging.getLogger(__name__)
        payload = getattr(profile, "payload", {})
        intake_cfg = payload.get("intake", {})
        self.required_fields: List[str] = list(intake_cfg.get("required_fields", ["client_name", "case_number"]))
        defaults = payload.get("case_defaults", {})
        if profile.display_name and not defaults.get("client_name"):
            defaults = dict(defaults)
            defaults["client_name"] = profile.display_name
        self.defaults = {k: v for k, v in defaults.items() if v}

    def process_artifacts(self, artifact_paths: Iterable[Path | str]) -> IntakeProcessingResult:
        paths = [Path(p) for p in artifact_paths]
        context: Dict[str, Any] = dict(self.defaults)

        for path in paths:
            if not path.exists():
                continue
            suffix = path.suffix.lower()
            try:
                if suffix == ".json":
                    self._ingest_json(path, context)
                elif suffix in {".txt", ".md"}:
                    self._ingest_text(path, context)
            except Exception as exc:  # pragma: no cover
                self.logger.debug("Unable to parse intake artifact %s: %s", path, exc)

        missing = [field for field in self.required_fields if not context.get(field)]
        return IntakeProcessingResult(case_context=context, missing_required=missing)

    # ------------------------------------------------------------------
    def _ingest_json(self, path: Path, context: Dict[str, Any]) -> None:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return
        for key, value in data.items():
            norm_key = self._normalise_key(key)
            if isinstance(value, str):
                value = value.strip()
            if value and norm_key not in context:
                context[norm_key] = value

    def _ingest_text(self, path: Path, context: Dict[str, Any]) -> None:
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if ':' not in line:
                continue
            key, value = line.split(':', 1)
            value = value.strip()
            if not value:
                continue
            norm_key = self._normalise_key(key)
            if norm_key not in context:
                context[norm_key] = value

    @staticmethod
    def _normalise_key(raw_key: str) -> str:
        key = raw_key.strip().lower().replace(' ', '_')
        aliases = {
            'client': 'client_name',
            'client_full_name': 'client_name',
            'case': 'case_number',
            'case_id': 'case_number',
            'location_of_events': 'location',
            'subject_name': 'subject',
        }
        return aliases.get(key, key)
