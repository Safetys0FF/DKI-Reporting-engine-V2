#!/usr/bin/env python3
"""
Section 9 Renderer - Certification & Disclaimers
Produces a standardized certification statement and optional disclaimers
based on available case, investigator, and agency metadata.

Patterned after other section renderers (Section2/5/6) for consistency.
"""

from datetime import datetime
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class Section9Renderer:
    """Renders Section 9 - Certification & Disclaimers"""

    SECTION_KEY = "section_9"
    TITLE = "SECTION 9 - CERTIFICATION & DISCLAIMERS"

    STYLE_RULES = {
        "font": "Times New Roman",
        "section_title": {"size_pt": 16, "bold": True, "all_caps": True, "align": "center", "shaded_background": True},
        "header": {"size_pt": 14, "bold": True, "underline": True, "all_caps": True, "align": "left"},
        "paragraph": {"size_pt": 12, "bold": False, "italic": False, "align": "left"},
        "emphasis": {"size_pt": 12, "italic": True, "align": "left"},
        "line_spacing": 1.15,
    }

    def _val(self, d: Dict[str, Any], key: str, default: str = "") -> str:
        v = d.get(key)
        return str(v).strip() if v else default

    def render_model(self, section_payload: Dict[str, Any], case_sources: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a render tree containing:
        - Title
        - Investigator/Agency certification block
        - Optional disclaimers (if available in case_sources['disclaimers'])
        """

        try:
            now_str = datetime.now().strftime("%Y-%m-%d")

            case = case_sources or {}
            prev = (section_payload or {}).get('previous_sections', {}) or {}
            cp_manifest = (prev.get('section_cp') or {}).get('manifest') if isinstance(prev.get('section_cp'), dict) else None
            cover_profile = (cp_manifest or {}).get('cover_profile', {}) if isinstance(cp_manifest, dict) else {}
            # Pull common fields with reasonable fallbacks
            investigator_name = self._val(case, "assigned_investigator", "David Krashin")
            investigator_license = self._val(case, "investigator_license", "0163814-C000480")
            investigator_title = self._val(case, "investigator_title", "Licensed Private Investigator")

            agency_name = cover_profile.get('agency_name') or self._val(case, "agency_name", "DKI Services LLC")
            agency_license = cover_profile.get('agency_license') or self._val(case, "agency_license", "0200812-IA000307")
            agency_address = cover_profile.get('mailing_address') or self._val(case, "agency_address", "Oklahoma")

            client_name = self._val(case, "client_name", "Client")
            case_id = self._val(case, "case_id", "UNKNOWN")

            standard_certification = (
                f"I, {investigator_name}, {investigator_title} (License {investigator_license}), certify that the contents of this report "
                f"are true and correct to the best of my knowledge and belief. All investigative activities were conducted in accordance "
                f"with applicable laws and professional standards. This report is prepared for {client_name} in relation to Case ID {case_id}."
            )

            agency_attestation = (
                f"{agency_name} (License {agency_license}) affirms that this investigation and report were performed by, or under the direct supervision of, "
                f"a duly licensed investigator. {agency_name} maintains appropriate records and adheres to industry best practices."
            )

            signature_block = (
                f"Signed: {investigator_name}\n"
                f"Title: {investigator_title}\n"
                f"License: {investigator_license}\n"
                f"Agency: {agency_name} (License {agency_license})\n"
                f"Address: {agency_address}\n"
                f"Date: {now_str}"
            )

            disclaimers: List[str] = []
            # Allow callers to inject additional disclaimers
            extra_disclaimers = case.get("disclaimers") or []
            for d in extra_disclaimers:
                if isinstance(d, str) and d.strip():
                    disclaimers.append(d.strip())

            # Reasonable defaults if none provided
            if not disclaimers:
                disclaimers = [
                    "This report is confidential and intended solely for the designated client. Unauthorized distribution is prohibited.",
                    "Findings reflect information available at the time of reporting. Subsequent developments may alter conclusions.",
                    "No surveillance activities were conducted in areas where individuals have a reasonable expectation of privacy.",
                ]

            render_tree: List[Dict[str, Any]] = []
            logo_path = cover_profile.get('logo_path')
            if logo_path:
                render_tree.append({
                    "type": "image",
                    "path": logo_path,
                    "label": None,
                })

            render_tree.append({
                "type": "title",
                "text": self.TITLE,
                "style": self.STYLE_RULES["section_title"],
            })

            render_tree.append({
                "type": "header",
                "text": "CERTIFICATION",
                "style": self.STYLE_RULES["header"],
            })

            render_tree.append({
                "type": "paragraph",
                "text": standard_certification,
                "style": self.STYLE_RULES["paragraph"],
            })

            render_tree.append({
                "type": "paragraph",
                "text": agency_attestation,
                "style": self.STYLE_RULES["paragraph"],
            })

            render_tree.append({
                "type": "paragraph",
                "text": signature_block,
                "style": self.STYLE_RULES["emphasis"],
            })

            render_tree.append({
                "type": "header",
                "text": "DISCLAIMERS",
                "style": self.STYLE_RULES["header"],
            })

            for dtext in disclaimers:
                render_tree.append({
                    "type": "paragraph",
                    "text": f"- {dtext}",
                    "style": self.STYLE_RULES["paragraph"],
                })

            manifest = {
                "section_key": self.SECTION_KEY,
                "fields_rendered": [
                    "investigator_name",
                    "investigator_license",
                    "investigator_title",
                    "agency_name",
                    "agency_license",
                    "agency_address",
                    "client_name",
                    "case_id",
                ],
                "generated_on": datetime.now().isoformat(),
            }

            return {
                "render_tree": render_tree,
                "manifest": manifest,
                "handoff": "gateway",
            }

        except Exception as e:
            logger.error(f"Section 9 render failed: {e}")
            return {
                "render_tree": [
                    {"type": "title", "text": self.TITLE, "style": self.STYLE_RULES["section_title"]},
                    {"type": "paragraph", "text": f"Error generating Section 9: {e}", "style": self.STYLE_RULES["emphasis"]},
                ],
                "manifest": {"section_key": self.SECTION_KEY, "error": str(e)},
                "handoff": "gateway",
            }
