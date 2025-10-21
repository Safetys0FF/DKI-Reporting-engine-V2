"""Initializer for Section 8 metadata extraction helper."""

from __future__ import annotations

from typing import Any, Dict, Optional


class Section8MetadataExtractor:
    """Extracts key metadata from media records."""

    def extract(self, media_id: str, record: Dict[str, Any], *, kind: str) -> Optional[Dict[str, Any]]:
        metadata = record.get("metadata") or {}
        exif = record.get("exif") or {}
        response: Dict[str, Any] = {}
        if metadata:
            response["metadata"] = metadata
        if exif:
            response["exif"] = exif
        response.setdefault("kind", kind)
        response.setdefault("media_id", media_id)
        return response or None


def init_section8_metadata_extractor(**_: Any) -> Section8MetadataExtractor:
    """Return the default metadata extractor."""

    return Section8MetadataExtractor()


__all__ = ["init_section8_metadata_extractor", "Section8MetadataExtractor"]
