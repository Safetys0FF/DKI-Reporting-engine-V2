"""Initializer for Section 8 computer vision detector helper."""

from __future__ import annotations

from typing import Any, Dict, Optional


class Section8CVDetector:
    """Stub detector that annotates media with heuristic tags."""

    def analyze(self, record: Dict[str, Any]) -> Dict[str, Any]:
        tags = []
        if record.get("kind") == "image":
            tags.append("photo")
        if record.get("kind") == "video":
            tags.append("video")
        if record.get("location"):
            tags.append("geo-tagged")
        if record.get("caption"):
            tags.append("captioned")
        return {"tags": tags}


def init_section8_cv_detector(**_: Any) -> Section8CVDetector:
    """Return the default CV detector helper."""

    return Section8CVDetector()


__all__ = ["init_section8_cv_detector", "Section8CVDetector"]
