"""
Unified Diagnostic System - Main Entry Point

This is the root engine for the Central Command diagnostic system.
All diagnostic functionality is coordinated through this main entry point.
"""

import sys
import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path

# CRITICAL: Set up log redirection BEFORE any bus imports
system_logs_path = Path(__file__).parent / "library" / "system_logs"
system_logs_path.mkdir(parents=True, exist_ok=True)

# Redirect ALL bus_core logging to system_logs before import
bus_log_path = system_logs_path / "dki_bus_core.log"
bus_core_logger = logging.getLogger("bus_core")
for handler in bus_core_logger.handlers[:]:
    bus_core_logger.removeHandler(handler)
    handler.close()

bus_file_handler = logging.FileHandler(bus_log_path, mode='a', encoding='utf-8')
bus_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
bus_file_handler.setFormatter(bus_formatter)
bus_core_logger.addHandler(bus_file_handler)

# Also redirect any existing dki_bus_core logger
dki_logger = logging.getLogger("dki_bus_core")
for handler in dki_logger.handlers[:]:
    dki_logger.removeHandler(handler)
    handler.close()
dki_logger.addHandler(bus_file_handler)

# Add Bus Core Design to path for CAN-BUS connection
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Bus Core Design'))
# Add Data Bus directory for universal_communicator
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from bus_core import DKIReportBus
    from universal_communicator import UniversalCommunicator
    BUS_AVAILABLE = True
except ImportError:
    DKIReportBus = None
    UniversalCommunicator = None
    BUS_AVAILABLE = False


