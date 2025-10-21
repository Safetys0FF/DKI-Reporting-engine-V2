# CANBUS ADDRESS REFACTOR PLAN
**Agent:** NETWORK (agent_2_NETWORK_CODING)  
**Date:** 2025-10-09  
**Task:** Comprehensive address restructuring for flow optimization

---

## REFACTOR OBJECTIVES

**Current Issue:** Address space fragmented across multiple ranges (1-x, 2-x, 3-x, 4-x, 5-x, 7-x, GUI-x)

**Target Flow:**
- **1** = Evidence Locker Complex
- **2** = Warden Complex
- **3** = Marshall Complex
- **4** = Section Engines (unchanged)
- **5** = Mission Debrief Complex
- **GUI-1** = User Interface (unchanged)
- **Bus-1** = CANBUS Core (unchanged)
- **DIAG-1** = Diagnostic System (unchanged)

---

## ADDRESS MAPPING

### **1. Evidence Locker Complex**

| Current | New | System | Change Type |
|---------|-----|--------|-------------|
| 1-1 | 1 | Evidence Locker Main | Parent address |
| 1-1.1 | 1.1 | Evidence Classifier | Submodule renumber |
| 1-1.2 | 1.2 | Evidence Identifier | Submodule renumber |
| 1-1.3 | 1.3 | Static Data Flow | Submodule renumber |
| 1-1.4 | 1.4 | Evidence Index | Submodule renumber |
| 1-1.5 | 1.5 | Evidence Manifest | Submodule renumber |
| 1-1.6 | 1.6 | Evidence Class Builder | Submodule renumber |
| 1-1.7 | 1.7 | Case Manifest Builder | Submodule renumber |
| 1-1.8 | 1.8 | OCR Processor | Submodule renumber |

**Code Changes:** `evidence_locker_main.py` MODULE_ADDRESS

### **2. Warden Complex** ✅ NO CHANGES

| Current | New | System | Change Type |
|---------|-----|--------|-------------|
| 2-1 | 2-1 | Warden Module | ✅ Unchanged |
| 2-2 | 2-2 | Ecosystem Controller | ✅ Unchanged |
| 2-2.1-4 | 2-2.1-4 | ECC Submodules | ✅ Unchanged |
| 2-3 | 2-3 | Gateway Controller | ✅ Unchanged |
| 2-3.1-4 | 2-3.1-4 | Gateway Submodules | ✅ Unchanged |

**Code Changes:** None required

### **3. Marshall Complex**

| Current | New | System | Change Type |
|---------|-----|--------|-------------|
| 1-2 | 3 | Marshall Module | Parent reassignment |
| (new) | 3-1 | Evidence Manager | Component restructure |
| (new) | 3-2 | Evidence Checkout | Component restructure |
| 5-1 | 3-3 or DEPRECATE | Gateway (Marshall) | TBD — User decision needed |
| 5-3 | 3-4 or DEPRECATE | Section Controller | TBD — User decision needed |

**Code Changes:**
- `evidence_manager.py` MODULE_ADDRESS: 1-2 → 3-1
- Create `marshall_module.py` (full wrapper, not shell)
- Create `_init_evidence_manager.py`
- Create `_init_evidence_checkout.py` (if needed)

### **4. Section Engines** ✅ NO CHANGES

| Current | New | System | Change Type |
|---------|-----|--------|-------------|
| 4-1 to 4-8 | 4-1 to 4-8 | Section Frameworks | ✅ Unchanged |
| 4-CP | 4-CP | Cover Page | ✅ Unchanged |
| 4-TOC | 4-TOC | Table of Contents | ✅ Unchanged |
| 4-DP | 4-DP | Disclosure Page | ✅ Unchanged |

**Code Changes:** None required (fault relay parent updates in registry only)

### **5. Mission Debrief Complex**

