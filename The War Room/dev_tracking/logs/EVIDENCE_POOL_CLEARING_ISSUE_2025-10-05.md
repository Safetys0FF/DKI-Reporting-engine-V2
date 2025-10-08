# Evidence Pool Clearing Issue
## Date: October 5, 2025

## Problem Identified
**The Evidence Locker is NOT clearing the evidence pool between cases!**

### Current Behavior:
1. Evidence Locker loads persistent manifest on initialization
2. **94 evidence entries** persist from previous case
3. **NO method exists** to clear evidence pool for new cases
4. Evidence accumulates across multiple cases

### Root Cause Analysis:

#### 1. **Evidence Locker Always Loads Persistent Data**
```python
def _load_persisted_manifest(self) -> None:
    """Populate in-memory evidence cache from the persisted manifest (if available)."""
    # Always loads existing manifest on initialization
    with self.manifest_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    
    # Loads ALL 94 entries from previous case
    entries = data.get("entries")
    for entry in entries:
        self.evidence_index[evidence_id] = record
```

#### 2. **No Case Reset/Clear Method**
**Missing Methods:**
- `start_new_case()`
- `clear_evidence_pool()`
- `reset_for_new_case()`
- `purge_evidence()`

#### 3. **Evidence Pool Never Gets Cleared**
The `clear()` method found is actually used to **load** data, not clear it:
```python
def _load_persisted_manifest(self):
    with self._manifest_lock:
        self.evidence_index.clear()  # Clears in-memory cache
        # Then immediately loads from persistent file
        for entry in entries:
            self.evidence_index[evidence_id] = record
```

## Required Solution

### 1. **Add Case Reset Method**
```python
def start_new_case(self, case_id: str) -> None:
    """Clear evidence pool for new case"""
    with self._manifest_lock:
        # Clear in-memory cache
        self.evidence_index.clear()
        if hasattr(self, "evidence_manifest"):
            self.evidence_manifest.clear()
        
        # Clear persistent manifest file
        empty_manifest = {
            "manifest_version": 1,
            "updated_at": datetime.now().isoformat(),
            "evidence_count": 0,
            "entries": []
        }
        
        with self.manifest_path.open("w", encoding="utf-8") as handle:
            json.dump(empty_manifest, handle, indent=2)
        
        self.logger.info(f"[NEW CASE] Evidence pool cleared for case: {case_id}")
```

### 2. **Add Evidence Pool Clear Method**
```python
def clear_evidence_pool(self) -> None:
    """Clear all evidence from pool"""
    with self._manifest_lock:
        # Clear in-memory cache
        self.evidence_index.clear()
        if hasattr(self, "evidence_manifest"):
            self.evidence_manifest.clear()
        
        # Clear persistent manifest
        empty_manifest = {
            "manifest_version": 1,
            "updated_at": datetime.now().isoformat(),
            "evidence_count": 0,
            "entries": []
        }
        
        with self.manifest_path.open("w", encoding="utf-8") as handle:
            json.dump(empty_manifest, handle, indent=2)
        
        self.logger.info("[CLEAR] Evidence pool cleared")
```

### 3. **ECC Should Trigger Case Reset**
```python
# In Ecosystem Controller
def start_new_case(self, case_id: str) -> None:
    """Start new case - clear evidence pool"""
    # Clear evidence pool
    if self.evidence_locker:
        self.evidence_locker.start_new_case(case_id)
    
    # Reset section states
    self.completed_sections.clear()
    self.failed_sections.clear()
    self.section_states.clear()
    
    self.logger.info(f"[NEW CASE] Started case: {case_id}")
```

## Current State
- **94 evidence entries** from previous case still in pool
- **Evidence Locker loads persistent data** on every initialization
- **No mechanism** to clear evidence between cases
- **Evidence accumulates** across multiple cases

## Impact
- Evidence from previous cases contaminates new cases
- Section assignments may be incorrect
- Evidence pool grows indefinitely
- Case isolation is broken

## Fix Priority: CRITICAL
This is a fundamental architectural flaw that breaks case isolation. Evidence pools must be cleared between cases.

## Implementation Plan
1. **Add `start_new_case()` method to Evidence Locker**
2. **Add `clear_evidence_pool()` method**
3. **ECC calls evidence pool clear on new case**
4. **Test case isolation**
5. **Verify evidence pool starts empty for new cases**

