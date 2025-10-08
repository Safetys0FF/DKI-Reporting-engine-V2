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
| 1-1 | Evidence Locker Main | evidence_locker_main.EvidenceLocker | - | ACTIVE | - |
| 1-1.1 | Evidence Classifier | evidence_classifier.EvidenceClassifier | 1-1 | ACTIVE | - |
| 1-1.2 | Evidence Identifier | evidence_identifier.EvidenceIdentifier | 1-1 | ACTIVE | - |
| 1-1.3 | Static Data Flow | static_data_flow.StaticDataFlow | 1-1 | ACTIVE | - |
| 1-1.4 | Evidence Index | evidence_index.EvidenceIndex | 1-1 | ACTIVE | - |
| 1-1.5 | Evidence Manifest | evidence_manifest.EvidenceManifest | 1-1 | ACTIVE | - |
| 1-1.6 | Evidence Class Builder | evidence_class_builder.EvidenceClassBuilder | 1-1 | ACTIVE | - |
| 1-1.7 | Case Manifest Builder | case_manifest_builder.CaseManifestBuilder | 1-1 | ACTIVE | - |
| 1-1.8 | OCR Processor | ocr_processor.OCRProcessor | 1-1 | ACTIVE | - |

### **Warden Complex (2-x)**
| Address | System Name | Handler | Parent | Status | Last Check |
|---------|-------------|---------|--------|--------|------------|
| 2-1 | Ecosystem Controller | ecosystem_controller.EcosystemController | - | ACTIVE | - |
| 2-1.1 | ECC State Manager | ecc_state_manager.ECCStateManager | 2-1 | ACTIVE | - |
| 2-1.2 | ECC Dependency Tracker | ecc_dependency_tracker.ECCDependencyTracker | 2-1 | ACTIVE | - |
| 2-1.3 | ECC Execution Order | ecc_execution_order.ECCExecutionOrder | 2-1 | ACTIVE | - |
| 2-1.4 | ECC Permission Controller | ecc_permission_controller.ECCPermissionController | 2-1 | ACTIVE | - |
| 2-2 | Gateway Controller | gateway_controller.GatewayController | - | ACTIVE | - |
| 2-2.1 | Gateway Signal Dispatcher | gateway_signal_dispatcher.GatewaySignalDispatcher | 2-2 | ACTIVE | - |
| 2-2.2 | Gateway Section Router | gateway_section_router.GatewaySectionRouter | 2-2 | ACTIVE | - |
| 2-2.3 | Gateway Evidence Pipeline | gateway_evidence_pipeline.GatewayEvidencePipeline | 2-2 | ACTIVE | - |
| 2-2.4 | Gateway Bottleneck Monitor | gateway_bottleneck_monitor.GatewayBottleneckMonitor | 2-2 | ACTIVE | - |

### **Mission Debrief Complex (3-x)**
| Address | System Name | Handler | Parent | Status | Last Check |
|---------|-------------|---------|--------|--------|------------|
| 3-1 | Mission Debrief Manager | mission_debrief_manager.MissionDebriefManager | - | ACTIVE | - |
| 3-1.1 | Report Generator | report_generator.ReportGenerator | 3-1 | ACTIVE | - |
| 3-1.2 | Digital Signing | digital_signing.DigitalSigning | 3-1 | ACTIVE | - |
| 3-1.3 | Template Engine | template_engine.TemplateEngine | 3-1 | ACTIVE | - |
| 3-1.4 | Watermark System | watermark_system.WatermarkSystem | 3-1 | ACTIVE | - |
| 3-2 | The Librarian | narrative_assembler.NarrativeAssembler | - | ACTIVE | - |
| 3-2.1 | Narrative Assembler | narrative_assembler.NarrativeAssembler | 3-2 | ACTIVE | - |
| 3-2.2 | Template Cache | template_cache.TemplateCache | 3-2 | ACTIVE | - |
| 3-2.3 | Document Processor | document_processor.DocumentProcessor | 3-2 | ACTIVE | - |
| 3-2.4 | OSINT Engine | osint_engine.OSINTEngine | 3-2 | ACTIVE | - |

