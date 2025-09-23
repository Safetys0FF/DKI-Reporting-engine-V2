#!/usr/bin/env python3
"""
Section TOC Renderer - Table of Contents preview model.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List


class SectionTOCRenderer:
    SECTION_KEY = "section_toc"
    TITLE = "TABLE OF CONTENTS"

    STYLE_RULES = {
        "font": "Times New Roman",
        "section_title": {"size_pt": 16, "bold": True, "all_caps": True, "align": "center", "shaded_background": True},
        "paragraph": {"size_pt": 12, "bold": False, "italic": False, "align": "left"},
        "emphasis": {"size_pt": 12, "bold": False, "italic": True, "align": "left"},
        "line_spacing": 1.15,
    }

    def render_model(self, section_payload: Dict[str, Any], case_sources: Dict[str, Any]) -> Dict[str, Any]:
        entries = section_payload.get("entries", []) or []
        generated_on = datetime.utcnow().isoformat()
        render_tree: List[Dict[str, Any]] = [
            {
                "type": "title",
                "text": self.TITLE,
                "style": self.STYLE_RULES["section_title"],
            }
        ]

        if entries:
            for entry in entries:
                title = str(entry.get("title") or "Section").strip()
                page = int(entry.get("page") or 1)
                available = bool(entry.get("available", True))
                label = self._format_line(title, page, available)
                style = self.STYLE_RULES["paragraph"] if available else self.STYLE_RULES["emphasis"]
                render_tree.append({
                    "type": "paragraph",
                    "text": label,
                    "style": style,
                })
        else:
            render_tree.append(
                {
                    "type": "paragraph",
                    "text": "No sections are currently available for the table of contents.",
                    "style": self.STYLE_RULES["emphasis"],
                }
            )

        manifest = {
            "section_key": self.SECTION_KEY,
            "generated_on": generated_on,
            "entries": entries,
            "report_type": section_payload.get("report_type"),
            "start_page": section_payload.get("start_page"),
        }

        return {
            "render_tree": render_tree,
            "manifest": manifest,
            "handoff": "gateway",
        }

    def _format_line(self, title: str, page: int, available: bool) -> str:
        sanitized = " ".join(title.split())
        max_width = 72
        dot_section = "."
        label = sanitized.upper()
        if not available:
            label = f"{label} (PENDING)"
        prefix = label[: max_width - 6]
        dots_needed = max(0, max_width - len(prefix) - len(str(page)))
        dots = dot_section * dots_needed
        return f"{prefix}{dots} {page}"


__all__ = ["SectionTOCRenderer"]
