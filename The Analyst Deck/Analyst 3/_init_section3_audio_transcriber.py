"""Initializer for Section 3 audio transcription helper."""

from __future__ import annotations

import importlib
from typing import Any


def init_section3_audio_transcriber(**_: Any):
    """Return a SurveillanceAudioTranscriber instance."""

    module = importlib.import_module("section_3_framework")
    Transcriber = getattr(module, "SurveillanceAudioTranscriber")
    return Transcriber()


__all__ = ["init_section3_audio_transcriber"]
