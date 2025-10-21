"""Initializer for Section 4 Cochran identity tool."""

from __future__ import annotations

import importlib
from typing import Any


def init_cochran_match(**_: Any):
    """Return the CochranMatchTool class."""

    module = importlib.import_module("section_4_framework")
    return module.CochranMatchTool


__all__ = ["init_cochran_match"]
