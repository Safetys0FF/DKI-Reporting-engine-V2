# Enhanced GUI System Summary

## Overview
The Enhanced GUI is the operator-facing console for Central Command. It now publishes section intent hints, surfaces live bus telemetry, orchestrates SectionBusAdapter controllers, and provides direct visibility into manifest coverage, billing analytics, disclosures, and gateway status without leaving the desktop interface.

## Key Responsibilities
- Drag-and-drop evidence intake with automatic locker registration, enrichment previews, and classification-aware bus publication.
- Dispatch `section.needs` hints (case metadata, tags, priorities) and seed SectionBusAdapter default requests so locker and gateway respond immediately.
- Display consolidated gateway diagnostics, locker manifest snapshots, section analytics, billing summaries, and latest `case.snapshot` telemetry.
- Facilitate Mission Debrief, Analyst Deck, and configuration workflows while preserving ECC-gated execution paths.

## UI + Bus Integration Highlights
- **Central Plugin Adapter:** Boots Warden, Gateway, Locker, Librarian, and SectionBusAdapter on the shared `DKIReportBus`; exposes `get_bus_snapshots()` plus enriched manifest context for UI panels.
- **Structured Section Builder:** `_build_structured_section_data` now merges locker manifest context, live `evidence.updated` enrichments, and SectionBusAdapter summaries before generating report drafts.
- **Analytics & Billing:** SectionBusAdapter feeds Section 6/7 data back into the GUI, presenting time, mileage, charge totals, tag coverage, and disclosure readiness.
- **Disclosure Library:** Preset disclosures are loaded from `disclosures_catalog.json`, letting operators append standardized language during final assembly.

## Recent Enhancements
- Added SectionBusAdapter orchestration: automatic bus handler registration, default evidence requests, and publication of analytics/billing/disclosure payloads.
- GUI structured data panes now show manifest-derived context (e.g., related sections, enrichment history) alongside uploaded artifacts.
- Billing dashboards highlight locker-derived totals and discrepancies, while analytics panels surface tag frequency and section coverage metrics.
- Disclosure picker integrated into the report workflow so Mission Debrief receives consistent legal verbiage.

## Operational Status
- **Completed:** Section hint publication, manifest context merge, analytics/billing/disclosure integration, central plugin + SectionBusAdapter wiring.
- **In Progress:** Inline manifest browser and per-section drill-down editors.
- **Next:** Guided remediation workflows, anomaly alerts, and direct narrative preview/editing inside the GUI.

*Last updated: 2025-10-01*
