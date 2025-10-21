"""Initializer for Section 8 renderer factory."""

from __future__ import annotations

from typing import Any, Callable


def init_section8_renderer(**_: Any) -> Callable[..., Any]:
    """Return a factory that instantiates Section8Renderer with optional dependencies."""

    def factory(
        *,
        captioner: Any = None,
        cv_detector: Any = None,
        audio_transcriber: Any = None,
        metadata_extractor: Any = None,
    ) -> Any:
        from section_8_framework import Section8Renderer

        return Section8Renderer(
            captioner=captioner,
            cv_detector=cv_detector,
            audio_transcriber=audio_transcriber,
            metadata_extractor=metadata_extractor,
        )

    return factory


__all__ = ["init_section8_renderer"]
