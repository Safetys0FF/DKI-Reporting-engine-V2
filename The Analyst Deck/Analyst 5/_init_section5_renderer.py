"""Initializer for Section 5 renderer."""

from __future__ import annotations

import importlib
from typing import Any


def init_section5_renderer(**_: Any):
    """Return the Section5Renderer class."""

    module = importlib.import_module("section_5_framework")
    return module.Section5Renderer


__all__ = ["init_section5_renderer"]
