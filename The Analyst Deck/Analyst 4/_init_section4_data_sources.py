"""Initializer for Section 4 public records data source."""

from __future__ import annotations

import importlib
from typing import Any


def init_section4_data_sources(**_: Any):
    """Return a PublicRecordsDataSource instance."""

    module = importlib.import_module("section_4_framework")
    DataSource = getattr(module, "PublicRecordsDataSource")
    return DataSource()


__all__ = ["init_section4_data_sources"]
