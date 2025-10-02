#!/usr/bin/env python3
"""Adapter wrapper for the Mission Debrief digital signature system."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from .digital_signature_system import DigitalSignatureSystem


class DigitalSignatureAdapter:
    """Expose capability metadata and helper methods for digital signing."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.system = DigitalSignatureSystem()

    def is_available(self) -> bool:
        requirements = [
            getattr(self.system, 'HAVE_CRYPTOGRAPHY', False),
            getattr(self.system, 'HAVE_PYPDF2', False),
        ]
        return all(requirements)

    def capability_status(self) -> Dict[str, Any]:
        return {
            "cryptography": getattr(self.system, 'HAVE_CRYPTOGRAPHY', False),
            "pypdf2": getattr(self.system, 'HAVE_PYPDF2', False),
            "reportlab": getattr(self.system, 'HAVE_REPORTLAB', False),
        }

    def sign(self, file_path: str, certificate_path: Optional[str] = None, password: Optional[str] = None) -> Dict[str, Any]:
        return self.system.sign_document(file_path, certificate_path, password)

    def verify(self, file_path: str) -> Dict[str, Any]:
        return self.system.verify_signature(file_path)

    def generate_certificate(self, subject: Dict[str, str], validity_days: int = 365) -> Dict[str, Any]:
        return self.system.generate_self_signed_certificate(subject, validity_days)
