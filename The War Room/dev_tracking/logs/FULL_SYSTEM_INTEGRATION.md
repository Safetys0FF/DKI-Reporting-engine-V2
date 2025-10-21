# GUI Full System Integration - CANBUS, Parent Modules, UDS
**Date:** October 10, 2025  
**Critical:** GUI must integrate as parent module, not standalone UI

---

## Current Reality Check

### GUI Must Communicate With

1. **CANBUS** - Register as GUI-1, emit/receive signals
2. **Evidence Locker** (1) - Receive evidence events, request manifests
3. **Warden** (2-1) - Coordinate with Gateway/ECC, get permissions
4. **Marshall** (3) - Request evidence distribution, receive status
5. **Mission Debrief** (5) - Trigger reports, receive outputs
6. **UDS** - Be monitored, emit radio codes, report health

### GUI Is Currently Missing

- ✗ Not registered as parent module (GUI-1)
- ✗ No `_handle_child_broadcast` implementation
- ✗ No radio code emissions to UDS
- ✗ Children don't emit to `gui.child.broadcast`
- ✗ Not in system_registry.json
- ✗ Not monitored by UDS

---

## Architecture Layer: GUI as Parent Module

### System Hierarchy (From Protocol Registry)

```
GUI-1 (Parent Module)
├── GUI-1.1  User Interface Controller
├── GUI-1.2  Case Management Interface
├── GUI-1.3  Evidence Display Interface
├── GUI-1.4  Section Review Interface
├── GUI-1.5  Report Generation Interface
├── GUI-1.6  System Status Interface
├── GUI-1.7  Error Display Interface
├── GUI-1.8  Progress Monitoring Interface
└── GUI-1.9  Health Monitor
```

**From `system_protocol_registry.py`:**
```python
"gui": {
    "address": "GUI-1",
    "wildcard_signal": "gui.child.broadcast",
    "handler_method": "_handle_child_broadcast",
    "translations": {
        "user_action": [
            {"signal": "gui.user.action", "radio_code": None, "description": "User initiated action"}
        ],
        "view_changed": [
            {"signal": "gui.view.changed", "radio_code": None, "description": "GUI view/tab changed"}
        ],
        "error_displayed": [
            {"signal": "gui.error.displayed", "radio_code": None, "description": "Error shown to user"}
        ],
        "progress_updated": [
            {"signal": "gui.progress.updated", "radio_code": None, "description": "Progress indicator updated"}
        ]
    }
}
```

---

## Integration Point 1: CANBUS Registration

### Current (Incomplete)
```python
# enhanced_functional_gui.py (lines 3382-3395)
def main(argv):
    bus = None
    try:
        from bus_core import DKIReportBus
        bus = DKIReportBus()
    except Exception as e:
        print(f"WARNING: Failed to initialize CANBUS: {e}")
        print("GUI will launch in SAFEMODE")
    
    gui = EnhancedDKIGUI(bus=bus)
    gui.mainloop()
```

**Problem:** Bus exists, but GUI never registers itself as parent module.

### Required (Complete)
```python
# gui_controller.py (NEW)
class GUIController:
    def __init__(self, bus, operator_profile):
        self.bus = bus
        self.operator_profile = operator_profile
        self.module_address = "GUI-1"
        
        # Initialize UniversalCommunicator
        self.communicator = self._init_communicator()
        
        # Register with CANBUS as parent module
        self._register_to_canbus()
        
        # Register signal handlers
        self._register_handlers()
    
    def _init_communicator(self):
        """Initialize UniversalCommunicator for GUI-1"""
        sys.path.insert(0, str(Path(__file__).parent.parent / "Data Bus"))
        from universal_communicator import UniversalCommunicator
        
        communicator = UniversalCommunicator(
            module_address=self.module_address,
            bus_connection=self.bus
        )
        
        logger.info(f"[OK] GUI-1 communicator initialized")
        return communicator
    
    def _register_to_canbus(self):
        """Register GUI-1 as parent module on CANBUS"""
        if not self.bus:
            logger.warning("No bus connection, running in SAFEMODE")
            return
        
        try:
            # Register parent module
            self.bus.register_module(
                module_id=self.module_address,
                module_type="gui_parent",
                capabilities=["user_interface", "case_management", "system_monitoring"]
            )
            
            # Emit ROLLCALL signal to announce presence
            self.communicator.send_signal(
                target_address="Bus-1",
                signal_name="module.registered",
                radio_code=RadioCode.ROLLCALL,
                payload={
                    "module_address": self.module_address,
                    "operator": self.operator_profile.name,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            logger.info(f"[OK] GUI-1 registered to CANBUS")
        
        except Exception as e:
            logger.error(f"Failed to register to CANBUS: {e}")
    
    def _register_handlers(self):
        """Register signal handlers for CANBUS communication"""
        # Listen for wildcard from children
        self.communicator.register_handler(
            "gui.child.broadcast",
            self._handle_child_broadcast
        )
        
        # Listen for signals from other parent modules
        self.communicator.register_handler("evidence.classified", self._on_evidence_classified)
        self.communicator.register_handler("case.created", self._on_case_created)
        self.communicator.register_handler("section.routed", self._on_section_routed)
        self.communicator.register_handler("report.ready", self._on_report_ready)
        
        # Listen for UDS health checks
        self.communicator.register_handler("uds.health_check", self._on_health_check)
        
        logger.info("[OK] Signal handlers registered")
```

