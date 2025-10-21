"""Initializer for Section 4 renderer."""

from __future__ import annotations

import importlib
from typing import Any


def init_section4_renderer(**_: Any):
    """Return the Section4Renderer class."""

    module = importlib.import_module("section_4_framework")
    return module.Section4Renderer


__all__ = ["init_section4_renderer"]