| Current | New | System | Change Type |
|---------|-----|--------|-------------|
| 3-1 | 5 | Mission Debrief Module | Parent reassignment |
| 3-2 | 5-1 | Debrief Manager | Component reassignment |
| 3-1.1 | 5.1 or DEPRECATE | Report Generator | Submodule (legacy?) |
| 3-1.2 | 5.2 or DEPRECATE | Digital Signing | Submodule (legacy?) |
| 3-1.3 | 5.3 or DEPRECATE | Template Engine | Submodule (legacy?) |
| 3-1.4 | 5.4 or DEPRECATE | Watermark System | Submodule (legacy?) |
| 3-3 | 5-2 | The Librarian | Component reassignment |
| 3-3.1 | 5-2.1 | Template Cache | Submodule reassignment |
| 3-3.2 | 5-2.2 | Document Processor | Submodule reassignment |
| 3-3.3 | 5-2.3 | OSINT Engine | Submodule reassignment |

**Code Changes:**
- `mission_debrief_module.py` MODULE_ADDRESS: 3-1 → 5
- `mission_debrief_manager.py` log addresses: [3-2] → [5-1]
- `narrative_assembler.py` log addresses: [3-3] → [5-2]

### **Other Systems** ✅ NO CHANGES

| Address | System | Change Type |
|---------|--------|-------------|
| GUI-1 | Enhanced Functional GUI | ✅ Unchanged |
| Bus-1, Bus-1.1-5 | CANBUS Core | ✅ Unchanged |
| DIAG-1 | Diagnostic System | ✅ Unchanged |
| 6-1, 6-2 | War Room (Dev, Tools) | ✅ Unchanged |

---

## FAULT RELAY UPDATES

### **Section Fault Relay (4-1 to 4-8)**

**Current:** Relay parent = 2-3 (Gateway Controller)  
**New:** ✅ Unchanged (2-3 remains Gateway)  
**Signals:** `section.fault.4-1` through `4-8` → Gateway (2-3)

### **Artifact Fault Relay**

**Current:** Relay parent = 3-1 (Mission Debrief Module)  
**New:** Relay parent = 5 (Mission Debrief Module)

**Registry Updates:**
- Change fault_relay.relay_parent: 3-1 → 5
- Signals remain: `section.fault.4-CP`, `4-TOC`, `4-DP`

**Code Updates:**
- `mission_debrief_manager.py`: Log `[3-1]` → `[5-1]`, enrichment `relay_parent: "3-1"` → `"5"`

---

## FILES REQUIRING CHANGES

### **Code Files (7):**
1. `evidence_locker_main.py` — MODULE_ADDRESS: "1-1" → "1"
2. `evidence_manager.py` — MODULE_ADDRESS: "1-2" → "3-1" (if Evidence Manager becomes child)
3. `marshall_module.py` — MODULE_ADDRESS: "1-2" → "3" (parent wrapper)
4. `mission_debrief_module.py` — MODULE_ADDRESS: "3-1" → "5"
5. `mission_debrief_manager.py` — Log tags: [3-2] → [5-1], relay_parent: "3-1" → "5"
6. `narrative_assembler.py` — Log tags: [3-3] → [5-2]
7. `section_framework_base.py` — Fault relay parent update (if hardcoded)

### **Registry Files (2):**
1. `system_registry.json` — 60+ address updates
2. `MASTER_DIAGNOSTIC_PROTOCOL_2025-10-05.md` — All system tables

---

## DEPRECATION DECISIONS NEEDED

**Marshall Gateway (5-1):**
- Current: `gateway.Gateway` in `The Marshall/Gateway/`
- Options:
  1. Move to 3-3 (child of Marshall-3)
  2. Deprecate (mark superseded_by Warden Gateway 2-3)
  3. Move to 6-x (War Room)

**Legacy Submodules (3-1.1 - 3-1.4):**
- Current: Report Generator, Digital Signing, Template Engine, Watermark
- Parent was 3-1 (now becoming 5)
- Options:
  1. Move to 5.1 - 5.4 (direct children of Mission Debrief-5)
  2. Deprecate (functionality now in adapters within 5-1 Debrief Manager)

**Section Controller (5-3):**
- Current: In Marshall folder, address 5-3
- Options:
  1. Move to 3-4 (child of Marshall-3)
  2. Deprecate

**User decision required on these before proceeding.**

---

**Refactor plan created. Awaiting:**
1. Gateway (5-1) reassignment decision
2. Legacy submodule (3-1.x) handling
3. "Start build" authorization


