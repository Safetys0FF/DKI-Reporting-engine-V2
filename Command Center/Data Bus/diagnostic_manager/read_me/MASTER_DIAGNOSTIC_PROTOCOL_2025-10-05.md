# Master Diagnostic Protocol
## Date: October 5, 2025
## Location: F:\The Central Command\The War Room\SOPs\READ FILES\diagnostics_protocols

# **CENTRAL COMMAND DIAGNOSTIC PROTOCOL MASTER REFERENCE**

This document serves as the **definitive reference** for all diagnostic protocols, system addresses, fault codes, and communication callouts across the Central Command system.

---

## **SYSTEM ADDRESS REGISTRY**

### **Bus System**
| Address | System Name | Handler | Status | Last Check |
|---------|-------------|---------|--------|------------|
| Bus-1 | Central Command Bus | bus_core.DKIReportBus | ACTIVE | - |
| Bus-1.1 | Universal Communicator | universal_communicator.UniversalCommunicator | ACTIVE | - |
| Bus-1.2 | Universal Communicator | universal_communicator.UniversalCommunicator | ACTIVE | - |
| Bus-1.3 | Bus Core | bus_core.DKIReportBus | ACTIVE | - |
| Bus-1.4 | Universal Communicator | universal_communicator.UniversalCommunicator | ACTIVE | - |
| Bus-1.5 | Unified Diagnostic System | unified_diagnostic_system.UnifiedDiagnosticSystem | ACTIVE | - |

### **Evidence Locker Complex (1-x)**
| Address | System Name | Handler | Parent | Status | Last Check |
|---------|-------------|---------|--------|--------|------------|
| 1 | Evidence Locker Main | evidence_locker_main.EvidenceLocker | - | ACTIVE | 2025-10-09 |
| 1.1 | Evidence Classifier | evidence_classifier.EvidenceClassifier | 1 | ACTIVE | - |
| 1.2 | Evidence Identifier | evidence_identifier.EvidenceIdentifier | 1 | ACTIVE | - |
| 1.3 | Static Data Flow | static_data_flow.StaticDataFlow | 1 | ACTIVE | - |
| 1.4 | Evidence Index | evidence_index.EvidenceIndex | 1 | ACTIVE | - |
| 1.5 | Evidence Manifest | evidence_manifest.EvidenceManifest | 1 | ACTIVE | - |
| 1.6 | Evidence Class Builder | evidence_class_builder.EvidenceClassBuilder | 1 | ACTIVE | - |
| 1.7 | Case Manifest Builder | case_manifest_builder.CaseManifestBuilder | 1 | ACTIVE | - |
| 1.8 | OCR Processor | ocr_processor.OCRProcessor | 1 | ACTIVE | - |

### **Warden Complex (2-x)**
| Address | System Name | Handler | Parent | Status | Last Check |
|---------|-------------|---------|--------|--------|------------|
| 2 | Warden Module (CANBUS Connected) | warden_module.Warden | - | ACTIVE | 2025-10-09 |
| 2-2 | Ecosystem Controller (Driven) | ecosystem_controller.EcosystemController | 2 | ACTIVE | 2025-10-09 |
| 2-2.1 | ECC State Manager | ecc_state_manager.ECCStateManager | 2-2 | ACTIVE | - |
| 2-2.2 | ECC Dependency Tracker | ecc_dependency_tracker.ECCDependencyTracker | 2-2 | ACTIVE | - |
| 2-2.3 | ECC Execution Order | ecc_execution_order.ECCExecutionOrder | 2-2 | ACTIVE | - |
| 2-2.4 | ECC Permission Controller | ecc_permission_controller.ECCPermissionController | 2-2 | ACTIVE | - |
| 2-3 | Gateway Controller (Driven, Fault Relay Handler) | gateway_controller.GatewayController | 2 | ACTIVE | 2025-10-09 |
| 2-3.1 | Gateway Signal Dispatcher | gateway_signal_dispatcher.GatewaySignalDispatcher | 2-3 | ACTIVE | - |
| 2-3.2 | Gateway Section Router | gateway_section_router.GatewaySectionRouter | 2-3 | ACTIVE | - |
| 2-3.3 | Gateway Evidence Pipeline | gateway_evidence_pipeline.GatewayEvidencePipeline | 2-3 | ACTIVE | - |
| 2-3.4 | Gateway Bottleneck Monitor | gateway_bottleneck_monitor.GatewayBottleneckMonitor | 2-3 | ACTIVE | - |

### **Marshall Complex (3-x)**
| Address | System Name | Handler | Parent | Status | Last Check |
|---------|-------------|---------|--------|--------|------------|
| 3 | Marshall Module (CANBUS Connected) | marshall_module.MarshallModule | - | ACTIVE | 2025-10-09 |
| 3-1 | Evidence Manager (Driven) | evidence_manager.EvidenceManager | 3 | ACTIVE | 2025-10-09 |
| 3-2 | Evidence Checkout (Driven) | section_controller.SectionController | 3 | ACTIVE | - |
| 3-3 | Gateway (Driven) | gateway.Gateway | 3 | ACTIVE | - |

### **Analyst Deck Complex (4-x)** — All CANBUS Connected via Base Class
| Address | System Name | Handler | Parent | Fault Relay Parent | Status | Last Check |
|---------|-------------|---------|--------|---------------------|--------|------------|
| 4-1 | Section 1 - Case Profile (CANBUS Connected) | section_1_framework.Section1Framework | - | 2-3 (Gateway) | ACTIVE | 2025-10-09 |
| 4-2 | Section 2 - Investigation Planning (CANBUS Connected) | section_2_framework.Section2Framework | - | 2-3 (Gateway) | ACTIVE | 2025-10-09 |
| 4-3 | Section 3 - Surveillance Operations (CANBUS Connected) | section_3_framework.Section3Framework | - | 2-3 (Gateway) | ACTIVE | 2025-10-09 |
| 4-4 | Section 4 - Session Review (CANBUS Connected) | section_4_framework.Section4Framework | - | 2-3 (Gateway) | ACTIVE | 2025-10-09 |
| 4-5 | Section 5 - Document Inventory (CANBUS Connected) | section_5_framework.Section5Framework | - | 2-3 (Gateway) | ACTIVE | 2025-10-09 |
| 4-6 | Section 6 - Billing Summary (CANBUS Connected) | section_6_framework.Section6Framework | - | 2-3 (Gateway) | ACTIVE | 2025-10-09 |
| 4-7 | Section 7 - Conclusion (CANBUS Connected) | section_7_framework.Section7Framework | - | 2-3 (Gateway) | ACTIVE | 2025-10-09 |
| 4-8 | Section 8 - Media Documentation (CANBUS Connected) | section_8_framework.Section8Framework | - | 2-3 (Gateway) | ACTIVE | 2025-10-09 |

