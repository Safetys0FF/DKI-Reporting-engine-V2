# System Address Diagnostic Codes
## Date: October 5, 2025

## **Diagnostic Code Format: [COMPONENT_ADDRESS-XX-LOCATION]**

Where:
- **COMPONENT_ADDRESS** = System address (1-1, 2-1, 3-1, etc.)
- **XX** = Failure code (01-99)
- **LOCATION** = Error location (line number or range)

---

## **COMMON FAILURE CODES (XX):**

### **Syntax/Configuration Errors**
- **01**: Syntax error in configuration file
- **02**: Missing required configuration parameter
- **03**: Invalid configuration value
- **04**: Configuration file corrupted
- **05**: Configuration file not found

### **Initialization Failures**
- **10**: Failed to initialize component
- **11**: Initialization timeout
- **12**: Missing initialization dependency
- **13**: Initialization resource unavailable
- **14**: Initialization permission denied

### **Communication Failures**
- **20**: Communication timeout
- **21**: Communication connection lost
- **22**: Communication protocol error
- **23**: Communication signal not received
- **24**: Communication address not found

### **Data Processing Failures**
- **30**: Data processing error
- **31**: Data validation failed
- **32**: Data corruption detected
- **33**: Data format unsupported
- **34**: Data parsing error

### **Resource Failures**
- **40**: Resource unavailable
- **41**: Resource exhausted
- **42**: Resource permission denied
- **43**: Resource locked by another process
- **44**: Resource disk space insufficient

### **Business Logic Failures**
- **50**: Business rule validation failed
- **51**: Workflow state invalid
- **52**: Operation not allowed in current state
- **53**: Dependency not satisfied

### **External Service Failures**
- **60**: External service unavailable
- **61**: External service timeout
- **62**: External service authentication failed
- **63**: External service rate limit exceeded

### **File System Failures**
- **70**: File not found
- **71**: File access denied
- **72**: File locked by another process
- **73**: File system full
- **74**: File system corruption

### **Database Failures**
- **80**: Database connection failed
- **81**: Database query timeout
- **82**: Database transaction failed
- **83**: Database constraint violation

### **Critical System Failures**
- **90**: System crash
- **91**: System out of memory
- **92**: System disk full
- **93**: System network failure
- **94**: System hardware failure

---

## **SYSTEM-SPECIFIC DIAGNOSTIC CODES:**

### **Evidence Locker Complex (1-x):**

#### **1-1 (Evidence Locker Main):**
- **1-1-01**: Evidence manifest syntax error
- **1-1-02**: Evidence manifest missing required fields
- **1-1-10**: Evidence locker initialization failed
- **1-1-11**: Evidence locker initialization timeout
- **1-1-20**: Evidence locker communication timeout
- **1-1-30**: Evidence processing error
- **1-1-31**: Evidence validation failed
- **1-1-40**: Evidence storage resource unavailable
- **1-1-70**: Evidence file not found
- **1-1-71**: Evidence file access denied

#### **1-1.1 (Evidence Classifier):**
- **1-1.1-01**: Classification rule syntax error
- **1-1.1-02**: Classification rule missing required fields
- **1-1.1-10**: Classifier initialization failed
- **1-1.1-30**: Classification processing error
- **1-1.1-31**: Classification validation failed
- **1-1.1-50**: Classification business rule failed

#### **1-1.2 (Evidence Identifier):**
- **1-1.2-01**: Identification rule syntax error
- **1-1.2-10**: Identifier initialization failed
- **1-1.2-30**: Evidence identification error
- **1-1.2-31**: Evidence identification validation failed
- **1-1.2-50**: Identification business rule failed

#### **1-1.3 (Static Data Flow):**
- **1-1.3-01**: Data flow configuration syntax error
- **1-1.3-10**: Data flow initialization failed
- **1-1.3-30**: Data flow processing error
- **1-1.3-31**: Data flow validation failed
- **1-1.3-50**: Data flow business rule failed

#### **1-1.4 (Evidence Index):**
- **1-1.4-01**: Index configuration syntax error
- **1-1.4-10**: Index initialization failed
- **1-1.4-30**: Index processing error
- **1-1.4-31**: Index validation failed
- **1-1.4-80**: Index database connection failed

