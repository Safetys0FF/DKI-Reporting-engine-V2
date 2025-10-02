#!/usr/bin/env python3
"""Adapters bridging Mission Debrief to War Room evidence pipeline."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

PROCESSORS_ROOT = Path(__file__).resolve().parents[3] / "The War Room" / "Processors"
if str(PROCESSORS_ROOT) not in sys.path:
    sys.path.insert(0, str(PROCESSORS_ROOT))

try:  # pragma: no cover - import-time capability check
    from evidence_pipeline import EvidencePipeline  # type: ignore
    from document_processor import DocumentProcessor  # type: ignore
    _PIPELINE_IMPORT_ERROR: Optional[Exception] = None
    _PIPELINE_AVAILABLE = True
except Exception as exc:  # pragma: no cover - recorded for status reporting
    EvidencePipeline = None  # type: ignore
    DocumentProcessor = None  # type: ignore
    _PIPELINE_IMPORT_ERROR = exc
    _PIPELINE_AVAILABLE = False


class EvidencePipelineAdapter:
    """Wrapper that exposes the War Room evidence pipeline to Mission Debrief."""

    def __init__(self, manifest_path: Optional[Path] = None) -> None:
        self.logger = logging.getLogger(__name__)
        self.available = _PIPELINE_AVAILABLE and EvidencePipeline is not None and DocumentProcessor is not None
        self.import_error = _PIPELINE_IMPORT_ERROR
        self.document_processor: Optional[DocumentProcessor] = None  # type: ignore
        self.pipeline: Optional[EvidencePipeline] = None  # type: ignore

        if self.available:
            try:
                self.document_processor = DocumentProcessor()  # type: ignore
                self.pipeline = EvidencePipeline(self.document_processor, manifest_path=manifest_path)  # type: ignore
            except Exception as exc:  # pragma: no cover - safeguard during env bring-up
                self.logger.exception("Evidence pipeline initialisation failed")
                self.available = False
                self.import_error = exc
                self.document_processor = None
                self.pipeline = None

    # ------------------------------------------------------------------
    # Capability helpers
    # ------------------------------------------------------------------
    def is_available(self) -> bool:
        return self.available

    def capability_status(self) -> Dict[str, Any]:
        return {
            "available": self.available,
            "import_error": str(self.import_error) if self.import_error else None,
            "document_processor": bool(self.document_processor),
            "pipeline": bool(self.pipeline),
        }

    # ------------------------------------------------------------------
    # Processing helpers
    # ------------------------------------------------------------------
    def process_batch(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run the War Room evidence pipeline for a batch of file descriptors."""
        if not self.pipeline:
            raise RuntimeError("Evidence pipeline adapter is unavailable")
        return self.pipeline.process_batch(files)

    def process_single(self, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """Convenience helper for single-file processing."""
        return self.process_batch([file_info])


class PdfExtractionAdapter:
    """Thin wrapper that focuses on PDF/text extraction via the evidence pipeline."""

    def __init__(self, manifest_path: Optional[Path] = None) -> None:
        self.logger = logging.getLogger(__name__)
        self.pipeline_adapter = EvidencePipelineAdapter(manifest_path=manifest_path)

    def is_available(self) -> bool:
        return self.pipeline_adapter.is_available()

    def capability_status(self) -> Dict[str, Any]:
        status = self.pipeline_adapter.capability_status()
        status["adapter"] = "pdf_extraction"
        return status

    def extract(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Return the processed data payload, highlighting extracted text."""
        result = self.pipeline_adapter.process_batch(files)
        processed = result.get("processed_data", {}) if isinstance(result, dict) else {}
        extracted_text = processed.get("extracted_text", {}) if isinstance(processed, dict) else {}
        return {
            "result": result,
            "extracted_text": extracted_text,
            "errors": result.get("errors", []) if isinstance(result, dict) else [],
        }
