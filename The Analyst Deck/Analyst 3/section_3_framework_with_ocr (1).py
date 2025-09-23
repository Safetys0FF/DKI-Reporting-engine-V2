```python
# Example toggle switches for Section 3 (with 'surveillance' terminology)
LOGIC_SWITCHES = {
    "report_type": "surveillance",   # investigative | surveillance | hybrid
    "enable_billing": True,
    "reverse_continuity_check": True,
    "metadata_enforcement": True,
    "subcontractor_flag": False,
    "subject_seen": True,
    "overrun": False,
}

def render_section3(context, switches=LOGIC_SWITCHES):
    if switches["report_type"] == "investigative":
        return {
            "heading": "INVESTIGATION DETAILS",
            "billing": "suppressed",
            "content": context.get("investigative_findings", []),
        }

    elif switches["report_type"] == "surveillance":
        return {
            "heading": "SURVEILLANCE SUMMARY",
            "billing": "enabled" if switches["enable_billing"] else "suppressed",
            "logs": context.get("field_logs", []),
            "notes": build_notes(switches),
        }

    elif switches["report_type"] == "hybrid":
        return {
            "heading": "INVESTIGATION DETAILS",
            "special_note": "Due to the needs of both the client and the case filed, investigation was requested.",
            "investigative": context.get("investigative_findings", []),
            "field_block": {
                "label": "FIELD DEPLOYMENT (PHASE 2)",
                "logs": context.get("field_logs", []),
            },
            "billing": "hybrid",
        }

def build_notes(switches):
    notes = []
    if not switches["subject_seen"]:
        notes.append("No visual contact was made during the logged window.")
    if switches["overrun"]:
        notes.append("Subject remained active past authorized tracking window.")
    if switches["subcontractor_flag"]:
        notes.append("External field attachment received from subcontracted team.")
    return notes
```
