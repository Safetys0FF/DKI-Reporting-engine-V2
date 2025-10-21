# GUI Architecture Blueprint - Full System Integration
**Date:** October 10, 2025  
**Analysis:** Report Engine → GUI mapping for complete system cohesion

---

## Report Engine Full Architecture (What We're Mirroring)

### Layer 1: Foundation

```
section_framework_base.py
├── LifecycleState (enum)
├── StageDefinition (dataclass)
├── CommunicationContract (dataclass)
├── OrderContract (dataclass)
├── PersistenceContract (dataclass)
├── FactGraphContract (dataclass)
└── SectionFramework (base class)
    ├── __init__(gateway, dependencies, communicator, etc.)
    ├── lifecycle_state()
    ├── initialize_dependencies()
    ├── transition_state()
    └── bus_section_id()
```

**Purpose:** Standardized base all sections inherit from

---

### Layer 2: Individual Sections

```
Section 1 (Analyst 1/)
├── _init_metadata_processor.py       ← Lazy loaders
├── _init_section_renderer.py         ← Lazy loaders
├── section_1_framework.py             ← Inherits SectionFramework
│   ├── SECTION_ID = "section_1_profile"
│   ├── MODULE_ADDRESS = "4-1"
│   ├── STAGES = (acquire, extract, normalize, validate, publish, monitor)
│   ├── COMMUNICATION = CommunicationContract(...)
│   ├── ORDER = OrderContract(execution_after=["section_cp", "section_toc"])
│   └── __init__(gateway, dependency_initializers={...})
└── tool kit/
    └── metadata_tool_v_5.py           ← Actual tools
```

**Purpose:** Self-contained execution units with declared contracts

---

### Layer 3: Central Orchestration

```
GatewayController (The Warden/gateway_controller.py)
├── __init__(ecosystem_controller, bus)
├── evidence_index: Dict                ← Master evidence registry
├── section_registry: Dict              ← All registered sections
├── signal_queue: List[Signal]          ← Inter-section communication
├── route_section(section_id, evidence) ← Dispatches work to sections
├── publish_section_result(...)         ← Receives section outputs
├── emit_signal(...)                    ← Coordinates signals
└── get_section_inputs(section_id)      ← Provides section data
```

**Purpose:** Owns master state, coordinates all sections

---

### Layer 4: Execution Control

```
EcosystemController (The Warden/ecosystem_controller.py)
├── Permission Control                   ← Sections ask "Can I run?"
├── Execution Order Enforcement          ← Based on OrderContract
├── Resource Management                  ← Queue, throttle, prioritize
├── Dependency Resolution                ← "Section 1 needs Section CP first"
└── State Tracking                       ← What's running, what's blocked
```

**Purpose:** Decides WHO runs WHEN and with WHAT permissions

---

### Layer 5: Communication Bus

```
UniversalCommunicator (Command Center/Data Bus/)
├── send_signal(address, signal, payload)
├── register_handler(signal_name, callback)
├── broadcast(signal_name, payload)
└── Radio codes (10-4, 10-6, 10-8, etc.)
```

**Purpose:** Signal routing between all modules

---

## Full Data Flow Example

```
User uploads evidence
        ↓
Evidence Locker ingests → emits "evidence.classified"
        ↓
Gateway Controller receives signal
        ↓
Gateway adds to evidence_index
        ↓
Gateway asks ECC: "Can Section 1 run?"
        ↓
ECC checks OrderContract: "Need section_cp, section_toc first"
        ↓
ECC: "Section CP clear to run"
        ↓
Section CP framework:
    1. initialize_dependencies() → loads _init_* tools
    2. run stage: acquire
    3. run stage: extract
    4. run stage: publish → emits "section_cp.completed"
        ↓
Gateway receives "section_cp.completed"
        ↓
ECC updates state: "CP done, unlock Section 1"
        ↓
Section 1 framework:
    1. initialize_dependencies()
    2. run stages...
    3. publish → emits "section_1_profile.completed"
        ↓
Gateway coordinates next sections...
        ↓
All sections complete
        ↓
Mission Debrief assembles final report
```

---

## GUI Equivalent Architecture

### Layer 1: GUI Foundation (NEW)

