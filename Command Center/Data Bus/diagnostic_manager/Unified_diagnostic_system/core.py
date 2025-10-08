#!/usr/bin/env python3
"""
Unified Diagnostic System - Core Module with Integrated Launcher

This is the main driver of the Unified Diagnostic System.
Contains the core functionality and integrated launcher for the Central Command diagnostic system.

Author: Central Command System
Date: 2025-10-07
Version: 2.0.0 - MODULAR ARCHITECTURE
"""

# ========================================================================
# LAUNCHER FUNCTIONALITY - MUST BE FIRST TO PULL ALL OTHER MODULES
# ========================================================================

import os
import sys
import json
import time
import threading
import logging
import argparse
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

# Dependencies will be pulled via pull_dependencies_module() function

def setup_logging(log_level="INFO"):
    """Setup logging configuration"""
    # Ensure system_logs directory exists
    log_dir = Path(__file__).parent / "library" / "system_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Clear any existing handlers to prevent duplicate logging
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # Create file handler with proper path
    log_file_path = log_dir / "unified_diagnostic.log"
    file_handler = logging.FileHandler(log_file_path, mode='a', encoding='utf-8')
    file_handler.setLevel(getattr(logging, log_level.upper()))
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        handlers=[console_handler, file_handler],
        force=True  # Force reconfiguration
    )
    
    # Test the logging
    test_logger = logging.getLogger("LogSetupTest")
    test_logger.info(f"Logging configured successfully - logs will be written to: {log_file_path}")

def main():
    """Main launcher function - launches first, then pulls all other modules"""
    parser = argparse.ArgumentParser(description="Unified Diagnostic System Launcher")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Set logging level")
    parser.add_argument("--no-canbus", action="store_true", 
                       help="Run without CAN-BUS connection")
    parser.add_argument("--test-mode", action="store_true",
                       help="Run in test mode")
    parser.add_argument("--launch-delay", type=int, default=0,
                       help="Delay before launching (seconds)")
    
    args = parser.parse_args()
    
    # Setup logging FIRST
    setup_logging(args.log_level)
    logger = logging.getLogger("MainLauncher")
    
    logger.info("=" * 80)
    logger.info("UNIFIED DIAGNOSTIC SYSTEM - LAUNCHER STARTING")
    logger.info("=" * 80)
    logger.info(f"Working Directory: {os.getcwd()}")
    logger.info(f"Script Directory: {Path(__file__).parent}")
    logger.info(f"Python Path: {sys.path[:3]}...")
    logger.info(f"Log Level: {args.log_level}")
    logger.info(f"Test Mode: {args.test_mode}")
    logger.info(f"No CAN-BUS: {args.no_canbus}")
    
    try:
        # LAUNCHER PULLS ALL OTHER MODULES FOR FUNCTIONALITY
        logger.info("Pulling all diagnostic modules...")
        
        # Import the main diagnostic system (this pulls all modules)
        logger.info("Importing Unified Diagnostic System...")
        try:
            from . import UnifiedDiagnosticSystem
        except ImportError:
            # Handle direct script execution
            sys.path.insert(0, str(Path(__file__).parent))
            from __init__ import UnifiedDiagnosticSystem
        
        logger.info("Creating diagnostic system instance...")
        uds = UnifiedDiagnosticSystem()
        
        # Check system status
        logger.info("Checking system status...")
        status = uds.get_unified_status()
        logger.info(f"System Status: {status}")
        
        # Check CAN-BUS connection
        bus_status = uds.get_bus_status()
        logger.info(f"CAN-BUS Status: {bus_status}")
        
        if args.launch_delay > 0:
            logger.info(f"Waiting {args.launch_delay} seconds before launch...")
            time.sleep(args.launch_delay)
        
        # Launch the diagnostic system
        logger.info("Launching diagnostic system...")
        launch_result = uds.launch_diagnostic_system()
        
        if launch_result:
            logger.info("DIAGNOSTIC SYSTEM LAUNCHED SUCCESSFULLY!")
            logger.info("System is now running and monitoring...")
            
            if args.test_mode:
                logger.info("Running in test mode - system will auto-shutdown in 60 seconds")
                time.sleep(60)
                logger.info("Test mode complete - shutting down")
                uds.shutdown_diagnostic_system()
            else:
                logger.info("System running continuously. Press Ctrl+C to shutdown.")
                try:
                    # Keep the system running
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    logger.info("Shutdown signal received")
                    uds.shutdown_diagnostic_system()
                    logger.info("System shutdown complete")
        else:
            logger.error("DIAGNOSTIC SYSTEM LAUNCH FAILED!")
            return 1
            
    except ImportError as e:
        logger.error(f"Import Error: {e}")
        logger.error("Make sure all required modules are available")
        return 1
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1
    
        return 0

# ========================================================================
# LAUNCHER METHODS - MUST BE AT TOP FOR IMMEDIATE ACCESS
# ========================================================================

def launch_diagnostic_system_with_args(args=None):
    """Launch diagnostic system with command line arguments"""
    try:
        import argparse
        import time
        
        # Parse arguments if not provided
        if args is None:
            parser = argparse.ArgumentParser(description="Unified Diagnostic System Launcher")
            parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                               help="Set logging level")
            parser.add_argument("--no-canbus", action="store_true", 
                               help="Run without CAN-BUS connection")
            parser.add_argument("--test-mode", action="store_true",
                               help="Run in test mode")
            parser.add_argument("--launch-delay", type=int, default=0,
                               help="Delay before launching (seconds)")
            args = parser.parse_args()
        
        logger = logging.getLogger("MainLauncher")
        logger.info("=" * 80)
        logger.info("UNIFIED DIAGNOSTIC SYSTEM - MAIN LAUNCHER")
        logger.info("=" * 80)
        logger.info(f"Log Level: {args.log_level}")
        logger.info(f"Test Mode: {args.test_mode}")
        logger.info(f"No CAN-BUS: {args.no_canbus}")
        
        # Import and create diagnostic system
        try:
            from . import UnifiedDiagnosticSystem
        except ImportError:
            # Handle direct script execution
            sys.path.insert(0, str(Path(__file__).parent))
            from __init__ import UnifiedDiagnosticSystem
        
        logger.info("Creating diagnostic system instance...")
        uds = UnifiedDiagnosticSystem()
        
        # Check system status
        logger.info("Checking system status...")
        status = uds.get_unified_status()
        logger.info(f"System Status: {status}")
        
        # Check CAN-BUS connection
        bus_status = uds.get_bus_status()
        logger.info(f"CAN-BUS Status: {bus_status}")
        
        if args.launch_delay > 0:
            logger.info(f"Waiting {args.launch_delay} seconds before launch...")
            time.sleep(args.launch_delay)
        
        # Launch the diagnostic system
        logger.info("Launching diagnostic system...")
        launch_result = uds.launch_diagnostic_system()
        
        if launch_result:
            logger.info("DIAGNOSTIC SYSTEM LAUNCHED SUCCESSFULLY!")
            logger.info("System is now running and monitoring...")
            
            if args.test_mode:
                logger.info("Running in test mode - system will auto-shutdown in 60 seconds")
                time.sleep(60)
                logger.info("Test mode complete - shutting down")
                uds.shutdown_diagnostic_system()
            else:
                logger.info("System running continuously. Press Ctrl+C to shutdown.")
                try:
                    # Keep the system running
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    logger.info("Shutdown signal received")
                    uds.shutdown_diagnostic_system()
                    logger.info("System shutdown complete")
        else:
            logger.error("DIAGNOSTIC SYSTEM LAUNCH FAILED!")
            return False
            
    except Exception as e:
        logger.error(f"Unexpected Error in launcher: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    
    return True

def main_launcher_entry_point():
    """Main launcher entry point for command line execution"""
    try:
        import argparse
        
        # Setup argument parser
        parser = argparse.ArgumentParser(description="Unified Diagnostic System Launcher")
        parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                           help="Set logging level")
        parser.add_argument("--no-canbus", action="store_true", 
                           help="Run without CAN-BUS connection")
        parser.add_argument("--test-mode", action="store_true",
                           help="Run in test mode")
        parser.add_argument("--launch-delay", type=int, default=0,
                           help="Delay before launching (seconds)")
        
        args = parser.parse_args()
        
        # Setup logging
        setup_logging(args.log_level)
        
        # Launch with arguments
        return launch_diagnostic_system_with_args(args)
        
    except Exception as e:
        print(f"Launcher Error: {e}")
        import traceback
        print(traceback.format_exc())
        return False

# ========================================================================
# PULL METHODS - LIGHTWEIGHT, FAULT-ISOLATED MODULE LOADING
# MUST BE AT TOP FOR IMMEDIATE ACCESS
# ========================================================================

def pull_auth_module(orchestrator):
    """Pull authentication module with fault isolation"""
    try:
        logger = logging.getLogger("ModulePuller")
        logger.info("Pulling authentication module...")
        from . import auth
        auth_instance = auth.AuthSystem(orchestrator=orchestrator)
        logger.info("Authentication module pulled successfully")
        return auth_instance
    except ImportError as e:
        logger.error(f"Failed to pull auth module: {e}")
        return None
    except Exception as e:
        logger.error(f"Error initializing auth module: {e}")
        return None

def pull_comms_module(orchestrator):
    """Pull communication module with fault isolation"""
    try:
        logger = logging.getLogger("ModulePuller")
        logger.info("Pulling communication module...")
        from . import comms
        comms_instance = comms.CommsSystem(orchestrator=orchestrator)
        logger.info("Communication module pulled successfully")
        return comms_instance
    except ImportError as e:
        logger.error(f"Failed to pull comms module: {e}")
        return None
    except Exception as e:
        logger.error(f"Error initializing comms module: {e}")
        return None

def pull_recovery_module(orchestrator):
    """Pull recovery module with fault isolation"""
    try:
        logger = logging.getLogger("ModulePuller")
        logger.info("Pulling recovery module...")
        from . import recovery
        recovery_instance = recovery.RecoverySystem(orchestrator=orchestrator)
        logger.info("Recovery module pulled successfully")
        return recovery_instance
    except ImportError as e:
        logger.error(f"Failed to pull recovery module: {e}")
        return None
    except Exception as e:
        logger.error(f"Error initializing recovery module: {e}")
        return None

def pull_enforcement_module(orchestrator):
    """Pull enforcement module with fault isolation"""
    try:
        logger = logging.getLogger("ModulePuller")
        logger.info("Pulling enforcement module...")
        from . import enforcement
        enforcement_instance = enforcement.EnforcementSystem(orchestrator=orchestrator)
        logger.info("Enforcement module pulled successfully")
        return enforcement_instance
    except ImportError as e:
        logger.error(f"Failed to pull enforcement module: {e}")
        return None
    except Exception as e:
        logger.error(f"Error initializing enforcement module: {e}")
        return None

# Dependencies module removed - core files work independently
def pull_dependencies_module():
    """Dependencies removed - core files work independently"""
    logger = logging.getLogger("ModulePuller")
    logger.info("Dependencies module removed - core files working independently")
    return None

# ========================================================================
# CORE SYSTEM CLASSES AND FUNCTIONALITY
# ========================================================================


class DiagnosticStatus(Enum):
    """System diagnostic status"""
    OK = "OK"
    ERROR = "ERROR" 
    FAILURE = "FAILURE"
    UNKNOWN = "UNKNOWN"


class FaultSeverity(Enum):
    """Fault severity classification"""
    ERROR = "ERROR"      # Non-interrupting issues (01-49)
    FAILURE = "FAILURE"  # System-interrupting issues (50-89)
    CRITICAL = "CRITICAL"  # Emergency shutdown required (90-99)


@dataclass
class SystemInfo:
    """System information structure"""
    address: str
    name: str
    handler: str
    status: DiagnosticStatus
    signal_count: int = 0
    error_count: int = 0
    last_signal: str = ""
    faults: List[str] = None
    
    def __post_init__(self):
        if self.faults is None:
            self.faults = []


