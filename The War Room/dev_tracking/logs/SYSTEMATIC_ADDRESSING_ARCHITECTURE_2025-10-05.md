# Systematic Call Sequence and Addressing Architecture
## Date: October 5, 2025

## Address Root Home System Design

### **Core Principle:**
Each module needs a **root address home** and **subsystem root home** for proper call sequence and addressing location before callout language standardization.

## **Address Architecture:**

### **1. BUS SYSTEM:**
```
Bus-1                    # Central Command Bus (Root)
├── Bus-1.1             # Signal Registry
├── Bus-1.2             # Event Logging
├── Bus-1.3             # Handler Management
└── Bus-1.4             # Translation Layer
```

### **2. EVIDENCE LOCKER COMPLEX (Root: 1-x):**
```
1-1                     # Evidence Locker Main (Root Home)
├── 1-1.1              # Evidence Classifier
├── 1-1.2              # Evidence Identifier
├── 1-1.3              # Static Data Flow
├── 1-1.4              # Evidence Index
├── 1-1.5              # Evidence Manifest
└── 1-1.6              # Evidence Class Builder
```

### **3. WARDEN COMPLEX (Root: 2-x):**
```
2-1                     # ECC - Ecosystem Controller (Root Home)
├── 2-1.1              # Section State Manager
├── 2-1.2              # Dependency Tracker
├── 2-1.3              # Execution Order
└── 2-1.4              # Permission Controller

2-2                     # Gateway Controller (Root Home)
├── 2-2.1              # Signal Dispatcher
├── 2-2.2              # Section Router
├── 2-2.3              # Evidence Pipeline
└── 2-2.4              # Bottleneck Monitor
```

### **4. MISSION DEBRIEF COMPLEX (Root: 3-x):**
```
3-1                     # Mission Debrief Manager (Root Home)
├── 3-1.1              # Report Generator
├── 3-1.2              # Digital Signing
├── 3-1.3              # Template Engine
└── 3-1.4              # Watermark System

3-2                     # The Librarian (Root Home)
├── 3-2.1              # Narrative Assembler
├── 3-2.2              # Template Cache
├── 3-2.3              # Document Processor
└── 3-2.4              # OSINT Engine
```

### **5. ANALYST DECK COMPLEX (Root: 4-x):**
```
4-1                     # Section 1 - Case Profile (Root Home)
├── 4-1.1              # Subject Profile Builder
├── 4-1.2              # Case Metadata
└── 4-1.3              # Initial Assessment

4-2                     # Section 2 - Investigation Planning (Root Home)
├── 4-2.1              # Planning Engine
├── 4-2.2              # Resource Allocation
└── 4-2.3              # Timeline Manager

4-3                     # Section 3 - Surveillance Operations (Root Home)
├── 4-3.1              # Surveillance Logs
├── 4-3.2              # Activity Tracker
└── 4-3.3              # Evidence Collection

4-4                     # Section 4 - Session Review (Root Home)
├── 4-4.1              # Review Engine
├── 4-4.2              # Narrative Builder
└── 4-4.3              # Quality Control

4-5                     # Section 5 - Document Inventory (Root Home)
├── 4-5.1              # Document Classifier
├── 4-5.2              # Inventory Tracker
└── 4-5.3              # Chain of Custody

4-6                     # Section 6 - Billing Summary (Root Home)
├── 4-6.1              # Billing Engine
├── 4-6.2              # Cost Calculator
└── 4-6.3              # Invoice Generator

4-7                     # Section 7 - Legal Compliance (Root Home)
├── 4-7.1              # Compliance Checker
├── 4-7.2              # Legal Review
└── 4-7.3              # Risk Assessment

4-8                     # Section 8 - Media Documentation (Root Home)
├── 4-8.1              # Media Processor
├── 4-8.2              # Evidence Index
└── 4-8.3              # Provenance Tracker

4-CP                    # Cover Page (Root Home)
├── 4-CP.1             # Cover Generator
├── 4-CP.2             # Template Manager
└── 4-CP.3             # Approval System

4-TOC                   # Table of Contents (Root Home)
├── 4-TOC.1            # TOC Generator
├── 4-TOC.2            # Section Mapper
└── 4-TOC.3            # Navigation Builder

4-DP                    # Disclosure Page (Root Home)
├── 4-DP.1             # Disclosure Generator
├── 4-DP.2             # Legal Templates
└── 4-DP.3             # Approval Workflow
```

