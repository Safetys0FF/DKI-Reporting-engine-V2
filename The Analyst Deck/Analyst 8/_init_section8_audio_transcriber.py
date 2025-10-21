"""Initializer for Section 8 audio transcription helper."""

from __future__ import annotations

from typing import Any, Dict, Optional


class Section8AudioTranscriber:
    """Provides simple audio transcription summaries."""

    def transcribe(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        summary = record.get("summary") or record.get("transcript")
        if summary:
            return {
                "text": summary,
                "language": record.get("language", "en"),
                "duration": record.get("duration"),
            }
        return None


def init_section8_audio_transcriber(**_: Any) -> Section8AudioTranscriber:
    """Return the default audio transcriber."""

    return Section8AudioTranscriber()


__all__ = ["init_section8_audio_transcriber", "Section8AudioTranscriber"]
