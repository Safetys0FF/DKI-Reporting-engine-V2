"""Initializer for Section 3 voice transcription helper."""

from __future__ import annotations

import importlib
from typing import Any


def init_section3_voice_helper(**_: Any):
    """Return the VoiceTranscriptionHelper class."""

    module = importlib.import_module("section_3_framework")
    return module.VoiceTranscriptionHelper


__all__ = ["init_section3_voice_helper"]
