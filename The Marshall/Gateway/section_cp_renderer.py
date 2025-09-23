#!/usr/bin/env python3
"""
Section CP Renderer - Cover Page

Produces a standardized cover page section for review/approval in the
gateway flow. The final exported document will still build its own cover
page via ReportGenerator, but this renderer lets the user preview and
approve the cover content early.
"""

from __future__ import annotations

from typing import Dict, Any, List
from datetime import datetime
import logging

try:
    # Optional: use configuration defaults for company/investigator info
    from config import get_config
    HAVE_CONFIG = True
except Exception:
    HAVE_CONFIG = False

logger = logging.getLogger(__name__)


class SectionCPRenderer:
    SECTION_KEY = "section_cp"
    TITLE = "COVER PAGE"

    STYLE_RULES = {
        "font": "Times New Roman",
        "section_title": {"size_pt": 16, "bold": True, "all_caps": True, "align": "center", "shaded_background": True},
        "header": {"size_pt": 14, "bold": True, "underline": True, "all_caps": True, "align": "left"},
        "field_label": {"size_pt": 12, "bold": True, "align": "left"},
        "field_value": {"size_pt": 12, "bold": False, "italic": False, "align": "left"},
        "placeholder_value": {"size_pt": 12, "italic": True, "align": "left"},
        "paragraph": {"size_pt": 12, "bold": False, "italic": False, "align": "left"},
        "line_spacing": 1.15,
    }

    def _val(self, d: Dict[str, Any], key: str, default: str = "") -> str:
        v = d.get(key)
        return str(v).strip() if v else default

    def render_model(self, section_payload: Dict[str, Any], case_sources: Dict[str, Any]) -> Dict[str, Any]:
        try:
            report_type = section_payload.get('report_type', 'Investigative')
            case_data = section_payload.get('case_data', {}) or {}
            cover_logo_path = section_payload.get('cover_logo_path')

            company = {}
            investigator = {}
            if HAVE_CONFIG:
                try:
                    cfg = get_config()
                    company = cfg.get_company_info() or {}
                    investigator = cfg.get_investigator_info() or {}
                except Exception:
                    pass

            # Values with fallbacks
            client_name = self._val(case_data, 'client_name', 'Client')
            client_phone = self._val(case_data, 'client_phone', '')
            client_address = self._val(case_data, 'client_address', '')
            contract_date = self._val(case_data, 'contract_date', '')
            case_id = self._val(case_data, 'case_id', '')

            client_profile = section_payload.get('client_profile', {}) or {}

            inv_name = self._val(client_profile, 'investigator_name',
                                  self._val(case_data, 'assigned_investigator', investigator.get('name', '')))
            inv_license = self._val(client_profile, 'investigator_license',
                                    self._val(case_data, 'investigator_license', investigator.get('license', '')))
            inv_title = self._val(client_profile, 'investigator_title',
                                   self._val(case_data, 'investigator_title', investigator.get('title', 'Licensed Private Investigator')))

            co_name = self._val(client_profile, 'agency_name', self._val(case_data, 'agency_name', company.get('name', '')))
            co_license = self._val(client_profile, 'agency_license', self._val(case_data, 'agency_license', company.get('license', '')))
            co_address = company.get('address', '')
            co_phone = company.get('phone', '')
            co_email = company.get('email', '')

            date_generated = datetime.now().strftime("%B %d, %Y")

            # Build render tree (add logo if available)
            render_tree: List[Dict[str, Any]] = []
            # Emit image block for logo if path available
            # Prefer client profile logo path, then user setting, then config
            logo_path = (client_profile.get('cover_logo_path') or client_profile.get('logo_path')
                         or cover_logo_path or company.get('logo_path'))
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

            subtitle = "INVESTIGATION FINAL REPORT"

            render_tree.append({
                "type": "paragraph",
                "text": subtitle,
                "style": self.STYLE_RULES["paragraph"],
            })

            # Case Number logic: LASTNAME-MONTH-YEAR(2)
            case_number = self._compute_case_number(client_name, contract_date)
            meta_lines = [
                f"CASE NUMBER: ({case_number})",
                f"Client: {client_name}",
                f"Date: {date_generated}",
            ]
            if client_phone:
                meta_lines.append(f"Client Phone: {client_phone}")
            if client_address:
                meta_lines.append(f"Client Address: {client_address}")

            render_tree.append({
                "type": "paragraph",
                "text": "\n".join(meta_lines),
                "style": self.STYLE_RULES["paragraph"],
            })

            # Prepared by / Company block
            pb_lines = []
            if inv_license:
                pb_lines.append(f"Oklahoma Investigator License #: {inv_license}")
            if co_name:
                pb_lines.append("")
                pb_lines.append(co_name)
            if co_license:
                pb_lines.append(f"Oklahoma Agency License #: {co_license}")
            # Insert mailing address and city/state ZIP between licenses and phone
            mailing_address = (
                self._val(client_profile, 'agency_mailing_address',
                          self._val(client_profile, 'mailing_address', co_address))
            )
            city_state_zip = (
                self._val(client_profile, 'agency_city_state_zip',
                          self._val(client_profile, 'city_state_zip', ''))
            )
            # Try compose from discrete parts if not provided
            if not city_state_zip:
                city = self._val(client_profile, 'city', '')
                state = self._val(client_profile, 'state', '')
                postal = self._val(client_profile, 'zip', '') or self._val(client_profile, 'postal_code', '')
                if city or state or postal:
                    city_state_zip = ", ".join([p for p in [city, state] if p])
                    if postal:
                        city_state_zip = (city_state_zip + f" {postal}").strip()
            if mailing_address:
                pb_lines.append(f"Mailing Address: {mailing_address}")
            if city_state_zip:
                pb_lines.append(f"City/State ZIP: {city_state_zip}")
            # Contact info prefers client profile override
            phone_pref = self._val(client_profile, 'phone', co_phone)
            email_pref = self._val(client_profile, 'email', co_email)
            if phone_pref:
                pb_lines.append(f"Phone: {phone_pref}")
            if email_pref:
                pb_lines.append(f"Email: {email_pref}")
            # Optional client slogan (e.g., "Truth Conquers ALL"), max 100 chars
            slogan = self._val(client_profile, 'slogan', '')
            if slogan:
                slogan = slogan[:100]
                pb_lines.append(f"“{slogan}”")

            render_tree.append({
                "type": "paragraph",
                "text": "\n".join([ln for ln in pb_lines if ln]),
                "style": self.STYLE_RULES["paragraph"],
            })

            # Expose a complete cover_profile block so disclosure page can reuse exactly these fields
            # Include ALL profile data from client_profile for complete integration
            cover_profile = {
                # Business/Agency Information
                'agency_name': co_name,
                'agency_license': co_license,
                'agency_mailing_address': mailing_address if mailing_address else company.get('address', ''),
                'agency_city_state_zip': city_state_zip,
                'phone': phone_pref,
                'email': email_pref,
                'cover_logo_path': logo_path or '',
                'logo_path': logo_path or '',
                'slogan': slogan if slogan else '',
                
                # Personal/Investigator Information
                'investigator_name': inv_name,
                'investigator_title': inv_title,
                'investigator_license': inv_license,
                'personal_phone': self._val(client_profile, 'personal_phone', ''),
                'personal_email': self._val(client_profile, 'personal_email', ''),
                'personal_mailing_address': self._val(client_profile, 'personal_mailing_address', ''),
                'personal_city_state_zip': self._val(client_profile, 'personal_city_state_zip', ''),
                'profile_photo_path': self._val(client_profile, 'profile_photo_path', ''),
                'signature_path': self._val(client_profile, 'signature_path', ''),
                
                # Additional fields for complete profile integration
                **{k: v for k, v in client_profile.items() if k not in [
                    'agency_name', 'agency_license', 'agency_mailing_address', 'agency_city_state_zip',
                    'phone', 'email', 'cover_logo_path', 'logo_path', 'slogan',
                    'investigator_name', 'investigator_title', 'investigator_license',
                    'personal_phone', 'personal_email', 'personal_mailing_address', 'personal_city_state_zip',
                    'profile_photo_path', 'signature_path'
                ]}
            }

            manifest = {
                "section_key": self.SECTION_KEY,
                "report_type": report_type,
                "case_id": case_id,
                "client_name": client_name,
                "generated_on": datetime.now().isoformat(),
                "uses_config_defaults": HAVE_CONFIG,
                "case_number": case_number,
                "logo_used": bool(logo_path),
                "slogan": slogan if slogan else None,
                "cover_profile": cover_profile,
            }

            return {
                "render_tree": render_tree,
                "manifest": manifest,
                "handoff": "gateway",
            }

        except Exception as e:
            logger.error(f"Section CP render failed: {e}")
            return {
                "render_tree": [
                    {"type": "title", "text": self.TITLE, "style": self.STYLE_RULES["section_title"]},
                    {"type": "paragraph", "text": f"Error generating Cover Page: {e}", "style": self.STYLE_RULES["paragraph"]},
                ],
                "manifest": {"section_key": self.SECTION_KEY, "error": str(e)},
                "handoff": "gateway",
            }

    def _compute_case_number(self, client_name: str, contract_date: str) -> str:
        try:
            last = (client_name or '').strip().split()[-1]
            last = last.upper() if last else 'CLIENT'
            # Expect contract_date like YYYY-MM-DD
            mm = '00'
            yy = '00'
            if contract_date:
                parts = str(contract_date).split('-')
                if len(parts) >= 2:
                    mm = f"{int(parts[1]):02d}"
                if len(parts) >= 1:
                    y = parts[0]
                    yy = f"{int(y) % 100:02d}"
            return f"{last}-{mm}-{yy}"
        except Exception:
            return "CLIENT-00-00"
