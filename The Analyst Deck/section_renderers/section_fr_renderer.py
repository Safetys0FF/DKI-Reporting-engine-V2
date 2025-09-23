#!/usr/bin/env python3
"""
Section FR Renderer - Final Report Assembly Overview

Generates the final review block shown before export. Summarises section
states, highlights outstanding approvals, and presents an ordered preview
using the same ReportGenerator that drives the production exporters.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Tuple
import logging

try:
    from report_generator import ReportGenerator
    HAVE_REPORT_GENERATOR = True
except Exception:
    HAVE_REPORT_GENERATOR = False


logger = logging.getLogger(__name__)


class SectionFRRenderer:
    SECTION_KEY = "section_fr"
    TITLE = "SECTION FR - FINAL REPORT ASSEMBLY"

    STYLE_RULES = {
        "font": "Times New Roman",
        "section_title": {"size_pt": 16, "bold": True, "all_caps": True, "align": "center", "shaded_background": True},
        "header": {"size_pt": 14, "bold": True, "underline": True, "all_caps": True, "align": "left"},
        "paragraph": {"size_pt": 12, "bold": False, "italic": False, "align": "left"},
        "emphasis": {"size_pt": 12, "bold": False, "italic": True, "align": "left"},
        "line_spacing": 1.15,
    }

    def _sanitize(self, text: str) -> str:
        return "".join(ch for ch in (text or "") if ord(ch) < 128)

    def _normalize_state(self, state_value: Any) -> str:
        if hasattr(state_value, 'value'):
            return str(state_value.value)
        text = str(state_value or '').lower()
        if '.' in text:
            text = text.split('.')[-1]
        return text or 'pending'

    def _partition_sections(self, report_sections: List[Tuple[str, str]], section_states: Dict[str, str]) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
        approved: List[Dict[str, str]] = []
        pending: List[Dict[str, str]] = []
        for section_id, label in report_sections:
            if section_id in {'section_fr'}:
                continue
            state = self._normalize_state(section_states.get(section_id, 'pending'))
            entry = {
                'id': section_id,
                'label': label,
                'state': state,
            }
            if state in {'approved', 'completed'}:
                approved.append(entry)
            else:
                pending.append(entry)
        return approved, pending

    def render_model(self, section_payload: Dict[str, Any], case_sources: Dict[str, Any]) -> Dict[str, Any]:
        try:
            case_data = section_payload.get('case_data', {}) or (case_sources or {})
            report_type = section_payload.get('report_type') or case_data.get('report_type') or 'Investigative'
            report_sections = section_payload.get('report_sections') or []
            if not isinstance(report_sections, list):
                report_sections = []
            section_states = section_payload.get('section_states') or {}
            if not isinstance(section_states, dict):
                section_states = {}
            section_states = {sid: self._normalize_state(state) for sid, state in section_states.items()}

            approved_sections, pending_sections = self._partition_sections(report_sections, section_states)
            total_tracked = len([sid for sid, _ in report_sections if sid != 'section_fr'])
            approvals_complete = len(pending_sections) == 0 and total_tracked > 0

            previous_sections = section_payload.get('previous_sections', {}) or {}
            friendly_lookup = {sid: label for sid, label in report_sections}

            preview_titles: List[str] = []
            compiled_metadata: Dict[str, Any] = {}
            if HAVE_REPORT_GENERATOR and previous_sections:
                try:
                    generator = ReportGenerator()
                    generator_payload = dict(previous_sections)
                    case_meta = {
                        'case_id': case_data.get('case_id'),
                        'client_name': case_data.get('client_name'),
                        'report_type': report_type,
                    }
                    generator_payload['_case_meta'] = case_meta
                    preview = generator.generate_full_report(generator_payload, report_type)
                    compiled_metadata = preview.get('metadata', {}) or {}
                    for section in preview.get('sections', []) or []:
                        sec_id = section.get('section_id') or ''
                        title = section.get('section_name') or friendly_lookup.get(sec_id) or sec_id.replace('_', ' ').title()
                        if title:
                            preview_titles.append(self._sanitize(title))
                except Exception as gen_err:
                    logger.warning(f"Final assembly preview failed: {gen_err}")

            render_tree: List[Dict[str, Any]] = []
            render_tree.append({
                "type": "title",
                "text": self.TITLE,
                "style": self.STYLE_RULES["section_title"],
            })

            render_tree.append({
                "type": "header",
                "text": "ASSEMBLY STATUS",
                "style": self.STYLE_RULES["header"],
            })

            summary_lines = [
                f"Total sections tracked: {total_tracked}",
                f"Approved or completed: {len(approved_sections)}",
                f"Pending or awaiting approval: {len(pending_sections)}",
            ]
            if approvals_complete:
                summary_lines.append("All required sections are approved. Ready for export.")
            else:
                summary_lines.append("One or more sections require attention before export.")

            render_tree.append({
                "type": "paragraph",
                "text": "\n".join(summary_lines),
                "style": self.STYLE_RULES["paragraph"],
            })

            if pending_sections:
                render_tree.append({
                    "type": "header",
                    "text": "REMAINING ACTIONS",
                    "style": self.STYLE_RULES["header"],
                })
                for entry in pending_sections:
                    render_tree.append({
                        "type": "paragraph",
                        "text": f"- {entry['label']} ({entry['id']}) is {entry['state']}",
                        "style": self.STYLE_RULES["paragraph"],
                    })

            if approved_sections:
                render_tree.append({
                    "type": "header",
                    "text": "APPROVED SECTIONS",
                    "style": self.STYLE_RULES["header"],
                })
                for entry in approved_sections:
                    render_tree.append({
                        "type": "paragraph",
                        "text": f"- {entry['label']} ({entry['id']})",
                        "style": self.STYLE_RULES["paragraph"],
                    })

            if preview_titles:
                render_tree.append({
                    "type": "header",
                    "text": "PREVIEW ORDER",
                    "style": self.STYLE_RULES["header"],
                })
                for idx, title in enumerate(preview_titles, start=1):
                    render_tree.append({
                        "type": "paragraph",
                        "text": f"{idx}. {title}",
                        "style": self.STYLE_RULES["paragraph"],
                    })

            render_tree.append({
                "type": "paragraph",
                "text": self._sanitize("Use the export controls to generate the DOCX or PDF package once approvals are complete."),
                "style": self.STYLE_RULES["emphasis"],
            })

            manifest = {
                "section_key": self.SECTION_KEY,
                "generated_on": datetime.now().isoformat(),
                "case_id": case_data.get('case_id'),
                "client_name": case_data.get('client_name'),
                "report_type": report_type,
                "total_sections": total_tracked,
                "approved_sections": len(approved_sections),
                "pending_sections": [entry['id'] for entry in pending_sections],
                "approvals_complete": approvals_complete,
                "preview_available": bool(preview_titles),
                "preview_titles": preview_titles,
                "compiled_metadata": compiled_metadata,
            }

            return {
                "render_tree": render_tree,
                "manifest": manifest,
                "handoff": "gateway",
            }

        except Exception as exc:
            logger.error(f"Section FR render failed: {exc}")
            return {
                "render_tree": [
                    {"type": "title", "text": self.TITLE, "style": self.STYLE_RULES["section_title"]},
                    {"type": "paragraph", "text": f"Error generating Section FR: {exc}", "style": self.STYLE_RULES["emphasis"]},
                ],
                "manifest": {"section_key": self.SECTION_KEY, "error": str(exc)},
                "handoff": "gateway",
            }
