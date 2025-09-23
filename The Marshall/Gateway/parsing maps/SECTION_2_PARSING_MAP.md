# Section 2 Parsing Map (Pre-Surveillance / Case Preparation)

## Purpose
Document operational readiness: resources, logistics, legal prerequisites, and risk posture before surveillance or field activity begins.

## Data Inputs
| Field | Origin | Notes |
|-------|--------|-------|
| preparation_plan | `case_data.preparation_plan`, `processed.manual_notes.prep_plan` | Ordered checklist of tasks prior to field deployment. |
| resource_assignments | `case_data.assignments`, `processed.manual_notes.resource_assignments` | Investigator/subcontractor routing, shift coverage, contact tree. |
| legal_notices | `processed.forms.legal` | Court orders, client authorisations, special permits gathered from OCR. |
| equipment | `processed.metadata.equipment_ready` | Gear readiness flags (tracking devices, cameras, comms). |
| risk_register | `case_data.risk_matrix`, `processed.manual_notes.risk` | Operational hazards, mitigation steps, escalation triggers. |

## Toolkit & AI Triggers
- OpenAI `plan_consistency` (pre_render) – confirms logistics cover the objectives from Section 1.
- OpenAI `legal_compliance` (pre_render) – ensures required notices/permits are attached.

## UI Checklist
- Mark each preparation item as ready.
- Confirm legal notices and subcontractor credentials.

## Dependencies
- Feeds: Sections 3, 6, 9 consume readiness, resource, and legal data.
- Shares: `resource_assignments`, `legal_notices`, `risk_register`.