class UnifiedDiagnosticSystem:
    """
    Unified Diagnostic System - Main Entry Point
    
    This is the root engine that establishes CAN-BUS connection and delegates to CoreSystem (THE DRIVER).
    CoreSystem handles all the pulling and coordination of modules.
    """
    
    def __init__(self):
        """Initialize with CAN-BUS as PRIMARY - CoreSystem drives the bus"""
        self.logger = logging.getLogger("UnifiedDiagnosticSystem")
        self.logger.info("=" * 60)
        self.logger.info("UNIFIED DIAGNOSTIC SYSTEM - ROOT ENGINE INITIALIZED")
        self.logger.info("CAN-BUS PRIMARY MODE - STANDALONE IS FAILSAFE")
        self.logger.info("=" * 60)
        
        # CAN-BUS is PRIMARY - attempt connection first
        self.bus = None
        self.communicator = None
        self.bus_connected = False
        self.safemode_active = False
        
        # PRIMARY: Connect to CAN-BUS
        self._connect_to_canbus_primary()
        
        # CoreSystem is THE DRIVER (CAN-BUS PRIMARY, not fallback)
        try:
            from . import core
        except ImportError:
            import core
        self.core = core.CoreSystem(bus_connection=self.bus, communicator=self.communicator)
        
        # Expose core's modules for easy access
        self.auth = self.core.auth
        self.comms = self.core.comms
        self.recovery = self.core.recovery
        self.enforcement = self.core.enforcement
        
        if self.bus_connected:
            self.logger.info("CoreSystem loaded as CAN-BUS PRIMARY DRIVER")
        else:
            self.logger.warning("CoreSystem loaded in SAFEMODE (CAN-BUS unavailable)")
    
    def _connect_to_canbus_primary(self):
        """Establish CAN-BUS connection as PRIMARY operation - standalone is failsafe only"""
        if not BUS_AVAILABLE:
            self.logger.critical("CAN-BUS not available - entering SAFEMODE")
            self.safemode_active = True
            self.bus_connected = False
            return
            
        try:
            # CRITICAL: Set up log redirection BEFORE creating bus instance
            system_logs_path = Path(__file__).parent / "library" / "system_logs"
            system_logs_path.mkdir(parents=True, exist_ok=True)
            bus_log_path = system_logs_path / "dki_bus_core.log"
            
            # Redirect bus_core logger BEFORE bus creation to prevent file creation
            bus_core_logger = logging.getLogger("bus_core")
            for handler in bus_core_logger.handlers[:]:
                bus_core_logger.removeHandler(handler)
                handler.close()
            
            # Add handler to system_logs directory
            bus_file_handler = logging.FileHandler(bus_log_path, mode='a', encoding='utf-8')
            bus_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            bus_file_handler.setFormatter(bus_formatter)
            bus_core_logger.addHandler(bus_file_handler)
            
            self.logger.info(f"Bus core logger pre-configured to: {bus_log_path}")
            
            # PRIMARY OPERATION: Create bus instance (now with redirected logging)
            self.bus = DKIReportBus()
            
            # Redirect the bus core logger completely
            if hasattr(self.bus, 'logger'):
                # Remove ALL existing handlers to prevent duplicate logging
                for handler in self.bus.logger.handlers[:]:
                    self.bus.logger.removeHandler(handler)
                    handler.close()  # Properly close the handler
                
                # Add new file handler to system_logs ONLY
                file_handler = logging.FileHandler(bus_log_path, mode='a', encoding='utf-8')
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                file_handler.setFormatter(formatter)
                self.bus.logger.addHandler(file_handler)
                
                # Also redirect the root logger for bus_core to prevent it from creating files
                bus_root_logger = logging.getLogger("bus_core")
                for handler in bus_root_logger.handlers[:]:
                    bus_root_logger.removeHandler(handler)
                    handler.close()
                
                bus_root_logger.addHandler(file_handler)
                
                # CRITICAL: Set the bus logger's log file path to prevent it from creating new files
                if hasattr(self.bus, 'log_file_path'):
                    self.bus.log_file_path = str(bus_log_path)
                
                self.logger.info(f"Bus core logger redirected to: {bus_log_path}")
            
            self.logger.info("CAN-BUS instance created - PRIMARY MODE")
            
            # PRIMARY OPERATION: Create communicator for diagnostic system
            self.communicator = UniversalCommunicator("DIAG-1", bus_connection=self.bus)
            self.logger.info("Universal Communicator created - PRIMARY MODE")
            
            # PRIMARY OPERATION: Register diagnostic system with bus
            self.bus.register_system_address("DIAG-1", {
                "system_type": "diagnostic_manager",
                "capabilities": ["fault_monitoring", "system_repair", "protocol_enforcement"],
                "status": "active",
                "mode": "primary"
            })
            self.logger.info("Diagnostic system registered with CAN-BUS - PRIMARY MODE")
            
            # PRIMARY OPERATION: Register diagnostic signal handlers
            self._register_diagnostic_signals()
            
            self.bus_connected = True
            self.safemode_active = False
            self.logger.info("CAN-BUS PRIMARY CONNECTION ESTABLISHED SUCCESSFULLY")
            
        except Exception as e:
            self.logger.critical(f"CAN-BUS PRIMARY CONNECTION FAILED: {e}")
            self.logger.critical("ENTERING SAFEMODE - LIMITED FUNCTIONALITY")
            self.bus_connected = False
            self.safemode_active = True
    
    def _register_diagnostic_signals(self):
        """Register diagnostic system signal handlers with CAN-BUS PRIMARY"""
        if not self.bus_connected:
            self.logger.warning("Cannot register signals - CAN-BUS not connected (SAFEMODE)")
            return
            
        # PRIMARY CAN-BUS: Register fault reporting signals
        self.bus.register_signal("fault.report", self._handle_fault_report_signal)
        self.bus.register_signal("fault.sos", self._handle_sos_fault_signal)
        self.bus.register_signal("system.fault", self._handle_system_fault_signal)
        self.bus.register_signal("error.report", self._handle_error_report_signal)
        
        # PRIMARY CAN-BUS: Register diagnostic control signals
        self.bus.register_signal("diagnostic.start", self._handle_diagnostic_start_signal)
        self.bus.register_signal("diagnostic.stop", self._handle_diagnostic_stop_signal)
        self.bus.register_signal("diagnostic.status", self._handle_diagnostic_status_signal)
        
        self.logger.info("Diagnostic signal handlers registered with CAN-BUS PRIMARY")
    
    def _handle_fault_report_signal(self, payload: Dict[str, Any]) -> None:
        """Handle fault report signals from other systems"""
        if self.core:
            self.core.process_fault_report(payload)
    
    def _handle_sos_fault_signal(self, payload: Dict[str, Any]) -> None:
        """Handle SOS fault signals"""
        if self.core:
            self.core.process_fault_report(payload)
    
    def _handle_system_fault_signal(self, payload: Dict[str, Any]) -> None:
        """Handle system fault signals"""
        if self.core:
            self.core.process_fault_report(payload)
    
    def _handle_error_report_signal(self, payload: Dict[str, Any]) -> None:
        """Handle error report signals"""
        if self.core:
            self.core.process_fault_report(payload)
    
    def _handle_diagnostic_start_signal(self, payload: Dict[str, Any]) -> None:
        """Handle diagnostic start signals"""
        if self.core:
            self.core.launch_diagnostic_system()
    
    def _handle_diagnostic_stop_signal(self, payload: Dict[str, Any]) -> None:
        """Handle diagnostic stop signals"""
        if self.core:
            self.core.shutdown()
    
    def _handle_diagnostic_status_signal(self, payload: Dict[str, Any]) -> None:
        """Handle diagnostic status request signals"""
        if self.core:
            status = self.core.get_system_status()
            # Send status response back through bus
            if self.bus_connected:
                self.bus.send("diagnostic.status.response", status)
    
    def launch_diagnostic_system(self) -> bool:
        """Launch system in CAN-BUS PRIMARY mode - CoreSystem drives the bus"""
        if self.bus_connected:
            self.logger.info("Launching diagnostic system in CAN-BUS PRIMARY mode")
            return self.core.launch_diagnostic_system()
        else:
            self.logger.warning("Launching diagnostic system in SAFEMODE (limited functionality)")
            return self.core.launch_diagnostic_system()
    
    def shutdown_diagnostic_system(self):
        """Shutdown system - CoreSystem does the work"""
        self.core.shutdown()
    
    def get_unified_status(self):
        """Get status - CoreSystem does the work"""
        return self.core.get_system_status()
    
    def process_fault_report(self, fault_data):
        """Process fault - CoreSystem coordinates"""
        self.enforcement.process_fault_report(fault_data)
    
    def get_bus_status(self):
        """Get CAN-BUS PRIMARY connection status"""
        return {
            "operation_mode": "CAN-BUS PRIMARY" if self.bus_connected else "SAFEMODE",
            "bus_connected": self.bus_connected,
            "safemode_active": self.safemode_active,
            "bus_available": BUS_AVAILABLE,
            "registered_addresses": self.bus.get_registered_addresses() if self.bus else [],
            "primary_function": "CAN-BUS operation" if self.bus_connected else "Limited standalone"
        }
    
    # Expose core functionality
    def create_diagnostic_payload(self, operation: str, data: Dict[str, Any], **kwargs):
        """Create diagnostic payload via comms module"""
        return self.comms.create_diagnostic_payload(operation, data, **kwargs)
    
    def validate_payload(self, payload: Dict[str, Any]):
        """Validate payload via comms module"""
        return self.comms.validate_payload(payload)
    
    def execute_test_plan(self, system_address: str, test_type: str = "smoke_test"):
        """Execute test plan via core module"""
        return self.core.execute_test_plan(system_address, test_type)
    
    def load_test_plan(self, system_address: str, test_type: str = "smoke_test"):
        """Load test plan via core module"""
        return self.core.load_test_plan(system_address, test_type)
    
    def transmit_rollcall(self):
        """Transmit rollcall via comms module"""
        return self.comms.transmit_rollcall()
    
    def transmit_radio_check(self, target_address: str):
        """Transmit radio check via comms module"""
        return self.comms.transmit_radio_check(target_address)
    
    def transmit_sos_fault(self, system_address: str, fault_code: str, description: str):
        """Transmit SOS fault via comms module"""
        return self.comms.transmit_sos_fault(system_address, fault_code, description)


# Main entry point for direct execution
if __name__ == "__main__":
    print("Starting Unified Diagnostic System - Root Engine")
    uds = UnifiedDiagnosticSystem()
    
    print("System initialized successfully!")
    print(f"CAN-BUS Connected: {uds.bus_connected}")
    print(f"Core System Status: {uds.get_unified_status()}")
    
    # Launch the diagnostic system
    launch_result = uds.launch_diagnostic_system()
    print(f"Diagnostic System Launch: {'SUCCESS' if launch_result else 'FAILED'}")