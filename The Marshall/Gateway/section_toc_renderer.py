#!/usr/bin/env python3
"""
Section TOC Renderer - Table of Contents

Generates a table of contents based on the current report type section order
and any available generated sections. Page numbers are estimated to help
navigation during review; the final export will recalculate pagination.
"""

from __future__ import annotations

from typing import Dict, Any, List, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SectionTOCRenderer:
    SECTION_KEY = "section_toc"
    TITLE = "TABLE OF CONTENTS"

    STYLE_RULES = {
        "font": "Times New Roman",
        "section_title": {"size_pt": 16, "bold": True, "all_caps": True, "align": "center", "shaded_background": True},
        "header": {"size_pt": 14, "bold": True, "underline": True, "all_caps": True, "align": "left"},
        "paragraph": {"size_pt": 12, "bold": False, "italic": False, "align": "left"},
        "line_spacing": 1.15,
    }

    # Rough estimate: characters per page in default export layout
    CHARS_PER_PAGE = 2000

    def render_model(self, section_payload: Dict[str, Any], case_sources: Dict[str, Any]) -> Dict[str, Any]:
        try:
            report_type = section_payload.get('report_type', 'Investigative')
            prev_sections: Dict[str, Any] = section_payload.get('previous_sections', {}) or {}
            report_sections: List[Tuple[str, str]] = section_payload.get('report_sections', []) or []

            # Build TOC entries in order
            entries: List[Dict[str, Any]] = []
            page_number = 3  # Reserve 1 for cover, 2 for TOC (approx)

            for sid, name in report_sections:
                # Estimate pages from available content; default 1 if unknown
                est_pages = 1
                if sid in prev_sections:
                    content = prev_sections.get(sid, {}).get('content', '')
                    if isinstance(content, str) and content.strip():
                        est_pages = max(1, len(content) // self.CHARS_PER_PAGE)

                entries.append({
                    'section_id': sid,
                    'section_name': name,
                    'estimated_page': page_number,
                    'estimated_pages': est_pages,
                    'available': sid in prev_sections,
                })

                page_number += est_pages

            # Build render tree content
            render_tree: List[Dict[str, Any]] = []
            render_tree.append({
                'type': 'title',
                'text': self.TITLE,
                'style': self.STYLE_RULES['section_title'],
            })

            # Show a simple list with dotted leader style using text fallback
            for e in entries:
                line = f"{e['section_name']} ... {e['estimated_page']}"
                render_tree.append({
                    'type': 'paragraph',
                    'text': line,
                    'style': self.STYLE_RULES['paragraph'],
                })

            manifest = {
                'section_key': self.SECTION_KEY,
                'report_type': report_type,
                'generated_on': datetime.now().isoformat(),
                'entries': entries,
            }

            return {
                'render_tree': render_tree,
                'manifest': manifest,
                'handoff': 'gateway',
            }

        except Exception as e:
            logger.error(f"Section TOC render failed: {e}")
            return {
                'render_tree': [
                    {'type': 'title', 'text': self.TITLE, 'style': self.STYLE_RULES['section_title']},
                    {'type': 'paragraph', 'text': f"Error generating TOC: {e}", 'style': self.STYLE_RULES['paragraph']},
                ],
                'manifest': {'section_key': self.SECTION_KEY, 'error': str(e)},
                'handoff': 'gateway',
            }

