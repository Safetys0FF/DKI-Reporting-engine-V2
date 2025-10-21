"""Initializer for Section 6 mileage tool."""

from __future__ import annotations

import importlib
from typing import Any


def init_section6_mileage_tool(**_: Any):
    """Return the MileageToolV2 class used in Section 6."""

    module = importlib.import_module("section_6_framework")
    return module.MileageToolV2


__all__ = ["init_section6_mileage_tool"]
