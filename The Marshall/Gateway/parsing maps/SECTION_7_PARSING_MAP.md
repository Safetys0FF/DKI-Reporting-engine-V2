# Section 7 Parsing Map (Conclusion)

## Purpose
Synthesize the investigation—tying objectives, planning outcomes, surveillance findings, supporting documents, and billing posture into a client-facing narrative with next-step guidance.

## Data Inputs
| Conclusion Component                    | Source Path(s)                                                                                         | Notes |
|----------------------------------------|--------------------------------------------------------------------------------------------------------|-------|
| objective recap & status               | `case_data.investigation_goals`, `case_data.objective_status`, `section3.render_manifest.findings`    | Summarises goal completion and evidence references (Sections 2–4). |
| surveillance highlights                | `section4.manifest`, `section3.render_manifest`                                                        | Key observations, subject confirmations, deviations. |
| supporting documents leveraged         | `section5.document_summaries`, `case_data.supporting_documents_used`                                   | Mentions critical documents cited in findings. |
| billing posture                        | `section6.billing_totals`, `section6.variance_notes`, `case_data.retainers.remaining`                  | Provides client-facing cost summary and remaining balance. |
| recommendations / next steps           | `case_data.recommendations`, `processed.manual_notes.recommendations`, narrative assembler output      | Actionable guidance: continue surveillance, legal follow-up, close case. |
| limitations / cautions                 | `processed.metadata.compliance_flags`, `toolkit_results.risk_highlight`, `case_data.limitations`       | Mirrors disclosure tone (legal, ethical considerations). |
| empathy / closing statement            | `narrative_assembler.conclusion_template`, manual edits                                                | Ensures professional, compassionate tone aligned with template. |

## Toolkit & AI Triggers
- OpenAI `evidence_support_audit` (pre_render) – checks that each finding references Sections 3/4/5 artifacts.
- OpenAI `tone_compliance` (pre_render) – enforces professional legal tone.
- Narrative assembler conclusion template stitches Sections 2–6 summaries into final wording.

## UI Checklist
- Validate findings cite specific sessions or documents.
- Confirm recommendations align with client objectives and legal constraints.
- Ensure billing and retainer summary match Section 6 figures.

## Dependencies
- Section 9 certifications reuse the conclusion summary and limitations.
- Final report assembly uses this text in both DOCX export and disclosure statements.
- Librarian archive includes findings metadata for search.