#### **1-1.5 (Evidence Manifest):**
- **1-1.5-01**: Manifest syntax error
- **1-1.5-02**: Manifest missing required fields
- **1-1.5-10**: Manifest initialization failed
- **1-1.5-30**: Manifest processing error
- **1-1.5-31**: Manifest validation failed
- **1-1.5-70**: Manifest file not found

#### **1-1.6 (Evidence Class Builder):**
- **1-1.6-01**: Class builder configuration syntax error
- **1-1.6-10**: Class builder initialization failed
- **1-1.6-30**: Class building error
- **1-1.6-31**: Class validation failed
- **1-1.6-50**: Class building business rule failed

### **Warden Complex (2-x):**

#### **2-1 (Ecosystem Controller):**
- **2-1-01**: ECC configuration syntax error
- **2-1-02**: ECC configuration missing required fields
- **2-1-10**: ECC initialization failed
- **2-1-11**: ECC initialization timeout
- **2-1-20**: ECC communication timeout
- **2-1-30**: ECC processing error
- **2-1-50**: ECC business rule failed
- **2-1-80**: ECC database connection failed
- **2-1-90**: ECC system crash

#### **2-1.1 (ECC State Manager):**
- **2-1.1-01**: State configuration syntax error
- **2-1.1-10**: State manager initialization failed
- **2-1.1-30**: State processing error
- **2-1.1-50**: State transition business rule failed

#### **2-1.2 (ECC Dependency Tracker):**
- **2-1.2-01**: Dependency configuration syntax error
- **2-1.2-10**: Dependency tracker initialization failed
- **2-1.2-30**: Dependency tracking error
- **2-1.2-50**: Dependency validation business rule failed

#### **2-1.3 (ECC Execution Order):**
- **2-1.3-01**: Execution order configuration syntax error
- **2-1.3-10**: Execution order initialization failed
- **2-1.3-30**: Execution order processing error
- **2-1.3-50**: Execution order business rule failed

#### **2-1.4 (ECC Permission Controller):**
- **2-1.4-01**: Permission configuration syntax error
- **2-1.4-10**: Permission controller initialization failed
- **2-1.4-30**: Permission processing error
- **2-1.4-50**: Permission validation business rule failed

#### **2-2 (Gateway Controller):**
- **2-2-01**: Gateway configuration syntax error
- **2-2-02**: Gateway configuration missing required fields
- **2-2-10**: Gateway initialization failed
- **2-2-11**: Gateway initialization timeout
- **2-2-20**: Gateway communication timeout
- **2-2-30**: Gateway processing error
- **2-2-50**: Gateway business rule failed
- **2-2-80**: Gateway database connection failed
- **2-2-90**: Gateway system crash

#### **2-2.1 (Gateway Signal Dispatcher):**
- **2-2.1-01**: Signal dispatcher configuration syntax error
- **2-2.1-10**: Signal dispatcher initialization failed
- **2-2.1-20**: Signal dispatch communication error
- **2-2.1-30**: Signal dispatch processing error

#### **2-2.2 (Gateway Section Router):**
- **2-2.2-01**: Section router configuration syntax error
- **2-2.2-10**: Section router initialization failed
- **2-2.2-30**: Section routing error
- **2-2.2-50**: Section routing business rule failed

#### **2-2.3 (Gateway Evidence Pipeline):**
- **2-2.3-01**: Evidence pipeline configuration syntax error
- **2-2.3-10**: Evidence pipeline initialization failed
- **2-2.3-30**: Evidence pipeline processing error
- **2-2.3-50**: Evidence pipeline business rule failed

#### **2-2.4 (Gateway Bottleneck Monitor):**
- **2-2.4-01**: Bottleneck monitor configuration syntax error
- **2-2.4-10**: Bottleneck monitor initialization failed
- **2-2.4-30**: Bottleneck monitoring error
- **2-2.4-50**: Bottleneck detection business rule failed

### **Mission Debrief Complex (3-x):**

