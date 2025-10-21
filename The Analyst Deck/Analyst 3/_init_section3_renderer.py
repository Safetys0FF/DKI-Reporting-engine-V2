"""Initializer for Section 3 renderer."""

from __future__ import annotations

import importlib
from typing import Any


def init_section3_renderer(**_: Any):
    """Return the Section3Renderer class."""

    module = importlib.import_module("section_3_framework")
    return module.Section3Renderer


__all__ = ["init_section3_renderer"]
