# SECTION 3 – SURVEILLANCE REPORTS / DAILY LOGS

case_mode = "field"  # options: "field", "investigative", "hybrid", "none"

if case_mode == "none":
    report_body = """
SECTION 3 – SURVEILLANCE REPORTS / DAILY LOGS

No surveillance was performed or required.
"""
elif case_mode == "investigative":
    report_body = """
SECTION 3 – INVESTIGATIVE FINDINGS

Date Block:
[Insert Date of Finding(s)]

Time Logs:
[Insert Time-based Descriptions of Findings]

Field Agent:
[Investigator Name]

Location Context:
[Location(s) of Investigative Findings]

Activities Observed:
[Details of findings, e.g. data gathered, interviews conducted]

Narrative Notes:
[Internal remarks or status of findings]

Voice Memos:
1. Voice Memo Example: Details about subject. (Language: English) [Duration: 00:30]
"""
elif case_mode == "hybrid":
    report_body = """
SECTION 3 – INVESTIGATION DETAILS

[INVESTIGATIVE SEGMENT]

Date Block:
[Insert Date(s) of Findings]

Time Logs:
[Insert Descriptions of Timed Findings]

Field Agent:
[Lead Investigator Name]

Location Context:
[Location(s) of Investigation]

Activities Observed:
[Summary of non-field activity]

Narrative Notes:
[Notes from Investigative Segment]

Voice Memos:
1. Investigative Memo

FIELD DEPLOYMENT (PHASE 2)

Date Block:
[Insert Date(s) of Surveillance]

Time Logs:
[Surveillance Actions Chronologically Listed]

Field Agent:
[Surveillance Agent]

Location Context:
[Observed Locations]

Activities Observed:
[What was seen]

Photos Captured:
Images: [X] | Videos: [Y]

Vehicles Logged:
[List of Vehicle Details]

Weather Conditions:
[Weather on Field Day(s)]

Narrative Notes:
[Any field notes]

Voice Memos:
1. Field Memo
"""
else:  # default to 'field'
    report_body = """
SECTION 3 – SURVEILLANCE REPORTS / DAILY LOGS

Date Block:
[Insert Date of Surveillance]

Time Logs:
[Chronological Logs Here]

Field Agent:
[Agent Name]

Location Context:
[Observed Locations]

Activities Observed:
[Actions Taken by Subject]

Photos Captured:
Images: [X] | Videos: [Y]

Vehicles Logged:
[List of Vehicle(s)]

Weather Conditions:
[Weather Description]

Narrative Notes:
[Surveillance Summary]

Voice Memos:
1. Field Memo: Subject tracked. [Duration: 00:47]
"""

print(report_body)