### **Mission Debrief Complex (5-x)**
| Address | System Name | Handler | Parent | Status | Last Check |
|---------|-------------|---------|--------|--------|------------|
| 5 | Mission Debrief Module (CANBUS Connected) | mission_debrief_module.MissionDebriefModule | - | ACTIVE | 2025-10-09 |
| 5-1 | Debrief Manager (Driven) | mission_debrief_manager.MissionDebriefManager | 5 | ACTIVE | 2025-10-09 |
| 5-1.1 | Cover Page Framework | section_cp_framework.SectionCPFramework | 5-1 | ACTIVE | 2025-10-09 |
| 5-1.2 | Disclosure Page Framework | section_dp_framework.SectionDPFramework | 5-1 | ACTIVE | 2025-10-09 |
| 5.1 | Report Generator (Utility Tool) | report_generator.ReportGenerator | 5 | ACTIVE | - |
| 5.2 | Digital Signing Tool (Utility) | digital_signature_system.DigitalSignatureSystem | 5 | ACTIVE | - |
| 5.3 | Template Engine Tool (Utility) | template_system.TemplateSystem | 5 | ACTIVE | - |
| 5.4 | Watermark Tool (Utility) | watermark_system.WatermarkSystem | 5 | ACTIVE | - |
| 5-2 | The Librarian (Driven) | narrative_assembler.NarrativeAssembler | 5 | ACTIVE | 2025-10-09 |
| 5-2.1 | Template Cache | template_cache.TemplateCache | 5-2 | ACTIVE | - |
| 5-2.2 | Document Processor | document_processor.DocumentProcessor | 5-2 | ACTIVE | - |
| 5-2.3 | OSINT Engine | osint_engine.OSINTEngine | 5-2 | ACTIVE | - |
| 5-2.4 | Table of Contents Framework | section_toc_framework.SectionTOCFramework | 5-2 | ACTIVE | 2025-10-09 |

### **War Room Complex (6-x)**
| Address | System Name | Handler | Parent | Status | Last Check |
|---------|-------------|---------|--------|--------|------------|
| 6-1 | Dev Environment | dev_environment.DevEnvironment | - | ACTIVE | - |
| 6-2 | Tool Dependencies | tool_dependencies.ToolDependencies | - | ACTIVE | - |

### **Enhanced Functional GUI (GUI-1)**
| Address | System Name | Handler | Parent | Status | Last Check |
|---------|-------------|---------|--------|--------|------------|
| GUI-1 | Enhanced Functional GUI (CANBUS Connected) | enhanced_functional_gui.EnhancedDKIGUI | - | ACTIVE | 2025-10-10 |
| 7-1 | Enhanced Functional GUI (Legacy) | enhanced_functional_gui.EnhancedFunctionalGUI | - | DEPRECATED | - |
| GUI-1.1 | User Interface Controller | ui_controller.UIController | GUI-1 | ACTIVE | 2025-10-10 |
| GUI-1.2 | Case Management Interface | case_management_interface.CaseManagementInterface | GUI-1 | ACTIVE | 2025-10-10 |
| GUI-1.3 | Evidence Display Interface | evidence_display_interface.EvidenceDisplayInterface | GUI-1 | ACTIVE | 2025-10-10 |
| GUI-1.4 | Section Review Interface | section_review_interface.SectionReviewInterface | GUI-1 | ACTIVE | 2025-10-10 |
| GUI-1.5 | Report Generation Interface | report_generation_interface.ReportGenerationInterface | GUI-1 | ACTIVE | 2025-10-10 |
| GUI-1.6 | System Status Interface | system_status_interface.SystemStatusInterface | GUI-1 | ACTIVE | 2025-10-10 |
| GUI-1.7 | Error Display Interface | error_display_interface.ErrorDisplayInterface | GUI-1 | ACTIVE | 2025-10-10 |
| GUI-1.8 | Progress Monitoring Interface | progress_monitoring_interface.ProgressMonitoringInterface | GUI-1 | ACTIVE | 2025-10-10 |
| GUI-1.9 | Health Monitor | health_monitor.HealthMonitor | GUI-1 | ACTIVE | 2025-10-10 |

### **General Systems**
| Address | System Name | Handler | Parent | Status | Last Check |
|---------|-------------|---------|--------|--------|------------|

---

## **UNIVERSAL SIGNAL TRANSLATION PROTOCOL**

**Updated:** October 10, 2025  
**Architect:** DEESCALATION Agent

### **Communication Architecture**

All parent modules (Evidence Locker, Warden, Marshall, Mission Debrief, GUI) implement a **universal translation layer** that converts internal child broadcasts to standardized CANBUS signals.

**Pattern:**
```
Child Component → Parent Wildcard (*.child.broadcast)
                ↓
Parent Module Translation Layer
                ↓
Universal CANBUS Signal + Radio Code
                ↓
All Systems (UDS, GUI, Other Modules)
```

### **Parent Module Signal Translations**

#### **Evidence Locker Module (Address 1)**

**Wildcard Signal:** `locker.child.broadcast`

| Child Message Type | Universal Signal Emitted | Radio Code | Description |
|--------------------|--------------------------|------------|-------------|
| `ingest_evidence` | `evidence.new` | 10-6 | Evidence file received and processing |
| `ingest_evidence` | `evidence.classified` | 10-4 | Evidence classified and ready |
| `start_new_case` | `case.created` | - | New case initialized |
| `clear_evidence_pool` | `locker.cleared` | - | Evidence pool cleared |

**Translation Handler:** `_handle_child_broadcast()`

#### **Warden Module (Address 2)**

**Wildcard Signal:** `warden.child.broadcast`

| Child Message Type | Universal Signal Emitted | Radio Code | Description |
|--------------------|--------------------------|------------|-------------|
| `gateway_ready` | `gateway.ready` | 10-4 | Gateway initialization complete |
| `ecosystem_ready` | `ecosystem.ready` | - | ECC initialization complete |
| `section_routed` | `section.routed` | 10-4 | Section routing approved |
| `handoff_complete` | `handoff.completed` | - | Module handoff successful |

**Translation Handler:** `_handle_child_broadcast()`

#### **Marshall Module (Address 3)**

**Wildcard Signal:** `marshall.child.broadcast`

| Child Message Type | Universal Signal Emitted | Radio Code | Description |
|--------------------|--------------------------|------------|-------------|
| `evidence_processed` | `evidence.processed` | 10-6 | Evidence processing active |
| `evidence_distributed` | `evidence.distributed` | - | Evidence distributed to section |
| `evidence_ready_for_debrief` | `evidence.ready_for_debrief` | 10-8 | Evidence processing complete |

**Translation Handler:** `_handle_child_broadcast()`

#### **Mission Debrief Module (Address 5)**

**Wildcard Signal:** `mission.child.broadcast`

