# The Marshall (Gateway) System Summary

## Overview
The Marshall Gateway coordinates section execution, evidence routing, and report assembly for Central Command. It now operates as a first-class bus participant, brokering `section.needs`, `evidence.request`, and enrichment updates between the Evidence Locker, sections, Mission Debrief, and ECC.

## Core Responsibilities
- Subscribe to `evidence.new`, `evidence.updated`, `section.needs`, and `case.snapshot` to maintain live context for every case.
- Build section-aware payloads using the `section_parsing_dispatcher` and cached toolkit results before invoking renderers.
- Stage drafts and wait for enrichment confirmation before emitting `section.data.updated` and `gateway.section.complete`.
- Issue `evidence.request` responses when sections advertise needs and track manifest coverage for final assembly.

## Architectural Highlights
- **Section Broker:** Aggregates processed data, consults parsing maps, and queues requests back to the locker when additional artifacts are required.
- **Bus Layer:** `_attach_bus` registers handlers for evidence signals, section hints, case snapshots, and emits section lifecycle updates.
- **Draft Registry:** `_pending_section_outputs` stores draft content and parsing plans until enrichment arrives via `evidence.updated`.
- **Status Surface:** `get_gateway_status()` now reports bus connectivity, pending drafts, evidence catalog size, manifest snapshots, and case snapshots preview for the UI.

## Recent Enhancements
- Parsing dispatcher integration replaces bespoke `_prepare_section_payload` logic, ensuring each section receives curated context from the latest manifest, toolkit cache, and case data.
- Gateway now automatically issues `evidence.request` payloads when sections advertise needs, tagging requests with case metadata and priority.
- Section renderers publish enrichment before completion; Gateway replays that payload via the bus, guaranteeing locker and Mission Debrief consume the same enriched structure.
- Gateway status API powers the UI dashboard and Mission Debrief summaries with live stats (bus state, manifest previews, case snapshots).

## Operational Status
- **Completed:** Bus subscription + emitters, section broker, parsing dispatcher adoption, status telemetry, ECC alignment.
- **In Progress:** Auto-prioritization heuristics for simultaneous section needs, deeper media enrichment caching.
- **Next:** Adaptive scheduling based on manifest coverage, cross-case trend detection, extended analytics for Analyst Deck pipelines.

*Last updated: 2025-09-30*
