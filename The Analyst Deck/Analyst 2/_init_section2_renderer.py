"""Initializer for Section 2 renderer."""

from __future__ import annotations

import importlib
from typing import Any


def init_section2_renderer(**_: Any):
    """Return the Section2Renderer class."""

    module = importlib.import_module("section_2_framework")
    return module.Section2Renderer


__all__ = ["init_section2_renderer"]
