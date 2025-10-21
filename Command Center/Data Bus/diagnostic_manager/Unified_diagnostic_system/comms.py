"""
Communication Module - Unified Diagnostic System
Handles bus communication, signal handling, and universal language enforcement

Author: Central Command System
Date: 2025-10-07
Version: 2.0.0 - MODULAR ARCHITECTURE
"""

import os
import sys
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

# Add paths for bus integration
current_dir = Path(__file__).parent
# Go up to diagnostic_manager, then to parent (Data Bus), then to Bus Core Design
bus_core_path = current_dir.parent.parent / "Bus Core Design"
data_bus_path = current_dir.parent.parent
sys.path.insert(0, str(bus_core_path))
sys.path.insert(0, str(data_bus_path))

try:
    from bus_core import DKIReportBus
    from universal_communicator import UniversalCommunicator, SignalType, RadioCode
    BUS_AVAILABLE = True
except ImportError as e:
    print(f"Bus integration not available: {e}")
    DKIReportBus = None
    UniversalCommunicator = None
    SignalType = None
    RadioCode = None
    BUS_AVAILABLE = False


# RadioCode and SignalType are imported from universal_communicator


@dataclass
class DiagnosticPayload:
    """Standardized diagnostic payload structure"""
    operation: str
    data: Dict[str, Any]
    metadata: Dict[str, Any] = None
    validation_checksum: str = ""
    priority: int = 5
    timestamp: str = ""


@dataclass
class CommunicationSignal:
    """Standard communication signal format"""
    signal_id: str
    caller_address: str
    target_address: str
    bus_address: str = "Bus-1"
    signal_type: str = "communication"
    radio_code: str = "10-4"
    message: str = ""
    payload: DiagnosticPayload = None
    response_expected: bool = False
    timeout: int = 30
    timestamp: str = ""


