class DKIComplianceTool:
    def __init__(self):
        self.jurisdiction = "Oklahoma"
        self.regulatory_body = "CLEET"
        self.subcontractor_docs_required = ["license", "contract_agreement", "defined_scope_of_work"]
        self.restricted_phrases = ["wiretap", "phone record", "unauthorized tracking"]
        self.search_sources = ["google", "yahoo", "reddit"]
        self.logs = []

    def verify_subcontractor(self, contractor_info):
        missing = [doc for doc in self.subcontractor_docs_required if doc not in contractor_info]
        if missing:
            self.logs.append(f"Subcontractor missing required documents: {missing}")
            return False
        return True

    def scan_evidence(self, evidence_text, source="client"):
        flags = [phrase for phrase in self.restricted_phrases if phrase in evidence_text.lower()]
        if flags:
            self.logs.append(f"Illegal content detected in evidence from {source}: {flags}")
            return False
        return True

    def label_client_evidence(self, evidence_item):
        if "supporting_docs" in evidence_item:
            return f"CLIENT-PROVIDED: {evidence_item['description']} (supported)"
        else:
            self.logs.append(f"Client evidence lacks support: {evidence_item['description']}")
            return None

    def is_compliant(self):
        return not any("Illegal content" in log for log in self.logs)

    def get_final_label(self):
        if self.is_compliant():
            return "COMPLIANT / CLEET VALIDATED"
        return "NON-COMPLIANT – INTERNAL USE ONLY"

    def run_summary(self):
        return {
            "jurisdiction": self.jurisdiction,
            "regulatory_body": self.regulatory_body,
            "compliance_status": self.get_final_label(),
            "log": self.logs
        }
