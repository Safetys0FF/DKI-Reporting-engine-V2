"""Initializer for Section 6 media correlation helper."""

from __future__ import annotations

import importlib
from typing import Any


def init_section6_media_helper(**_: Any):
    """Return the MediaCorrelationHelper class."""

    module = importlib.import_module("section_6_framework")
    return module.MediaCorrelationHelper


__all__ = ["init_section6_media_helper"]
