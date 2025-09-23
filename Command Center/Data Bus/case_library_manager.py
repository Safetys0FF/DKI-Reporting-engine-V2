# case_library_manager.py
# Manages finalized case storage, recall, and metadata browsing

import os
import json

class CaseLibraryManager:
    def __init__(self, cases_dir="./cases"):
        self.cases_dir = cases_dir

    def list_cases(self):
        return [name for name in os.listdir(self.cases_dir)
                if os.path.isdir(os.path.join(self.cases_dir, name))]

    def get_case_manifest(self, case_id):
        manifest_path = os.path.join(self.cases_dir, case_id, "manifest.json")
        if not os.path.exists(manifest_path):
            return None
        with open(manifest_path, 'r') as f:
            return json.load(f)

    def get_case_metadata(self, case_id):
        manifest = self.get_case_manifest(case_id)
        if not manifest:
            return None
        return {
            "case_id": manifest.get("case_id"),
            "sections": list(manifest.get("sections", {}).keys()),
            "generated_at": manifest.get("generated_at"),
            "locked": manifest.get("locked")
        }

    def get_final_pdf_path(self, case_id):
        path = os.path.join(self.cases_dir, case_id, "report.pdf")
        return path if os.path.exists(path) else None