# Section 3 Surveillance Logs Renderer Logic

class Section3Renderer:
    """
    Handles Section 3: Daily Surveillance Logs
    - Field logs with full time-stamp format
    - Placeholder compliance
    - 3x cyclical fallback logic across 4 data zones
    - Outputs section artifact + manifest, returns to Gateway
    """

    SECTION_KEY = "section_3"
    TITLE = "SECTION 3 – SURVEILLANCE REPORTS / DAILY LOGS"

    WHITELIST_FIELDS = [
        "date_block", "time_logs", "field_agent", "location_context", "activities_observed",
        "photos_captured", "vehicles_logged", "weather_conditions", "narrative_notes"
    ]

    PLACEHOLDERS = {
        "unknown": "*Unknown*",
        "unconfirmed": "*Unconfirmed at this time*",
        "suppressed": "*Due to the nature of this case this portion was not performed or was not necessary*"
    }

    BANNED_TOKENS = {"", " ", "N/A", "NA", "TBD", "[REDACTED]", "REDACTED"}

    STYLE_RULES = {
        "font": "Times New Roman",
        "section_title": {"size_pt": 16, "bold": True, "all_caps": True, "align": "center", "shaded_background": True},
        "header": {"size_pt": 14, "bold": True, "underline": True, "all_caps": True, "align": "left"},
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
        Performs 3x cyclical validation over all fallback zones:
        - intake, notes, evidence, prior_section
        Returns first valid value or None after full cycle
        """
        for _ in range(3):
            for zone in ["intake", "notes", "evidence", "prior_section"]:
                val = zones.get(zone, {}).get(key)
                if val:
                    return val
        return None

    def render_model(self, section_payload, case_sources):
        rendered_blocks = []
        drift_bounced = {}
        placeholders_used = {}

        rendered_blocks.append({
            "type": "title",
            "text": self.TITLE,
            "style": self.STYLE_RULES["section_title"]
        })

        for key in self.WHITELIST_FIELDS:
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
            "fields_rendered": self.WHITELIST_FIELDS,
            "placeholders_used": placeholders_used,
            "drift_bounced": drift_bounced
        }

        return {
            "render_tree": rendered_blocks,
            "manifest": manifest,
            "handoff": "gateway"
        }