```python
# gui_framework_base.py
class UIComponentState(Enum):
    CREATED = auto()
    INITIALIZING = auto()
    ACTIVE = auto()
    HIDDEN = auto()
    DISABLED = auto()
    ERROR = auto()

@dataclass(frozen=True)
class VisibilityContract:
    """Which roles can see this component"""
    required_role: str  # "basic", "analyst", "supervisor", "admin"
    required_permissions: Tuple[str, ...]  # ["view_cases", "edit_reports"]
    conditional_display: Optional[Callable] = None  # Custom logic

@dataclass(frozen=True)
class DataContract:
    """What data this component needs/provides"""
    input_signals: Tuple[str, ...]   # ["case.selected", "evidence.loaded"]
    output_signals: Tuple[str, ...]  # ["case.created", "files.uploaded"]
    state_keys: Tuple[str, ...]      # ["active_case_id", "operator_name"]

@dataclass(frozen=True)
class LayoutContract:
    """Where this component lives in UI"""
    tab_id: str                      # "home", "cases", "workspace", "system"
    position: str                    # "main", "sidebar", "footer"
    size: str                        # "full", "half", "quarter"
    
class UIComponentFramework:
    """Base class for all GUI components (like SectionFramework)"""
    
    COMPONENT_ID: str = ""
    MODULE_ADDRESS: str = ""
    VISIBILITY: VisibilityContract
    DATA: DataContract
    LAYOUT: LayoutContract
    
    def __init__(
        self,
        parent,
        gui_controller,
        *,
        communicator,
        dependency_initializers: Optional[Dict[str, Callable]] = None,
        **kwargs
    ):
        self.parent = parent
        self.gui_controller = gui_controller
        self.communicator = communicator
        self._dependency_initializers = dependency_initializers or {}
        self.dependencies = {}
        self._state = UIComponentState.CREATED
        self._widget = None
        
    def initialize_dependencies(self):
        """Lazy load component dependencies (like sections do)"""
        for name, initializer in self._dependency_initializers.items():
            if name not in self.dependencies:
                self.dependencies[name] = initializer()
    
    def transition_state(self, new_state: UIComponentState):
        """Manage lifecycle"""
        self._state = new_state
    
    def show(self):
        """Make component visible"""
        if self._widget:
            self._widget.pack(fill='both', expand=True)
        self.transition_state(UIComponentState.ACTIVE)
    
    def hide(self):
        """Hide component"""
        if self._widget:
            self._widget.pack_forget()
        self.transition_state(UIComponentState.HIDDEN)
    
    def handle_signal(self, signal_name: str, payload: Dict):
        """Process incoming signals (like sections do)"""
        pass
```

---

### Layer 2: Individual Components (Refactored)

```python
# components/system_health_dashboard.py (REFACTORED)
from gui_framework_base import UIComponentFramework, VisibilityContract, DataContract, LayoutContract

class SystemHealthDashboard(UIComponentFramework):
    """System health monitoring component"""
    
    COMPONENT_ID = "system_health"
    MODULE_ADDRESS = "GUI-1.6"  # System Status Interface
    
    VISIBILITY = VisibilityContract(
        required_role="supervisor",
        required_permissions=("view_system_health",)
    )
    
    DATA = DataContract(
        input_signals=("system.metrics",),
        output_signals=("health.alert",),
        state_keys=("cpu_percent", "memory_percent", "disk_usage")
    )
    
    LAYOUT = LayoutContract(
        tab_id="system",
        position="main",
        size="half"
    )
    
    def __init__(self, parent, gui_controller, communicator, **kwargs):
        # Initialize dependencies (like sections)
        dependency_initializers = {
            "psutil": init_psutil,  # Lazy loader
            "performance_tracker": init_performance_tracker,
        }
        
        super().__init__(
            parent,
            gui_controller,
            communicator=communicator,
            dependency_initializers=dependency_initializers,
            **kwargs
        )
        
        # Build UI after dependencies ready
        self._build_ui()
        self.transition_state(UIComponentState.ACTIVE)
    
    def _build_ui(self):
        """Build tkinter widgets"""
        self.initialize_dependencies()  # Load psutil, etc.
        # ... existing UI code ...
    
    def handle_signal(self, signal_name: str, payload: Dict):
        """React to system signals"""
        if signal_name == "system.metrics":
            self._update_metrics(payload)
```

