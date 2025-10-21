"""Initializer for Section 2 reverse continuity tool."""

from __future__ import annotations

import importlib
from typing import Any


def init_reverse_continuity(**_: Any):
    """Return the ReverseContinuityTool class."""

    module = importlib.import_module("section_2_framework")
    return module.ReverseContinuityTool


__all__ = ["init_reverse_continuity"]