### **Analyst Deck Complex (4-x)**
| Address | System Name | Handler | Parent | Status | Last Check |
|---------|-------------|---------|--------|--------|------------|
| 4-1 | Section 1 - Case Profile | section_1_framework.Section1Framework | - | ACTIVE | - |
| 4-2 | Section 2 - Investigation Planning | section_2_framework.Section2Framework | - | ACTIVE | - |
| 4-3 | Section 3 - Surveillance Operations | section_3_framework.Section3Framework | - | ACTIVE | - |
| 4-4 | Section 4 - Session Review | section_4_framework.Section4Framework | - | ACTIVE | - |
| 4-5 | Section 5 - Document Inventory | section_5_framework.Section5Framework | - | ACTIVE | - |
| 4-6 | Section 6 - Billing Summary | section_6_framework.Section6Framework | - | ACTIVE | - |
| 4-7 | Section 7 - Legal Compliance | section_7_framework.Section7Framework | - | ACTIVE | - |
| 4-8 | Section 8 - Media Documentation | section_8_framework.Section8Framework | - | ACTIVE | - |
| 4-CP | Cover Page | section_cp_framework.SectionCPFramework | - | ACTIVE | - |
| 4-TOC | Table of Contents | section_toc_framework.SectionTOCFramework | - | ACTIVE | - |
| 4-DP | Disclosure Page | section_dp_framework.SectionDPFramework | - | ACTIVE | - |

### **Marshall Complex (5-x)**
| Address | System Name | Handler | Parent | Status | Last Check |
|---------|-------------|---------|--------|--------|------------|
| 5-1 | Gateway | gateway.Gateway | - | ACTIVE | - |
| 5-2 | Evidence Manager | evidence_manager.EvidenceManager | - | ACTIVE | - |
| 5-3 | Section Controller | section_controller.SectionController | - | ACTIVE | - |

### **War Room Complex (6-x)**
| Address | System Name | Handler | Parent | Status | Last Check |
|---------|-------------|---------|--------|--------|------------|
| 6-1 | Dev Environment | dev_environment.DevEnvironment | - | ACTIVE | - |
| 6-2 | Tool Dependencies | tool_dependencies.ToolDependencies | - | ACTIVE | - |

### **Enhanced Functional GUI (7-x)**
| Address | System Name | Handler | Parent | Status | Last Check |
|---------|-------------|---------|--------|--------|------------|
| 7-1 | Enhanced Functional GUI | enhanced_functional_gui.EnhancedFunctionalGUI | - | ACTIVE | - |
| 7-1.1 | User Interface Controller | ui_controller.UIController | 7-1 | ACTIVE | - |
| 7-1.2 | Case Management Interface | case_management_interface.CaseManagementInterface | 7-1 | ACTIVE | - |
| 7-1.3 | Evidence Display Interface | evidence_display_interface.EvidenceDisplayInterface | 7-1 | ACTIVE | - |
| 7-1.4 | Section Review Interface | section_review_interface.SectionReviewInterface | 7-1 | ACTIVE | - |
| 7-1.5 | Report Generation Interface | report_generation_interface.ReportGenerationInterface | 7-1 | ACTIVE | - |
| 7-1.6 | System Status Interface | system_status_interface.SystemStatusInterface | 7-1 | ACTIVE | - |
| 7-1.7 | Error Display Interface | error_display_interface.ErrorDisplayInterface | 7-1 | ACTIVE | - |
| 7-1.8 | Progress Monitoring Interface | progress_monitoring_interface.ProgressMonitoringInterface | 7-1 | ACTIVE | - |
| 7-1.9 | Health Monitor | health_monitor.HealthMonitor | 7-1 | ACTIVE | - |

