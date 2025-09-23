# Section 6 – Billing Summary Renderer

class Section6BillingRenderer:
    """
    Handles Section 6: Billing Summary
    - Fixed template layout
    - Variable billing logic slots (fixed placeholders if undefined)
    - Strict suppression enforcement per case type and scope
    - Total summary and metadata-compliant output
    - Hands back to gateway
    """

    SECTION_KEY = "section_6"
    TITLE = "SECTION 6 – BILLING SUMMARY"

    PLACEHOLDERS = {
        "unknown": "*Unknown or not itemized*",
        "suppressed": "*Due to the nature of this case this portion was not performed or was not necessary*",
        "fixed_reporting": "1 hour @ $100.00 – $100.00"
    }

    BANNED_TOKENS = {"", " ", "N/A", "NA", "TBD", "REDACTED", "[REDACTED]"}

    CATEGORIES = [
        "Surveillance Operations",
        "Investigative Analysis",
        "Records & Document Review",
        "Travel & Mileage",
        "Reporting & File Transfer"
    ]

    def _normalize(self, val):
        return str(val).strip() if val else None

    def _apply_placeholder(self, value, category, case_type):
        if not value or value.upper() in self.BANNED_TOKENS:
            if category == "Reporting & File Transfer":
                return self.PLACEHOLDERS["fixed_reporting"], False
            if (case_type == "Investigative" and category == "Surveillance Operations") or \
               (case_type == "Surveillance" and category == "Investigative Analysis"):
                return self.PLACEHOLDERS["suppressed"], True
            return self.PLACEHOLDERS["unknown"], True
        return value, False

    def render_model(self, section_payload, case_type):
        rendered_blocks = []
        placeholders_used = {}

        rendered_blocks.append({
            "type": "title",
            "text": self.TITLE,
            "style": {"font": "Times New Roman", "size_pt": 16, "bold": True, "align": "center", "all_caps": True}
        })

        total = 0

        for category in self.CATEGORIES:
            raw_val = self._normalize(section_payload.get(category))
            value, is_placeholder = self._apply_placeholder(raw_val, category, case_type)
            if is_placeholder:
                placeholders_used[category] = value
            if not is_placeholder and value:
                try:
                    amount = float(value.split("$")[-1].replace(",", ""))
                    total += amount
                except Exception:
                    pass  # skip total if unreadable format
            rendered_blocks.append({
                "type": "field",
                "label": category,
                "value": value,
                "style": {
                    "font": "Times New Roman",
                    "size_pt": 12,
                    "label_bold": True,
                    "value_italic": is_placeholder,
                    "align": "left",
                    "spacing": 1.15
                }
            })

        # Total Summary
        rendered_blocks.append({
            "type": "total",
            "label": "Total Billed",
            "value": f"${total:,.2f}",
            "style": {
                "font": "Times New Roman",
                "size_pt": 12,
                "bold": True,
                "align": "right",
                "spacing": 1.15
            }
        })

        return {
            "render_tree": rendered_blocks,
            "manifest": {
                "section_key": self.SECTION_KEY,
                "placeholders_used": placeholders_used,
                "total_billed": f"${total:,.2f}"
            },
            "handoff": "gateway"
        }
