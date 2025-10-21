"""Initializer for Section 6 voice transcription helper."""

from __future__ import annotations

import importlib
from typing import Any


def init_section6_voice_helper(**_: Any):
    """Return the VoiceTranscriptionHelper class."""

    module = importlib.import_module("section_6_framework")
    return module.VoiceTranscriptionHelper


__all__ = ["init_section6_voice_helper"]