| Child Message Type | Universal Signal Emitted | Radio Code | Description |
|--------------------|--------------------------|------------|-------------|
| `report_assembled` | `mission.report.assembled` | 10-8 | Report assembly complete |
| `narrative_assembled` | `narrative.assembled` | - | Narrative assembly complete |
| `artifacts_generated` | `artifacts.generated` | - | Artifacts (CP, TOC, DP) generated |
| `final_report_ready` | `report.ready` | - | Final report ready for delivery |

**Translation Handler:** `_handle_child_broadcast()`

#### **GUI Module (Address GUI-1)**

**Wildcard Signal:** `gui.child.broadcast`

| Child Message Type | Universal Signal Emitted | Radio Code | Description |
|--------------------|--------------------------|------------|-------------|
| `user_action` | `gui.user.action` | - | User initiated action |
| `view_changed` | `gui.view.changed` | - | GUI view/tab changed |
| `error_displayed` | `gui.error.displayed` | - | Error shown to user |
| `progress_updated` | `gui.progress.updated` | - | Progress indicator updated |

**Translation Handler:** `_handle_child_broadcast()` (pending implementation)

### **Radio Code Callout Protocol**

Based on UniversalCommunicator RadioCode enum and gateway callbox logic:

| Radio Code | Meaning | Parent Module Usage | Gateway Action | UDS Monitoring |
|------------|---------|---------------------|----------------|----------------|
| **10-4** | ACKNOWLEDGED | Message received and understood / Section approved / Ready signals | Unlock next section | System operational |
| **10-6** | EVIDENCE_RECEIVED | Evidence received and being processed / Toolkit initialized | Broadcast toolkit context | Processing started |
| **10-8** | EVIDENCE_COMPLETE | Evidence processing complete / Section finished / Output ready | Collect output payload | Processing complete |
| **10-9** | REPEAT | Please repeat last message / Manual review requested / Communication retry | Trigger manual review | Communication issue |
| **10-10** | STANDBY | Processing in progress / System waiting / Emergency halt | Freeze gateway, notify lead | System waiting |
| **SOS** | EMERGENCY | System failure detected / Critical error | Escalate to diagnostics | Fault detected |
| **MAYDAY** | CRITICAL_FAILURE | System down / Complete failure / Unrecoverable error | Emergency shutdown protocol | System down |
| **STATUS** | STATUS_REQUEST | Request system status / Health check | Return status payload | Health monitoring |
| **ROLLCALL** | ROLLCALL | All systems respond / System discovery | Registry update | System registration |
| **RADIO_CHECK** | COMMUNICATION_TEST | Communication test / Connectivity validation | Acknowledge receipt | Connectivity test |

### **Implementation Requirements**

**All parent modules MUST:**
1. Register `[module_name].child.broadcast` signal handler
2. Implement `_handle_child_broadcast(payload)` method
3. Translate child `message_type` to universal signals
4. Emit appropriate radio codes via `communicator.send_signal()`
5. Log translation events for debugging

**All child components MUST:**
1. Emit to parent wildcard only (`locker.child.broadcast`, etc.)
2. Include `message_type` in payload
3. NOT directly emit to universal CANBUS signals
4. Let parent handle all external communication

### **Validation Method**

Per UDS observation protocol: **Absence of fault = translation successful**

Test with real evidence flow:
```bash
cd diagnostic_manager/test_plans
python run_real_flow_test.py
```

Expected: Exit code 0, signals captured, zero UDS faults.

---

## **FAULT SYMPTOMS & DIAGNOSTIC CODES**

### **Common Failure Codes (XX)**

#### **Syntax/Configuration Errors**
| Code | Symptom | Description | Resolution |
|------|---------|-------------|------------|
| 01 | Syntax error in configuration file | Invalid syntax in config files | Fix syntax errors, validate JSON/XML |
| 02 | Missing required configuration parameter | Required config parameter not found | Add missing parameter to config |
| 03 | Invalid configuration value | Configuration value outside valid range | Correct configuration value |
| 04 | Configuration file corrupted | Config file cannot be parsed | Restore from backup or recreate |
| 05 | Configuration file not found | Config file missing from expected location | Restore config file or recreate |

#### **Initialization Failures**
| Code | Symptom | Description | Resolution |
|------|---------|-------------|------------|
| 10 | Failed to initialize component | Component initialization failed | Check dependencies, fix initialization code |
| 11 | Initialization timeout | Component initialization exceeded timeout | Increase timeout, check for deadlocks |
| 12 | Missing initialization dependency | Required dependency not available | Install/start missing dependency |
| 13 | Initialization resource unavailable | Required resource not available | Free up resources or increase capacity |
| 14 | Initialization permission denied | Insufficient permissions for initialization | Grant required permissions |

#### **Communication Failures**
| Code | Symptom | Description | Resolution |
|------|---------|-------------|------------|
| 20 | Communication timeout | Signal not received within timeout period | Check network, increase timeout |
| 21 | Communication connection lost | Connection to target system lost | Reestablish connection |
| 22 | Communication protocol error | Invalid protocol or format | Fix protocol implementation |
| 23 | Communication signal not received | Expected signal not received | Check sender, verify addressing |
| 24 | Communication address not found | Target address not in registry | Register address or fix addressing |

#### **Data Processing Failures**
| Code | Symptom | Description | Resolution |
|------|---------|-------------|------------|
| 30 | Data processing error | Error during data processing | Fix processing logic, validate input |
| 31 | Data validation failed | Data failed validation checks | Fix data format or validation rules |
| 32 | Data corruption detected | Data integrity compromised | Restore from backup, fix corruption |
| 33 | Data format unsupported | Data format not supported | Convert format or add support |
| 34 | Data parsing error | Error parsing data | Fix parser, validate data format |

#### **Resource Failures**
| Code | Symptom | Description | Resolution |
|------|---------|-------------|------------|
| 40 | Resource unavailable | Required resource not available | Free up resources, increase capacity |
| 41 | Resource exhausted | Resource limit reached | Increase limits, optimize usage |
| 42 | Resource permission denied | Insufficient permissions for resource | Grant required permissions |
| 43 | Resource locked by another process | Resource in use by another process | Wait or force release lock |
| 44 | Resource disk space insufficient | Not enough disk space | Free up disk space |

#### **Business Logic Failures**
| Code | Symptom | Description | Resolution |
|------|---------|-------------|------------|
| 50 | Business rule validation failed | Business rule validation failed | Fix business logic, update rules |
| 51 | Workflow state invalid | Workflow in invalid state | Reset workflow state |
| 52 | Operation not allowed in current state | Operation not permitted | Change state or modify operation |
| 53 | Dependency not satisfied | Required dependency not met | Satisfy dependency requirements |