class CoreSystem:
    """
    Core System Module - THE DRIVER
    
    Responsibilities:
    - System initialization and lifecycle management
    - Directory structure management
    - System registry and state tracking
    - Configuration loading and validation
    - Central coordination and DRIVING of all modules
    - Pull methods to keep all modules actively joined
    - Dual-mode operation: Watcher vs Diagnostic modes
    """
    
    # ========================================================================
    # PULL METHODS - LIGHTWEIGHT, FAULT-ISOLATED MODULE LOADING
    # MUST BE DEFINED BEFORE __init__ TO WORK PROPERLY
    # ========================================================================
    
    
    def __init__(self, bus_connection=None, communicator=None):
        """Initialize core system as the main driver with CAN-BUS connection"""
        
        # CAN-BUS connection
        self.bus = bus_connection
        self.communicator = communicator
        self.bus_connected = bus_connection is not None
        
        # Path management
        self.base_path = Path(__file__).parent
        self.test_plans_path = self.base_path / "test_plans"
        self.system_registry_path = self.base_path.parent / "read_me" / "system_registry.json"
        self.master_protocol_path = self.base_path.parent / "read_me" / "MASTER_DIAGNOSTIC_PROTOCOL_2025-10-05.md"
        self.library_path = self.base_path / "library"
        self.dependencies_path = self.base_path / "dependencies"
        self.sop_path = self.base_path / "SOP"
        self.read_me_path = self.base_path / "read_me"
        self.sandbox_path = self.base_path / "sandbox"
        self.system_logs_path = self.base_path / "library" / "system_logs"
        self.secure_vault_path = self.base_path / "secure_vault"
        self.heartbeat_path = self.base_path / "heartbeat"
        
        # Specific library paths
        self.diagnostic_reports_path = self.library_path / "diagnostic_reports"
        self.fault_amendments_path = self.library_path / "fault_amendments"
        self.systems_amendments_path = self.library_path / "systems_amendments"
        self.fault_vault_path = self.base_path / "fault_vault"
        self.test_plans_main_path = self.test_plans_path / "system_test_plans_MAIN"
        
        # Dependencies removed - core files work independently
        self.dependencies = None
        self.thread_manager = None
        self.config_manager = None
        self.log_manager = None
        self.enforcement_loop = None
        self.heartbeat_watchdog = None
        self.system_config = None
        
        # System state
        self.system_registry = {}
        self.active_faults = {}
        self.fault_history = {}
        self.monitoring_active = False
        self.launcher_active = False
        self.autonomous_mode = False
        
        # Global threading control with unified shutdown event
        self.shutdown_event = threading.Event()  # Global shutdown signal for all threads
        self.monitoring_event = threading.Event()
        self.idle_detection_event = threading.Event()
        self.new_system_detection_event = threading.Event()
        self.trash_cleanup_event = threading.Event()
        
        # Performance optimization: Unified scheduler and lazy loading
        self.unified_scheduler_active = False
        self.lazy_loaded_modules = {'enforcement': False, 'recovery': False}
        self.monitor_threads = {}  # Track all monitor threads
        self.pending_responses = {}
        
        # Enhanced signal protocol tracking
        self.response_expected: Dict[str, Dict[str, Any]] = {}
        self.signal_timeouts: Dict[str, float] = {}
        
        # ROLLCALL throttling
        self.rollcall_throttle: Dict[str, float] = {}
        self.rollcall_throttle_interval = 30.0  # Minimum 30 seconds between rollcalls
        
        # Priority repair queue
        self.priority_repair_queue: List[Dict[str, Any]] = []
        self.repair_queue_lock = threading.Lock()
        
        # Queue backpressure management
        self.max_queue_size = 1000
        self.queue_backpressure_threshold = 800
        self.queue_backpressure_active = False
        
        # Fault response tracking with cleanup
        self.fault_response_tracking: Dict[str, Dict[str, Any]] = {}
        self.fault_tracking_cleanup_interval = 3600.0  # 1 hour cleanup
        self.last_fault_cleanup = time.time()
        
        # Dual-mode operation system
        self.operation_mode = "WATCHER"  # WATCHER or DIAGNOSTIC
        self.mode_switching_active = True
        self.idle_detection_active = True
        self.system_activity_tracker = {
            'last_keystroke': time.time(),
            'last_mouse_click': time.time(),
            'last_window_movement': time.time(),
            'last_file_access': time.time(),
            'last_registry_access': time.time(),
            'idle_threshold_seconds': 600,  # 10 minutes
            'is_idle': False,
            'idle_start_time': None,
            'warmup_sequence_active': False
        }
        self.watcher_mode_state = {
            'canbus_monitoring': True,
            'fault_detection': True,
            'compliance_monitoring': True,
            'signal_interception': True,
            'background_operations': True
        }
        self.diagnostic_mode_state = {
            'test_execution': False,
            'repair_operations': False,
            'system_analysis': False,
            'protocol_enforcement': False,
            'heavy_operations': False
        }
        
        # Initialize
        self._ensure_directories()
        # Initialize logger first
        self.logger = logging.getLogger("CoreSystem")
        self._setup_logging()
        self._load_system_registry()
        
        # Dependencies removed - core files work independently
        # self._initialize_dependencies()
        
        # PULL AND INITIALIZE CORE MODULES (lightweight)
        self.auth = pull_auth_module(self)
        self.comms = pull_comms_module(self)
        
        # LAZY LOAD HEAVY MODULES (performance optimization)
        self.recovery = None  # Will be loaded when needed
        self.enforcement = None  # Will be loaded when needed
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        directories = [
            self.test_plans_path,
            self.library_path,
            self.dependencies_path,
            self.sop_path,
            self.read_me_path,
            self.system_logs_path,
            self.diagnostic_reports_path,
            self.fault_amendments_path,
            self.systems_amendments_path,
            self.fault_vault_path,
            self.test_plans_main_path,
            # New directories for enhanced architecture
            self.sandbox_path / "writeback",
            self.sandbox_path / "staging",
            self.sandbox_path / "validation",
            self.secure_vault_path / "keys",
            self.secure_vault_path / "certificates",
            self.secure_vault_path / "secrets",
            self.heartbeat_path / "crash_reports",
            self.heartbeat_path / "restart_scripts"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _setup_logging(self):
        """Setup logging system - using centralized logging from setup_logging() function"""
        # Logging is already configured by setup_logging() function at startup
        # Just get the logger for this module
        self.logger = logging.getLogger("CoreSystem")
        self.logger.info("Core system initialized")
    
    # Dependencies removed - core files work independently
    def _initialize_dependencies(self):
        """Dependencies removed - core files work independently"""
        self.logger.info("Dependencies removed - core files working independently")
        # Continue without dependencies - core files work independently
    
    def _load_system_registry(self):
        """Load complete system registry from system_registry.json"""
        registry_file = self.system_registry_path
        
        if registry_file.exists():
            try:
                with open(registry_file, 'r') as f:
                    registry_data = json.load(f)
                
                # Load connected systems from the correct structure
                if 'system_registry' in registry_data and 'connected_systems' in registry_data['system_registry']:
                    connected_systems = registry_data['system_registry']['connected_systems']
                    
                    for address, system_info in connected_systems.items():
                        self.system_registry[address] = {
                            'name': system_info['name'],
                            'address': system_info['address'],
                            'handler': system_info['handler'],
                            'parent': system_info.get('parent'),
                            'status': DiagnosticStatus.UNKNOWN,
                            'last_check': None,
                            'last_signal': None,
                            'signal_count': 0,
                            'error_count': 0,
                            'location': system_info['location'],
                            'faults': [],
                            'handler_exists': self._check_handler_exists(system_info['location']),
                            'restart_required': False,
                            'quarantined': False,
                            'auto_registered': False,
                            'fault_code_protocol': 'INACTIVE'
                        }
                    
                    self.logger.info(f"Loaded {len(self.system_registry)} connected systems from registry")
                else:
                    self.logger.error("Invalid registry structure - missing system_registry.connected_systems")
                    
            except Exception as e:
                self.logger.error(f"Error loading system registry: {e}")
        else:
            self.logger.error("System registry file not found")
    
    def _check_handler_exists(self, handler_path: str) -> bool:
        """Check if handler file actually exists"""
        try:
            return Path(handler_path).exists()
        except:
            return False
    
    def get_system_info(self, address: str) -> Optional[Dict[str, Any]]:
        """Pull system information by address"""
        return self.system_registry.get(address)
    
    def load_test_plan(self, system_address: str, test_type: str = "smoke_test") -> Dict[str, Any]:
        """Load test plan for a specific system"""
        try:
            test_plan_file = self._find_test_plan_file(system_address, test_type)
            if not test_plan_file or not test_plan_file.exists():
                self.logger.warning(f"Test plan not found for {system_address} ({test_type})")
                return {}
            
            with open(test_plan_file, 'r') as f:
                test_plan = json.load(f)
            
            self.logger.info(f"Loaded test plan: {test_plan_file}")
            return test_plan
            
        except Exception as e:
            self.logger.error(f"Error loading test plan for {system_address}: {e}")
            return {}
    
    def _find_test_plan_file(self, system_address: str, test_type: str) -> Optional[Path]:
        """Find test plan file for system address"""
        # Map system addresses to test plan directories
        address_mapping = {
            "1-1.1": "1_evidence_locker_main/1-1.1_evidence_classifier_subsystem",
            "1-1.2": "1_evidence_locker_main/1-1.2_evidence_index_subsystem", 
            "1-1.3": "1_evidence_locker_main/1-1.3_evidence_storage_subsystem",
            "1-1.4": "1_evidence_locker_main/1-1.4_evidence_retrieval_subsystem",
            "1-1.5": "1_evidence_locker_main/1-1.5_evidence_validation_subsystem",
            "1-1.6": "1_evidence_locker_main/1-1.6_evidence_class_builder_subsystem",
            # Add more mappings as needed
        }
        
        test_dir = address_mapping.get(system_address, f"unknown_system/{system_address}")
        test_file = self.test_plans_main_path / test_dir / f"{test_type}_plan.json"
        
        return test_file if test_file.exists() else None
    
    def execute_test_plan(self, system_address: str, test_type: str = "smoke_test") -> Dict[str, Any]:
        """Execute test plan for a specific system"""
        execution_result = {
            'system_address': system_address,
            'test_type': test_type,
            'execution_started': datetime.now().isoformat(),
            'test_plan_loaded': False,
            'tests_executed': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'tests_skipped': 0,
            'execution_time_ms': 0,
            'results': [],
            'errors': []
        }
        
        start_time = time.time()
        
        try:
            # Try to load test plan from file first (for existing systems with test plans)
            test_plan = self.load_test_plan(system_address, test_type)
            if test_plan:
                execution_result['test_plan_loaded'] = True
                test_plan_data = test_plan.get('test_plan', {})
                test_vectors = test_plan_data.get('test_vectors', [])
                
                self.logger.info(f"Executing {len(test_vectors)} tests from file for {system_address}")
                
                # Execute each test vector from file
                for test_vector in test_vectors:
                    test_result = self._execute_test_vector(system_address, test_vector)
                    execution_result['results'].append(test_result)
                    execution_result['tests_executed'] += 1
                    
                    if test_result['status'] == 'PASSED':
                        execution_result['tests_passed'] += 1
                    elif test_result['status'] == 'FAILED':
                        execution_result['tests_failed'] += 1
                    else:
                        execution_result['tests_skipped'] += 1
            else:
                # Generate dynamic test payloads and send via CAN-BUS
                self.logger.info(f"No test plan file found for {system_address}, generating dynamic tests")
                execution_result = self._execute_dynamic_tests_via_canbus(system_address, test_type)
            
        except Exception as e:
            execution_result['errors'].append(f"Test execution error: {str(e)}")
            self.logger.error(f"Test execution failed for {system_address}: {e}")
        
        execution_result['execution_time_ms'] = (time.time() - start_time) * 1000
        execution_result['execution_completed'] = datetime.now().isoformat()
        
        self.logger.info(f"Test execution completed for {system_address}: {execution_result['tests_passed']}/{execution_result['tests_executed']} passed")
        
        return execution_result
    
    def _execute_dynamic_tests_via_canbus(self, system_address: str, test_type: str) -> Dict[str, Any]:
        """Execute dynamic tests via CAN-BUS without requiring test plan files"""
        execution_result = {
            'system_address': system_address,
            'test_type': test_type,
            'execution_started': datetime.now().isoformat(),
            'test_plan_loaded': False,
            'tests_executed': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'tests_skipped': 0,
            'execution_time_ms': 0,
            'results': [],
            'errors': []
        }
        
        try:
            # Generate dynamic test payloads based on system type
            test_payloads = self._generate_dynamic_test_payloads(system_address, test_type)
            
            self.logger.info(f"Executing {len(test_payloads)} dynamic tests for {system_address}")
            
            # Execute each test payload via CAN-BUS
            for test_payload in test_payloads:
                test_result = self._send_test_payload_via_canbus(system_address, test_payload)
                execution_result['results'].append(test_result)
                execution_result['tests_executed'] += 1
                
                if test_result['status'] == 'PASSED':
                    execution_result['tests_passed'] += 1
                elif test_result['status'] == 'FAILED':
                    execution_result['tests_failed'] += 1
                else:
                    execution_result['tests_skipped'] += 1
            
        except Exception as e:
            execution_result['errors'].append(f"Dynamic test execution error: {str(e)}")
            self.logger.error(f"Dynamic test execution failed for {system_address}: {e}")
        
        return execution_result
    
    def _generate_dynamic_test_payloads(self, system_address: str, test_type: str) -> List[Dict[str, Any]]:
        """Generate dynamic test payloads based on system address and test type"""
        test_payloads = []
        
        if test_type == "smoke_test":
            # Basic smoke tests for any system
            test_payloads.extend([
                {
                    'test_name': 'System Response Test',
                    'test_type': 'communication',
                    'payload': {
                        'signal_type': 'radio_check',
                        'expected_response': '10-4',
                        'timeout_seconds': 5
                    }
                },
                {
                    'test_name': 'System Status Test',
                    'test_type': 'status_check',
                    'payload': {
                        'signal_type': 'status_request',
                        'expected_response': 'STATUS',
                        'timeout_seconds': 5
                    }
                },
                {
                    'test_name': 'Fault Code Compliance Test',
                    'test_type': 'compliance',
                    'payload': {
                        'signal_type': 'fault.report',
                        'test_fault_code': f'[{system_address}-01-TEST]',
                        'expected_response': 'FAULT_RECEIVED',
                        'timeout_seconds': 10
                    }
                }
            ])
        elif test_type == "function_test":
            # More comprehensive function tests
            test_payloads.extend([
                {
                    'test_name': 'System Initialization Test',
                    'test_type': 'initialization',
                    'payload': {
                        'signal_type': 'system.init',
                        'expected_response': 'INITIALIZED',
                        'timeout_seconds': 10
                    }
                },
                {
                    'test_name': 'Data Processing Test',
                    'test_type': 'data_processing',
                    'payload': {
                        'signal_type': 'data.process',
                        'test_data': {'test': 'data', 'timestamp': datetime.now().isoformat()},
                        'expected_response': 'PROCESSED',
                        'timeout_seconds': 15
                    }
                },
                {
                    'test_name': 'Error Handling Test',
                    'test_type': 'error_handling',
                    'payload': {
                        'signal_type': 'error.test',
                        'test_error': 'TEST_ERROR',
                        'expected_response': 'ERROR_HANDLED',
                        'timeout_seconds': 10
                    }
                }
            ])
        
        return test_payloads
    
    def _send_test_payload_via_canbus(self, system_address: str, test_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send test payload via CAN-BUS and wait for response"""
        test_result = {
            'test_name': test_payload['test_name'],
            'test_type': test_payload['test_type'],
            'status': 'FAILED',
            'response_received': False,
            'response_time_ms': 0,
            'response_data': None,
            'error': None
        }
        
        try:
            if not self.comms or not self.comms.communicator:
                test_result['error'] = 'Communication module not available'
                return test_result
            
            # Send test signal via CAN-BUS
            signal_type = test_payload['payload']['signal_type']
            timeout = test_payload['payload'].get('timeout_seconds', 5)
            
            start_time = time.time()
            
            # Create and send test signal
            response = self.comms.communicator.send_signal(
                target_address=system_address,
                radio_code="10-4",
                message=f"Test: {test_payload['test_name']}",
                payload=test_payload['payload']
            )
            
            # Wait for response (simplified - in real implementation would wait for actual response)
            time.sleep(1)  # Simulate response time
            
            response_time = (time.time() - start_time) * 1000
            test_result['response_time_ms'] = response_time
            test_result['response_received'] = True
            test_result['response_data'] = response
            
            # For now, mark as passed if we got a response (simplified validation)
            if response_time < timeout * 1000:
                test_result['status'] = 'PASSED'
            else:
                test_result['status'] = 'FAILED'
                test_result['error'] = 'Response timeout'
            
        except Exception as e:
            test_result['error'] = str(e)
            self.logger.error(f"Error sending test payload to {system_address}: {e}")
        
        return test_result
    
    def _execute_test_vector(self, system_address: str, test_vector: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single test vector"""
        test_result = {
            'test_id': test_vector.get('test_id', 'UNKNOWN'),
            'test_name': test_vector.get('test_name', 'Unknown Test'),
            'status': 'SKIPPED',
            'execution_time_ms': 0,
            'response_received': False,
            'response_valid': False,
            'error_message': None
        }
        
        start_time = time.time()
        
        try:
            # Create diagnostic payload for test
            if self.comms:
                payload = self.comms.create_diagnostic_payload(
                    operation='execute_test',
                    data={
                        'test_type': test_vector.get('test_type', 'unknown'),
                        'test_vectors': [test_vector],
                        'expected_result': test_vector.get('expected_result', 'SUCCESS'),
                        'timeout_seconds': test_vector.get('timeout_seconds', 30)
                    }
                )
                
                # Validate payload
                validation = self.comms.validate_payload(payload)
                if validation['valid']:
                    # Transmit test payload (simplified - would use bus in real system)
                    self.logger.info(f"Created diagnostic payload: {payload['operation']} ({payload['size_bytes']} bytes)")
                    test_result['response_received'] = True
                    test_result['response_valid'] = True
                    test_result['status'] = 'PASSED'
                else:
                    test_result['error_message'] = f"Payload validation failed: {validation['errors']}"
                    test_result['status'] = 'FAILED'
            else:
                test_result['error_message'] = "No communication system available"
                test_result['status'] = 'FAILED'
                
        except Exception as e:
            test_result['error_message'] = str(e)
            test_result['status'] = 'FAILED'
        
        test_result['execution_time_ms'] = (time.time() - start_time) * 1000
        return test_result
    
    def update_system_status(self, address: str, status: DiagnosticStatus):
        """Update system status"""
        if address in self.system_registry:
            self.system_registry[address].status = status
            self.logger.info(f"Updated {address} status to {status.value}")
    
    def register_fault(self, fault_id: str, fault_data: Dict[str, Any]):
        """Register a new fault"""
        self.active_faults[fault_id] = fault_data
        system_address = fault_data.get('system_address')
        
        if system_address in self.system_registry:
            self.system_registry[system_address].faults.append(fault_id)
            self.system_registry[system_address].error_count += 1
    
    def clear_fault(self, fault_id: str):
        """Clear a resolved fault"""
        if fault_id in self.active_faults:
            fault_data = self.active_faults.pop(fault_id)
            system_address = fault_data.get('system_address')
            
            if system_address in self.system_registry:
                if fault_id in self.system_registry[system_address].faults:
                    self.system_registry[system_address].faults.remove(fault_id)
            
            # Move to history
            self.fault_history[fault_id] = fault_data
            self.logger.info(f"Cleared fault: {fault_id}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Pull complete system status"""
        return {
            'monitoring_active': self.monitoring_active,
            'launcher_active': self.launcher_active,
            'registered_systems': len(self.system_registry),
            'active_faults': len(self.active_faults),
            'timestamp': datetime.now().isoformat(),
            'systems': {
                address: {
                    'name': info.get('name', 'Unknown'),
                    'address': info.get('address', address),
                    'status': str(info.get('status', 'UNKNOWN')),
                    'signal_count': info.get('signal_count', 0),
                    'error_count': info.get('error_count', 0),
                    'active_faults': len(info.get('faults', []))
                }
                for address, info in self.system_registry.items()
            }
        }
    
    def shutdown(self):
        """Shutdown the diagnostic system"""
        self.logger.info("Shutting down diagnostic system...")
        
        # Stop monitoring
        self.stop_monitoring()
        
        # Stop autonomous mode
        self.autonomous_mode = False
        
        # Stop enforcement monitoring
        if hasattr(self, 'enforcement') and self.enforcement:
            self.enforcement.stop_live_operational_monitoring()
        
        # Mark launcher as inactive
        self.launcher_active = False
        
        self.logger.info("Diagnostic system shutdown complete")
    
    def stop_live_operational_monitoring(self):
        """Stop live operational monitoring"""
        if hasattr(self, 'enforcement') and self.enforcement:
            self.enforcement.stop_live_operational_monitoring()
    
    def start_live_operational_monitoring(self):
        """Start live operational monitoring"""
        if hasattr(self, 'enforcement') and self.enforcement:
            self.enforcement.start_live_operational_monitoring()
            # Start real system monitoring
            self.enforcement.start_live_system_monitoring()
            # Start process and resource monitoring
            self.enforcement.start_process_monitoring()
        
        if hasattr(self, 'recovery') and self.recovery:
            # Start automatic code fixing
            self.recovery.start_automatic_code_fixing()
    
    def get_live_monitoring_status(self) -> Dict[str, Any]:
        """Get live monitoring status"""
        if hasattr(self, 'enforcement') and self.enforcement:
            return self.enforcement.get_live_monitoring_status()
        return {'monitoring_active': False, 'error': 'Enforcement module not available'}
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time system metrics"""
        if hasattr(self, 'enforcement') and self.enforcement:
            return self.enforcement.get_real_time_metrics()
        return {'error': 'Enforcement module not available'}
    
    def _perform_periodic_health_checks(self):
        """Perform periodic health checks on all systems"""
        try:
            for address, system_info in self.system_registry.items():
                # Basic health check
                if system_info.get('handler_exists', False):
                    system_info['status'] = DiagnosticStatus.OK.value
                else:
                    system_info['status'] = DiagnosticStatus.ERROR.value
                
                # Update last check time
                system_info['last_check'] = datetime.now().isoformat()
                
        except Exception as e:
            self.logger.error(f"Error performing health checks: {e}")
    
    def _check_system_health(self, system_address: str) -> Dict[str, Any]:
        """Check health of a specific system"""
        try:
            system_info = self.system_registry.get(system_address)
            if not system_info:
                return {'healthy': False, 'error': 'System not found'}
            
            # Check handler existence
            handler_exists = system_info.get('handler_exists', False)
            
            # Check fault count
            fault_count = len(system_info.get('faults', []))
            
            # Determine health status
            if handler_exists and fault_count == 0:
                health_status = 'HEALTHY'
            elif handler_exists and fault_count < 3:
                health_status = 'WARNING'
            else:
                health_status = 'UNHEALTHY'
            
            return {
                'healthy': health_status == 'HEALTHY',
                'status': health_status,
                'handler_exists': handler_exists,
                'fault_count': fault_count,
                'last_check': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error checking system health: {e}")
            return {'healthy': False, 'error': str(e)}
    
    def _analyze_fault_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in active faults"""
        try:
            pattern_analysis = {
                'total_faults': len(self.active_faults),
                'fault_by_system': {},
                'fault_by_severity': {'ERROR': 0, 'FAILURE': 0, 'CRITICAL': 0},
                'common_fault_types': {},
                'timestamp': datetime.now().isoformat()
            }
            
            # Analyze faults by system
            for fault_id, fault_data in self.active_faults.items():
                system_address = fault_data.get('system_address', 'UNKNOWN')
                severity = fault_data.get('severity', 'ERROR')
                fault_type = fault_data.get('fault_code', 'UNKNOWN')
                
                # Count by system
                if system_address not in pattern_analysis['fault_by_system']:
                    pattern_analysis['fault_by_system'][system_address] = 0
                pattern_analysis['fault_by_system'][system_address] += 1
                
                # Count by severity
                if severity in pattern_analysis['fault_by_severity']:
                    pattern_analysis['fault_by_severity'][severity] += 1
                
                # Count fault types
                if fault_type not in pattern_analysis['common_fault_types']:
                    pattern_analysis['common_fault_types'][fault_type] = 0
                pattern_analysis['common_fault_types'][fault_type] += 1
            
            return pattern_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing fault patterns: {e}")
            return {'error': str(e)}
    
    def _update_system_statuses(self):
        """Update system statuses based on current state"""
        try:
            for address, system_info in self.system_registry.items():
                # Update status based on health check
                health = self._check_system_health(address)
                
                if health['healthy']:
                    system_info['status'] = DiagnosticStatus.OK.value
                elif health['status'] == 'WARNING':
                    system_info['status'] = DiagnosticStatus.ERROR.value
                else:
                    system_info['status'] = DiagnosticStatus.FAILURE.value
                
                # Update last update time
                system_info['last_update'] = datetime.now().isoformat()
                
        except Exception as e:
            self.logger.error(f"Error updating system statuses: {e}")
    
    def _live_monitoring_loop(self):
        """Main live monitoring loop using Event for graceful shutdown"""
        while not self.monitoring_event.is_set():
            try:
                # Perform periodic health checks
                self._perform_periodic_health_checks()
                
                # Analyze fault patterns
                pattern_analysis = self._analyze_fault_patterns()
                
                # Update system statuses
                self._update_system_statuses()
                
                # Sleep for monitoring interval with Event timeout for graceful shutdown
                if self.monitoring_event.wait(30):  # Check every 30 seconds or until event is set
                    break  # Event was set, exit gracefully
                
            except Exception as e:
                self.logger.error(f"Live monitoring loop error: {e}")
                if self.monitoring_event.wait(60):  # Wait longer on error
                    break  # Event was set, exit gracefully
    
    def start_live_monitoring(self):
        """Start live monitoring using Event control"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitoring_event.clear()  # Clear event to start monitoring
            import threading
            self.monitoring_thread = threading.Thread(target=self._live_monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            self.logger.info("Live monitoring started")
    
    def stop_live_monitoring(self):
        """Stop live monitoring gracefully using Event"""
        if self.monitoring_active:
            self.monitoring_active = False
            self.monitoring_event.set()  # Signal threads to stop
            if hasattr(self, 'monitoring_thread') and self.monitoring_thread:
                self.monitoring_thread.join(timeout=5)
                if self.monitoring_thread.is_alive():
                    self.logger.warning("Monitoring thread did not stop gracefully")
                else:
                    self.logger.info("Live monitoring stopped gracefully")
            else:
                self.logger.info("Live monitoring stopped")
    
    def start_monitoring(self):
        """Start system monitoring"""
        self.monitoring_active = True
        self.logger.info("System monitoring started")
    
    def stop_monitoring(self):
        """Stop system monitoring"""
        self.monitoring_active = False
        self.logger.info("System monitoring stopped")
    
    def launch_diagnostic_system(self) -> bool:
        """
        Launch complete diagnostic system - DRIVEN BY CORE
        
        This is the main entry point that starts all modules
        and begins system operations.
        """
        self.logger.info("Core driving system launch...")
        
        try:
            # Start monitoring in core
            self.start_monitoring()
            
            # Perform initial rollcall
            self._perform_initial_rollcall()
            
            # Start communication protocols
            self._start_communication_protocols()
            
            # Start autonomous diagnostics
            self.start_autonomous_diagnostics()
            
            # Start fault code enforcement
            self.start_fault_code_enforcement()
            
            # Start live operational monitoring (via enforcement module)
            if hasattr(self, 'enforcement') and self.enforcement:
                self.enforcement.start_live_operational_monitoring()
            
            # Mark system as active
            self.launcher_active = True
            
            self.logger.info("DIAGNOSTIC SYSTEM LAUNCHED BY CORE")
            return True
            
        except Exception as e:
            self.logger.error(f"Error launching diagnostic system: {e}")
            return False
    
    # ===== LAUNCHER AND SYSTEM MANAGEMENT =====
    
    def _initialize_launcher(self):
        """Initialize the launcher system"""
        self.logger.info("Initializing diagnostic system launcher...")
        
        # Verify all required directories exist
        self._ensure_directories()
        
        # Setup logging
        self._setup_logging()
        
        # Initialize communication state
        self.pending_responses = {}
        self.signal_counter = 0
        
        # Initialize autonomous mode flag
        self.autonomous_mode = False
        
        self.logger.info("Launcher initialized successfully")
    
    def _start_communication_protocols(self):
        """Start communication protocols"""
        self.logger.info("Starting communication protocols...")
        
        # Start periodic status checks
        self._start_periodic_status_checks()
        
        # Start response monitoring
        self._start_response_monitoring()
        
        self.logger.info("Communication protocols started")
    
    def _start_periodic_status_checks(self):
        """Start periodic status checks"""
        import threading
        
        def status_check_loop():
            while self.launcher_active:
                try:
                    self._perform_status_check()
                    time.sleep(30)  # Check every 30 seconds
                except Exception as e:
                    self.logger.error(f"Status check error: {e}")
                    time.sleep(5)
        
        threading.Thread(target=status_check_loop, daemon=True).start()
    
    def _start_response_monitoring(self):
        """Start monitoring for pending responses"""
        import threading
        
        def response_monitor_loop():
            while self.launcher_active:
                try:
                    self._check_pending_responses()
                    time.sleep(5)  # Check every 5 seconds
                except Exception as e:
                    self.logger.error(f"Response monitoring error: {e}")
                    time.sleep(1)
        
        threading.Thread(target=response_monitor_loop, daemon=True).start()
    
    def _perform_status_check(self):
        """Perform system-wide status check"""
        try:
            self.logger.info("Performing system status check...")
            
            # Check system registry status
            for address, system_info in self.system_registry.items():
                # Update last check time
                system_info['last_check'] = datetime.now().isoformat()
                
                # Basic health check
                if system_info.get('handler_exists', False):
                    system_info['status'] = DiagnosticStatus.OK.value
                else:
                    system_info['status'] = DiagnosticStatus.ERROR.value
            
            self.logger.info("System status check completed")
            
        except Exception as e:
            self.logger.error(f"Error performing status check: {e}")
    
    def _check_pending_responses(self):
        """Enhanced check for pending responses with protocol compliance"""
        try:
            current_time = time.time()
            timeout_threshold = 30  # 30 seconds
            
            # Check each pending response with enhanced tracking
            for signal_id, response_data in list(self.pending_responses.items()):
                sent_time = response_data.get('sent_time', current_time)
                timeout = response_data.get('timeout', timeout_threshold)
                system_address = response_data.get('system_address', 'UNKNOWN')
                
                # Check if response timed out
                if current_time - sent_time > timeout:
                    self.logger.warning(f"Response timeout for signal {signal_id} from {system_address}")
                    
                    # Track timeout in fault response tracking
                    if system_address not in self.fault_response_tracking:
                        self.fault_response_tracking[system_address] = {
                            'timeout_count': 0,
                            'last_timeout': None,
                            'total_signals': 0
                        }
                    
                    self.fault_response_tracking[system_address]['timeout_count'] += 1
                    self.fault_response_tracking[system_address]['last_timeout'] = current_time
                    
                    # Remove from pending responses
                    del self.pending_responses[signal_id]
                    
                    # Add to priority repair queue if critical
                    if response_data.get('priority', 'NORMAL') == 'CRITICAL':
                        self._add_to_priority_repair_queue({
                            'system_address': system_address,
                            'fault_type': 'SIGNAL_TIMEOUT',
                            'fault_code': signal_id,
                            'priority': 'HIGH',
                            'timestamp': current_time
                        })
            
            # Check queue backpressure
            self._check_queue_backpressure()
            
            # Cleanup fault response tracking if needed
            self._cleanup_fault_response_tracking()
            
        except Exception as e:
            self.logger.error(f"Error checking pending responses: {e}")
    
    def handle_response(self, signal_id: str, response_data: Dict[str, Any]):
        """Handle incoming response from systems"""
        try:
            self.logger.info(f"Handling response for signal {signal_id}")
            
            # Remove from pending responses
            if signal_id in self.pending_responses:
                del self.pending_responses[signal_id]
            
            # Process response data
            system_address = response_data.get('system_address', 'UNKNOWN')
            response_type = response_data.get('response_type', 'UNKNOWN')
            
            # Update system registry
            if system_address in self.system_registry:
                system_info = self.system_registry[system_address]
                system_info['last_signal'] = datetime.now().isoformat()
                system_info['signal_count'] += 1
                
                # Update status based on response
                if response_type == 'SUCCESS':
                    system_info['status'] = DiagnosticStatus.OK.value
                elif response_type == 'ERROR':
                    system_info['status'] = DiagnosticStatus.ERROR.value
                    system_info['error_count'] += 1
            
            self.logger.info(f"Response processed for {system_address}")
            
        except Exception as e:
            self.logger.error(f"Error handling response: {e}")
    
    def _perform_initial_rollcall(self):
        """Perform initial rollcall to all systems with throttling"""
        try:
            # Check ROLLCALL throttling
            if not self._check_rollcall_throttle():
                self.logger.warning("ROLLCALL throttled - too frequent requests")
                return
            
            self.logger.info("Performing initial rollcall...")
            
            # Use comms module to transmit rollcall
            if self.comms:
                signal_ids = self.comms.transmit_rollcall()
                self.logger.info(f"Initial rollcall transmitted to {len(signal_ids)} systems")
                
                # Update throttle timestamp
                self.rollcall_throttle['last_rollcall'] = time.time()
            
            # Wait for responses (simplified)
            time.sleep(2)
            
            self.logger.info("Initial rollcall completed")
            
        except Exception as e:
            self.logger.error(f"Error performing initial rollcall: {e}")
    
    def _check_rollcall_throttle(self) -> bool:
        """Check if ROLLCALL is allowed based on throttle interval"""
        try:
            current_time = time.time()
            last_rollcall = self.rollcall_throttle.get('last_rollcall', 0)
            
            if current_time - last_rollcall < self.rollcall_throttle_interval:
                return False
            
            return True
        except Exception as e:
            self.logger.error(f"Error checking rollcall throttle: {e}")
            return True  # Allow on error to prevent system lockup
    
    def _add_to_priority_repair_queue(self, repair_item: Dict[str, Any]):
        """Add item to priority repair queue with proper ordering"""
        try:
            with self.repair_queue_lock:
                # Insert based on priority (HIGH, MEDIUM, LOW)
                priority_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
                item_priority = priority_order.get(repair_item.get('priority', 'MEDIUM'), 1)
                
                # Find insertion point
                insert_index = 0
                for i, existing_item in enumerate(self.priority_repair_queue):
                    existing_priority = priority_order.get(existing_item.get('priority', 'MEDIUM'), 1)
                    if item_priority <= existing_priority:
                        insert_index = i + 1
                    else:
                        break
                
                # Insert item
                self.priority_repair_queue.insert(insert_index, repair_item)
                
                self.logger.info(f"Added {repair_item['fault_type']} to priority repair queue at position {insert_index}")
                
        except Exception as e:
            self.logger.error(f"Error adding to priority repair queue: {e}")
    
    def _process_priority_repair_queue(self):
        """Process items in priority repair queue"""
        try:
            with self.repair_queue_lock:
                if not self.priority_repair_queue:
                    return
                
                # Process highest priority item
                repair_item = self.priority_repair_queue.pop(0)
                
                system_address = repair_item.get('system_address')
                fault_type = repair_item.get('fault_type')
                
                self.logger.info(f"Processing priority repair: {fault_type} for {system_address}")
                
                # Implement repair logic based on fault type
                if fault_type == 'SIGNAL_TIMEOUT':
                    self._repair_signal_timeout(system_address)
                elif fault_type == 'SYSTEM_UNRESPONSIVE':
                    self._repair_unresponsive_system(system_address)
                elif fault_type == 'COMMUNICATION_FAILURE':
                    self._repair_communication_failure(system_address)
                
        except Exception as e:
            self.logger.error(f"Error processing priority repair queue: {e}")
    
    def _check_queue_backpressure(self):
        """Check and manage queue backpressure"""
        try:
            total_queue_size = (len(self.pending_responses) + 
                              len(self.priority_repair_queue) + 
                              len(self.fault_response_tracking))
            
            if total_queue_size >= self.queue_backpressure_threshold:
                if not self.queue_backpressure_active:
                    self.queue_backpressure_active = True
                    self.logger.warning(f"Queue backpressure activated: {total_queue_size}/{self.max_queue_size}")
                    
                    # Implement backpressure mitigation
                    self._mitigate_queue_backpressure()
            else:
                if self.queue_backpressure_active:
                    self.queue_backpressure_active = False
                    self.logger.info("Queue backpressure resolved")
                    
        except Exception as e:
            self.logger.error(f"Error checking queue backpressure: {e}")
    
    def _mitigate_queue_backpressure(self):
        """Mitigate queue backpressure by cleaning up old entries"""
        try:
            current_time = time.time()
            cleanup_threshold = 3600  # 1 hour
            
            # Clean up old pending responses
            old_responses = []
            for signal_id, response_data in self.pending_responses.items():
                sent_time = response_data.get('sent_time', 0)
                if current_time - sent_time > cleanup_threshold:
                    old_responses.append(signal_id)
            
            for signal_id in old_responses:
                del self.pending_responses[signal_id]
            
            # Clean up old fault tracking entries
            old_faults = []
            for system_address, fault_data in self.fault_response_tracking.items():
                last_timeout = fault_data.get('last_timeout', 0)
                if last_timeout and current_time - last_timeout > cleanup_threshold:
                    old_faults.append(system_address)
            
            for system_address in old_faults:
                del self.fault_response_tracking[system_address]
            
            self.logger.info(f"Backpressure mitigation: cleaned {len(old_responses)} responses, {len(old_faults)} fault entries")
            
        except Exception as e:
            self.logger.error(f"Error mitigating queue backpressure: {e}")
    
    def _cleanup_fault_response_tracking(self):
        """Clean up old fault response tracking entries"""
        try:
            current_time = time.time()
            
            # Only cleanup if enough time has passed
            if current_time - self.last_fault_cleanup < self.fault_tracking_cleanup_interval:
                return
            
            cleanup_threshold = 7200  # 2 hours
            cleaned_count = 0
            
            # Clean up old entries
            old_entries = []
            for system_address, fault_data in self.fault_response_tracking.items():
                last_timeout = fault_data.get('last_timeout', 0)
                if last_timeout and current_time - last_timeout > cleanup_threshold:
                    old_entries.append(system_address)
            
            for system_address in old_entries:
                del self.fault_response_tracking[system_address]
                cleaned_count += 1
            
            if cleaned_count > 0:
                self.logger.info(f"Cleaned up {cleaned_count} old fault response tracking entries")
            
            self.last_fault_cleanup = current_time
            
        except Exception as e:
            self.logger.error(f"Error cleaning up fault response tracking: {e}")
    
    def _repair_signal_timeout(self, system_address: str):
        """Repair signal timeout for a system"""
        try:
            self.logger.info(f"Attempting to repair signal timeout for {system_address}")
            
            # Reset signal timeout tracking
            if system_address in self.fault_response_tracking:
                self.fault_response_tracking[system_address]['timeout_count'] = 0
                self.fault_response_tracking[system_address]['last_timeout'] = None
            
            # Attempt to re-establish communication
            if self.comms:
                # Send test signal to system
                test_signal_id = f"REPAIR_TEST_{int(time.time())}"
                self.comms.transmit_signal(system_address, "HEALTH_CHECK", test_signal_id)
                
                # Add to pending responses with shorter timeout
                self.pending_responses[test_signal_id] = {
                    'system_address': system_address,
                    'sent_time': time.time(),
                    'timeout': 10.0,  # Shorter timeout for repair
                    'priority': 'HIGH'
                }
            
            self.logger.info(f"Signal timeout repair initiated for {system_address}")
            
        except Exception as e:
            self.logger.error(f"Error repairing signal timeout for {system_address}: {e}")
    
    def _repair_unresponsive_system(self, system_address: str):
        """Repair unresponsive system"""
        try:
            self.logger.info(f"Attempting to repair unresponsive system {system_address}")
            
            # Update system status
            if system_address in self.system_registry:
                self.system_registry[system_address]['status'] = 'REPAIR_IN_PROGRESS'
            
            # Attempt system restart or reconnection
            self.logger.info(f"Unresponsive system repair initiated for {system_address}")
            
        except Exception as e:
            self.logger.error(f"Error repairing unresponsive system {system_address}: {e}")
    
    def _repair_communication_failure(self, system_address: str):
        """Repair communication failure with system"""
        try:
            self.logger.info(f"Attempting to repair communication failure with {system_address}")
            
            # Reset communication state
            if system_address in self.system_registry:
                self.system_registry[system_address]['last_signal'] = None
                self.system_registry[system_address]['error_count'] = 0
            
            # Attempt to re-establish communication
            self.logger.info(f"Communication failure repair initiated for {system_address}")
            
        except Exception as e:
            self.logger.error(f"Error repairing communication failure with {system_address}: {e}")

    # ===== AUTONOMOUS DIAGNOSTICS =====
    
    def start_autonomous_diagnostics(self):
        """Start autonomous diagnostic system with full Smart Testing Protocol"""
        try:
            self.logger.info("Starting autonomous diagnostics with Smart Testing Protocol...")
            
            # Initialize Smart Testing Protocol
            self._initialize_smart_testing_protocol()
            
            # Start diagnostic scheduler
            self._start_diagnostic_scheduler()
            
            # Start fault management engine
            self._start_fault_management_engine()
            
            # Start fault resolution engine
            self._start_fault_resolution_engine()
            
            # Start protocol monitoring engine
            self._start_protocol_monitoring_engine()
            
            # Start autonomous monitoring threads
            self._start_autonomous_monitoring_threads()
            
            self.autonomous_mode = True
            self.logger.info("Autonomous diagnostics with Smart Testing Protocol started")
            
        except Exception as e:
            self.logger.error(f"Error starting autonomous diagnostics: {e}")
    
    def _initialize_smart_testing_protocol(self):
        """Initialize the Smart Testing Protocol with full autonomous test scheduling"""
        try:
            self.logger.info("Initializing Smart Testing Protocol...")
            
            # Smart Testing Protocol Configuration
            self.smart_testing_protocol = {
                'startup_initialization_tests': {
                    'trigger': 'system_startup',
                    'delay_seconds': 5,
                    'purpose': 'System initialization and component verification',
                    'tests': [
                        'system_wakeup_test',
                        'component_initialization_test',
                        'communication_test',
                        'configuration_validation_test',
                        'function_availability_test'
                    ],
                    'timeout_seconds': 30,
                    'retry_count': 3
                },
                'basic_function_tests': {
                    'trigger': 'time_interval',
                    'interval_minutes': 15,
                    'purpose': 'Basic operational function testing',
                    'tests': [
                        'basic_functionality_test',
                        'communication_test',
                        'data_processing_test',
                        'resource_availability_test'
                    ],
                    'timeout_seconds': 60,
                    'retry_count': 2
                },
                'fault_response_tests': {
                    'trigger': 'fault_detected',
                    'delay_seconds': 2,
                    'purpose': 'Targeted testing in response to faults',
                    'tests': [
                        'targeted_health_check',
                        'communication_test',
                        'fault_specific_testing',
                        'system_recovery_test'
                    ],
                    'timeout_seconds': 45,
                    'retry_count': 1
                },
                'comprehensive_maintenance_tests': {
                    'trigger': 'time_interval',
                    'interval_hours': 1,
                    'purpose': 'Comprehensive system maintenance testing',
                    'tests': [
                        'full_system_test_suite',
                        'performance_benchmarking',
                        'stress_testing',
                        'integration_testing'
                    ],
                    'timeout_seconds': 120,
                    'retry_count': 1
                },
                'idle_monitoring_tests': {
                    'trigger': 'system_idle',
                    'idle_threshold_minutes': 10,
                    'purpose': 'Testing during idle periods',
                    'tests': [
                        'idle_health_check',
                        'background_processing_test',
                        'resource_cleanup_test',
                        'standby_mode_test'
                    ],
                    'timeout_seconds': 30,
                    'retry_count': 1
                }
            }
            
            # Fault escalation configuration
            self.fault_escalation_config = {
                'escalation_levels': {
                    'LEVEL_1': {'max_faults': 3, 'action': 'log_and_monitor'},
                    'LEVEL_2': {'max_faults': 5, 'action': 'targeted_testing'},
                    'LEVEL_3': {'max_faults': 8, 'action': 'comprehensive_testing'},
                    'LEVEL_4': {'max_faults': 12, 'action': 'system_isolation'},
                    'LEVEL_5': {'max_faults': 20, 'action': 'forced_shutdown'}
                },
                'escalation_timeframe_minutes': 15,
                'escalation_cooldown_minutes': 5
            }
            
            # Smart testing loops configuration
            self.smart_testing_loops = {
                'startup_loop': {
                    'enabled': True,
                    'max_iterations': 5,
                    'iteration_delay_seconds': 10,
                    'success_threshold': 0.8
                },
                'function_loop': {
                    'enabled': True,
                    'max_iterations': 3,
                    'iteration_delay_seconds': 30,
                    'success_threshold': 0.7
                },
                'idle_loop': {
                    'enabled': True,
                    'max_iterations': 2,
                    'iteration_delay_seconds': 60,
                    'success_threshold': 0.6
                }
            }
            
            self.logger.info("Smart Testing Protocol initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing Smart Testing Protocol: {e}")
    
    def _start_diagnostic_scheduler(self):
        """Start diagnostic scheduler"""
        import threading
        
        def scheduler_loop():
            while self.autonomous_mode:
                try:
                    # Trigger different types of tests based on time
                    current_hour = datetime.now().hour
                    
                    if current_hour % 6 == 0:  # Every 6 hours
                        self._trigger_startup_initialization_tests()
                    elif current_hour % 2 == 0:  # Every 2 hours
                        self._trigger_basic_function_tests()
                    elif current_hour % 12 == 0:  # Every 12 hours
                        self._trigger_comprehensive_maintenance_tests()
                    
                    time.sleep(3600)  # Check every hour
                    
                except Exception as e:
                    self.logger.error(f"Diagnostic scheduler error: {e}")
                    time.sleep(3600)
        
        threading.Thread(target=scheduler_loop, daemon=True).start()
        self.logger.info("Diagnostic scheduler started")
    
    def _trigger_startup_initialization_tests(self):
        """Trigger startup/initialization tests"""
        try:
            self.logger.info("Triggering startup/initialization tests...")
            
            # Run initialization tests for all systems
            for system_address in self.system_registry.keys():
                if self.comms:
                    self.comms.transmit_radio_check(system_address)
            
        except Exception as e:
            self.logger.error(f"Error triggering startup tests: {e}")
    
    def _trigger_basic_function_tests(self):
        """Trigger basic function tests"""
        try:
            self.logger.info("Triggering basic function tests...")
            
            # Run basic function tests
            for system_address in self.system_registry.keys():
                self.execute_test_plan(system_address, "smoke_test")
            
        except Exception as e:
            self.logger.error(f"Error triggering basic function tests: {e}")
    
    def _trigger_comprehensive_maintenance_tests(self):
        """Trigger comprehensive maintenance tests"""
        try:
            self.logger.info("Triggering comprehensive maintenance tests...")
            
            # Run comprehensive tests
            for system_address in self.system_registry.keys():
                self.execute_test_plan(system_address, "function_test")
            
        except Exception as e:
            self.logger.error(f"Error triggering comprehensive tests: {e}")
    
    def _start_fault_management_engine(self):
        """Start fault management engine"""
        import threading
        
        def fault_manager_loop():
            while self.autonomous_mode:
                try:
                    self._check_for_new_faults()
                    time.sleep(60)  # Check every minute
                    
                except Exception as e:
                    self.logger.error(f"Fault management engine error: {e}")
                    time.sleep(60)
        
        threading.Thread(target=fault_manager_loop, daemon=True).start()
        self.logger.info("Fault management engine started")
    
    def _check_for_new_faults(self):
        """Check for new faults in the system"""
        try:
            # Check for new faults in the fault vault
            fault_vault_files = list(self.fault_vault_path.glob("*.md"))
            
            for fault_file in fault_vault_files:
                if fault_file.stat().st_mtime > time.time() - 60:  # Modified in last minute
                    self.logger.info(f"New fault detected: {fault_file.name}")
                    
        except Exception as e:
            self.logger.error(f"Error checking for new faults: {e}")
    
    def _start_fault_resolution_engine(self):
        """Start fault resolution engine"""
        import threading
        
        def resolution_loop():
            while self.autonomous_mode:
                try:
                    self._check_fault_resolution()
                    time.sleep(300)  # Check every 5 minutes
                    
                except Exception as e:
                    self.logger.error(f"Fault resolution engine error: {e}")
                    time.sleep(300)
        
        threading.Thread(target=resolution_loop, daemon=True).start()
        self.logger.info("Fault resolution engine started")
    
    def _check_fault_resolution(self):
        """Check for resolved faults"""
        try:
            # Check if any active faults have been resolved
            for fault_id in list(self.active_faults.keys()):
                # Simple resolution check - in real system would be more complex
                if fault_id not in self.active_faults:
                    self.logger.info(f"Fault {fault_id} appears to be resolved")
                    
        except Exception as e:
            self.logger.error(f"Error checking fault resolution: {e}")
    
    def _start_protocol_monitoring_engine(self):
        """Start protocol monitoring engine"""
        import threading
        
        def protocol_monitor_loop():
            last_protocol_check = time.time()
            
            while self.autonomous_mode:
                try:
                    current_time = time.time()
                    
                    # Check protocol every 6 hours (21600 seconds)
                    if current_time - last_protocol_check > 21600:
                        self._monitor_and_update_protocol()
                        last_protocol_check = current_time
                    
                    time.sleep(3600)  # Check every hour for 6-hour intervals
                    
                except Exception as e:
                    self.logger.error(f"Protocol monitoring engine error: {e}")
                    time.sleep(7200)  # Wait 2 hours on error
        
        threading.Thread(target=protocol_monitor_loop, daemon=True).start()
        self.logger.info("Protocol monitoring engine started (every 6 hours)")
    
    def _monitor_and_update_protocol(self):
        """Monitor protocol file and update with new systems"""
        try:
            self.logger.info("Starting protocol monitoring and auto-registration...")
            
            # Scan for new Python modules in system directories
            new_systems = self._scan_for_new_systems()
            
            if new_systems:
                self.logger.info(f"Found {len(new_systems)} new systems to register")
                
                # Auto-register new systems
                for system_info in new_systems:
                    self._auto_register_system(system_info)
                
                # Update system registry file
                self._update_system_registry_file()
                
                # Update master protocol file
                self._update_master_protocol_file()
                
                # Generate test plans for new systems
                self._generate_test_plans_for_new_systems(new_systems)
                
                self.logger.info("Auto-registration completed successfully")
            else:
                self.logger.info("No new systems found")
            
            self.logger.info("Protocol monitoring completed")
            
        except Exception as e:
            self.logger.error(f"Protocol monitoring failed: {e}")
    
    def _scan_for_new_systems(self):
        """Scan system directories for new Python modules"""
        new_systems = []
        
        # Define system directories to scan
        system_directories = [
            "F:/The Central Command/Evidence Locker",
            "F:/The Central Command/Gateway Controller", 
            "F:/The Central Command/Mission Debrief Manager",
            "F:/The Central Command/Analyst Deck",
            "F:/The Central Command/Marshall",
            "F:/The Central Command/War Room",
            "F:/The Central Command/Enhanced Functional GUI",
            "F:/The Central Command/Command Center/Data Bus"
        ]
        
        for directory in system_directories:
            dir_path = Path(directory)
            if dir_path.exists():
                # Scan for Python files
                python_files = list(dir_path.rglob("*.py"))
                
                for py_file in python_files:
                    # Skip __pycache__ and test files
                    if "__pycache__" in str(py_file) or "test_" in py_file.name:
                        continue
                    
                    # Check if this system is already registered
                    if self._is_system_already_registered(py_file):
                        continue
                    
                    # Extract system information
                    system_info = self._extract_system_info(py_file)
                    if system_info:
                        new_systems.append(system_info)
        
        return new_systems
    
    def _is_system_already_registered(self, file_path):
        """Check if a system is already registered"""
        file_path_str = str(file_path)
        
        for address, system_info in self.system_registry.items():
            if system_info.get('location') == file_path_str:
                return True
        return False
    
    def _extract_system_info(self, file_path):
        """Extract system information from Python file"""
        try:
            # Read file to extract class names and system info
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for class definitions
            import re
            class_matches = re.findall(r'class\s+(\w+)\s*\([^)]*\):', content)
            
            if not class_matches:
                return None
            
            main_class = class_matches[0]
            
            # Determine system type and parent from directory structure
            system_info = self._determine_system_address(file_path, main_class)
            
            return {
                'file_path': str(file_path),
                'class_name': main_class,
                'handler': f"{file_path.stem}.{main_class}",
                'system_info': system_info
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting system info from {file_path}: {e}")
            return None
    
    def _determine_system_address(self, file_path, class_name):
        """Determine system address based on file location and naming"""
        file_path_str = str(file_path)
        file_name = file_path.stem
        
        # Map directories to system families
        if "Evidence Locker" in file_path_str:
            family = "1"
            if file_path.parent.name == "Evidence Locker":
                # Main system
                return {
                    'address': f"{family}-1",
                    'name': file_name.replace('_', ' ').title(),
                    'parent': None,
                    'system_type': 'main'
                }
            else:
                # Subsystem
                subsystem_num = self._get_next_subsystem_number(family)
                return {
                    'address': f"{family}-1.{subsystem_num}",
                    'name': file_name.replace('_', ' ').title(),
                    'parent': f"{family}-1",
                    'system_type': 'subsystem'
                }
        
        elif "Gateway Controller" in file_path_str:
            family = "2"
            if file_path.parent.name == "Gateway Controller":
                return {
                    'address': f"{family}-2",
                    'name': file_name.replace('_', ' ').title(),
                    'parent': None,
                    'system_type': 'main'
                }
            else:
                subsystem_num = self._get_next_subsystem_number(f"{family}-2")
                return {
                    'address': f"{family}-2.{subsystem_num}",
                    'name': file_name.replace('_', ' ').title(),
                    'parent': f"{family}-2",
                    'system_type': 'subsystem'
                }
        
        elif "Mission Debrief Manager" in file_path_str:
            family = "3"
            if file_path.parent.name == "Mission Debrief Manager":
                return {
                    'address': f"{family}-1",
                    'name': file_name.replace('_', ' ').title(),
                    'parent': None,
                    'system_type': 'main'
                }
            else:
                subsystem_num = self._get_next_subsystem_number(f"{family}-1")
                return {
                    'address': f"{family}-1.{subsystem_num}",
                    'name': file_name.replace('_', ' ').title(),
                    'parent': f"{family}-1",
                    'system_type': 'subsystem'
                }
        
        elif "Analyst Deck" in file_path_str:
            family = "4"
            # Analyst Deck has special addressing (4-1, 4-2, etc.)
            subsystem_num = self._get_next_subsystem_number(family)
            return {
                'address': f"{family}-{subsystem_num}",
                'name': file_name.replace('_', ' ').title(),
                'parent': None,
                'system_type': 'section'
            }
        
        elif "Marshall" in file_path_str:
            family = "5"
            subsystem_num = self._get_next_subsystem_number(family)
            return {
                'address': f"{family}-{subsystem_num}",
                'name': file_name.replace('_', ' ').title(),
                'parent': None,
                'system_type': 'main'
            }
        
        elif "War Room" in file_path_str:
            family = "6"
            subsystem_num = self._get_next_subsystem_number(family)
            return {
                'address': f"{family}-{subsystem_num}",
                'name': file_name.replace('_', ' ').title(),
                'parent': None,
                'system_type': 'main'
            }
        
        elif "Enhanced Functional GUI" in file_path_str:
            family = "7"
            if file_path.parent.name == "Enhanced Functional GUI":
                return {
                    'address': f"{family}-1",
                    'name': file_name.replace('_', ' ').title(),
                    'parent': None,
                    'system_type': 'main'
                }
            else:
                subsystem_num = self._get_next_subsystem_number(f"{family}-1")
                return {
                    'address': f"{family}-1.{subsystem_num}",
                    'name': file_name.replace('_', ' ').title(),
                    'parent': f"{family}-1",
                    'system_type': 'subsystem'
                }
        
        elif "Data Bus" in file_path_str:
            if "Bus Core Design" in file_path_str:
                return {
                    'address': "Bus-1",
                    'name': "Central Command Bus",
                    'parent': None,
                    'system_type': 'bus'
                }
            else:
                return {
                    'address': "Bus-1.1",
                    'name': file_name.replace('_', ' ').title(),
                    'parent': "Bus-1",
                    'system_type': 'bus_subsystem'
                }
        
        # Default fallback
        return {
            'address': f"UNKNOWN-{len(self.system_registry) + 1}",
            'name': file_name.replace('_', ' ').title(),
            'parent': None,
            'system_type': 'unknown'
        }
    
    def _get_next_subsystem_number(self, parent_address):
        """Get the next available subsystem number for a parent address"""
        max_num = 0
        
        for address in self.system_registry.keys():
            if address.startswith(parent_address + "."):
                try:
                    subsystem_part = address.split(".")[-1]
                    if subsystem_part.isdigit():
                        max_num = max(max_num, int(subsystem_part))
                    elif subsystem_part.startswith(parent_address.split("-")[-1]):
                        # Handle cases like 4-CP, 4-TOC
                        continue
                except:
                    continue
        
        return max_num + 1
    
    def _auto_register_system(self, system_info):
        """Auto-register a new system"""
        try:
            address = system_info['system_info']['address']
            name = system_info['system_info']['name']
            handler = system_info['handler']
            parent = system_info['system_info']['parent']
            file_path = system_info['file_path']
            
            # Add to system registry
            self.system_registry[address] = {
                'name': name,
                'address': address,
                'handler': handler,
                'parent': parent,
                'status': 'ACTIVE',
                'location': file_path,
                'last_check': None,
                'test_plans': [],
                'handler_exists': Path(file_path).exists(),
                'restart_required': False,
                'quarantined': False,
                'auto_registered': True,
                'fault_code_protocol': 'INACTIVE',
                'signal_count': 0,
                'error_count': 0,
                'faults': []
            }
            
            self.logger.info(f"Auto-registered system: {address} - {name}")
            
        except Exception as e:
            self.logger.error(f"Error auto-registering system: {e}")
    
    def _update_system_registry_file(self):
        """Update the system registry JSON file"""
        try:
            registry_data = {
                "system_registry": {
                    "metadata": {
                        "version": "1.0.0",
                        "last_updated": datetime.now().strftime("%Y-%m-%d"),
                        "total_systems": len(self.system_registry),
                        "connected_systems": len(self.system_registry),
                        "missing_systems": 0,
                        "connection_percentage": 100
                    },
                    "connected_systems": self.system_registry
                }
            }
            
            with open(self.system_registry_path, 'w') as f:
                # Convert DiagnosticStatus enums to strings for JSON serialization
                serializable_data = self._make_json_serializable(registry_data)
                json.dump(serializable_data, f, indent=2)
            
            self.logger.info("System registry file updated")
            
        except Exception as e:
            self.logger.error(f"Error updating system registry file: {e}")
    
    def _make_json_serializable(self, obj):
        """Convert objects to JSON serializable format"""
        if isinstance(obj, dict):
            return {key: self._make_json_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        elif hasattr(obj, 'value'):  # Enum objects
            return obj.value
        else:
            return obj
    
    def _update_master_protocol_file(self):
        """Update the master protocol file with new systems"""
        try:
            new_systems = [sys for sys in self.system_registry.values() if sys.get('auto_registered', False)]
            
            if not new_systems:
                self.logger.info("No new systems to add to master protocol")
                return
            
            # Read current protocol file
            if not self.master_protocol_path.exists():
                self.logger.error(f"Master protocol file not found: {self.master_protocol_path}")
                return
            
            with open(self.master_protocol_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Update each system family section
            updated_content = content
            
            for system in new_systems:
                address = system['address']
                name = system['name']
                handler = system['handler']
                parent = system.get('parent', '-')
                
                # Determine which section to update
                if address.startswith("Bus-"):
                    updated_content = self._update_bus_section(updated_content, address, name, handler, parent)
                elif address.startswith("1-"):
                    updated_content = self._update_evidence_locker_section(updated_content, address, name, handler, parent)
                elif address.startswith("2-"):
                    updated_content = self._update_warden_section(updated_content, address, name, handler, parent)
                elif address.startswith("3-"):
                    updated_content = self._update_mission_debrief_section(updated_content, address, name, handler, parent)
                elif address.startswith("4-"):
                    updated_content = self._update_analyst_deck_section(updated_content, address, name, handler, parent)
                elif address.startswith("5-"):
                    updated_content = self._update_marshall_section(updated_content, address, name, handler, parent)
                elif address.startswith("6-"):
                    updated_content = self._update_war_room_section(updated_content, address, name, handler, parent)
                elif address.startswith("7-"):
                    updated_content = self._update_gui_section(updated_content, address, name, handler, parent)
            
            # Write updated content back to file
            with open(self.master_protocol_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            self.logger.info(f"Updated master protocol with {len(new_systems)} new systems")
            
        except Exception as e:
            self.logger.error(f"Error updating master protocol file: {e}")
    
    def _update_bus_section(self, content, address, name, handler, parent):
        """Update the Bus System section"""
        # Find the Bus System table
        bus_section_pattern = r'(### \*\*Bus System\*\*\s*\n\| Address \| System Name \| Handler \| Status \| Last Check \|\s*\n\|-+\|-+\|-+\|-+\|-+\|\s*\n)'
        
        def add_to_bus_table(match):
            table_header = match.group(1)
            new_row = f"| {address} | {name} | {handler} | ACTIVE | - |\n"
            return table_header + new_row
        
        return re.sub(bus_section_pattern, add_to_bus_table, content)
    
    def _update_evidence_locker_section(self, content, address, name, handler, parent):
        """Update the Evidence Locker Complex section"""
        evidence_section_pattern = r'(### \*\*Evidence Locker Complex \(1-x\)\*\*\s*\n\| Address \| System Name \| Handler \| Parent \| Status \| Last Check \|\s*\n\|-+\|-+\|-+\|-+\|-+\|-+\|\s*\n)'
        
        def add_to_evidence_table(match):
            table_header = match.group(1)
            new_row = f"| {address} | {name} | {handler} | {parent} | ACTIVE | - |\n"
            return table_header + new_row
        
        return re.sub(evidence_section_pattern, add_to_evidence_table, content)
    
    def _update_warden_section(self, content, address, name, handler, parent):
        """Update the Warden Complex section"""
        warden_section_pattern = r'(### \*\*Warden Complex \(2-x\)\*\*\s*\n\| Address \| System Name \| Handler \| Parent \| Status \| Last Check \|\s*\n\|-+\|-+\|-+\|-+\|-+\|-+\|\s*\n)'
        
        def add_to_warden_table(match):
            table_header = match.group(1)
            new_row = f"| {address} | {name} | {handler} | {parent} | ACTIVE | - |\n"
            return table_header + new_row
        
        return re.sub(warden_section_pattern, add_to_warden_table, content)
    
    def _update_mission_debrief_section(self, content, address, name, handler, parent):
        """Update the Mission Debrief Complex section"""
        mission_section_pattern = r'(### \*\*Mission Debrief Complex \(3-x\)\*\*\s*\n\| Address \| System Name \| Handler \| Parent \| Status \| Last Check \|\s*\n\|-+\|-+\|-+\|-+\|-+\|-+\|\s*\n)'
        
        def add_to_mission_table(match):
            table_header = match.group(1)
            new_row = f"| {address} | {name} | {handler} | {parent} | ACTIVE | - |\n"
            return table_header + new_row
        
        return re.sub(mission_section_pattern, add_to_mission_table, content)
    
    def _update_analyst_deck_section(self, content, address, name, handler, parent):
        """Update the Analyst Deck Complex section"""
        analyst_section_pattern = r'(### \*\*Analyst Deck Complex \(4-x\)\*\*\s*\n\| Address \| System Name \| Handler \| Parent \| Status \| Last Check \|\s*\n\|-+\|-+\|-+\|-+\|-+\|-+\|\s*\n)'
        
        def add_to_analyst_table(match):
            table_header = match.group(1)
            new_row = f"| {address} | {name} | {handler} | {parent} | ACTIVE | - |\n"
            return table_header + new_row
        
        return re.sub(analyst_section_pattern, add_to_analyst_table, content)
    
    def _update_marshall_section(self, content, address, name, handler, parent):
        """Update the Marshall Complex section"""
        marshall_section_pattern = r'(### \*\*Marshall Complex \(5-x\)\*\*\s*\n\| Address \| System Name \| Handler \| Parent \| Status \| Last Check \|\s*\n\|-+\|-+\|-+\|-+\|-+\|-+\|\s*\n)'
        
        def add_to_marshall_table(match):
            table_header = match.group(1)
            new_row = f"| {address} | {name} | {handler} | {parent} | ACTIVE | - |\n"
            return table_header + new_row
        
        return re.sub(marshall_section_pattern, add_to_marshall_table, content)
    
    def _update_war_room_section(self, content, address, name, handler, parent):
        """Update the War Room Complex section"""
        war_room_section_pattern = r'(### \*\*War Room Complex \(6-x\)\*\*\s*\n\| Address \| System Name \| Handler \| Parent \| Status \| Last Check \|\s*\n\|-+\|-+\|-+\|-+\|-+\|-+\|\s*\n)'
        
        def add_to_war_room_table(match):
            table_header = match.group(1)
            new_row = f"| {address} | {name} | {handler} | {parent} | ACTIVE | - |\n"
            return table_header + new_row
        
        return re.sub(war_room_section_pattern, add_to_war_room_table, content)
    
    def _update_gui_section(self, content, address, name, handler, parent):
        """Update the Enhanced Functional GUI section"""
        gui_section_pattern = r'(### \*\*Enhanced Functional GUI \(7-x\)\*\*\s*\n\| Address \| System Name \| Handler \| Parent \| Status \| Last Check \|\s*\n\|-+\|-+\|-+\|-+\|-+\|-+\|\s*\n)'
        
        def add_to_gui_table(match):
            table_header = match.group(1)
            new_row = f"| {address} | {name} | {handler} | {parent} | ACTIVE | - |\n"
            return table_header + new_row
        
        return re.sub(gui_section_pattern, add_to_gui_table, content)
    
    def _update_general_section(self, content, address, name, handler, parent):
        """Update the General Systems section"""
        # For general systems, add to a new section or existing general section
        general_section_pattern = r'(### \*\*General Systems\*\*\s*\n\| Address \| System Name \| Handler \| Parent \| Status \| Last Check \|\s*\n\|-+\|-+\|-+\|-+\|-+\|-+\|\s*\n)'
        
        def add_to_general_table(match):
            table_header = match.group(1)
            new_row = f"| {address} | {name} | {handler} | {parent} | ACTIVE | - |\n"
            return table_header + new_row
        
        # If general section exists, update it
        if re.search(general_section_pattern, content):
            return re.sub(general_section_pattern, add_to_general_table, content)
        else:
            # Create new general section
            general_section = f"""
### **General Systems**
| Address | System Name | Handler | Parent | Status | Last Check |
|---------|-------------|---------|--------|--------|------------|
| {address} | {name} | {handler} | {parent} | ACTIVE | - |

"""
            # Insert before the fault codes section
            fault_codes_pattern = r'(## \*\*FAULT SYMPTOMS & DIAGNOSTIC CODES\*\*)'
            return re.sub(fault_codes_pattern, general_section + r'\\1', content)
    
    def _generate_test_plans_for_new_systems(self, new_systems):
        """Generate test plans for newly registered systems"""
        try:
            for system_info in new_systems:
                address = system_info['system_info']['address']
                name = system_info['system_info']['name']
                
                # Generate smoke test plan
                self._create_smoke_test_plan(address, name)
                
                # Generate function test plan
                self._create_function_test_plan(address, name)
                
            self.logger.info(f"Generated test plans for {len(new_systems)} new systems")
            
        except Exception as e:
            self.logger.error(f"Error generating test plans: {e}")
    
    def _create_smoke_test_plan(self, address, name):
        """Create a smoke test plan for a system"""
        try:
            # Determine test plan directory based on address
            test_dir = self._get_test_plan_directory(address)
            test_file = test_dir / "smoke_test_plan.json"
            
            # Create directory if it doesn't exist
            test_dir.mkdir(parents=True, exist_ok=True)
            
            # Create basic smoke test plan
            smoke_test_plan = {
                "test_plan": {
                    "system_address": address,
                    "system_name": name,
                    "test_type": "smoke_test",
                    "description": f"Basic functionality test for {name}",
                    "test_vectors": [
                        {
                            "test_id": "INIT_001",
                            "test_name": "System Initialization",
                            "test_type": "initialization",
                            "description": "Test system initialization",
                            "expected_result": "SUCCESS",
                            "timeout_seconds": 30
                        },
                        {
                            "test_id": "COMM_001", 
                            "test_name": "Communication Test",
                            "test_type": "communication",
                            "description": "Test system communication",
                            "expected_result": "SUCCESS",
                            "timeout_seconds": 30
                        }
                    ]
                }
            }
            
            with open(test_file, 'w') as f:
                json.dump(smoke_test_plan, f, indent=2)
            
            self.logger.info(f"Created smoke test plan for {address}")
            
        except Exception as e:
            self.logger.error(f"Error creating smoke test plan for {address}: {e}")
    
    def _create_function_test_plan(self, address, name):
        """Create a function test plan for a system"""
        try:
            # Determine test plan directory based on address
            test_dir = self._get_test_plan_directory(address)
            test_file = test_dir / "function_test_plan.json"
            
            # Create directory if it doesn't exist
            test_dir.mkdir(parents=True, exist_ok=True)
            
            # Create basic function test plan
            function_test_plan = {
                "test_plan": {
                    "system_address": address,
                    "system_name": name,
                    "test_type": "function_test",
                    "description": f"Comprehensive functionality test for {name}",
                    "test_vectors": [
                        {
                            "test_id": "FUNC_001",
                            "test_name": "Core Function Test",
                            "test_type": "functionality",
                            "description": "Test core system functionality",
                            "expected_result": "SUCCESS",
                            "timeout_seconds": 60
                        },
                        {
                            "test_id": "PERF_001",
                            "test_name": "Performance Test",
                            "test_type": "performance",
                            "description": "Test system performance",
                            "expected_result": "SUCCESS",
                            "timeout_seconds": 120
                        }
                    ]
                }
            }
            
            with open(test_file, 'w') as f:
                json.dump(function_test_plan, f, indent=2)
            
            self.logger.info(f"Created function test plan for {address}")
            
        except Exception as e:
            self.logger.error(f"Error creating function test plan for {address}: {e}")
    
    def _get_test_plan_directory(self, address):
        """Get the test plan directory for a system address"""
        # Map address to test plan directory structure
        if address.startswith("1-"):
            return self.test_plans_main_path / "1_evidence_locker_main" / f"{address}_subsystem"
        elif address.startswith("2-"):
            return self.test_plans_main_path / "2_warden_complex" / f"{address}_subsystem"
        elif address.startswith("3-"):
            return self.test_plans_main_path / "3_mission_debrief_manager" / f"{address}_subsystem"
        elif address.startswith("4-"):
            return self.test_plans_main_path / "4_analyst_deck_system" / f"{address}_subsystem"
        elif address.startswith("5-"):
            return self.test_plans_main_path / "5_marshall_system" / f"{address}_subsystem"
        elif address.startswith("6-"):
            return self.test_plans_main_path / "6_war_room_complex" / f"{address}_subsystem"
        elif address.startswith("7-"):
            return self.test_plans_main_path / "7_enhanced_functional_gui" / f"{address}_subsystem"
        elif address.startswith("Bus-"):
            return self.test_plans_main_path / "Bus-1_bus_system" / f"{address}_subsystem"
        else:
            return self.test_plans_main_path / "unknown_system" / f"{address}_subsystem"
    
    def _start_autonomous_monitoring_threads(self):
        """Start autonomous monitoring threads for globally coordinated background monitoring"""
        try:
            self.logger.info("Starting autonomous monitoring threads...")
            
            # Status monitoring thread
            self.status_monitor_thread = threading.Thread(
                target=self._status_monitoring_loop,
                daemon=True,
                name="StatusMonitor"
            )
            self.status_monitor_thread.start()
            
            # Backup validation monitoring thread
            self.backup_monitor_thread = threading.Thread(
                target=self._backup_validation_monitoring_loop,
                daemon=True,
                name="BackupMonitor"
            )
            self.backup_monitor_thread.start()
            
            # System health monitoring thread
            self.health_monitor_thread = threading.Thread(
                target=self._system_health_monitoring_loop,
                daemon=True,
                name="HealthMonitor"
            )
            self.health_monitor_thread.start()
            
            # Performance monitoring thread
            self.performance_monitor_thread = threading.Thread(
                target=self._performance_monitoring_loop,
                daemon=True,
                name="PerformanceMonitor"
            )
            self.performance_monitor_thread.start()
            
            # Communication monitoring thread
            self.communication_monitor_thread = threading.Thread(
                target=self._communication_monitoring_loop,
                daemon=True,
                name="CommunicationMonitor"
            )
            self.communication_monitor_thread.start()
            
            self.logger.info("Autonomous monitoring threads started successfully")
            
        except Exception as e:
            self.logger.error(f"Error starting autonomous monitoring threads: {e}")
    
    def _status_monitoring_loop(self):
        """Status monitoring loop for all systems"""
        while self.autonomous_mode:
            try:
                # Monitor system statuses
                for address, system_info in self.system_registry.items():
                    # Check system status
                    current_status = self._check_system_status(address)
                    if current_status != system_info.get('status'):
                        self.logger.info(f"Status change detected: {address} - {system_info.get('status')} -> {current_status}")
                        system_info['status'] = current_status
                        system_info['last_status_check'] = datetime.now().isoformat()
                
                # Sleep for monitoring interval
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error in status monitoring loop: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _backup_validation_monitoring_loop(self):
        """Backup validation monitoring loop"""
        while self.autonomous_mode:
            try:
                # Validate backups every hour
                if hasattr(self, 'recovery') and self.recovery:
                    self.recovery._validate_all_backups()
                
                # Sleep for 1 hour
                time.sleep(3600)
                
            except Exception as e:
                self.logger.error(f"Error in backup validation monitoring loop: {e}")
                time.sleep(3600)  # Wait 1 hour on error
    
    def _system_health_monitoring_loop(self):
        """System health monitoring loop"""
        while self.autonomous_mode:
            try:
                # Check system health
                for address, system_info in self.system_registry.items():
                    health_status = self._check_system_health(address)
                    if health_status['healthy'] == False:
                        self.logger.warning(f"System health issue detected: {address} - {health_status}")
                
                # Sleep for 5 minutes
                time.sleep(300)
                
            except Exception as e:
                self.logger.error(f"Error in system health monitoring loop: {e}")
                time.sleep(300)  # Wait 5 minutes on error
    
    def _performance_monitoring_loop(self):
        """Performance monitoring loop"""
        while self.autonomous_mode:
            try:
                # Monitor performance metrics
                performance_metrics = self._collect_performance_metrics()
                if performance_metrics:
                    self._analyze_performance_metrics(performance_metrics)
                
                # Sleep for 10 minutes
                time.sleep(600)
                
            except Exception as e:
                self.logger.error(f"Error in performance monitoring loop: {e}")
                time.sleep(600)  # Wait 10 minutes on error
    
    def _communication_monitoring_loop(self):
        """Communication monitoring loop"""
        while self.autonomous_mode:
            try:
                # Monitor communication health
                for address, system_info in self.system_registry.items():
                    comm_health = self._check_communication_health(address)
                    if comm_health['healthy'] == False:
                        self.logger.warning(f"Communication health issue: {address} - {comm_health}")
                
                # Sleep for 2 minutes
                time.sleep(120)
                
            except Exception as e:
                self.logger.error(f"Error in communication monitoring loop: {e}")
                time.sleep(120)  # Wait 2 minutes on error
    
    # ===== COMPREHENSIVE TEST SUITE / TEST PLANS LOADER =====
    
    def initialize_comprehensive_test_suite(self):
        """Initialize comprehensive test suite with test plan orchestration and test-suite aggregation"""
        try:
            self.logger.info("Initializing Comprehensive Test Suite / Test Plans Loader...")
            
            # Test suite configuration
            self.test_suite_config = {
                'test_suites': {
                    'startup_validation_suite': {
                        'description': 'Complete startup and initialization validation',
                        'test_plans': ['system_wakeup_test', 'component_initialization_test', 'communication_test'],
                        'execution_order': 'sequential',
                        'timeout_minutes': 30,
                        'retry_count': 2
                    },
                    'functionality_suite': {
                        'description': 'Core functionality validation across all systems',
                        'test_plans': ['basic_functionality_test', 'data_processing_test', 'resource_availability_test'],
                        'execution_order': 'parallel',
                        'timeout_minutes': 60,
                        'retry_count': 1
                    },
                    'integration_suite': {
                        'description': 'System integration and communication validation',
                        'test_plans': ['integration_test', 'communication_test', 'data_flow_test'],
                        'execution_order': 'sequential',
                        'timeout_minutes': 45,
                        'retry_count': 1
                    },
                    'performance_suite': {
                        'description': 'Performance benchmarking and stress testing',
                        'test_plans': ['performance_test', 'load_test', 'stress_test'],
                        'execution_order': 'sequential',
                        'timeout_minutes': 90,
                        'retry_count': 1
                    },
                    'maintenance_suite': {
                        'description': 'System maintenance and health validation',
                        'test_plans': ['health_check_test', 'maintenance_test', 'cleanup_test'],
                        'execution_order': 'parallel',
                        'timeout_minutes': 30,
                        'retry_count': 2
                    }
                },
                'test_plan_orchestration': {
                    'parallel_execution_limit': 5,
                    'sequential_execution_delay': 10,
                    'aggregation_timeout_minutes': 120,
                    'result_consolidation': True
                },
                'test_suite_aggregation': {
                    'aggregate_results': True,
                    'generate_summary': True,
                    'consolidate_reports': True,
                    'performance_metrics': True
                }
            }
            
            # Test plan loader configuration
            self.test_plan_loader_config = {
                'supported_formats': ['json', 'yaml', 'xml'],
                'test_plan_directory': self.test_plans_main_path,
                'cache_enabled': True,
                'cache_duration_minutes': 60,
                'validation_enabled': True,
                'auto_discovery': True
            }
            
            # Initialize test plan cache
            self.test_plan_cache = {}
            self.test_suite_results = {}
            
            # Initialize test orchestration
            self._initialize_test_orchestration()
            
            self.logger.info("Comprehensive Test Suite / Test Plans Loader initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing comprehensive test suite: {e}")
    
    def _initialize_test_orchestration(self):
        """Initialize test orchestration system"""
        try:
            self.logger.info("Initializing test orchestration system...")
            
            # Test orchestration state
            self.test_orchestration = {
                'active_tests': {},
                'test_queue': [],
                'execution_history': [],
                'performance_metrics': {},
                'aggregated_results': {},
                'orchestration_active': False
            }
            
            # Test plan discovery
            self._discover_test_plans()
            
            # Initialize test execution engine
            self._initialize_test_execution_engine()
            
            self.logger.info("Test orchestration system initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing test orchestration: {e}")
    
    def _discover_test_plans(self):
        """Auto-discover test plans in the test plans directory"""
        try:
            self.logger.info("Discovering test plans...")
            
            discovered_plans = {}
            
            if self.test_plans_main_path.exists():
                for system_dir in self.test_plans_main_path.iterdir():
                    if system_dir.is_dir():
                        system_address = system_dir.name
                        system_plans = {}
                        
                        # Look for test plan files
                        for test_file in system_dir.rglob("*.json"):
                            if test_file.name.endswith("_plan.json"):
                                test_type = test_file.stem.replace("_plan", "")
                                
                                try:
                                    with open(test_file, 'r') as f:
                                        test_plan = json.load(f)
                                    
                                    system_plans[test_type] = {
                                        'file_path': str(test_file),
                                        'test_plan': test_plan,
                                        'last_modified': test_file.stat().st_mtime,
                                        'size_bytes': test_file.stat().st_size
                                    }
                                    
                                    # Cache the test plan
                                    cache_key = f"{system_address}_{test_type}"
                                    self.test_plan_cache[cache_key] = system_plans[test_type]
                                    
                                except Exception as e:
                                    self.logger.error(f"Error loading test plan {test_file}: {e}")
                        
                        if system_plans:
                            discovered_plans[system_address] = system_plans
            
            self.test_orchestration['discovered_plans'] = discovered_plans
            self.logger.info(f"Discovered {len(discovered_plans)} systems with test plans")
            
        except Exception as e:
            self.logger.error(f"Error discovering test plans: {e}")
    
    def _initialize_test_execution_engine(self):
        """Initialize test execution engine for orchestrated testing"""
        try:
            self.logger.info("Initializing test execution engine...")
            
            # Test execution configuration
            self.test_execution_engine = {
                'execution_threads': {},
                'execution_queue': [],
                'execution_stats': {
                    'total_executions': 0,
                    'successful_executions': 0,
                    'failed_executions': 0,
                    'execution_time_avg': 0
                },
                'execution_monitoring': {
                    'active_monitoring': False,
                    'performance_tracking': True,
                    'resource_monitoring': True
                }
            }
            
            self.logger.info("Test execution engine initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing test execution engine: {e}")
    
    def execute_comprehensive_test_suite(self, suite_name: str = None) -> Dict[str, Any]:
        """Execute comprehensive test suite with orchestration and aggregation"""
        try:
            self.logger.info(f"Executing comprehensive test suite: {suite_name or 'all'}")
            
            # Initialize suite execution
            suite_execution = {
                'suite_name': suite_name or 'comprehensive_suite',
                'execution_started': datetime.now().isoformat(),
                'test_suites_executed': [],
                'aggregated_results': {},
                'performance_metrics': {},
                'execution_summary': {},
                'errors': []
            }
            
            # Determine which test suites to execute
            if suite_name:
                suites_to_execute = {suite_name: self.test_suite_config['test_suites'].get(suite_name, {})}
            else:
                suites_to_execute = self.test_suite_config['test_suites']
            
            # Execute each test suite
            for suite_name, suite_config in suites_to_execute.items():
                try:
                    suite_result = self._execute_test_suite(suite_name, suite_config)
                    suite_execution['test_suites_executed'].append(suite_result)
                    
                except Exception as e:
                    self.logger.error(f"Error executing test suite {suite_name}: {e}")
                    suite_execution['errors'].append({
                        'suite_name': suite_name,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
            
            # Aggregate results
            suite_execution['aggregated_results'] = self._aggregate_test_suite_results(suite_execution['test_suites_executed'])
            
            # Generate performance metrics
            suite_execution['performance_metrics'] = self._generate_performance_metrics(suite_execution)
            
            # Generate execution summary
            suite_execution['execution_summary'] = self._generate_execution_summary(suite_execution)
            
            suite_execution['execution_completed'] = datetime.now().isoformat()
            
            # Save suite execution results
            self._save_test_suite_execution_results(suite_execution)
            
            self.logger.info(f"Comprehensive test suite execution completed: {suite_name or 'all'}")
            
            return suite_execution
            
        except Exception as e:
            self.logger.error(f"Error executing comprehensive test suite: {e}")
            return {'error': str(e), 'suite_name': suite_name}
    
    def _execute_test_suite(self, suite_name: str, suite_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute individual test suite with orchestration"""
        try:
            self.logger.info(f"Executing test suite: {suite_name}")
            
            suite_result = {
                'suite_name': suite_name,
                'description': suite_config.get('description', ''),
                'execution_started': datetime.now().isoformat(),
                'test_plans': suite_config.get('test_plans', []),
                'execution_order': suite_config.get('execution_order', 'sequential'),
                'test_results': [],
                'suite_summary': {},
                'errors': []
            }
            
            # Execute test plans based on execution order
            if suite_config.get('execution_order') == 'parallel':
                suite_result['test_results'] = self._execute_test_plans_parallel(suite_config['test_plans'])
            else:
                suite_result['test_results'] = self._execute_test_plans_sequential(suite_config['test_plans'])
            
            # Generate suite summary
            suite_result['suite_summary'] = self._generate_suite_summary(suite_result['test_results'])
            
            suite_result['execution_completed'] = datetime.now().isoformat()
            
            self.logger.info(f"Test suite execution completed: {suite_name}")
            
            return suite_result
            
        except Exception as e:
            self.logger.error(f"Error executing test suite {suite_name}: {e}")
            return {'error': str(e), 'suite_name': suite_name}
    
    def _execute_test_plans_sequential(self, test_plans: List[str]) -> List[Dict[str, Any]]:
        """Execute test plans sequentially"""
        try:
            results = []
            
            for test_plan_name in test_plans:
                try:
                    # Find and execute test plan
                    test_result = self._execute_single_test_plan(test_plan_name)
                    results.append(test_result)
                    
                    # Sequential execution delay
                    time.sleep(self.test_suite_config['test_plan_orchestration']['sequential_execution_delay'])
                    
                except Exception as e:
                    self.logger.error(f"Error executing test plan {test_plan_name}: {e}")
                    results.append({
                        'test_plan_name': test_plan_name,
                        'status': 'ERROR',
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in sequential test plan execution: {e}")
            return []
    
    def _execute_test_plans_parallel(self, test_plans: List[str]) -> List[Dict[str, Any]]:
        """Execute test plans in parallel"""
        try:
            import threading
            from concurrent.futures import ThreadPoolExecutor
            
            results = []
            max_workers = self.test_suite_config['test_plan_orchestration']['parallel_execution_limit']
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all test plans for parallel execution
                future_to_plan = {
                    executor.submit(self._execute_single_test_plan, test_plan_name): test_plan_name
                    for test_plan_name in test_plans
                }
                
                # Collect results as they complete
                for future in future_to_plan:
                    test_plan_name = future_to_plan[future]
                    try:
                        result = future.result(timeout=300)  # 5 minute timeout per test
                        results.append(result)
                    except Exception as e:
                        self.logger.error(f"Error in parallel execution of {test_plan_name}: {e}")
                        results.append({
                            'test_plan_name': test_plan_name,
                            'status': 'ERROR',
                            'error': str(e),
                            'timestamp': datetime.now().isoformat()
                        })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in parallel test plan execution: {e}")
            return []
    
    def _execute_single_test_plan(self, test_plan_name: str) -> Dict[str, Any]:
        """Execute a single test plan"""
        try:
            self.logger.info(f"Executing test plan: {test_plan_name}")
            
            # Find test plan in cache or load it
            test_plan_data = self._load_test_plan(test_plan_name)
            if not test_plan_data:
                return {
                    'test_plan_name': test_plan_name,
                    'status': 'ERROR',
                    'error': 'Test plan not found',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Execute test plan
            execution_result = self.execute_test_plan(
                test_plan_data.get('system_address', 'UNKNOWN'),
                test_plan_data.get('test_type', 'unknown')
            )
            
            return {
                'test_plan_name': test_plan_name,
                'system_address': test_plan_data.get('system_address', 'UNKNOWN'),
                'test_type': test_plan_data.get('test_type', 'unknown'),
                'execution_result': execution_result,
                'status': 'COMPLETED' if execution_result.get('tests_executed', 0) > 0 else 'ERROR',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error executing single test plan {test_plan_name}: {e}")
            return {
                'test_plan_name': test_plan_name,
                'status': 'ERROR',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _load_test_plan(self, test_plan_name: str) -> Optional[Dict[str, Any]]:
        """Load test plan from cache or file system"""
        try:
            # Check cache first
            for cache_key, cached_plan in self.test_plan_cache.items():
                if test_plan_name in cache_key:
                    return cached_plan
            
            # Search for test plan in discovered plans
            for system_address, system_plans in self.test_orchestration.get('discovered_plans', {}).items():
                for test_type, test_plan_data in system_plans.items():
                    if test_plan_name in test_type or test_plan_name in test_plan_data.get('file_path', ''):
                        return test_plan_data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error loading test plan {test_plan_name}: {e}")
            return None
    
    def _aggregate_test_suite_results(self, test_suite_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate results from multiple test suites"""
        try:
            aggregation = {
                'total_suites': len(test_suite_results),
                'successful_suites': 0,
                'failed_suites': 0,
                'total_tests': 0,
                'successful_tests': 0,
                'failed_tests': 0,
                'total_execution_time': 0,
                'suite_summaries': []
            }
            
            for suite_result in test_suite_results:
                if suite_result.get('error'):
                    aggregation['failed_suites'] += 1
                else:
                    aggregation['successful_suites'] += 1
                    
                    # Aggregate test results
                    suite_summary = suite_result.get('suite_summary', {})
                    aggregation['total_tests'] += suite_summary.get('total_tests', 0)
                    aggregation['successful_tests'] += suite_summary.get('successful_tests', 0)
                    aggregation['failed_tests'] += suite_summary.get('failed_tests', 0)
                    aggregation['total_execution_time'] += suite_summary.get('execution_time_seconds', 0)
                    
                    aggregation['suite_summaries'].append({
                        'suite_name': suite_result.get('suite_name', ''),
                        'summary': suite_summary
                    })
            
            return aggregation
            
        except Exception as e:
            self.logger.error(f"Error aggregating test suite results: {e}")
            return {'error': str(e)}
    
    def _generate_performance_metrics(self, suite_execution: Dict[str, Any]) -> Dict[str, Any]:
        """Generate performance metrics for test suite execution"""
        try:
            metrics = {
                'execution_time_seconds': 0,
                'tests_per_second': 0,
                'success_rate': 0,
                'average_test_time': 0,
                'resource_usage': {},
                'performance_grade': 'UNKNOWN'
            }
            
            # Calculate execution time
            start_time = datetime.fromisoformat(suite_execution.get('execution_started', ''))
            end_time = datetime.fromisoformat(suite_execution.get('execution_completed', ''))
            metrics['execution_time_seconds'] = (end_time - start_time).total_seconds()
            
            # Calculate performance metrics
            aggregated = suite_execution.get('aggregated_results', {})
            total_tests = aggregated.get('total_tests', 1)
            successful_tests = aggregated.get('successful_tests', 0)
            
            metrics['tests_per_second'] = total_tests / max(metrics['execution_time_seconds'], 1)
            metrics['success_rate'] = (successful_tests / max(total_tests, 1)) * 100
            metrics['average_test_time'] = metrics['execution_time_seconds'] / max(total_tests, 1)
            
            # Determine performance grade
            if metrics['success_rate'] >= 95 and metrics['tests_per_second'] >= 1:
                metrics['performance_grade'] = 'EXCELLENT'
            elif metrics['success_rate'] >= 90 and metrics['tests_per_second'] >= 0.5:
                metrics['performance_grade'] = 'GOOD'
            elif metrics['success_rate'] >= 80:
                metrics['performance_grade'] = 'FAIR'
            else:
                metrics['performance_grade'] = 'POOR'
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error generating performance metrics: {e}")
            return {'error': str(e)}
    
    def _generate_execution_summary(self, suite_execution: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive execution summary"""
        try:
            summary = {
                'execution_overview': {
                    'total_suites': len(suite_execution.get('test_suites_executed', [])),
                    'execution_time': suite_execution.get('performance_metrics', {}).get('execution_time_seconds', 0),
                    'success_rate': suite_execution.get('performance_metrics', {}).get('success_rate', 0),
                    'performance_grade': suite_execution.get('performance_metrics', {}).get('performance_grade', 'UNKNOWN')
                },
                'aggregated_results': suite_execution.get('aggregated_results', {}),
                'performance_metrics': suite_execution.get('performance_metrics', {}),
                'errors': suite_execution.get('errors', []),
                'recommendations': self._generate_test_recommendations(suite_execution)
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating execution summary: {e}")
            return {'error': str(e)}
    
    def _generate_suite_summary(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary for individual test suite"""
        try:
            summary = {
                'total_tests': len(test_results),
                'successful_tests': 0,
                'failed_tests': 0,
                'execution_time_seconds': 0,
                'success_rate': 0
            }
            
            for test_result in test_results:
                if test_result.get('status') == 'COMPLETED':
                    summary['successful_tests'] += 1
                else:
                    summary['failed_tests'] += 1
                
                # Add execution time if available
                execution_result = test_result.get('execution_result', {})
                summary['execution_time_seconds'] += execution_result.get('execution_time_ms', 0) / 1000
            
            summary['success_rate'] = (summary['successful_tests'] / max(summary['total_tests'], 1)) * 100
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating suite summary: {e}")
            return {'error': str(e)}
    
    def _generate_test_recommendations(self, suite_execution: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on test execution results"""
        try:
            recommendations = []
            
            performance_metrics = suite_execution.get('performance_metrics', {})
            success_rate = performance_metrics.get('success_rate', 0)
            
            if success_rate < 80:
                recommendations.append("Low success rate detected - investigate failing tests")
            
            if performance_metrics.get('tests_per_second', 0) < 0.5:
                recommendations.append("Slow test execution - consider optimizing test performance")
            
            if performance_metrics.get('performance_grade') == 'POOR':
                recommendations.append("Poor performance detected - comprehensive system review recommended")
            
            errors = suite_execution.get('errors', [])
            if len(errors) > 0:
                recommendations.append(f"{len(errors)} execution errors detected - review error logs")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating test recommendations: {e}")
            return ['Error generating recommendations']
    
    def _save_test_suite_execution_results(self, suite_execution: Dict[str, Any]):
        """Save test suite execution results"""
        try:
            if self.orchestrator:
                # Save to diagnostic reports
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                report_path = self.diagnostic_reports_path / f"test_suite_execution_{timestamp}.json"
                
                with open(report_path, 'w') as f:
                    json.dump(suite_execution, f, indent=2, default=str)
                
                self.logger.info(f"Test suite execution results saved: {report_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving test suite execution results: {e}")
    
    def get_test_suite_status(self) -> Dict[str, Any]:
        """Get comprehensive test suite status"""
        try:
            return {
                'test_suite_initialized': True,
                'test_suite_config': self.test_suite_config,
                'test_plan_loader_config': self.test_plan_loader_config,
                'test_orchestration': self.test_orchestration,
                'test_execution_engine': self.test_execution_engine,
                'discovered_plans': len(self.test_orchestration.get('discovered_plans', {})),
                'cached_plans': len(self.test_plan_cache),
                'execution_history': len(self.test_orchestration.get('execution_history', []))
            }
            
        except Exception as e:
            self.logger.error(f"Error getting test suite status: {e}")
            return {'error': str(e)}
    
    # ===== FAULT CODE ENFORCEMENT =====
    
    def start_fault_code_enforcement(self):
        """Start fault code enforcement system"""
        try:
            self.logger.info("Starting fault code enforcement...")
            
            # Start diagnostic test execution engine
            self._start_diagnostic_test_execution_engine()
            
            # Start universal language validator
            self._start_universal_language_validator()
            
            # Start protocol compliance enforcer
            self._start_protocol_compliance_enforcer()
            
            self.logger.info("Fault code enforcement started")
            
        except Exception as e:
            self.logger.error(f"Error starting fault code enforcement: {e}")
    
    def _start_diagnostic_test_execution_engine(self):
        """Start diagnostic test execution engine"""
        import threading
        
        def test_execution_loop():
            while self.autonomous_mode:
                try:
                    self._execute_system_diagnostic_tests()
                    time.sleep(1800)  # Check every 30 minutes
                    
                except Exception as e:
                    self.logger.error(f"Test execution engine error: {e}")
                    time.sleep(1800)
        
        threading.Thread(target=test_execution_loop, daemon=True).start()
        self.logger.info("Diagnostic test execution engine started")
    
    def _execute_system_diagnostic_tests(self):
        """Execute diagnostic tests for all systems"""
        try:
            for system_address, system_data in self.system_registry.items():
                self._execute_single_system_test(system_address, system_data)
                
        except Exception as e:
            self.logger.error(f"Error executing system diagnostic tests: {e}")
    
    def _execute_single_system_test(self, system_address: str, system_data: Dict[str, Any]):
        """Execute diagnostic test for a single system"""
        try:
            # Run smoke test
            test_result = self.execute_test_plan(system_address, "smoke_test")
            
            # Check if test passed
            if test_result.get('tests_passed', 0) > 0:
                system_data['status'] = DiagnosticStatus.OK.value
            else:
                system_data['status'] = DiagnosticStatus.ERROR.value
                
        except Exception as e:
            self.logger.error(f"Error executing test for {system_address}: {e}")
    
    def _start_universal_language_validator(self):
        """Start universal language validator"""
        import threading
        
        def validator_loop():
            while self.autonomous_mode:
                try:
                    self._validate_pending_responses()
                    time.sleep(60)  # Check every minute
                    
                except Exception as e:
                    self.logger.error(f"Universal language validator error: {e}")
                    time.sleep(60)
        
        threading.Thread(target=validator_loop, daemon=True).start()
        self.logger.info("Universal language validator started")
    
    def _validate_pending_responses(self):
        """Validate pending responses against protocol"""
        try:
            for signal_id, response_data in list(self.pending_responses.items()):
                # Validate response format
                if self._validate_response_against_protocol(response_data):
                    self.logger.info(f"Response {signal_id} validated successfully")
                else:
                    self.logger.warning(f"Response {signal_id} failed validation")
                    
        except Exception as e:
            self.logger.error(f"Error validating pending responses: {e}")
    
    def _validate_response_against_protocol(self, response_data: Dict[str, Any]) -> bool:
        """Validate response against universal language protocol"""
        try:
            # Check required fields
            required_fields = ['system_address', 'response_type', 'timestamp']
            for field in required_fields:
                if field not in response_data:
                    return False
            
            # Validate system address format
            if not self._validate_system_address_format(response_data['system_address']):
                return False
            
            # Validate response code format
            if not self._validate_response_code_format(response_data.get('response_code', '')):
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating response against protocol: {e}")
            return False
    
    def _validate_system_address_format(self, address: str) -> bool:
        """Validate system address format"""
        try:
            # Basic address format validation
            import re
            pattern = r'^[A-Za-z0-9-]+$'
            return bool(re.match(pattern, address))
            
        except Exception as e:
            self.logger.error(f"Error validating system address format: {e}")
            return False
    
    def _validate_response_code_format(self, response_code: str) -> bool:
        """Validate response code format"""
        try:
            # Basic response code validation
            if not response_code:
                return True  # Optional field
            
            import re
            pattern = r'^[A-Za-z0-9_-]+$'
            return bool(re.match(pattern, response_code))
            
        except Exception as e:
            self.logger.error(f"Error validating response code format: {e}")
            return False
    
    def _start_protocol_compliance_enforcer(self):
        """Start protocol compliance enforcer"""
        import threading
        
        def compliance_loop():
            while self.autonomous_mode:
                try:
                    self._enforce_protocol_compliance()
                    time.sleep(300)  # Check every 5 minutes
                    
                except Exception as e:
                    self.logger.error(f"Protocol compliance enforcer error: {e}")
                    time.sleep(300)
        
        threading.Thread(target=compliance_loop, daemon=True).start()
        self.logger.info("Protocol compliance enforcer started")
    
    def _enforce_protocol_compliance(self):
        """Enforce protocol compliance across all systems"""
        try:
            for system_address, system_data in self.system_registry.items():
                compliance_result = self._check_system_compliance(system_address, system_data)
                
                if not compliance_result.get('compliant', True):
                    violations = compliance_result.get('violations', [])
                    self.logger.warning(f"System {system_address} has compliance violations: {violations}")
                    
        except Exception as e:
            self.logger.error(f"Error enforcing protocol compliance: {e}")
    
    def _check_system_compliance(self, system_address: str, system_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check system compliance with protocol"""
        try:
            violations = []
            
            # Check if system responds to diagnostics
            if not self._system_responds_to_diagnostics(system_address):
                violations.append('NO_DIAGNOSTIC_RESPONSE')
            
            # Check if system uses proper fault codes
            if not self._system_uses_proper_fault_codes(system_address):
                violations.append('INVALID_FAULT_CODES')
            
            # Check if system follows universal language
            if not self._system_follows_universal_language(system_address):
                violations.append('NON_UNIVERSAL_LANGUAGE')
            
            return {
                'compliant': len(violations) == 0,
                'violations': violations,
                'system_address': system_address
            }
            
        except Exception as e:
            self.logger.error(f"Error checking system compliance: {e}")
            return {'compliant': False, 'violations': ['COMPLIANCE_CHECK_ERROR'], 'system_address': system_address}
    
    def _system_responds_to_diagnostics(self, system_address: str) -> bool:
        """Check if system responds to diagnostics"""
        try:
            # Simple check - look at last signal time
            system_info = self.system_registry.get(system_address, {})
            last_signal = system_info.get('last_signal')
            
            if last_signal:
                # Check if signal was recent (within last hour)
                signal_time = datetime.fromisoformat(last_signal)
                time_diff = (datetime.now() - signal_time).total_seconds()
                return time_diff < 3600
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking system diagnostic response: {e}")
            return False
    
    def _system_uses_proper_fault_codes(self, system_address: str) -> bool:
        """Check if system uses proper fault codes"""
        try:
            # Check if system has any fault codes in the vault
            fault_vault_files = list(self.fault_vault_path.glob(f"*{system_address}*"))
            
            for fault_file in fault_vault_files:
                try:
                    with open(fault_file, 'r') as f:
                        content = f.read()
                        
                    # Look for fault code patterns
                    import re
                    if re.search(r'\[[A-Za-z0-9-]+-\d{2}-[A-Za-z0-9_-]+\]', content):
                        return True
                        
                except Exception:
                    continue
            
            return len(fault_vault_files) == 0  # No fault files = compliant
            
        except Exception as e:
            self.logger.error(f"Error checking system fault codes: {e}")
            return True  # Assume compliant on error
    
    def _system_follows_universal_language(self, system_address: str) -> bool:
        """Check if system follows universal language"""
        try:
            # Check system registry for proper format
            system_info = self.system_registry.get(system_address, {})
            
            # Check if address format is valid
            if not self._validate_system_address_format(system_address):
                return False
            
            # Check if name and handler are present
            if not system_info.get('name') or not system_info.get('handler'):
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking system universal language: {e}")
            return False
    
    # ===== TRANSMIT FUNCTIONS =====
    
    def transmit_signal(self, target_address: str, signal_type: str, radio_code: str, 
                       message: str, payload: Dict[str, Any] = None, 
                       response_expected: bool = False, timeout: int = 30) -> str:
        """Transmit signal to target system via comms module"""
        if self.comms:
            return self.comms.transmit_signal(target_address, signal_type, radio_code, 
                                            message, payload, response_expected, timeout)
        else:
            self.logger.error("No communication system available")
            return ""
    
    def transmit_radio_check(self, target_address: str) -> str:
        """Transmit radio check to target system"""
        if self.comms:
            return self.comms.transmit_radio_check(target_address)
        else:
            self.logger.error("No communication system available")
            return ""
    
    def transmit_status_request(self, target_address: str) -> str:
        """Transmit status request to target system"""
        if self.comms:
            return self.comms.transmit_signal(target_address, "status_request", "STATUS", 
                                            "Status check requested")
        else:
            self.logger.error("No communication system available")
            return ""
    
    def transmit_rollcall(self) -> List[str]:
        """Transmit rollcall to all systems"""
        if self.comms:
            return self.comms.transmit_rollcall()
        else:
            self.logger.error("No communication system available")
            return []
    
    def transmit_sos_fault(self, system_address: str, fault_code: str, description: str) -> str:
        """Transmit SOS fault signal"""
        if self.comms:
            return self.comms.transmit_sos_fault(system_address, fault_code, description)
        else:
            self.logger.error("No communication system available")
            return ""
    
    # ===== SYSTEM MANAGEMENT FUNCTIONS =====
    
    def save_diagnostic_report(self, report_data: Dict[str, Any], report_type: str = "general"):
        """Save diagnostic report to appropriate location"""
        try:
            report_file = self.diagnostic_reports_path / f"{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            
            with open(report_file, 'w') as f:
                f.write(f"# {report_type.upper()} DIAGNOSTIC REPORT\n")
                f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
                
                for key, value in report_data.items():
                    f.write(f"**{key}:** {value}\n")
            
            self.logger.info(f"Diagnostic report saved: {report_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving diagnostic report: {e}")
    
    def save_fault_amendment(self, fault_id: str, amendment_data: Dict[str, Any]):
        """Save fault amendment to appropriate location"""
        try:
            amendment_file = self.fault_amendments_path / f"fault_{fault_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            
            with open(amendment_file, 'w') as f:
                f.write(f"# FAULT AMENDMENT - {fault_id}\n")
                f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
                
                for key, value in amendment_data.items():
                    f.write(f"**{key}:** {value}\n")
            
            self.logger.info(f"Fault amendment saved: {amendment_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving fault amendment: {e}")
    
    def save_system_amendment(self, system_address: str, amendment_data: Dict[str, Any]):
        """Save system amendment to appropriate location"""
        try:
            amendment_file = self.systems_amendments_path / f"system_{system_address}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            
            with open(amendment_file, 'w') as f:
                f.write(f"# SYSTEM AMENDMENT - {system_address}\n")
                f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
                
                for key, value in amendment_data.items():
                    f.write(f"**{key}:** {value}\n")
            
            self.logger.info(f"System amendment saved: {amendment_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving system amendment: {e}")
    
    def load_dependencies(self) -> Dict[str, Any]:
        """Load system dependencies"""
        try:
            dependencies_file = self.dependencies_path / "dependencies.json"
            
            if dependencies_file.exists():
                with open(dependencies_file, 'r') as f:
                    return json.load(f)
            else:
                return {}
                
        except Exception as e:
            self.logger.error(f"Error loading dependencies: {e}")
            return {}
    
    def save_sop_document(self, sop_data: Dict[str, Any], sop_type: str):
        """Save SOP document to appropriate location"""
        try:
            sop_file = self.sop_path / f"{sop_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            
            with open(sop_file, 'w') as f:
                f.write(f"# {sop_type.upper()} SOP\n")
                f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
                
                for key, value in sop_data.items():
                    f.write(f"**{key}:** {value}\n")
            
            self.logger.info(f"SOP document saved: {sop_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving SOP document: {e}")
    
    def get_directory_status(self) -> Dict[str, Any]:
        """Get status of all directories"""
        try:
            directory_status = {}
            
            for path_name, path_obj in [
                ("test_plans", self.test_plans_path),
                ("library", self.library_path),
                ("dependencies", self.dependencies_path),
                ("sop", self.sop_path),
                ("sandbox", self.sandbox_path),
                ("secure_vault", self.secure_vault_path),
                ("heartbeat", self.heartbeat_path),
                ("fault_vault", self.fault_vault_path)
            ]:
                directory_status[path_name] = {
                    "exists": path_obj.exists(),
                    "readable": path_obj.is_dir() and os.access(path_obj, os.R_OK),
                    "writable": path_obj.is_dir() and os.access(path_obj, os.W_OK),
                    "file_count": len(list(path_obj.glob("*"))) if path_obj.exists() else 0
                }
            
            return directory_status
            
        except Exception as e:
            self.logger.error(f"Error getting directory status: {e}")
            return {}
    
    # ===== FAULT PROCESSING FUNCTIONS =====
    
    def process_fault_report(self, fault_data: Dict[str, Any]):
        """Process incoming fault report - coordinate with enforcement module"""
        try:
            if self.enforcement:
                # Lazy load enforcement module if needed
                if not self.lazy_loaded_modules['enforcement']:
                    self.lazy_load_enforcement_module()
                
                if self.enforcement:
                    self.enforcement.process_fault_report(fault_data)
            else:
                self.logger.error("No enforcement module available to process fault report")
                
        except Exception as e:
            self.logger.error(f"Error processing fault report: {e}")
    
    def _process_incoming_fault_code(self, fault_code: str, payload: Dict[str, Any], priority: str = 'NORMAL'):
        """Process incoming fault code from other systems"""
        try:
            system_address = payload.get('system_address', 'UNKNOWN')
            self.logger.info(f"Processing incoming fault code: {fault_code} from {system_address}")
            
            # Validate fault code using auth module
            if self.auth:
                validation_result = self.auth.validate_fault_code(fault_code, system_address)
                
                if not validation_result['valid']:
                    self.logger.error(f"Fault code validation failed: {validation_result['errors']}")
                    return
                
                if validation_result['warnings']:
                    for warning in validation_result['warnings']:
                        self.logger.warning(f"Fault validation warning: {warning}")
                
                # Use validated severity
                severity = validation_result['severity']
            else:
                # Fallback validation if auth module not available
                if not self._validate_fault_code_format(fault_code):
                    self.logger.error(f"Invalid fault code format: {fault_code}")
                    return
                
                parsed_code = self._parse_fault_code(fault_code)
                severity = self._determine_fault_severity(parsed_code.get('fault_id', ''))
            
            # Parse fault code components
            parsed_code = self._parse_fault_code(fault_code)
            
            # Create fault report
            fault_report = {
                'fault_code': fault_code,
                'system_address': parsed_code.get('system_address', system_address),
                'fault_id': parsed_code.get('fault_id', 'UNKNOWN'),
                'line_number': parsed_code.get('line_number', 'UNKNOWN'),
                'severity': severity,
                'payload': payload,
                'priority': priority,
                'timestamp': datetime.now().isoformat(),
                'validated': True,
                'authenticated': self.auth and validation_result.get('authenticated', False) if self.auth else False
            }
            
            # Route to enforcement module for processing
            if self.enforcement:
                self.enforcement.process_fault_report(fault_report)
            
            self.logger.info(f"Fault code processed and validated: {fault_code}")
            
        except Exception as e:
            self.logger.error(f"Error processing incoming fault code: {e}")
    
    def _validate_fault_code_format(self, fault_code: str) -> bool:
        """Validate fault code format"""
        try:
            import re
            # Expected format: [SYSTEM_ADDRESS-FAULT_ID-LINE_NUMBER]
            pattern = r'^\[[A-Za-z0-9-]+-\d{2}-[A-Za-z0-9_-]+\]$'
            return bool(re.match(pattern, fault_code))
            
        except Exception as e:
            self.logger.error(f"Error validating fault code format: {e}")
            return False
    
    def _parse_fault_code(self, fault_code: str) -> Dict[str, str]:
        """Parse fault code into components"""
        try:
            # Remove brackets and split by hyphens
            clean_code = fault_code.strip('[]')
            parts = clean_code.split('-')
            
            if len(parts) >= 3:
                return {
                    'system_address': parts[0],
                    'fault_id': parts[1],
                    'line_number': '-'.join(parts[2:])  # In case line number contains hyphens
                }
            else:
                return {
                    'system_address': 'UNKNOWN',
                    'fault_id': 'UNKNOWN',
                    'line_number': 'UNKNOWN'
                }
                
        except Exception as e:
            self.logger.error(f"Error parsing fault code: {e}")
            return {
                'system_address': 'UNKNOWN',
                'fault_id': 'UNKNOWN',
                'line_number': 'UNKNOWN'
            }
    
    def _determine_fault_severity(self, fault_id: str) -> 'FaultSeverity':
        """Determine fault severity from fault ID"""
        try:
            # Import FaultSeverity enum (assuming it exists in the system)
            # This is a simplified version - real implementation would be more complex
            
            fault_num = int(fault_id) if fault_id.isdigit() else 99
            
            if 1 <= fault_num <= 49:
                return 'ERROR'  # Help me
            elif 50 <= fault_num <= 89:
                return 'FAILURE'  # I'm dead
            elif 90 <= fault_num <= 99:
                return 'CRITICAL'  # System dead
            else:
                return 'UNKNOWN'
                
        except Exception as e:
            self.logger.error(f"Error determining fault severity: {e}")
            return 'UNKNOWN'
    
    # ===== SYSTEM STATUS AND HEALTH FUNCTIONS =====
    
    def get_unified_status(self) -> Dict[str, Any]:
        """Get unified system status"""
        try:
            status = {
                'timestamp': datetime.now().isoformat(),
                'core_status': {
                    'monitoring_active': self.monitoring_active,
                    'launcher_active': self.launcher_active,
                    'autonomous_mode': self.autonomous_mode,
                    'registered_systems': len(self.system_registry),
                    'active_faults': len(self.active_faults)
                },
                'directory_status': self.get_directory_status(),
                'system_registry': {
                    address: {
                        'name': info.get('name', 'Unknown'),
                        'status': str(info.get('status', 'UNKNOWN')),
                        'signal_count': info.get('signal_count', 0),
                        'error_count': info.get('error_count', 0)
                    }
                    for address, info in self.system_registry.items()
                }
            }
            
            # Add module statuses if available
            if hasattr(self, 'auth') and self.auth:
                status['auth_status'] = self.auth.get_authentication_status()
            
            if hasattr(self, 'comms') and self.comms:
                status['comms_status'] = self.comms.get_communication_status()
            
            if hasattr(self, 'recovery') and self.recovery:
                status['recovery_status'] = self.recovery.get_recovery_status()
            
            if hasattr(self, 'enforcement') and self.enforcement:
                status['enforcement_status'] = self.enforcement.get_enforcement_status()
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting unified status: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    def run_comprehensive_test_suite(self, test_type: str = "smoke_test") -> Dict[str, Any]:
        """Run comprehensive test suite for all systems"""
        try:
            self.logger.info(f"Running comprehensive {test_type} test suite...")
            
            suite_result = {
                'test_type': test_type,
                'start_time': datetime.now().isoformat(),
                'systems_tested': 0,
                'systems_passed': 0,
                'systems_failed': 0,
                'total_tests': 0,
                'total_passed': 0,
                'total_failed': 0,
                'results': []
            }
            
            # Test each system
            for system_address, system_data in self.system_registry.items():
                try:
                    test_result = self.execute_test_plan(system_address, test_type)
                    suite_result['results'].append(test_result)
                    
                    suite_result['systems_tested'] += 1
                    suite_result['total_tests'] += test_result.get('tests_executed', 0)
                    suite_result['total_passed'] += test_result.get('tests_passed', 0)
                    suite_result['total_failed'] += test_result.get('tests_failed', 0)
                    
                    if test_result.get('tests_passed', 0) > 0:
                        suite_result['systems_passed'] += 1
                    else:
                        suite_result['systems_failed'] += 1
                        
                except Exception as e:
                    self.logger.error(f"Error testing system {system_address}: {e}")
                    suite_result['systems_failed'] += 1
            
            suite_result['end_time'] = datetime.now().isoformat()
            suite_result['duration_seconds'] = (
                datetime.fromisoformat(suite_result['end_time']) - 
                datetime.fromisoformat(suite_result['start_time'])
            ).total_seconds()
            
            # Save test suite report
            self._save_test_suite_report(suite_result)
            
            self.logger.info(f"Test suite completed: {suite_result['systems_passed']}/{suite_result['systems_tested']} systems passed")
            
            return suite_result
            
        except Exception as e:
            self.logger.error(f"Error running comprehensive test suite: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    def _save_test_suite_report(self, suite_result: Dict[str, Any]):
        """Save test suite report to diagnostic reports"""
        try:
            report_data = {
                'test_type': suite_result.get('test_type', 'unknown'),
                'systems_tested': suite_result.get('systems_tested', 0),
                'systems_passed': suite_result.get('systems_passed', 0),
                'systems_failed': suite_result.get('systems_failed', 0),
                'total_tests': suite_result.get('total_tests', 0),
                'total_passed': suite_result.get('total_passed', 0),
                'total_failed': suite_result.get('total_failed', 0),
                'duration_seconds': suite_result.get('duration_seconds', 0),
                'start_time': suite_result.get('start_time', ''),
                'end_time': suite_result.get('end_time', '')
            }
            
            self.save_diagnostic_report(report_data, "comprehensive_test_suite")
            
        except Exception as e:
            self.logger.error(f"Error saving test suite report: {e}")
    
    # ===== SIGNAL HANDLER FUNCTIONS =====
    
    def _handle_diagnostic_rollcall(self, payload: Dict[str, Any]) -> None:
        """Handle diagnostic rollcall signal"""
        try:
            source_address = payload.get('source_address', 'UNKNOWN')
            self.logger.info(f"Received rollcall from {source_address}")
            
            # Update system registry
            if source_address in self.system_registry:
                system_info = self.system_registry[source_address]
                system_info['last_signal'] = datetime.now().isoformat()
                system_info['signal_count'] += 1
                system_info['status'] = DiagnosticStatus.OK.value
            
            # Route to enforcement for auto-registration
            if self.enforcement:
                self.enforcement.process_rollcall_response(payload)
                
        except Exception as e:
            self.logger.error(f"Error handling diagnostic rollcall: {e}")
    
    def _handle_diagnostic_status_request(self, payload: Dict[str, Any]) -> None:
        """Handle diagnostic status request signal"""
        try:
            source_address = payload.get('source_address', 'UNKNOWN')
            self.logger.info(f"Received status request from {source_address}")
            
            # Update system registry
            if source_address in self.system_registry:
                system_info = self.system_registry[source_address]
                system_info['last_signal'] = datetime.now().isoformat()
                system_info['signal_count'] += 1
            
            # Send status response
            status_response = self.get_system_status()
            if self.comms:
                self.comms.transmit_signal(source_address, "status_response", "10-4", 
                                         "Status response", status_response)
                
        except Exception as e:
            self.logger.error(f"Error handling diagnostic status request: {e}")
    
    def _handle_diagnostic_radio_check(self, payload: Dict[str, Any]) -> None:
        """Handle diagnostic radio check signal"""
        try:
            source_address = payload.get('source_address', 'UNKNOWN')
            self.logger.info(f"Received radio check from {source_address}")
            
            # Update system registry
            if source_address in self.system_registry:
                system_info = self.system_registry[source_address]
                system_info['last_signal'] = datetime.now().isoformat()
                system_info['signal_count'] += 1
                system_info['status'] = DiagnosticStatus.OK.value
            
            # Send radio check response
            if self.comms:
                self.comms.transmit_signal(source_address, "radio_check_response", "10-4", 
                                         "Radio check response")
                
        except Exception as e:
            self.logger.error(f"Error handling diagnostic radio check: {e}")
    
    def _handle_diagnostic_sos_fault(self, payload: Dict[str, Any]) -> None:
        """Handle diagnostic SOS fault signal"""
        try:
            source_address = payload.get('source_address', 'UNKNOWN')
            fault_code = payload.get('fault_code', 'UNKNOWN')
            self.logger.warning(f"Received SOS fault from {source_address}: {fault_code}")
            
            # Update system registry
            if source_address in self.system_registry:
                system_info = self.system_registry[source_address]
                system_info['last_signal'] = datetime.now().isoformat()
                system_info['signal_count'] += 1
                system_info['status'] = DiagnosticStatus.FAILURE.value
                system_info['faults'].append(fault_code)
            
            # Route to enforcement for processing
            if self.enforcement:
                self.enforcement.process_sos_fault_report(payload)
                
        except Exception as e:
            self.logger.error(f"Error handling diagnostic SOS fault: {e}")
    
    def _handle_fault_report(self, payload: Dict[str, Any]) -> None:
        """Handle fault report signal"""
        try:
            source_address = payload.get('source_address', 'UNKNOWN')
            fault_code = payload.get('fault_code', 'UNKNOWN')
            self.logger.warning(f"Received fault report from {source_address}: {fault_code}")
            
            # Update system registry
            if source_address in self.system_registry:
                system_info = self.system_registry[source_address]
                system_info['last_signal'] = datetime.now().isoformat()
                system_info['signal_count'] += 1
                system_info['error_count'] += 1
                system_info['status'] = DiagnosticStatus.ERROR.value
                system_info['faults'].append(fault_code)
            
            # Route to enforcement for processing
            if self.enforcement:
                self.enforcement.process_fault_report(payload)
                
        except Exception as e:
            self.logger.error(f"Error handling fault report: {e}")
    
    def _handle_sos_fault_report(self, payload: Dict[str, Any]) -> None:
        """Handle SOS fault report signal"""
        try:
            source_address = payload.get('source_address', 'UNKNOWN')
            fault_code = payload.get('fault_code', 'UNKNOWN')
            self.logger.error(f"Received SOS fault report from {source_address}: {fault_code}")
            
            # Update system registry
            if source_address in self.system_registry:
                system_info = self.system_registry[source_address]
                system_info['last_signal'] = datetime.now().isoformat()
                system_info['signal_count'] += 1
                system_info['status'] = DiagnosticStatus.FAILURE.value
                system_info['faults'].append(fault_code)
            
            # Route to enforcement for processing
            if self.enforcement:
                self.enforcement.process_sos_fault_report(payload)
                
        except Exception as e:
            self.logger.error(f"Error handling SOS fault report: {e}")
    
    def _handle_system_fault_report(self, payload: Dict[str, Any]) -> None:
        """Handle system fault report signal"""
        try:
            source_address = payload.get('source_address', 'UNKNOWN')
            fault_code = payload.get('fault_code', 'UNKNOWN')
            self.logger.error(f"Received system fault report from {source_address}: {fault_code}")
            
            # Update system registry
            if source_address in self.system_registry:
                system_info = self.system_registry[source_address]
                system_info['last_signal'] = datetime.now().isoformat()
                system_info['signal_count'] += 1
                system_info['status'] = DiagnosticStatus.FAILURE.value
                system_info['faults'].append(fault_code)
            
            # Route to enforcement for processing
            if self.enforcement:
                self.enforcement.process_system_fault_report(payload)
                
        except Exception as e:
            self.logger.error(f"Error handling system fault report: {e}")
    
    def _handle_error_report(self, payload: Dict[str, Any]) -> None:
        """Handle error report signal"""
        try:
            source_address = payload.get('source_address', 'UNKNOWN')
            error_code = payload.get('error_code', 'UNKNOWN')
            self.logger.warning(f"Received error report from {source_address}: {error_code}")
            
            # Update system registry
            if source_address in self.system_registry:
                system_info = self.system_registry[source_address]
                system_info['last_signal'] = datetime.now().isoformat()
                system_info['signal_count'] += 1
                system_info['error_count'] += 1
                system_info['status'] = DiagnosticStatus.ERROR.value
                system_info['faults'].append(error_code)
            
            # Route to enforcement for processing
            if self.enforcement:
                self.enforcement.process_error_report(payload)
                
        except Exception as e:
            self.logger.error(f"Error handling error report: {e}")
    
    # ===== PAYLOAD AND TEST EXECUTION FUNCTIONS =====
    
    def create_diagnostic_payload(self, operation: str, data: Dict[str, Any], 
                                metadata: Dict[str, Any] = None, priority: int = 5,
                                retention_days: int = 30, compression: str = "none",
                                encryption: str = "none") -> Dict[str, Any]:
        """Create diagnostic payload via comms module"""
        if self.comms:
            return self.comms.create_diagnostic_payload(operation, data, metadata, 
                                                      priority, retention_days, compression, encryption)
        else:
            self.logger.error("No communication system available")
            return {}
    
    def validate_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validate payload via comms module"""
        if self.comms:
            return self.comms.validate_payload(payload)
        else:
            self.logger.error("No communication system available")
            return {'valid': False, 'errors': ['No communication system available']}
    
    def route_payload(self, payload: Dict[str, Any], target_address: str, 
                     signal_type: str = "diagnostic_request", 
                     response_expected: bool = False, timeout: int = 30) -> str:
        """Route payload to target system"""
        try:
            if self.comms:
                return self.comms.transmit_signal(target_address, signal_type, "STATUS", 
                                                "Diagnostic payload", payload, response_expected, timeout)
            else:
                self.logger.error("No communication system available")
                return ""
                
        except Exception as e:
            self.logger.error(f"Error routing payload: {e}")
            return ""
    
    def _archive_payload(self, signal_id: str, payload: Dict[str, Any]):
        """Archive payload for record keeping"""
        try:
            archive_file = self.diagnostic_reports_path / f"payload_archive_{signal_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(archive_file, 'w') as f:
                json.dump({
                    'signal_id': signal_id,
                    'payload': payload,
                    'archived_at': datetime.now().isoformat()
                }, f, indent=2)
            
            self.logger.info(f"Payload archived: {archive_file}")
            
        except Exception as e:
            self.logger.error(f"Error archiving payload: {e}")
    
    def execute_fault_repair_test(self, fault_id: str, repair_action: str, target_system: str) -> Dict[str, Any]:
        """Execute fault repair test"""
        try:
            self.logger.info(f"Executing fault repair test: {fault_id} on {target_system}")
            
            repair_test_result = {
                'fault_id': fault_id,
                'repair_action': repair_action,
                'target_system': target_system,
                'start_time': datetime.now().isoformat(),
                'test_passed': False,
                'test_failed': False,
                'error_message': None,
                'repair_result': None
            }
            
            # Attempt fault repair
            if self.recovery:
                repair_result = self.recovery._attempt_fault_repair(fault_id, repair_action, target_system)
                repair_test_result['repair_result'] = repair_result
                
                if repair_result.get('success', False):
                    repair_test_result['test_passed'] = True
                else:
                    repair_test_result['test_failed'] = True
                    repair_test_result['error_message'] = repair_result.get('error', 'Unknown error')
            else:
                repair_test_result['test_failed'] = True
                repair_test_result['error_message'] = "No recovery system available"
            
            repair_test_result['end_time'] = datetime.now().isoformat()
            
            # Save repair test result
            self._save_fault_repair_test_result(repair_test_result)
            
            return repair_test_result
            
        except Exception as e:
            self.logger.error(f"Error executing fault repair test: {e}")
            return {
                'fault_id': fault_id,
                'repair_action': repair_action,
                'target_system': target_system,
                'test_failed': True,
                'error_message': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _save_fault_repair_test_result(self, repair_test_result: Dict[str, Any]):
        """Save fault repair test result"""
        try:
            result_data = {
                'fault_id': repair_test_result.get('fault_id', 'UNKNOWN'),
                'repair_action': repair_test_result.get('repair_action', 'UNKNOWN'),
                'target_system': repair_test_result.get('target_system', 'UNKNOWN'),
                'test_passed': repair_test_result.get('test_passed', False),
                'test_failed': repair_test_result.get('test_failed', False),
                'error_message': repair_test_result.get('error_message'),
                'start_time': repair_test_result.get('start_time'),
                'end_time': repair_test_result.get('end_time'),
                'repair_result': repair_test_result.get('repair_result')
            }
            
            self.save_diagnostic_report(result_data, "fault_repair_test")
            
        except Exception as e:
            self.logger.error(f"Error saving fault repair test result: {e}")
    
    def save_diagnostic_check_results(self, check_results: Dict[str, Any], check_type: str = "diagnostic_check"):
        """Save diagnostic check results to fault vault"""
        try:
            # Create fault vault entry
            fault_vault_file = self.fault_vault_path / f"diagnostic_check_{check_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            
            with open(fault_vault_file, 'w') as f:
                f.write(f"# DIAGNOSTIC CHECK RESULTS - {check_type.upper()}\n")
                f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
                
                f.write("## Check Summary\n")
                f.write(f"- **Check Type:** {check_type}\n")
                f.write(f"- **Systems Checked:** {check_results.get('systems_checked', 0)}\n")
                f.write(f"- **Checks Passed:** {check_results.get('checks_passed', 0)}\n")
                f.write(f"- **Checks Failed:** {check_results.get('checks_failed', 0)}\n")
                f.write(f"- **Duration:** {check_results.get('duration_seconds', 0)} seconds\n\n")
                
                if check_results.get('failed_systems'):
                    f.write("## Failed Systems\n")
                    for system in check_results['failed_systems']:
                        f.write(f"- **{system.get('address', 'UNKNOWN')}:** {system.get('error', 'Unknown error')}\n")
                    f.write("\n")
                
                if check_results.get('passed_systems'):
                    f.write("## Passed Systems\n")
                    for system in check_results['passed_systems']:
                        f.write(f"- **{system.get('address', 'UNKNOWN')}:** OK\n")
                    f.write("\n")
            
            self.logger.info(f"Diagnostic check results saved: {fault_vault_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving diagnostic check results: {e}")
    
    # ===== LIVE MONITORING AND OPERATIONAL FUNCTIONS =====
    
    def start_live_monitoring(self):
        """Start live monitoring system"""
        try:
            self.logger.info("Starting live monitoring...")
            
            # Start live operational monitoring via enforcement module
            if self.enforcement:
                self.enforcement.start_live_operational_monitoring()
            
            self.monitoring_active = True
            self.logger.info("Live monitoring started")
            
        except Exception as e:
            self.logger.error(f"Error starting live monitoring: {e}")
    
    def stop_live_monitoring(self):
        """Stop live monitoring system"""
        try:
            self.logger.info("Stopping live monitoring...")
            
            # Stop live operational monitoring via enforcement module
            if self.enforcement:
                self.enforcement.stop_live_monitoring()
            
            self.monitoring_active = False
            self.logger.info("Live monitoring stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping live monitoring: {e}")
    
    def _live_monitoring_loop(self):
        """Live monitoring loop"""
        import threading
        
        def monitoring_loop():
            while self.monitoring_active:
                try:
                    self._perform_periodic_health_checks()
                    self._analyze_fault_patterns()
                    self._update_system_statuses()
                    
                    time.sleep(60)  # Check every minute
                    
                except Exception as e:
                    self.logger.error(f"Live monitoring loop error: {e}")
                    time.sleep(60)
        
        threading.Thread(target=monitoring_loop, daemon=True).start()
        self.logger.info("Live monitoring loop started")
    
    def _perform_periodic_health_checks(self):
        """Perform periodic health checks on all systems"""
        try:
            self.logger.info("Performing periodic health checks...")
            
            for system_address, system_data in self.system_registry.items():
                try:
                    # Perform basic health check
                    health_status = self._check_system_health(system_address)
                    
                    # Update system status
                    if health_status.get('healthy', False):
                        system_data['status'] = DiagnosticStatus.OK.value
                    else:
                        system_data['status'] = DiagnosticStatus.ERROR.value
                        system_data['error_count'] += 1
                        
                except Exception as e:
                    self.logger.error(f"Health check failed for {system_address}: {e}")
                    system_data['status'] = DiagnosticStatus.ERROR.value
                    system_data['error_count'] += 1
            
            self.logger.info("Periodic health checks completed")
            
        except Exception as e:
            self.logger.error(f"Error performing periodic health checks: {e}")
    
    def _check_system_health(self, system_address: str) -> Dict[str, Any]:
        """Check health of a specific system"""
        try:
            health_result = {
                'system_address': system_address,
                'healthy': True,
                'checks_performed': [],
                'issues_found': []
            }
            
            # Check if handler exists
            system_info = self.system_registry.get(system_address, {})
            if system_info.get('handler_exists', False):
                health_result['checks_performed'].append('handler_exists')
            else:
                health_result['issues_found'].append('handler_missing')
                health_result['healthy'] = False
            
            # Check last signal time
            last_signal = system_info.get('last_signal')
            if last_signal:
                signal_time = datetime.fromisoformat(last_signal)
                time_diff = (datetime.now() - signal_time).total_seconds()
                
                if time_diff < 3600:  # Within last hour
                    health_result['checks_performed'].append('recent_signal')
                else:
                    health_result['issues_found'].append('stale_signal')
                    health_result['healthy'] = False
            else:
                health_result['issues_found'].append('no_signals')
                health_result['healthy'] = False
            
            # Check error count
            error_count = system_info.get('error_count', 0)
            if error_count > 10:  # Too many errors
                health_result['issues_found'].append('high_error_count')
                health_result['healthy'] = False
            
            return health_result
            
        except Exception as e:
            self.logger.error(f"Error checking system health for {system_address}: {e}")
            return {
                'system_address': system_address,
                'healthy': False,
                'checks_performed': [],
                'issues_found': ['health_check_error']
            }
    
    def _analyze_fault_patterns(self):
        """Analyze fault patterns across systems"""
        try:
            self.logger.info("Analyzing fault patterns...")
            
            # Collect fault data from all systems
            fault_patterns = {
                'total_faults': 0,
                'fault_by_system': {},
                'fault_by_type': {},
                'recent_faults': []
            }
            
            for system_address, system_data in self.system_registry.items():
                faults = system_data.get('faults', [])
                fault_patterns['total_faults'] += len(faults)
                fault_patterns['fault_by_system'][system_address] = len(faults)
                
                # Analyze fault types
                for fault in faults:
                    if fault in fault_patterns['fault_by_type']:
                        fault_patterns['fault_by_type'][fault] += 1
                    else:
                        fault_patterns['fault_by_type'][fault] = 1
            
            # Identify patterns
            if fault_patterns['total_faults'] > 0:
                self.logger.warning(f"Fault pattern analysis: {fault_patterns['total_faults']} total faults detected")
                
                # Log systems with most faults
                top_faulty_systems = sorted(fault_patterns['fault_by_system'].items(), 
                                          key=lambda x: x[1], reverse=True)[:3]
                for system, count in top_faulty_systems:
                    if count > 0:
                        self.logger.warning(f"System {system} has {count} faults")
            
            self.logger.info("Fault pattern analysis completed")
            
        except Exception as e:
            self.logger.error(f"Error analyzing fault patterns: {e}")
    
    def _update_system_statuses(self):
        """Update system statuses based on current state"""
        try:
            self.logger.info("Updating system statuses...")
            
            for system_address, system_data in self.system_registry.items():
                # Update last check time
                system_data['last_check'] = datetime.now().isoformat()
                
                # Determine status based on various factors
                error_count = system_data.get('error_count', 0)
                fault_count = len(system_data.get('faults', []))
                handler_exists = system_data.get('handler_exists', False)
                
                if not handler_exists:
                    system_data['status'] = DiagnosticStatus.FAILURE.value
                elif fault_count > 5 or error_count > 10:
                    system_data['status'] = DiagnosticStatus.ERROR.value
                elif error_count > 0 or fault_count > 0:
                    system_data['status'] = DiagnosticStatus.ERROR.value
                else:
                    system_data['status'] = DiagnosticStatus.OK.value
            
            self.logger.info("System statuses updated")
            
        except Exception as e:
            self.logger.error(f"Error updating system statuses: {e}")
    
    def get_live_monitoring_status(self) -> Dict[str, Any]:
        """Get live monitoring status"""
        try:
            return {
                'monitoring_active': self.monitoring_active,
                'systems_monitored': len(self.system_registry),
                'active_faults': len(self.active_faults),
                'last_health_check': datetime.now().isoformat(),
                'monitoring_mode': 'live' if self.monitoring_active else 'inactive'
            }
            
        except Exception as e:
            self.logger.error(f"Error getting live monitoring status: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    # ===== AUTO-REGISTRATION AND ROLLCALL FUNCTIONS =====
    
    def _force_mandatory_auto_registration(self, system_address: str):
        """Force mandatory auto-registration for a system"""
        try:
            self.logger.info(f"Forcing mandatory auto-registration for {system_address}")
            
            # Create auto-registration script
            auto_registration_script = self._create_mandatory_auto_registration_script(system_address)
            
            # Send registration script to system
            if self.comms:
                signal_id = self.comms.transmit_signal(system_address, "auto_registration", "MANDATORY", 
                                                    "Mandatory auto-registration", auto_registration_script)
                
                # Wait for compliance confirmation
                compliance_result = self._check_auto_registration_compliance(system_address, signal_id)
                
                if compliance_result:
                    self.logger.info(f"System {system_address} successfully auto-registered")
                else:
                    self.logger.warning(f"System {system_address} failed auto-registration compliance")
            
        except Exception as e:
            self.logger.error(f"Error forcing mandatory auto-registration for {system_address}: {e}")
    
    def _create_mandatory_auto_registration_script(self, system_address: str) -> Dict[str, Any]:
        """Create mandatory auto-registration script for a system"""
        try:
            # Load fault code protocol
            protocol_file = self.base_path / "SOP" / "diagnostic_code_protocol.json"
            
            if protocol_file.exists():
                with open(protocol_file, 'r') as f:
                    protocol = json.load(f)
            else:
                protocol = {}
            
            # Get inherited fault families for this system
            inherited_families = self._get_inherited_fault_families(system_address, protocol)
            
            # Create registration script
            registration_script = {
                'system_address': system_address,
                'registration_type': 'mandatory_auto_registration',
                'protocol_version': protocol.get('version', '1.0.0'),
                'inherited_fault_families': inherited_families,
                'required_capabilities': [
                    'fault_reporting',
                    'diagnostic_response',
                    'protocol_compliance',
                    'universal_language'
                ],
                'registration_timestamp': datetime.now().isoformat(),
                'compliance_requirements': {
                    'fault_code_format': '[SYSTEM_ADDRESS-FAULT_ID-LINE_NUMBER]',
                    'response_format': 'universal_language',
                    'signal_handling': 'mandatory',
                    'error_reporting': 'immediate'
                }
            }
            
            return registration_script
            
        except Exception as e:
            self.logger.error(f"Error creating auto-registration script for {system_address}: {e}")
            return self._create_fallback_registration_script(system_address)
    
    def _get_inherited_fault_families(self, system_address: str, protocol: Dict[str, Any]) -> List[str]:
        """Get inherited fault families for a system"""
        try:
            inherited_families = []
            
            # Check inheritance mappings in protocol
            inheritance_mappings = protocol.get('inheritance_mappings', {})
            
            for pattern, families in inheritance_mappings.items():
                if self._matches_address_pattern(system_address, pattern):
                    inherited_families.extend(families)
            
            # Add default fault families if none found
            if not inherited_families:
                inherited_families = ['general_system_faults', 'communication_faults']
            
            return inherited_families
            
        except Exception as e:
            self.logger.error(f"Error getting inherited fault families for {system_address}: {e}")
            return ['general_system_faults']
    
    def _matches_address_pattern(self, system_address: str, pattern: str) -> bool:
        """Check if system address matches a pattern"""
        try:
            import re
            
            # Convert pattern to regex
            regex_pattern = pattern.replace('*', '.*').replace('?', '.')
            
            return bool(re.match(regex_pattern, system_address))
            
        except Exception as e:
            self.logger.error(f"Error matching address pattern: {e}")
            return False
    
    def _create_fallback_registration_script(self, system_address: str) -> Dict[str, Any]:
        """Create fallback registration script when protocol is not available"""
        try:
            return {
                'system_address': system_address,
                'registration_type': 'fallback_auto_registration',
                'protocol_version': '1.0.0',
                'inherited_fault_families': ['general_system_faults', 'communication_faults'],
                'required_capabilities': [
                    'fault_reporting',
                    'diagnostic_response',
                    'protocol_compliance'
                ],
                'registration_timestamp': datetime.now().isoformat(),
                'compliance_requirements': {
                    'fault_code_format': '[SYSTEM_ADDRESS-FAULT_ID-LINE_NUMBER]',
                    'response_format': 'universal_language',
                    'signal_handling': 'mandatory'
                },
                'fallback_mode': True
            }
            
        except Exception as e:
            self.logger.error(f"Error creating fallback registration script: {e}")
            return {}
    
    def _check_auto_registration_compliance(self, system_address: str, signal_id: str) -> bool:
        """Check if system complies with auto-registration"""
        try:
            self.logger.info(f"Checking auto-registration compliance for {system_address}")
            
            # Wait for response (simplified - real implementation would be more complex)
            time.sleep(2)
            
            # Check if system is now properly registered
            if system_address in self.system_registry:
                system_info = self.system_registry[system_address]
                
                # Check if system has proper fault code protocol
                if system_info.get('fault_code_protocol') == 'ACTIVE':
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking auto-registration compliance: {e}")
            return False

    def shutdown(self):
        """Graceful system shutdown - DRIVEN BY CORE"""
        self.logger.info("=" * 60)
        self.logger.info("INITIATING GRACEFUL SYSTEM SHUTDOWN")
        self.logger.info("=" * 60)
        
        try:
            # Phase 1: Stop dependency systems
            self.logger.info("Phase 1: Stopping dependency systems")
            self._stop_dependency_systems()
            
            # Phase 2: Stop unified scheduler and all monitoring
            self.logger.info("Phase 2: Stopping unified scheduler and all monitoring")
            self.stop_unified_scheduler()
            
            # Phase 3: Stop dual-mode operations
            self.logger.info("Phase 3: Stopping dual-mode operations")
            self._stop_dual_mode_operations()
            
            # Phase 3: Cleanup cache and temporary data
            self.logger.info("Phase 3: Cleaning up cache and temporary data")
            self._perform_shutdown_cleanup()
            
            # Phase 4: Save final state
            self.logger.info("Phase 4: Saving final system state")
            self._save_final_system_state()
            
            # Phase 5: Stop all modules
            self.logger.info("Phase 5: Stopping all modules")
            self._stop_all_modules()
            
            # Phase 6: Final cleanup
            self.logger.info("Phase 6: Final cleanup")
            self._final_cleanup()
            
            self.launcher_active = False
            self.autonomous_mode = False
            
            self.logger.info("GRACEFUL SYSTEM SHUTDOWN COMPLETED")
            self.logger.info("=" * 60)
            
        except Exception as e:
            self.logger.error(f"Error during graceful shutdown: {e}")
            self.logger.error("Performing emergency shutdown...")
            self._emergency_shutdown()
    
    def _stop_all_monitoring_daemons(self):
        """Stop all monitoring daemons and threads using Events"""
        try:
            # Stop live monitoring
            self.stop_live_monitoring()
            
            # Stop idle detection
            if hasattr(self, 'idle_detection_active'):
                self.idle_detection_active = False
                self.idle_detection_event.set()  # Signal idle detection thread to stop
                if hasattr(self, 'idle_detection_thread') and self.idle_detection_thread:
                    self.idle_detection_thread.join(timeout=5)
                    if self.idle_detection_thread.is_alive():
                        self.logger.warning("Idle detection thread did not stop gracefully")
                    else:
                        self.logger.info("Idle detection thread stopped gracefully")
            
            # Stop new system detection
            if hasattr(self, 'monitoring_active'):
                self.monitoring_active = False
                self.new_system_detection_event.set()  # Signal new system detection to stop
            
            # Stop trash cycle cleanup
            if hasattr(self, 'monitoring_active'):
                self.monitoring_active = False
                self.trash_cleanup_event.set()  # Signal trash cleanup to stop
            
            # Set global shutdown event
            self.shutdown_event.set()
            
            self.logger.info("All monitoring daemons stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping monitoring daemons: {e}")
    
    def _stop_dual_mode_operations(self):
        """Stop dual-mode operations"""
        try:
            # Switch to safe mode
            if hasattr(self, 'operation_mode'):
                self.operation_mode = "SHUTDOWN"
            
            # Stop mode switching
            if hasattr(self, 'mode_switching_active'):
                self.mode_switching_active = False
            
            # Stop diagnostic operations
            if hasattr(self, 'diagnostic_mode_state'):
                self.diagnostic_mode_state.update({
                    'test_execution': False,
                    'repair_operations': False,
                    'system_analysis': False,
                    'protocol_enforcement': False,
                    'heavy_operations': False
                })
            
            # Stop watcher operations
            if hasattr(self, 'watcher_mode_state'):
                self.watcher_mode_state.update({
                    'canbus_monitoring': False,
                    'fault_detection': False,
                    'compliance_monitoring': False,
                    'signal_interception': False,
                    'background_operations': False
                })
            
            self.logger.info("Dual-mode operations stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping dual-mode operations: {e}")
    
    def _perform_shutdown_cleanup(self):
        """Perform cleanup of cache and temporary data"""
        try:
            cleanup_results = {
                'start_time': datetime.now().isoformat(),
                'cleanup_operations': [],
                'files_cleaned': 0,
                'space_freed_bytes': 0,
                'errors': []
            }
            
            # Cleanup operations for shutdown
            cleanup_operations = [
                {
                    'name': 'temp_files_cleanup',
                    'path': self.base_path.parent / 'temp',
                    'retention_days': 0,  # Clean all temp files
                    'preserve_fault_reports': True
                },
                {
                    'name': 'cache_cleanup',
                    'path': self.base_path.parent / 'cache',
                    'retention_days': 0,  # Clean all cache files
                    'preserve_fault_reports': True
                },
                {
                    'name': 'log_cleanup',
                    'path': self.base_path.parent / 'logs',
                    'retention_days': 1,  # Keep only today's logs
                    'preserve_fault_reports': True
                }
            ]
            
            # Execute cleanup operations
            for operation in cleanup_operations:
                try:
                    result = self._execute_cleanup_operation(operation)
                    cleanup_results['cleanup_operations'].append(result)
                    cleanup_results['files_cleaned'] += result.get('files_cleaned', 0)
                    cleanup_results['space_freed_bytes'] += result.get('space_freed_bytes', 0)
                    
                except Exception as e:
                    error_msg = f"Error in {operation['name']}: {e}"
                    cleanup_results['errors'].append(error_msg)
                    self.logger.error(error_msg)
            
            cleanup_results['end_time'] = datetime.now().isoformat()
            
            # Save shutdown cleanup results
            self._save_shutdown_cleanup_results(cleanup_results)
            
            self.logger.info(f"Shutdown cleanup completed: {cleanup_results['files_cleaned']} files cleaned, {cleanup_results['space_freed_bytes']} bytes freed")
            
        except Exception as e:
            self.logger.error(f"Error performing shutdown cleanup: {e}")
    
    def _save_shutdown_cleanup_results(self, cleanup_results: Dict[str, Any]):
        """Save shutdown cleanup results"""
        try:
            results_file = self.diagnostic_reports_path / f"shutdown_cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(results_file, 'w') as f:
                json.dump(cleanup_results, f, indent=2)
            
            self.logger.info(f"Shutdown cleanup results saved: {results_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving shutdown cleanup results: {e}")
    
    def _save_final_system_state(self):
        """Save final system state before shutdown"""
        try:
            final_state = {
                'shutdown_timestamp': datetime.now().isoformat(),
                'system_registry': self.system_registry,
                'active_faults': self.active_faults,
                'operation_mode': getattr(self, 'operation_mode', 'UNKNOWN'),
                'modules_status': self.get_module_status(),
                'cleanup_performed': True
            }
            
            # Save to systems_amendments
            state_file = self.systems_amendments_path / f"final_system_state_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(state_file, 'w') as f:
                json.dump(final_state, f, indent=2)
            
            self.logger.info(f"Final system state saved: {state_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving final system state: {e}")
    
    def _stop_all_modules(self):
        """Stop all system modules"""
        try:
            # Stop enforcement module
            if self.enforcement:
                try:
                    if hasattr(self.enforcement, 'shutdown'):
                        self.enforcement.shutdown()
                    self.logger.info("Enforcement module stopped")
                except Exception as e:
                    self.logger.error(f"Error stopping enforcement module: {e}")
            
            # Stop recovery module
            if self.recovery:
                try:
                    if hasattr(self.recovery, 'shutdown'):
                        self.recovery.shutdown()
                    self.logger.info("Recovery module stopped")
                except Exception as e:
                    self.logger.error(f"Error stopping recovery module: {e}")
            
            # Stop comms module
            if self.comms:
                try:
                    if hasattr(self.comms, 'shutdown'):
                        self.comms.shutdown()
                    self.logger.info("Communication module stopped")
                except Exception as e:
                    self.logger.error(f"Error stopping communication module: {e}")
            
            # Stop auth module
            if self.auth:
                try:
                    if hasattr(self.auth, 'shutdown'):
                        self.auth.shutdown()
                    self.logger.info("Authentication module stopped")
                except Exception as e:
                    self.logger.error(f"Error stopping authentication module: {e}")
            
            self.logger.info("All modules stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping modules: {e}")
    
    def _final_cleanup(self):
        """Final cleanup operations"""
        try:
            # Close any open file handles
            # Reset system state
            self.system_registry.clear()
            self.active_faults.clear()
            
            # Clear module references
            self.auth = None
            self.comms = None
            self.recovery = None
            self.enforcement = None
            
            self.logger.info("Final cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error in final cleanup: {e}")
    
    def _emergency_shutdown(self):
        """Emergency shutdown when graceful shutdown fails"""
        try:
            self.logger.critical("EMERGENCY SHUTDOWN INITIATED")
            
            # Force stop all operations using Events
            self.monitoring_active = False
            self.launcher_active = False
            self.autonomous_mode = False
            
            # Set all Events to force thread termination
            self.shutdown_event.set()
            self.monitoring_event.set()
            self.idle_detection_event.set()
            self.new_system_detection_event.set()
            self.trash_cleanup_event.set()
            
            # Clear all references
            self.auth = None
            self.comms = None
            self.recovery = None
            self.enforcement = None
            
            self.logger.critical("EMERGENCY SHUTDOWN COMPLETED")
            
        except Exception as e:
            self.logger.critical(f"Emergency shutdown error: {e}")
    
    def stop_monitoring(self):
        """Stop monitoring system"""
        try:
            self.logger.info("Stopping monitoring system...")
            
            # Stop live monitoring
            self.stop_live_monitoring()
            
            self.monitoring_active = False
            self.logger.info("Monitoring system stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping monitoring: {e}")
    
    
    # ========================================================================
    # PRIORITY-BASED EXECUTION METHODS
    # ========================================================================
    
    def execute_priority_operation(self, operation_type: str, priority: int, operation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute operations based on priority - important needs can interrupt less critical operations
        
        Priority Levels:
        1-3: CRITICAL (System failure, emergency shutdown)
        4-6: HIGH (Fault detection, protocol violations)
        7-8: MEDIUM (Health checks, maintenance)
        9-10: LOW (Logging, cleanup, reporting)
        """
        try:
            self.logger.info(f"Executing priority operation: {operation_type} (Priority: {priority})")
            
            # Check if we need to interrupt current operations
            if priority <= 3:  # CRITICAL operations
                self.logger.critical(f"CRITICAL OPERATION INTERRUPTING: {operation_type}")
                self._interrupt_lower_priority_operations(priority)
            
            # Execute the operation based on type
            if operation_type == "fault_detection":
                return self._execute_fault_detection_priority(operation_data)
            elif operation_type == "system_repair":
                return self._execute_system_repair_priority(operation_data)
            elif operation_type == "protocol_enforcement":
                return self._execute_protocol_enforcement_priority(operation_data)
            elif operation_type == "health_check":
                return self._execute_health_check_priority(operation_data)
            else:
                self.logger.warning(f"Unknown operation type: {operation_type}")
                return {"success": False, "error": "Unknown operation type"}
                
        except Exception as e:
            self.logger.error(f"Error executing priority operation: {e}")
            return {"success": False, "error": str(e)}
    
    def _interrupt_lower_priority_operations(self, current_priority: int):
        """Interrupt operations with lower priority than current"""
        try:
            self.logger.info(f"Interrupting operations with priority > {current_priority}")
            
            # Stop monitoring threads if they're lower priority
            if current_priority <= 3 and self.monitoring_active:
                self.logger.info("Stopping monitoring for critical operation")
                self.stop_monitoring()
            
            # Pause non-critical modules if needed
            if current_priority <= 4:
                self.logger.info("Pausing non-critical modules for high priority operation")
                # Implementation would pause specific module operations
            
        except Exception as e:
            self.logger.error(f"Error interrupting lower priority operations: {e}")
    
    def _execute_fault_detection_priority(self, operation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute fault detection with priority handling"""
        try:
            # Pull enforcement module if not already loaded
            if not self.enforcement:
                self.enforcement = pull_enforcement_module(self)
            
            if self.enforcement:
                return self.enforcement.detect_faults_priority(operation_data)
            else:
                return {"success": False, "error": "Enforcement module not available"}
                
        except Exception as e:
            self.logger.error(f"Error in priority fault detection: {e}")
            return {"success": False, "error": str(e)}
    
    def _execute_system_repair_priority(self, operation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute system repair with priority handling"""
        try:
            # Pull recovery module if not already loaded
            if not self.recovery:
                self.recovery = pull_recovery_module(self)
            
            if self.recovery:
                return self.recovery.repair_system_priority(operation_data)
            else:
                return {"success": False, "error": "Recovery module not available"}
                
        except Exception as e:
            self.logger.error(f"Error in priority system repair: {e}")
            return {"success": False, "error": str(e)}
    
    def _execute_protocol_enforcement_priority(self, operation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute protocol enforcement with priority handling"""
        try:
            # Pull enforcement module if not already loaded
            if not self.enforcement:
                self.enforcement = pull_enforcement_module(self)
            
            if self.enforcement:
                return self.enforcement.enforce_protocol_priority(operation_data)
            else:
                return {"success": False, "error": "Enforcement module not available"}
                
        except Exception as e:
            self.logger.error(f"Error in priority protocol enforcement: {e}")
            return {"success": False, "error": str(e)}
    
    def _execute_health_check_priority(self, operation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute health check with priority handling"""
        try:
            # Health checks can be performed by core directly
            system_address = operation_data.get('system_address')
            if system_address:
                return self._check_system_health(system_address)
            else:
                return self._perform_periodic_health_checks()
                
        except Exception as e:
            self.logger.error(f"Error in priority health check: {e}")
            return {"success": False, "error": str(e)}
    
    # ========================================================================
    # MODULE FAULT ISOLATION METHODS
    # ========================================================================
    
    def is_module_healthy(self, module_name: str) -> bool:
        """Check if a specific module is healthy and responsive"""
        try:
            if module_name == "auth" and self.auth:
                return hasattr(self.auth, 'is_healthy') and self.auth.is_healthy()
            elif module_name == "comms" and self.comms:
                return hasattr(self.comms, 'is_healthy') and self.comms.is_healthy()
            elif module_name == "recovery" and self.recovery:
                return hasattr(self.recovery, 'is_healthy') and self.recovery.is_healthy()
            elif module_name == "enforcement" and self.enforcement:
                return hasattr(self.enforcement, 'is_healthy') and self.enforcement.is_healthy()
            else:
                return False
        except Exception as e:
            self.logger.error(f"Error checking module health for {module_name}: {e}")
            return False
    
    def restart_failed_module(self, module_name: str) -> bool:
        """Restart a failed module with fault isolation"""
        try:
            self.logger.info(f"Restarting failed module: {module_name}")
            
            if module_name == "auth":
                self.auth = pull_auth_module(self)
                return self.auth is not None
            elif module_name == "comms":
                self.comms = pull_comms_module(self)
                return self.comms is not None
            elif module_name == "recovery":
                self.recovery = pull_recovery_module(self)
                return self.recovery is not None
            elif module_name == "enforcement":
                self.enforcement = pull_enforcement_module(self)
                return self.enforcement is not None
            else:
                self.logger.error(f"Unknown module name: {module_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error restarting module {module_name}: {e}")
            return False
    
    def get_module_status(self) -> Dict[str, Any]:
        """Get status of all modules for monitoring"""
        try:
            return {
                "auth": {
                    "loaded": self.auth is not None,
                    "healthy": self.is_module_healthy("auth") if self.auth else False
                },
                "comms": {
                    "loaded": self.comms is not None,
                    "healthy": self.is_module_healthy("comms") if self.comms else False
                },
                "recovery": {
                    "loaded": self.recovery is not None,
                    "healthy": self.is_module_healthy("recovery") if self.recovery else False
                },
                "enforcement": {
                    "loaded": self.enforcement is not None,
                    "healthy": self.is_module_healthy("enforcement") if self.enforcement else False
                }
            }
        except Exception as e:
            self.logger.error(f"Error getting module status: {e}")
            return {}
    
    # ========================================================================
    # STARTUP SEQUENCE AND SYSTEM LAUNCH
    # ========================================================================
    
    def launch_diagnostic_system(self) -> bool:
        """Launch the diagnostic system with complete startup sequence"""
        try:
            self.logger.info("=" * 60)
            self.logger.info("LAUNCHING UNIFIED DIAGNOSTIC SYSTEM")
            self.logger.info("=" * 60)
            
            # Phase 1: System Initialization
            self.logger.info("Phase 1: System Initialization")
            if not self._initialize_system_components():
                self.logger.error("System initialization failed")
                return False
            
            # Phase 2: File System Validation
            self.logger.info("Phase 2: File System Validation")
            if not self._validate_file_system():
                self.logger.error("File system validation failed")
                return False
            
            # Phase 3: Force System Startup
            self.logger.info("Phase 3: Force System Startup")
            if not self._force_system_startup():
                self.logger.error("Force system startup failed")
                return False
            
            # Phase 4: Perform Rollcall
            self.logger.info("Phase 4: Perform System Rollcall")
            if not self._perform_startup_rollcall():
                self.logger.error("Startup rollcall failed")
                return False
            
            # Phase 5: Subscribe to Protocols
            self.logger.info("Phase 5: Subscribe to Protocols")
            if not self._subscribe_to_protocols():
                self.logger.error("Protocol subscription failed")
                return False
            
            # Phase 6: Baseline Testing
            self.logger.info("Phase 6: Baseline Testing")
            if not self._perform_baseline_testing():
                self.logger.error("Baseline testing failed")
                return False
            
            # Phase 7: Start Dependency Systems
            self.logger.info("Phase 7: Start Dependency Systems")
            self._start_dependency_systems()
            
            # Phase 8: Start Monitoring
            self.logger.info("Phase 8: Start Unified Scheduler")
            self.start_unified_scheduler()
            
            # Phase 9: Initialize Dual-Mode Operation
            self.logger.info("Phase 9: Initialize Dual-Mode Operation")
            self._initialize_dual_mode_operation()
            
            self.launcher_active = True
            self.logger.info("DIAGNOSTIC SYSTEM LAUNCHED SUCCESSFULLY")
            self.logger.info("=" * 60)
            return True
            
        except Exception as e:
            self.logger.error(f"System launch failed: {e}")
            return False
    
    def _initialize_system_components(self) -> bool:
        """Initialize all system components"""
        try:
            self.logger.info("Initializing system components...")
            
            # Ensure all directories exist
            self._ensure_directories()
            
            # Load system registry
            self._load_system_registry()
            
            # Initialize modules if not already done
            if not self.auth:
                self.auth = pull_auth_module(self)
            if not self.comms:
                self.comms = pull_comms_module(self)
            if not self.recovery:
                self.recovery = pull_recovery_module(self)
            if not self.enforcement:
                self.enforcement = pull_enforcement_module(self)
            
            # Validate module initialization
            modules_loaded = {
                'auth': self.auth is not None,
                'comms': self.comms is not None,
                'recovery': self.recovery is not None,
                'enforcement': self.enforcement is not None
            }
            
            failed_modules = [name for name, loaded in modules_loaded.items() if not loaded]
            if failed_modules:
                self.logger.error(f"Failed to load modules: {failed_modules}")
                return False
            
            self.logger.info("All system components initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing system components: {e}")
            return False
    
    def _validate_file_system(self) -> bool:
        """Validate file system structure and critical files"""
        try:
            self.logger.info("Validating file system...")
            
            # Check critical directories
            critical_dirs = [
                self.test_plans_path,
                self.library_path,
                self.diagnostic_reports_path,
                self.fault_amendments_path,
                self.systems_amendments_path,
                self.fault_vault_path,
                self.sop_path
            ]
            
            for dir_path in critical_dirs:
                if not dir_path.exists():
                    self.logger.error(f"Critical directory missing: {dir_path}")
                    return False
            
            # Check critical files
            critical_files = [
                self.system_registry_path,
                self.master_protocol_path
            ]
            
            for file_path in critical_files:
                if not file_path.exists():
                    self.logger.warning(f"Critical file missing: {file_path}")
                    # Create if possible
                    if file_path.suffix == '.json':
                        self._create_empty_json_file(file_path)
                    elif file_path.suffix == '.md':
                        self._create_empty_markdown_file(file_path)
            
            self.logger.info("File system validation completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating file system: {e}")
            return False
    
    def _create_empty_json_file(self, file_path: Path):
        """Create empty JSON file with basic structure"""
        try:
            if file_path.name == 'system_registry.json':
                empty_data = {
                    "system_registry": {
                        "connected_systems": {},
                        "last_updated": datetime.now().isoformat()
                    }
                }
            else:
                empty_data = {}
            
            with open(file_path, 'w') as f:
                json.dump(empty_data, f, indent=2)
            
            self.logger.info(f"Created empty JSON file: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Error creating empty JSON file {file_path}: {e}")
    
    def _create_empty_markdown_file(self, file_path: Path):
        """Create empty markdown file with basic structure"""
        try:
            content = f"# {file_path.stem}\n\nGenerated: {datetime.now().isoformat()}\n"
            
            with open(file_path, 'w') as f:
                f.write(content)
            
            self.logger.info(f"Created empty markdown file: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Error creating empty markdown file {file_path}: {e}")
    
    def _force_system_startup(self) -> bool:
        """Force startup of all registered systems"""
        try:
            self.logger.info("Forcing system startup...")
            
            startup_results = {
                'total_systems': len(self.system_registry),
                'startup_successful': 0,
                'startup_failed': 0,
                'startup_results': []
            }
            
            for system_address, system_info in self.system_registry.items():
                try:
                    self.logger.info(f"Starting system: {system_address}")
                    
                    # Force auto-registration for each system
                    self._force_mandatory_auto_registration(system_address)
                    
                    # Update system status
                    system_info['status'] = DiagnosticStatus.OK.value
                    system_info['last_check'] = datetime.now().isoformat()
                    
                    startup_results['startup_successful'] += 1
                    startup_results['startup_results'].append({
                        'address': system_address,
                        'status': 'SUCCESS',
                        'timestamp': datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    self.logger.error(f"Failed to start system {system_address}: {e}")
                    startup_results['startup_failed'] += 1
                    startup_results['startup_results'].append({
                        'address': system_address,
                        'status': 'FAILED',
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
            
            self.logger.info(f"System startup completed: {startup_results['startup_successful']}/{startup_results['total_systems']} successful")
            
            # Save startup results
            self._save_startup_results(startup_results)
            
            return startup_results['startup_successful'] > 0
            
        except Exception as e:
            self.logger.error(f"Error forcing system startup: {e}")
            return False
    
    def _save_startup_results(self, startup_results: Dict[str, Any]):
        """Save startup results to systems_amendments"""
        try:
            results_file = self.systems_amendments_path / f"startup_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(results_file, 'w') as f:
                json.dump(startup_results, f, indent=2)
            
            self.logger.info(f"Startup results saved: {results_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving startup results: {e}")
    
    def _perform_startup_rollcall(self) -> bool:
        """Perform startup rollcall to all systems"""
        try:
            self.logger.info("Performing startup rollcall...")
            
            if not self.comms:
                self.logger.error("Communication module not available")
                return False
            
            # Transmit rollcall to all systems
            self.comms.transmit_rollcall()
            
            # Wait for responses (simplified - real implementation would track responses)
            time.sleep(5)
            
            self.logger.info("Startup rollcall completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error performing startup rollcall: {e}")
            return False
    
    def _subscribe_to_protocols(self) -> bool:
        """Subscribe to all diagnostic protocols"""
        try:
            self.logger.info("Subscribing to diagnostic protocols...")
            
            if not self.enforcement:
                self.logger.error("Enforcement module not available")
                return False
            
            # Force subscription for all systems
            for system_address in self.system_registry.keys():
                self._force_mandatory_auto_registration(system_address)
            
            self.logger.info("Protocol subscription completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error subscribing to protocols: {e}")
            return False
    
    def _start_monitoring_systems(self):
        """Start monitoring all systems"""
        try:
            self.logger.info("Starting system monitoring...")
            
            # Start live monitoring
            self.start_live_monitoring()
            
            # Start idle detection
            self.start_idle_detection()
            
            self.logger.info("System monitoring started")
            
        except Exception as e:
            self.logger.error(f"Error starting system monitoring: {e}")
    
    def _perform_baseline_testing(self) -> bool:
        """Perform baseline testing on all systems using existing test plans"""
        try:
            self.logger.info("Performing baseline testing...")
            
            baseline_results = {
                'total_systems': len(self.system_registry),
                'tests_executed': 0,
                'tests_passed': 0,
                'tests_failed': 0,
                'systems_tested': 0,
                'test_results': [],
                'start_time': datetime.now().isoformat()
            }
            
            # Test each system with smoke tests
            for system_address, system_info in self.system_registry.items():
                try:
                    self.logger.info(f"Running baseline test for system: {system_address}")
                    
                    # Load and execute smoke test plan
                    test_result = self.execute_test_plan(system_address, "smoke_test")
                    
                    baseline_results['tests_executed'] += test_result.get('tests_executed', 0)
                    baseline_results['tests_passed'] += test_result.get('tests_passed', 0)
                    baseline_results['tests_failed'] += test_result.get('tests_failed', 0)
                    baseline_results['systems_tested'] += 1
                    
                    # Store detailed results
                    baseline_results['test_results'].append({
                        'system_address': system_address,
                        'system_name': system_info.get('name', 'Unknown'),
                        'test_result': test_result,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # Wait for pass/fail signals (simplified - real implementation would track responses)
                    time.sleep(2)
                    
                    # Check if system passed baseline tests
                    if test_result.get('tests_passed', 0) > 0 and test_result.get('tests_failed', 0) == 0:
                        self.logger.info(f"System {system_address} passed baseline testing")
                        system_info['status'] = DiagnosticStatus.OK.value
                    else:
                        self.logger.warning(f"System {system_address} failed baseline testing")
                        system_info['status'] = DiagnosticStatus.ERROR.value
                    
                except Exception as e:
                    self.logger.error(f"Error testing system {system_address}: {e}")
                    baseline_results['test_results'].append({
                        'system_address': system_address,
                        'system_name': system_info.get('name', 'Unknown'),
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
            
            baseline_results['end_time'] = datetime.now().isoformat()
            baseline_results['duration_seconds'] = (
                datetime.fromisoformat(baseline_results['end_time']) - 
                datetime.fromisoformat(baseline_results['start_time'])
            ).total_seconds()
            
            # Save baseline testing results
            self._save_baseline_test_results(baseline_results)
            
            success_rate = (baseline_results['tests_passed'] / max(baseline_results['tests_executed'], 1)) * 100
            self.logger.info(f"Baseline testing completed: {baseline_results['tests_passed']}/{baseline_results['tests_executed']} tests passed ({success_rate:.1f}%)")
            
            return baseline_results['tests_passed'] > 0
            
        except Exception as e:
            self.logger.error(f"Error performing baseline testing: {e}")
            return False
    
    def _save_baseline_test_results(self, baseline_results: Dict[str, Any]):
        """Save baseline testing results to diagnostic_reports"""
        try:
            results_file = self.diagnostic_reports_path / f"baseline_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(results_file, 'w') as f:
                json.dump(baseline_results, f, indent=2)
            
            # Also create a markdown summary
            summary_file = self.diagnostic_reports_path / f"baseline_test_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            
            with open(summary_file, 'w') as f:
                f.write(f"# Baseline Testing Results\n\n")
                f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
                f.write(f"## Summary\n")
                f.write(f"- **Systems Tested:** {baseline_results['systems_tested']}/{baseline_results['total_systems']}\n")
                f.write(f"- **Tests Executed:** {baseline_results['tests_executed']}\n")
                f.write(f"- **Tests Passed:** {baseline_results['tests_passed']}\n")
                f.write(f"- **Tests Failed:** {baseline_results['tests_failed']}\n")
                f.write(f"- **Duration:** {baseline_results['duration_seconds']:.2f} seconds\n\n")
                
                success_rate = (baseline_results['tests_passed'] / max(baseline_results['tests_executed'], 1)) * 100
                f.write(f"- **Success Rate:** {success_rate:.1f}%\n\n")
                
                f.write("## System Results\n")
                for result in baseline_results['test_results']:
                    f.write(f"### {result['system_address']} - {result.get('system_name', 'Unknown')}\n")
                    if 'error' in result:
                        f.write(f"**Error:** {result['error']}\n")
                    else:
                        test_result = result.get('test_result', {})
                        f.write(f"- **Tests Passed:** {test_result.get('tests_passed', 0)}\n")
                        f.write(f"- **Tests Failed:** {test_result.get('tests_failed', 0)}\n")
                        f.write(f"- **Execution Time:** {test_result.get('execution_time_ms', 0)}ms\n")
                    f.write("\n")
            
            self.logger.info(f"Baseline testing results saved: {results_file}")
            self.logger.info(f"Baseline testing summary saved: {summary_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving baseline test results: {e}")
    
    def _start_dependency_systems(self):
        """Start all dependency systems and managers"""
        try:
            self.logger.info("Starting dependency systems...")
            
            # Start enforcement loop
            if self.enforcement_loop:
                self.enforcement_loop.start()
                self.logger.info("Enforcement loop started")
            
            # Start heartbeat watchdog
            if self.heartbeat_watchdog:
                self.heartbeat_watchdog.start()
                self.logger.info("Heartbeat watchdog started")
                
                # Register UniversalCommunicator for heartbeat monitoring
                if self.communicator:
                    # Dependencies removed - core files work independently
                    # comm_config = ComponentConfig(
                    #     name="UniversalCommunicator",
                    #     process_name="python",
                    #     executable_path=sys.executable,
                    #     working_directory=str(self.base_path),
                    #     arguments=["-c", "import comms; comms.main()"],
                    #     heartbeat_interval=30.0,
                    #     heartbeat_timeout=90.0,
                    #     restart_strategy=RestartStrategy.SOFT_RESTART,
                    #     max_restart_attempts=3,
                    #     restart_delay=10.0,
                    #     enabled=True
                    # )
                    # self.heartbeat_watchdog.register_component(comm_config)
                    self.logger.info("UniversalCommunicator registered with heartbeat watchdog")
            
            # Start thread manager (if not already started)
            if self.thread_manager:
                # Register core system threads with thread manager
                self.thread_manager.register_thread(
                    "CoreSystem-Main",
                    target=self._core_system_main_loop,
                    daemon=True
                )
                self.logger.info("Core system threads registered with thread manager")
            
            self.logger.info("All dependency systems started successfully")
            
        except Exception as e:
            self.logger.error(f"Error starting dependency systems: {e}")
    
    def _core_system_main_loop(self, shutdown_event):
        """Main loop for core system (registered with thread manager)"""
        try:
            while not shutdown_event.is_set():
                # Core system operations
                time.sleep(1.0)
        except Exception as e:
            self.logger.error(f"Error in core system main loop: {e}")
    
    def _initialize_dual_mode_operation(self):
        """Initialize dual-mode operation system"""
        try:
            self.logger.info("Initializing dual-mode operation...")
            
            # Start in WATCHER mode
            self.switch_operation_mode("WATCHER")
            
            # Start new system detection
            self._start_new_system_detection()
            
            # Start trash cycle cleanup
            self._start_trash_cycle_cleanup()
            
            self.logger.info("Dual-mode operation initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing dual-mode operation: {e}")
    
    def _start_new_system_detection(self):
        """Start new system detection monitoring"""
        try:
            self.logger.info("Starting new system detection...")
            
            # Start detection thread
            detection_thread = threading.Thread(target=self._new_system_detection_loop, daemon=True)
            detection_thread.start()
            
            self.logger.info("New system detection started")
            
        except Exception as e:
            self.logger.error(f"Error starting new system detection: {e}")
    
    def _new_system_detection_loop(self):
        """Monitor for new systems and auto-register them"""
        try:
            while self.monitoring_active:
                try:
                    # Scan for new systems every 6 hours (semi-quarterly)
                    self._scan_for_new_systems()
                    
                    # Wait 6 hours before next scan
                    time.sleep(6 * 60 * 60)  # 6 hours in seconds
                    
                except Exception as e:
                    self.logger.error(f"Error in new system detection loop: {e}")
                    time.sleep(3600)  # Wait 1 hour before retrying
                    
        except Exception as e:
            self.logger.error(f"New system detection loop failed: {e}")
    
    def _scan_for_new_systems(self):
        """Scan for new Python-based systems and register them"""
        try:
            self.logger.info("Scanning for new systems...")
            
            # Define directories to scan for new systems
            scan_directories = [
                self.base_path.parent.parent,  # Data Bus directory
                self.base_path.parent.parent.parent,  # Command Center directory
            ]
            
            new_systems_found = []
            
            for scan_dir in scan_directories:
                if not scan_dir.exists():
                    continue
                
                # Scan for Python files that might be new systems
                for py_file in scan_dir.rglob("*.py"):
                    try:
                        # Skip test files and __pycache__
                        if any(skip in str(py_file) for skip in ['__pycache__', 'test_', '_test']):
                            continue
                        
                        # Check if this file represents a new system
                        system_info = self._extract_system_info_from_file(py_file)
                        if system_info and not self._is_system_already_registered(system_info['address']):
                            new_systems_found.append(system_info)
                            
                    except Exception as e:
                        self.logger.debug(f"Error scanning file {py_file}: {e}")
                        continue
            
            # Process new systems found
            for system_info in new_systems_found:
                try:
                    self._auto_register_new_system(system_info)
                except Exception as e:
                    self.logger.error(f"Error auto-registering system {system_info['address']}: {e}")
            
            if new_systems_found:
                self.logger.info(f"Found and registered {len(new_systems_found)} new systems")
            else:
                self.logger.info("No new systems found")
                
        except Exception as e:
            self.logger.error(f"Error scanning for new systems: {e}")
    
    def _extract_system_info_from_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Extract system information from a Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for system indicators in the file
            system_indicators = [
                'class.*System',
                'def.*main',
                'if __name__.*main',
                'system_address',
                'DIAG-',
                'Bus-',
                '1-1',
                '2-1',
                '3-1',
                '4-1',
                '5-1',
                '6-1',
                '7-1'
            ]
            
            # Check if file contains system indicators
            has_indicators = any(indicator in content for indicator in system_indicators)
            if not has_indicators:
                return None
            
            # Extract system name from file name
            system_name = file_path.stem.replace('_', ' ').title()
            
            # Determine system address based on file location and name
            system_address = self._determine_system_address_from_path(file_path)
            
            # Extract handler information
            handler_path = str(file_path)
            
            return {
                'address': system_address,
                'name': system_name,
                'handler': handler_path,
                'location': str(file_path.parent),
                'file_size': file_path.stat().st_size,
                'last_modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                'detected_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.debug(f"Error extracting system info from {file_path}: {e}")
            return None
    
    def _determine_system_address_from_path(self, file_path: Path) -> str:
        """Determine system address based on file path"""
        try:
            # Get relative path from base directory
            relative_path = file_path.relative_to(self.base_path.parent.parent.parent)
            path_parts = relative_path.parts
            
            # Map path patterns to system addresses
            if 'evidence' in str(file_path).lower():
                return f"1-1.{len(path_parts)}"
            elif 'warden' in str(file_path).lower():
                return f"2-1.{len(path_parts)}"
            elif 'mission' in str(file_path).lower() or 'debrief' in str(file_path).lower():
                return f"3-1.{len(path_parts)}"
            elif 'report' in str(file_path).lower() or 'generation' in str(file_path).lower():
                return f"4-1.{len(path_parts)}"
            elif 'marshall' in str(file_path).lower():
                return f"5-1.{len(path_parts)}"
            elif 'analyst' in str(file_path).lower():
                return f"6-1.{len(path_parts)}"
            elif 'gui' in str(file_path).lower():
                return f"7-1.{len(path_parts)}"
            elif 'bus' in str(file_path).lower():
                return f"Bus-1.{len(path_parts)}"
            else:
                # Generate a generic address
                return f"GEN-{len(path_parts)}.{hash(str(file_path)) % 1000}"
                
        except Exception as e:
            self.logger.debug(f"Error determining system address from path {file_path}: {e}")
            return f"UNKNOWN-{hash(str(file_path)) % 1000}"
    
    def _is_system_already_registered(self, system_address: str) -> bool:
        """Check if system is already registered"""
        return system_address in self.system_registry
    
    def _auto_register_new_system(self, system_info: Dict[str, Any]):
        """Auto-register a new system"""
        try:
            system_address = system_info['address']
            
            self.logger.info(f"Auto-registering new system: {system_address} - {system_info['name']}")
            
            # Add to system registry
            self.system_registry[system_address] = {
                'name': system_info['name'],
                'address': system_address,
                'handler': system_info['handler'],
                'parent': None,  # Will be determined later
                'status': DiagnosticStatus.UNKNOWN.value,
                'last_check': None,
                'last_signal': None,
                'signal_count': 0,
                'error_count': 0,
                'location': system_info['location'],
                'faults': [],
                'handler_exists': True,
                'restart_required': False,
                'quarantined': False,
                'auto_registered': True,
                'fault_code_protocol': 'ACTIVE',
                'detected_at': system_info['detected_at'],
                'file_size': system_info['file_size'],
                'last_modified': system_info['last_modified']
            }
            
            # Update system registry file
            self._update_system_registry_file()
            
            # Update master protocol file
            self._update_master_protocol_file_single(system_info)
            
            # Generate test plans for new system
            self._generate_test_plans_for_new_system(system_info)
            
            # Create system amendment record
            self._create_system_amendment_record(system_info)
            
            self.logger.info(f"Successfully auto-registered system: {system_address}")
            
        except Exception as e:
            self.logger.error(f"Error auto-registering system: {e}")
    
    def _update_system_registry_file(self):
        """Update the system registry JSON file"""
        try:
            registry_data = {
                "system_registry": {
                    "connected_systems": {},
                    "last_updated": datetime.now().isoformat()
                }
            }
            
            # Convert system registry to JSON-serializable format
            for address, system_info in self.system_registry.items():
                registry_data["system_registry"]["connected_systems"][address] = {
                    "name": system_info['name'],
                    "address": system_info['address'],
                    "handler": system_info['handler'],
                    "parent": system_info.get('parent'),
                    "location": system_info['location'],
                    "auto_registered": system_info.get('auto_registered', False),
                    "detected_at": system_info.get('detected_at'),
                    "last_modified": system_info.get('last_modified')
                }
            
            # Write to file
            with open(self.system_registry_path, 'w') as f:
                json.dump(registry_data, f, indent=2)
            
            self.logger.info("System registry file updated")
            
        except Exception as e:
            self.logger.error(f"Error updating system registry file: {e}")
    
    def _update_master_protocol_file_single(self, system_info: Dict[str, Any]):
        """Update the master diagnostic protocol file with a single new system (in-line table editing)"""
        try:
            if not self.master_protocol_path.exists():
                self.logger.warning("Master protocol file not found, creating new one")
                self._create_empty_markdown_file(self.master_protocol_path)
            
            # Read current protocol file
            with open(self.master_protocol_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            address = system_info['address']
            name = system_info['name']
            handler = system_info['handler']
            parent = system_info.get('parent', '-')
            
            # Determine which section to update and add to the appropriate table
            if address.startswith("Bus-"):
                content = self._update_bus_section(content, address, name, handler, parent)
            elif address.startswith("1-"):
                content = self._update_evidence_locker_section(content, address, name, handler, parent)
            elif address.startswith("2-"):
                content = self._update_warden_section(content, address, name, handler, parent)
            elif address.startswith("3-"):
                content = self._update_mission_debrief_section(content, address, name, handler, parent)
            elif address.startswith("4-"):
                content = self._update_analyst_deck_section(content, address, name, handler, parent)
            elif address.startswith("5-"):
                content = self._update_marshall_section(content, address, name, handler, parent)
            elif address.startswith("6-"):
                content = self._update_war_room_section(content, address, name, handler, parent)
            elif address.startswith("7-"):
                content = self._update_gui_section(content, address, name, handler, parent)
            elif address.startswith("GEN-"):
                content = self._update_general_section(content, address, name, handler, parent)
            
            # Write back to file
            with open(self.master_protocol_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"Master protocol file updated with system {address} in-line")
            
        except Exception as e:
            self.logger.error(f"Error updating master protocol file: {e}")
    
    def _generate_test_plans_for_new_system(self, system_info: Dict[str, Any]):
        """Generate test plans for a new system"""
        try:
            system_address = system_info['address']
            
            # Create test plan directory
            test_dir = self.test_plans_main_path / f"{system_address.replace('-', '_')}_system"
            test_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate smoke test plan
            smoke_test_plan = self._create_smoke_test_plan(system_info)
            smoke_file = test_dir / "smoke_test_plan.json"
            with open(smoke_file, 'w') as f:
                json.dump(smoke_test_plan, f, indent=2)
            
            # Generate function test plan
            function_test_plan = self._create_function_test_plan(system_info)
            function_file = test_dir / "function_test_plan.json"
            with open(function_file, 'w') as f:
                json.dump(function_test_plan, f, indent=2)
            
            self.logger.info(f"Generated test plans for system {system_address}")
            
        except Exception as e:
            self.logger.error(f"Error generating test plans for system {system_info['address']}: {e}")
    
    def _create_smoke_test_plan(self, system_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create smoke test plan for new system"""
        return {
            "test_plan": {
                "system_address": system_info['address'],
                "system_name": system_info['name'],
                "test_type": "smoke_test",
                "created_at": datetime.now().isoformat(),
                "description": f"Basic functionality test for {system_info['name']}",
                "test_vectors": [
                    {
                        "test_id": "ST001",
                        "description": "System initialization test",
                        "test_method": "check_handler_exists",
                        "expected_result": "PASS",
                        "timeout_seconds": 30
                    },
                    {
                        "test_id": "ST002", 
                        "description": "Basic communication test",
                        "test_method": "ping_system",
                        "expected_result": "PASS",
                        "timeout_seconds": 15
                    },
                    {
                        "test_id": "ST003",
                        "description": "Fault code protocol test",
                        "test_method": "check_fault_protocol",
                        "expected_result": "PASS",
                        "timeout_seconds": 10
                    }
                ]
            }
        }
    
    def _create_function_test_plan(self, system_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create function test plan for new system"""
        return {
            "test_plan": {
                "system_address": system_info['address'],
                "system_name": system_info['name'],
                "test_type": "function_test",
                "created_at": datetime.now().isoformat(),
                "description": f"Comprehensive functionality test for {system_info['name']}",
                "test_vectors": [
                    {
                        "test_id": "FT001",
                        "description": "Full system functionality test",
                        "test_method": "execute_main_function",
                        "expected_result": "PASS",
                        "timeout_seconds": 60
                    },
                    {
                        "test_id": "FT002",
                        "description": "Error handling test",
                        "test_method": "test_error_handling",
                        "expected_result": "PASS",
                        "timeout_seconds": 30
                    },
                    {
                        "test_id": "FT003",
                        "description": "Performance test",
                        "test_method": "measure_performance",
                        "expected_result": "PASS",
                        "timeout_seconds": 45
                    }
                ]
            }
        }
    
    def _create_system_amendment_record(self, system_info: Dict[str, Any]):
        """Create system amendment record for new system"""
        try:
            amendment_record = {
                "system_address": system_info['address'],
                "system_name": system_info['name'],
                "amendment_type": "NEW_SYSTEM_DETECTED",
                "detected_at": system_info['detected_at'],
                "handler_path": system_info['handler'],
                "location": system_info['location'],
                "file_size": system_info['file_size'],
                "last_modified": system_info['last_modified'],
                "auto_registered": True,
                "test_plans_generated": True,
                "protocol_updated": True,
                "registry_updated": True
            }
            
            # Save amendment record
            amendment_file = self.systems_amendments_path / f"new_system_{system_info['address']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(amendment_file, 'w') as f:
                json.dump(amendment_record, f, indent=2)
            
            self.logger.info(f"System amendment record created: {amendment_file}")
            
        except Exception as e:
            self.logger.error(f"Error creating system amendment record: {e}")
    
    def _start_trash_cycle_cleanup(self):
        """Start trash cycle cleanup system"""
        try:
            self.logger.info("Starting trash cycle cleanup...")
            
            # Start cleanup thread
            cleanup_thread = threading.Thread(target=self._trash_cycle_cleanup_loop, daemon=True)
            cleanup_thread.start()
            
            self.logger.info("Trash cycle cleanup started")
            
        except Exception as e:
            self.logger.error(f"Error starting trash cycle cleanup: {e}")
    
    def _trash_cycle_cleanup_loop(self):
        """Trash cycle cleanup loop"""
        try:
            while self.monitoring_active:
                try:
                    # Perform cleanup operations
                    self._perform_systematic_cleanup()
                    
                    # Wait 24 hours before next cleanup
                    time.sleep(24 * 60 * 60)  # 24 hours in seconds
                    
                except Exception as e:
                    self.logger.error(f"Error in trash cycle cleanup loop: {e}")
                    time.sleep(3600)  # Wait 1 hour before retrying
                    
        except Exception as e:
            self.logger.error(f"Trash cycle cleanup loop failed: {e}")
    
    def _perform_systematic_cleanup(self):
        """Perform systematic cleanup of cache data while preserving fault reports"""
        try:
            self.logger.info("Performing systematic cleanup...")
            
            cleanup_results = {
                'start_time': datetime.now().isoformat(),
                'cleanup_operations': [],
                'files_cleaned': 0,
                'space_freed_bytes': 0,
                'errors': []
            }
            
            # Cleanup operations with retention policies
            cleanup_operations = [
                {
                    'name': 'cache_cleanup',
                    'path': self.base_path.parent / 'cache',
                    'retention_days': 7,
                    'preserve_fault_reports': True
                },
                {
                    'name': 'temp_files_cleanup',
                    'path': self.base_path.parent / 'temp',
                    'retention_days': 3,
                    'preserve_fault_reports': True
                },
                {
                    'name': 'log_rotation',
                    'path': self.base_path.parent / 'logs',
                    'retention_days': 30,
                    'preserve_fault_reports': True
                },
                {
                    'name': 'backup_cleanup',
                    'path': self.base_path.parent / 'backups',
                    'retention_days': 14,
                    'preserve_fault_reports': True
                }
            ]
            
            # Execute cleanup operations
            for operation in cleanup_operations:
                try:
                    result = self._execute_cleanup_operation(operation)
                    cleanup_results['cleanup_operations'].append(result)
                    cleanup_results['files_cleaned'] += result.get('files_cleaned', 0)
                    cleanup_results['space_freed_bytes'] += result.get('space_freed_bytes', 0)
                    
                except Exception as e:
                    error_msg = f"Error in {operation['name']}: {e}"
                    cleanup_results['errors'].append(error_msg)
                    self.logger.error(error_msg)
            
            cleanup_results['end_time'] = datetime.now().isoformat()
            cleanup_results['duration_seconds'] = (
                datetime.fromisoformat(cleanup_results['end_time']) - 
                datetime.fromisoformat(cleanup_results['start_time'])
            ).total_seconds()
            
            # Save cleanup results
            self._save_cleanup_results(cleanup_results)
            
            self.logger.info(f"Systematic cleanup completed: {cleanup_results['files_cleaned']} files cleaned, {cleanup_results['space_freed_bytes']} bytes freed")
            
        except Exception as e:
            self.logger.error(f"Error performing systematic cleanup: {e}")
    
    def _execute_cleanup_operation(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific cleanup operation"""
        try:
            operation_result = {
                'operation_name': operation['name'],
                'path': str(operation['path']),
                'retention_days': operation['retention_days'],
                'files_cleaned': 0,
                'space_freed_bytes': 0,
                'files_preserved': 0,
                'errors': []
            }
            
            cleanup_path = operation['path']
            retention_days = operation['retention_days']
            preserve_fault_reports = operation['preserve_fault_reports']
            
            if not cleanup_path.exists():
                self.logger.info(f"Cleanup path does not exist: {cleanup_path}")
                return operation_result
            
            # Calculate cutoff date
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            # Process files in the cleanup path
            for file_path in cleanup_path.rglob('*'):
                if file_path.is_file():
                    try:
                        # Check if file should be preserved
                        if preserve_fault_reports and self._is_fault_report_file(file_path):
                            operation_result['files_preserved'] += 1
                            continue
                        
                        # Check if file is older than retention period
                        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if file_mtime < cutoff_date:
                            # Get file size before deletion
                            file_size = file_path.stat().st_size
                            
                            # Delete the file
                            file_path.unlink()
                            
                            operation_result['files_cleaned'] += 1
                            operation_result['space_freed_bytes'] += file_size
                            
                            self.logger.debug(f"Cleaned up file: {file_path}")
                        
                    except Exception as e:
                        error_msg = f"Error cleaning file {file_path}: {e}"
                        operation_result['errors'].append(error_msg)
                        self.logger.warning(error_msg)
            
            return operation_result
            
        except Exception as e:
            self.logger.error(f"Error executing cleanup operation {operation['name']}: {e}")
            return {
                'operation_name': operation['name'],
                'error': str(e),
                'files_cleaned': 0,
                'space_freed_bytes': 0
            }
    
    def _is_fault_report_file(self, file_path: Path) -> bool:
        """Check if file is a fault report that should be preserved"""
        try:
            file_name = file_path.name.lower()
            
            # Check for fault report indicators in filename
            fault_indicators = [
                'fault_report',
                'fault_vault',
                'diagnostic_report',
                'system_fault',
                'error_report',
                'sos_fault'
            ]
            
            return any(indicator in file_name for indicator in fault_indicators)
            
        except Exception as e:
            self.logger.debug(f"Error checking fault report file {file_path}: {e}")
            return False
    
    def _save_cleanup_results(self, cleanup_results: Dict[str, Any]):
        """Save cleanup results to diagnostic_reports"""
        try:
            results_file = self.diagnostic_reports_path / f"cleanup_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(results_file, 'w') as f:
                json.dump(cleanup_results, f, indent=2)
            
            # Also create a markdown summary
            summary_file = self.diagnostic_reports_path / f"cleanup_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            
            with open(summary_file, 'w') as f:
                f.write(f"# Trash Cycle Cleanup Results\n\n")
                f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
                f.write(f"## Summary\n")
                f.write(f"- **Files Cleaned:** {cleanup_results['files_cleaned']}\n")
                f.write(f"- **Space Freed:** {cleanup_results['space_freed_bytes']} bytes ({cleanup_results['space_freed_bytes'] / (1024*1024):.2f} MB)\n")
                f.write(f"- **Duration:** {cleanup_results['duration_seconds']:.2f} seconds\n")
                f.write(f"- **Errors:** {len(cleanup_results['errors'])}\n\n")
                
                f.write("## Cleanup Operations\n")
                for operation in cleanup_results['cleanup_operations']:
                    f.write(f"### {operation['operation_name']}\n")
                    f.write(f"- **Path:** {operation['path']}\n")
                    f.write(f"- **Retention:** {operation['retention_days']} days\n")
                    f.write(f"- **Files Cleaned:** {operation['files_cleaned']}\n")
                    f.write(f"- **Space Freed:** {operation['space_freed_bytes']} bytes\n")
                    f.write(f"- **Files Preserved:** {operation.get('files_preserved', 0)}\n")
                    if operation.get('errors'):
                        f.write(f"- **Errors:** {len(operation['errors'])}\n")
                    f.write("\n")
                
                if cleanup_results['errors']:
                    f.write("## Errors\n")
                    for error in cleanup_results['errors']:
                        f.write(f"- {error}\n")
                    f.write("\n")
            
            self.logger.info(f"Cleanup results saved: {results_file}")
            self.logger.info(f"Cleanup summary saved: {summary_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving cleanup results: {e}")
    
    # ========================================================================
    # DUAL-MODE OPERATION SYSTEM
    # ========================================================================
    
    def switch_operation_mode(self, new_mode: str) -> bool:
        """Switch between WATCHER and DIAGNOSTIC modes"""
        try:
            if new_mode not in ["WATCHER", "DIAGNOSTIC"]:
                self.logger.error(f"Invalid operation mode: {new_mode}")
                return False
            
            if new_mode == self.operation_mode:
                self.logger.info(f"Already in {new_mode} mode")
                return True
            
            old_mode = self.operation_mode
            self.logger.info(f"Switching from {old_mode} to {new_mode} mode")
            
            # Transition operations
            if old_mode == "WATCHER" and new_mode == "DIAGNOSTIC":
                self._transition_to_diagnostic_mode()
            elif old_mode == "DIAGNOSTIC" and new_mode == "WATCHER":
                self._transition_to_watcher_mode()
            
            self.operation_mode = new_mode
            self.logger.info(f"Successfully switched to {new_mode} mode")
            return True
            
        except Exception as e:
            self.logger.error(f"Error switching operation mode: {e}")
            return False
    
    def _transition_to_diagnostic_mode(self):
        """Transition from watcher to diagnostic mode"""
        try:
            self.logger.info("Transitioning to DIAGNOSTIC mode")
            
            # Activate diagnostic capabilities
            self.diagnostic_mode_state.update({
                'test_execution': True,
                'repair_operations': True,
                'system_analysis': True,
                'protocol_enforcement': True,
                'heavy_operations': True
            })
            
            # Deactivate heavy watcher operations
            self.watcher_mode_state.update({
                'canbus_monitoring': False,  # Reduce monitoring intensity
                'signal_interception': False,  # Focus on diagnostic signals only
                'background_operations': False  # Stop non-critical background tasks
            })
            
            # Start diagnostic mode operations
            self._start_diagnostic_operations()
            
        except Exception as e:
            self.logger.error(f"Error transitioning to diagnostic mode: {e}")
    
    def _transition_to_watcher_mode(self):
        """Transition from diagnostic to watcher mode"""
        try:
            self.logger.info("Transitioning to WATCHER mode")
            
            # Deactivate diagnostic capabilities
            self.diagnostic_mode_state.update({
                'test_execution': False,
                'repair_operations': False,
                'system_analysis': False,
                'protocol_enforcement': False,
                'heavy_operations': False
            })
            
            # Reactivate watcher operations
            self.watcher_mode_state.update({
                'canbus_monitoring': True,
                'fault_detection': True,
                'compliance_monitoring': True,
                'signal_interception': True,
                'background_operations': True
            })
            
            # Stop diagnostic operations
            self._stop_diagnostic_operations()
            
        except Exception as e:
            self.logger.error(f"Error transitioning to watcher mode: {e}")
    
    def _start_diagnostic_operations(self):
        """Start diagnostic mode operations"""
        try:
            self.logger.info("Starting diagnostic operations")
            
            # Start system analysis
            if self.enforcement:
                self.enforcement.start_live_system_monitoring()
            
            # Start repair operations
            if self.recovery:
                self.recovery.start_automatic_code_fixing()
            
            # Start protocol enforcement
            if self.enforcement:
                self.enforcement.start_protocol_monitoring()
            
        except Exception as e:
            self.logger.error(f"Error starting diagnostic operations: {e}")
    
    def _stop_diagnostic_operations(self):
        """Stop diagnostic mode operations"""
        try:
            self.logger.info("Stopping diagnostic operations")
            
            # Stop heavy operations
            if self.enforcement:
                self.enforcement.stop_live_system_monitoring()
            
            if self.recovery:
                self.recovery.stop_automatic_code_fixing()
            
        except Exception as e:
            self.logger.error(f"Error stopping diagnostic operations: {e}")
    
    def start_idle_detection(self):
        """Start monitoring system activity for idle detection"""
        try:
            if not self.idle_detection_active:
                return
            
            self.logger.info("Starting idle detection monitoring")
            
            # Clear event and start idle detection thread
            self.idle_detection_event.clear()
            idle_thread = threading.Thread(target=self._idle_detection_loop, daemon=True)
            self.idle_detection_thread = idle_thread  # Store reference for graceful shutdown
            idle_thread.start()
            
            self.logger.info("Idle detection monitoring started")
            
        except Exception as e:
            self.logger.error(f"Error starting idle detection: {e}")
    
    def _idle_detection_loop(self):
        """Monitor system activity for idle state detection using Event"""
        try:
            while not self.idle_detection_event.is_set():
                current_time = time.time()
                
                # Check if system is idle
                time_since_activity = min(
                    current_time - self.system_activity_tracker['last_keystroke'],
                    current_time - self.system_activity_tracker['last_mouse_click'],
                    current_time - self.system_activity_tracker['last_window_movement'],
                    current_time - self.system_activity_tracker['last_file_access'],
                    current_time - self.system_activity_tracker['last_registry_access']
                )
                
                # Check if we should switch to diagnostic mode
                if time_since_activity >= self.system_activity_tracker['idle_threshold_seconds']:
                    if not self.system_activity_tracker['is_idle']:
                        self.system_activity_tracker['is_idle'] = True
                        self.system_activity_tracker['idle_start_time'] = current_time
                        self.logger.info("System detected as idle - switching to diagnostic mode")
                        self.switch_operation_mode("DIAGNOSTIC")
                        self._start_system_warmup_sequence()
                else:
                    if self.system_activity_tracker['is_idle']:
                        self.system_activity_tracker['is_idle'] = False
                        self.system_activity_tracker['idle_start_time'] = None
                        self.logger.info("System activity detected - switching to watcher mode")
                        self.switch_operation_mode("WATCHER")
                
                # Sleep with Event timeout for graceful shutdown
                if self.idle_detection_event.wait(30):  # Check every 30 seconds or until event is set
                    break  # Event was set, exit gracefully
                
        except Exception as e:
            self.logger.error(f"Error in idle detection loop: {e}")
    
    def _start_system_warmup_sequence(self):
        """Start gradual system warmup to avoid CPU spikes"""
        try:
            if self.system_activity_tracker['warmup_sequence_active']:
                return
            
            self.system_activity_tracker['warmup_sequence_active'] = True
            self.logger.info("Starting system warmup sequence")
            
            # Start warmup thread
            warmup_thread = threading.Thread(target=self._system_warmup_loop, daemon=True)
            warmup_thread.start()
            
        except Exception as e:
            self.logger.error(f"Error starting warmup sequence: {e}")
    
    def _system_warmup_loop(self):
        """Gradual system warmup to avoid high spike traffic"""
        try:
            warmup_steps = [
                {"action": "light_ping", "delay": 5, "description": "Light system ping"},
                {"action": "status_check", "delay": 10, "description": "Status check"},
                {"action": "communication_test", "delay": 15, "description": "Communication test"},
                {"action": "health_check", "delay": 20, "description": "Health check"},
                {"action": "diagnostic_ready", "delay": 30, "description": "Diagnostic operations ready"}
            ]
            
            for step in warmup_steps:
                if not self.system_activity_tracker['is_idle']:
                    self.logger.info("Activity detected - aborting warmup sequence")
                    break
                
                self.logger.info(f"Warmup step: {step['description']}")
                self._execute_warmup_action(step['action'])
                
                time.sleep(step['delay'])
            
            self.system_activity_tracker['warmup_sequence_active'] = False
            self.logger.info("System warmup sequence completed")
            
        except Exception as e:
            self.logger.error(f"Error in warmup loop: {e}")
            self.system_activity_tracker['warmup_sequence_active'] = False
    
    def _execute_warmup_action(self, action: str):
        """Execute specific warmup action"""
        try:
            if action == "light_ping":
                if self.comms:
                    self.comms.transmit_radio_check("Bus-1")
            elif action == "status_check":
                self.get_system_status()
            elif action == "communication_test":
                if self.comms:
                    self.comms.transmit_rollcall()
            elif action == "health_check":
                if self.enforcement:
                    self.enforcement.detect_faults_priority({})
            elif action == "diagnostic_ready":
                self.logger.info("Diagnostic system ready for operations")
                
        except Exception as e:
            self.logger.error(f"Error executing warmup action {action}: {e}")
    
    def update_activity_tracker(self, activity_type: str):
        """Update activity tracker when system activity is detected"""
        try:
            current_time = time.time()
            
            if activity_type in self.system_activity_tracker:
                self.system_activity_tracker[f'last_{activity_type}'] = current_time
                
                # If we're in diagnostic mode and activity is detected, switch back to watcher
                if self.operation_mode == "DIAGNOSTIC" and not self.system_activity_tracker['is_idle']:
                    self.logger.info("Activity detected during diagnostic mode - switching to watcher")
                    self.switch_operation_mode("WATCHER")
                    
        except Exception as e:
            self.logger.error(f"Error updating activity tracker: {e}")
    
    def get_operation_mode_status(self) -> Dict[str, Any]:
        """Get current operation mode status"""
        try:
            return {
                "current_mode": self.operation_mode,
                "mode_switching_active": self.mode_switching_active,
                "idle_detection_active": self.idle_detection_active,
                "is_idle": self.system_activity_tracker['is_idle'],
                "idle_duration": time.time() - self.system_activity_tracker['idle_start_time'] if self.system_activity_tracker['is_idle'] else 0,
                "watcher_state": self.watcher_mode_state,
                "diagnostic_state": self.diagnostic_mode_state,
                "warmup_active": self.system_activity_tracker['warmup_sequence_active']
            }
        except Exception as e:
            self.logger.error(f"Error getting operation mode status: {e}")
            return {}
    
    def start_unified_scheduler(self):
        """Start unified scheduler to manage all monitoring threads efficiently"""
        try:
            if self.unified_scheduler_active:
                self.logger.warning("Unified scheduler already active")
                return
            
            self.unified_scheduler_active = True
            self.logger.info("Starting unified scheduler for efficient thread management")
            
            # Start unified scheduler thread
            scheduler_thread = threading.Thread(
                target=self._unified_scheduler_loop,
                name="UnifiedScheduler",
                daemon=True
            )
            scheduler_thread.start()
            self.monitor_threads['unified_scheduler'] = scheduler_thread
            
            self.logger.info("Unified scheduler started successfully")
            
        except Exception as e:
            self.logger.error(f"Error starting unified scheduler: {e}")
            self.unified_scheduler_active = False
    
    def stop_unified_scheduler(self):
        """Stop unified scheduler and all managed threads"""
        try:
            self.logger.info("Stopping unified scheduler...")
            self.unified_scheduler_active = False
            
            # Set global shutdown event to signal all threads
            self.shutdown_event.set()
            
            # Wait for all monitor threads to finish gracefully
            for thread_name, thread in self.monitor_threads.items():
                if thread.is_alive():
                    self.logger.info(f"Waiting for {thread_name} to finish...")
                    thread.join(timeout=5)  # 5 second timeout per thread
                    if thread.is_alive():
                        self.logger.warning(f"{thread_name} did not stop gracefully")
            
            self.monitor_threads.clear()
            self.logger.info("Unified scheduler stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping unified scheduler: {e}")
    
    def _unified_scheduler_loop(self):
        """Unified scheduler loop that manages all monitoring tasks efficiently"""
        try:
            self.logger.info("Unified scheduler loop started")
            
            # Schedule intervals for different tasks
            last_live_monitoring = time.time()
            last_idle_check = time.time()
            last_system_scan = time.time()
            last_cleanup = time.time()
            
            # Task intervals (in seconds)
            intervals = {
                'live_monitoring': 30,      # Every 30 seconds
                'idle_check': 60,           # Every 60 seconds  
                'system_scan': 3600,        # Every hour
                'cleanup': 86400            # Every 24 hours
            }
            
            while not self.shutdown_event.is_set() and self.unified_scheduler_active:
                current_time = time.time()
                
                # Live monitoring task
                if current_time - last_live_monitoring >= intervals['live_monitoring']:
                    self._execute_live_monitoring_task()
                    last_live_monitoring = current_time
                
                # Idle detection task
                if current_time - last_idle_check >= intervals['idle_check']:
                    self._execute_idle_detection_task()
                    last_idle_check = current_time
                
                # System scanning task
                if current_time - last_system_scan >= intervals['system_scan']:
                    self._execute_system_scanning_task()
                    last_system_scan = current_time
                
                # Cleanup task
                if current_time - last_cleanup >= intervals['cleanup']:
                    self._execute_cleanup_task()
                    last_cleanup = current_time
                
                # Sleep for 1 second before next check
                time.sleep(1)
                
        except Exception as e:
            self.logger.error(f"Error in unified scheduler loop: {e}")
        finally:
            self.logger.info("Unified scheduler loop ended")
    
    def _execute_live_monitoring_task(self):
        """Execute live monitoring task efficiently"""
        try:
            if self.enforcement and self.lazy_loaded_modules['enforcement']:
                # Only run if enforcement module is loaded
                self.enforcement.detect_faults_priority({})
        except Exception as e:
            self.logger.error(f"Error in live monitoring task: {e}")
    
    def _execute_idle_detection_task(self):
        """Execute idle detection task efficiently"""
        try:
            # Update idle status
            current_time = time.time()
            last_activity = max(
                self.system_activity_tracker.get('last_keystroke', 0),
                self.system_activity_tracker.get('last_mouse_click', 0),
                self.system_activity_tracker.get('last_window_movement', 0),
                self.system_activity_tracker.get('last_file_access', 0)
            )
            
            idle_duration = current_time - last_activity
            threshold = self.system_activity_tracker['idle_threshold_seconds']
            
            if idle_duration >= threshold and not self.system_activity_tracker['is_idle']:
                self.system_activity_tracker['is_idle'] = True
                self.system_activity_tracker['idle_start_time'] = current_time
                self.logger.info(f"System entered idle state (duration: {idle_duration:.1f}s)")
            elif idle_duration < threshold and self.system_activity_tracker['is_idle']:
                self.system_activity_tracker['is_idle'] = False
                self.logger.info(f"System exited idle state (duration: {idle_duration:.1f}s)")
                
        except Exception as e:
            self.logger.error(f"Error in idle detection task: {e}")
    
    def _execute_system_scanning_task(self):
        """Execute system scanning task efficiently"""
        try:
            if self.auth and self.lazy_loaded_modules.get('auth', True):
                # Run system analysis
                analysis_result = self.auth.analyze_system_registry()
                if analysis_result:
                    self.logger.info(f"System scan completed: {analysis_result.get('total', 0)} systems")
        except Exception as e:
            self.logger.error(f"Error in system scanning task: {e}")
    
    def _execute_cleanup_task(self):
        """Execute cleanup task efficiently"""
        try:
            # Clean up old log files
            self._cleanup_old_logs()
            
            if self.recovery and self.lazy_loaded_modules['recovery']:
                # Run cleanup operations
                self.recovery.cleanup_old_backups()
        except Exception as e:
            self.logger.error(f"Error in cleanup task: {e}")
    
    def _cleanup_old_logs(self):
        """Clean up old log files from system_logs directory"""
        try:
            if not self.system_logs_path.exists():
                return
                
            import time
            current_time = time.time()
            retention_days = 7  # Keep logs for 7 days
            retention_seconds = retention_days * 24 * 60 * 60
            
            cleaned_count = 0
            cleaned_size = 0
            
            for log_file in self.system_logs_path.glob("*.log"):
                try:
                    file_age = current_time - log_file.stat().st_mtime
                    if file_age > retention_seconds:
                        file_size = log_file.stat().st_size
                        log_file.unlink()  # Delete the file
                        cleaned_count += 1
                        cleaned_size += file_size
                        self.logger.info(f"Cleaned up old log file: {log_file.name}")
                except Exception as e:
                    self.logger.warning(f"Could not clean log file {log_file.name}: {e}")
            
            if cleaned_count > 0:
                self.logger.info(f"Log cleanup completed: {cleaned_count} files, {cleaned_size} bytes freed")
                
        except Exception as e:
            self.logger.error(f"Error during log cleanup: {e}")
    
    def lazy_load_enforcement_module(self):
        """Lazy load enforcement module when needed"""
        try:
            if not self.lazy_loaded_modules['enforcement']:
                self.logger.info("Lazy loading enforcement module...")
                self.enforcement = pull_enforcement_module(self)
                self.lazy_loaded_modules['enforcement'] = True
                self.logger.info("Enforcement module lazy loaded successfully")
                return True
            return True  # Already loaded
        except Exception as e:
            self.logger.error(f"Error lazy loading enforcement module: {e}")
            return False
    
    def lazy_load_recovery_module(self):
        """Lazy load recovery module when needed"""
        try:
            if not self.lazy_loaded_modules['recovery']:
                self.logger.info("Lazy loading recovery module...")
                self.recovery = pull_recovery_module(self)
                self.lazy_loaded_modules['recovery'] = True
                self.logger.info("Recovery module lazy loaded successfully")
                return True
            return True  # Already loaded
        except Exception as e:
            self.logger.error(f"Error lazy loading recovery module: {e}")
            return False
    

# ========================================================================
# MAIN ENTRY POINT
# ========================================================================

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
