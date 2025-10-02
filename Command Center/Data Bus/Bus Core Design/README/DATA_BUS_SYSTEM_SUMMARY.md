# Data Bus System Summary

## Overview
`DKIReportBus` is the shared signal fabric for Central Command. It now exposes manifest/status APIs, brokers enrichment flows, and synchronizes UI dashboards, Gateway operations, Mission Debrief, and Analyst Deck pipelines.

## Core Capabilities
- Thread-safe publish/subscribe with structured handler registration and default stubs.
- Evidence manifest, latest status, and case snapshot services powering UI widgets and automation scripts.
- Convenience wrappers (`emit`, `register_handler`, `register_default_handlers`) plus helper methods for subsystems.
- Logging and diagnostics for signal delivery, handler failures, and default handler usage.

## Recent Enhancements
- Added `get_evidence_manifest()`, `get_latest_status()`, and `get_case_snapshots()` so consumers can retrieve locker state without direct coupling.
- Expanded default handler map to include enrichment, request, and mission status topics for safer bootstrapping.
- Gateway `_attach_bus()` and ECC bus helpers rely on new manifest services to report health and status.
- Enhanced logging provides debug insights for manifest/state tracking and reset logic.

## Subsystem Integration Snapshot
- **Evidence Locker:** Publishes manifest updates, responds to requests, records snapshots.
- **Gateway:** Subscribes to evidence signals, issues section requests, emits section lifecycle events.
- **Mission Debrief / Librarian:** Consumes section updates and completions, re-emits narrative and debrief events.
- **ECC / Warden:** Listens for section lifecycle events, emits `mission.status`, and surfaces telemetry.
- **Enhanced GUI:** Calls `get_gateway_status()` and `get_bus_snapshots()` via the central plugin.

## Operational Status
- **Completed:** Manifest/status APIs, default handler extensions, logging improvements, broad subsystem adoption.
- **In Progress:** Formal schema docs and replay tooling for tests.
- **Next:** Streaming transport abstraction and persistent signal journaling.

*Last updated: 2025-09-30*
