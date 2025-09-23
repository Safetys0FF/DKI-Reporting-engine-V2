# section4_mode_switchboard.py — with WHITELISTED LOGIC TRIGGERS

from typing import Dict, List, Any

class Section4Switchboard:
    BANNED_TOKENS = {"", " ", "N/A", "NA", "TBD", "[REDACTED]", "REDACTED"}

    SWITCH_TRIGGERS = {
        "INVESTIGATIVE": {
            "contracts": ["investigative", "analysis"],
            "intake_flags": ["investigation_only", "intel_requested"],
            "evidence_keys": ["findings_timeline", "verified_confirmations"]
        },
        "FIELD": {
            "contracts": ["field", "surveillance"],
            "intake_flags": ["surveillance_only", "tracking_requested"],
            "evidence_keys": ["full_field_log", "visual_metadata_checks"]
        },
        "HYBRID": {
            "contracts": ["hybrid"],
            "intake_flags": ["investigation_then_surveillance", "tiered_case"],
            "evidence_keys": ["findings_list", "field_log_block"]
        }
    }

    def __init__(self, context: Dict[str, Any]):
        self.context = context
        self.mode = self._detect_mode()
        self.output = self._configure_mode()

    def _detect_mode(self) -> str:
        contracts = [c.lower() for c in self.context.get("contracts", [])]
        intake_flags = self.context.get("intake_flags", [])
        evidence_keys = set(self.context.get("evidence_payload", {}).keys())

        for mode, triggers in self.SWITCH_TRIGGERS.items():
            if (
                any(ct in triggers["contracts"] for ct in contracts) and
                any(flag in triggers["intake_flags"] for flag in intake_flags) and
                any(key in evidence_keys for key in triggers["evidence_keys"])
            ):
                return mode
        return "FIELD"  # default fallback

    def _configure_mode(self) -> Dict[str, Any]:
        if self.mode == "INVESTIGATIVE":
            return {
                "heading": "INVESTIGATION DETAILS",
                "fields": ["findings_timeline", "verified_confirmations", "document_notes"],
                "suppress": ["field_logs", "visuals", "billing_blocks"],
                "billing_model": "Flat"
            }

        elif self.mode == "FIELD":
            return {
                "heading": "SURVEILLANCE SUMMARY",
                "fields": ["full_field_log", "billing_blocks", "visual_metadata_checks"],
                "enforce": ["continuity_checks", "timestamp_requirements"],
                "billing_model": "Hourly"
            }

        elif self.mode == "HYBRID":
            return {
                "heading": ["INVESTIGATION DETAILS", "FIELD DEPLOYMENT (PHASE 2)"],
                "fields": ["findings_list", "field_log_block", "hybrid_special_note"],
                "field_log_block": {
                    "label": "FIELD DEPLOYMENT (PHASE 2)",
                    "visuals_mode": "Supplemental Verification",
                    "billing_split": {"investigative": [1, 2], "field": [3]}
                },
                "billing_model": "Hybrid"
            }

    def get_value_or_placeholder(self, field_name: str, value: str) -> str:
        if not value or str(value).strip().upper() in self.BANNED_TOKENS:
            return f"*Unknown for {field_name}*"
        return value.strip()

    def render_config(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            **self.output
        }


# Example usage
if __name__ == "__main__":
    test_contexts = [
        {
            "contracts": ["Investigative"],
            "intake_flags": ["investigation_only"],
            "evidence_payload": {"findings_timeline": "2025-08-21"}
        },
        {
            "contracts": ["Surveillance"],
            "intake_flags": ["tracking_requested"],
            "evidence_payload": {"full_field_log": "Log Entry A"}
        },
        {
            "contracts": ["Hybrid"],
            "intake_flags": ["investigation_then_surveillance"],
            "evidence_payload": {"field_log_block": "Phase 2 Start"}
        },
        {
            "contracts": ["Unknown"],
            "intake_flags": [],
            "evidence_payload": {}
        }
    ]

    for idx, context in enumerate(test_contexts, 1):
        board = Section4Switchboard(context)
        print(f"\n--- TEST CONTEXT {idx} ---")
        for k, v in board.render_config().items():
            print(f"{k}: {v}")