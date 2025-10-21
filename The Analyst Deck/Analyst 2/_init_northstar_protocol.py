"""Initializer for Section 2 North Star protocol tool."""

from __future__ import annotations

import importlib
from typing import Any


def init_northstar_protocol(**_: Any):
    """Return the NorthstarProtocolTool class."""

    module = importlib.import_module("section_2_framework")
    return module.NorthstarProtocolTool


__all__ = ["init_northstar_protocol"]