---

## Integration Point 2: Parent Module Translation

### Implementation (Matches Other Parents)
```python
# gui_controller.py
def _handle_child_broadcast(self, payload: Dict[str, Any]) -> None:
    """
    Handle child component broadcasts and translate to universal CANBUS signals.
    
    This matches Evidence Locker, Warden, Marshall, Mission Debrief pattern.
    Children emit to gui.child.broadcast, parent translates to universal signals.
    """
    message_type = payload.get('message_type')
    if not message_type:
        logger.warning("[WARN] Child broadcast missing message_type")
        return
    
    logger.info(f"[SIGNAL] GUI-1 received child broadcast: {message_type}")
    
    # Translate based on protocol registry definitions
    if message_type == "user_action":
        self.communicator.send_signal(
            target_address="Bus-1",
            signal_name="gui.user.action",
            payload=payload
        )
        logger.info("[OK] Translated user_action to gui.user.action")
    
    elif message_type == "view_changed":
        self.communicator.send_signal(
            target_address="Bus-1",
            signal_name="gui.view.changed",
            payload=payload
        )
        logger.info("[OK] Translated view_changed to gui.view.changed")
    
    elif message_type == "error_displayed":
        self.communicator.send_signal(
            target_address="Bus-1",
            signal_name="gui.error.displayed",
            payload=payload
        )
        logger.info("[OK] Translated error_displayed to gui.error.displayed")
    
    elif message_type == "progress_updated":
        self.communicator.send_signal(
            target_address="Bus-1",
            signal_name="gui.progress.updated",
            payload=payload
        )
        logger.info("[OK] Translated progress_updated to gui.progress.updated")
    
    elif message_type == "case_created":
        # This is important - user creates case via GUI, needs to go to Evidence Locker
        self.communicator.send_signal(
            target_address="1",  # Evidence Locker
            signal_name="case.new",
            radio_code=RadioCode.TEN_SIX,  # Evidence received
            payload=payload
        )
        logger.info("[OK] Translated case_created to case.new (to Evidence Locker)")
    
    elif message_type == "evidence_uploaded":
        # User uploads evidence via GUI, route to Evidence Locker
        self.communicator.send_signal(
            target_address="1",  # Evidence Locker
            signal_name="evidence.ingest",
            radio_code=RadioCode.TEN_SIX,  # Evidence received
            payload=payload
        )
        logger.info("[OK] Translated evidence_uploaded to evidence.ingest")
    
    elif message_type == "report_requested":
        # User requests report, signal to Mission Debrief
        self.communicator.send_signal(
            target_address="5",  # Mission Debrief
            signal_name="report.generate",
            radio_code=RadioCode.TEN_FOUR,  # Acknowledged
            payload=payload
        )
        logger.info("[OK] Translated report_requested to report.generate")
    
    else:
        logger.warning(f"[WARN] Unknown child message type: {message_type}")
```

---

## Integration Point 3: Parent Module Communication

