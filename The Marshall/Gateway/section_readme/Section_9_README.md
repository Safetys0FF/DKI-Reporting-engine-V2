# Section 9 – Certification & Disclaimers Guide

## Overview
Section 9 records the investigator/agency certification and required disclaimers. It reuses branding, licensing, and contact information from the cover page and case profile to ensure legal statements remain consistent. Any additional disclaimers provided by the client or legal counsel are inserted here.

## Required Inputs & Extraction Workflow
- **Case Data:** `case_sources` supplies `assigned_investigator`, licenses, and agency data. Most values originate from Section 1 intake and the user profile wizard.
- **Previous Sections:** The renderer references `previous_sections['section_cp'].manifest['cover_profile']` to mirror the exact branding and contact details used earlier.
- **Toolkit Results:** Continuity and QA tools may add disclaimers (e.g., confidentiality, chain-of-custody notes); these appear in `case_sources['disclaimers']` if configured.

## Data Handling & Placeholder Policy
- `_val` helper ensures all fields print cleanly; missing data pulls from config defaults (e.g., `DKI Services LLC`).
- Signature block includes investigator name, title, license, agency name/license, mailing address, and current date.
- Optional logo path is reused for consistency.

## Cross-Reference & Validation
- Values should match Section 1 and the cover page. Any mismatch indicates the profile manager was updated mid-case; rerun Section CP if necessary.
- Section 5 document inventory and Section 6 billing references rely on these legal disclosures; ensure disclaimers cover confidentiality and evidentiary handling.

## Reporting Expectations
- Provide a first-person certification statement affirming truthfulness and compliance.
- Provide agency attestation confirming supervision by a licensed investigator.
- List standard disclaimers covering confidentiality, temporal accuracy, and privacy compliance. Append additional disclaimers when requested.

## Inter-Section & Gateway Flow
- Manifest stores the certification and disclaimer text so Final Assembly can reuse it in the disclosure appendix.
- Gateway ensures Section 9 approval occurs before final exports; missing values raise warnings in the conclusion (Section 7).

## Presentation Guidelines
- Fonts/titles follow standard styling; disclaimers are bullet-like paragraphs prefixed with dashes.
- Signature block uses emphasis style (italic) for clarity.
- Include current ISO date for audit traceability.

## Parsing Map Reference
The detailed parsing and validation map for this section is kept at F:\Report Engine\Gateway\parsing maps\SECTION_9_PARSING_MAP.md. Consult it for data sourcing, OpenAI trigger timing, and UI checklist expectations.