class CommsSystem:
    """
    Communication System Module
    
    Responsibilities:
    - Bus communication and signal handling
    - Universal language enforcement
    - Radio codes and protocol compliance
    - Signal interception and routing
    - Payload management and validation
    - Fault code protocol enforcement
    """
    
    def __init__(self, orchestrator=None, bus_connection=None, communicator=None):
        """Initialize communication system with CAN-BUS connection"""
        self.orchestrator = orchestrator
        self.bus = bus_connection
        self.communicator = communicator
        self.bus_connected = bus_connection is not None
        self.logger = logging.getLogger("CommsSystem")
        
        # Redirect bus core log to system_logs directory if bus is available
        if self.bus_connected:
            system_logs_path = Path(__file__).parent / "library" / "system_logs"
            system_logs_path.mkdir(parents=True, exist_ok=True)
            # Update bus core log path to use system_logs directory
            bus_log_path = system_logs_path / "dki_bus_core.log"
            if hasattr(self.bus, 'log_file_path'):
                self.bus.log_file_path = str(bus_log_path)
                self.logger.info(f"Bus core log redirected to: {self.bus.log_file_path}")
            else:
                # Create a custom logger for bus core if it doesn't have log_file_path
                bus_logger = logging.getLogger("bus_core")
                bus_handler = logging.FileHandler(bus_log_path, mode='a', encoding='utf-8')
                bus_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
                bus_logger.addHandler(bus_handler)
                self.logger.info(f"Bus core logger created at: {bus_log_path}")
        
        # Bus integration (use provided connections)
        if not self.bus_connected:
            self.bus = None
            self.communicator = None
        
        # Communication state
        self.pending_responses = {}
        self.signal_counter = 0
        self.signal_interceptor = None
        self.parent_map = {}
        self.parent_children_map = {}
        self.root_addresses = set()
        
        # Protocol enforcement
        self.protocol_file = None
        self.fault_code_protocol = {}
        
        # Initialize
        # CRITICAL: Only connect to bus if no bus was provided (fallback mode)
        if not self.bus_connected:
            self.logger.warning("No bus provided, creating fallback bus connection")
            self._connect_to_bus()
        else:
            # Use provided bus - register handlers on shared bus
            self.logger.info("Using provided shared bus connection")
            self._register_diagnostic_signals()
        
        self._load_fault_code_protocol()
        
        # Initialize real system response handlers
        self._initialize_system_response_handlers()
        self._build_parent_map()
        if self.bus_connected:
            self._initialize_subscriptions()
        
        self.logger.info("Communication system initialized")
    
    def _initialize_system_response_handlers(self):
        """Initialize real system response handlers for forced subscription"""
        self.logger.info("INITIALIZING REAL SYSTEM RESPONSE HANDLERS")
        
        # Response handler state
        self.response_handlers = {
            'subscription_responses': {},
            'rollcall_responses': {},
            'radio_check_responses': {},
            'status_responses': {},
            'fault_responses': {},
            'compliance_responses': {}
        }
        
        # Response tracking
        self.pending_responses = {}
        self.response_timeouts = {}
        
        # Real system communication protocols
        self.system_protocols = {
            'forced_subscription': True,
            'mandatory_handshake': True,
            'compliance_enforcement': True,
            'real_time_monitoring': True
        }
        
        self.logger.info("Real system response handlers initialized")
    

    def _build_parent_map(self):
        """Map subsystem addresses to their parent controllers."""
        self.parent_map = {}
        self.parent_children_map = {}
        self.root_addresses = set()

        registry = {}
        try:
            if self.orchestrator and hasattr(self.orchestrator, 'system_registry'):
                registry = self.orchestrator.system_registry
                if callable(registry):
                    registry = registry()
        except Exception as exc:
            self.logger.warning(f"Unable to load system registry for parent mapping: {exc}")
            registry = {}

        if not registry:
            return

        for address, info in registry.items():
            parent = info.get('parent') if isinstance(info, dict) else getattr(info, 'parent', None)
            if parent:
                self.parent_map[address] = parent
                self.parent_children_map.setdefault(parent, set()).add(address)
            else:
                self.root_addresses.add(address)

        for parent in self.parent_children_map.keys():
            self.root_addresses.add(parent)

    def _resolve_signal_target(self, address: str) -> str:
        """Resolve signal destination to the appropriate parent module."""
        if not address or address.upper() == "ALL" or address.startswith("Bus-") or address == "DIAG-1":
            return address
        return self.parent_map.get(address, address)

    def _initialize_subscriptions(self):
        """Send subscription notices to parent controllers on the bus."""
        if not self.bus_connected or not self.bus:
            return

        targets = set(getattr(self, 'root_addresses', set()))
        targets.add('Bus-1')
        targets.discard('DIAG-1')

        for target in sorted(targets):
            payload = {
                'signal_id': f"SUB-{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                'system_address': 'DIAG-1',
                'parent_address': target,
                'child_addresses': sorted(self.parent_children_map.get(target, set())),
                'timestamp': datetime.now().isoformat()
            }
            try:
                self.bus.send('diagnostic.subscription', payload)
                self.logger.info(f"Subscription request sent to {target}")
            except Exception as exc:
                self.logger.error(f"Failed to send subscription to {target}: {exc}")

    def _connect_to_bus(self):
        """Connect to DKI Report Bus"""
        if not BUS_AVAILABLE:
            self.logger.warning("Bus integration not available")
            return
        
        try:
            self.bus = DKIReportBus()
            self.communicator = UniversalCommunicator("DIAG-1", bus_connection=self.bus)
            self.bus_connected = True
            
            # Register diagnostic signals
            self._register_diagnostic_signals()
            
            self.logger.info("Connected to DKI Report Bus")
        except Exception as e:
            self.logger.error(f"Error connecting to bus: {e}")
            self.bus_connected = False
    
    def _register_diagnostic_signals(self):
        """Register diagnostic signal handlers"""
        if not self.bus:
            return
        
        try:
            # CRITICAL: Register 'communication' handler (where UniversalCommunicator actually sends)
            self.bus.register_signal('communication', self._handle_communication_signal)
            
            # Register diagnostic signal handlers
            self.bus.register_signal('diagnostic.rollcall', self._handle_rollcall)
            self.bus.register_signal('fault.report', self._handle_fault_report)
            self.bus.register_signal('fault.sos', self._handle_sos_fault)  # Keep for legacy
            self.bus.register_signal('system.fault', self._handle_system_fault)
            self.bus.register_signal('error.report', self._handle_error_report)
            self.bus.register_signal('subscription.response', self._handle_subscription_response)
            self.bus.register_signal('diagnostic.subscription', self._handle_subscription_response)
            
            # BIDIRECTIONAL COMM FIX (2025-10-12): Register response handlers for UDS requests
            self.bus.register_signal('rollcall_response', self._handle_rollcall_response)
            self.bus.register_signal('radio_check_response', self._handle_radio_check_response)
            self.bus.register_signal('auto_registration', self._handle_auto_registration_response)
            self.bus.register_signal('response', self._handle_generic_response)  # Generic response handler
            # Note: Self-test completion signals handled within _handle_communication_signal
            
            self.logger.info("Registered diagnostic signal handlers on SHARED BUS (including 'communication' and response handlers)")
        except Exception as e:
            self.logger.error(f"Error registering signals: {e}")
    
    def _load_fault_code_protocol(self):
        """Load fault code protocol from JSON"""
        if self.orchestrator and hasattr(self.orchestrator, 'core'):
            protocol_path = self.orchestrator.core.sop_path / "diagnostic_code_protocol.json"
        else:
            protocol_path = Path(__file__).parent / "SOP" / "diagnostic_code_protocol.json"
        
        if protocol_path.exists():
            try:
                with open(protocol_path, 'r') as f:
                    self.fault_code_protocol = json.load(f)
                self.logger.info("Loaded fault code protocol")
            except Exception as e:
                self.logger.error(f"Error loading fault code protocol: {e}")
    
    def validate_fault_code(self, fault: Dict[str, Any]) -> str:
        """
        Validate fault against JSON protocol rules
        Returns standardized fault code format: [ADDRESS-XX-LINE]
        """
        if not self.fault_code_protocol:
            self.logger.warning("Fault code protocol not loaded")
            return "PROTOCOL_NOT_LOADED"
        
        address = fault.get('address')
        code = fault.get('code')
        instance = fault.get('instance', 'unknown')
        
        # Validate against protocol rules
        if 'system_addresses' in self.fault_code_protocol:
            if address not in self.fault_code_protocol['system_addresses']:
                return "INVALID_ADDRESS"
        
        if 'fault_codes' in self.fault_code_protocol:
            if code not in self.fault_code_protocol['fault_codes']:
                return "INVALID_CODE"
        
        # Return standardized format
        return f"[{address}-{code}-{instance}]"
    
    def transmit_signal(self, target_address: str, signal_type: SignalType, 
                       radio_code: RadioCode, message: str = "", 
                       payload: DiagnosticPayload = None) -> bool:
        """Transmit signal to target system"""
        if not self.bus_connected:
            self.logger.warning("Cannot transmit - bus not connected")
            return False
        
        self.signal_counter += 1
        signal = CommunicationSignal(
            signal_id=f"DIAG-{self.signal_counter}",
            caller_address="DIAG-1",
            target_address=target_address,
            signal_type=signal_type.value,
            radio_code=radio_code.value,
            message=message,
            payload=payload,
            timestamp=datetime.now().isoformat()
        )
        
        try:
            # Send via bus - sender must be in data dict, not separate parameter
            self.bus.send(
                signal_type.value,
                {
                    'signal_id': signal.signal_id,
                    'sender': 'DIAG-1',
                    'caller_address': 'DIAG-1',
                    'target_address': target_address,
                    'radio_code': signal.radio_code,
                    'message': signal.message,
                    'payload': payload.__dict__ if payload else None
                }
            )
            
            self.logger.info(f"Transmitted signal to {target_address}: {radio_code.value}")
            return True
        except Exception as e:
            self.logger.error(f"Error transmitting signal: {e}")
            return False
    
    def transmit_rollcall(self) -> bool:
        """Broadcast rollcall to all systems"""
        return self.transmit_signal(
            target_address="ALL",
            signal_type="diagnostic.rollcall",  # FIX: Use diagnostic prefix string
            radio_code=RadioCode.ROLLCALL,
            message="All systems respond with status"
        )
    
    def transmit_radio_check(self, target_address: str) -> bool:
        """Send radio check to specific system"""
        return self.transmit_signal(
            target_address=target_address,
            signal_type="diagnostic.radio_check",  # FIX: Use diagnostic prefix string
            radio_code=RadioCode.RADIO_CHECK,
            message="Communication test"
        )
    
    def _handle_rollcall(self, signal_data: Dict[str, Any]):
        """Handle rollcall signal with real response processing"""
        self.logger.info("Received rollcall signal")
        
        # Store rollcall response for compliance tracking
        sender = signal_data.get('sender', 'UNKNOWN')
        self.response_handlers['rollcall_responses'][sender] = {
            'payload': signal_data,
            'timestamp': datetime.now().isoformat(),
            'status': 'received',
            'compliance_status': 'compliant'
        }
        
        # Respond with diagnostic system status
        if self.orchestrator and hasattr(self.orchestrator, 'core'):
            status = self.orchestrator.core.get_system_status()
            response_payload = {
                'system_address': 'DIAG-1',
                'status': 'OPERATIONAL',
                'active_faults': len(status.get('active_faults', {})),
                'compliance_status': 'COMPLIANT',
                'protocol_version': '1.0.0'
            }
            
            self.transmit_signal(
                target_address=signal_data.get('sender', 'Bus-1'),
                signal_type=SignalType.RESPONSE,
                radio_code=RadioCode.ACKNOWLEDGED,
                message=f"Diagnostic system operational: {status['active_faults']} active faults",
                payload=response_payload
            )
            
            # Update response tracking
            self.response_handlers['rollcall_responses'][sender]['response_sent'] = True
            self.response_handlers['rollcall_responses'][sender]['response_payload'] = response_payload
    
    def _handle_subscription_response(self, signal_data: Dict[str, Any]):
        """Handle subscription response from systems"""
        self.logger.info(f"Received subscription response: {signal_data}")
        
        # Extract system information
        sender = signal_data.get('sender', 'UNKNOWN')
        payload = signal_data.get('payload', {})
        
        # Store subscription response
        self.response_handlers['subscription_responses'][sender] = {
            'payload': signal_data,
            'timestamp': datetime.now().isoformat(),
            'status': 'subscribed',
            'protocol_version': payload.get('protocol_version', 'unknown'),
            'compliance_status': payload.get('compliance_status', 'unknown')
        }
        
        # Notify enforcement system of successful subscription
        if self.orchestrator and hasattr(self.orchestrator, 'enforcement') and self.orchestrator.enforcement:
            self.orchestrator.enforcement._handle_subscription_success(sender, payload)
        
        # Send acknowledgment
        ack_payload = {
            'subscription_status': 'ACCEPTED',
            'system_address': sender,
            'diagnostic_address': 'DIAG-1',
            'compliance_enforcement': 'ACTIVE',
            'monitoring_status': 'ENABLED'
        }
        
        self.transmit_signal(
            target_address=sender,
            signal_type=SignalType.RESPONSE,
            radio_code=RadioCode.ACKNOWLEDGED,
            message="Subscription accepted - compliance monitoring enabled",
            payload=ack_payload
        )
        
        self.logger.info(f"System {sender} successfully subscribed to diagnostic protocol")
    
    def _handle_self_test_complete(self, signal_data: Dict[str, Any]):
        """Handle self-test completion signals from parent modules (via communication topic)"""
        try:
            # Extract payload from UniversalCommunicator signal structure
            payload = signal_data.get('payload', {})
            
            # Check if this is a self-test completion signal
            operation = payload.get('operation', '')
            if operation != 'self_test_complete':
                # Not a self-test signal, ignore
                return
            
            # Extract self-test completion data
            system_address = payload.get('system_address', signal_data.get('caller_address', 'UNKNOWN'))
            test_result = payload.get('test_result', 'UNKNOWN')
            system_name = payload.get('system_name', 'Unknown System')
            children_tested = payload.get('children_tested', 0)
            
            # Track completion
            if 'self_test_completions' not in self.response_handlers:
                self.response_handlers['self_test_completions'] = {}
            
            self.response_handlers['self_test_completions'][system_address] = {
                'test_result': test_result,
                'system_name': system_name,
                'children_tested': children_tested,
                'timestamp': datetime.now().isoformat(),
                'signal_data': signal_data
            }
            
            self.logger.info(f"[UDS] Self-test complete from {system_address} ({system_name}): {test_result} - {children_tested} children tested")
            
        except Exception as e:
            self.logger.error(f"[UDS] Error handling self-test completion: {e}")
    
    def _handle_generic_response(self, signal_data: Dict[str, Any]):
        """Handle generic response signals (acknowledgments from systems)"""
        try:
            sender = signal_data.get('sender') or signal_data.get('source_address') or signal_data.get('caller_address') or signal_data.get('system_address', 'UNKNOWN')
            radio_code = signal_data.get('radio_code', '')
            payload = signal_data.get('payload', {})
            message = signal_data.get('message', '')
            
            # Log response for tracking
            self.logger.debug(f"[UDS] Received response from {sender} [{radio_code}]: {message}")
            
            # Update tracking
            if 'generic_responses' not in self.response_handlers:
                self.response_handlers['generic_responses'] = {}
            
            self.response_handlers['generic_responses'][sender] = {
                'payload': signal_data,
                'timestamp': datetime.now().isoformat(),
                'radio_code': radio_code,
                'message': message
            }
            
        except Exception as e:
            self.logger.error(f"[UDS] Error handling generic response: {e}")
    
    def _handle_rollcall_response(self, signal_data: Dict[str, Any]):
        """Handle rollcall response from systems (BIDIRECTIONAL COMM FIX 2025-10-12)"""
        try:
            sender = signal_data.get('sender') or signal_data.get('source_address') or signal_data.get('caller_address') or signal_data.get('system_address', 'UNKNOWN')
            radio_code = signal_data.get('radio_code', '')
            payload = signal_data.get('payload', {})
            
            # Validate response
            if not sender or sender == 'UNKNOWN':
                self.logger.warning("[UDS] Invalid rollcall response: missing sender (received: %s)", signal_data.keys())
                return
            
            # Update tracking
            self.response_handlers['rollcall_responses'][sender] = {
                'payload': signal_data,
                'timestamp': datetime.now().isoformat(),
                'radio_code': radio_code,
                'status': payload.get('status', 'UNKNOWN'),
                'compliance_status': payload.get('compliance_status', 'UNKNOWN')
            }
            
            # Notify enforcement module (if initialized)
            if self.orchestrator and hasattr(self.orchestrator, 'enforcement') and self.orchestrator.enforcement:
                self.orchestrator.enforcement.process_rollcall_response(signal_data)
            
            self.logger.info(f"[UDS] Received rollcall response from {sender} [{radio_code}] - Status: {payload.get('status', 'N/A')}")
            
        except Exception as e:
            self.logger.error(f"[UDS] Error handling rollcall response: {e}")
    
    def _handle_radio_check_response(self, signal_data: Dict[str, Any]):
        """Handle radio check response from systems (BIDIRECTIONAL COMM FIX 2025-10-12)"""
        try:
            sender = signal_data.get('source_address') or signal_data.get('sender') or signal_data.get('caller_address') or signal_data.get('system_address', 'UNKNOWN')
            radio_code = signal_data.get('radio_code', '')
            payload = signal_data.get('payload', {})
            
            # Validate response
            if not sender or sender == 'UNKNOWN':
                self.logger.warning("[UDS] Invalid radio check response: missing sender (received: %s)", signal_data.keys())
                return
            
            # Update tracking
            self.response_handlers['radio_check_responses'][sender] = {
                'payload': signal_data,
                'timestamp': datetime.now().isoformat(),
                'radio_code': radio_code,
                'latency_ms': payload.get('latency_ms', 0),
                'signal_strength': payload.get('signal_strength', 'UNKNOWN')
            }
            
            # Update system connectivity status in enforcement
            if self.orchestrator and hasattr(self.orchestrator, 'enforcement') and self.orchestrator.enforcement:
                connectivity_data = {
                    'system_address': sender,
                    'radio_code': radio_code,
                    'latency_ms': payload.get('latency_ms', 0),
                    'timestamp': datetime.now().isoformat(),
                    'status': 'CONNECTED'
                }
                self.orchestrator.enforcement.update_connectivity_status(connectivity_data)
            
            self.logger.info(f"[UDS] Received radio check response from {sender} [{radio_code}] - Latency: {payload.get('latency_ms', 'N/A')}ms")
            
        except Exception as e:
            self.logger.error(f"[UDS] Error handling radio check response: {e}")
    
    def _handle_auto_registration_response(self, signal_data: Dict[str, Any]):
        """Handle auto-registration response from systems (BIDIRECTIONAL COMM FIX 2025-10-12)
        
        CRITICAL: This handler receives confirmation that a system has completed auto-registration.
        Without this handler, UDS waits indefinitely for responses that are never processed.
        
        LIFECYCLE FIX: Only processes CALL_ANSWERED messages to prevent infinite loops.
        """
        try:
            # Check message lifecycle state - only process responses
            message_state = signal_data.get('message_state', '')
            if message_state != "CALL_ANSWERED":
                # Ignore requests, only process answers
                return
            
            sender = signal_data.get('source_address') or signal_data.get('sender') or signal_data.get('caller_address') or signal_data.get('system_address', 'UNKNOWN')
            radio_code = signal_data.get('radio_code', '')
            payload = signal_data.get('payload', {})
            
            # Validate response
            if not sender or sender == 'UNKNOWN':
                self.logger.warning("[UDS] Invalid auto-registration response: missing sender (received: %s)", signal_data.keys())
                return
            
            # Extract system metadata
            system_metadata = {
                'system_address': sender,
                'system_name': payload.get('system_name', 'UNKNOWN'),
                'capabilities': payload.get('capabilities', []),
                'protocol_version': payload.get('protocol_version', 'unknown'),
                'compliance_status': payload.get('compliance_status', 'PENDING'),
                'parent_address': payload.get('parent_address', None),
                'registration_timestamp': datetime.now().isoformat()
            }
            
            # Notify enforcement module with confirmed registration
            if self.orchestrator and hasattr(self.orchestrator, 'enforcement') and self.orchestrator.enforcement:
                self.orchestrator.enforcement.process_registration_confirmation(system_metadata)
                self.logger.info(f"[UDS] Auto-registration confirmed for {sender} [{radio_code}] - Compliance: {system_metadata['compliance_status']}")
            else:
                self.logger.warning(f"[UDS] Enforcement module not ready - registration for {sender} received but not confirmed")
            
            # Don't send acknowledgment - modules already know registration succeeded
            # Sending a response creates infinite loop: module responds → UDS acks → module sees ack as new request → repeat
            # The module confirmation IS the handshake completion - no ACK needed
            self.logger.debug(f"[UDS] Auto-registration handshake complete for {sender} - no ACK sent (prevents feedback loop)")
            
        except Exception as e:
            self.logger.error(f"[UDS] Error handling auto-registration response: {e}")
    
    def _handle_fault_report(self, signal_data: Dict[str, Any]):
        """Handle fault report signal"""
        self.logger.info(f"Received fault report: {signal_data}")
        
        # Authenticate fault report
        if self.orchestrator and hasattr(self.orchestrator, 'auth') and self.orchestrator.auth:
            if not self.orchestrator.auth.authenticate_fault_report(signal_data):
                self.logger.warning("Fault report authentication failed")
                return
        
        # Route to enforcement for processing
        if self.orchestrator and hasattr(self.orchestrator, 'enforcement') and self.orchestrator.enforcement:
            self.orchestrator.enforcement.process_fault_report(signal_data)
    
    def _handle_sos_fault(self, signal_data: Dict[str, Any]):
        """Handle SOS fault signal (emergency)"""
        fault_code = signal_data.get('fault_code', 'UNKNOWN')
        caller_address = signal_data.get('caller_address', signal_data.get('parent_address', 'UNKNOWN'))
        component = signal_data.get('component', 'Unknown Component')
        
        self.logger.critical(
            f"[UDS] SOS FAULT RECEIVED: {fault_code} from {caller_address} (component: {component})"
        )
        
        # FIRST: Record the fault to system_registry via process_fault_report
        if self.orchestrator and hasattr(self.orchestrator, 'enforcement') and self.orchestrator.enforcement:
            # Ensure fault data has parent_address for registry lookup
            if 'parent_address' not in signal_data and 'caller_address' in signal_data:
                signal_data['parent_address'] = signal_data['caller_address']
            
            # Process fault report (adds to system_registry and consolidation buffer)
            self.orchestrator.enforcement.process_fault_report(signal_data)
            
            self.logger.info(
                f"[UDS] Fault recorded to system registry: {fault_code} from {caller_address}"
            )
        else:
            self.logger.warning(
                f"[UDS] Enforcement module not ready - fault {fault_code} from {caller_address} received but not logged (UDS still initializing)"
            )
    
    def _handle_system_fault(self, signal_data: Dict[str, Any]):
        """Handle system fault signal"""
        self.logger.error(f"Received system fault: {signal_data}")
        
        # Route to enforcement for processing
        if self.orchestrator and hasattr(self.orchestrator, 'enforcement') and self.orchestrator.enforcement:
            self.orchestrator.enforcement.process_system_fault(signal_data)
    
    def _handle_error_report(self, signal_data: Dict[str, Any]):
        """Handle error report signal"""
        self.logger.warning(f"Received error report: {signal_data}")
        
        # Route to enforcement for monitoring
        if self.orchestrator and hasattr(self.orchestrator, 'enforcement') and self.orchestrator.enforcement:
            self.orchestrator.enforcement.process_error_report(signal_data)
    
    def _handle_communication_signal(self, signal_data: Dict[str, Any]):
        """
        Handle incoming communication signals and route based on radio_code.
        This is the PRIMARY signal handler for UniversalCommunicator messages.
        """
        try:
            target_address = signal_data.get('target_address')
            
            # Only process signals directed at UDS (DIAG-1 or Bus-1)
            if target_address not in ["Bus-1", "DIAG-1"]:
                return
            
            radio_code = signal_data.get('radio_code')
            caller_address = signal_data.get('caller_address')
            payload = signal_data.get('payload', {})
            
            self.logger.debug(
                f"[Comms] Communication signal received: {radio_code} from {caller_address}"
            )
            
            # Route based on radio_code
            if radio_code == "SOS":
                self.logger.critical(
                    f"[Comms] SOS signal from {caller_address} - routing to fault handler"
                )
                # Extract fault payload and route to _handle_sos_fault
                self._handle_sos_fault(payload if payload else signal_data)
            
            elif radio_code == "MAYDAY":
                self.logger.critical(f"[Comms] MAYDAY from {caller_address}")
                self._handle_system_fault(payload if payload else signal_data)
            
            elif radio_code == "ROLLCALL":
                self.logger.debug(f"[Comms] ROLLCALL from {caller_address}")
                self._handle_rollcall(signal_data)
            
            elif radio_code in ["10-4", "10-6", "10-8", "10-9", "10-10"]:
                self.logger.debug(f"[Comms] Status: {radio_code} from {caller_address}")
                
                # Check if this is a self-test completion signal
                if payload.get('operation') == 'self_test_complete':
                    self._handle_self_test_complete(signal_data)
                # Other status codes are informational, no action needed
            
            else:
                self.logger.warning(f"[Comms] Unknown radio_code: {radio_code} from {caller_address}")
        
        except Exception as e:
            self.logger.error(f"[Comms] Error handling communication signal: {e}", exc_info=True)
    
    def get_communication_status(self) -> Dict[str, Any]:
        """Pull communication system status"""
        return {
            'bus_connected': self.bus_connected,
            'signals_sent': self.signal_counter,
            'pending_responses': len(self.pending_responses),
            'protocol_loaded': bool(self.fault_code_protocol),
            'signal_handlers_registered': self.bus is not None
        }
    
    def create_diagnostic_payload(self, operation: str, data: Dict[str, Any], 
                                metadata: Dict[str, Any] = None, priority: int = 5,
                                retention_days: int = 30, compression: str = "none",
                                encryption: str = "none") -> Dict[str, Any]:
        """Create a standardized diagnostic payload"""
        import hashlib
        import json
        
        # Create metadata if not provided
        if metadata is None:
            metadata = {
                'created_by': 'DIAG-1',
                'system_version': '1.0.0',
                'payload_type': 'diagnostic',
                'source_module': 'unified_diagnostic_system'
            }
        
        # Calculate payload size
        data_json = json.dumps(data, sort_keys=True)
        size_bytes = len(data_json.encode('utf-8'))
        
        # Generate validation checksum
        checksum_data = f"{operation}:{data_json}:{json.dumps(metadata, sort_keys=True)}"
        validation_checksum = hashlib.md5(checksum_data.encode('utf-8')).hexdigest()
        
        payload = {
            'operation': operation,
            'data': data,
            'metadata': metadata,
            'validation_checksum': validation_checksum,
            'size_bytes': size_bytes,
            'compression': compression,
            'encryption': encryption,
            'priority': priority,
            'retention_days': retention_days,
            'timestamp': datetime.now().isoformat()
        }
        
        self.logger.info(f"Created diagnostic payload: {operation} ({size_bytes} bytes)")
        return payload
    
    def validate_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validate payload integrity and format"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'checksum_valid': False,
            'size_acceptable': False,
            'format_valid': False
        }
        
        try:
            # Check required fields
            required_fields = ['operation', 'data', 'metadata', 'validation_checksum']
            for field in required_fields:
                if field not in payload:
                    validation_result['errors'].append(f"Missing required field: {field}")
                    validation_result['valid'] = False
            
            # Validate checksum
            if 'validation_checksum' in payload:
                import hashlib
                import json
                
                checksum_data = f"{payload['operation']}:{json.dumps(payload['data'], sort_keys=True)}:{json.dumps(payload['metadata'], sort_keys=True)}"
                expected_checksum = hashlib.md5(checksum_data.encode('utf-8')).hexdigest()
                
                if payload['validation_checksum'] == expected_checksum:
                    validation_result['checksum_valid'] = True
                else:
                    validation_result['errors'].append("Checksum validation failed")
                    validation_result['valid'] = False
            
            # Check size limits
            max_size = 1024 * 1024  # 1MB limit
            if payload.get('size_bytes', 0) <= max_size:
                validation_result['size_acceptable'] = True
            else:
                validation_result['warnings'].append(f"Payload size {payload.get('size_bytes', 0)} exceeds recommended limit of {max_size}")
            
            # Check format validity
            if payload.get('operation') and payload.get('data'):
                validation_result['format_valid'] = True
            else:
                validation_result['errors'].append("Invalid payload format")
                validation_result['valid'] = False
            
            self.logger.info(f"Payload validation: {validation_result['valid']} - {len(validation_result['errors'])} errors, {len(validation_result['warnings'])} warnings")
            
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Validation error: {str(e)}")
            self.logger.error(f"Payload validation failed: {e}")
        
        return validation_result
    
    def transmit_rollcall(self) -> List[str]:
        """Transmit rollcall to all systems"""
        signal_ids = []
        
        if self.orchestrator and hasattr(self.orchestrator, 'system_registry'):
            for address in self.orchestrator.system_registry.keys():
                signal_id = self.transmit_signal(
                    target_address=address,
                    signal_type="diagnostic.rollcall",  # FIX: Use diagnostic prefix
                    radio_code=RadioCode.ROLLCALL.value,
                    message="Rollcall - please respond with status",
                    response_expected=True,
                    timeout=60
                )
                if signal_id:
                    signal_ids.append(signal_id)
        
        self.logger.info(f"Rollcall transmitted to {len(signal_ids)} systems")
        return signal_ids
    
    def transmit_radio_check(self, target_address: str) -> str:
        """Transmit radio check to specific system"""
        return self.transmit_signal(
            target_address=target_address,
            signal_type="diagnostic.radio_check",  # FIX: Use diagnostic prefix
            radio_code=RadioCode.RADIO_CHECK.value,
            message=f"Radio check to {target_address}",
            response_expected=True,
            timeout=30
        )
    
    def transmit_sos_fault(self, system_address: str, fault_code: str, description: str) -> str:
        """Transmit SOS fault signal"""
        return self.transmit_signal(
            target_address="DIAG-1",
            signal_type=SignalType.SOS_FAULT.value,
            radio_code=RadioCode.SOS.value,
            message=f"SOS fault from {system_address}",
            payload={
                'operation': 'sos_fault',
                'fault_code': fault_code,
                'description': description,
                'system_address': system_address,
                'timestamp': datetime.now().isoformat()
            },
            response_expected=True,
            timeout=5
        )
    
    def transmit_signal(self, target_address: str, signal_type: str, radio_code: str, 
                       message: str, payload: Dict[str, Any] = None, 
                       response_expected: bool = False, timeout: int = 30,
                       message_state: str = "CALL_SENT") -> str:
        """Transmit signal to target system with message lifecycle state"""
        try:
            signal_type_value = signal_type.value if hasattr(signal_type, 'value') else signal_type
            radio_code_value = radio_code.value if hasattr(radio_code, 'value') else radio_code

            original_target = target_address
            resolved_target = self._resolve_signal_target(original_target)
            if resolved_target != original_target:
                self.logger.debug(f"Routing signal for {original_target} through parent {resolved_target}")

            signal_id = f"SIG-{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

            payload_data = dict(payload) if payload else {}
            payload_data.setdefault('target_subsystem', original_target)

            signal_data = {
                'signal_id': signal_id,
                'source_address': 'DIAG-1',
                'target_address': resolved_target,
                'original_target_address': original_target,
                'signal_type': signal_type_value,
                'radio_code': radio_code_value,
                'message': message,
                'message_state': message_state,
                'payload': payload_data,
                'response_expected': response_expected,
                'timeout': timeout,
                'timestamp': datetime.now().isoformat()
            }

            if self.bus_connected and self.bus:
                self.bus.send(signal_type_value, signal_data)
                self.logger.info(f"Signal transmitted via bus: {signal_type_value} to {resolved_target}")
            else:
                self.logger.warning("Cannot transmit - no communicator available")

            if response_expected:
                self.pending_responses[signal_id] = {
                    'signal_data': signal_data,
                    'sent_time': datetime.now(),
                    'timeout': timeout
                }

            self.signal_counter += 1
            return signal_id

        except Exception as e:
            self.logger.error(f"Signal transmission failed: {e}")
            return ""
    
    def archive_payload(self, signal_id: str, payload: Dict[str, Any]):
        """Archive payload for record keeping"""
        try:
            # Get diagnostic reports path from orchestrator
            if self.orchestrator and hasattr(self.orchestrator, 'diagnostic_reports_path'):
                diagnostic_reports_path = self.orchestrator.diagnostic_reports_path
            else:
                diagnostic_reports_path = Path(__file__).parent / "library" / "diagnostic_reports"
                diagnostic_reports_path.mkdir(parents=True, exist_ok=True)
            
            archive_file = diagnostic_reports_path / f"payload_archive_{signal_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(archive_file, 'w') as f:
                json.dump({
                    'signal_id': signal_id,
                    'payload': payload,
                    'archived_at': datetime.now().isoformat()
                }, f, indent=2)
            
            self.logger.info(f"Payload archived: {archive_file}")
            
        except Exception as e:
            self.logger.error(f"Error archiving payload: {e}")

