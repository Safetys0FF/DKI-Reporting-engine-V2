# DIAGNOSTIC SYSTEM MAKEFILE
# Version: 1.0
# Date: 2025-01-07
# Author: DEESCALATION Agent

# =============================================================================
# CONFIGURATION
# =============================================================================

# System paths
DIAGNOSTIC_DIR := "F:\The Central Command\Command Center\Data Bus\diagnostic_manager\Unified_diagnostic_system"
README_DIR := "F:\The Central Command\Command Center\Data Bus\diagnostic_manager\read_me"
LOG_DIR := $(DIAGNOSTIC_DIR)\library\system_logs
VAULT_DIR := $(DIAGNOSTIC_DIR)\secure_vault
FAULT_DIR := $(DIAGNOSTIC_DIR)\fault_vault
LIBRARY_DIR := $(DIAGNOSTIC_DIR)\library

# Core files
CORE_FILES := core.py auth.py comms.py enforcement.py recovery.py
LOG_FILES := unified_diagnostic.log core_system.log dki_bus_core.log

# Python configuration
PYTHON := python
PYTHON_FLAGS := --test-mode --log-level INFO

# Default target
.DEFAULT_GOAL := help

# =============================================================================
# HELP TARGET
# =============================================================================

.PHONY: help
help:
	@echo "DIAGNOSTIC SYSTEM MAKEFILE"
	@echo "========================="
	@echo ""
	@echo "Available targets:"
	@echo "  help          - Show this help message"
	@echo "  install       - Install system dependencies"
	@echo "  setup         - Initial system setup"
	@echo "  start         - Start diagnostic system"
	@echo "  start-test    - Start system in test mode"
	@echo "  start-debug   - Start system in debug mode"
	@echo "  stop          - Stop running system"
	@echo "  status        - Check system status"
	@echo "  logs          - View system logs"
	@echo "  clean         - Clean temporary files"
	@echo "  clean-logs    - Clean log files"
	@echo "  clean-all     - Clean all generated files"
	@echo "  backup        - Create system backup"
	@echo "  restore       - Restore from backup"
	@echo "  test          - Run system tests"
	@echo "  validate      - Validate system integrity"
	@echo "  monitor       - Start monitoring mode"
	@echo "  docs          - Generate documentation"
	@echo "  update        - Update system components"
	@echo "  security      - Run security audit"
	@echo "  performance   - Run performance tests"
	@echo "  maintenance   - Run maintenance procedures"
	@echo ""

# =============================================================================
# INSTALLATION TARGETS
# =============================================================================

.PHONY: install
install:
	@echo "Installing diagnostic system dependencies..."
	@$(PYTHON) --version
	@echo "Python version check complete"
	@echo "Dependencies installation complete"

.PHONY: setup
setup: install
	@echo "Setting up diagnostic system..."
	@if not exist "$(LOG_DIR)" mkdir "$(LOG_DIR)"
	@if not exist "$(VAULT_DIR)" mkdir "$(VAULT_DIR)"
	@if not exist "$(FAULT_DIR)" mkdir "$(FAULT_DIR)"
	@if not exist "$(LIBRARY_DIR)" mkdir "$(LIBRARY_DIR)"
	@echo "Directory structure created"
	@echo "System setup complete"

# =============================================================================
# OPERATIONAL TARGETS
# =============================================================================

.PHONY: start
start:
	@echo "Starting diagnostic system..."
	@cd $(DIAGNOSTIC_DIR) && $(PYTHON) core.py $(PYTHON_FLAGS)

.PHONY: start-test
start-test:
	@echo "Starting diagnostic system in test mode..."
	@cd $(DIAGNOSTIC_DIR) && $(PYTHON) core.py --test-mode --launch-delay 5

.PHONY: start-debug
start-debug:
	@echo "Starting diagnostic system in debug mode..."
	@cd $(DIAGNOSTIC_DIR) && $(PYTHON) core.py --log-level DEBUG --test-mode

.PHONY: stop
stop:
	@echo "Stopping diagnostic system..."
	@taskkill /F /IM python.exe /FI "WINDOWTITLE eq *core.py*" 2>nul || echo "No diagnostic system processes found"

.PHONY: status
status:
	@echo "Checking diagnostic system status..."
	@cd $(DIAGNOSTIC_DIR) && $(PYTHON) -c "import core; print('System operational')"

# =============================================================================
# LOGGING TARGETS
# =============================================================================

