"""Initializer for Section 8 captioning helper."""

from __future__ import annotations

from typing import Any, Dict, Optional


class Section8Captioner:
    """Generates human-readable captions for media assets."""

    def generate_caption(self, record: Dict[str, Any]) -> Optional[str]:
        label = record.get("label") or record.get("description")
        location = record.get("location")
        captured_at = record.get("captured_at")
        parts = []
        if label:
            parts.append(str(label))
        if location:
            parts.append(str(location))
        if captured_at:
            parts.append(str(captured_at))
        if not parts:
            return None
        return " | ".join(parts)


def init_section8_captioner(**_: Any) -> Section8Captioner:
    """Return the default captioner."""

    return Section8Captioner()


__all__ = ["init_section8_captioner", "Section8Captioner"]