#### **3-1 (Mission Debrief Manager):**
- **3-1-01**: Debrief configuration syntax error
- **3-1-02**: Debrief configuration missing required fields
- **3-1-10**: Debrief initialization failed
- **3-1-11**: Debrief initialization timeout
- **3-1-20**: Debrief communication timeout
- **3-1-30**: Debrief processing error
- **3-1-50**: Debrief business rule failed
- **3-1-80**: Debrief database connection failed
- **3-1-90**: Debrief system crash

#### **3-1.1 (Report Generator):**
- **3-1.1-01**: Report generator configuration syntax error
- **3-1.1-10**: Report generator initialization failed
- **3-1.1-30**: Report generation error
- **3-1.1-31**: Report validation failed
- **3-1.1-50**: Report generation business rule failed
- **3-1.1-70**: Report template file not found

#### **3-1.2 (Digital Signing):**
- **3-1.2-01**: Digital signing configuration syntax error
- **3-1.2-10**: Digital signing initialization failed
- **3-1.2-30**: Digital signing error
- **3-1.2-50**: Digital signing business rule failed
- **3-1.2-70**: Digital certificate file not found

#### **3-1.3 (Template Engine):**
- **3-1.3-01**: Template engine configuration syntax error
- **3-1.3-10**: Template engine initialization failed
- **3-1.3-30**: Template processing error
- **3-1.3-31**: Template validation failed
- **3-1.3-50**: Template business rule failed
- **3-1.3-70**: Template file not found

#### **3-1.4 (Watermark System):**
- **3-1.4-01**: Watermark configuration syntax error
- **3-1.4-10**: Watermark system initialization failed
- **3-1.4-30**: Watermark processing error
- **3-1.4-31**: Watermark validation failed
- **3-1.4-50**: Watermark business rule failed

#### **3-2 (The Librarian):**
- **3-2-01**: Librarian configuration syntax error
- **3-2-02**: Librarian configuration missing required fields
- **3-2-10**: Librarian initialization failed
- **3-2-11**: Librarian initialization timeout
- **3-2-20**: Librarian communication timeout
- **3-2-30**: Librarian processing error
- **3-2-50**: Librarian business rule failed
- **3-2-80**: Librarian database connection failed
- **3-2-90**: Librarian system crash

#### **3-2.1 (Narrative Assembler):**
- **3-2.1-01**: Narrative assembler configuration syntax error
- **3-2.1-10**: Narrative assembler initialization failed
- **3-2.1-30**: Narrative assembly error
- **3-2.1-31**: Narrative validation failed
- **3-2.1-50**: Narrative assembly business rule failed

#### **3-2.2 (Template Cache):**
- **3-2.2-01**: Template cache configuration syntax error
- **3-2.2-10**: Template cache initialization failed
- **3-2.2-30**: Template cache processing error
- **3-2.2-40**: Template cache resource unavailable

#### **3-2.3 (Document Processor):**
- **3-2.3-01**: Document processor configuration syntax error
- **3-2.3-10**: Document processor initialization failed
- **3-2.3-30**: Document processing error
- **3-2.3-31**: Document validation failed
- **3-2.3-50**: Document processing business rule failed

#### **3-2.4 (OSINT Engine):**
- **3-2.4-01**: OSINT engine configuration syntax error
- **3-2.4-10**: OSINT engine initialization failed
- **3-2.4-30**: OSINT processing error
- **3-2.4-60**: OSINT external service unavailable
- **3-2.4-61**: OSINT external service timeout

### **Analyst Deck Complex (4-x):**

#### **4-1 (Section 1 - Case Profile):**
- **4-1-01**: Section 1 configuration syntax error
- **4-1-02**: Section 1 configuration missing required fields
- **4-1-10**: Section 1 initialization failed
- **4-1-11**: Section 1 initialization timeout
- **4-1-20**: Section 1 communication timeout
- **4-1-30**: Section 1 processing error
- **4-1-50**: Section 1 business rule failed
- **4-1-80**: Section 1 database connection failed
- **4-1-90**: Section 1 system crash

#### **4-2 (Section 2 - Investigation Planning):**
- **4-2-01**: Section 2 configuration syntax error
- **4-2-02**: Section 2 configuration missing required fields
- **4-2-10**: Section 2 initialization failed
- **4-2-11**: Section 2 initialization timeout
- **4-2-20**: Section 2 communication timeout
- **4-2-30**: Section 2 processing error
- **4-2-50**: Section 2 business rule failed
- **4-2-80**: Section 2 database connection failed
- **4-2-90**: Section 2 system crash

