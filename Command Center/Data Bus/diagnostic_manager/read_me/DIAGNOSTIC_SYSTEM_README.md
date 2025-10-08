# UNIFIED DIAGNOSTIC SYSTEM README

## 🚀 Quick Start Guide

The Unified Diagnostic System is an autonomous fault detection, analysis, and repair engine designed for Central Command infrastructure management.

### Prerequisites
- Python 3.8+
- Windows 10/11
- Administrative privileges (for system-level operations)

### Installation
```bash
# Clone or navigate to the diagnostic system directory
cd "F:\The Central Command\Command Center\Data Bus\diagnostic_manager\Unified_diagnostic_system"

# Verify core files are present
ls core.py auth.py comms.py enforcement.py recovery.py

# Start the system
python core.py --test-mode
```

## 📋 System Overview

### Core Components
- **`core.py`** - Main diagnostic engine and system coordinator
- **`auth.py`** - Authentication and security management
- **`comms.py`** - Communication protocol handler
- **`enforcement.py`** - Policy enforcement and compliance monitoring
- **`recovery.py`** - Fault recovery and system repair

### Key Features
- ✅ **Autonomous Diagnostics** - Self-managing fault detection
- ✅ **Signal Protocol Management** - Enhanced timeout and response tracking
- ✅ **ROLLCALL Throttling** - Prevents system overload
- ✅ **Priority Repair Queue** - Intelligent fault prioritization
- ✅ **Queue Backpressure Management** - Automatic resource management
- ✅ **Fault Response Tracking** - Comprehensive monitoring with cleanup

## 🎯 Usage Examples

### Basic Startup
```bash
# Test mode (recommended for first run)
python core.py --test-mode --launch-delay 5

# Production mode
python core.py --log-level INFO

# Debug mode
python core.py --log-level DEBUG --test-mode
```

### Command Line Options
```bash
python core.py [OPTIONS]

Options:
  -h, --help            Show help message
  --log-level LEVEL     Set logging level (DEBUG, INFO, WARNING, ERROR)
  --no-canbus          Run without CAN-BUS connection
  --test-mode          Run in test mode
  --launch-delay SECONDS  Delay before launching
```

### System Status Check
```bash
# Check system health
python -c "import core; print('System operational')"

# View recent logs
tail -f library/system_logs/unified_diagnostic.log
```

## 🔧 Configuration

### System Registry
The system registry (`system_registry.json`) contains:
- Connected system definitions
- Communication protocols
- Fault detection rules
- Repair procedures

### Directory Structure
```
Unified_diagnostic_system/
├── core.py                 # Main diagnostic engine
├── auth.py                 # Authentication system
├── comms.py                # Communication handler
├── enforcement.py          # Policy enforcement
├── recovery.py             # Recovery procedures
├── library/
│   ├── system_logs/        # System operation logs
│   ├── diagnostic_reports/ # Fault reports
│   ├── fault_amendments/   # Repair documentation
│   └── systems_amendments/ # System modifications
├── secure_vault/           # Security keys and certificates
├── fault_vault/            # Active fault storage
└── test_plans/             # System test procedures
```

## 📊 Monitoring and Maintenance

### Log Files
- **`unified_diagnostic.log`** - Main system log
- **`core_system.log`** - Core engine operations
- **`dki_bus_core.log`** - Communication bus logs

### Automatic Maintenance
- **Log Rotation** - Weekly cleanup, keep latest 2 files
- **Fault Tracking Cleanup** - Hourly cleanup of old entries
- **Queue Management** - Automatic backpressure mitigation
- **Registry Validation** - Daily integrity checks

### Manual Maintenance
```bash
# Check system status
python core.py --status-check

# Review fault reports
ls library/diagnostic_reports/

# Check repair queue
grep "priority_repair_queue" library/system_logs/unified_diagnostic.log
```

## 🚨 Troubleshooting

### Common Issues

#### System Won't Start
```bash
# Check Python version
python --version

# Verify file permissions
ls -la core.py

# Check for missing dependencies
python -c "import core"
```

#### Signal Timeout Issues
```bash
# Check timeout rates
grep "timeout" library/system_logs/unified_diagnostic.log

# Review fault tracking
grep "fault_response_tracking" library/system_logs/unified_diagnostic.log
```

#### Queue Backpressure
```bash
# Check queue sizes
grep "backpressure" library/system_logs/unified_diagnostic.log

# Review cleanup operations
grep "mitigation" library/system_logs/unified_diagnostic.log
```

### Emergency Procedures
1. **System Recovery**: Stop system (`Ctrl+C`), backup logs, restart in test mode
2. **Critical Faults**: Automatically escalated to HIGH priority repair queue
3. **Data Recovery**: Restore from automatic backups in `secure_vault/`

## 🔒 Security

### Authentication
- System uses encrypted authentication keys
- All operations logged with timestamps
- Secure vault protection for sensitive data

### Data Protection
- Logs encrypted at rest
- Fault data anonymized where possible
- Regular security audits and updates

## 📈 Performance

### Optimization Features
- **Smart Throttling** - Prevents system overload
- **Priority Queuing** - Intelligent task prioritization
- **Automatic Cleanup** - Prevents memory leaks
- **Load Balancing** - Dynamic resource allocation

### Performance Metrics
- Signal response times
- Fault detection rates
- Repair success rates
- System uptime statistics

## 🆘 Support

### Documentation
- **SOP**: `DIAGNOSTIC_SYSTEM_SOP.md` - Standard operating procedures
- **Blueprint**: `DIAGNOSTIC_SYSTEM_BLUEPRINT.md` - Technical architecture
- **PRD**: `DIAGNOSTIC_SYSTEM_PRD.md` - Product requirements
- **Makefile**: `DIAGNOSTIC_SYSTEM_MAKEFILE.mk` - Build instructions

### Getting Help
1. Check this README for common solutions
2. Review system logs for error messages
3. Consult the SOP for detailed procedures
4. Contact system administrator for critical issues

## 📝 Version History

### Current Version: 1.0
- Initial release with enhanced protocol support
- Signal timeout and response tracking
- ROLLCALL throttling implementation
- Priority repair queue system
- Queue backpressure management
- Comprehensive fault tracking with cleanup

### Upcoming Features
- Advanced machine learning fault prediction
- Enhanced repair automation
- Improved performance monitoring
- Extended security features

## 📄 License

This system is proprietary software of Central Command. Unauthorized distribution or modification is prohibited.

---

**Last Updated**: 2025-01-07  
**Version**: 1.0  
**Author**: DEESCALATION Agent  
**Classification**: INTERNAL