### **General Systems**
| Address | System Name | Handler | Parent | Status | Last Check |
|---------|-------------|---------|--------|--------|------------|
| GEN-2.924 | Case Management Panel | F:\The Central Command\Command Center\Plug-ins\case_management_panel.py | - | ACTIVE | - |
| GEN-2.249 | Case Management Panel | F:\The Central Command\Command Center\Plug-ins\case_management_panel.py | - | ACTIVE | - |
| GEN-2.367 | Case Management Panel | F:\The Central Command\Command Center\Plug-ins\case_management_panel.py | - | ACTIVE | - |
| GEN-2.381 | Case Management Panel | F:\The Central Command\Command Center\Plug-ins\case_management_panel.py | - | ACTIVE | - |
| GEN-2.908 | Case Management Panel | F:\The Central Command\Command Center\Plug-ins\case_management_panel.py | - | ACTIVE | - |
| GEN-2.973 | Case Management Panel | F:\The Central Command\Command Center\Plug-ins\case_management_panel.py | - | ACTIVE | - |
| GEN-2.798 | Case Management Panel | F:\The Central Command\Command Center\Plug-ins\case_management_panel.py | None | ACTIVE | - |
| GEN-2.97 | Case Management Panel | F:\The Central Command\Command Center\Plug-ins\case_management_panel.py | None | ACTIVE | - |

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

### **Evidence Locker Complex (1-x)**

#### **1-1 (Evidence Locker Main)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 1-1-01 | Evidence manifest syntax error | Invalid JSON in evidence manifest | Fix JSON syntax |
| 1-1-02 | Evidence manifest missing required fields | Required fields missing from manifest | Add missing fields |
| 1-1-10 | Evidence locker initialization failed | Failed to initialize evidence locker | Check dependencies |
| 1-1-11 | Evidence locker initialization timeout | Initialization exceeded timeout | Increase timeout |
| 1-1-20 | Evidence locker communication timeout | Communication timeout with other systems | Check network |
| 1-1-30 | Evidence processing error | Error during evidence processing | Fix processing logic |
| 1-1-31 | Evidence validation failed | Evidence failed validation checks | Fix evidence format |
| 1-1-40 | Evidence storage resource unavailable | Storage resource not available | Free up storage |
| 1-1-70 | Evidence file not found | Evidence file missing | Restore evidence file |
| 1-1-71 | Evidence file access denied | Insufficient permissions for evidence file | Grant file permissions |

#### **1-1.1 (Evidence Classifier)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 1-1.1-01 | Classification rule syntax error | Invalid syntax in classification rules | Fix rule syntax |
| 1-1.1-02 | Classification rule missing required fields | Required fields missing from rules | Add missing fields |
| 1-1.1-10 | Classifier initialization failed | Failed to initialize classifier | Check dependencies |
| 1-1.1-30 | Classification processing error | Error during classification | Fix classification logic |
| 1-1.1-31 | Classification validation failed | Classification failed validation | Fix validation rules |
| 1-1.1-50 | Classification business rule failed | Business rule validation failed | Fix business logic |

#### **1-1.2 (Evidence Identifier)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 1-1.2-01 | Identification rule syntax error | Invalid syntax in identification rules | Fix rule syntax |
| 1-1.2-10 | Identifier initialization failed | Failed to initialize identifier | Check dependencies |
| 1-1.2-30 | Evidence identification error | Error during identification | Fix identification logic |
| 1-1.2-31 | Evidence identification validation failed | Identification failed validation | Fix validation rules |
| 1-1.2-50 | Identification business rule failed | Business rule validation failed | Fix business logic |