### Receive Signals from Other Parents
```python
# gui_controller.py
def _on_evidence_classified(self, payload: Dict[str, Any]) -> None:
    """Evidence Locker classified new evidence - update GUI"""
    evidence_id = payload.get("evidence_id")
    classification = payload.get("classification")
    
    logger.info(f"[SIGNAL] Evidence classified: {evidence_id} as {classification}")
    
    # Update GUI state
    self.update_state("last_evidence", payload)
    
    # Notify components that care about evidence
    self.route_signal("evidence.classified", payload)
    
    # Show notification to user
    self._show_notification(f"Evidence {evidence_id} processed", "info")

def _on_case_created(self, payload: Dict[str, Any]) -> None:
    """Evidence Locker created case - update GUI"""
    case_id = payload.get("case_id")
    
    logger.info(f"[SIGNAL] Case created: {case_id}")
    
    # Set as active case
    self.update_state("active_case_id", case_id)
    self.update_state("active_case", payload)
    
    # Notify components
    self.route_signal("case.created", payload)

def _on_section_routed(self, payload: Dict[str, Any]) -> None:
    """Warden routed section for processing - show progress"""
    section_id = payload.get("section_id")
    
    logger.info(f"[SIGNAL] Section routed: {section_id}")
    
    # Update progress display
    self._update_progress(section_id, "processing")

def _on_report_ready(self, payload: Dict[str, Any]) -> None:
    """Mission Debrief completed report - notify user"""
    report_id = payload.get("report_id")
    
    logger.info(f"[SIGNAL] Report ready: {report_id}")
    
    # Show notification
    self._show_notification("Report generation complete", "success")
    
    # Emit radio code to UDS (report completed)
    self.communicator.send_signal(
        target_address="Bus-1",
        radio_code=RadioCode.TEN_EIGHT,  # Evidence complete
        payload={"report_id": report_id}
    )
```

---

## Integration Point 4: UDS Communication

### Health Monitoring
```python
# gui_controller.py
def _on_health_check(self, payload: Dict[str, Any]) -> None:
    """UDS health check - respond with status"""
    health_status = self._get_health_status()
    
    # Respond to UDS
    self.communicator.send_signal(
        target_address="Bus-1.5",  # UDS
        signal_name="module.health",
        radio_code=RadioCode.STATUS,
        payload={
            "module_address": self.module_address,
            "status": health_status["status"],
            "components_active": health_status["active_components"],
            "operator": self.operator_profile.name,
            "uptime": health_status["uptime"],
            "memory_usage": health_status["memory_mb"]
        }
    )
    
    logger.info(f"[UDS] Health check response: {health_status['status']}")

def _get_health_status(self) -> Dict[str, Any]:
    """Calculate GUI health status for UDS"""
    active_components = len([c for c in self.components.values() if c._state == UIComponentState.ACTIVE])
    
    # Check if bus connected
    bus_connected = self.bus is not None and self.communicator is not None
    
    # Determine overall status
    if not bus_connected:
        status = "SAFEMODE"
    elif active_components == 0:
        status = "IDLE"
    elif active_components > 0:
        status = "OPERATIONAL"
    else:
        status = "UNKNOWN"
    
    return {
        "status": status,
        "active_components": active_components,
        "uptime": time.time() - self.start_time,
        "memory_mb": self._get_memory_usage()
    }

def _emit_fault(self, fault_code: str, description: str):
    """Emit fault to UDS (like sections do)"""
    self.communicator.send_signal(
        target_address="Bus-1.5",  # UDS
        signal_name="module.fault",
        radio_code=RadioCode.SOS,  # Emergency
        payload={
            "module_address": self.module_address,
            "fault_code": fault_code,
            "description": description,
            "timestamp": datetime.now().isoformat()
        }
    )
    
    logger.error(f"[FAULT] {fault_code}: {description}")
```

---

## Integration Point 5: Child Components Emitting to Parent

### Component Implementation
```python
# components/case_management_panel.py (REFACTORED)
class CaseManagementPanel(UIComponentFramework):
    def __init__(self, parent, gui_controller, communicator, **kwargs):
        super().__init__(parent, gui_controller, communicator, **kwargs)
        self.gui_controller = gui_controller
        self.communicator = communicator
    
    def new_case(self):
        """User creates new case - emit to parent via wildcard"""
        case_data = self._collect_case_data()
        
        # Emit to parent wildcard (gui.child.broadcast)
        self.communicator.send_signal(
            target_address="GUI-1",
            signal_name="gui.child.broadcast",
            payload={
                "message_type": "case_created",  # Parent translates this
                "source_component": "GUI-1.2",   # Case Management Interface
                "case_data": case_data
            }
        )
        
        logger.info("[OK] Emitted case_created to parent")
    
    def on_files_dropped(self, files):
        """User uploads evidence - emit to parent"""
        self.communicator.send_signal(
            target_address="GUI-1",
            signal_name="gui.child.broadcast",
            payload={
                "message_type": "evidence_uploaded",
                "source_component": "GUI-1.2",
                "files": files,
                "case_id": self.current_case_info.get("case_id")
            }
        )
        
        logger.info(f"[OK] Emitted evidence_uploaded to parent ({len(files)} files)")
```

---

## Complete Communication Flow Example

### User Uploads Evidence