#### **External Service Failures**
| Code | Symptom | Description | Resolution |
|------|---------|-------------|------------|
| 60 | External service unavailable | External service not responding | Check service status, wait for recovery |
| 61 | External service timeout | External service response timeout | Increase timeout, check service health |
| 62 | External service authentication failed | Authentication with external service failed | Check credentials, renew tokens |
| 63 | External service rate limit exceeded | Rate limit for external service exceeded | Wait for rate limit reset |

#### **File System Failures**
| Code | Symptom | Description | Resolution |
|------|---------|-------------|------------|
| 70 | File not found | Required file missing | Restore file or recreate |
| 71 | File access denied | Insufficient permissions for file | Grant file permissions |
| 72 | File locked by another process | File in use by another process | Wait or force release lock |
| 73 | File system full | File system out of space | Free up disk space |
| 74 | File system corruption | File system corruption detected | Run file system check, restore |

#### **Database Failures**
| Code | Symptom | Description | Resolution |
|------|---------|-------------|------------|
| 80 | Database connection failed | Cannot connect to database | Check database service, fix connection |
| 81 | Database query timeout | Database query exceeded timeout | Optimize query, increase timeout |
| 82 | Database transaction failed | Database transaction failed | Check data integrity, retry transaction |
| 83 | Database constraint violation | Database constraint violated | Fix data to meet constraints |

#### **Critical System Failures**
| Code | Symptom | Description | Resolution |
|------|---------|-------------|------------|
| 90 | System crash | System crashed unexpectedly | Restart system, check logs |
| 91 | System out of memory | System ran out of memory | Increase memory, optimize usage |
| 92 | System disk full | System disk full | Free up disk space |
| 93 | System network failure | Network connectivity lost | Check network configuration |
| 94 | System hardware failure | Hardware component failed | Replace hardware component |

---

## **COMMUNICATION CALLOUTS & RADIO CODES**

### **Standard Radio Codes**
| Code | Meaning | Usage | Response Required |
|------|--------|-------|-------------------|
| 10-4 | Acknowledged - Message received and understood | General acknowledgment | No |
| 10-6 | Evidence Received - Evidence has been received and is being processed | Evidence processing | Yes |
| 10-8 | Evidence Complete - Evidence processing is complete and ready | Evidence completion | Yes |
| 10-9 | Repeat - Please repeat your last message | Request repeat | Yes |
| 10-10 | Standby - Please wait, processing in progress | Processing status | Yes |

### **Emergency Radio Codes**
| Code | Meaning | Usage | Response Required |
|------|--------|-------|-------------------|
| SOS | Emergency - System failure, immediate assistance required | Critical failures | Yes (5 sec) |
| MAYDAY | Critical failure - System is down | System crashes | Yes (5 sec) |

### **System Status Radio Codes**
| Code | Meaning | Usage | Response Required |
|------|--------|-------|-------------------|
| STATUS | Status request - Please provide system status | Health checks | Yes (30 sec) |
| ROLLCALL | Rollcall - All systems respond with status | System inventory | Yes (60 sec) |
| RADIO_CHECK | Radio check - Test communication | Connectivity test | Yes (15 sec) |

---

## **SYSTEM-SPECIFIC FAULT CODES**

### **Bus-1 (CANBUS Network)**

**System Type:** Communication Backbone  
**Address:** Bus-1  
**Parent:** None (root infrastructure)  
**Critical:** YES - Single point of failure  
**Health Monitoring:** `get_health_metrics()`

#### **Bus-1 Fault Codes**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| Bus-1-10 | Bus connection failure | Bus failed to initialize | Restart system |
| Bus-1-11 | Signal registration failure | Handler registration failed | Check handler path |
| Bus-1-12 | Initialization dependency missing | Required component missing | Check dependencies |
| Bus-1-20 | Signal routing error | Message routing failed | Check signal registry |
| Bus-1-21 | Handler execution error | Signal handler crashed | Fix handler logic |
| Bus-1-30 | Performance degradation | Processing time >100ms avg | Reduce traffic load |
| Bus-1-31 | High traffic warning | Messages >1000/sec | Throttle message rate |
| Bus-1-40 | Memory warning | Event log >10,000 entries | Clear event log |
| Bus-1-50 | Unresponsive | No heartbeat >30 seconds | Restart bus |

### **Evidence Locker Complex (1-x)**

#### **1 (Evidence Locker Main)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 1-01 | Evidence manifest syntax error | Invalid JSON in evidence manifest | Fix JSON syntax |
| 1-02 | Evidence manifest missing required fields | Required fields missing from manifest | Add missing fields |
| 1-10 | Evidence locker initialization failed | Failed to initialize evidence locker | Check dependencies |
| 1-11 | Evidence locker initialization timeout | Initialization exceeded timeout | Increase timeout |
| 1-20 | Evidence locker communication timeout | Communication timeout with other systems | Check network |
| 1-30 | Evidence processing error | Error during evidence processing | Fix processing logic |
| 1-31 | Evidence validation failed | Evidence failed validation checks | Fix evidence format |
| 1-40 | Evidence storage resource unavailable | Storage resource not available | Free up storage |
| 1-70 | Evidence file not found | Evidence file missing | Restore evidence file |
| 1-71 | Evidence file access denied | Insufficient permissions for evidence file | Grant file permissions |

#### **1.1 (Evidence Classifier)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 1.1-01 | Classification rule syntax error | Invalid syntax in classification rules | Fix rule syntax |
| 1.1-02 | Classification rule missing required fields | Required fields missing from rules | Add missing fields |
| 1.1-10 | Classifier initialization failed | Failed to initialize classifier | Check dependencies |
| 1.1-30 | Classification processing error | Error during classification | Fix classification logic |
| 1.1-31 | Classification validation failed | Classification failed validation | Fix validation rules |
| 1.1-50 | Classification business rule failed | Business rule validation failed | Fix business logic |

#### **1.2 (Evidence Identifier)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 1.2-01 | Identification rule syntax error | Invalid syntax in identification rules | Fix rule syntax |
| 1.2-10 | Identifier initialization failed | Failed to initialize identifier | Check dependencies |
| 1.2-30 | Evidence identification error | Error during identification | Fix identification logic |
| 1.2-31 | Evidence identification validation failed | Identification failed validation | Fix validation rules |
| 1.2-50 | Identification business rule failed | Business rule validation failed | Fix business logic |

#### **1.3 (Static Data Flow)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 1.3-01 | Data flow configuration syntax error | Invalid syntax in data flow config | Fix config syntax |
| 1.3-10 | Data flow initialization failed | Failed to initialize data flow | Check dependencies |
| 1.3-30 | Data flow processing error | Error during data flow processing | Fix processing logic |
| 1.3-31 | Data flow validation failed | Data flow failed validation | Fix validation rules |
| 1.3-50 | Data flow business rule failed | Business rule validation failed | Fix business logic |

