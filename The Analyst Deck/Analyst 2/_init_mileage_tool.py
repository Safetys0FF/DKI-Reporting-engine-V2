"""Initializer for Section 2 mileage tool."""

from __future__ import annotations

import importlib
from typing import Any


def init_mileage_tool(**_: Any):
    """Return the MileageToolV2 class."""

    module = importlib.import_module("section_2_framework")
    return module.MileageToolV2


__all__ = ["init_mileage_tool"]
