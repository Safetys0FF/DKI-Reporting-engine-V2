# dki_scale_model.py
# Upgraded scalable architecture model with global evidence index, per-section data routing, validation, dictation, and authorization logic

import os
import uuid
import mimetypes
from datetime import datetime
from gateway_controller import GatewayController


class EvidenceClassifier:
    def classify(self, file_path):
        name = os.path.basename(file_path).lower()
        mime, _ = mimetypes.guess_type(file_path)

        if "lease" in name or "contract" in name:
            return "section_5"
        elif name.endswith(".mp4") or "surveillance" in name:
            return "section_3"
        elif name.endswith(".jpg") or name.endswith(".png"):
            return "section_8"
        else:
            return "unassigned"


class ScalableGateway(GatewayController):
    def __init__(self):
        self.master_evidence_index = {}
        self.evidence_map = {}
        self.section_cache = {}
        self.completed_sections = set()

    def register_file(self, file_path):
        section = EvidenceClassifier().classify(file_path)
        evidence_id = str(uuid.uuid4())

        record = {
            "filename": os.path.basename(file_path),
            "path": file_path,
            "assigned_section": section,
            "cross_links": [],
        }

        self.master_evidence_index[evidence_id] = record

        if section not in self.evidence_map:
            self.evidence_map[section] = []

        self.evidence_map[section].append(record)
        print(f"🧾 Registered {file_path} to {section} as {evidence_id}")

    def get_evidence_for(self, section_id):
        return self.evidence_map.get(section_id, [])

    def add_cross_link(self, evidence_id, keyword):
        if evidence_id in self.master_evidence_index:
            self.master_evidence_index[evidence_id]["cross_links"].append(keyword)
            print(f"🔗 Added cross-link: {keyword} to {evidence_id}")

    def transfer_section_data(self, section_id, structured_section_data):
        self.section_cache[section_id] = {
            "data": structured_section_data,
            "validated": False,
            "timestamp": datetime.now().isoformat(),
            "review_notes": []
        }
        print(f"📡 Section data stored for {section_id}")

    def sign_off_section(self, section_id, by_user):
        if section_id in self.section_cache:
            self.section_cache[section_id]["validated"] = True
            self.section_cache[section_id]["signed_by"] = by_user
            self.section_cache[section_id]["sign_time"] = datetime.now().isoformat()
            self.completed_sections.add(section_id)
            print(f"✅ Section {section_id} validated and authorized by {by_user}")

    def is_section_complete(self, section_id):
        return section_id in self.completed_sections

    def get_authorized_context(self):
        authorized = {}
        for sec_id in self.completed_sections:
            authorized[sec_id] = self.section_cache[sec_id]["data"]
        return authorized

    def assemble_for_report(self, section_id):
        entry = self.section_cache.get(section_id)
        if not entry:
            return None

        data = entry["data"]

        if section_id == "section_3":
            blocks = data.get("content", [])
            subject = data.get("subject", "[Unknown Subject]")
            location = data.get("location", "[Unknown Location]")
            narrative = "\n".join([
                f"At {b['start']} — {b['action']} at {location}" for b in blocks
            ])
            return {
                "header": f"Surveillance Summary: {subject}",
                "body": narrative,
                "meta": {
                    "tags": data.get("narrative_tags", []),
                    "priority": data.get("priority", "low"),
                    "validated": entry["validated"],
                    "signed_by": entry.get("signed_by"),
                    "sign_time": entry.get("sign_time")
                }
            }
        return None


class NarrativeAssembler:
    def assemble(self, section_id, data):
        if section_id == "section_3":
            subject = data.get("subject", "[Unknown Subject]")
            location = data.get("location", "[Unknown Location]")
            blocks = data.get("content", [])
            output = []
            for b in blocks:
                output.append(
                    f"On record, subject {subject} was observed to {b['action'].lower()} at {location} around {b['start']}."
                )
            return "\n".join(output)
        return "[No narrative template for this section]"


class Section3Manager:
    def __init__(self, gateway: ScalableGateway, get_active_section):
        self.gateway = gateway
        self.active_section_id = "section_3"
        self.get_active_section = get_active_section
        self.narrative_engine = NarrativeAssembler()

    def run_pipeline(self):
        if self.get_active_section() != self.active_section_id:
            print("❌ Section 3 not active. Skipping.")
            return

        files = self.gateway.get_evidence_for(self.active_section_id)
        for f in files:
            print(f"📁 Processing: {f['filename']}")
            # Mock OCR + AI call
            raw_text = f"(OCR’d text from {f['filename']})"
            structured = {
                "section": "section_3",
                "subject": "Matthew Rajesh",
                "location": "714 N Duncan St",
                "content": [
                    {"start": "12:00", "end": "13:15", "action": "Departed"},
                    {"start": "13:45", "end": "15:00", "action": "Returned"}
                ],
                "priority": "high",
                "narrative_tags": ["activity", "location"]
            }

            # Dictation logic
            narrative = self.narrative_engine.assemble(self.active_section_id, structured)
            structured["dictated_narrative"] = narrative

            self.gateway.transfer_section_data(self.active_section_id, structured)
            self.gateway.add_cross_link(f"{f['filename']}", "subject:Matthew Rajesh")


# === USAGE ===
if __name__ == "__main__":
    gateway = ScalableGateway()
    active_section = lambda: "section_3"

    # Simulate file uploads
    test_files = [
        "uploads/surveillance_log_1.jpg",
        "uploads/Lease_Agreement.pdf",
        "uploads/Subject_Photo.png",
    ]

    for f in test_files:
        gateway.register_file(f)

    # Run a section manager
    section3 = Section3Manager(gateway, active_section)
    section3.run_pipeline()

    # Mark section complete
    gateway.sign_off_section("section_3", by_user="David Krashin")

    # Assemble for report output
    report_data = gateway.assemble_for_report("section_3")
    print("\n📝 ASSEMBLED REPORT DATA:")
    print(report_data)

    # Pull global context
    global_context = gateway.get_authorized_context()
    print("\n🌐 GLOBAL CONTEXT ACCESSIBLE TO OTHER SECTIONS:")
    print(global_context)
