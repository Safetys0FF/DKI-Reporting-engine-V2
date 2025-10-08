# Archive Manager System Summary

## Overview
The Archive Manager secures finalized narratives and packaged reports for Central Command. It provides immutable storage, retrieval tooling, and integration points for GUI exports, billing appendices, disclosure sets, and cloud synchronization.

## Core Responsibilities
- Persist narrative bundles under case-specific, human-readable directories (`final_narrative_{case_number}_{timestamp}.json`).
- Maintain checksum and audit logs for every archived asset to protect chain-of-custody.
- Offer retrieval APIs (`list_all_reports`, `get_case_report`) for GUI workflows, Mission Debrief, Analyst Deck validation, and automated final-assembly checks.
- Gate user-driven exports while preparing for future cloud targets (S3, Google Drive, Azure).

## Architecture Highlights
- **Read-Only Vault:** Enforces immutable storage semantics; write access limited to post-approval pipelines.
- **Audit Subsystem:** Automatically records SHA-256 hashes, version history, and append-only audit entries per archive event.
- **GUI Bridge:** Works with the Enhanced GUI to surface available archives, billing summaries, and disclosure sets while permitting controlled user downloads.
- **Cloud-Ready Layout:** Abstracted directory structure aligns with planned sync adapters for hybrid deployments and compliance retention policies.

## Recent Enhancements
- Integrated SectionBusAdapter payloads so archived report packages include billing analytics, disclosure selections, and media indexes alongside narratives.
- Added manifest snapshot references to match the new locker classification map, enabling the UI and Librarian to cross-check archived content before export.
- Improved export guardrails: audit log now captures disclosure selections and billing totals, ensuring ECC approval precedes transfer.

## Operational Status
- **Completed:** Immutable storage workflow, audit logging, GUI retrieval endpoints, bus integration, SectionBusAdapter metadata ingestion.
- **In Progress:** Automated cold-storage tiering and metadata diffing against live manifests.
- **Next:** Cloud sync adapters, retention policies, cross-region replication, and automated disclosure compliance attestations.

*Last updated: 2025-10-01*
