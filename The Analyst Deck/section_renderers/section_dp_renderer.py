#!/usr/bin/env python3
"""
Section DP Renderer - Disclosure & Authenticity

Builds the disclosure/authenticity page preview used inside the gateway
workflow. The renderer mirrors the language produced by the final report
export routines while surfacing toolkit flags so reviewers can confirm all
quality checks prior to packaging.
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


class SectionDPRenderer:
    SECTION_KEY = "section_dp"
    TITLE = "SECTION DP - DISCLOSURE & AUTHENTICITY"

    STYLE_RULES = {
        "font": "Times New Roman",
        "section_title": {"size_pt": 16, "bold": True, "all_caps": True, "align": "center", "shaded_background": True},
        "header": {"size_pt": 14, "bold": True, "underline": True, "all_caps": True, "align": "left"},
        "paragraph": {"size_pt": 12, "bold": False, "italic": False, "align": "left"},
        "emphasis": {"size_pt": 12, "bold": False, "italic": True, "align": "left"},
        "line_spacing": 1.15,
    }

    def _val(self, data: Dict[str, Any], key: str, default: str = "") -> str:
        value = data.get(key)
        return str(value).strip() if value else default

    def _sanitize(self, text: str) -> str:
        return "".join(ch for ch in (text or "") if ord(ch) < 128)

    def _extract_cover_profile(self, section_payload: Dict[str, Any], case_sources: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        previous_sections = section_payload.get('previous_sections', {}) or {}
        profile: Dict[str, Any] = {}
        source = "case_defaults"

        cp_output = previous_sections.get('section_cp')
        if isinstance(cp_output, dict):
            render_data = cp_output.get('render_data') or {}
            manifest = render_data.get('manifest') if isinstance(render_data, dict) else cp_output.get('manifest')
            if isinstance(manifest, dict):
                candidate = manifest.get('cover_profile', {}) or {}
                if candidate:
                    profile = candidate
                    source = "section_cp"

        if not profile:
            candidate = (case_sources or {}).get('client_profile', {}) or {}
            if candidate:
                profile = candidate
                source = "client_profile"

        if not profile:
            case = case_sources or {}
            profile = {
                'investigator_name': case.get('assigned_investigator', 'David Krashin'),
                'investigator_title': case.get('investigator_title', 'Licensed Private Investigator'),
                'investigator_license': case.get('investigator_license', '0163814-C000480'),
                'agency_name': case.get('agency_name', 'DKI Services LLC'),
                'agency_license': case.get('agency_license', '0200812-IA000307'),
                'phone': case.get('agency_phone') or case.get('client_phone'),
                'email': case.get('agency_email') or case.get('client_email'),
                'logo_path': case.get('agency_logo'),
                'signature_path': case.get('investigator_signature'),
            }
            source = "case_defaults"

        return profile, source

    def _collect_disclaimers(self, previous_sections: Dict[str, Any]) -> List[str]:
        section9 = previous_sections.get('section_9')
        if not isinstance(section9, dict):
            return []

        render_data = section9.get('render_data') or {}
        render_tree = render_data.get('render_tree') if isinstance(render_data, dict) else []
        disclaimers: List[str] = []
        for block in render_tree or []:
            if not isinstance(block, dict):
                continue
            if block.get('type') == 'paragraph':
                text = str(block.get('text', '')).strip()
                if text.startswith('- '):
                    disclaimers.append(self._sanitize(text))
        return disclaimers

    def _summarize_toolkit(self, toolkit_results: Dict[str, Any]) -> Tuple[List[str], List[Dict[str, Any]]]:
        qa_notes: List[str] = []
        manifest_entries: List[Dict[str, Any]] = []

        for tool_name in sorted(toolkit_results.keys()):
            result = toolkit_results.get(tool_name) or {}
            if isinstance(result, dict):
                status = str(result.get('status', 'unknown')).lower()
                summary = self._sanitize(result.get('summary') or result.get('message') or '')
                severity = result.get('severity') or ('error' if status in {'error', 'failed', 'fail'} else 'info')
            else:
                status = 'unknown'
                summary = self._sanitize(str(result))
                severity = 'info'

            manifest_entries.append({
                'tool': tool_name,
                'status': status,
                'severity': severity,
                'summary': summary,
            })

            if status not in {'success', 'ok', 'pass', 'completed'}:
                note = f"{tool_name}: {summary or status.upper()}"
                qa_notes.append(note.strip())

        return qa_notes, manifest_entries

    def render_model(self, section_payload: Dict[str, Any], case_sources: Dict[str, Any]) -> Dict[str, Any]:
        try:
            case_data = section_payload.get('case_data', {}) or (case_sources or {})
            previous_sections = section_payload.get('previous_sections', {}) or {}
            toolkit_results = section_payload.get('toolkit_results', {}) or {}
            report_type = section_payload.get('report_type') or case_data.get('report_type') or 'Investigative'
            metadata = section_payload.get('metadata', {}) or {}

            profile, profile_source = self._extract_cover_profile(section_payload, case_data)
            logo_path = profile.get('logo_path') or profile.get('cover_logo_path')
            signature_path = profile.get('signature_path')

            investigator_name = profile.get('investigator_name') or case_data.get('assigned_investigator', 'David Krashin')
            investigator_title = profile.get('investigator_title') or case_data.get('investigator_title', 'Licensed Private Investigator')
            investigator_license = profile.get('investigator_license') or case_data.get('investigator_license', '0163814-C000480')

            agency_name = profile.get('agency_name') or case_data.get('agency_name', 'DKI Services LLC')
            agency_license = profile.get('agency_license') or case_data.get('agency_license', '0200812-IA000307')
            agency_phone = profile.get('phone') or case_data.get('client_phone')
            agency_email = profile.get('email') or case_data.get('client_email')

            case_id = self._val(case_data, 'case_id', metadata.get('case_id', 'UNKNOWN'))
            client_name = self._val(case_data, 'client_name', 'Client')
            final_timestamp = metadata.get('finalized_timestamp') or metadata.get('processed_at') or datetime.now().isoformat()

            disclosure_content = ''
            disclosure_metadata: Dict[str, Any] = {}
            if HAVE_REPORT_GENERATOR:
                try:
                    generator = ReportGenerator()
                    generator_payload = dict(previous_sections)
                    disclosure = generator._generate_disclosure_page(generator_payload, report_type)
                    disclosure_content = disclosure.get('content', '')
                    disclosure_metadata = disclosure.get('metadata', {}) or {}
                except Exception as gen_err:
                    logger.warning(f"Falling back to inline disclosure generation: {gen_err}")

            if not disclosure_content:
                disclosure_lines = [
                    "DISCLOSURE AND CERTIFICATION",
                    f"This report has been prepared by {investigator_name}, a licensed private investigator (License #{investigator_license}).",
                    "All investigative activities were completed in accordance with applicable laws and agency policy.",
                    "The contents of this report remain confidential and may only be shared with authorized parties.",
                    f"Case ID: {case_id}",
                    f"Report Type: {report_type}",
                    f"Date of Report: {datetime.now().strftime('%B %d, %Y')}",
                    "",
                    "The accompanying documents include the client contract, intake form, final narrative, and supporting exhibits.",
                    f"Neither {investigator_name} nor {agency_name} is responsible for the misuse or unauthorized disclosure of these materials.",
                    "",
                    "Clients are encouraged to consult with legal counsel regarding the findings outlined in this investigation.",
                    "",
                    "_________________________________",
                    investigator_name,
                    investigator_title,
                    f"License: {investigator_license}",
                    f"Date: {datetime.now().strftime('%B %d, %Y')}",
                    "",
                    "_________________________________",
                    agency_name,
                    f"License: {agency_license}",
                    f"Phone: {agency_phone}" if agency_phone else "",
                    f"Email: {agency_email}" if agency_email else "",
                ]
                disclosure_content = "\n".join(line for line in disclosure_lines if line is not None)

            disclaimers = self._collect_disclaimers(previous_sections)
            qa_notes, qa_manifest = self._summarize_toolkit(toolkit_results)

            render_tree: List[Dict[str, Any]] = []
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

            # Break disclosure content into readable blocks
            for block in self._sanitize(disclosure_content).split("\n\n"):
                text = block.strip()
                if not text:
                    continue
                is_signature = text.startswith('_________________________________') or text.startswith(investigator_name)
                style = self.STYLE_RULES["emphasis"] if is_signature else self.STYLE_RULES["paragraph"]
                if text.upper() == "DISCLOSURE AND CERTIFICATION":
                    render_tree.append({
                        "type": "header",
                        "text": text,
                        "style": self.STYLE_RULES["header"],
                    })
                else:
                    render_tree.append({
                        "type": "paragraph",
                        "text": text,
                        "style": style,
                    })

            render_tree.append({
                "type": "header",
                "text": "SECTION 9 ALIGNMENT",
                "style": self.STYLE_RULES["header"],
            })
            if disclaimers:
                for line in disclaimers:
                    render_tree.append({
                        "type": "paragraph",
                        "text": line,
                        "style": self.STYLE_RULES["paragraph"],
                    })
            else:
                render_tree.append({
                    "type": "paragraph",
                    "text": "No additional disclaimers provided beyond Section 9.",
                    "style": self.STYLE_RULES["paragraph"],
                })

            render_tree.append({
                "type": "header",
                "text": "QUALITY FLAGS",
                "style": self.STYLE_RULES["header"],
            })
            if qa_notes:
                for note in qa_notes:
                    render_tree.append({
                        "type": "paragraph",
                        "text": f"- {note}",
                        "style": self.STYLE_RULES["paragraph"],
                    })
            else:
                render_tree.append({
                    "type": "paragraph",
                    "text": "Toolkit checks report no outstanding issues.",
                    "style": self.STYLE_RULES["paragraph"],
                })

            render_tree.append({
                "type": "paragraph",
                "text": f"Finalized timestamp: {final_timestamp}",
                "style": self.STYLE_RULES["emphasis"],
            })

            manifest = {
                "section_key": self.SECTION_KEY,
                "case_id": case_id,
                "client_name": client_name,
                "report_type": report_type,
                "generated_on": datetime.now().isoformat(),
                "finalized_timestamp": final_timestamp,
                "cover_profile_source": profile_source,
                "logo_used": bool(logo_path),
                "signature_path": signature_path,
                "toolkit_flags": qa_manifest,
                "disclaimer_count": len(disclaimers),
                "disclosure_metadata": disclosure_metadata,
            }

            return {
                "render_tree": render_tree,
                "manifest": manifest,
                "handoff": "gateway",
            }

        except Exception as exc:
            logger.error(f"Section DP render failed: {exc}")
            return {
                "render_tree": [
                    {"type": "title", "text": self.TITLE, "style": self.STYLE_RULES["section_title"]},
                    {"type": "paragraph", "text": f"Error generating Section DP: {exc}", "style": self.STYLE_RULES["emphasis"]},
                ],
                "manifest": {"section_key": self.SECTION_KEY, "error": str(exc)},
                "handoff": "gateway",
            }
