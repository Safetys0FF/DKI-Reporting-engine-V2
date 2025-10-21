"""Initializer for Section 2 Cochran identity tool."""

from __future__ import annotations

import importlib
from typing import Any


def init_cochran_match(**_: Any):
    """Return the CochranMatchTool class."""

    module = importlib.import_module("section_2_framework")
    return module.CochranMatchTool


__all__ = ["init_cochran_match"]