#### **4-3 (Section 3 - Surveillance Operations):**
- **4-3-01**: Section 3 configuration syntax error
- **4-3-02**: Section 3 configuration missing required fields
- **4-3-10**: Section 3 initialization failed
- **4-3-11**: Section 3 initialization timeout
- **4-3-20**: Section 3 communication timeout
- **4-3-30**: Section 3 processing error
- **4-3-50**: Section 3 business rule failed
- **4-3-80**: Section 3 database connection failed
- **4-3-90**: Section 3 system crash

#### **4-4 (Section 4 - Session Review):**
- **4-4-01**: Section 4 configuration syntax error
- **4-4-02**: Section 4 configuration missing required fields
- **4-4-10**: Section 4 initialization failed
- **4-4-11**: Section 4 initialization timeout
- **4-4-20**: Section 4 communication timeout
- **4-4-30**: Section 4 processing error
- **4-4-50**: Section 4 business rule failed
- **4-4-80**: Section 4 database connection failed
- **4-4-90**: Section 4 system crash

#### **4-5 (Section 5 - Document Inventory):**
- **4-5-01**: Section 5 configuration syntax error
- **4-5-02**: Section 5 configuration missing required fields
- **4-5-10**: Section 5 initialization failed
- **4-5-11**: Section 5 initialization timeout
- **4-5-20**: Section 5 communication timeout
- **4-5-30**: Section 5 processing error
- **4-5-50**: Section 5 business rule failed
- **4-5-80**: Section 5 database connection failed
- **4-5-90**: Section 5 system crash

#### **4-6 (Section 6 - Billing Summary):**
- **4-6-01**: Section 6 configuration syntax error
- **4-6-02**: Section 6 configuration missing required fields
- **4-6-10**: Section 6 initialization failed
- **4-6-11**: Section 6 initialization timeout
- **4-6-20**: Section 6 communication timeout
- **4-6-30**: Section 6 processing error
- **4-6-50**: Section 6 business rule failed
- **4-6-80**: Section 6 database connection failed
- **4-6-90**: Section 6 system crash

#### **4-7 (Section 7 - Legal Compliance):**
- **4-7-01**: Section 7 configuration syntax error
- **4-7-02**: Section 7 configuration missing required fields
- **4-7-10**: Section 7 initialization failed
- **4-7-11**: Section 7 initialization timeout
- **4-7-20**: Section 7 communication timeout
- **4-7-30**: Section 7 processing error
- **4-7-50**: Section 7 business rule failed
- **4-7-80**: Section 7 database connection failed
- **4-7-90**: Section 7 system crash

#### **4-8 (Section 8 - Media Documentation):**
- **4-8-01**: Section 8 configuration syntax error
- **4-8-02**: Section 8 configuration missing required fields
- **4-8-10**: Section 8 initialization failed
- **4-8-11**: Section 8 initialization timeout
- **4-8-20**: Section 8 communication timeout
- **4-8-30**: Section 8 processing error
- **4-8-50**: Section 8 business rule failed
- **4-8-80**: Section 8 database connection failed
- **4-8-90**: Section 8 system crash

#### **4-CP (Cover Page):**
- **4-CP-01**: Cover page configuration syntax error
- **4-CP-02**: Cover page configuration missing required fields
- **4-CP-10**: Cover page initialization failed
- **4-CP-11**: Cover page initialization timeout
- **4-CP-20**: Cover page communication timeout
- **4-CP-30**: Cover page processing error
- **4-CP-50**: Cover page business rule failed
- **4-CP-80**: Cover page database connection failed
- **4-CP-90**: Cover page system crash

#### **4-TOC (Table of Contents):**
- **4-TOC-01**: TOC configuration syntax error
- **4-TOC-02**: TOC configuration missing required fields
- **4-TOC-10**: TOC initialization failed
- **4-TOC-11**: TOC initialization timeout
- **4-TOC-20**: TOC communication timeout
- **4-TOC-30**: TOC processing error
- **4-TOC-50**: TOC business rule failed
- **4-TOC-80**: TOC database connection failed
- **4-TOC-90**: TOC system crash

