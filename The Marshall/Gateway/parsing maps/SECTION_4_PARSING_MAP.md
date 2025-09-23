# Section 4 Parsing Map (Review of Surveillance Sessions)

## Purpose
Summarise surveillance sessions with conditions, tactics, performance notes, and continuity metrics derived from Section 3 and toolkit analytics.

## Data Inputs
| Field | Origin | Notes |
|-------|--------|-------|
| sessions | `toolkit_results.continuity_check.sessions` | Toolkit-derived session slices with timing and variance data. |
| environmental | `processed.metadata.environmental` | Weather/locale context impacting surveillance quality. |
| tactics | `processed.manual_notes.tactics` | Operational approaches, hand-offs, ingress/egress notes. |
| issues | `processed.manual_notes.issues` | Session-level anomalies, equipment faults, lessons learned. |

## Toolkit & AI Triggers
- OpenAI `session_summary` (post_compile) – drafts session narratives referencing evidence.
- OpenAI `condition_validation` (post_compile) – cross-checks environmental statements.

## UI Checklist
- Adjust session boundaries where needed.
- Confirm documented issues and lessons learned.

## Dependencies
- Feeds: Section 7 relies on session outcomes for findings.
- Shares: `session_metrics`, `issues`.
