# body_text_switchboard.py — Controls narrative injection and field rendering logic

from typing import Dict, List, Any

class BodyTextSwitchboard:
    def __init__(self, mode: str):
        self.mode = mode.upper()
        self.logic = self._build_logic()

    def _build_logic(self) -> Dict[str, Any]:
        if self.mode == "INVESTIGATIVE":
            return {
                "title": "SECTION 6 – BILLING SUMMARY (INVESTIGATIVE)",
                "sections": [
                    "Investigation Overview",
                    "Research & Analysis",
                    "Documentation Time",
                    "Compliance Notes"
                ],
                "summary_rules": ["Include contract terms, PO, background steps taken."],
                "field_visibility": False,
                "voice_notes_included": True,
                "mileage_statement": None,
            }

        elif self.mode == "FIELD":
            return {
                "title": "SECTION 6 – BILLING SUMMARY (FIELD OPERATIONS)",
                "sections": [
                    "Surveillance Summary",
                    "Field Logs Verified",
                    "Prep Allocation",
                    "Documentation Fee"
                ],
                "summary_rules": ["Ensure time in/out aligns with Section 3.", "Match narrative with visuals."],
                "field_visibility": True,
                "voice_notes_included": True,
                "mileage_statement": "Mileage was waived as a professional courtesy.",
            }

        elif self.mode == "HYBRID":
            return {
                "title": "SECTION 6 – BILLING SUMMARY (HYBRID SERVICES)",
                "sections": [
                    "Investigation Findings",
                    "Surveillance Results",
                    "Joint Documentation",
                    "Compliance and Review"
                ],
                "summary_rules": [
                    "Tie Sections 2–5 together.",
                    "Flag any overages or field time gaps.",
                    "Mark recon as visible but not billed."
                ],
                "field_visibility": True,
                "voice_notes_included": True,
                "mileage_statement": "Mileage was waived as a professional courtesy.",
            }

        return {
            "title": "SECTION 6 – BILLING SUMMARY",
            "sections": ["Billing Narrative Not Specified"],
            "summary_rules": ["Fallback mode. Check upstream inputs."],
            "field_visibility": False,
            "voice_notes_included": False,
            "mileage_statement": None,
        }

    def get_narrative_blocks(self) -> List[str]:
        return self.logic.get("sections", [])

    def get_title(self) -> str:
        return self.logic.get("title")

    def include_voice_notes(self) -> bool:
        return self.logic.get("voice_notes_included", False)

    def show_mileage_statement(self) -> str:
        return self.logic.get("mileage_statement") or ""

    def get_summary_rules(self) -> List[str]:
        return self.logic.get("summary_rules", [])

    def is_field_visible(self) -> bool:
        return self.logic.get("field_visibility", False)


# Example usage
if __name__ == "__main__":
    for mode in ["Investigative", "Field", "Hybrid", "Unknown"]:
        switch = BodyTextSwitchboard(mode)
        print(f"\n=== {mode.upper()} MODE ===")
        print("Title:", switch.get_title())
        print("Narrative Blocks:", switch.get_narrative_blocks())
        print("Mileage Statement:", switch.show_mileage_statement())
        print("Field Visibility:", switch.is_field_visible())