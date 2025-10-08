# Evidence Locker Structure Analysis
## Date: October 5, 2025

## Current Evidence Locker Architecture

### Core Components
1. **`evidence_locker_main.py`** - Main orchestrator (17,000+ lines)
2. **`evidence_index.py`** - Central evidence management system
3. **`evidence_classifier.py`** - Classification system for assigning evidence to sections
4. **`evidence_class_builder.py`** - Evidence class building
5. **`case_manifest_builder.py`** - Case manifest generation
6. **`static_data_flow.py`** - Data flow patterns between Gateway and sections
7. **`section_registry.py`** - Section registry and reporting standards
8. **`bus_extensions.py`** - Bus integration mixins

### Persistent Evidence Pool
**File:** `evidence_manifest.json`
- **94 evidence entries** currently stored
- **Full persistence** with timestamps, classifications, and metadata
- **Section assignments** and cross-references
- **Evidence cards remain alive** between sessions

### Key Findings

#### 1. **Evidence Pool Already Exists and Persists**
```json
{
  "manifest_version": 1,
  "updated_at": "2025-10-04T12:07:49.498606",
  "evidence_count": 94,
  "entries": [
    {
      "evidence_id": "evidence_0001",
      "file_path": "E:\\DKI Services Case Oct-Dec 24\\.Completed Files\\Vargas, Ulesis\\welding school cert.jpg",
      "classification": {
        "assigned_section": "section_8",
        "related_sections": ["section_2", "section_6", "section_7"],
        "evidence_type": "image",
        "tags": ["evidence_index", "media", "photo", "video", "image"],
        "classification_method": "keyword_rules",
        "confidence": 0.88
      },
      "status": "indexed",
      "timestamp": "2025-10-03T14:31:14.503748"
    }
  ]
}
```

#### 2. **All Components Have ECC Integration**
Every module has ECC call-out methods:
- `_call_out_to_ecc(operation, data)`
- `_wait_for_ecc_confirm(operation, request_id)`
- `_send_message(operation, data)`
- `_send_accept_signal(operation, data)`

#### 3. **Evidence Classification System**
**File:** `evidence_classifier.py`
- **File type rules** (PDF → section_5, JPG → section_8, etc.)
- **Content keywords** for each section
- **Confidence scoring** and classification methods
- **ECC-aware signalling** for validation

#### 4. **Data Flow Contracts**
**File:** `static_data_flow.py`
- **Data contracts** defining structure and validation
- **Flow orchestration** between Gateway and sections
- **ECC integration** for validation
- **Bidirectional communication** patterns

## ECC's Role with Persistent Evidence Pool

### What ECC NO LONGER Needs to Do:
- ❌ Manage evidence lifecycle (evidence pool handles this)
- ❌ Track evidence state changes (evidence pool persists this)
- ❌ Handle evidence storage/retrieval (evidence pool owns this)

### What ECC SHOULD Focus On:

#### 1. **Evidence Classification Approval**
```python
def approve_evidence_classification(self, evidence_id: str, classification: dict) -> bool:
    """ECC validates Evidence Locker's classification"""
    # Validate tags, section assignments, confidence scores
    # Approve or reject evidence assignments to sections
    return self.evidence_pool.approve_classification(evidence_id, classification)
```

#### 2. **Section Execution Control**
```python
def can_run_section(self, section_id: str) -> bool:
    """ECC controls which section runs when"""
    # Check dependencies, execution order
    # Validate section readiness
    return section_id in self.ready_sections
```

#### 3. **Evidence Pool Permissions**
```python
def grant_evidence_access(self, section_id: str, evidence_filter: dict) -> List[str]:
    """ECC grants evidence access to sections"""
    # Control which evidence sections can access
    # Manage evidence pool permissions
    return self.evidence_pool.get_approved_evidence(section_id, evidence_filter)
```

## Current Evidence Locker Capabilities

### Evidence Processing Pipeline
1. **Ingestion** - Raw artifacts uploaded
2. **OCR/Enrichment** - Heavy-tool adapters process content
3. **Classification** - Evidence classifier assigns to sections
4. **Persistence** - Evidence manifest stores everything
5. **Bus Publishing** - `evidence.new`/`evidence.updated` signals
6. **Section Delivery** - Responds to `section.needs` requests

### Bus Integration
- **Custom mixins** for bus handler registration
- **Evidence signals** (`evidence.new`, `evidence.updated`)
- **Section requests** (`section.needs`, `evidence.request`)
- **Gateway coordination** (`gateway.*` signals)
- **Status logging** (`mission.status` snapshots)

## ECC's Simplified Role

With the persistent evidence pool, ECC becomes a **permission controller**:

### 1. **Evidence Classification Gatekeeper**
- Approve/reject Evidence Locker classifications
- Validate section assignments
- Control evidence pool access permissions

### 2. **Section Execution Orchestrator**
- Control section execution order
- Validate dependencies
- Manage section completion validation

### 3. **Evidence Pool Permission Manager**
- Grant evidence access to sections
- Control evidence visibility
- Manage evidence pool security

## Implementation Strategy

### Phase 1: ECC as Permission Controller
```python
class EcosystemController:
    def __init__(self):
        self.evidence_pool = None  # Reference to Evidence Locker
        self.section_contracts = {...}  # Execution order
        self.completed_sections = set()
        
    def approve_evidence_classification(self, evidence_id: str, classification: dict) -> bool:
        """ECC validates Evidence Locker's classification"""
        # Validate classification quality
        # Check section assignments
        # Approve or reject
        return self.evidence_pool.approve_classification(evidence_id, classification)
    
    def can_run_section(self, section_id: str) -> bool:
        """ECC controls section execution order"""
        # Check dependencies
        # Validate execution order
        return section_id in self.ready_sections
```

### Phase 2: Evidence Pool Integration
```python
class EvidenceLocker:
    def __init__(self, ecc=None):
        self.ecc = ecc
        self.evidence_manifest = self.load_manifest()
        
    def classify_evidence(self, evidence_id: str, classification: dict) -> bool:
        """Classify evidence with ECC approval"""
        # Get ECC approval
        if self.ecc:
            approved = self.ecc.approve_evidence_classification(evidence_id, classification)
            if not approved:
                return False
        
        # Update evidence pool
        self.evidence_manifest[evidence_id]['classification'] = classification
        self.save_manifest()
        return True
```

## Key Insight

**The Evidence Locker already IS the persistent evidence pool!** It has:
- ✅ Persistent storage (`evidence_manifest.json`)
- ✅ Evidence lifecycle management
- ✅ Classification system
- ✅ Bus integration
- ✅ Section assignment logic

**ECC's role becomes:** Permission controller and execution orchestrator, not data manager.

The evidence pool handles the data, ECC handles the permissions and execution order.