---

### Layer 3: GUI Controller (Central Orchestration)

```python
# gui_controller.py (NEW - like GatewayController)
class GUIController:
    """
    Central orchestrator for GUI (mirrors GatewayController role)
    
    Responsibilities:
    - Owns application state (active case, operator, etc.)
    - Registers all components
    - Routes signals between components
    - Coordinates with Data Bus
    - Manages component lifecycle
    """
    
    def __init__(self, bus, component_loader, operator_profile):
        self.bus = bus
        self.component_loader = component_loader
        self.operator_profile = operator_profile
        
        # Master state (like gateway's evidence_index)
        self.app_state = {
            "active_case_id": None,
            "active_case": None,
            "operator_name": operator_profile.name,
            "uploaded_files": [],
            "current_tab": "home",
        }
        
        # Component registry (like gateway's section_registry)
        self.components: Dict[str, UIComponentFramework] = {}
        
        # Signal queue (like gateway's signal_queue)
        self.signal_queue: List[Dict] = []
        
        # Communicator for bus signals
        self.communicator = self._init_communicator()
    
    def register_component(
        self,
        component_id: str,
        component_instance: UIComponentFramework
    ):
        """Register a component (like gateway registers sections)"""
        self.components[component_id] = component_instance
        
        # Subscribe to component's input signals
        for signal in component_instance.DATA.input_signals:
            self.communicator.register_handler(
                signal,
                lambda payload: component_instance.handle_signal(signal, payload)
            )
    
    def update_state(self, key: str, value: Any):
        """Update app state and notify components"""
        self.app_state[key] = value
        
        # Find components that depend on this state key
        for comp in self.components.values():
            if key in comp.DATA.state_keys:
                comp.handle_signal(f"state.{key}.changed", {"value": value})
    
    def route_signal(self, signal_name: str, payload: Dict):
        """Route signal to interested components (like gateway routes to sections)"""
        for comp_id, comp in self.components.items():
            if signal_name in comp.DATA.input_signals:
                comp.handle_signal(signal_name, payload)
    
    def get_component_data(self, component_id: str) -> Dict:
        """Provide data to component (like gateway's get_section_inputs)"""
        comp = self.components.get(component_id)
        if not comp:
            return {}
        
        # Gather all state keys this component needs
        data = {}
        for key in comp.DATA.state_keys:
            data[key] = self.app_state.get(key)
        
        return data
    
    def publish_component_output(self, component_id: str, signal_name: str, payload: Dict):
        """Component publishes output (like gateway's publish_section_result)"""
        # Emit to bus
        self.communicator.send_signal(
            target_address="Bus-1",
            signal_name=signal_name,
            payload=payload
        )
        
        # Route to other components
        self.route_signal(signal_name, payload)
```

---

### Layer 4: Enhanced GUI (Refactored to use Controller)

```python
# enhanced_functional_gui.py (REFACTORED)
class EnhancedDKIGUI:
    def __init__(self, bus=None):
        self.root = self._create_root()
        
        # Determine user role
        user_role = self._determine_user_role()
        
        # Initialize component loader
        self.component_loader = ComponentLoader(user_role)
        
        # Initialize GUI Controller (NEW - central orchestrator)
        self.gui_controller = GUIController(
            bus=bus,
            component_loader=self.component_loader,
            operator_profile=self.operator_profile
        )
        
        # Build layout with controller
        self._build_layout()
        
        # Initialize bus handlers (connect to Data Bus)
        self._init_bus_handlers()
    
    def _build_layout(self):
        """Build GUI layout with controller-managed components"""
        # Create tabs based on role
        tabs = self.component_loader.get_role_appropriate_tabs()
        
        for tab_info in tabs:
            if tab_info["id"] == "system":
                self._build_system_tab(tab_container)
    
    def _build_system_tab(self, parent):
        """Build system tab with controller-managed components"""
        container = ttk.Frame(parent)
        
        # Create system health component using framework
        if self.component_loader.is_component_available("system_health"):
            health_comp = SystemHealthDashboard(
                parent=container,
                gui_controller=self.gui_controller,
                communicator=self.gui_controller.communicator
            )
            
            # Register with controller
            self.gui_controller.register_component("system_health", health_comp)
            
            # Show component
            health_comp.show()
        
        return container
    
    def _init_bus_handlers(self):
        """Connect GUI to Data Bus (like sections connect to gateway)"""
        # Listen for case events
        self.gui_controller.communicator.register_handler(
            "case.created",
            self._on_case_created
        )
        
        # Listen for evidence events
        self.gui_controller.communicator.register_handler(
            "evidence.classified",
            self._on_evidence_classified
        )
    
    def _on_case_created(self, payload: Dict):
        """Handle case creation event (like section handles prepare_signal)"""
        case_id = payload.get("case_id")
        self.gui_controller.update_state("active_case_id", case_id)
        self.gui_controller.update_state("active_case", payload)
    
    def _new_case(self):
        """User creates new case (like user uploads evidence)"""
        dialog = CaseCreationDialog(self.root)
        if dialog.result:
            case_data = dialog.result
            
            # Publish to GUI controller
            self.gui_controller.publish_component_output(
                component_id="case_management",
                signal_name="case.created",
                payload=case_data
            )
```

