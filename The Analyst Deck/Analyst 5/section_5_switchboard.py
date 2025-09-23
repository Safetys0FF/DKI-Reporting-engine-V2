# section5_switchboard.py — Logic Switchboard for Section 5: Supporting Documents

from typing import Dict, List, Any

class Section5Switchboard:
    BANNED_TOKENS = {"", " ", "N/A", "NA", "TBD", "[REDACTED]", "REDACTED"}

    MODE_TRIGGERS = {
        "INVESTIGATIVE": {
            "contracts": ["investigative", "analysis"],
            "intake_flags": ["investigation_only", "intel_requested"],
            "document_keys": ["findings_timeline", "verified_confirmations"]
        },
        "SURVEILLANCE": {
            "contracts": ["field", "surveillance"],
            "intake_flags": ["surveillance_only", "tracking_requested"],
            "document_keys": ["full_field_log", "visual_metadata_checks"]
        },
        "HYBRID": {
            "contracts": ["hybrid"],
            "intake_flags": ["investigation_then_surveillance", "tiered_case"],
            "document_keys": ["findings_list", "field_log_block"]
        }
    }

    REQUIRED_FIELDS = ["subject_name", "record_type", "jurisdiction", "record_date"]
    DOCUMENT_CATEGORIES = [
        "identity_records",
        "supporting_government_records",
        "county_and_court_filings",
        "delivery_confirmations",
        "case_administration"
    ]

    def __init__(self, context: Dict[str, Any]):
        self.context = context
        self.mode = self._detect_mode()
        self.output = self._configure_mode()
        self.toolkit_results = self._run_integrated_tools()

    def _detect_mode(self) -> str:
        contracts = [c.lower() for c in self.context.get("contracts", [])]
        intake_flags = self.context.get("intake_flags", [])
        doc_keys = set(self.context.get("document_payload", {}).keys())

        for mode, triggers in self.MODE_TRIGGERS.items():
            if (
                any(ct in triggers["contracts"] for ct in contracts) and
                any(f in triggers["intake_flags"] for f in intake_flags) and
                any(k in doc_keys for k in triggers["document_keys"])
            ):
                return mode
        return "FIELD"

    def _configure_mode(self) -> Dict[str, Any]:
        if self.mode == "INVESTIGATIVE":
            return {
                "heading": "SECTION 5 - INVESTIGATION DOCUMENT INVENTORY",
                "suppress": ["visuals"],
                "billing_model": "Flat",
                "document_scope": ["identity_records", "case_administration"]
            }
        elif self.mode == "FIELD":
            return {
                "heading": "SECTION 5 - SUPPORTING DOCUMENTS",
                "enforce": ["jurisdiction_required", "date_required"],
                "billing_model": "Hourly",
                "document_scope": self.DOCUMENT_CATEGORIES
            }
        elif self.mode == "HYBRID":
            return {
                "heading": "SECTION 5 - INVESTIGATION & FIELD DOCUMENTS",
                "hybrid_note": "Field ops were launched following initial investigative findings.",
                "billing_model": "Hybrid",
                "document_scope": self.DOCUMENT_CATEGORIES
            }

    def _run_integrated_tools(self) -> Dict[str, Any]:
        from metadata_tool_v_5 import process_zip
        from reverse_continuity_tool import ReverseContinuityTool
        from cochran_match_tool import verify_identity

        metadata_zip = self.context.get("metadata_bundle_zip")
        metadata_result = process_zip(metadata_zip, "./metadata_out") if metadata_zip else {"status": "SKIPPED"}

        reverse_tool = ReverseContinuityTool()
        documents = self.context.get("document_payload", {})
        doc_text_blob = "\n".join([r.get("record_title", "") for cat in documents.values() for r in cat])
        continuity_check, continuity_log = reverse_tool.run_validation(doc_text_blob, [], [])

        subjects = self.context.get("subjects", [])
        candidates = self.context.get("identity_candidates", {})
        identity_checks = []
        for subj in subjects:
            sid = subj.get("id") or subj.get("subject_id")
            if sid and sid in candidates:
                identity_checks.append({"subject_id": sid, "result": verify_identity(subj, candidates[sid])})

        return {
            "metadata_audit": metadata_result,
            "reverse_continuity": {"ok": continuity_check, "log": continuity_log},
            "identity_checks": identity_checks,
        }

    def get_value_or_placeholder(self, field_name: str, value: str) -> str:
        if not value or str(value).strip().upper() in self.BANNED_TOKENS:
            return f"*Unknown for {field_name}*"
        return value.strip()

    def render_config(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            **self.output,
            "required_fields": self.REQUIRED_FIELDS,
            "toolkit": self.toolkit_results
        }


# Example usage
if __name__ == "__main__":
    example_contexts = [
        {
            "contracts": ["Investigative"],
            "intake_flags": ["intel_requested"],
            "document_payload": {"verified_confirmations": [{}]},
            "metadata_bundle_zip": "./example.zip",
            "subjects": [],
            "identity_candidates": {}
        },
        {
            "contracts": ["Surveillance"],
            "intake_flags": ["tracking_requested"],
            "document_payload": {"visual_metadata_checks": [{}]},
            "metadata_bundle_zip": None,
            "subjects": [],
            "identity_candidates": {}
        }
    ]

    for i, ctx in enumerate(example_contexts, 1):
        board = Section5Switchboard(ctx)
        print(f"\n--- CONTEXT {i} ---")
        for k, v in board.render_config().items():
            print(f"{k}: {v}")