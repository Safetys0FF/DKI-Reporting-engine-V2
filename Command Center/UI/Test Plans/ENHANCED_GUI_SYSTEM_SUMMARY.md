# Enhanced GUI System Summary

## Overview
The Enhanced GUI is the operator-facing console for Central Command. It now publishes section intent hints, surfaces live bus telemetry, and provides direct visibility into manifest coverage, case snapshots, and gateway status without leaving the desktop interface.

## Key Responsibilities
- Drag-and-drop evidence intake with automatic locker registration, enrichment preview, and bus publication.
- Dispatch `section.needs` hints (case metadata, tags, priorities) when evidence is dropped so the locker and gateway can respond immediately.
- Display consolidated gateway diagnostics, evidence manifest previews, latest bus status, and case snapshot excerpts.
- Expose tooling for Mission Debrief, Analyst Deck, and configuration while maintaining ECC-gated workflows.

## UI + Bus Integration Highlights
- **Central Plugin Adapter:** Instantiates Warden, Gateway, Locker, and Mission Debrief with the shared `DKIReportBus`; new `get_bus_snapshots()` powers dashboards.
- **File Drop Pipeline:** After storing files, the UI calls `_publish_section_need()` with section hints, evidence IDs, and classification context.
- **Gateway Status Panel:** Uses `get_gateway_status()` plus `get_bus_snapshots()` to render manifest counts, preview entries, latest status payloads, and case snapshots.
- **Audit + Telemetry:** Updated logging records bus publications and locker registrations for QA and compliance.

## Recent Enhancements
- Added `_publish_section_need()` helper and bus calls directly in the evidence drop workflow.
- Gateway status refresh now summarizes bus connectivity, pending requests, manifest preview, and case snapshot counts before dumping full JSON.
- Central plugin exposes manifest/status/case previews used by the UI, CLI tooling, and automated tests.
- Bus-driven health indicators align the GUI with Warden and Mission Debrief dashboards.

## Operational Status
- **Completed:** Section hint publication, gateway status dashboard, manifest snapshot view, central plugin bus APIs.
- **In Progress:** Inline locker manifest browser and section-specific drill-downs.
- **Next:** Guided remediation workflows, anomaly alerts, and direct narrative review integration.

*Last updated: 2025-09-30*