#### **1.4 (Evidence Index)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 1.4-01 | Index configuration syntax error | Invalid syntax in index config | Fix config syntax |
| 1.4-10 | Index initialization failed | Failed to initialize index | Check dependencies |
| 1.4-30 | Index processing error | Error during indexing | Fix indexing logic |
| 1.4-31 | Index validation failed | Index failed validation | Fix validation rules |
| 1.4-80 | Index database connection failed | Cannot connect to index database | Check database service |

#### **1.5 (Evidence Manifest)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 1.5-01 | Manifest syntax error | Invalid syntax in manifest | Fix manifest syntax |
| 1.5-02 | Manifest missing required fields | Required fields missing from manifest | Add missing fields |
| 1.5-10 | Manifest initialization failed | Failed to initialize manifest | Check dependencies |
| 1.5-30 | Manifest processing error | Error during manifest processing | Fix processing logic |
| 1.5-31 | Manifest validation failed | Manifest failed validation | Fix validation rules |
| 1.5-70 | Manifest file not found | Manifest file missing | Restore manifest file |

#### **1.6 (Evidence Class Builder)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 1.6-01 | Class builder configuration syntax error | Invalid syntax in class builder config | Fix config syntax |
| 1.6-10 | Class builder initialization failed | Failed to initialize class builder | Check dependencies |
| 1.6-30 | Class building error | Error during class building | Fix building logic |
| 1.6-31 | Class validation failed | Class failed validation | Fix validation rules |
| 1.6-50 | Class building business rule failed | Business rule validation failed | Fix business logic |

#### **1.7 (Case Manifest Builder)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 1.7-01 | Manifest builder configuration error | Invalid syntax in manifest config | Fix config syntax |
| 1.7-10 | Manifest builder initialization failed | Failed to initialize | Check dependencies |
| 1.7-30 | Manifest building error | Error during manifest building | Fix building logic |
| 1.7-31 | Manifest validation failed | Manifest validation failed | Fix validation rules |
| 1.7-70 | Manifest file creation failed | Cannot create manifest file | Check file permissions |

#### **1.8 (OCR Processor)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 1.8-01 | OCR configuration error | Invalid syntax in OCR config | Fix config syntax |
| 1.8-10 | OCR processor initialization failed | Failed to initialize OCR | Check dependencies |
| 1.8-30 | OCR processing error | Error during OCR processing | Fix OCR logic |
| 1.8-31 | OCR validation failed | OCR output validation failed | Improve OCR quality |
| 1.8-40 | OCR engine unavailable | OCR engine not available | Install OCR engine |
| 1.8-70 | OCR input file not found | Input file missing | Check file path |

### **Warden Complex (2-x)**

#### **2 (Warden Module)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 2-1-01 | Warden configuration syntax error | Invalid syntax in Warden config | Fix config syntax |
| 2-1-02 | Warden configuration missing required fields | Required fields missing from Warden config | Add missing fields |
| 2-1-10 | Warden initialization failed | Failed to initialize Warden | Check dependencies |
| 2-1-11 | Warden initialization timeout | Warden initialization exceeded timeout | Increase timeout |
| 2-1-20 | Warden communication timeout | Communication timeout with other systems | Check network |
| 2-1-30 | Warden processing error | Error during Warden processing | Fix processing logic |
| 2-1-50 | Warden business rule failed | Business rule validation failed | Fix business logic |
| 2-1-90 | Warden system crash | Warden crashed unexpectedly | Restart Warden |

#### **2-2 (Ecosystem Controller)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 2-2-01 | ECC configuration syntax error | Invalid syntax in ECC config | Fix config syntax |
| 2-2-02 | ECC configuration missing required fields | Required fields missing from ECC config | Add missing fields |
| 2-2-10 | ECC initialization failed | Failed to initialize ECC | Check dependencies |
| 2-2-11 | ECC initialization timeout | ECC initialization exceeded timeout | Increase timeout |
| 2-2-20 | ECC communication timeout | Communication timeout with other systems | Check network |
| 2-2-30 | ECC processing error | Error during ECC processing | Fix processing logic |
| 2-2-50 | ECC business rule failed | Business rule validation failed | Fix business logic |
| 2-2-80 | ECC database connection failed | Cannot connect to ECC database | Check database service |
| 2-2-90 | ECC system crash | ECC crashed unexpectedly | Restart ECC |

#### **2-2.1 (ECC State Manager)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 2-2.1-01 | State configuration syntax error | Invalid syntax in state config | Fix config syntax |
| 2-2.1-10 | State manager initialization failed | Failed to initialize state manager | Check dependencies |
| 2-2.1-30 | State processing error | Error during state processing | Fix processing logic |
| 2-2.1-50 | State transition business rule failed | Business rule validation failed | Fix business logic |

#### **2-2.2 (ECC Dependency Tracker)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 2-2.2-01 | Dependency configuration syntax error | Invalid syntax in dependency config | Fix config syntax |
| 2-2.2-10 | Dependency tracker initialization failed | Failed to initialize dependency tracker | Check dependencies |
| 2-2.2-30 | Dependency tracking error | Error during dependency tracking | Fix tracking logic |
| 2-2.2-50 | Dependency validation business rule failed | Business rule validation failed | Fix business logic |

#### **2-2.3 (ECC Execution Order)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 2-2.3-01 | Execution order configuration syntax error | Invalid syntax in execution order config | Fix config syntax |
| 2-2.3-10 | Execution order initialization failed | Failed to initialize execution order | Check dependencies |
| 2-2.3-30 | Execution order processing error | Error during execution order processing | Fix processing logic |
| 2-2.3-50 | Execution order business rule failed | Business rule validation failed | Fix business logic |

#### **2-2.4 (ECC Permission Controller)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 2-2.4-01 | Permission configuration syntax error | Invalid syntax in permission config | Fix config syntax |
| 2-2.4-10 | Permission controller initialization failed | Failed to initialize permission controller | Check dependencies |
| 2-2.4-30 | Permission processing error | Error during permission processing | Fix processing logic |
| 2-2.4-50 | Permission validation business rule failed | Business rule validation failed | Fix business logic |

#### **2-3 (Gateway Controller)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 2-3-01 | Gateway configuration syntax error | Invalid syntax in gateway config | Fix config syntax |
| 2-3-02 | Gateway configuration missing required fields | Required fields missing from gateway config | Add missing fields |
| 2-3-10 | Gateway initialization failed | Failed to initialize gateway | Check dependencies |
| 2-3-11 | Gateway initialization timeout | Gateway initialization exceeded timeout | Increase timeout |
| 2-3-20 | Gateway communication timeout | Communication timeout with other systems | Check network |
| 2-3-30 | Gateway processing error | Error during gateway processing | Fix processing logic |
| 2-3-50 | Gateway business rule failed | Business rule validation failed | Fix business logic |
| 2-3-80 | Gateway database connection failed | Cannot connect to gateway database | Check database service |
| 2-3-90 | Gateway system crash | Gateway crashed unexpectedly | Restart gateway |