#### **4-DP (Disclosure Page):**
- **4-DP-01**: Disclosure page configuration syntax error
- **4-DP-02**: Disclosure page configuration missing required fields
- **4-DP-10**: Disclosure page initialization failed
- **4-DP-11**: Disclosure page initialization timeout
- **4-DP-20**: Disclosure page communication timeout
- **4-DP-30**: Disclosure page processing error
- **4-DP-50**: Disclosure page business rule failed
- **4-DP-80**: Disclosure page database connection failed
- **4-DP-90**: Disclosure page system crash

### **Marshall Complex (5-x):**

#### **5-1 (Gateway):**
- **5-1-01**: Gateway configuration syntax error
- **5-1-02**: Gateway configuration missing required fields
- **5-1-10**: Gateway initialization failed
- **5-1-11**: Gateway initialization timeout
- **5-1-20**: Gateway communication timeout
- **5-1-30**: Gateway processing error
- **5-1-50**: Gateway business rule failed
- **5-1-80**: Gateway database connection failed
- **5-1-90**: Gateway system crash

#### **5-2 (Evidence Manager):**
- **5-2-01**: Evidence manager configuration syntax error
- **5-2-02**: Evidence manager configuration missing required fields
- **5-2-10**: Evidence manager initialization failed
- **5-2-11**: Evidence manager initialization timeout
- **5-2-20**: Evidence manager communication timeout
- **5-2-30**: Evidence manager processing error
- **5-2-50**: Evidence manager business rule failed
- **5-2-80**: Evidence manager database connection failed
- **5-2-90**: Evidence manager system crash

#### **5-3 (Section Controller):**
- **5-3-01**: Section controller configuration syntax error
- **5-3-02**: Section controller configuration missing required fields
- **5-3-10**: Section controller initialization failed
- **5-3-11**: Section controller initialization timeout
- **5-3-20**: Section controller communication timeout
- **5-3-30**: Section controller processing error
- **5-3-50**: Section controller business rule failed
- **5-3-80**: Section controller database connection failed
- **5-3-90**: Section controller system crash

### **War Room Complex (6-x):**

#### **6-1 (Dev Environment):**
- **6-1-01**: Dev environment configuration syntax error
- **6-1-02**: Dev environment configuration missing required fields
- **6-1-10**: Dev environment initialization failed
- **6-1-11**: Dev environment initialization timeout
- **6-1-20**: Dev environment communication timeout
- **6-1-30**: Dev environment processing error
- **6-1-50**: Dev environment business rule failed
- **6-1-80**: Dev environment database connection failed
- **6-1-90**: Dev environment system crash

#### **6-2 (Tool Dependencies):**
- **6-2-01**: Tool dependencies configuration syntax error
- **6-2-02**: Tool dependencies configuration missing required fields
- **6-2-10**: Tool dependencies initialization failed
- **6-2-11**: Tool dependencies initialization timeout
- **6-2-20**: Tool dependencies communication timeout
- **6-2-30**: Tool dependencies processing error
- **6-2-50**: Tool dependencies business rule failed
- **6-2-80**: Tool dependencies database connection failed
- **6-2-90**: Tool dependencies system crash

### **Enhanced Functional GUI (7-x):**

#### **7-1 (Enhanced Functional GUI):**
- **7-1-01**: GUI configuration syntax error
- **7-1-02**: GUI configuration missing required fields
- **7-1-10**: GUI initialization failed
- **7-1-11**: GUI initialization timeout
- **7-1-20**: GUI communication timeout
- **7-1-30**: GUI processing error
- **7-1-50**: GUI business rule failed
- **7-1-80**: GUI database connection failed
- **7-1-90**: GUI system crash

#### **7-1.1 (User Interface Controller):**
- **7-1.1-01**: UI controller configuration syntax error
- **7-1.1-10**: UI controller initialization failed
- **7-1.1-30**: UI controller processing error
- **7-1.1-50**: UI controller business rule failed

#### **7-1.2 (Case Management Interface):**
- **7-1.2-01**: Case management configuration syntax error
- **7-1.2-10**: Case management initialization failed
- **7-1.2-30**: Case management processing error
- **7-1.2-50**: Case management business rule failed

