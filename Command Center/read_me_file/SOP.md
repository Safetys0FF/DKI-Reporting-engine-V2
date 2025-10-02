# Standard Operating Procedure (SOP) - DKI Command Ecosystem

## Document Control
- Owner: Central Command Operations
- Last Updated: 2025-09-25
- Applies To: All mission operators, on-call engineers, analyst supervisors, and automation leads.

## 1. Purpose
Provide a repeatable operating procedure for starting, monitoring, and shutting down the DKI investigation reporting platform while preserving evidence integrity and operational compliance.

## 2. Scope
Covers day-to-day operations within `F:\The Central Command`, including the Data Bus, Warden, Marshall, Evidence Locker, Analyst Deck, War Room processors, and Mission Debrief services.

## 3. Roles and Responsibilities
- **Mission Operator**: Executes startup sequence, monitors signals, performs evidence intake, and initiates report runs.
- **On-Call Engineer**: Responds to incidents, maintains dependencies, and coordinates fixes across subsystems.
- **Analyst Supervisor**: Approves section readiness, tracks revisions (10-9), and validates outputs before publication.
- **Automation Lead**: Maintains Ops Center jobs (log rotation, backups, nightly tests).

## 4. Pre-Shift Readiness Checklist
1. Confirm workstation has Python 3.11+ and required external binaries (Tesseract, FFmpeg, Ghostscript if printing).
2. Pull latest code and confirm no unresolved merge conflicts: `git status`.
3. Ensure virtual environment is current: `make install`.
4. Validate plugin manifests under `Command Center/Plug-ins` and license files under `Command Center/Plug-ins/licenses` if any updates occurred overnight.
5. Confirm log directories have free space (>10 GB recommended) and backup jobs from `Ops Center/Automation` succeeded.
6. Open the incident tracker to review outstanding issues and planned maintenance windows.

## 5. System Startup Procedure
1. Open four terminals at `F:\The Central Command`.
2. **Terminal 1**: `make run-bus` to start the Data Bus (central signal hub). Wait for `[MAIN] Bus runtime launched`.
3. **Terminal 2**: `make run-warden` to bring the Ecosystem Controller online. Verify it registers sections and confirms ECC heartbeat.
4. **Terminal 3**: `make run-marshall` to activate evidence ingestion and gateway orchestration. Confirm connection to ECC and Evidence Locker.
5. **Terminal 4**: `make run-debrief` when report finalization is required. Keep idle if no missions are scheduled.
6. Launch UI tooling from the War Room or Start Menu as mission demands (`The War Room/Processors` executables).
7. Document startup time, operator initials, and any anomalies in the mission log.

## 6. Evidence Intake Procedure
1. Ingest evidence through the Marshall interface (CLI or UI). Ensure metadata (case ID, section hints, tags) is supplied.
2. Verify Evidence Locker classification via logs: look for `classification_complete` signals.
3. Confirm evidence index updates succeeded. Run spot checks with `EvidenceLocker.get_manager_status()` if needed.
4. For high-priority evidence, trigger manual validation using the Analyst Deck toolkit before release to sections.
5. If classification fails, raise a 10-9 signal (revision) and assign an analyst to review metadata or content issues.

## 7. Section Processing Procedure
1. Monitor the Warden console for section lifecycle transitions (IDLE -> PREPARING -> EXECUTING -> COMPLETED).
2. Analysts run section frameworks from the Analyst Deck (`section_X_framework.py`).
3. Ensure each section publishes back to the bus with `publish_section_payload` or equivalent method.
4. Capture `10-4` (section ready) or `10-9` (revision) signals for each section and log them in the daily status sheet.
5. If a section hangs in EXECUTING for more than 15 minutes without log activity, escalate to the on-call engineer.

## 8. Mission Debrief and Publication
1. When all sections report `10-4`, trigger Mission Debrief via `make run-debrief` or UI button.
2. Confirm professional tools (digital signature, watermark, templates, OSINT) are enabled per case requirements.
3. Review the draft narrative in the Librarian output directory before archival.
4. Upon approval, archive the final package in `Command Center/Mission Debrief/Library` and update the chain-of-custody manifest.
5. Export required deliverables (PDF, DOCX, RTF) as specified in the case briefing. Record hash digests for legal compliance.

## 9. Plugin Lifecycle Management
1. New plugins must include a manifest and optional license file. Place them under `Command Center/Plug-ins`.
2. Run `make run-bus` in dry-run mode (`python ... main_application.py --dry-run`) if available to test discovery without affecting production signals.
3. Review plugin registration logs for contract compliance warnings.
4. Disable plugins by toggling `enabled: false` in the configuration file and restarting the bus.

## 10. Incident Response Workflow
1. **Detection**: Capture the first error message and affected signal ID.
2. **Containment**: Pause intake (`10-10`) from the Marshall gateway if data integrity is threatened.
3. **Diagnosis**: Inspect relevant module logs and run targeted tests in `.\Ops Center\Automation`.
4. **Resolution**: Apply hotfix or configuration change. Document steps taken.
5. **Recovery**: Resume paused signals with `10-8` once verified.
6. **Post-Incident**: File a debrief entry summarizing root cause, mitigation, and follow-up actions.

### Signal Reference
- `10-4` - Section ready / approved.
- `10-6` - Toolkit ready for dispatch.
- `10-8` - Section reporting complete.
- `10-9` - Revision requested.
- `10-10` - Emergency halt.
- `10-99` - Final report approved.

## 11. Reporting and Audit Trail
- Maintain a mission log capturing evidence IDs, signal transitions, operator actions, and timestamps.
- Archive daily logs under `Evidence Locker` and `Mission Debrief` library folders.
- Ensure checksum reports are exported for every finalized case and stored alongside deliverables.

## 12. Shutdown Procedure
1. Confirm mission queue is empty (`Marshall.get_manager_status`).
2. Gracefully exit Mission Debrief (`CTRL+C` or UI shutdown) and verify library writes completed.
3. Halt the Marshall gateway (`CTRL+C`) after ensuring no active processing threads.
4. Stop the Warden controller and confirm sections return to IDLE state.
5. Shut down the Data Bus last to flush pending signals.
6. Archive the daily mission log and upload incident summaries to the Ops Center repository.

## 13. Appendices
- **Key Logs**: Refer to `Logs/` subdirectories within each module. Rotate via `Ops Center/Automation/log_rotation.ps1`.
- **Backups**: Evidence archives replicate nightly to secure storage. Verify success each morning.
- **Contacts**: Warden Owner (ecosystem@central.local), Marshall Owner (gateway@central.local), Mission Debrief Owner (debrief@central.local).
