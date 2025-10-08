# Evidence Locker ECC Bypass Implementation
## Date: October 5, 2025

## Issue
Evidence Locker has duplicate `_call_out_to_ecc` methods and needs ECC bypass for headless operation.

## Location
**File:** `F:\The Central Command\Evidence Locker\evidence_locker_main.py`  
**Method:** `_call_out_to_ecc` at line ~1878

## Required Change
Add ECC bypass immediately after the docstring (around line 1910):

```python
def _call_out_to_ecc(self, operation: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Call out to ECC for permission to perform operation"""
    # ECC bypass for headless operation
    if not self.ecc:
        self.logger.info("ECC not available - operating in headless mode for %s", operation)
        return {"permission_granted": True, "request_id": None}
    
    # Continue with normal ECC call-out logic...
    try:
        if not self.ecc:
            # Existing code...
```

## Why This Is Needed
Based on your architecture:
1. **Evidence Locker** scans evidence parcels
2. **ECC** designates whether tags/classifications are correct  
3. **Gateway Controller** moves evidence through pipeline on section-aware path

Evidence Locker MUST be able to scan and classify evidence even if ECC is unavailable. ECC approval is for validation, not initialization. Without bypass:
- System crashes if ECC unavailable during init
- Evidence scanning halts if ECC disconnects
- Single point of failure

## Manual Fix Required
Due to duplicate methods in file, manual edit needed:
1. Open `evidence_locker_main.py`
2. Find `_call_out_to_ecc` method at line 1878
3. After docstring at line 1910, add the bypass code shown above
4. Test headless operation

## Next Steps After Fix
1. Add standardized signal emissions using `shared_interfaces.py`
2. Use `StandardEvidenceData` for evidence payloads
3. Add signal validation
4. Test ECC-approved vs headless modes