#### **1-1.3 (Static Data Flow)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 1-1.3-01 | Data flow configuration syntax error | Invalid syntax in data flow config | Fix config syntax |
| 1-1.3-10 | Data flow initialization failed | Failed to initialize data flow | Check dependencies |
| 1-1.3-30 | Data flow processing error | Error during data flow processing | Fix processing logic |
| 1-1.3-31 | Data flow validation failed | Data flow failed validation | Fix validation rules |
| 1-1.3-50 | Data flow business rule failed | Business rule validation failed | Fix business logic |

#### **1-1.4 (Evidence Index)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 1-1.4-01 | Index configuration syntax error | Invalid syntax in index config | Fix config syntax |
| 1-1.4-10 | Index initialization failed | Failed to initialize index | Check dependencies |
| 1-1.4-30 | Index processing error | Error during indexing | Fix indexing logic |
| 1-1.4-31 | Index validation failed | Index failed validation | Fix validation rules |
| 1-1.4-80 | Index database connection failed | Cannot connect to index database | Check database service |

#### **1-1.5 (Evidence Manifest)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 1-1.5-01 | Manifest syntax error | Invalid syntax in manifest | Fix manifest syntax |
| 1-1.5-02 | Manifest missing required fields | Required fields missing from manifest | Add missing fields |
| 1-1.5-10 | Manifest initialization failed | Failed to initialize manifest | Check dependencies |
| 1-1.5-30 | Manifest processing error | Error during manifest processing | Fix processing logic |
| 1-1.5-31 | Manifest validation failed | Manifest failed validation | Fix validation rules |
| 1-1.5-70 | Manifest file not found | Manifest file missing | Restore manifest file |

#### **1-1.6 (Evidence Class Builder)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 1-1.6-01 | Class builder configuration syntax error | Invalid syntax in class builder config | Fix config syntax |
| 1-1.6-10 | Class builder initialization failed | Failed to initialize class builder | Check dependencies |
| 1-1.6-30 | Class building error | Error during class building | Fix building logic |
| 1-1.6-31 | Class validation failed | Class failed validation | Fix validation rules |
| 1-1.6-50 | Class building business rule failed | Business rule validation failed | Fix business logic |

### **Warden Complex (2-x)**

#### **2-1 (Ecosystem Controller)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 2-1-01 | ECC configuration syntax error | Invalid syntax in ECC config | Fix config syntax |
| 2-1-02 | ECC configuration missing required fields | Required fields missing from ECC config | Add missing fields |
| 2-1-10 | ECC initialization failed | Failed to initialize ECC | Check dependencies |
| 2-1-11 | ECC initialization timeout | ECC initialization exceeded timeout | Increase timeout |
| 2-1-20 | ECC communication timeout | Communication timeout with other systems | Check network |
| 2-1-30 | ECC processing error | Error during ECC processing | Fix processing logic |
| 2-1-50 | ECC business rule failed | Business rule validation failed | Fix business logic |
| 2-1-80 | ECC database connection failed | Cannot connect to ECC database | Check database service |
| 2-1-90 | ECC system crash | ECC crashed unexpectedly | Restart ECC |

#### **2-1.1 (ECC State Manager)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 2-1.1-01 | State configuration syntax error | Invalid syntax in state config | Fix config syntax |
| 2-1.1-10 | State manager initialization failed | Failed to initialize state manager | Check dependencies |
| 2-1.1-30 | State processing error | Error during state processing | Fix processing logic |
| 2-1.1-50 | State transition business rule failed | Business rule validation failed | Fix business logic |

#### **2-1.2 (ECC Dependency Tracker)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 2-1.2-01 | Dependency configuration syntax error | Invalid syntax in dependency config | Fix config syntax |
| 2-1.2-10 | Dependency tracker initialization failed | Failed to initialize dependency tracker | Check dependencies |
| 2-1.2-30 | Dependency tracking error | Error during dependency tracking | Fix tracking logic |
| 2-1.2-50 | Dependency validation business rule failed | Business rule validation failed | Fix business logic |

