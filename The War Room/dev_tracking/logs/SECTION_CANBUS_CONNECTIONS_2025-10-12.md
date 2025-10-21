# SECTION CANBUS CONNECTIONS IMPLEMENTATION
**Date:** 2025-10-12  
**Agent:** NETWORK  
**Status:** IN PROGRESS (2/8 complete)

---

## OBJECTIVE

Add direct CANBUS connection initialization to all 8 section frameworks, matching parent module pattern (Evidence Locker, Marshall, Warden, Mission Debrief).

**User requirement:** *"just like the primary parent modules they need a direct section for canbus connection. this must be at the top of each sections code."*

---

## IMPLEMENTATION PATTERN

### Required Changes per Section:

**1. Update __init__ signature:**
```python
def __init__(
    self,
    gateway: Any,
    ecc: Optional[Any] = None,
    bus: Optional[Any] = None,  # NEW
    communicator: Optional[Any] = None  # NEW
) -> None:
```

**2. Add CANBUS initialization at top:**
```python
# ------------------------------------------------------------------ #
# CANBUS CONNECTION (SECTION MODULE - INLINE)
# ------------------------------------------------------------------ #
self.bus = bus
self.communicator = communicator
self.bus_connected = False
self.MODULE_ADDRESS = "4-X"  # Section-specific

if self.bus:
    self._initialize_canbus(self.bus, communicator=self.communicator)
```

**3. Add _initialize_canbus() method:**
- Import UniversalCommunicator
- Create communicator if not provided
- Register system address with capabilities
- Register signal handlers
- Set bus_connected = True

**4. Add signal handlers:**
- `_register_signal_handlers()`
- `_handle_evidence_request()`
- `_handle_wake_signal()`
- `_handle_sleep_signal()`
- `_handle_status_signal()`

**5. Add self-test with bus:**
- `_run_startup_self_test()` - validates tools
- Emits fault codes via `self.communicator.send_signal()`

---

## COMPLETION STATUS

| Section | Address | Status | Tools Count | Notes |
|---------|---------|--------|-------------|-------|
| Section 1 | 4-1 | ✅ COMPLETE | 10 | Modern framework - self-test already existed |
| Section 2 | 4-2 | ✅ COMPLETE | 7 | Legacy framework - added full bus + self-test |
| Section 3 | 4-3 | ⏳ IN PROGRESS | 11 | Legacy framework |
| Section 4 | 4-4 | ⏳ PENDING | 11 | Legacy framework |
| Section 5 | 4-5 | ⏳ PENDING | 4 | Legacy framework |
| Section 6 | 4-6 | ⏳ PENDING | 9 | Legacy framework |
| Section 7 | 4-7 | ⏳ PENDING | 0 | Legacy framework (minimal tools) |
| Section 8 | 4-8 | ⏳ PENDING | 6 | Legacy framework |

---

## KEY DIFFERENCES: Modern vs Legacy Frameworks

### Modern Framework (Section 1):
- Inherits from `SectionFramework` base class
- Already had `communicator_initializer` parameter pattern
- Self-test already implemented
- **Change:** Switched from `communicator_initializer` to direct `bus` parameter

### Legacy Framework (Sections 2-8):
- Inherits from `LegacySectionFramework`
- Simple `__init__(gateway, ecc)` signature
- NO bus connection capability
- NO self-test implementation
- **Change:** Added bus parameters + full CANBUS initialization + self-test

---

## CANBUS CAPABILITIES REGISTERED

Each section registers with these capabilities:
```python
{
    "system_type": "section_engine",
    "capabilities": [
        "evidence_request",    # Can request evidence from Evidence Locker
        "evidence_processing", # Can process received evidence
        "section_rendering",   # Can generate section output
        "fault_reporting"      # Can report faults to Marshall/UDS
    ],
    "status": "active",
    "section_name": "...",    # Human-readable name
    "tools": [...]            # List of tool dependencies
}
```

---

## SIGNAL TOPICS REGISTERED

Each section registers these handlers:
- `section_X.evidence_request` - Evidence request from section
- `section_X.wake` - Wake command from Marshall
- `section_X.sleep` - Sleep command from Marshall
- `section_X.status` - Status query from UDS/Marshall

---

## EVIDENCE FLOW WITH CANBUS

**Before (no bus):**
```
Section → Gateway (method call) → Evidence Locker
```
- Tight coupling
- No signal-based communication
- Cannot function independently

**After (with bus):**
```
Section → CANBUS (evidence.request signal) → Evidence Locker
Evidence Locker → CANBUS (evidence.deliver signal) → Section
```
- Loose coupling
- Signal-based communication
- Independent operation
- UDS can monitor evidence flow

---

## FAULT REPORTING WITH CANBUS

**Self-test failures now emit to Marshall:**
```python
self.communicator.send_signal(
    target_address="3",  # Marshall
    radio_code="SOS",
    message=f"{tool_name} initialization failed",
    payload={
        "fault_code": f"[{tool_addr}-12-INIT]",
        "description": "...",
        "reporting_address": tool_addr,
        "parent_address": self.MODULE_ADDRESS,
        "severity": "CRITICAL"
    }
)
```

**Marshall relays to UDS on CANBUS.**

---

## FILES MODIFIED

### Completed:
1. `F:\The Central Command\The Analyst Deck\Analyst 1\section_1_framework.py` ✅
2. `F:\The Central Command\The Analyst Deck\Analyst 2\section_2_framework.py` ✅

### Pending:
3. `F:\The Central Command\The Analyst Deck\Analyst 3\section_3_framework.py`
4. `F:\The Central Command\The Analyst Deck\Analyst 4\section_4_framework.py`
5. `F:\The Central Command\The Analyst Deck\Analyst 5\section_5_framework.py`
6. `F:\The Central Command\The Analyst Deck\Analyst 6\section_6_framework.py`
7. `F:\The Central Command\The Analyst Deck\Analyst 7\section_7_framework.py`
8. `F:\The Central Command\The Analyst Deck\Analyst 8\section_8_framework.py`

---

## NEXT STEPS

1. Complete Sections 3-8 CANBUS implementation
2. Update section tests to pass `bus` parameter
3. Update Gateway/Marshall to pass bus when creating sections
4. Validate evidence request/delivery flow via CANBUS
5. Test fault propagation: Section → Marshall → UDS

---

## ARCHITECTURE VALIDATION

**✓ Sections now match parent module pattern:**
- Direct CANBUS connection at top of code
- UniversalCommunicator created inline
- System address registered
- Signal handlers registered
- Self-test validates children/tools
- Fault codes emitted on CANBUS

**✓ Evidence flow now possible:**
- Sections can request evidence via `evidence.request` signal
- Evidence Locker can deliver via `evidence.deliver` signal
- No tight coupling to Gateway methods

**✓ UDS monitoring enabled:**
- Sections emit fault codes to Marshall
- Marshall relays to UDS on CANBUS
- UDS receives fault codes passively

---

**Resuming implementation of Sections 3-8...**

