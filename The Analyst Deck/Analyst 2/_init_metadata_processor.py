"""Initializer for Section 2 metadata processor."""

from __future__ import annotations

import importlib
from typing import Any


def init_metadata_processor(**_: Any):
    """Return the MetadataToolV5 class."""

    module = importlib.import_module("section_2_framework")
    return module.MetadataToolV5


__all__ = ["init_metadata_processor"]