#### **2-1.3 (ECC Execution Order)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 2-1.3-01 | Execution order configuration syntax error | Invalid syntax in execution order config | Fix config syntax |
| 2-1.3-10 | Execution order initialization failed | Failed to initialize execution order | Check dependencies |
| 2-1.3-30 | Execution order processing error | Error during execution order processing | Fix processing logic |
| 2-1.3-50 | Execution order business rule failed | Business rule validation failed | Fix business logic |

#### **2-1.4 (ECC Permission Controller)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 2-1.4-01 | Permission configuration syntax error | Invalid syntax in permission config | Fix config syntax |
| 2-1.4-10 | Permission controller initialization failed | Failed to initialize permission controller | Check dependencies |
| 2-1.4-30 | Permission processing error | Error during permission processing | Fix processing logic |
| 2-1.4-50 | Permission validation business rule failed | Business rule validation failed | Fix business logic |

#### **2-2 (Gateway Controller)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 2-2-01 | Gateway configuration syntax error | Invalid syntax in gateway config | Fix config syntax |
| 2-2-02 | Gateway configuration missing required fields | Required fields missing from gateway config | Add missing fields |
| 2-2-10 | Gateway initialization failed | Failed to initialize gateway | Check dependencies |
| 2-2-11 | Gateway initialization timeout | Gateway initialization exceeded timeout | Increase timeout |
| 2-2-20 | Gateway communication timeout | Communication timeout with other systems | Check network |
| 2-2-30 | Gateway processing error | Error during gateway processing | Fix processing logic |
| 2-2-50 | Gateway business rule failed | Business rule validation failed | Fix business logic |
| 2-2-80 | Gateway database connection failed | Cannot connect to gateway database | Check database service |
| 2-2-90 | Gateway system crash | Gateway crashed unexpectedly | Restart gateway |

#### **2-2.1 (Gateway Signal Dispatcher)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 2-2.1-01 | Signal dispatcher configuration syntax error | Invalid syntax in signal dispatcher config | Fix config syntax |
| 2-2.1-10 | Signal dispatcher initialization failed | Failed to initialize signal dispatcher | Check dependencies |
| 2-2.1-20 | Signal dispatch communication error | Error during signal dispatch | Fix communication logic |
| 2-2.1-30 | Signal dispatch processing error | Error during signal dispatch processing | Fix processing logic |

#### **2-2.2 (Gateway Section Router)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 2-2.2-01 | Section router configuration syntax error | Invalid syntax in section router config | Fix config syntax |
| 2-2.2-10 | Section router initialization failed | Failed to initialize section router | Check dependencies |
| 2-2.2-30 | Section routing error | Error during section routing | Fix routing logic |
| 2-2.2-50 | Section routing business rule failed | Business rule validation failed | Fix business logic |

#### **2-2.3 (Gateway Evidence Pipeline)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 2-2.3-01 | Evidence pipeline configuration syntax error | Invalid syntax in evidence pipeline config | Fix config syntax |
| 2-2.3-10 | Evidence pipeline initialization failed | Failed to initialize evidence pipeline | Check dependencies |
| 2-2.3-30 | Evidence pipeline processing error | Error during evidence pipeline processing | Fix processing logic |
| 2-2.3-50 | Evidence pipeline business rule failed | Business rule validation failed | Fix business logic |

#### **2-2.4 (Gateway Bottleneck Monitor)**
| Fault Code | Symptom | Description | Resolution |
|------------|---------|-------------|------------|
| 2-2.4-01 | Bottleneck monitor configuration syntax error | Invalid syntax in bottleneck monitor config | Fix config syntax |
| 2-2.4-10 | Bottleneck monitor initialization failed | Failed to initialize bottleneck monitor | Check dependencies |
| 2-2.4-30 | Bottleneck monitoring error | Error during bottleneck monitoring | Fix monitoring logic |
| 2-2.4-50 | Bottleneck detection business rule failed | Business rule validation failed | Fix business logic |

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