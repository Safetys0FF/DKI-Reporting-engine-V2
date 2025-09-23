class SectionBaseFramework:
    """
    Shared base logic for Sections 2A–2E to enforce:
    - Switch handling
    - Fallback rendering
    - Metadata tracking
    - Case mode gating (investigative / field / hybrid)
    - Optional feedback to evidence manager
    """
    DEFAULT_PLACEHOLDER = "*Not used / Not reported*"

    def __init__(self, logic_switches: dict, context: dict, gateway: object = None):
        self.logic_switches = logic_switches
        self.context = context
        self.gateway = gateway
        self.fallback_fields = []
        self.section_key = ""

    def is_trigger_active(self, key: str) -> bool:
        return bool(self.logic_switches.get(key))

    def case_mode_allows(self, modes: set[str]) -> bool:
        return self.logic_switches.get("case_mode") in modes

    def get_field(self, label: str, value: str = None) -> dict:
        clean_value = value.strip() if value else ""
        if not clean_value:
            self.fallback_fields.append(label)
            return {
                "type": "field",
                "label": label,
                "value": self.DEFAULT_PLACEHOLDER,
                "style": "placeholder_value"
            }
        return {
            "type": "field",
            "label": label,
            "value": clean_value,
            "style": "field_value"
        }

    def build_render_tree(self, fields: list[tuple]) -> list[dict]:
        return [self.get_field(label, value) for label, value in fields]

    def generate_manifest(self) -> dict:
        return {
            "section_key": self.section_key,
            "fallback_fields": self.fallback_fields,
            "logic_switches": self.logic_switches
        }

    def render(self, fields: list[tuple]) -> dict:
        result = {
            "render_tree": self.build_render_tree(fields),
            "manifest": self.generate_manifest(),
            "handoff": "gateway"
        }
        self.send_feedback_to_evidence_controller(result)
        return result

    def send_feedback_to_evidence_controller(self, result: dict):
        if not self.gateway:
            return
        evidence_manager = getattr(self.gateway, "evidence_controller", None)
        if hasattr(evidence_manager, "submit_feedback"):
            try:
                evidence_manager.submit_feedback({
                    "section": self.section_key,
                    "manifest": result.get("manifest"),
                    "qa_flags": result.get("manifest", {}).get("logic_switches", {}).get("qa_flags", [])
                })
            except Exception:
                pass


# All Section 2A–2E classes below remain unchanged, except they now support feedback via self.gateway
