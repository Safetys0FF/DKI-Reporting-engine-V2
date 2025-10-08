# mileage_tool_v2.py
# DKI Mileage Policy Enforcement Tool v2.0

import os
import json
import hashlib
from datetime import datetime

# --- Configuration ---
MILEAGE_TOLERANCE_PERCENT = 10  # +/- 10% route tolerance
MINIMUM_VALID_MILES = 0.5
MAX_TIME_GAP_MINUTES = 5
MILEAGE_FOLDER = "./artifacts/mileage"

# --- Helper Functions ---
def load_mileage_logs():
    logs = []
    if not os.path.isdir(MILEAGE_FOLDER):
        return logs
    for file in os.listdir(MILEAGE_FOLDER):
        if file.endswith(".json"):
            with open(os.path.join(MILEAGE_FOLDER, file), "r", encoding="utf-8") as f:
                logs.append(json.load(f))
    return logs

def check_tolerance(expected, actual):
    margin = expected * (MILEAGE_TOLERANCE_PERCENT / 100)
    return abs(expected - actual) <= margin or abs(expected - actual) <= MINIMUM_VALID_MILES

def validate_entry(entry):
    issues = []
    if entry.get("billed_to_client"):
        if not entry.get("subcontractor_charge"):
            issues.append("Billed mileage requires subcontractor charge record")
        if not entry.get("case_manager_approval"):
            issues.append("Mileage charge lacks case manager approval")

    expected = entry.get("expected_miles", 0)
    actual = entry.get("actual_miles", 0)
    if not check_tolerance(expected, actual):
        issues.append(f"Mileage variance outside tolerance: expected {expected}, got {actual}")

    if actual < MINIMUM_VALID_MILES:
        issues.append("Mileage below minimum valid reporting threshold")

    return issues

def audit_mileage():
    logs = load_mileage_logs()
    if not logs:
        return {"status": "SKIPPED", "reason": "No mileage artifacts available"}

    report = []
    for log in logs:
        for entry in log.get("entries", []):
            issues = validate_entry(entry)
            report.append({
                "filename": log.get("filename"),
                "entry_id": entry.get("id"),
                "issues": issues,
                "status": "FAIL" if issues else "PASS"
            })

    os.makedirs(MILEAGE_FOLDER, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(MILEAGE_FOLDER, f"audit_report_{timestamp}.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return {"status": "COMPLETED", "report_path": report_path, "entries": len(report)}

