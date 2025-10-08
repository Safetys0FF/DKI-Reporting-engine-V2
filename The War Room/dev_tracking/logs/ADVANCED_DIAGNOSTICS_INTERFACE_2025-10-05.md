# Advanced Diagnostics Interface
## Date: October 5, 2025

## **GUI Integration: Existing Health Monitor + Advanced Diagnostics**

The diagnostic system integrates with the **existing health monitor** in the GUI and adds **Advanced Diagnostics** for detailed fault analysis.

---

## **DIAGNOSTIC INTERFACE LAYOUT:**

### **Main Diagnostic Panel:**
```
┌─────────────────────────────────────────────────────────────┐
│ Central Command - Advanced Diagnostics                      │
├─────────────────────────────────────────────────────────────┤
│ File  Edit  View  Tools  Help                               │
├─────────────────────────────────────────────────────────────┤
│ [System Status] [Communication] [Fault Log] [Radio Check]   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  System Address Registry:                                   │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Bus-1    │ Central Command Bus        │ ACTIVE   │ 00   │ │
│  │ 1-1      │ Evidence Locker Main       │ ACTIVE   │ 00   │ │
│  │ 1-1.1    │ Evidence Classifier        │ ACTIVE   │ 00   │ │
│  │ 2-1      │ Ecosystem Controller       │ FAULT    │ 01   │ │
│  │ 2-1.1    │ ECC State Manager          │ ACTIVE   │ 00   │ │
│  │ 3-1      │ Mission Debrief Manager    │ ACTIVE   │ 00   │ │
│  │ 4-1      │ Section 1 Framework        │ ACTIVE   │ 00   │ │
│  │ 5-1      │ Gateway                    │ ACTIVE   │ 00   │ │
│  │ 6-1      │ Dev Environment            │ ACTIVE   │ 00   │ │
│  │ 7-1      │ Enhanced Functional GUI    │ ACTIVE   │ 00   │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
│  [Rollcall All Systems] [Radio Check Selected] [Clear Logs] │
├─────────────────────────────────────────────────────────────┤
│ Active Faults:                                              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 2-1-01-102-170 │ ECC Config Syntax Error               │ │
│ │ Time: 2025-10-05 14:23:15                              │ │
│ │ Location: ecosystem_controller.py lines 102-170        │ │
│ │ Status: ACTIVE                                          │ │
│ │ [View Details] [Attempt Fix] [Ignore]                  │ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ Communication Log:                                          │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 14:23:15 │ 2-1 → Bus-1 │ SOS │ 2-1-01-102-170        │ │
│ │ 14:23:16 │ Bus-1 → 7-1.7 │ ALERT │ Fault notification  │ │
│ │ 14:23:17 │ 7-1.7 → 2-1 │ 10-4 │ Fault acknowledged   │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## **DIAGNOSTIC INTERFACE FEATURES:**

### **1. System Address Registry Panel**
- **Real-time status** of all systems
- **Current diagnostic codes** (00 = normal, others = faults)
- **Click to select** system for detailed diagnostics
- **Color coding**: Green (active), Red (fault), Yellow (warning)

### **2. Active Faults Panel**
- **Current active faults** with full diagnostic codes
- **Fault details** including line numbers and descriptions
- **Action buttons**: View Details, Attempt Fix, Ignore
- **Fault resolution tracking**

### **3. Communication Log Panel**
- **Real-time communication** between systems
- **Radio code tracking** (10-4, 10-6, 10-8, etc.)
- **SOS fault broadcasts** and responses
- **Communication timeline** with timestamps

### **4. Diagnostic Tools**
- **Rollcall All Systems** - Broadcast rollcall to all systems
- **Radio Check Selected** - Test communication with selected system
- **Clear Logs** - Clear communication and fault logs
- **Export Diagnostics** - Export diagnostic data for analysis

---

## **ADVANCED DIAGNOSTIC FEATURES:**

### **1. Fault Detail Window**
```
┌─────────────────────────────────────────────────────────────┐
│ Fault Details: 2-1-01-102-170                              │
├─────────────────────────────────────────────────────────────┤
│ System: ECC (Ecosystem Controller)                          │
│ Fault Code: 01 (Syntax error in configuration file)        │
│ Location: ecosystem_controller.py lines 102-170            │
│ Timestamp: 2025-10-05 14:23:15                             │
│ Status: ACTIVE                                              │
├─────────────────────────────────────────────────────────────┤
│ Error Details:                                              │
│ Invalid JSON syntax in dependency_config.json              │
│ Line 156: Missing closing brace '}'                        │
│ Expected: {"dependency": "gateway_controller"}             │
│ Found: {"dependency": "gateway_controller"                 │
├─────────────────────────────────────────────────────────────┤
│ [Attempt Auto-Fix] [Manual Fix] [Ignore] [Close]           │
└─────────────────────────────────────────────────────────────┘
```

### **2. Radio Check Results**
```
┌─────────────────────────────────────────────────────────────┐
│ Radio Check Results                                         │
├─────────────────────────────────────────────────────────────┤
│ Target: 2-1 (ECC)                                          │
│ Response Time: 45ms                                        │
│ Status: FAILED                                             │
│ Diagnostic Code: 2-1-01-102-170                           │
│ Message: Configuration syntax error                        │
├─────────────────────────────────────────────────────────────┤
│ [Retry] [View Details] [Close]                             │
└─────────────────────────────────────────────────────────────┘
```

### **3. Rollcall Results**
```
┌─────────────────────────────────────────────────────────────┐
│ Rollcall Results - 2025-10-05 14:25:00                     │
├─────────────────────────────────────────────────────────────┤
│ Total Systems: 50                                          │
│ Responding: 49                                             │
│ Failed: 1                                                  │
├─────────────────────────────────────────────────────────────┤
│ Failed Systems:                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 2-1 │ ECC │ 2-1-01-102-170 │ Config syntax error      │ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ [Retry Rollcall] [Export Results] [Close]                  │
└─────────────────────────────────────────────────────────────┘
```

---

## **ACCESS CONTROL:**

### **User Permissions:**
- **Normal Users**: No access to Advanced Diagnostics
- **System Administrators**: Full access to all diagnostic features
- **Developers**: Full access + ability to modify diagnostic settings
- **Audit Log**: Track who accessed diagnostics and when

### **Security Features:**
- **Authentication required** to access Advanced Diagnostics
- **Session timeout** after 30 minutes of inactivity
- **Audit logging** of all diagnostic actions
- **Read-only mode** for non-admin users

---

## **INTEGRATION WITH EXISTING GUI:**

## **HEALTH MONITOR INTEGRATION:**

### **Existing Health Monitor Display:**
```
┌─────────────────────────────────────────────────────────────┐
│ System Health Monitor                                       │
├─────────────────────────────────────────────────────────────┤
│ Evidence Locker    │ [OK]     │ 1-1-00                     │
│ ECC               │ [ERROR]  │ 2-1-01-102-170             │
│ Gateway Controller │ [OK]     │ 2-2-00                     │
│ Mission Debrief   │ [OK]     │ 3-1-00                     │
│ Section 1         │ [OK]     │ 4-1-00                     │
│ Section 2         │ [FAILURE]│ 4-2-80-156                 │
│ GUI               │ [OK]     │ 7-1-00                     │
└─────────────────────────────────────────────────────────────┘
```

### **Health Status Definitions:**
- **OK** (Green) - System operational, no faults
- **ERROR** (Yellow) - Fault detected but system still operational
- **FAILURE** (Red) - Fault interrupts system performance

### **Menu Structure:**
```
Enhanced Functional GUI
├── Case Management
├── Evidence Display
├── Section Review
├── Report Generation
├── System Status
│   └── Health Monitor          ← Existing health monitor
└── Systems
    ├── Settings
    ├── Advanced Settings
    │   └── Diagnostics          ← Detailed fault analysis
    └── Maintenance
```

### **Health Monitor Features:**
- **Real-time status** of all systems
- **Color-coded indicators** (Green/Yellow/Red)
- **Diagnostic codes** displayed for faults
- **Click to expand** for fault details
- **Quick access** to Advanced Diagnostics

This creates a **professional diagnostic interface** that's separate from normal user operations but easily accessible for system administration and troubleshooting!
