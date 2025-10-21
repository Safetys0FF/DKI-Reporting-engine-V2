"""Initializer for Section 8 media orchestration helper."""

from __future__ import annotations

from typing import Any, Dict, Optional


class Section8MediaOrchestrator:
    """Lightweight media orchestration helper for catalog summaries."""

    def catalog_media(
        self,
        media_index: Optional[Dict[str, Dict[str, Any]]] = None,
        manifests: Optional[Dict[str, Any]] = None,
        normalized: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        media_index = media_index or {}
        normalized = normalized or {}
        summary = self.summarize(media_index)
        payload: Dict[str, Dict[str, Any]] = {
            "images": normalized.get("images", {}),
            "videos": normalized.get("videos", {}),
            "audio": normalized.get("audio", {}),
            "summary": summary,
        }
        # Promote primary location metadata if available
        if manifests:
            payload["manifests"] = {
                "section_3": manifests.get("section_3"),
                "section_4": manifests.get("section_4"),
            }
        return payload

    def summarize(self, media_index: Optional[Dict[str, Dict[str, Any]]]) -> Dict[str, Any]:
        media_index = media_index or {}
        counts = {
            "images": len(media_index.get("images") or {}),
            "videos": len(media_index.get("videos") or {}),
            "audio": len(media_index.get("audio") or {}),
        }
        return {"counts": counts, "warnings": []}


def init_section8_media_orchestrator(**_: Any) -> Section8MediaOrchestrator:
    """Return a default media orchestrator instance."""

    return Section8MediaOrchestrator()


__all__ = ["init_section8_media_orchestrator", "Section8MediaOrchestrator"]
