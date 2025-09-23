# Section DP – Disclosure & Authenticity Page Guide

## Overview
Section DP produces the disclosure/authenticity page that accompanies the finished report package. It restates the investigator’s attestation, legal disclosures, and confidentiality notices in a dedicated section that precedes final assembly. The gateway treats Section DP as a full participant in the callbox workflow so approvals, revisions, and freezes can happen before final packaging.

## Required Inputs & Extraction Workflow
- **Cover Profile Reuse:** Pull branding, logos, investigator signatures, and mailing addresses from the cover page manifest (`previous_sections['section_cp'].manifest['cover_profile']`).
- **Certification Text:** Reuse or adapt language from Section 9 to ensure consistency; the disclosure page typically mirrors the same authenticity statement.
- **Toolkit Context:** When `MasterToolKitEngine` runs, it injects unified results and flags (e.g., outstanding QA issues) that must appear in the disclosure summary.
- **System Metadata:** `System Lock Protocol` provides the finalized timestamp; overrides require justification and are logged for audit.

## Data Handling & Structure
- Layout is predefined: logo (optional) → authenticity statement → investigator signature block → disclosure text. Fonts/spacing align with professional legal documents (Times New Roman, 9pt).
- Disclosure paragraphs include confidentiality, liability, and legal disclaimers. Additional text can be sourced from repository templates if required.
- Gateway YAML config defines signal handling so Section DP emits `section_completed` and `ready_for_next` payloads, enabling the approval loop.

## Cross-Reference & Validation
- Section DP must reference the same finalized date as the report lock, ensuring timestamps match final exports.
- Disclosures should align with document inventory in Section 5 and certifications in Section 9 to avoid conflicting statements.
- Gateway flags (from toolkit) surface here so reviewers know whether unresolved issues exist before final assembly.

## Reporting Expectations
- Present clear authenticity language affirming the honesty of the report.
- List disclosure paragraphs covering document handling, legal boundaries, and recommendations to seek counsel.
- Include signature graphics when available; otherwise provide textual signatures.

## Inter-Section & Gateway Flow
- Section DP participates fully in callbox signals (10-4 approval, 10-9 revision, 10-10 halt). Reviewers can request edits or freeze the gateway from this stage.
- Upon approval, Section DP forwards its prepared report chunk to Section FR (Final Assembly) for inclusion in the export package.
- Feedback loop captures user suggestions and routes them back into the section payload when revisions are requested.

## Presentation Guidelines
- Keep formatting tight and legible; use justified paragraphs with box borders as defined in the layout spec.
- Signature and logo placements should mirror the cover page to maintain brand consistency.
- Ensure disclosure text addresses privacy, legal non-advice, document handling responsibilities, and change notice.
