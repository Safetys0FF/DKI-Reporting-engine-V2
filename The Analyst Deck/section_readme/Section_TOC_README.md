# Section TOC – Table of Contents Operations Guide

## Overview
The Table of Contents offers a live index of the report structure while sections are still under review. It reads the active report type from the gateway and lists each section name in sequence with estimated pagination. Although final exports recompute page numbers, this early TOC is essential for reviewer navigation and for validating that the proper sections have been activated.

## Required Inputs & Extraction Workflow
- Takes `section_payload['report_sections']` from the gateway controller. This list comes directly from `GatewayController.report_types[report_type]['sections']`, ensuring the UI and engine reference the same canonical order.
- `previous_sections` contains any rendered sections; their `content` length feeds the page estimates. Content originates from the combination of OCR text (via `DocumentProcessor`), AI summaries (`MasterToolKitEngine`), and manual edits captured in `section_outputs`.
- No additional OCR or voice processing occurs here, but accurate character counts depend on upstream sections properly materializing textual render trees.

## Data Handling & Sorting
- The renderer iterates section IDs in declared order; it never re-sorts alphabetically. Missing sections remain listed but flagged as unavailable (`entries[n]['available'] = False`).
- Page estimates default to 1 when no content exists, preventing zero-page gaps.
- Rendering begins on page 3 (cover + TOC occupy first two pages) to keep early navigation consistent with exported documents.

## Cross-Reference & Validation
- The TOC manifest captures `entries` with computed pages; the gateway can audit this list to ensure required sections are on deck before proceeding to final assembly.
- If Section 1 toggles report type mid-case, `_ensure_gateway_case_initialized()` refreshes the section list; the TOC renderer will reflect that on the next run.

## Reporting Expectations
- Display each section name with dotted leader formatting (`Name ... Page`).
- Update automatically as soon as a section completes so reviewers can jump to the correct content.

## Inter-Section & Gateway Flow
- Output: `{ "render_tree": [...], "manifest": { 'entries': [...] }, "handoff": 'gateway' }`.
- Gateway stores manifest for downstream exporters; Final Assembly uses it to annotate working DOCX/PDF files when constructing hyperlinks.
- Because the UI now synchronizes report type selection with the gateway, the TOC always mirrors the true case layout.

## Presentation Guidelines
- Keep headings uppercase, Times New Roman.
- When no sections are available, the TOC still renders the title and explicitly notes the absence to avoid silent failures.
- No media, voice, or graphics appear here; it is purely typographical.
