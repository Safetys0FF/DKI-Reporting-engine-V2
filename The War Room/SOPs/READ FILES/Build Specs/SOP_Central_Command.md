# CENTRAL COMMAND - STANDARD OPERATING PROCEDURES (SOP)
## Operational Procedures and Guidelines

**Version:** 1.0 (Current Build 2025-10-12)  
**Status:** CURRENT  
**Audience:** System Operators, Administrators  
**Document Type:** Standard Operating Procedures

---

## TABLE OF CONTENTS

1. [System Startup](#system-startup)
2. [Case Creation and Processing](#case-creation-and-processing)
3. [Evidence Management](#evidence-management)
4. [System Monitoring](#system-monitoring)
5. [Fault Handling](#fault-handling)
6. [Report Generation](#report-generation)
7. [System Shutdown](#system-shutdown)
8. [Troubleshooting](#troubleshooting)
9. [Maintenance](#maintenance)

---

## SYSTEM STARTUP

### SOP-001: Standard System Launch

**Procedure:**

1. **Navigate to UDS Launcher**
   ```
   F:\The Central Command\Command Center\Data Bus\diagnostic_manager\Unified_diagnostic_system\LAUNCH_DIAGNOSTIC_SYSTEM.bat
   ```

2. **Execute Launcher**
   - Double-click `LAUNCH_DIAGNOSTIC_SYSTEM.bat`
   - OR right-click → "Run as administrator" (if elevated privileges required)

3. **Monitor Initialization**
   - Watch console output for system initialization messages
   - Verify parent module instantiation:
     ```
     [INFO] Instantiating Evidence Locker (1)...
     [INFO] Instantiating Warden (2-1)...
     [INFO] Instantiating Marshall (3)...
     [INFO] Instantiating Mission Debrief (5)...
     [INFO] Instantiating GUI (GUI-1)...
     ```

4. **Verify Auto-Registration**
   - Confirm all 6 parent modules register successfully:
     ```
     [OK] Evidence Locker (1) - COMPLIANT
     [OK] Warden (2-1) - COMPLIANT
     [OK] Marshall (3) - COMPLIANT
     [OK] Mission Debrief (5) - COMPLIANT
     [OK] Bus-1 - COMPLIANT
     [OK] GUI-1 - COMPLIANT
     ```

5. **Complete Baseline Testing**
   - Wait for UDS to complete baseline tests
   - Verify "System operational" message
   - Check for fault codes (zero is optimal)

6. **GUI Launch**
   - GUI window should appear automatically
   - If setup wizard appears, complete initial setup
   - Authenticate with operator credentials

7. **Verification Checklist**
   - [ ] UDS console shows "System operational"
   - [ ] All 6 modules registered (6/6)
   - [ ] No critical fault codes
   - [ ] GUI window visible
   - [ ] GUI bus connection status shows "Connected"

**Expected Duration:** 30-60 seconds

**Troubleshooting:** See SOP-901 if startup fails

---

### SOP-002: GUI Standalone Launch (SAFEMODE)

**Use Case:** Launch GUI without full system initialization (testing, demonstration)

**Procedure:**

1. **Navigate to GUI Directory**
   ```
   F:\The Central Command\Command Center\UI\
   ```

2. **Launch Python Script**
   ```powershell
   python enhanced_functional_gui.py
   ```

3. **GUI Starts in SAFEMODE**
   - GUI operates without CANBUS connection
   - Limited functionality (local file management only)
   - Bus status shows "Disconnected" or "SAFEMODE"

4. **Verification**
   - [ ] GUI window visible
   - [ ] SAFEMODE indicator active
   - [ ] Local features operational

**Expected Duration:** 5-10 seconds

---

## CASE CREATION AND PROCESSING

### SOP-100: Create New Case

**Procedure:**

1. **Access Case Manager**
   - In GUI, locate "Case Manager" panel
   - OR click "New Case" button

2. **Enter Case Details**
   - **Case Name:** [Required] Descriptive case identifier
   - **Case Type:** [Required] Select investigation type
   - **Investigator:** [Required] Operator name
   - **Date:** [Auto] Current date (editable)
   - **Description:** [Optional] Case summary

3. **Submit Case Creation**
   - Click "Create Case" button
   - GUI emits `case_create` signal on CANBUS

4. **Verify Case Initialization**
   - Evidence Locker (1) receives signal
   - Case structure created
   - Case manifest initialized
   - GUI displays case ID and status: "Ready for Evidence"

5. **Verification Checklist**
   - [ ] Case appears in case list
   - [ ] Case status shows "Ready for Evidence"
   - [ ] Evidence upload UI enabled

**Expected Duration:** 5-10 seconds

**Troubleshooting:** See SOP-902 if case creation fails

---

### SOP-101: Upload Evidence

**Procedure:**

1. **Access Evidence Upload UI**
   - In GUI, open active case
   - Navigate to "Evidence Upload" tab

2. **Select Evidence Files**
   - **Method A:** Click "Browse Files" button, select files
   - **Method B:** Drag and drop files into upload area

3. **Review Selected Files**
   - Verify files listed correctly
   - Check file sizes and formats
   - Remove any incorrect selections

4. **Upload Evidence**
   - Click "Upload Evidence" button
   - GUI emits `files_add` signal on CANBUS
   - Monitor upload progress bar

5. **Verify Upload Success**
   - GUI shows "Upload complete" message
   - Evidence Locker (1) confirms receipt
   - Case manifest updates with new evidence count

6. **Monitor Classification**
   - Evidence Locker automatically classifies files
   - Status shows "Classifying evidence..."
   - Classification completes (typically 10 seconds per file)

7. **Review Evidence Manifest**
   - Check evidence list in GUI
   - Verify file types correctly identified
   - Confirm section relevance scores assigned

8. **Verification Checklist**
   - [ ] All files uploaded successfully
   - [ ] Evidence classified
   - [ ] Evidence manifest updated
   - [ ] No upload errors

**Expected Duration:** 1-5 minutes (depends on file count and sizes)

**Troubleshooting:** See SOP-903 if upload fails

---

### SOP-102: Initiate Case Processing

**Procedure:**

1. **Verify Evidence Ready**
   - All evidence uploaded
   - Classification complete
   - Case manifest validated

2. **Start Processing**
   - Click "Process Case" button in GUI
   - System automatically initiates workflow

3. **Automated Workflow Execution**
   - **Phase 1:** Warden (2-1) receives `evidence_ready` signal
   - **Phase 2:** Gateway (2-3) analyzes manifest, determines target sections
   - **Phase 3:** Marshall (3) wakes Analyst sections via LINBUS
   - **Phase 4:** Evidence distributed to sections
   - **Phase 5:** Sections process evidence (4-1 to 4-8)
   - **Phase 6:** Mission Debrief (5) assembles report
   - **Phase 7:** Report exported and archived

4. **Monitor Progress**
   - Watch Status Dashboard in GUI
   - Track section completion (GUI-1.5 Section Monitor)
   - Monitor for fault codes

5. **Await Completion**
   - System emits `narrative.assembled` signal
   - GUI displays "Report Complete" notification
   - Report Viewer enabled

6. **Verification Checklist**
   - [ ] All target sections completed
   - [ ] No critical fault codes
   - [ ] Report assembled
   - [ ] Report available in Report Viewer

**Expected Duration:** 15-30 minutes (typical case with 50 evidence files)

**Troubleshooting:** See SOP-904 if processing fails

---

## EVIDENCE MANAGEMENT

### SOP-200: Search Evidence

**Procedure:**

1. **Access Evidence Index**
   - In GUI, open case
   - Navigate to "Evidence" tab

2. **Enter Search Query**
   - Type keywords in search box
   - Use filters (file type, date, section)

3. **Review Results**
   - Evidence list displays matching items
   - Click evidence to view details

4. **Open Evidence**
   - Double-click evidence item
   - System opens in default application (image viewer, PDF reader, etc.)

**Expected Duration:** 1-5 seconds

---

### SOP-201: Modify Evidence Classification

**Use Case:** Correct misclassified evidence

**Procedure:**

1. **Locate Evidence**
   - Find evidence item in case manifest

2. **Access Classification Details**
   - Right-click evidence item
   - Select "Edit Classification"

3. **Modify Classification**
   - Update file type if incorrect
   - Adjust section relevance scores
   - Add/remove keywords

4. **Save Changes**
   - Click "Save"
   - System updates evidence index

5. **Verification**
   - [ ] Classification updated
   - [ ] Evidence index refreshed

**Expected Duration:** 30-60 seconds per file

---

## SYSTEM MONITORING

### SOP-300: Monitor System Health

**Procedure:**

1. **Access Status Dashboard**
   - In GUI, click "System Status" tab (GUI-1.3)

2. **Review System Metrics**
   - **Module Status:** All parent modules should show "Operational"
   - **Bus Status:** CANBUS should show "Connected"
   - **Fault Codes:** Should be zero or low

3. **Check Section Status**
   - Navigate to "Section Monitor" (GUI-1.5)
   - Verify sections in correct state (idle, processing, complete)

4. **Review Logs**
   - Access Log Viewer (GUI-1.8)
   - Filter by severity (INFO, WARNING, ERROR)
   - Investigate any ERROR or WARNING entries

5. **Verification Checklist**
   - [ ] All modules operational
   - [ ] CANBUS connected
   - [ ] No critical faults
   - [ ] Logs show normal operation

**Frequency:** Every 30 minutes during active use

---

### SOP-301: Review Fault Codes

**Procedure:**

1. **Access Fault Log**
   - In GUI, navigate to "Faults" tab
   - OR check UDS console output

2. **Identify Fault Codes**
   - Format: `MODULE_ADDRESS.FAULT_NUMBER`
   - Example: `1.10` = Evidence Locker ingestion failure

3. **Determine Severity**
   - **XX.00-XX.09:** CRITICAL - immediate action required
   - **XX.10-XX.89:** ERROR - investigate and resolve
   - **XX.90-XX.99:** WARNING - monitor but continue

4. **Consult Fault Registry**
   - Refer to module README for fault code definitions
   - Example: `Evidence Locker/README.md` for codes 1.00-1.99

5. **Take Action**
   - **CRITICAL:** Halt operation, escalate to administrator
   - **ERROR:** Attempt recovery, retry operation
   - **WARNING:** Log and monitor

6. **Document Resolution**
   - Record fault code
   - Document actions taken
   - Verify resolution

**Frequency:** On fault detection (real-time)

---

## FAULT HANDLING

### SOP-400: Handle Critical Faults

**Definition:** Critical faults (XX.00-XX.09) require immediate intervention

**Procedure:**

1. **Identify Critical Fault**
   - Fault code in range XX.00-XX.09
   - Example: `DIAG-1.00` = UDS initialization failure

2. **Halt Operations**
   - STOP current case processing
   - Do NOT start new cases
   - Prevent data corruption

3. **Document Fault**
   - Record fault code
   - Note time of occurrence
   - Capture relevant log entries

4. **Attempt Recovery**
   - Refer to module-specific troubleshooting (module README)
   - If recovery procedure exists, follow it
   - If no procedure, escalate

5. **Restart System**
   - Shutdown system (SOP-700)
   - Restart system (SOP-001)
   - Verify fault resolved

6. **Escalate If Unresolved**
   - Contact system administrator
   - Provide fault code and logs
   - Await resolution

**Expected Resolution Time:** 10-60 minutes

---

### SOP-401: Handle Non-Critical Faults

**Definition:** Non-critical faults (XX.10-XX.99) may allow continued operation

**Procedure:**

1. **Identify Fault**
   - Fault code in range XX.10-XX.99

2. **Assess Impact**
   - Does fault block current operation?
   - Can operation continue?

3. **Retry Operation** (if applicable)
   - Example: Evidence upload failure → retry upload
   - Example: Section processing timeout → wake section again

4. **Monitor for Recurrence**
   - If fault repeats 3+ times, escalate to ERROR level

5. **Document**
   - Log fault occurrence
   - Note resolution attempts

**Expected Resolution Time:** 5-30 minutes

---

## REPORT GENERATION

### SOP-500: View Completed Report

**Procedure:**

1. **Verify Report Complete**
   - GUI shows "Report Complete" notification
   - Case status: "Complete"

2. **Access Report Viewer**
   - In GUI, navigate to "Report Viewer" (GUI-1.4)
   - OR click "View Report" button

3. **Review Report**
   - Scroll through report sections
   - Verify all sections present
   - Check formatting and layout

4. **Verification Checklist**
   - [ ] All 8 sections present (TOC, Cover, Summary, Analysis, Timeline, Findings, Recommendations, Appendices)
   - [ ] Evidence correctly cited
   - [ ] Formatting consistent
   - [ ] No missing content

---

### SOP-501: Export Report

**Procedure:**

1. **Access Export Options**
   - In Report Viewer, click "Export" button

2. **Select Format**
   - **PDF:** For distribution and printing
   - **DOCX:** For editing

3. **Choose Export Location**
   - Default: `F:\The Central Command\Generated Reports\`
   - OR select custom location

4. **Export Report**
   - Click "Export" button
   - Monitor export progress

5. **Verify Export**
   - Navigate to export location
   - Open exported file
   - Verify content and formatting

6. **Verification Checklist**
   - [ ] File exists in export location
   - [ ] File opens correctly
   - [ ] Content matches Report Viewer
   - [ ] Formatting preserved

**Expected Duration:** 30-120 seconds

---

### SOP-502: Archive Report

**Procedure:**

1. **Automatic Archival**
   - The Librarian (5-2) automatically archives reports
   - Archive location: `Command Center/Mission Debrief/Library/`

2. **Verify Archival**
   - Check Library for report
   - Confirm case ID matches

3. **Retrieve Archived Report** (if needed)
   - In GUI, navigate to "Library"
   - Search by case ID, date, or investigator
   - Click report to open

**Frequency:** Automatic on report completion

---

## SYSTEM SHUTDOWN

### SOP-700: Standard System Shutdown

**Procedure:**

1. **Verify No Active Cases**
   - Check Status Dashboard
   - Confirm no cases in "Processing" state

2. **Close GUI**
   - Click "File" → "Exit"
   - OR click window close button (X)

3. **GUI Shutdown Sequence**
   - GUI saves state
   - GUI disconnects from CANBUS
   - GUI window closes

4. **UDS Shutdown** (if applicable)
   - If UDS console still running, press Ctrl+C
   - OR close UDS console window

5. **Verify Shutdown**
   - No system windows open
   - No Python processes running (check Task Manager)

6. **Verification Checklist**
   - [ ] GUI closed
   - [ ] UDS closed
   - [ ] No orphan processes

**Expected Duration:** 10-20 seconds

---

### SOP-701: Emergency Shutdown

**Use Case:** Critical fault, system unresponsive

**Procedure:**

1. **Force Close GUI**
   - Task Manager → Find Python processes
   - End Task on GUI process

2. **Force Close UDS**
   - Task Manager → Find Python processes
   - End Task on UDS process

3. **Verify Data Integrity**
   - Check case manifests for corruption
   - Review log files for incomplete operations

4. **Document Emergency Shutdown**
   - Record time and reason
   - Note active cases at shutdown
   - Flag cases for verification on restart

**Expected Duration:** 30-60 seconds

---

## TROUBLESHOOTING

### SOP-901: System Startup Failure

**Symptoms:** UDS fails to launch, modules don't register

**Procedure:**

1. **Check Python Installation**
   ```powershell
   python --version
   ```
   - Should be Python 3.11+

2. **Check CANBUS**
   - Verify `bus_core.py` exists
   - Check for import errors in console

3. **Review UDS Logs**
   - Location: `Command Center/Data Bus/diagnostic_manager/Unified_diagnostic_system/library/system_logs/`
   - Look for ERROR entries

4. **Retry Startup**
   - Close all windows
   - Restart via SOP-001

5. **If Still Failing:**
   - Check for disk space issues
   - Verify file permissions
   - Escalate to administrator

---

### SOP-902: Case Creation Failure

**Symptoms:** "Create Case" button unresponsive, case not created

**Procedure:**

1. **Verify Bus Connection**
   - Check GUI Bus State Monitor (GUI-1.9)
   - Should show "Connected"

2. **Check Evidence Locker Status**
   - In Status Dashboard, verify Evidence Locker (1) operational

3. **Retry Case Creation**
   - Re-enter case details
   - Click "Create Case" again

4. **If Still Failing:**
   - Restart GUI (SOP-002)
   - Restart entire system (SOP-700, SOP-001)

---

### SOP-903: Evidence Upload Failure

**Symptoms:** Upload progress bar stalls, error message displayed

**Procedure:**

1. **Check File Validity**
   - Verify file exists
   - Check file not corrupted
   - Verify file format supported

2. **Check File Size**
   - Maximum: 2GB per file
   - If larger, split or compress

3. **Check Disk Space**
   - Verify adequate space in Evidence Locker directory

4. **Retry Upload**
   - Remove failed file from selection
   - Re-add file
   - Retry upload

5. **If Still Failing:**
   - Upload files individually (not batch)
   - Check Evidence Locker logs

---

### SOP-904: Case Processing Stalls

**Symptoms:** Processing stuck on one section, no progress

**Procedure:**

1. **Identify Stuck Section**
   - Check Section Monitor (GUI-1.5)
   - Note which section shows "Processing" for extended time

2. **Check Section Fault Codes**
   - Review Fault Log
   - Look for faults in range 4.XX (Analyst sections)

3. **Review Marshall Status**
   - Verify Marshall (3) operational
   - Check LINBUS connectivity

4. **Manual Section Wake** (if available)
   - Send wake command to stuck section
   - Monitor for response

5. **Restart Processing**
   - Cancel current processing
   - Restart case processing (SOP-102)

6. **If Still Failing:**
   - Escalate to administrator
   - Provide section ID and fault codes

---

## MAINTENANCE

### SOP-800: Daily Maintenance

**Frequency:** Daily (if system in active use)

**Procedure:**

1. **Review System Logs**
   - Check UDS logs for errors
   - Review Bus logs for anomalies

2. **Check Disk Space**
   - Verify adequate space for evidence and reports
   - Archive or delete old cases if needed

3. **Backup Critical Data**
   - Case manifests
   - System registry
   - Configuration files

4. **Verification Checklist**
   - [ ] Logs reviewed
   - [ ] Disk space adequate (≥ 10GB free)
   - [ ] Backups current

**Expected Duration:** 10-15 minutes

---

### SOP-801: Weekly Maintenance

**Frequency:** Weekly

**Procedure:**

1. **Full System Test**
   - Run UDS baseline testing (SOP-001)
   - Verify all modules operational

2. **Review Archived Reports**
   - Verify Library integrity
   - Check report count

3. **Clean Temporary Files**
   - Clear system logs older than 30 days
   - Remove temporary evidence files

4. **Update Documentation**
   - Document any new operational issues
   - Update this SOP if procedures changed

5. **Verification Checklist**
   - [ ] System test passed
   - [ ] Library integrity verified
   - [ ] Temporary files cleaned
   - [ ] Documentation current

**Expected Duration:** 30-45 minutes

---

### SOP-802: Monthly Maintenance

**Frequency:** Monthly

**Procedure:**

1. **Full Data Backup**
   - Backup entire `F:\The Central Command\` directory
   - Store backup on external drive or network

2. **Performance Review**
   - Check average case processing time
   - Review fault code frequency
   - Identify performance bottlenecks

3. **System Update Check**
   - Check for Python updates
   - Check for module updates

4. **Verification Checklist**
   - [ ] Full backup complete
   - [ ] Performance metrics reviewed
   - [ ] Updates applied (if any)

**Expected Duration:** 1-2 hours

---

## APPENDIX

### A. File Locations

**System Root:**  
`F:\The Central Command\`

**UDS Launcher:**  
`F:\The Central Command\Command Center\Data Bus\diagnostic_manager\Unified_diagnostic_system\LAUNCH_DIAGNOSTIC_SYSTEM.bat`

**GUI Script:**  
`F:\The Central Command\Command Center\UI\enhanced_functional_gui.py`

**Evidence Storage:**  
`F:\The Central Command\intake\`

**Report Output:**  
`F:\The Central Command\Generated Reports\`

**Report Archive:**  
`F:\The Central Command\Command Center\Mission Debrief\Library\`

**System Logs:**  
`F:\The Central Command\Command Center\Data Bus\diagnostic_manager\Unified_diagnostic_system\library\system_logs\`

---

### B. Common Radio Codes

| Code | Meaning |
|------|---------|
| 10-4 | Acknowledged |
| 10-6 | Busy |
| 10-20 | Location |
| 10-36 | Correct time |
| 10-77 | ETA |

---

### C. Support Contacts

**System Administrator:** [Contact Information]  
**Technical Support:** [Contact Information]  
**Documentation:** `The War Room/SOPs/READ FILES/Build Specs/`

---

**Document Type:** Standard Operating Procedures  
**Version:** 1.0  
**Status:** CURRENT  
**Last Updated:** 2025-10-12

**Related Documentation:**
- `SYSTEM_README.md` - System overview
- `CURRENT_SYSTEM_ARCHITECTURE_2025-10-12.md` - Architecture
- `PRD_Central_Command.md` - Requirements
- `System_Blueprint_Central_Command.md` - Technical design
