#!/usr/bin/env python3
"""Adapter for printing system."""

from __future__ import annotations

import logging
from typing import Dict, Optional

from .printing_system import PrintingSystem


class PrintingAdapter:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.system = PrintingSystem()

    def is_available(self) -> bool:
        return getattr(self.system, 'HAVE_WIN32_PRINT', False)

    def capability_status(self) -> Dict[str, bool]:
        return {"win32_print": getattr(self.system, 'HAVE_WIN32_PRINT', False)}

    def print_document(self, file_path: str, printer_name: Optional[str] = None, settings: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        return self.system.print_document(file_path, printer_name, settings or {})