---

## Architecture Comparison

| Layer | Report Engine | GUI Equivalent |
|-------|---------------|----------------|
| **Base Framework** | `SectionFramework` | `UIComponentFramework` |
| **Contracts** | Communication, Order, Persistence | Visibility, Data, Layout |
| **Individual Units** | Section 1, 2, 3... (frameworks) | SystemHealth, CaseMgmt... (components) |
| **Central Orchestrator** | `GatewayController` | `GUIController` |
| **Execution Control** | `EcosystemController` | N/A (GUI is UI-driven, not execution pipeline) |
| **Communication** | `UniversalCommunicator` | Same (shared bus) |
| **Dependency Loading** | `_init_*.py` files | ComponentLoader + lazy factories |
| **Master State** | `evidence_index` | `app_state` |
| **Signal Routing** | `route_section()` | `route_signal()` |
| **Lifecycle** | CREATED→ACTIVE→RESTING | CREATED→ACTIVE→HIDDEN |

---

## Key Insights

### What Report Engine Does Right
1. **Base Framework** - All sections inherit consistent interface
2. **Contracts** - Sections declare needs upfront
3. **Central Controller** - Owns master state, coordinates everything
4. **Dependency Injection** - Tools loaded on-demand
5. **Signal Protocol** - Clear communication between sections
6. **Lifecycle Management** - Sections have states, transitions tracked

### What GUI Currently Missing
1. ✗ No base framework - components are independent
2. ✗ No contracts - components don't declare needs
3. ✗ No central controller - state scattered across main GUI
4. ✗ No dependency injection - components import directly
5. ✗ Weak signal protocol - manual callback passing
6. ✗ No lifecycle management - components just exist or don't

---

## Implementation Plan

### Phase 1: Foundation (1-2 hours)
1. Create `gui_framework_base.py` with:
   - `UIComponentFramework` base class
   - Contract dataclasses
   - Lifecycle enum
2. Create `gui_controller.py` with:
   - State management
   - Component registry
   - Signal routing

### Phase 2: Refactor Components (2-3 hours)
1. Convert `SystemHealthDashboard` to inherit `UIComponentFramework`
2. Add contracts to each component
3. Convert to use dependency initializers

### Phase 3: Integration (1-2 hours)
1. Update `enhanced_functional_gui.py` to use `GUIController`
2. Register all components with controller
3. Connect signal handlers

### Phase 4: Testing (1 hour)
1. Verify component lifecycle
2. Test signal routing
3. Validate role-based visibility

---

## Result: Clean, Cohesive System

**Before (Current):**
- Components = independent widgets
- State = scattered across GUI class
- Communication = manual callbacks
- No contracts, no lifecycle

**After (Proposed):**
- Components = frameworks (like sections)
- State = owned by GUIController
- Communication = signal protocol
- Contracts declare needs, lifecycle tracked

**Matches Report Engine architecture** ✓  
**Clean integration with Data Bus** ✓  
**Role-based filtering preserved** ✓  
**Lazy loading maintained** ✓  
**Testable, maintainable, extensible** ✓

---

**This is the "lot more going on" you asked about. Ready to build it?**

