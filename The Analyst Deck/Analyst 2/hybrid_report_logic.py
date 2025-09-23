from datetime import datetime

# === Input: contract history must be a list of dicts ===
# Example contract_history:
# [
#   {"type": "Investigative", "signed_date": datetime(2025, 5, 1)},
#   {"type": "Surveillance", "signed_date": datetime(2025, 5, 21)}
# ]

def get_report_config(contract_history):
    """
    Validates contract order, assigns report type,
    returns rendering + logic config for Section 2.
    """

    def determine_type(history):
        contracts = sorted(history, key=lambda x: x['signed_date'])
        has_investigative = any(c['type'] == "Investigative" for c in contracts)
        has_surveillance = any(c['type'] == "Surveillance" for c in contracts)

        if has_investigative and has_surveillance:
            for i, c in enumerate(contracts):
                if c['type'] == "Surveillance" and any(prev['type'] == "Investigative" for prev in contracts[:i]):
                    return "Hybrid", True  # Valid hybrid trigger
            return "Surveillance", False
        elif has_surveillance:
            return "Surveillance", True
        elif has_investigative:
            return "Investigative", True
        return "Unknown", False

    report_type, contract_order_validated = determine_type(contract_history)

    hybrid_render_order = [
        "2A_case_summary",
        "2B_subject_information",
        "2C_habits_and_POIs",
        "2B_investigative_data",
        "2D_visual_assets",
        "2E_final_planning"
    ]

    report_type_switch = {
        "Investigative": {
            "label": "SECTION 2 – INVESTIGATIVE REQUIREMENTS",
            "billing": "Flat",
            "clause": "no_surveillance",
            "modules": {
                "active": ["investigative_data"],
                "inactive": ["surveillance_logs", "route_plan", "vehicle_id", "photos", "mileage"]
            },
            "effects": {
                "hide": ["2C", "2D"],
                "tag": "Investigation Only"
            }
        },

        "Surveillance": {
            "label": "SECTION 2 – PRE-SURVEILLANCE SUMMARY",
            "billing": "Hourly",
            "clause": "field_hours",
            "modules": {
                "active": ["surveillance_logs", "vehicle_id", "poi_analysis", "photos", "mileage"],
                "inactive": ["investigative_data", "court_lookups"]
            },
            "effects": {
                "render_all": True,
                "tag": "Surveillance Ready"
            },
            "disclaimer": (
                "The following observations were made during physical surveillance activities "
                "conducted by licensed investigators operating within jurisdictional and contractual limits. "
                "This report contains no assumptions regarding subject intent or legal conclusions. "
                "If the case is prepped and not finished: an investigator has been assigned to this case as requested by the client. "
                "That investigator is operating by their own licensing and legal ability under state statutes. "
                "The investigator has been allocated 15 hours of field operation time for this case."
            )
        },

        "Hybrid": {
            "label": "SECTION 2 – HYBRID PREPARATION SUMMARY",
            "billing": "Hybrid",
            "clause": "mixed",
            "modules": {
                "active": ["investigative_data", "surveillance_logs", "vehicle_id", "poi_analysis", "photos", "mileage"],
                "inactive": []
            },
            "effects": {
                "forced_render_order": hybrid_render_order,
                "contract_order_required": True,
                "tag": "Full Stack"
            },
            "disclaimer": (
                "This report includes a combination of documented investigative research and field surveillance observations. "
                "All findings have been timestamped, source-anchored, and reviewed for continuity against the client intake. "
                "No part of this report makes conclusions beyond factual reporting or visual confirmation. "
                "If the case is prepped and not finished: an investigator has been assigned to this case as requested by the client. "
                "That investigator is operating by their own licensing and legal ability under state statutes. "
                "The investigator has been allocated 15 hours of field operation time for this case."
            )
        }
    }

    if report_type == "Hybrid" and not contract_order_validated:
        report_type = "Surveillance"
        log_msg = "Hybrid denied: Surveillance contract not signed after Investigative."
    else:
        log_msg = f"{report_type} mode selected."

    return {
        "report_type": report_type,
        "config": report_type_switch[report_type],
        "log": log_msg
    }

# === Example Usage ===
if __name__ == "__main__":
    contract_history = [
        {"type": "Investigative", "signed_date": datetime(2025, 5, 1)},
        {"type": "Surveillance", "signed_date": datetime(2025, 5, 21)}
    ]

    result = get_report_config(contract_history)
    print(result["log"])
    print(result["config"])
