# northstar_protocol_tool.py
# DKI North Star Classification Engine v1.0

from datetime import datetime
import json

# --- Case Anchor Configuration ---
CASE_ANCHORS = {
    "contract_date": "2023-11-10T00:00:00",
    "field_ops_start": "2023-11-15T08:00:00",
    "timezone": "UTC"
}

# --- Classification Boundaries ---
def classify_asset(field_time):
    contract = datetime.fromisoformat(CASE_ANCHORS["contract_date"])
    ops_start = datetime.fromisoformat(CASE_ANCHORS["field_ops_start"])

    if field_time < contract:
        return "PRE-INVESTIGATIVE"
    elif contract <= field_time < ops_start:
        return "PRE-SURVEILLANCE"
    else:
        return "SURVEILLANCE RETURN"

# --- Normalization + Validation ---
def validate_asset(asset):
    issues = []
    if not asset.get("field_time") or not asset.get("received_time"):
        issues.append("Missing one or both timestamps")
    return issues

def process_assets(assets):
    output = []
    deadfile = []
    audit_log = []

    for asset in assets:
        entry = {
            "id": asset.get("id"),
            "original_tags": asset.get("tags", []),
            "classification": None,
            "issues": [],
            "final_status": ""
        }

        try:
            field_time = datetime.fromisoformat(asset["field_time"])
            classification = classify_asset(field_time)
            entry["classification"] = classification
            entry["final_status"] = "OK"

        except Exception as e:
            entry["issues"].append("Invalid or missing field_time")
            entry["final_status"] = "REVIEW"
            deadfile.append(asset)

        timestamp_issues = validate_asset(asset)
        if timestamp_issues:
            entry["issues"].extend(timestamp_issues)
            entry["final_status"] = "REVIEW"
            deadfile.append(asset)

        output.append(entry)

    return {
        "classified": output,
        "deadfile_registry": deadfile
    }

# --- Example Usage ---
# assets = [
#     {
#         "id": "photo001",
#         "field_time": "2023-11-09T16:45:00",
#         "received_time": "2023-11-10T08:10:00",
#         "tags": ["vehicle", "plate"]
#     },
#     {
#         "id": "photo002",
#         "field_time": "2023-11-16T09:00:00",
#         "received_time": "2023-11-16T09:02:00",
#         "tags": ["subject", "contact"]
#     }
# ]

# result = process_assets(assets)
# print(json.dumps(result, indent=2))