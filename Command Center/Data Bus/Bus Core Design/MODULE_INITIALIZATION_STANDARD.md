# Module Initialization Standard
**Central Command Bus - Required Protocol for All Modules**

## Overview
All modules MUST follow this standardized initialization sequence to ensure stable, predictable system startup.

## Core Principles
1. **10-Second Bus Stabilization** - Bus requires 10 seconds to fully initialize before accepting connections
2. **Orchestrated Sequence** - Modules initialize in strict dependency order
3. **Registration Protocol** - Modules must register with bus before operating
4. **Wait for Turn** - Modules must wait for their turn in the initialization sequence

## Initialization Sequence

```
Bus-1 (Bus Core)        → Stabilizes for 10 seconds
  ↓
DIAG-1 (UDS)            → Diagnostic system
  ↓
GUI-1 (User Interface)  → Interface layer
  ↓
3 (The Warden)          → Gateway controller
  ↓
2-1 (Evidence Locker)   → Evidence management
  ↓
5 (Mission Debrief)     → Report generation
  ↓
1 (The Marshall)        → Section coordination
```

## Standard Module Template

### Step 1: Wait for Bus Ready
```python
from bus_core import DKIReportBus

# Create or get bus instance
bus = DKIReportBus()  # or get existing instance

# Wait for bus stabilization (10s countdown)
if not bus.wait_for_ready(timeout=15.0):
    logger.error("Bus stabilization timeout - cannot proceed")
    return False
```

### Step 2: Wait for Your Turn
```python
# Wait for this module's turn in the sequence
module_address = '3'  # Your module's address

if not bus.wait_for_module_turn(module_address, timeout=30.0):
    logger.error(f"Module {module_address} initialization timeout")
    return False
```

### Step 3: Initialize Module
```python
# Now safe to initialize your module
try:
    # Your module initialization code here
    my_module = MyModule(bus=bus)
    
    # Register with bus
    if bus.register_module_init(module_address, {
        'version': '1.0',
        'type': 'your_module_type',
        'capabilities': ['feature1', 'feature2']
    }):
        logger.info(f"[OK] Module {module_address} initialized successfully")
    else:
        logger.warning(f"Module {module_address} registration failed")
        return False
        
except Exception as e:
    logger.error(f"Module {module_address} initialization error: {e}")
    return False
```

### Step 4: Verify System Status
```python
# Check initialization status
init_status = bus.get_initialization_status()
logger.info(f"System initialization: {init_status['initialized_count']}/{init_status['total_count']} modules")

if init_status['initialization_complete']:
    logger.info("[OK] All core modules initialized - system ready")
```

## Module Addresses

| Address | Module Name | Type |
|---------|-------------|------|
| Bus-1 | Bus Core | Central bus |
| DIAG-1 | Unified Diagnostic System | Diagnostic |
| GUI-1 | User Interface | Interface |
| 3 | The Warden | Gateway controller |
| 2-1 | Evidence Locker | Evidence management |
| 5 | Mission Debrief | Report generation |
| 1 | The Marshall | Section coordination |

## Health Monitoring

### Check Bus Health
```python
health = bus.get_health_metrics()
print(f"Bus Status: {health['status']}")
print(f"Bus Ready: {health['bus_ready']}")
print(f"Initialization Complete: {health['initialization_complete']}")
print(f"Modules: {health['initialized_modules']}/{health['total_modules']}")
```

### Check Initialization Status
```python
status = bus.get_initialization_status()
for module_addr, module_info in status['modules'].items():
    print(f"{module_addr}: {module_info['status']}")
```

## Error Handling

### Timeout Handling
```python
if not bus.wait_for_ready(timeout=15.0):
    logger.error("Bus stabilization timeout")
    # Fallback or retry logic
    return False
```

### Registration Failure
```python
if not bus.register_module_init(module_address, module_info):
    logger.warning("Registration failed - module may not be in sequence")
    # Continue anyway if module is optional
    pass
```

## Testing Your Module

### Test Bus Stabilization
```python
# Test the stabilization sequence
bus = DKIReportBus()
print(f"Bus ready: {bus.is_ready()}")  # Should be False initially

if bus.wait_for_ready(timeout=15.0):
    print("Bus stabilized successfully")
    print(f"Health: {bus.get_health_metrics()}")
```

### Test Module Sequence
```python
# Test module initialization
module_address = '3'  # Your module address

if bus.wait_for_module_turn(module_address, timeout=30.0):
    print(f"Module {module_address} turn reached")
    # Initialize module
    if bus.register_module_init(module_address, {'version': '1.0'}):
        print(f"Module {module_address} registered")
```

## Migration Checklist

For existing modules, ensure:
- [ ] Module waits for bus ready using `bus.wait_for_ready()`
- [ ] Module waits for turn using `bus.wait_for_module_turn()`
- [ ] Module registers with bus using `bus.register_module_init()`
- [ ] Module handles timeouts gracefully
- [ ] Module logs initialization status
- [ ] Module checks `bus.is_ready()` before operations

## Common Mistakes

❌ **Creating bus and immediately using it**
```python
bus = DKIReportBus()
bus.send('signal', data)  # WRONG - bus not ready yet
```

✅ **Waiting for bus to stabilize**
```python
bus = DKIReportBus()
if bus.wait_for_ready(timeout=15.0):
    bus.send('signal', data)  # CORRECT - bus is ready
```

❌ **Initializing modules in wrong order**
```python
# Module A initializes immediately
module_a = ModuleA(bus)  # WRONG - may fail if dependencies not ready
```

✅ **Waiting for proper sequence**
```python
# Module A waits for its turn
if bus.wait_for_module_turn('A', timeout=30.0):
    module_a = ModuleA(bus)  # CORRECT - dependencies ready
```

## Support

For questions or issues with module initialization:
1. Check bus logs: `Command Center/Data Bus/diagnostic_manager/Unified_diagnostic_system/library/system_logs/`
2. Verify module address matches sequence
3. Test with standalone bus: `python bus_core.py`
4. Review UDS safe mode initialization as reference

---

**Last Updated:** 2025-10-14
**Version:** 1.0.0
**Standard Maintained By:** Central Command System

