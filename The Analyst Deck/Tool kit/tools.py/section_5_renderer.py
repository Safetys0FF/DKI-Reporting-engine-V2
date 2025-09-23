# Section 5 – Review of Supporting Documents Renderer Logic

class Section5Renderer:
    """
    Handles Section 5: Review of Supporting Documents
    - Covers investigative and field documentation
    - Supports hybrid case structure (investigative first, then field)
    - Validates all entries for subject, date, jurisdiction, and type
    - Integrates 3x fallback structure for record data integrity
    - Always hands off to Gateway
    """

    SECTION_KEY = "section_5"
    TITLE = "SECTION 5 – REVIEW OF SUPPORTING DOCUMENTS"

    DOCUMENT_CATEGORIES = [
        "identity_records",
        "supporting_government_records",
        "county_and_court_filings",
        "delivery_confirmations",
        "case_administration"
    ]

    REQUIRED_FIELDS = ["subject_name", "record_type", "jurisdiction", "record_date"]

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
        Performs 3-pass fallback validation over:
        - Intake
        - Prior Section Output
        - Document Upload Index
        Returns first valid entry or None
        """
        for _ in range(3):
            for zone in ["intake", "prior_section", "upload_index"]:
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

        for cat in self.DOCUMENT_CATEGORIES:
            records = section_payload.get(cat, [])
            if not records:
                continue

            rendered_blocks.append({
                "type": "header",
                "text": cat.replace("_", " ").title(),
                "style": self.STYLE_RULES["header"]
            })

            for entry in records:
                block = []
                for field in self.REQUIRED_FIELDS:
                    val = entry.get(field)
                    if not val:
                        val = self._fallback_check(field, case_sources)
                    value, is_ph = self._placeholder_for(field, self._normalize(val))
                    if is_ph:
                        placeholders_used[f"{cat}.{field}"] = value
                    block.append({
                        "type": "field",
                        "label": field.replace("_", " ").title(),
                        "value": value,
                        "style": self.STYLE_RULES["placeholder_value"] if is_ph else self.STYLE_RULES["field_value"]
                    })
                rendered_blocks.extend(block)

        manifest = {
            "section_key": self.SECTION_KEY,
            "placeholders_used": placeholders_used,
            "fields_rendered": self.REQUIRED_FIELDS,
            "drift_bounced": drift_bounced
        }

        return {
            "render_tree": rendered_blocks,
            "manifest": manifest,
            "handoff": "gateway"
        }