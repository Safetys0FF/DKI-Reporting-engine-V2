"""Initializer for Section 3 tracker path decoder."""

from __future__ import annotations

import importlib
from typing import Any


def init_section3_track_decoder(**_: Any):
    """Return a TrackerPathDecoder instance."""

    module = importlib.import_module("section_3_framework")
    Decoder = getattr(module, "TrackerPathDecoder")
    return Decoder()


__all__ = ["init_section3_track_decoder"]