### **6. MARSHALL COMPLEX (Root: 5-x):**
```
5-1                     # Gateway (Root Home)
├── 5-1.1              # Section Router
├── 5-1.2              # Evidence Pipeline
└── 5-1.3              # Processing Queue

5-2                     # Evidence Manager (Root Home)
├── 5-2.1              # Evidence Ingestor
├── 5-2.2              # Processing Engine
└── 5-2.3              # Handoff Manager

5-3                     # Section Controller (Root Home)
├── 5-3.1              # Section Bridge
├── 5-3.2              # Evidence Checkout
└── 5-3.3              # Data Flow Manager
```

### **7. WAR ROOM COMPLEX (Root: 6-x):**
```
6-1                     # Dev Environment (Root Home)
├── 6-1.1              # Development Tools
├── 6-1.2              # Testing Framework
└── 6-1.3              # Debug Console

6-2                     # Tool Dependencies (Root Home)
├── 6-2.1              # OCR Tools
├── 6-2.2              # Document Processors
└── 6-2.3              # External APIs
```

## **Call Sequence Architecture:**

### **1. Standard Call Sequence Pattern:**
```
Caller Address → Bus-1 → Target Address → Handler → Response → Bus-1 → Caller Address
```

### **2. Address-Based Signal Format:**
```python
# Signal Format with Addressing
{
    "signal_id": "unique_signal_id",
    "caller_address": "1-1.1",           # Evidence Classifier
    "target_address": "2-1",             # ECC Root
    "bus_address": "Bus-1",              # Central Bus
    "signal_type": "permission_request",
    "payload": {
        "operation": "classify_evidence",
        "data": {...},
        "timestamp": "2025-10-05T12:00:00"
    },
    "routing_path": ["1-1.1", "Bus-1", "2-1"],
    "response_expected": True,
    "timeout": 30
}
```

### **3. Address Resolution System:**
```python
# Address Resolution Mapping
ADDRESS_REGISTRY = {
    # Bus System
    "Bus-1": {
        "type": "bus",
        "handler": "bus_core.DKIReportBus",
        "subsystems": ["Bus-1.1", "Bus-1.2", "Bus-1.3", "Bus-1.4"]
    },
    
    # Evidence Locker Complex
    "1-1": {
        "type": "evidence_locker_main",
        "handler": "evidence_locker_main.EvidenceLocker",
        "subsystems": ["1-1.1", "1-1.2", "1-1.3", "1-1.4", "1-1.5", "1-1.6"]
    },
    "1-1.1": {
        "type": "evidence_classifier",
        "handler": "evidence_classifier.EvidenceClassifier",
        "parent": "1-1"
    },
    "1-1.2": {
        "type": "evidence_identifier",
        "handler": "evidence_identifier.EvidenceIdentifier",
        "parent": "1-1"
    },
    "1-1.3": {
        "type": "static_data_flow",
        "handler": "static_data_flow.StaticDataFlow",
        "parent": "1-1"
    },
    "1-1.4": {
        "type": "evidence_index",
        "handler": "evidence_index.EvidenceIndex",
        "parent": "1-1"
    },
    "1-1.5": {
        "type": "evidence_manifest",
        "handler": "evidence_manifest.EvidenceManifest",
        "parent": "1-1"
    },
    "1-1.6": {
        "type": "evidence_class_builder",
        "handler": "evidence_class_builder.EvidenceClassBuilder",
        "parent": "1-1"
    },
    
    # Warden Complex
    "2-1": {
        "type": "ecc",
        "handler": "ecosystem_controller.EcosystemController",
        "subsystems": ["2-1.1", "2-1.2", "2-1.3", "2-1.4"]
    },
    "2-2": {
        "type": "gateway_controller",
        "handler": "gateway_controller.GatewayController",
        "subsystems": ["2-2.1", "2-2.2", "2-2.3", "2-2.4"]
    },
    
    # Mission Debrief Complex
    "3-1": {
        "type": "mission_debrief_manager",
        "handler": "mission_debrief_manager.MissionDebriefManager",
        "subsystems": ["3-1.1", "3-1.2", "3-1.3", "3-1.4"]
    },
    "3-2": {
        "type": "librarian",
        "handler": "narrative_assembler.NarrativeAssembler",
        "subsystems": ["3-2.1", "3-2.2", "3-2.3", "3-2.4"]
    },
    
    # Analyst Deck Complex
    "4-1": {
        "type": "section_1_framework",
        "handler": "section_1_framework.Section1Framework",
        "subsystems": ["4-1.1", "4-1.2", "4-1.3"]
    },
    "4-2": {
        "type": "section_2_framework",
        "handler": "section_2_framework.Section2Framework",
        "subsystems": ["4-2.1", "4-2.2", "4-2.3"]
    },
    # ... (continue for all sections)
    
    # Marshall Complex
    "5-1": {
        "type": "gateway",
        "handler": "gateway.Gateway",
        "subsystems": ["5-1.1", "5-1.2", "5-1.3"]
    },
    "5-2": {
        "type": "evidence_manager",
        "handler": "evidence_manager.EvidenceManager",
        "subsystems": ["5-2.1", "5-2.2", "5-2.3"]
    },
    "5-3": {
        "type": "section_controller",
        "handler": "section_controller.SectionController",
        "subsystems": ["5-3.1", "5-3.2", "5-3.3"]
    },
    
    # War Room Complex
    "6-1": {
        "type": "dev_environment",
        "handler": "dev_environment.DevEnvironment",
        "subsystems": ["6-1.1", "6-1.2", "6-1.3"]
    },
    "6-2": {
        "type": "tool_dependencies",
        "handler": "tool_dependencies.ToolDependencies",
        "subsystems": ["6-2.1", "6-2.2", "6-2.3"]
    }
}
```

