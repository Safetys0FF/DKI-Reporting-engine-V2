# cochran_match_tool.py
# DKI Identity Match Engine v1.0 — Based on COCHRAN THEORY

import json
import re
from datetime import datetime
from difflib import SequenceMatcher

# --- Normalization Helpers ---
def clean_name(name):
    return re.sub(r'[^a-zA-Z ]', '', name).strip().lower()

def normalize_address(addr):
    return re.sub(r'[^a-zA-Z0-9 ]', '', addr).strip().lower()

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio() > 0.92

# --- Core Verification ---
def verify_identity(subject, candidate):
    reasons = []

    # Name Check
    subj_name = clean_name(subject.get("full_name", ""))
    cand_name = clean_name(candidate.get("full_name", ""))
    name_match = similar(subj_name, cand_name)
    if not name_match:
        reasons.append("Name mismatch")

    # DOB Check
    dob_match = subject.get("dob") == candidate.get("dob")
    if not dob_match:
        reasons.append("DOB mismatch")

    # Address Overlap (60+ days)
    subj_addr = normalize_address(subject.get("address", ""))
    cand_addr = normalize_address(candidate.get("address", ""))
    days_overlap = candidate.get("address_days_overlap", 0)
    addr_match = subj_addr == cand_addr and days_overlap >= 60
    if not addr_match:
        reasons.append("Address mismatch or overlap < 60 days")

    # Source Check
    source_valid = candidate.get("source") in ["court", "gov", "dmv"]
    if not source_valid:
        reasons.append("Untrusted source")

    # Final Status Logic
    if name_match and dob_match and addr_match and source_valid:
        status = "ACCEPT"
    elif name_match and dob_match and addr_match:
        status = "REVIEW"
    else:
        status = "REJECT"

    return {
        "status": status,
        "name_match": name_match,
        "dob_match": dob_match,
        "address_match": addr_match,
        "source_valid": source_valid,
        "reasoning": reasons
    }

# --- Example Input ---
# subject = {
#     "full_name": "Robert Cochran",
#     "dob": "1986-11-25",
#     "address": "123 Justice Ln"
# }

# candidate = {
#     "full_name": "Robert A. Cochran",
#     "dob": "1986-11-25",
#     "address": "123 Justice Lane",
#     "address_days_overlap": 85,
#     "source": "court"
# }

# result = verify_identity(subject, candidate)
# print(json.dumps(result, indent=2))