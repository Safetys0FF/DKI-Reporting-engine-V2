# NETWORK AGENT — FAULT CODE TRIAGE GUIDE
**Agent:** `agent_2_NETWORK_CODING`  
**Purpose:** Determine which fault codes are NETWORK scope vs require handoff  
**Date:** 2025-10-09

---

## 🎯 NETWORK AGENT DESIGNATION

**Primary Responsibilities:**
- CANBUS communication integrity
- Signal routing and transmission
- Protocol compliance (UDS)
- System address registration
- Connection health monitoring

**NOT Responsible For:**
- System business logic
- Data processing algorithms
- Configuration/initialization
- Resource management
- External service integration

---

## 🔍 FAULT CODE TRIAGE MATRIX

### **NETWORK SCOPE** ✅ (Fix Immediately)

| Code Range | Category | Description | Action |
|------------|----------|-------------|--------|
| **XX-20** | Communication timeout | Signal not received within timeout | Increase timeout, check bus health |
| **XX-21** | Connection lost | Connection to target system lost | Reestablish connection, verify address |
| **XX-22** | Protocol error | Invalid protocol or format | Fix signal format, verify UDS compliance |
| **XX-23** | Signal not received | Expected signal not received | Check sender registration, verify handler |
| **XX-24** | Address not found | Target address not in registry | Register address, validate system connection |

**Resolution Authority:** NETWORK Agent handles directly

---

### **POWER AGENT SCOPE** 🔵 (Handoff Required)

| Code Range | Category | Description | Handoff Reason |
|------------|----------|-------------|----------------|
| **XX-01 to XX-05** | Configuration/Syntax | Config syntax errors, missing params, invalid values | System configuration ownership |
| **XX-30 to XX-34** | Data Processing | Processing errors, validation failures, parsing errors | Business logic implementation |
| **XX-50 to XX-53** | Business Logic | Business rule failures, workflow state issues | Application logic ownership |

**Handoff Target:** `agent_1_POWER_CODING`  
**Handoff Type:** REQUEST  
**Priority:** Based on fault severity

---

### **DEESCALATION AGENT SCOPE** 🟠 (Handoff Required)

| Code Range | Category | Description | Handoff Reason |
|------------|----------|-------------|----------------|
| **XX-10 to XX-14** | Initialization | Initialization failures, timeouts, missing dependencies | System stability/recovery |
| **XX-40 to XX-44** | Resource Management | Resource unavailable, exhausted, permission denied | Operational stability |
| **XX-60 to XX-63** | External Services | Service unavailable, timeout, auth failed, rate limits | External dependency management |
| **XX-70 to XX-74** | File System | File not found, access denied, locked, disk full | System resource management |
| **XX-80 to XX-83** | Database | DB connection, query timeout, transaction failures | Data layer stability |
| **XX-90 to XX-94** | Critical Failures | System crash, out of memory, disk full, hardware | Critical system recovery |

**Handoff Target:** `agent_3_DEESCALATION_CODING`  
**Handoff Type:** REQUEST (Normal) or EMERGENCY (90-94 codes)  
**Priority:** HIGH (90-94), MEDIUM (all others)

---

## 📋 TRIAGE WORKFLOW

### **Step 1: Detect Fault Code**
```
Receive fault signal → Parse fault code (e.g., "2-1-22")
                     ↓
Extract code category: -22 = Communication protocol error
```

### **Step 2: Determine Scope**
```
Check code range:
  - Is it XX-20 to XX-24? → NETWORK scope
  - Is it XX-01 to XX-05, XX-30 to XX-34, XX-50 to XX-53? → POWER scope
  - Is it all others? → DEESCALATION scope
```

### **Step 3: Take Action**
```
IF NETWORK scope:
  → Fix immediately
  → Log resolution
  → Continue testing

IF POWER/DEESCALATION scope:
  → Document fault details
  → Create handoff request
  → Submit to Handshakes folder
  → Log handoff
  → Continue with next system (don't block on out-of-scope issues)
```

---

## 📨 HANDOFF REQUEST PROTOCOL

### **When to Create Handoff**
- Any fault code outside XX-20 to XX-24 range
- Multiple faults from same system (batch handoff)
- Critical faults (XX-90 to XX-94) = IMMEDIATE handoff

### **Handoff Content Requirements**
- List of fault codes with descriptions
- System address and name
- Connection test results
- Suggested priority level
- Request type (NORMAL vs EMERGENCY)

### **Handoff Locations**
- **Template:** `F:\The Central Command\The War Room\dev_tracking\agent_2_NETWORK_CODING\Network Agent Directory\Handshake templates\request.md`
- **Submit to:** `F:\The Central Command\The War Room\dev_tracking\Handshakes\`
- **Filename format:** `HANDSHAKE_2025-10-09_NETWORK_to_{TARGET}_{SUBJECT}.md`

---

## 🔢 FAULT CODE EXAMPLES

### **NETWORK Agent Handles:**
```
2-1-22: Gateway Controller protocol error → Fix signal format
4-3-23: Section 3 signal not received → Verify handler registration
1-2-24: Evidence Manager address not found → Register system address
GUI-1-20: GUI communication timeout → Increase timeout, check connection
```

### **POWER Agent Handles:**
```
2-1-01: ECC configuration syntax error → Handoff CONFIG file fixes
4-5-30: Section 5 data processing error → Handoff BUSINESS LOGIC fixes
1-2-50: Evidence Manager business rule failed → Handoff LOGIC fixes
```

### **DEESCALATION Agent Handles:**
```
2-1-10: ECC initialization failed → Handoff RECOVERY procedures
4-1-90: Section 1 system crash → Handoff EMERGENCY recovery
GUI-1-40: GUI resource unavailable → Handoff RESOURCE management
3-1-80: Mission Debrief database connection failed → Handoff DATABASE fixes
```

---

## ✅ DECISION TREE

```
Fault Code Detected
       │
       ├─ XX-20 to XX-24? ──→ YES ──→ NETWORK fixes immediately
       │                      NO
       │                       ↓
       ├─ XX-01 to XX-05? ──→ YES ──→ Handoff to POWER
       ├─ XX-30 to XX-34? ──→ YES ──→ Handoff to POWER
       ├─ XX-50 to XX-53? ──→ YES ──→ Handoff to POWER
       │                      NO
       │                       ↓
       └─ All others ────────────→ Handoff to DEESCALATION
          (10-14, 40-44, 60-94)
```

---

**END OF TRIAGE GUIDE**

This guide ensures NETWORK Agent stays within CANBUS/connectivity designation and properly delegates out-of-scope faults.