## **Radio Call-Out Call Sequence Examples:**

### **1. Evidence Classification Call Sequence with Radio Codes:**
```
1-1.1 (Evidence Classifier) → Bus-1 → 2-1 (ECC) → "10-4" (Acknowledged)
2-1 (ECC) → Bus-1 → 1-1.1 → "10-6" (Evidence Received - Processing)
2-1 (ECC) → Bus-1 → 1-1.1 → "10-8" (Evidence Complete - Ready)
```

### **2. Section Processing Call Sequence with Radio Codes:**
```
4-1 (Section 1) → Bus-1 → 2-2 (Gateway Controller) → "10-4" (Acknowledged)
2-2 (Gateway Controller) → Bus-1 → 4-1 → "10-10" (Standby - Processing)
2-2 (Gateway Controller) → Bus-1 → 4-1 → "10-8" (Evidence Complete - Ready)
```

### **3. Report Generation Call Sequence with Radio Codes:**
```
3-1 (Mission Debrief) → Bus-1 → 3-2 (Librarian) → "10-4" (Acknowledged)
3-2 (Librarian) → Bus-1 → 3-1 → "10-6" (Evidence Received - Processing)
3-2 (Librarian) → Bus-1 → 3-1 → "10-8" (Evidence Complete - Ready)
```

### **4. Evidence Handoff Call Sequence with Radio Codes:**
```
5-2 (Evidence Manager) → Bus-1 → 1-1 (Evidence Locker) → "10-4" (Acknowledged)
1-1 (Evidence Locker) → Bus-1 → 5-2 → "10-6" (Evidence Received - Processing)
1-1 (Evidence Locker) → Bus-1 → 5-2 → "10-8" (Evidence Complete - Ready)
```

### **5. Error Handling Call Sequence with Radio Codes:**
```
1-1.1 (Evidence Classifier) → Bus-1 → 2-1 (ECC) → "10-4" (Acknowledged)
2-1 (ECC) → Bus-1 → 1-1.1 → "10-9" (Repeat - Please resend evidence data)
1-1.1 (Evidence Classifier) → Bus-1 → 2-1 (ECC) → "10-4" (Acknowledged)
2-1 (ECC) → Bus-1 → 1-1.1 → "10-6" (Evidence Received - Processing)
```

## **Radio Call-Out Logic System:**

### **Standard Radio Codes:**
```python
# Radio Call-Out Response Codes
RADIO_CODES = {
    "10-4": "Acknowledged - Message received and understood",
    "10-6": "Evidence Received - Evidence has been received and is being processed",
    "10-8": "Evidence Complete - Evidence processing is complete and ready",
    "10-9": "Repeat - Please repeat your last message",
    "10-10": "Standby - Please wait, processing in progress"
}

# Expanded Evidence-Specific Codes
EVIDENCE_RADIO_CODES = {
    "10-4": "Acknowledged - Evidence request received and understood",
    "10-6": "Evidence Received - Evidence has been received and is being processed",
    "10-8": "Evidence Complete - Evidence processing is complete and ready for handoff",
    "10-9": "Evidence Repeat - Please resend evidence data",
    "10-10": "Evidence Standby - Evidence processing in progress, please wait"
}
```

