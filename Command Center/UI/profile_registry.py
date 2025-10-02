#!/usr/bin/env python3
"""Profile registry for the Enhanced Central Command GUI.

Provides lightweight profile loading so the GUI can resolve the active
workflow, contract catalogue, and intake configuration without relying on
legacy Report Engine modules.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class Profile:
    """Represents the active analyst profile."""

    display_name: str
    payload: Dict[str, Any]


class ProfileRegistry:
    """Loads and exposes analyst profile configuration."""

    def __init__(self, config_root: Optional[Path | str] = None) -> None:
        base = Path(config_root) if config_root else Path(__file__).resolve().parent
        self._config_root = str(base)
        self._profile_path = base / "user_profile.json"
        self._cached: Optional[Profile] = None

        base.mkdir(parents=True, exist_ok=True)

    def load_profile(self) -> Profile:
        if self._cached is not None:
            return self._cached

        user_data = self._load_user_data()
        payload = self._build_payload(user_data)
        display_name = user_data.get("user_name") or user_data.get("business_name") or "Analyst"
        profile = Profile(display_name=display_name, payload=payload)
        self._cached = profile
        return profile

    def get_raw_profile(self) -> Dict[str, Any]:
        """Return the raw profile JSON as a dictionary."""
        return self._load_user_data()

    def save_profile(self, user_data: Dict[str, Any]) -> Profile:
        """Persist updated profile data and rebuild cached payload."""
        try:
            self._profile_path.write_text(json.dumps(user_data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as exc:  # pragma: no cover - IO errors
            logger.error("Failed to write profile json: %s", exc)
            raise
        self._cached = None
        profile = self.load_profile()
        logger.info("Profile updated at %s", self._profile_path)
        return profile

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------
    def _load_user_data(self) -> Dict[str, Any]:
        if not self._profile_path.exists():
            logger.warning("Profile file missing at %s", self._profile_path)
            return {}
        try:
            return json.loads(self._profile_path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to load profile json: %s", exc)
            return {}

    def _build_payload(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        root = Path(self._config_root)
        templates_dir = root / "templates"
        contracts_dir = root / "contracts"
        intake_dir = root / "intake"

        templates_dir.mkdir(parents=True, exist_ok=True)
        contracts_dir.mkdir(parents=True, exist_ok=True)
        intake_dir.mkdir(parents=True, exist_ok=True)

        default_contract_id = "investigation_surveillance"
        catalog = [
            {
                "contract_id": default_contract_id,
                "title": "Surveillance Investigation Agreement",
                "workflow": "surveillance",
                "template": str((templates_dir / "surveillance_agreement.docx").resolve()),
                "keywords": ["surveillance", "investigation", "agreement"],
            },
            {
                "contract_id": "due_diligence",
                "title": "Due Diligence Agreement",
                "workflow": "due_diligence",
                "template": str((templates_dir / "due_diligence_agreement.docx").resolve()),
                "keywords": ["diligence", "due", "audit"],
            },
        ]

        workflows = [
            {
                "id": "surveillance",
                "label": "Surveillance Workflow",
                "linked_contract": default_contract_id,
                "sections": [
                    "section_cp",
                    "section_toc",
                    "section_1",
                    "section_3",
                    "section_5",
                    "section_8",
                    "section_dp",
                ],
            },
            {
                "id": "due_diligence",
                "label": "Due Diligence Workflow",
                "linked_contract": "due_diligence",
                "sections": [
                    "section_cp",
                    "section_toc",
                    "section_1",
                    "section_5",
                    "section_7",
                    "section_dp",
                ],
            },
        ]

        intake_forms = [
            {
                "id": "client_intake_pdf",
                "label": "Client Intake Form",
                "path": str((intake_dir / "client_intake.pdf").resolve()),
                "required_fields": ["client_name", "case_number", "start_date"],
            },
            {
                "id": "field_activity_log",
                "label": "Field Activity Log",
                "path": str((intake_dir / "field_activity_log.pdf").resolve()),
                "required_fields": ["case_number", "investigation_date"],
            },
        ]

        defaults = {
            "case_number": user_data.get("case_number"),
            "client_name": user_data.get("client_name") or user_data.get("business_name"),
            "subject": user_data.get("subject_name") or "Primary Subject",
            "location": user_data.get("case_location") or user_data.get("business_address"),
            "sign_date": user_data.get("sign_date"),
            "start_date": user_data.get("start_date"),
        }
        if not defaults.get("case_number"):
            defaults["case_number"] = f"CASE-{datetime.now():%Y%m%d}"
        if not defaults.get("sign_date"):
            defaults["sign_date"] = datetime.now().strftime('%Y-%m-%d')
        if not defaults.get("start_date"):
            defaults["start_date"] = datetime.now().strftime('%Y-%m-%d')

        payload: Dict[str, Any] = {
            "profile_id": user_data.get("profile_id", "default"),
            "reporting": {
                "workflows": workflows,
                "default": user_data.get("preferred_workflow") or workflows[0]["id"],
            },
            "contracts": {
                "catalog": catalog,
                "default": user_data.get("preferred_contract") or default_contract_id,
            },
            "intake": {
                "forms": intake_forms,
                "required_fields": ["client_name", "case_number", "start_date"],
            },
            "billing": {
                "hourly_rate": user_data.get("labor_rate"),
            },
            "case_defaults": defaults,
        }

        return payload


__all__ = ["ProfileRegistry", "Profile"]
