# Evidence Locker System Summary

## Overview
The Evidence Locker is the shared evidence orchestration hub for Central Command. It ingests raw artifacts, enriches metadata, tracks chain-of-custody, and keeps the gateway, section controllers, and Mission Debrief aligned through the `DKIReportBus`.

## Core Responsibilities
- Comprehensive ingestion, OCR, enrichment, and classification for all uploaded evidence.
- Maintain the canonical manifest and publish `evidence.new`, `evidence.annotated`, and `evidence.updated` signals used by Gateway, sections, and Librarian.
- Respond to `section.needs` / `evidence.request` traffic with deduplicated `evidence.deliver` payloads tailored to section filters (tags, evidence type, priority).
- Broadcast locker health, manifest counts, and case snapshots to support ECC dashboards, Analyst Deck analytics, and automated QA hooks.

## Architectural Highlights
- **Section-Aware Classification:** `classify_evidence` now maps intake, contracts, billing artifacts, geo media, and surveillance documents directly to their target sections and publishes related-section metadata for downstream reuse.
- **Bus Extensions:** Evidence Locker bus mixins register handlers for `evidence.request`, `section.needs`, and manifest queries while enforcing a delivery dedupe window to avoid flooding sections with identical payloads.
- **Manifest & Context Services:** `get_evidence_manifest`, `get_case_snapshots`, and manifest helper APIs provide consolidated context to SectionBusAdapter, the Enhanced GUI, and Mission Debrief templates.
- **Integrity Logging:** Processing history, enrichment timestamps, and section usage are recorded for each artifact, enabling cross-section validation and billing reconciliation.

## Recent Enhancements
- Added classification heuristics that align with the new section data contract (Sections 1–8, plus DP disclosures), including tag propagation and related-section hints.
- Implemented per-recipient deduplication and richer filter handling when answering `evidence.request`, reducing bus noise while respecting priority overrides.
- Published enrichment histories (`evidence.updated`) before section completion, guaranteeing Gateway, Librarian, and Archive Manager operate on identical data snapshots.
- Surfaced manifest context and locker status through the SectionBusAdapter so GUI billing analytics and disclosure workflows stay synchronized with the locker’s source of truth.

## Operational Status
- **Completed:** Section-aware classification, manifest APIs, enrichment feedback loop, delivery dedupe, ECC validation, status logging.
- **In Progress:** Automated integrity scoring and anomaly detection across manifest histories.
- **Next:** Streaming ingestion, ML-assisted tagging, and long-term vault integrations.

*Last updated: 2025-10-01*