#### **2-3.1 (Gateway Signal Dispatcher)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 2-3.1-01 | Signal dispatcher configuration syntax error | Invalid syntax in signal dispatcher config | Fix config syntax |
| 2-3.1-10 | Signal dispatcher initialization failed | Failed to initialize signal dispatcher | Check dependencies |
| 2-3.1-20 | Signal dispatch communication error | Error during signal dispatch | Fix communication logic |
| 2-3.1-30 | Signal dispatch processing error | Error during signal dispatch processing | Fix processing logic |

#### **2-3.2 (Gateway Section Router)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 2-3.2-01 | Section router configuration syntax error | Invalid syntax in section router config | Fix config syntax |
| 2-3.2-10 | Section router initialization failed | Failed to initialize section router | Check dependencies |
| 2-3.2-30 | Section routing error | Error during section routing | Fix routing logic |
| 2-3.2-50 | Section routing business rule failed | Business rule validation failed | Fix business logic |

#### **2-3.3 (Gateway Evidence Pipeline)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 2-3.3-01 | Evidence pipeline configuration syntax error | Invalid syntax in evidence pipeline config | Fix config syntax |
| 2-3.3-10 | Evidence pipeline initialization failed | Failed to initialize evidence pipeline | Check dependencies |
| 2-3.3-30 | Evidence pipeline processing error | Error during evidence pipeline processing | Fix processing logic |
| 2-3.3-50 | Evidence pipeline business rule failed | Business rule validation failed | Fix business logic |

#### **2-3.4 (Gateway Bottleneck Monitor)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 2-3.4-01 | Bottleneck monitor configuration syntax error | Invalid syntax in bottleneck monitor config | Fix config syntax |
| 2-3.4-10 | Bottleneck monitor initialization failed | Failed to initialize bottleneck monitor | Check dependencies |
| 2-3.4-30 | Bottleneck monitoring error | Error during bottleneck monitoring | Fix monitoring logic |
| 2-3.4-50 | Bottleneck detection business rule failed | Business rule validation failed | Fix business logic |

### **Marshall Complex (3-x)**

#### **3 (Marshall Module)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 3-01 | Marshall configuration syntax error | Invalid syntax in Marshall config | Fix config syntax |
| 3-02 | Marshall configuration missing required fields | Required fields missing from Marshall config | Add missing fields |
| 3-10 | Marshall initialization failed | Failed to initialize Marshall | Check dependencies |
| 3-11 | Marshall initialization timeout | Marshall initialization exceeded timeout | Increase timeout |
| 3-20 | Marshall communication timeout | Communication timeout with other systems | Check network |
| 3-30 | Marshall processing error | Error during Marshall processing | Fix processing logic |
| 3-50 | Marshall business rule failed | Business rule validation failed | Fix business logic |
| 3-90 | Marshall system crash | Marshall crashed unexpectedly | Restart Marshall |

#### **3-1 (Evidence Manager)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 3-1-01 | Evidence Manager configuration syntax error | Invalid syntax in Evidence Manager config | Fix config syntax |
| 3-1-02 | Evidence Manager missing required fields | Required fields missing from config | Add missing fields |
| 3-1-10 | Evidence Manager initialization failed | Failed to initialize Evidence Manager | Check dependencies |
| 3-1-20 | Evidence Manager communication timeout | Communication timeout | Check network |
| 3-1-30 | Evidence processing error | Error during evidence processing | Fix processing logic |
| 3-1-40 | Evidence resource unavailable | Resource not available | Free up resources |
| 3-1-70 | Evidence file not found | Evidence file missing | Restore evidence file |

#### **3-2 (Evidence Checkout)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 3-2-01 | Checkout configuration error | Invalid syntax in checkout config | Fix config syntax |
| 3-2-10 | Checkout initialization failed | Failed to initialize checkout | Check dependencies |
| 3-2-20 | Checkout communication timeout | Communication timeout | Check network |
| 3-2-30 | Evidence delivery error | Error during evidence delivery | Fix delivery logic |
| 3-2-31 | Section routing failed | Section routing failed | Check section addresses |
| 3-2-50 | Checkout business rule failed | Business rule failed | Fix business logic |

#### **3-3 (Gateway - Marshall)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 3-3-01 | Gateway configuration error | Invalid syntax in gateway config | Fix config syntax |
| 3-3-10 | Gateway initialization failed | Failed to initialize gateway | Check dependencies |
| 3-3-20 | Gateway communication timeout | Communication timeout | Check network |
| 3-3-30 | File processing error | Error during file processing | Fix processing logic |
| 3-3-31 | Report generation failed | Report generation failed | Check report generator |
| 3-3-50 | Gateway business rule failed | Business rule failed | Fix business logic |

### **Section Engines (4-x)**

#### **4-1 (Section 1 - Case Profile)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 4-1-01 | Section 1 configuration error | Invalid syntax in section config | Fix config syntax |
| 4-1-10 | Section 1 initialization failed | Failed to initialize section | Check dependencies |
| 4-1-20 | Section 1 communication timeout | Communication timeout | Check network |
| 4-1-30 | Section 1 processing error | Error during section processing | Fix processing logic |
| 4-1-31 | Section 1 validation failed | Section validation failed | Fix validation rules |
| 4-1-50 | Section 1 business rule failed | Business rule failed | Fix business logic |

#### **4-2 (Section 2 - Investigation Planning)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 4-2-01 | Section 2 configuration error | Invalid syntax in section config | Fix config syntax |
| 4-2-10 | Section 2 initialization failed | Failed to initialize section | Check dependencies |
| 4-2-20 | Section 2 communication timeout | Communication timeout | Check network |
| 4-2-30 | Section 2 processing error | Error during section processing | Fix processing logic |
| 4-2-50 | Section 2 business rule failed | Business rule failed | Fix business logic |

#### **4-3 (Section 3 - Surveillance Operations)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 4-3-01 | Section 3 configuration error | Invalid syntax in section config | Fix config syntax |
| 4-3-10 | Section 3 initialization failed | Failed to initialize section | Check dependencies |
| 4-3-20 | Section 3 communication timeout | Communication timeout | Check network |
| 4-3-30 | Section 3 processing error | Error during section processing | Fix processing logic |
| 4-3-50 | Section 3 business rule failed | Business rule failed | Fix business logic |

#### **4-4 (Section 4 - Session Review)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 4-4-01 | Section 4 configuration error | Invalid syntax in section config | Fix config syntax |
| 4-4-10 | Section 4 initialization failed | Failed to initialize section | Check dependencies |
| 4-4-20 | Section 4 communication timeout | Communication timeout | Check network |
| 4-4-30 | Section 4 processing error | Error during section processing | Fix processing logic |
| 4-4-50 | Section 4 business rule failed | Business rule failed | Fix business logic |

