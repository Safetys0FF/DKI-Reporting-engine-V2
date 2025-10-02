# DKI Command Ecosystem README

## Overview
The Central Command workspace hosts the Central Command investigation ecosystem, the successor to the legacy DKI report engine. The system is a modular Python ecosystem built around the Data Bus signal architecture, the Warden orchestration layer, the Marshall gateway, the Evidence Locker classification hub, the Analyst Deck section processors, and the Mission Debrief publication stack. This README orients operators, engineers, and analysts so they can bring the platform online, monitor the mission lifecycle, and extend components safely.

## Quick Start
1. Install Python 3.11 (or the version specified in team standards) and ensure `python` resolves on your PATH.
2. Clone or sync the repository into a writeable workspace such as `F:\The Central Command`.
3. From the repository root, run `make -f Command Center/read_me_file/Makefile install` to create a virtual environment and pull core dependencies (`The War Room/Processors/requirements.txt`).
4. Launch the bus runtime with `make -f Command Center/read_me_file/Makefile run-bus` once per host session. This primes the signal hub.
5. Use `make -f Command Center/read_me_file/Makefile run-warden`, `make -f Command Center/read_me_file/Makefile run-marshall`, and `make -f Command Center/read_me_file/Makefile run-debrief` to bring orchestration, gateway, and report assembly layers online in separate terminals.
6. Trigger section processors or UI workflows through the Analyst Deck or War Room interfaces as needed.

## Directory Map (high level)
- `Command Center/Data Bus` - Signal hub, plugin ecosystem, and case library managers.
- `Command Center/Mission Debrief` - Report finalization, library archives, and professional tooling adapters.
- `Command Center/Plug-ins` - Managed extensions packaged for bus discovery.
- `Command Center/Start Menu` - Bootstrap artefacts that tie UI entry points to command flows.
- `Command Center/UI` - Operator interface controllers and presentation assets.
- `The Warden` - Ecosystem controller, gateway coordinator, and lifecycle state enforcement.
- `The Marshall` - Evidence manager, section orchestration gateway, and media processing engines.
- `Evidence Locker` - Classification, indexing, and case manifest builders (see `Command Center/Evidence Locker`).
- `The Analyst Deck` - Section frameworks, renderers, and toolkits for 1-9 plus CP, DP, TOC.
- `The War Room` - Processor bundles, GUI launchers, and dependency manifests for analyst tooling.
- `Ops Center` - Automation harnesses, stress scenarios, and monitoring scripts.
- `Evidence Locker/System`, `Mission Debrief/System`, etc. - Legacy dumps retained for reference.

## Primary Workflows
- **Case Intake**: Evidence arrives through the Marshall gateway, is classified by the Evidence Locker, and is registered with the bus for downstream handlers.
- **Section Processing**: Analyst Deck frameworks consume bus signals, run section toolkits, and publish structured payloads back to the Warden and Marshall.
- **Report Finalization**: Mission Debrief assembles narratives, applies professional tooling (signatures, watermarks, OSINT enrichments), and archives outputs in the Library.
- **Plugin Lifecycle**: The Data Bus plugin manager scans `Command Center/Plug-ins` for manifest-compliant packages, validates licenses, and injects them during bus startup.
- **UI Operations**: War Room processors power the operator-facing desktop experiences; Start Menu shortcuts bridge the UI with the bus runtime, and the Enhanced GUI now talks to the Gateway Controller through the refactored `central_plugin` adapter.

## Operational Entry Points
- `make run-bus` executes `Command Center/Data Bus/Bus Core Design/main_application.py`.
- `make run-warden` executes `The Warden/warden_main.py`.
- `make run-marshall` launches the Marshall evidence manager for CLI-driven validations.
- `make run-debrief` runs the Mission Debrief manager for final report orchestration.
- `make test` executes the pytest suite (Analyst Deck section tests and War Room processors) once dependencies are installed.

## Documentation Set
- `SOP.md` - Day-to-day operations guide for on-call engineers and mission operators.
- `PRD.md` - Product requirements, target personas, and staged feature roadmap.
- `BLUEPRINT.md` - Technical architecture, data flows, and integration guardrails.
- `SYSTEM_README.md` (this file) - Orientation, quick start, and workflow map.
- Existing module deep dives remain in `Command Center/read_me_file/*.md` for subsystem detail.

## Support and Maintenance
- Central logging is written to module-specific logs under `Logs/` folders (per subsystem). Ensure log rotation scripts in `Ops Center/Automation` run nightly.
- Dependency upgrades should be tested with `make lint` and `make test` before merging.
- Use the signal codes documented in `SOP.md` for incident escalation (10-4, 10-9, 10-10, etc.).
- Coordinate cross-team changes through the Ecosystem Controller by updating section contracts and ensuring Analyst Deck frameworks stay in sync.

## Troubleshooting Tips
- If the bus fails to discover plugins, validate manifest JSON under `Command Center/Plug-ins` and confirm license files are present.
- Unexpected signal drops usually indicate a gateway controller misconfiguration; rerun `make run-warden` after checking the configuration directory.
- Report generation stalls typically trace back to missing professional toolkit dependencies; verify optional modules (Pillow, reportlab, etc.) are installed.
- For OCR failures, confirm external executables like Tesseract are reachable on PATH and the War Room configuration points at the correct binary.

## Escalation Path
1. Capture logs from the failing module and attach relevant evidence IDs.
2. Notify the Ecosystem Controller team (Warden owners) with the signal trail.
3. Open a mission incident in the Ops Center tracker and tag impacted sections.
4. Engage Mission Debrief maintainers if archival integrity is at risk.
5. Document remediation steps in the daily debrief for audit readiness.
