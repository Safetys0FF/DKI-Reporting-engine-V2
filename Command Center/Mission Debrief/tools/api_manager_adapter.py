#!/usr/bin/env python3
"""Adapters for OSINT/API services exposed to Mission Debrief."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

PROCESSORS_ROOT = Path(__file__).resolve().parents[3] / "The War Room" / "Processors"
if str(PROCESSORS_ROOT) not in sys.path:
    sys.path.insert(0, str(PROCESSORS_ROOT))

try:  # pragma: no cover - ability detection
    from osint_module import OSINTEngine  # type: ignore
    _OSINT_IMPORT_ERROR: Optional[Exception] = None
    _OSINT_AVAILABLE = True
except Exception as exc:  # pragma: no cover - capability reporting
    OSINTEngine = None  # type: ignore
    _OSINT_AVAILABLE = False
    _OSINT_IMPORT_ERROR = exc


class ApiServiceAdapter:
    """Wraps `OSINTEngine` so Mission Debrief can perform external lookups."""

    SERVICE_MAP = {
        "google_search": "google_search",
        "verify_address": "verify_address",
        "reverse_phone": "reverse_phone_lookup",
        "business_lookup": "business_lookup",
        "person_lookup": "person_lookup",
        "comprehensive_verification": "comprehensive_verification",
        "system_status": "get_system_status",
    }

    def __init__(self, api_keys_file: Optional[str] = None, user_profile_manager: Any = None) -> None:
        self.logger = logging.getLogger(__name__)
        self.available = _OSINT_AVAILABLE and OSINTEngine is not None
        self.import_error = _OSINT_IMPORT_ERROR
        self.engine: Optional[OSINTEngine] = None  # type: ignore
        if self.available:
            try:
                self.engine = OSINTEngine(api_keys_file=api_keys_file or "api_keys.json", user_profile_manager=user_profile_manager)  # type: ignore
            except Exception as exc:  # pragma: no cover - handle runtime import errors
                self.logger.exception("Failed to initialise OSINT engine")
                self.available = False
                self.import_error = exc
                self.engine = None

    def is_available(self) -> bool:
        return self.available

    def capability_status(self) -> Dict[str, Any]:
        return {
            "available": self.available,
            "import_error": str(self.import_error) if self.import_error else None,
            "has_engine": self.engine is not None,
        }

    def perform_lookup(self, service: str, **kwargs: Any) -> Dict[str, Any]:
        if not self.engine:
            raise RuntimeError("API services adapter unavailable")
        method_name = self.SERVICE_MAP.get(service, service)
        if not hasattr(self.engine, method_name):
            raise ValueError(f"Unsupported service '{service}'")
        method = getattr(self.engine, method_name)
        result = method(**kwargs)
        if isinstance(result, dict):
            return result
        return {"result": result}

    def get_system_status(self) -> Dict[str, Any]:
        if not self.engine or not hasattr(self.engine, "get_system_status"):
            return {"available": self.available, "engine": bool(self.engine)}
        status = self.engine.get_system_status()
        if isinstance(status, dict):
            return status
        return {"status": status}


class OsintAdapter(ApiServiceAdapter):
    """Alias for clarity when referenced as a professional tool."""
    pass
