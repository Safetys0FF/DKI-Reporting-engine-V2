#!/usr/bin/env python3
"""
Section 7 Renderer - Conclusion

Produces a professional conclusion that:
- Summarizes findings using prior sections (1–5 and 8)
- Notes coverage and simple consistency status
- Avoids billing entirely (Section 6 is intentionally excluded)
- Ends with an explicit decision: Case Closed or Further Investigation Required
"""

from __future__ import annotations

from typing import Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Section7Renderer:
    SECTION_KEY = "section_7"
    TITLE = "SECTION 7 - CONCLUSION"

    STYLE_RULES = {
        "font": "Times New Roman",
        "section_title": {"size_pt": 16, "bold": True, "all_caps": True, "align": "center", "shaded_background": True},
        "header": {"size_pt": 14, "bold": True, "underline": True, "all_caps": True, "align": "left"},
        "paragraph": {"size_pt": 12, "bold": False, "italic": False, "align": "left"},
        "emphasis": {"size_pt": 12, "italic": True, "align": "left"},
        "line_spacing": 1.15,
    }

    def render_model(self, section_payload: Dict[str, Any], case_sources: Dict[str, Any]) -> Dict[str, Any]:
        try:
            report_type = section_payload.get('report_type', 'Investigative')
            case_data = section_payload.get('case_data', {}) or {}
            toolkit = section_payload.get('toolkit_results', {}) or {}
            prev = section_payload.get('previous_sections', {}) or {}

            # Consider only Sections 1–5 and 8
            sec_ids = ['section_1', 'section_2', 'section_3', 'section_4', 'section_5', 'section_8']
            available = {sid: bool(prev.get(sid)) for sid in sec_ids}

            flags: List[str] = []
            for sid, present in available.items():
                if not present:
                    flags.append(f"Missing supporting content from {sid.replace('_', ' ').title()}")

            # Simple continuity signal (from toolkit if present); do not use billing
            continuity = toolkit.get('continuity_check') or {}
            # Handle case where continuity_check returns a tuple (success, log)
            if isinstance(continuity, tuple):
                continuity_ok = continuity[0] if len(continuity) > 0 else False
            elif isinstance(continuity, dict):
                continuity_ok = bool(continuity) and (continuity.get('status') == 'success' or continuity.get('ok') is True)
            else:
                continuity_ok = bool(continuity)
            if continuity and not continuity_ok:
                flags.append("Continuity validation reported issues")

            # Build render tree
            render_tree: List[Dict[str, Any]] = []
            render_tree.append({
                "type": "title",
                "text": self.TITLE,
                "style": self.STYLE_RULES["section_title"],
            })

            render_tree.append({
                "type": "header",
                "text": "SUMMARY OF FINDINGS",
                "style": self.STYLE_RULES["header"],
            })

            client = case_data.get('client_name', 'Client')
            case_id = case_data.get('case_id', 'UNKNOWN')
            intro = (
                f"This conclusion summarizes the {report_type.lower()} investigation for {client} (Case ID: {case_id}). "
                "It reflects corroborated findings from the objectives, requirements, daily logs, surveillance sessions, supporting documents, "
                "and the photo/video evidence index."
            )
            render_tree.append({"type": "paragraph", "text": intro, "style": self.STYLE_RULES["paragraph"]})

            # Evidentiary basis (high-level bullets as paragraphs)
            basis_lines: List[str] = []
            if available['section_1']:
                basis_lines.append("- Objectives and case information identified (Section 1)")
            if available['section_2']:
                basis_lines.append("- Requirements and pre‑surveillance preparation documented (Section 2)")
            if available['section_3']:
                basis_lines.append("- Field activity recorded in daily logs (Section 3)")
            if available['section_4']:
                basis_lines.append("- Surveillance sessions summarized with time anchors (Section 4)")
            if available['section_5']:
                basis_lines.append("- Supporting documentation reviewed (Section 5)")
            if available['section_8']:
                basis_lines.append("- Photo/Video evidence indexed and chronologically aligned (Section 8)")
            if basis_lines:
                render_tree.append({
                    "type": "paragraph",
                    "text": "\n".join(basis_lines),
                    "style": self.STYLE_RULES["paragraph"],
                })

            render_tree.append({
                "type": "header",
                "text": "INTEGRITY CHECKS",
                "style": self.STYLE_RULES["header"],
            })

            integ: List[str] = []
            integ.append(f"- Continuity status: {'Passed' if continuity_ok else 'Issues detected' if continuity else 'Unavailable'}")
            if flags:
                integ.append("- Items requiring review are listed below")
            render_tree.append({"type": "paragraph", "text": "\n".join(integ), "style": self.STYLE_RULES["paragraph"]})

            if flags:
                render_tree.append({
                    "type": "header",
                    "text": "REVIEW FLAGS",
                    "style": self.STYLE_RULES["header"],
                })
                render_tree.append({
                    "type": "paragraph",
                    "text": "\n".join([f"- {f}" for f in flags]),
                    "style": self.STYLE_RULES["paragraph"],
                })

            render_tree.append({
                "type": "header",
                "text": "CLOSING STATEMENT",
                "style": self.STYLE_RULES["header"],
            })

            if flags:
                closing = (
                    "This conclusion reflects the validated findings contained in this report. "
                    "At this time, further investigation is required to resolve the above review items and preserve report integrity."
                )
                decision = "CASE DECISION: Further Investigation Required"
            else:
                closing = (
                    "This conclusion reflects the validated findings contained in this report. "
                    "Based on the current record and corroborated evidence, the investigation is complete."
                )
                decision = "CASE DECISION: Case Closed"

            render_tree.append({"type": "paragraph", "text": closing, "style": self.STYLE_RULES["paragraph"]})
            render_tree.append({"type": "paragraph", "text": decision, "style": self.STYLE_RULES["emphasis"]})

            manifest = {
                "section_key": self.SECTION_KEY,
                "generated_on": datetime.now().isoformat(),
                "coverage": available,
                "flags": flags,
                "decision": decision,
            }

            return {
                "render_tree": render_tree,
                "manifest": manifest,
                "handoff": "gateway",
            }

        except Exception as e:
            logger.error(f"Section 7 render failed: {e}")
            return {
                "render_tree": [
                    {"type": "title", "text": self.TITLE, "style": self.STYLE_RULES["section_title"]},
                    {"type": "paragraph", "text": f"Error generating Section 7: {e}", "style": self.STYLE_RULES["emphasis"]},
                ],
                "manifest": {"section_key": self.SECTION_KEY, "error": str(e)},
                "handoff": "gateway",
            }

