# Technical Blueprint - DKI Command Ecosystem

## Document Summary
- Author: Architecture Guild, Central Command
- Version: 1.0
- Last Updated: 2025-09-25

## 1. System Context
The DKI ecosystem is a modular Python platform that orchestrates evidence ingestion, section analysis, and report finalization. A signal-based Data Bus coordinates independent services: the Warden (ecosystem control), the Marshall (gateway and evidence manager), the Evidence Locker (classification and indexing), the Analyst Deck (section processors), and Mission Debrief (publication and archival). Operator tooling resides in the War Room, while automation and monitoring live in the Ops Center.

## 2. Core Components
- **Data Bus (Command Center/Data Bus)**: Provides the `DKIReportBus`, signal registry, plugin lifecycle, API manager, PDF manager, and case library manager. Offers publish/subscribe semantics with payload validation and event logging.
- **The Warden**: Hosts `warden_main.py`, `ecosystem_controller.py`, and `gateway_controller.py`. Manages section lifecycle, bootstraps modules, enforces ECC permissions, and mediates signal flow between components.
- **The Marshall**: Implements `evidence_manager.py` plus gateway renderers and processing engines. Handles evidence ingestion, validation, section orchestration, and media pipelines.
- **Evidence Locker**: Maintains evidence index, classifier, class builder, case manifests, and static data flows. Provides chain-of-custody integrity and section-aware routing.
- **Analyst Deck**: Contains section frameworks (`section_X_framework.py`), renderers, toolkits, and tests for sections 1-9, CP, DP, TOC. Defines standard stage pipeline (Acquire, Extract, Normalize, Validate, Publish).
- **Mission Debrief**: Houses `mission_debrief_manager.py`, `narrative_assembler.py`, archive manager, and professional tooling adapters (printing, watermark, digital signature, OSINT). Produces final deliverables stored in Library.
- **War Room**: GUI processors, drag-and-drop integrations, dependency manifests (`requirements.txt`), and support for advanced OCR/video pipelines.
- **Ops Center**: Automation scripts, stress tests, log rotation, regression harnesses.

## 3. Data Flow Overview
1. **Ingestion**: Files enter via Marshall gateway (CLI/UI). Metadata captured and hashed.
2. **Classification**: Evidence Locker analyzes file types, metadata, and heuristics; updates master index and assigns sections.
3. **Signal Dispatch**: Data Bus publishes `evidence_ready` signals consumed by Warden and section frameworks.
4. **Section Processing**: Analyst Deck modules process assigned evidence, produce structured payloads, and issue `section_ready` or `revision_required` signals.
5. **Orchestration**: Warden coordinates dependencies, ensures ECC permissions, and manages revisions (10-9) until sections confirm `10-4`.
6. **Narrative Assembly**: Mission Debrief pulls curated data, assembles narratives, applies professional tooling, and emits `10-99` when archive is complete.
7. **Archival**: Library stores deliverables with hash manifests and audit logs; Ops Center verifies nightly.

## 4. Sequence Snapshots
- **Batch Intake**
  1. Operator issues `marshall.ingest_batch`.
  2. Marshall calls ECC for permission, receives approval, processes each file.
  3. Evidence Locker classifies files and updates index.
  4. Bus emits `evidence_classified` signals; sections subscribe per contract.
- **Revision Loop**
  1. Analyst flags anomaly, Warden signals `10-9`.
  2. Section framework rewinds to last stable checkpoint, reruns toolkit.
  3. Upon success, section publishes update and signals `10-4`.
  4. Warden resumes downstream orchestration.
- **Publication**
  1. Warden confirms all sections complete; triggers Mission Debrief.
  2. Mission Debrief orchestrator loads templates, runs toolkit adapters, and generates deliverables.
  3. Archive manager writes outputs, calculates hashes, stores audit entries.
  4. Bus emits `mission_complete` for Ops Center automation.

## 5. Deployment Topology
- Primary deployment is a single host or small cluster running Python services launched via CLI or service wrapper.
- Recommended layout:
  - **Instance 1**: Data Bus and Warden (low CPU, high I/O).
  - **Instance 2**: Marshall and Evidence Locker (CPU intensive, access to GPU if available for OCR/CV).
  - **Instance 3**: Mission Debrief (CPU and disk heavy) with access to professional tool binaries.
  - **Operator Workstations**: War Room GUI clients connecting to bus endpoints.
- Services communicate over process boundaries (shared memory or IPC) or via network sockets when distributed; ensure TLS if remote.

## 6. Interface Contracts
- **Signals**: Standard event names (`evidence_ready`, `section_ready`, `revision_required`, `mission_complete`). Payloads include `case_id`, `section_id`, `evidence_id`, status, and timestamp.
- **Plugin API**: Plugins implement manifest metadata, lifecycle hooks (`on_install`, `on_enable`, `on_signal`), and version compatibility. Licenses stored under `Command Center/Plug-ins/licenses`.
- **Case Library API**: Provides CRUD for case metadata, export pipelines, and case-level configuration for sections.
- **Professional Tools API**: Mission Debrief uses adapter interfaces for printing, signatures, watermarks, and OSINT enrichment with fallback to simulated responses when offline.

## 7. Security and Compliance
- ECC permission checks gate every critical operation (call-out, confirm, send, accept, complete handoff).
- Evidence chain-of-custody maintained via SHA-256 hashes, logs, and audit manifests.
- API keys encrypted at rest. Use environment variables or secrets vault for runtime access.
- Logging is immutable and stored per module. Rotation jobs push logs to secure archive nightly.
- Access control enforced at application layer; integrate with OS-level permissions for shared storage.

## 8. Observability
- **Logging**: Each module logs to `Logs/` directories with JSON or structured text entries containing signal IDs and trace context.
- **Metrics**: Ops Center scripts compute mission duration, queue length, throughput per section, and error rates.
- **Tracing**: Signal IDs propagate through payloads; adopt consistent `request_id` generation for cross-module correlation.
- **Alarms**: Configure monitors for queue backlog thresholds, plugin registration failures, and Mission Debrief timeouts.

## 9. Scalability and Resilience
- Data Bus supports asynchronous handler pools and batching to handle surge traffic.
- Evidence Locker processing can be parallelized; design to shard by case or evidence batches.
- Mission Debrief pipeline supports caching and replay to recover from downstream errors.
- Plugins execute in sandboxed contexts; failure isolates to offending handler without halting bus.
- Warm standby recommended for Mission Debrief to avoid single point of failure.

## 10. Implementation Guidelines
- Maintain strict layering: Warden mediates cross-module operations; avoid direct coupling between sections and Debrief.
- Keep frameworks and toolkits pure; heavy dependencies load lazily and advertise availability via signals.
- Provide configuration via YAML or environment variables and store defaults in `Command Center/Config` (to be finalized).
- Enforce tests for every new section or plugin; integrate with `make test` target.
- Document new signals and payload schemas in `Command Center/Docs/signals.md` (planned addition).

## 11. Roadmap Alignment
- Short term: finalize automation around log verification, expand Ops Center dashboards, introduce plugin staging harness.
- Mid term: add AI-assisted classification optional module, implement distributed bus endpoints, containerize mission stack.
- Long term: deliver cloud sync adapters, mobile operator console, and predictive scaling tied to mission backlog analytics.

## 12. References
- `read_me_file/*.md` - Subsystem summaries.
- `SOP.md` - Operational procedures.
- `PRD.md` - Product objectives.
- `Makefile` - Build, run, and test automation.
