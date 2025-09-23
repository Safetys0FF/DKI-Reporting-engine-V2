# Section 7 Parsing Map (Conclusion)

## Purpose
Deliver a professional assessment of objectives, findings, and next steps using evidence-backed narratives and compliance disclaimers.

## Data Inputs
| Field | Origin | Notes |
|-------|--------|-------|
| objective_status | `case_data.objective_status`, `processed.manual_notes.objective_status` | Goal completion matrix referencing Section 1 objectives. |
| key_findings | `processed.manual_notes.findings` | Investigator findings mapped to evidence IDs. |
| recommendations | `case_data.recommendations`, `processed.manual_notes.recommendations` | Client guidance and follow-up actions. |
| risk_limitations | `processed.metadata.compliance_flags` | Constraints or cautions that survived earlier checks. |
| osint_summary | `toolkit_results.osint_verification` | Additional verification notes supporting conclusions. |

## Toolkit & AI Triggers
- OpenAI `evidence_support_audit` (pre_render) – verifies each finding cites evidence from Sections 3/8.
- OpenAI `tone_compliance` (pre_render) – ensures wording meets professional and legal standards.

## UI Checklist
- Approve findings and their evidence references.
- Confirm recommendations are actionable for the client.

## Dependencies
- Feeds: Sections 9 and FR reuse findings, limitations, and recommendations.
- Shares: `findings`, `limitations`, `recommendations`.
