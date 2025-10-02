#!/usr/bin/env python3
"""Re-export PdfExtractionAdapter for clarity."""

from __future__ import annotations

from .evidence_pipeline_adapter import PdfExtractionAdapter as PdfExtractionAdapter

__all__ = ["PdfExtractionAdapter"]
