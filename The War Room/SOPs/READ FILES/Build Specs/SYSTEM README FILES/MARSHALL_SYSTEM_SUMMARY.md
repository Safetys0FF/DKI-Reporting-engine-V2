# The Marshall (Gateway) System Summary

## Overview
The Marshall Gateway coordinates section execution, evidence routing, and report assembly for Central Command. As a first-class bus participant, it now brokers classification handoffs from the GUI, `section.needs` advertisements from sections, and `evidence.updated` enrichment cycles between the Evidence Locker, SectionBusAdapter, Mission Debrief, and ECC.

## Core Responsibilities
- Subscribe to `evidence.new`, `evidence.updated`, `evidence.deliver`, `section.needs`, and `case.snapshot` to maintain live case context.
- Register classification handoffs, seed `_pending_section_outputs`, and dispatch curated payloads through the parsing dispatcher before invoking section renderers.
- Emit `section.data.updated` and `gateway.section.complete` once enrichment confirms, keeping Librarian and Analyst Deck aligned with the locker manifest.
- Manage evidence requests on behalf of sections, tracking manifest coverage and pending drafts for final assembly readiness.

## Architectural Highlights
- **Classification Router:** `register_evidence_locker_handoff` now normalizes GUI/locker payloads, updates the master evidence index, and issues targeted `section.needs` events (with filters/tags) for primary and related sections.
- **Pending Output Ledger:** `_pending_section_outputs` stores draft narratives, parsing plans, and delivery metadata so enrichment responses can finalize sections deterministically.
- **Status Surface:** `get_gateway_status()` reports manifest catalog size, pending handoffs, section states, SectionBusAdapter summaries, and analytics snapshots for the Enhanced GUI.
- **Bus Alignment:** Marionette handlers integrate with the SectionBusAdapter and Librarian to keep billing summaries, analytics, and disclosures synchronized across modules.

## Recent Enhancements
- Upgraded classification handoff flow to consume the GUI’s enriched metadata (tags, related sections, filters) and auto-issue `section.needs` plus queued `evidence.request` payloads.
- Ensured every `evidence.updated` reply finalizes the corresponding section and replays enrichment to the locker, eliminating stale narratives.
- Added awareness of SectionBusAdapter analytics, so Gateway status now reports billing insights, disclosure availability, and media coverage statistics.
- Hardened evidence catalog bookkeeping and manifest snapshots for Analyst Deck regression tests and ECC mission telemetry.

## Operational Status
- **Completed:** Classification router, section broker, parsing dispatcher adoption, status telemetry, ECC alignment, SectionBusAdapter integration.
- **In Progress:** Auto-prioritization for simultaneous section needs, deeper media enrichment caching.
- **Next:** Adaptive scheduling based on manifest coverage, cross-case trend detection, predictive analytics for Analyst Deck pipelines.

*Last updated: 2025-10-01*
