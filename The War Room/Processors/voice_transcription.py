#!/usr/bin/env python3
"""Utility wrapper for voice transcription services used by the media engine."""

from __future__ import annotations

import logging
import os
import tempfile
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

try:
    import whisper  # type: ignore
    _HAS_WHISPER = True
except Exception:  # pragma: no cover - library optional
    whisper = None  # type: ignore
    _HAS_WHISPER = False

try:  # Prefer soundfile for reliable WAV writes
    import soundfile as sf  # type: ignore
    _HAS_SOUNDFILE = True
except Exception:  # pragma: no cover - optional dependency
    sf = None  # type: ignore
    _HAS_SOUNDFILE = False

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionResult:
    """Simple container for normalized transcription output."""

    text: str
    language: Optional[str]
    segments: List[Dict[str, Any]]
    model: Optional[str]


class VoiceTranscriber:
    """High-level fa?ade around the configured speech-to-text backend."""

    def __init__(self, model_name: Optional[str] = None, device: Optional[str] = None):
        self.model_name = model_name or os.getenv("DKI_VOICE_MODEL", "tiny")
        self.device = device or os.getenv("DKI_VOICE_DEVICE")
        self.available = _HAS_WHISPER
        self._model = None

        if not self.available:
            logger.warning("Voice transcription backend not available (openai-whisper not installed)")

    # ------------------------------------------------------------------
    def is_ready(self) -> bool:
        """Expose backend availability for callers."""

        return self.available

    # ------------------------------------------------------------------
    def transcribe_file(self, file_path: str, **kwargs: Any) -> Optional[TranscriptionResult]:
        """Transcribe an audio file located on disk."""

        if not self.available:
            return None

        model = self._ensure_model_loaded()
        if model is None:
            return None

        try:
            options = {"verbose": False, "temperature": 0.0}
            options.update(kwargs)
            result = model.transcribe(file_path, **options)
            return self._normalize_output(result)
        except Exception as exc:  # pragma: no cover - backend failure logging
            logger.warning("Voice transcription failed for %s: %s", file_path, exc)
            return None

    # ------------------------------------------------------------------
    def transcribe_array(self, audio_array: Any, sample_rate: int, **kwargs: Any) -> Optional[TranscriptionResult]:
        """Transcribe an in-memory audio array using a temporary WAV container."""

        if not self.available or not _HAS_SOUNDFILE:
            return None

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            temp_path = tmp.name
        try:
            sf.write(temp_path, audio_array, sample_rate)  # type: ignore[arg-type]
            return self.transcribe_file(temp_path, **kwargs)
        finally:
            try:
                os.remove(temp_path)
            except Exception:
                pass

    # ------------------------------------------------------------------
    def _ensure_model_loaded(self):
        if not self.available:
            return None
        if self._model is None:
            try:
                if self.device:
                    self._model = whisper.load_model(self.model_name, device=self.device)  # type: ignore[arg-type]
                else:
                    self._model = whisper.load_model(self.model_name)  # type: ignore[arg-type]
                logger.info("Loaded whisper model '%s' for voice transcription", self.model_name)
            except Exception as exc:  # pragma: no cover - backend load failures
                logger.warning("Failed to load whisper model '%s': %s", self.model_name, exc)
                self._model = None
        return self._model

    # ------------------------------------------------------------------
    def _normalize_output(self, raw: Dict[str, Any]) -> Optional[TranscriptionResult]:
        if not raw:
            return None
        text = (raw.get("text") or "").strip()
        language = raw.get("language")
        segments: List[Dict[str, Any]] = []
        for seg in raw.get("segments", []) or []:
            segments.append({
                "start": float(seg.get("start", 0.0)),
                "end": float(seg.get("end", 0.0)),
                "text": (seg.get("text") or "").strip(),
                "confidence": float(seg.get("avg_logprob", 0.0)) if seg.get("avg_logprob") is not None else None,
            })
        return TranscriptionResult(text=text, language=language, segments=segments, model=self.model_name)


__all__ = ["VoiceTranscriber", "TranscriptionResult"]
