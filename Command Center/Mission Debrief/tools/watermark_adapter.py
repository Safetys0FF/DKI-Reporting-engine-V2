#!/usr/bin/env python3
"""Adapter for watermark tooling."""

from __future__ import annotations

import logging
from typing import Dict

from .watermark_system import WatermarkSystem


class WatermarkAdapter:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.system = WatermarkSystem()

    def is_available(self) -> bool:
        return getattr(self.system, 'HAVE_REPORTLAB', False)

    def capability_status(self) -> Dict[str, bool]:
        return {"reportlab": getattr(self.system, 'HAVE_REPORTLAB', False)}

    def add(self, file_path: str, text: str = 'DRAFT', watermark_type: str = 'draft') -> Dict[str, str]:
        return self.system.add_watermark(file_path, text, watermark_type)