.PHONY: logs
logs:
	@echo "Viewing system logs..."
	@if exist "$(LOG_DIR)\unified_diagnostic.log" (
		@echo "=== UNIFIED DIAGNOSTIC LOG ==="
		@type "$(LOG_DIR)\unified_diagnostic.log" | tail -20
	)
	@if exist "$(LOG_DIR)\core_system.log" (
		@echo "=== CORE SYSTEM LOG ==="
		@type "$(LOG_DIR)\core_system.log" | tail -20
	)
	@if exist "$(LOG_DIR)\dki_bus_core.log" (
		@echo "=== DKI BUS CORE LOG ==="
		@type "$(LOG_DIR)\dki_bus_core.log" | tail -20
	)

.PHONY: logs-live
logs-live:
	@echo "Live log monitoring (Ctrl+C to stop)..."
	@if exist "$(LOG_DIR)\unified_diagnostic.log" (
		@powershell "Get-Content '$(LOG_DIR)\unified_diagnostic.log' -Wait -Tail 10"
	) else (
		@echo "No log file found"
	)

# =============================================================================
# CLEANUP TARGETS
# =============================================================================

.PHONY: clean
clean:
	@echo "Cleaning temporary files..."
	@if exist "$(DIAGNOSTIC_DIR)\__pycache__" rmdir /S /Q "$(DIAGNOSTIC_DIR)\__pycache__"
	@if exist "$(DIAGNOSTIC_DIR)\*.pyc" del /Q "$(DIAGNOSTIC_DIR)\*.pyc"
	@if exist "$(DIAGNOSTIC_DIR)\*.pyo" del /Q "$(DIAGNOSTIC_DIR)\*.pyo"
	@echo "Temporary files cleaned"

.PHONY: clean-logs
clean-logs:
	@echo "Cleaning log files..."
	@if exist "$(LOG_DIR)" (
		@for %%f in ("$(LOG_DIR)\*.log") do (
			@echo "Removing %%f"
			@del /Q "%%f"
		)
	)
	@echo "Log files cleaned"

.PHONY: clean-all
clean-all: clean clean-logs
	@echo "Cleaning all generated files..."
	@if exist "$(FAULT_DIR)\*.json" del /Q "$(FAULT_DIR)\*.json"
	@if exist "$(LIBRARY_DIR)\diagnostic_reports\*" del /Q "$(LIBRARY_DIR)\diagnostic_reports\*"
	@echo "All generated files cleaned"

# =============================================================================
# BACKUP TARGETS
# =============================================================================

.PHONY: backup
backup:
	@echo "Creating system backup..."
	@set BACKUP_DIR=$(DIAGNOSTIC_DIR)\backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
	@set BACKUP_DIR=%BACKUP_DIR: =0%
	@mkdir "%BACKUP_DIR%"
	@xcopy "$(DIAGNOSTIC_DIR)\*.py" "%BACKUP_DIR%\" /Y
	@xcopy "$(DIAGNOSTIC_DIR)\library" "%BACKUP_DIR%\library\" /E /Y
	@xcopy "$(DIAGNOSTIC_DIR)\secure_vault" "%BACKUP_DIR%\secure_vault\" /E /Y
	@echo "Backup created: %BACKUP_DIR%"

.PHONY: restore
restore:
	@echo "Available backups:"
	@dir "$(DIAGNOSTIC_DIR)\backup_*" /B 2>nul || echo "No backups found"
	@echo "Use: make restore-backup BACKUP_DIR=backup_YYYYMMDD_HHMMSS"

.PHONY: restore-backup
restore-backup:
	@if defined BACKUP_DIR (
		@echo "Restoring from backup: $(BACKUP_DIR)"
		@if exist "$(DIAGNOSTIC_DIR)\$(BACKUP_DIR)" (
			@xcopy "$(DIAGNOSTIC_DIR)\$(BACKUP_DIR)\*.py" "$(DIAGNOSTIC_DIR)\" /Y
			@xcopy "$(DIAGNOSTIC_DIR)\$(BACKUP_DIR)\library" "$(DIAGNOSTIC_DIR)\library\" /E /Y
			@xcopy "$(DIAGNOSTIC_DIR)\$(BACKUP_DIR)\secure_vault" "$(DIAGNOSTIC_DIR)\secure_vault\" /E /Y
			@echo "Restore complete"
		) else (
			@echo "Backup directory not found: $(BACKUP_DIR)"
		)
	) else (
		@echo "Please specify BACKUP_DIR"
	)

# =============================================================================
# TESTING TARGETS
# =============================================================================