```
1. User drags files to FileDropZone (GUI-1.3 Evidence Display Interface)
        ↓
2. FileDropZone component emits to parent:
   signal_name: "gui.child.broadcast"
   payload: {
       "message_type": "evidence_uploaded",
       "source_component": "GUI-1.3",
       "files": ["photo1.jpg", "photo2.jpg"],
       "case_id": "CASE-001"
   }
        ↓
3. GUIController._handle_child_broadcast() receives wildcard
        ↓
4. Translates to universal signal:
   target_address: "1" (Evidence Locker)
   signal_name: "evidence.ingest"
   radio_code: RadioCode.TEN_SIX (Evidence received)
        ↓
5. Evidence Locker receives signal
        ↓
6. Evidence Locker processes files, classifies
        ↓
7. Evidence Locker emits:
   signal_name: "evidence.classified"
   radio_code: RadioCode.TEN_FOUR (Acknowledged)
        ↓
8. GUIController._on_evidence_classified() receives signal
        ↓
9. GUI updates display, shows "Evidence processed" notification
        ↓
10. UDS monitors entire flow via radio codes
```

---

## System Registry Entry

**GUI must be in `system_registry.json`:**
```json
{
  "name": "Enhanced Functional GUI",
  "address": "GUI-1",
  "handler": "enhanced_functional_gui.EnhancedDKIGUI",
  "location": "F:\\The Central Command\\Command Center\\UI\\enhanced_functional_gui.py",
  "parent": "none",
  "status": "ACTIVE",
  "last_check": "2025-10-10",
  "children": [
    "GUI-1.1",
    "GUI-1.2",
    "GUI-1.3",
    "GUI-1.4",
    "GUI-1.5",
    "GUI-1.6",
    "GUI-1.7",
    "GUI-1.8",
    "GUI-1.9"
  ]
}
```

---

## Implementation Checklist

### Phase 1: GUIController with CANBUS
- [ ] Create `gui_controller.py`
- [ ] Initialize UniversalCommunicator
- [ ] Register to CANBUS as GUI-1
- [ ] Implement `_handle_child_broadcast()`
- [ ] Register signal handlers for parent modules

### Phase 2: Signal Translation
- [ ] Implement translation for all GUI message types
- [ ] Add radio code emissions to UDS
- [ ] Handle signals from Evidence Locker
- [ ] Handle signals from Warden
- [ ] Handle signals from Marshall
- [ ] Handle signals from Mission Debrief

### Phase 3: UDS Integration
- [ ] Implement health check responses
- [ ] Add fault emission capability
- [ ] Track component lifecycle for health status
- [ ] Emit STATUS radio codes periodically

### Phase 4: Component Refactoring
- [ ] Update components to inherit UIComponentFramework
- [ ] Change components to emit to gui.child.broadcast
- [ ] Remove direct callback patterns
- [ ] Use signal protocol instead

### Phase 5: Registration
- [ ] Add GUI-1 to system_registry.json
- [ ] Update protocol registry (already done in system_protocol_registry.py)
- [ ] Test UDS discovers GUI-1
- [ ] Verify GUI appears in system health checks

---

## Testing Validation

### Test 1: CANBUS Registration
```python
# Should see in logs:
[OK] GUI-1 communicator initialized
[OK] GUI-1 registered to CANBUS
[ROLLCALL] GUI-1 announced presence
```

### Test 2: Child-to-Parent Signal
```python
# User creates case
[SIGNAL] GUI-1 received child broadcast: case_created
[OK] Translated case_created to case.new (to Evidence Locker)
[10-6] Evidence received
```

### Test 3: Parent-to-GUI Signal
```python
# Evidence Locker processes evidence
[SIGNAL] Evidence classified: EV-001 as document
[OK] GUI updated: case CASE-001 has new evidence
```

### Test 4: UDS Monitoring
```python
# UDS health check
[UDS] Health check request received
[STATUS] GUI-1: OPERATIONAL, 6 components active
[OK] Health response sent to UDS
```

---

## Summary

**GUI Must Be:**
1. ✓ Registered to CANBUS as GUI-1 parent module
2. ✓ Implementing `_handle_child_broadcast()` translation
3. ✓ Emitting radio codes to UDS for monitoring
4. ✓ Receiving signals from Evidence Locker, Warden, Marshall, Mission Debrief
5. ✓ Having children emit to `gui.child.broadcast` wildcard
6. ✓ Listed in system_registry.json
7. ✓ Monitored by UDS like all other parent modules

**This makes GUI a first-class parent module, not just a UI layer.**

---

**Ready to implement full integration?**