#### **4-5 (Section 5 - Document Inventory)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 4-5-01 | Section 5 configuration error | Invalid syntax in section config | Fix config syntax |
| 4-5-10 | Section 5 initialization failed | Failed to initialize section | Check dependencies |
| 4-5-20 | Section 5 communication timeout | Communication timeout | Check network |
| 4-5-30 | Section 5 processing error | Error during section processing | Fix processing logic |
| 4-5-50 | Section 5 business rule failed | Business rule failed | Fix business logic |

#### **4-6 (Section 6 - Billing Summary)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 4-6-01 | Section 6 configuration error | Invalid syntax in section config | Fix config syntax |
| 4-6-10 | Section 6 initialization failed | Failed to initialize section | Check dependencies |
| 4-6-20 | Section 6 communication timeout | Communication timeout | Check network |
| 4-6-30 | Section 6 processing error | Error during section processing | Fix processing logic |
| 4-6-50 | Section 6 business rule failed | Business rule failed | Fix business logic |

#### **4-7 (Section 7 - Conclusion)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 4-7-01 | Section 7 configuration error | Invalid syntax in section config | Fix config syntax |
| 4-7-10 | Section 7 initialization failed | Failed to initialize section | Check dependencies |
| 4-7-20 | Section 7 communication timeout | Communication timeout | Check network |
| 4-7-30 | Section 7 processing error | Error during section processing | Fix processing logic |
| 4-7-50 | Section 7 business rule failed | Business rule failed | Fix business logic |

#### **4-8 (Section 8 - Media Documentation)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 4-8-01 | Section 8 configuration error | Invalid syntax in section config | Fix config syntax |
| 4-8-10 | Section 8 initialization failed | Failed to initialize section | Check dependencies |
| 4-8-20 | Section 8 communication timeout | Communication timeout | Check network |
| 4-8-30 | Section 8 processing error | Error during section processing | Fix processing logic |
| 4-8-50 | Section 8 business rule failed | Business rule failed | Fix business logic |

### **Mission Debrief Complex (5-x)**

#### **5 (Mission Debrief Module)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 5-01 | Mission Debrief configuration syntax error | Invalid syntax in config | Fix config syntax |
| 5-02 | Mission Debrief missing required fields | Required fields missing | Add missing fields |
| 5-10 | Mission Debrief initialization failed | Failed to initialize | Check dependencies |
| 5-20 | Mission Debrief communication timeout | Communication timeout | Check network |
| 5-30 | Mission Debrief processing error | Error during processing | Fix processing logic |
| 5-50 | Mission Debrief business rule failed | Business rule failed | Fix business logic |
| 5-90 | Mission Debrief system crash | System crashed | Restart system |

#### **5-1 (Debrief Manager)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 5-1-01 | Debrief Manager configuration error | Invalid syntax in config | Fix config syntax |
| 5-1-10 | Debrief Manager initialization failed | Failed to initialize | Check dependencies |
| 5-1-20 | Debrief Manager communication timeout | Communication timeout | Check network |
| 5-1-30 | Artifact generation error | Error during artifact generation | Fix generation logic |
| 5-1-31 | Framework execution failed | Framework execution failed | Check framework dependencies |
| 5-1-40 | Resource unavailable | Resource not available | Free up resources |
| 5-1-50 | Business rule failed | Business rule failed | Fix business logic |

#### **5-1.1 (Cover Page Framework)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 5-1.1-01 | Cover Page configuration error | Invalid syntax in CP config | Fix config syntax |
| 5-1.1-10 | Cover Page initialization failed | Failed to initialize CP framework | Check dependencies |
| 5-1.1-20 | Cover Page communication timeout | Communication timeout | Check network |
| 5-1.1-30 | Cover Page generation error | Error during CP generation | Fix generation logic |
| 5-1.1-31 | Branding asset validation failed | Branding assets failed validation | Check asset files |
| 5-1.1-50 | Cover Page business rule failed | Business rule failed | Fix business logic |

#### **5-1.2 (Disclosure Page Framework)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 5-1.2-01 | Disclosure Page configuration error | Invalid syntax in DP config | Fix config syntax |
| 5-1.2-10 | Disclosure Page initialization failed | Failed to initialize DP framework | Check dependencies |
| 5-1.2-20 | Disclosure Page communication timeout | Communication timeout | Check network |
| 5-1.2-30 | Disclosure generation error | Error during DP generation | Fix generation logic |
| 5-1.2-31 | Disclaimer validation failed | Disclaimer validation failed | Check legal disclaimers |
| 5-1.2-50 | Disclosure business rule failed | Business rule failed | Fix business logic |

#### **5.1 (Report Generator Tool)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 5.1-01 | Report Generator import failed | Cannot import report generator | Check dependencies |
| 5.1-10 | Report Generator initialization failed | Failed to initialize | Check configuration |
| 5.1-30 | PDF assembly error | Error during PDF assembly | Fix assembly logic |
| 5.1-31 | Report formatting failed | Report formatting failed | Check template files |
| 5.1-70 | Output file creation failed | Cannot create output file | Check file permissions |

#### **5.2 (Digital Signing Tool)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 5.2-01 | Digital signature import failed | Cannot import signature system | Check dependencies |
| 5.2-10 | Signature system initialization failed | Failed to initialize | Check certificate files |
| 5.2-30 | Signature generation error | Error during signature generation | Check private key |
| 5.2-31 | Signature verification failed | Signature verification failed | Check certificate validity |
| 5.2-70 | Certificate file not found | Certificate file missing | Restore certificate |

#### **5.3 (Template Engine Tool)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 5.3-01 | Template engine import failed | Cannot import template system | Check dependencies |
| 5.3-10 | Template engine initialization failed | Failed to initialize | Check template directory |
| 5.3-30 | Template rendering error | Error during template rendering | Fix template syntax |
| 5.3-31 | Variable substitution failed | Variable substitution failed | Check variable mapping |
| 5.3-70 | Template file not found | Template file missing | Restore template file |

#### **5.4 (Watermark Tool)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 5.4-01 | Watermark tool import failed | Cannot import watermark system | Check dependencies |
| 5.4-10 | Watermark initialization failed | Failed to initialize | Check watermark assets |
| 5.4-30 | Watermark generation error | Error during watermark generation | Fix watermark logic |
| 5.4-31 | Watermark application failed | Watermark application failed | Check document format |
| 5.4-70 | Watermark asset not found | Watermark asset missing | Restore asset file |

#### **5-2 (The Librarian)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 5-2-01 | Librarian configuration error | Invalid syntax in config | Fix config syntax |
| 5-2-10 | Librarian initialization failed | Failed to initialize | Check dependencies |
| 5-2-20 | Librarian communication timeout | Communication timeout | Check network |
| 5-2-30 | Narrative assembly error | Error during narrative assembly | Fix assembly logic |
| 5-2-31 | Template processing failed | Template processing failed | Check template dependencies |
| 5-2-50 | Court-safe language rule failed | Language validation failed | Fix language rules |