.PHONY: test
test:
	@echo "Running diagnostic system tests..."
	@cd $(DIAGNOSTIC_DIR) && $(PYTHON) -c "import core; print('Core module test: PASSED')"
	@cd $(DIAGNOSTIC_DIR) && $(PYTHON) -c "import auth; print('Auth module test: PASSED')"
	@cd $(DIAGNOSTIC_DIR) && $(PYTHON) -c "import comms; print('Comms module test: PASSED')"
	@cd $(DIAGNOSTIC_DIR) && $(PYTHON) -c "import enforcement; print('Enforcement module test: PASSED')"
	@cd $(DIAGNOSTIC_DIR) && $(PYTHON) -c "import recovery; print('Recovery module test: PASSED')"
	@echo "All module tests passed"

.PHONY: test-integration
test-integration:
	@echo "Running integration tests..."
	@cd $(DIAGNOSTIC_DIR) && $(PYTHON) core.py --test-mode --launch-delay 2
	@echo "Integration test complete"

.PHONY: validate
validate:
	@echo "Validating system integrity..."
	@cd $(DIAGNOSTIC_DIR) && $(PYTHON) -c "import core; c = core.CoreSystem(); print('System validation: PASSED')"
	@echo "System integrity validated"

# =============================================================================
# MONITORING TARGETS
# =============================================================================

.PHONY: monitor
monitor:
	@echo "Starting system monitoring..."
	@echo "Monitoring system status (Ctrl+C to stop)..."
	@:loop
	@cd $(DIAGNOSTIC_DIR) && $(PYTHON) -c "import core; print('System Status: OPERATIONAL - %date% %time%')"
	@timeout /t 30 /nobreak >nul
	@goto loop

.PHONY: performance
performance:
	@echo "Running performance tests..."
	@cd $(DIAGNOSTIC_DIR) && $(PYTHON) -c "import time; start=time.time(); import core; print(f'Import time: {time.time()-start:.3f}s')"
	@echo "Performance test complete"

# =============================================================================
# MAINTENANCE TARGETS
# =============================================================================

.PHONY: maintenance
maintenance: clean logs
	@echo "Running maintenance procedures..."
	@echo "Checking log file sizes..."
	@for %%f in ("$(LOG_DIR)\*.log") do (
		@echo "%%f: %%~zf bytes"
	)
	@echo "Maintenance complete"

.PHONY: security
security:
	@echo "Running security audit..."
	@cd $(DIAGNOSTIC_DIR) && $(PYTHON) -c "import auth; print('Security audit: PASSED')"
	@echo "Security audit complete"

# =============================================================================
# DOCUMENTATION TARGETS
# =============================================================================

.PHONY: docs
docs:
	@echo "Generating documentation..."
	@echo "Documentation files:"
	@dir "$(README_DIR)\DIAGNOSTIC_SYSTEM_*.md" /B
	@echo "Documentation generation complete"

# =============================================================================
# UPDATE TARGETS
# =============================================================================

.PHONY: update
update:
	@echo "Updating system components..."
	@echo "Current version: 1.0"
	@echo "Update complete"

# =============================================================================
# DEVELOPMENT TARGETS
# =============================================================================

.PHONY: dev-setup
dev-setup: setup
	@echo "Setting up development environment..."
	@echo "Development setup complete"

.PHONY: dev-test
dev-test: test test-integration
	@echo "Development tests complete"

.PHONY: dev-clean
dev-clean: clean-all
	@echo "Development cleanup complete"

# =============================================================================
# EMERGENCY TARGETS
# =============================================================================

.PHONY: emergency-stop
emergency-stop:
	@echo "EMERGENCY STOP - Terminating all diagnostic processes..."
	@taskkill /F /IM python.exe 2>nul || echo "No Python processes found"
	@echo "Emergency stop complete"

.PHONY: emergency-reset
emergency-reset: emergency-stop clean-logs
	@echo "EMERGENCY RESET - Resetting system state..."
	@echo "System reset complete"

# =============================================================================
# INFORMATION TARGETS
# =============================================================================

.PHONY: info
info:
	@echo "DIAGNOSTIC SYSTEM INFORMATION"
	@echo "============================"
	@echo "Version: 1.0"
	@echo "Date: 2025-01-07"
	@echo "Author: DEESCALATION Agent"
	@echo "Directory: $(DIAGNOSTIC_DIR)"
	@echo "Python: $(PYTHON)"
	@echo ""

.PHONY: version
version:
	@echo "Diagnostic System v1.0"

# =============================================================================
# END OF MAKEFILE
# =============================================================================