#### **7-1.3 (Evidence Display Interface):**
- **7-1.3-01**: Evidence display configuration syntax error
- **7-1.3-10**: Evidence display initialization failed
- **7-1.3-30**: Evidence display processing error
- **7-1.3-50**: Evidence display business rule failed

#### **7-1.4 (Section Review Interface):**
- **7-1.4-01**: Section review configuration syntax error
- **7-1.4-10**: Section review initialization failed
- **7-1.4-30**: Section review processing error
- **7-1.4-50**: Section review business rule failed

#### **7-1.5 (Report Generation Interface):**
- **7-1.5-01**: Report generation configuration syntax error
- **7-1.5-10**: Report generation initialization failed
- **7-1.5-30**: Report generation processing error
- **7-1.5-50**: Report generation business rule failed

#### **7-1.6 (System Status Interface):**
- **7-1.6-01**: System status configuration syntax error
- **7-1.6-10**: System status initialization failed
- **7-1.6-30**: System status processing error
- **7-1.6-50**: System status business rule failed

#### **7-1.7 (Error Display Interface):**
- **7-1.7-01**: Error display configuration syntax error
- **7-1.7-10**: Error display initialization failed
- **7-1.7-30**: Error display processing error
- **7-1.7-50**: Error display business rule failed

#### **7-1.8 (Progress Monitoring Interface):**
- **7-1.8-01**: Progress monitoring configuration syntax error
- **7-1.8-10**: Progress monitoring initialization failed
- **7-1.8-30**: Progress monitoring processing error
- **7-1.8-50**: Progress monitoring business rule failed

---

## **DIAGNOSTIC CODE USAGE EXAMPLES:**

### **SOS Fault Reporting:**
```python
# Evidence Locker Main has syntax error in configuration at line 45
sos_fault = "1-1-01-45"
description = "Evidence manifest syntax error - invalid JSON format at line 45"

# ECC initialization timeout in dependency check (lines 102-170)
sos_fault = "2-1-11-102-170"
description = "ECC initialization timeout - dependency not responding in lines 102-170"

# Report Generator file not found in template loader
sos_fault = "3-1.1-70-23"
description = "Report template file not found - template_master.docx missing at line 23"

# Section 1 database connection failed in connection pool
sos_fault = "4-1-80-156"
description = "Section 1 database connection failed - connection pool exhausted at line 156"

# GUI system crash in memory allocation
sos_fault = "7-1-90-89"
description = "GUI system crash - out of memory error at line 89"
```

### **Radio Check Response:**
```python
# System responding normally
radio_response = "1-1-00"  # 00 = Normal operation
description = "Evidence Locker operational"

# System has configuration error at line 67
radio_response = "2-1-01-67"
description = "ECC configuration syntax error at line 67"

# System initialization failed in dependency check
radio_response = "3-1-10-45"
description = "Mission Debrief initialization failed at line 45"

# System communication timeout in signal handler
radio_response = "4-1-20-123"
description = "Section 1 communication timeout at line 123"
```

### **Rollcall Response:**
```python
# All systems responding
rollcall_response = {
    "1-1": "1-1-00",  # Evidence Locker operational
    "2-1": "2-1-00",  # ECC operational
    "3-1": "3-1-00",  # Mission Debrief operational
    "4-1": "4-1-00",  # Section 1 operational
    "5-1": "5-1-00",  # Gateway operational
    "6-1": "6-1-00",  # Dev Environment operational
    "7-1": "7-1-00"   # GUI operational
}

# Some systems failing
rollcall_response = {
    "1-1": "1-1-00",  # Evidence Locker operational
    "2-1": "2-1-01",  # ECC configuration error
    "3-1": "3-1-10",  # Mission Debrief initialization failed
    "4-1": "4-1-20",  # Section 1 communication timeout
    "5-1": "5-1-00",  # Gateway operational
    "6-1": "6-1-00",  # Dev Environment operational
    "7-1": "7-1-90"   # GUI system crash
}
```

This diagnostic code system provides **specific, actionable error codes** for every component in the Central Command system, making troubleshooting and fault resolution much more effective!