#### **5-2.1 (Template Cache)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 5-2.1-01 | Template cache configuration error | Invalid syntax in cache config | Fix config syntax |
| 5-2.1-10 | Template cache initialization failed | Failed to initialize cache | Check dependencies |
| 5-2.1-30 | Template cache error | Error accessing template cache | Fix cache logic |
| 5-2.1-70 | Template file not found | Template file missing from cache | Restore template file |

#### **5-2.2 (Document Processor)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 5-2.2-01 | Document processor configuration error | Invalid syntax in processor config | Fix config syntax |
| 5-2.2-10 | Document processor initialization failed | Failed to initialize processor | Check dependencies |
| 5-2.2-30 | Document processing error | Error during document processing | Fix processing logic |
| 5-2.2-70 | Document file not found | Document file missing | Check file path |

#### **5-2.3 (OSINT Engine)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 5-2.3-01 | OSINT configuration error | Invalid syntax in OSINT config | Fix config syntax |
| 5-2.3-10 | OSINT engine initialization failed | Failed to initialize OSINT | Check dependencies |
| 5-2.3-20 | OSINT communication timeout | OSINT API timeout | Check API connectivity |
| 5-2.3-30 | OSINT processing error | Error during OSINT processing | Fix processing logic |
| 5-2.3-60 | OSINT API connection failed | Cannot connect to OSINT API | Check API credentials |

#### **5-2.4 (Table of Contents Framework)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 5-2.4-01 | TOC configuration error | Invalid syntax in TOC config | Fix config syntax |
| 5-2.4-10 | TOC initialization failed | Failed to initialize TOC framework | Check dependencies |
| 5-2.4-20 | TOC communication timeout | Communication timeout | Check network |
| 5-2.4-30 | TOC generation error | Error during TOC generation | Fix generation logic |
| 5-2.4-31 | Section indexing failed | Section indexing failed | Check section data |
| 5-2.4-50 | TOC business rule failed | Business rule failed | Fix business logic |

### **War Room Complex (6-x)**

#### **6-1 (Dev Environment)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 6-1-01 | Dev environment configuration error | Invalid syntax in dev config | Fix config syntax |
| 6-1-10 | Dev environment initialization failed | Failed to initialize dev environment | Check dependencies |
| 6-1-30 | Development tool error | Error using development tool | Fix tool configuration |
| 6-1-40 | Dev resource unavailable | Development resource not available | Install required tools |

#### **6-2 (Tool Dependencies)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 6-2-01 | Dependency configuration error | Invalid syntax in dependency config | Fix config syntax |
| 6-2-10 | Dependency initialization failed | Failed to initialize dependencies | Check dependency availability |
| 6-2-30 | Dependency resolution error | Error resolving dependencies | Fix dependency conflicts |
| 6-2-40 | Missing dependency | Required dependency not found | Install missing dependency |

### **GUI Complex (GUI-1, 7-x)**

#### **GUI-1 (Enhanced Functional GUI)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| GUI-1-01 | GUI configuration error | Invalid syntax in GUI config | Fix config syntax |
| GUI-1-10 | GUI initialization failed | Failed to initialize GUI | Check dependencies |
| GUI-1-20 | GUI communication timeout | Communication timeout | Check network |
| GUI-1-30 | GUI rendering error | Error rendering interface | Fix rendering logic |
| GUI-1-40 | Display resource unavailable | Display resource not available | Check display settings |

---

## **COMMUNICATION PROTOCOLS**

### **Signal Format**
```python
{
    "signal_id": "unique_signal_id",
    "caller_address": "source_address",
    "target_address": "destination_address", 
    "bus_address": "Bus-1",
    "signal_type": "communication|response|sos_fault|rollcall|radio_check",
    "radio_code": "10-4|10-6|10-8|10-9|10-10|SOS|STATUS|ROLLCALL|RADIO_CHECK",
    "message": "human_readable_message",
    "payload": {
        "operation": "operation_type",
        "data": {...},
        "timestamp": "ISO_timestamp"
    },
    "response_expected": true|false,
    "timeout": timeout_seconds
}
```

### **Response Format**
```python
{
    "signal_id": "response_to_signal_id",
    "caller_address": "responder_address",
    "target_address": "original_caller_address",
    "bus_address": "Bus-1", 
    "signal_type": "response",
    "radio_code": "10-4|10-6|10-8|10-9|10-10",
    "message": "response_message",
    "payload": {
        "status": "success|failure|error",
        "data": {...},
        "timestamp": "ISO_timestamp"
    }
}
```

### **SOS Fault Format**
```python
{
    "signal_id": "sos_fault_id",
    "caller_address": "fault_reporting_address",
    "target_address": "Bus-1",
    "bus_address": "Bus-1",
    "signal_type": "sos_fault",
    "radio_code": "SOS",
    "message": "SOS fault description",
    "payload": {
        "operation": "sos_fault",
        "fault_code": "ADDRESS-XX-LOCATION",
        "description": "fault_description",
        "details": {...},
        "timestamp": "ISO_timestamp"
    },
    "response_expected": true,
    "timeout": 5
}
```

---

## **DIAGNOSTIC PROCEDURES**

### **Radio Check Procedure**
1. Send `RADIO_CHECK` signal to target system
2. Wait for response (15 second timeout)
3. Log response time and status
4. Report diagnostic code if fault detected

### **Rollcall Procedure**
1. Broadcast `ROLLCALL` signal to all systems
2. Wait for responses (60 second timeout)
3. Log responding and non-responding systems
4. Report missing systems with diagnostic codes

### **SOS Fault Procedure**
1. System detects fault and generates diagnostic code
2. Send `SOS` signal to Bus-1 with fault details
3. Bus-1 routes to GUI Error Display Interface (7-1.7)
4. Log fault in diagnostic system
5. Alert system administrators

### **Health Monitor Procedure**
1. Continuous monitoring of all system addresses
2. Send `STATUS` requests every 30 seconds
3. Update health status (OK/ERROR/FAILURE)
4. Display diagnostic codes for faults
5. Alert on status changes

---

## **MAINTENANCE & UPDATES**

### **Protocol Versioning**
- **Version**: 1.0.0
- **Last Updated**: 2025-10-05
- **Next Review**: 2025-11-05

### **Change Log**
- **2025-10-05**: Initial protocol definition
- **2025-10-05**: Added diagnostic codes with line numbers
- **2025-10-05**: Integrated with existing health monitor

### **Contact Information**
- **System Administrator**: [Contact Info]
- **Technical Support**: [Contact Info]
- **Emergency Contact**: [Contact Info]

---

**END OF MASTER DIAGNOSTIC PROTOCOL**

This document serves as the definitive reference for all diagnostic operations within the Central Command system. All modules must adhere to these protocols as their Standard Operating Procedure (SOP).
