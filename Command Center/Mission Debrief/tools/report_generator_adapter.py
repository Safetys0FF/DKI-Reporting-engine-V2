#!/usr/bin/env python3
"""Adapter for War Room report generator."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

PROCESSORS_ROOT = Path(__file__).resolve().parents[3] / "The War Room" / "Processors" / "report generator"
PARENT_ROOT = Path(__file__).resolve().parents[3] / "The War Room" / "Processors"
for candidate in [str(PROCESSORS_ROOT), str(PARENT_ROOT)]:
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

try:  # pragma: no cover - dependency probe
    from report_generator import ReportGenerator  # type: ignore
    _GENERATOR_IMPORT_ERROR: Optional[Exception] = None
    _GENERATOR_AVAILABLE = True
except Exception as exc:  # pragma: no cover
    ReportGenerator = None  # type: ignore
    _GENERATOR_IMPORT_ERROR = exc
    _GENERATOR_AVAILABLE = False


class ReportGeneratorAdapter:
    """Expose report generation/export helpers to Mission Debrief."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.available = _GENERATOR_AVAILABLE and ReportGenerator is not None
        self.import_error = _GENERATOR_IMPORT_ERROR
        self.generator: Optional[ReportGenerator] = None  # type: ignore
        if self.available:
            try:
                self.generator = ReportGenerator()  # type: ignore
            except Exception as exc:
                self.logger.exception("Report generator initialisation failed")
                self.available = False
                self.import_error = exc
                self.generator = None

    def is_available(self) -> bool:
        return self.available

    def capability_status(self) -> Dict[str, Any]:
        return {
            "available": self.available,
            "import_error": str(self.import_error) if self.import_error else None,
            "docx_supported": getattr(self.generator, 'HAVE_DOCX', False) if self.generator else False,
            "pdf_supported": getattr(self.generator, 'HAVE_REPORTLAB', False) if self.generator else False,
        }

    def generate(self, section_data: Dict[str, Any], report_type: str = "Investigative") -> Dict[str, Any]:
        if not self.generator:
            raise RuntimeError("Report generator unavailable")
        return self.generator.generate_full_report(section_data, report_type)

    def export(self, payload: Dict[str, Any], export_path: str, export_format: str = "PDF") -> Dict[str, Any]:
        if not self.generator:
            raise RuntimeError("Report generator unavailable")
        return self.generator.export_report(payload, export_path, export_format)

    def save_snapshot(self, payload: Dict[str, Any], output_dir: str) -> str:
        if not self.generator:
            raise RuntimeError("Report generator unavailable")
        return self.generator.save_report_data(payload, output_dir)

    def load_snapshot(self, snapshot_path: str) -> Dict[str, Any]:
        if not self.generator:
            raise RuntimeError("Report generator unavailable")
        return self.generator.load_report_data(snapshot_path)
