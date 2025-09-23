# CORE ENGINE — Fallback Logic Index (Read-Only)

Purpose
- Define the reference documents used to understand behaviors, rules, structure, and performance of the core engine.
- These are consulted before making any core-engine changes to ensure edits align with intended logic.

Precedence
- Authoritative configs: the 12 numbered core files (e.g., `1. Section CP.txt`, ..., `12. Final Assembly.txt`).
- Fallback references: the documents listed below. If conflicts arise, they are flagged; configs are adjusted to reflect the intended behavior derived from these references.

Section Mapping
- Section 1 (section_1)
  - `Section 1 - Investigation Objectives (updated).txt:1`
  - `Section 1 - Investigation Objectives with switches.txt:1`

- Section 2 (section_2)
  - `Section 2 - Presurveillance Logic.txt:1`
  - `section 2 - pres-urveillance.txt:1`

- Section 3 (section_3)
  - `section 3 - data logs.txt:1`
  - `Section 3 - Surveillance Reports - Dialy Logs.txt:1`

- Section 4 (section_4)
  - `Section 4 - Review of Surveillance Sessions.txt:1`
  - `Section 4 - review of surveillance.txt:1`

- Section 5 (section_5)
  - `Section 5 - review of documents Logic Overview.txt:1`
  - `Section 5 - Review of Supporting Docs.txt:1`

- Section 6 (section_6)
  - `section 6 - BILLING SUMMARY.txt:1`

Workflow Usage
- Cross-check naming, handoffs, and label text in `logic_switches` against these references.
- Validate emitter payload semantics (`origin`/`from`) and section roles.
- Use as the basis for standard terminology across sections.
- When recommendations or changes are proposed, cite the relevant fallback files in the read-only records.

Next Steps (upon request)
- Extract per-section "Logic Profiles" summarizing rules, constraints, and expected outputs to validate configs automatically.
- Add pre-commit validation to compare config labels vs. fallback profiles.

Timestamp: 2025-09-14
Author: Core Functions Owner (AI)

