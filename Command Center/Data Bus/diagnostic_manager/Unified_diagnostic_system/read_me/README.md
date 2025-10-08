# Unified Diagnostic System - Root Engine

## Overview
The Unified Diagnostic System is the main diagnostic launch program for the Central Command architecture. It serves as the root engine that coordinates all diagnostic functionality across the system.

## Directory Structure
```
Unified_diagnostic_system/
├── __init__.py              # Main entry point and CAN-BUS integration
├── main_launcher.py         # Primary launcher script
├── LAUNCH_DIAGNOSTIC_SYSTEM.bat  # Windows batch launcher
├── test_system.py           # Simple test script
├── core.py                  # Core system driver (THE DRIVER)
├── auth.py                  # Authentication and security
├── comms.py                 # Communication protocols
├── recovery.py              # System recovery and repair
├── enforcement.py           # Protocol enforcement and monitoring
└── README.md               # This file
```

## Quick Start

### Windows
```batch
# Double-click or run:
LAUNCH_DIAGNOSTIC_SYSTEM.bat

# Or from command line:
python main_launcher.py
```

### Python Direct
```python
from Unified_diagnostic_system import UnifiedDiagnosticSystem

# Create system instance
uds = UnifiedDiagnosticSystem()

# Launch the system
uds.launch_diagnostic_system()

# Check status
status = uds.get_unified_status()
print(status)
```

### Test Mode
```bash
python main_launcher.py --test-mode --log-level INFO
```

## System Architecture

### Core Components
1. **CoreSystem (THE DRIVER)** - Main orchestrator that pulls and coordinates all modules
2. **AuthSystem** - Handles fault authentication and cryptographic security
3. **CommsSystem** - Manages communication protocols and CAN-BUS integration
4. **RecoverySystem** - Handles system recovery, repair, and code restoration
5. **EnforcementSystem** - Enforces protocols and monitors system compliance

### Key Features
- **CAN-BUS Integration** - Connects to the Central Command data bus
- **Modular Architecture** - Five focused modules working together
- **Autonomous Diagnostics** - Self-monitoring and self-repair capabilities
- **Protocol Enforcement** - Ensures universal language compliance
- **Live Monitoring** - Real-time system health monitoring
- **Fault Management** - Comprehensive fault detection and resolution

## System Status
- **OK** - System functioning normally
- **ERROR** - Non-interrupting issues detected
- **FAILURE** - System function disrupted
- **CRITICAL** - Emergency shutdown required

## Command Line Options
```bash
python main_launcher.py [options]

Options:
  --log-level {DEBUG,INFO,WARNING,ERROR}  Set logging level
  --no-canbus                            Run without CAN-BUS connection
  --test-mode                            Run in test mode (auto-shutdown)
  --launch-delay N                       Delay before launching (seconds)
```

## Integration Points
- **CAN-BUS**: `F:\The Central Command\Command Center\Data Bus\Bus Core Design\`
- **System Registry**: `F:\The Central Command\Command Center\Data Bus\diagnostic_manager\test_plans\system_registry.json`
- **Protocol Files**: `F:\The Central Command\Command Center\Data Bus\diagnostic_manager\read_me\MASTER_DIAGNOSTIC_PROTOCOL_2025-10-05.md`

## Logging
- **Console Output**: Real-time status and error messages
- **Log File**: `unified_diagnostic.log` in the system directory
- **Log Levels**: DEBUG, INFO, WARNING, ERROR

## Troubleshooting

### Common Issues
1. **CAN-BUS Not Available**: System runs in standalone mode
2. **Missing System Registry**: Creates empty registry, no systems registered
3. **Protocol File Not Found**: Uses default protocols
4. **Import Errors**: Check Python path and module dependencies

### Verification
Run the test script to verify system functionality:
```bash
python test_system.py
```

## System Requirements
- Python 3.7+
- Access to Central Command Data Bus (optional)
- Windows environment (for batch launcher)

## Status
✅ **FULLY OPERATIONAL** - All core functionality working
- System initialization: ✅ Working
- Module loading: ✅ Working  
- CAN-BUS integration: ✅ Working (standalone mode)
- Autonomous diagnostics: ✅ Working
- Protocol enforcement: ✅ Working
- Live monitoring: ✅ Working
- System recovery: ✅ Working

## Support
For issues or questions, refer to the main diagnostic system documentation in the parent directory.
