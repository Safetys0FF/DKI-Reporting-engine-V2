"""Initializer for Section 4 voice transcription helper."""

from __future__ import annotations

import importlib
from typing import Any


def init_section4_voice_helper(**_: Any):
    """Return the VoiceTranscriptionHelper class."""

    module = importlib.import_module("section_4_framework")
    return module.VoiceTranscriptionHelper


__all__ = ["init_section4_voice_helper"]