### **Radio Call-Out Protocol:**
```python
# Radio Call-Out Signal Format
{
    "signal_id": "unique_signal_id",
    "caller_address": "1-1.1",           # Evidence Classifier
    "target_address": "2-1",             # ECC Root
    "bus_address": "Bus-1",              # Central Bus
    "signal_type": "radio_call_out",
    "radio_code": "10-4",                # Radio response code
    "message": "Evidence classification request",
    "payload": {
        "operation": "classify_evidence",
        "data": {...},
        "timestamp": "2025-10-05T12:00:00"
    },
    "response_expected": True,
    "timeout": 30
}
```

### **Radio Response Format:**
```python
# Radio Response Signal Format
{
    "signal_id": "response_to_signal_id",
    "caller_address": "2-1",             # ECC Root
    "target_address": "1-1.1",           # Evidence Classifier
    "bus_address": "Bus-1",              # Central Bus
    "signal_type": "radio_response",
    "radio_code": "10-6",                # Evidence received
    "message": "Evidence received and processing",
    "payload": {
        "status": "processing",
        "estimated_completion": "2025-10-05T12:05:00",
        "timestamp": "2025-10-05T12:00:30"
    }
}
```

## **Address-Based Communication Protocol:**

### **1. Signal Registration:**
```python
# Each component registers with its address
def register_address(self, address: str, component_type: str, handler: Any) -> None:
    """Register component with address system"""
    ADDRESS_REGISTRY[address] = {
        "type": component_type,
        "handler": handler,
        "registered_at": datetime.now().isoformat(),
        "status": "active"
    }
```

### **2. Address Resolution:**
```python
# Bus resolves addresses to handlers
def resolve_address(self, address: str) -> Any:
    """Resolve address to handler"""
    if address in ADDRESS_REGISTRY:
        return ADDRESS_REGISTRY[address]["handler"]
    return None
```

### **3. Address-Based Routing with Radio Codes:**
```python
# Route signals based on addresses with radio code responses
def route_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
    """Route signal based on target address with radio code response"""
    target_address = signal.get("target_address")
    handler = self.resolve_address(target_address)
    
    if handler:
        # Process signal and return with radio code
        result = handler.process_signal(signal)
        
        # Add radio code response
        radio_response = {
            "signal_id": f"response_{signal.get('signal_id')}",
            "caller_address": target_address,
            "target_address": signal.get("caller_address"),
            "bus_address": "Bus-1",
            "signal_type": "radio_response",
            "radio_code": self._determine_radio_code(result),
            "message": self._get_radio_message(result),
            "payload": result,
            "timestamp": datetime.now().isoformat()
        }
        
        return radio_response
    else:
        return {
            "error": f"Address {target_address} not found",
            "radio_code": "10-9",  # Repeat - address not found
            "message": "Please check address and resend"
        }

def _determine_radio_code(self, result: Dict[str, Any]) -> str:
    """Determine appropriate radio code based on result"""
    if result.get("error"):
        return "10-9"  # Repeat
    elif result.get("status") == "processing":
        return "10-10"  # Standby
    elif result.get("status") == "complete":
        return "10-8"  # Evidence Complete
    elif result.get("status") == "received":
        return "10-6"  # Evidence Received
    else:
        return "10-4"  # Acknowledged

def _get_radio_message(self, result: Dict[str, Any]) -> str:
    """Get appropriate radio message based on result"""
    radio_code = self._determine_radio_code(result)
    return EVIDENCE_RADIO_CODES.get(radio_code, "Message processed")
```

## **Benefits of Systematic Addressing:**

### **1. Clear Call Sequences:**
- **Predictable routing** - every signal has a clear path
- **Traceable communication** - can track signal flow
- **Debuggable system** - can identify where signals go

### **2. Proper Address Locations:**
- **Root addresses** for main components
- **Subsystem addresses** for sub-components
- **Hierarchical structure** for organization

### **3. Standardized Communication:**
- **Consistent addressing** across all components
- **Uniform signal format** with addresses
- **Centralized routing** through Bus-1

## **Implementation Plan:**

### **Phase 1: Address Assignment**
1. **Assign root addresses** to all main components
2. **Assign subsystem addresses** to all sub-components
3. **Create address registry** with all mappings

### **Phase 2: Address Integration**
1. **Update all components** to use address-based communication
2. **Implement address resolution** in Bus-1
3. **Create address-based signal format**

### **Phase 3: Call Sequence Implementation**
1. **Implement standard call sequences** for all operations
2. **Create address-based routing** system
3. **Test end-to-end communication** with addresses

### **Phase 4: Language Standardization**
1. **Standardize signal names** based on addresses
2. **Standardize payload formats** with address information
3. **Implement unified communication** protocol

This systematic addressing architecture will provide the **foundation for proper call sequences and addressing locations** before we standardize the callout language.
