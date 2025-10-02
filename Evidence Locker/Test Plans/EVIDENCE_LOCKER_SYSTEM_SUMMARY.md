# Evidence Locker System Summary

## Overview
The Evidence Locker is the shared evidence orchestration hub for Central Command. It ingests raw artifacts, enriches metadata, tracks chain-of-custody, and keeps the gateway, sections, and Mission Debrief aligned through the `DKIReportBus`.

## Core Responsibilities
- Comprehensive ingestion, OCR, and enrichment for all uploaded evidence.
- Maintains the canonical evidence manifest and publishes `evidence.new` / `evidence.updated` signals.
- Responds to `section.needs` and `evidence.request` events to prioritize delivery for active sections.
- Records case snapshots and locker status for downstream audits and UI dashboards.

## Architectural Highlights
- **Processing Pipeline:** `scan_file`, `process_evidence_comprehensive`, and heavy-tool adapters populate the manifest with enriched artifacts.
- **Bus Extensions:** Custom mixins ensure locker modules register bus handlers for `evidence.*`, `section.needs`, `gateway.*`, and manifest queries.
- **Manifest Services:** `get_evidence_manifest`, `get_case_snapshots`, and locker state helpers back the UI and Mission Debrief summaries.
- **Integration Points:** Locker works with Gateway section brokers, ECC validation, Mission Debrief queueing, and Analyst Deck analytics via shared bus topics.

## Recent Enhancements
- Publishes enriched payloads before section completion, ensuring downstream consumers read the same data as the manifest.
- Tracks per-section usage, enrichment history, and timestamps for cross-section validation and final reconciliation.
- Emits locker status into `mission.status` snapshots so ECC and the UI can surface health indicators in real time.
- Improved request routing: locker now filters based on section hints, tags, and artifact types when answering `section.needs` advertisements.

## Operational Status
- **Completed:** Bus alignment, manifest APIs, enrichment feedback loop, ECC validation, and status logging.
- **In Progress:** Advanced classification heuristics and automated integrity scoring.
- **Next:** Machine-learning aided tagging, streaming ingestion, and cloud vault integration.

*Last updated: 2025-09-30*
