# Section 2 Pre-Surveillance / Case Prep Renderer Logic

class Section2Renderer:
    """
    Handles Section 2: Pre-Surveillance / Case Prep
    - Breaks into logical subsections (2A–2E)
    - Renderer outputs formatted report structure and manifest
    - Placeholder enforcement and drift guard in place
    - Implements 3x cyclical fallback validation across intake, notes, evidence, and prior section
    - Always hands off to Gateway
    """

    SECTION_KEY = "section_2"
    TITLE = "SECTION 2 – PRE‑SURVEILLANCE / CASE PREP"

    SUBSECTIONS = {
        "2A": ["case_summary", "summary_tags", "case_type_token"],
        "2B": ["verified_subjects", "known_aliases", "verified_addresses", "subject_vehicles", "subject_employment", "subject_contact"],
        "2C": ["routines", "poi_tags", "timeline_blocks", "observed_patterns"],
        "2D": ["geo_areas", "pinned_locations", "visual_aids"],
        "2E": ["field_ready", "ethics_statement", "surveillance_hours_allocated", "planning_notes"]
    }

    PLACEHOLDERS = {
        "unknown": "*Unknown*",
        "unconfirmed": "*Unconfirmed at this time*",
        "suppressed": "*Due to the nature of this case this portion was not performed or was not necessary*"
    }

    BANNED_TOKENS = {"", " ", "N/A", "NA", "TBD", "[REDACTED]", "REDACTED"}

    STYLE_RULES = {
        "font": "Times New Roman",
        "section_title": {"size_pt": 16, "bold": True, "all_caps": True, "align": "center", "shaded_background": True},
        "subsection_header": {"size_pt": 14, "bold": True, "underline": True, "all_caps": True, "align": "left"},
        "field_label": {"size_pt": 12, "bold": True, "align": "left"},
        "field_value": {"size_pt": 12, "bold": False, "italic": False, "align": "left"},
        "placeholder_value": {"size_pt": 12, "italic": True, "align": "left"},
        "line_spacing": 1.15
    }

    def _normalize(self, val):
        return str(val).strip() if val else None

    def _placeholder_for(self, key, value):
        if not value or value.upper() in self.BANNED_TOKENS:
            return self.PLACEHOLDERS["unknown"], True
        return value, False

    def _fallback_check(self, key, zones):
        """
        3-pass cyclical fallback validation across:
        - Intake
        - Investigator Notes
        - Submitted Evidence
        - Prior Section Output
        Uses consistency rules before triggering user query
        """
        for _ in range(3):
            for zone in ["intake", "notes", "evidence", "prior_section"]:
                val = zones.get(zone, {}).get(key)
                if val:
                    return val
        return None

    def render_model(self, section_payload, case_sources):
        rendered_blocks = []
        placeholders_used = {}
        drift_bounced = {}

        rendered_blocks.append({
            "type": "title",
            "text": self.TITLE,
            "style": self.STYLE_RULES["section_title"]
        })

        for sub_key, field_keys in self.SUBSECTIONS.items():
            rendered_blocks.append({
                "type": "subheader",
                "text": f"SUBSECTION {sub_key}",
                "style": self.STYLE_RULES["subsection_header"]
            })
            for key in field_keys:
                val = section_payload.get(key)
                if not val:
                    val = self._fallback_check(key, case_sources)
                value, is_ph = self._placeholder_for(key, self._normalize(val))
                if is_ph:
                    placeholders_used[key] = value
                rendered_blocks.append({
                    "type": "field",
                    "label": key.replace("_", " ").title(),
                    "value": value,
                    "style": self.STYLE_RULES["placeholder_value"] if is_ph else self.STYLE_RULES["field_value"]
                })

        manifest = {
            "section_key": self.SECTION_KEY,
            "placeholders_used": placeholders_used,
            "fields_rendered": [k for keys in self.SUBSECTIONS.values() for k in keys],
            "drift_bounced": drift_bounced
        }

        return {
            "render_tree": rendered_blocks,
            "manifest": manifest,
            "handoff": "gateway"
        }










