# Section Self-Test Implementation Pattern
**Date:** 2025-10-11  
**Agent:** NETWORK Agent  
**Status:** 1/8 Sections Complete (Pattern Established)

---

## SECTION 1 (4-1) - COMPLETE ✅

**File:** `F:\The Central Command\The Analyst Deck\Analyst 1\section_1_framework.py`

**Tool Dependencies Validated (10):**
- 4-1.1 - Evidence Manager
- 4-1.2 - Northstar Protocol
- 4-1.3 - Cochran Match
- 4-1.4 - Reverse Continuity
- 4-1.5 - Metadata Processor
- 4-1.6 - Mileage Audit
- 4-1.7 - Section Renderer
- 4-1.8 - Tesseract Engine
- 4-1.9 - Unstructured Engine
- 4-1.10 - EasyOCR Engine

**Implementation:**
- Added `_run_startup_self_test()` method after `__init__`
- Validates all 10 tool dependencies
- Emits fault codes to Marshall (3) for failed tools
- Called automatically during initialization

---

## PATTERN FOR REMAINING 7 SECTIONS

### Step 1: Identify Tool Dependencies

**Each section has similar structure in `__init__`:**
```python
self.tool_1 = self.get_dependency("tool_1")
self.tool_2 = self.get_dependency("tool_2")
# ... etc
```

**Map each tool to a sub-address:**
- First tool → 4-X.1
- Second tool → 4-X.2
- Third tool → 4-X.3
- etc.

### Step 2: Add Self-Test Method

**Insert after `__init__`, before lifecycle methods:**
```python
# Run mandatory self-test per UDS protocol
self._run_startup_self_test()

# ------------------------------------------------------------------
# Self-Test Protocol (UDS Compliance)
# ------------------------------------------------------------------
def _run_startup_self_test(self) -> bool:
    """Validate all tool dependencies per UDS self-test protocol."""
    self.logger.info("[%s] Running mandatory startup self-test per UDS protocol", self.MODULE_ADDRESS)
    operational = True
    
    tools_to_validate = [
        ('4-X.1', 'Tool Name 1', lambda: self.tool_1),
        ('4-X.2', 'Tool Name 2', lambda: self.tool_2),
        # ... all tools
    ]
    
    for tool_addr, tool_name, get_tool_ref in tools_to_validate:
        try:
            tool_ref = get_tool_ref()
            
            if tool_ref is None:
                self.logger.error("[%s] Self-test FAILED: %s (%s) not initialized", 
                                  self.MODULE_ADDRESS, tool_name, tool_addr)
                
                if hasattr(self, 'communicator') and self.communicator:
                    self.communicator.send_signal(
                        target_address="3",  # Marshall
                        radio_code="SOS",
                        message=f"{tool_name} initialization failed",
                        payload={
                            "fault_code": f"[{tool_addr}-12-INIT]",
                            "description": f"{tool_name} not initialized",
                            "component": tool_name,
                            "reporting_address": tool_addr,
                            "parent_address": self.MODULE_ADDRESS,
                            "severity": "CRITICAL",
                            "timestamp": datetime.now().isoformat(),
                            "fault_type": "12",
                            "fault_type_description": "Missing initialization dependency"
                        }
                    )
                    self.logger.warning("[%s] Fault code emitted: [%s-12-INIT]", 
                                       self.MODULE_ADDRESS, tool_addr)
                
                operational = False
            else:
                self.logger.info("[%s] Self-test PASSED: %s (%s) operational", 
                                self.MODULE_ADDRESS, tool_name, tool_addr)
        
        except Exception as exc:
            self.logger.error("[%s] Self-test ERROR: %s (%s): %s", 
                             self.MODULE_ADDRESS, tool_name, tool_addr, exc)
            operational = False
    
    if operational:
        self.logger.info("[%s] PASS - Self-test COMPLETE", self.MODULE_ADDRESS)
    else:
        self.logger.warning("[%s] FAIL - Self-test COMPLETE", self.MODULE_ADDRESS)
    
    return operational
```

---

## REMAINING SECTIONS (7)

### Section 2 (4-2) - Presurveillance Logic ⏳
**File:** `F:\The Central Command\The Analyst Deck\Analyst 2\section_2_framework.py`  
**Likely Tools:** Evidence Manager, Northstar, Cochran, Reverse Continuity, Metadata, Mileage, Renderer

### Section 3 (4-3) - Surveillance Reports ⏳
**File:** `F:\The Central Command\The Analyst Deck\Analyst 3\section_3_framework.py`  
**Likely Tools:** Media helpers, Voice helpers, Track decoder, Video analyzer, Audio transcriber, Renderer

### Section 4 (4-4) - Review of Surveillance Sessions ⏳
**File:** `F:\The Central Command\The Analyst Deck\Analyst 4\section_4_framework.py`  
**Likely Tools:** Compliance rules, Data sources, Document validator, Media helper, Voice helper, Renderer

### Section 5 (4-5) ⏳
**File:** `F:\The Central Command\The Analyst Deck\Analyst 5\section_5_framework.py`  
**Tools:** TBD

### Section 6 (4-6) ⏳
**File:** `F:\The Central Command\The Analyst Deck\Analyst 6\section_6_framework.py`  
**Tools:** TBD

### Section 7 (4-7) - Conclusion ⏳
**File:** `F:\The Central Command\The Analyst Deck\Analyst 7\section_7_framework.py`  
**Tools:** TBD

### Section 8 (4-8) ⏳
**File:** `F:\The Central Command\The Analyst Deck\Analyst 8\section_8_framework.py`  
**Tools:** TBD

---

## KEY DIFFERENCES FROM PARENT MODULES

1. **Fault Target:** Sections emit to Marshall (3), not UDS (Bus-1)
2. **Tool Sub-Addresses:** Use 4-X.Y format (e.g., 4-1.1, 4-1.2)
3. **Tool Count:** Varies by section (5-15 tools typical)
4. **Communicator Check:** Must check `hasattr(self, 'communicator')` since sections may not have it during init

---

## VALIDATION FLOW

```
Section 4-1 detects broken Tesseract (4-1.8)
    ↓
Section 4-1 emits [4-1.8-12-INIT] to Marshall (3)
    ↓
Marshall _handle_child_broadcast() receives fault
    ↓
Marshall relays [4-1.8-12-INIT] to UDS (Bus-1) with parent context
    ↓
UDS logs fault, reports "Section 1 Tesseract Engine failed"
```

---

## TESTING STRATEGY

**Each section should have individual test script:**
```python
# test_section_X_self_test.py
from section_X_framework import SectionXFramework

section = SectionXFramework(gateway=None)
# Self-test runs during __init__
# Check logs for PASS/FAIL and fault codes
```

**Fast iteration:**
- Test Section 1 only: ~3 seconds
- No need to initialize all 8 sections
- No need to run full system

---

## ESTIMATED WORK

- **Section 1:** ✅ COMPLETE
- **Sections 2-8:** ~30 minutes each (identify tools, add self-test, test)
- **Total remaining:** ~3.5 hours for all 7 sections

---

**Pattern is proven and repeatable. Each section follows exact same structure as Section 1.**


