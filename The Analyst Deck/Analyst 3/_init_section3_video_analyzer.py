"""Initializer for Section 3 video analysis helper."""

from __future__ import annotations

import importlib
from typing import Any


def init_section3_video_analyzer(**_: Any):
    """Return a VideoAnalysisHelper instance."""

    module = importlib.import_module("section_3_framework")
    Analyzer = getattr(module, "VideoAnalysisHelper")
    return Analyzer()


__all__ = ["init_section3_video_analyzer"]
