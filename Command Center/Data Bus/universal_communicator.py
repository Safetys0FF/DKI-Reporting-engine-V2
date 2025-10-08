#!/usr/bin/env python3
"""
Universal Communicator - Central Command Communication Protocol
Implements the Universal Communication Protocol for all system communications
"""

import os
import sys
import json
import time
import threading
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class RadioCode(Enum):
    """Standard radio communication codes"""
    ACKNOWLEDGED = "10-4"           # Message received and understood
    EVIDENCE_RECEIVED = "10-6"      # Evidence received and being processed
    EVIDENCE_COMPLETE = "10-8"      # Evidence processing complete
    REPEAT = "10-9"                 # Please repeat last message
    STANDBY = "10-10"               # Processing in progress
    SOS = "SOS"                     # Emergency - system failure
    MAYDAY = "MAYDAY"               # Critical failure - system down
    STATUS = "STATUS"               # Status request
    ROLLCALL = "ROLLCALL"           # All systems respond
    RADIO_CHECK = "RADIO_CHECK"     # Communication test


class SignalType(Enum):
    """Signal types for communication"""
    COMMUNICATION = "communication"
    RESPONSE = "response"
    SOS_FAULT = "sos_fault"
    ROLLCALL = "rollcall"
    RADIO_CHECK = "radio_check"
    STATUS_REQUEST = "status_request"


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
    payload: Dict[str, Any] = None
    response_expected: bool = False
    timeout: int = 30
    timestamp: str = ""


class UniversalCommunicator:
    """
    Universal Communicator - Central Command Communication Protocol
    
    Provides standardized communication across all systems using:
    - Radio codes for status communication
    - Signal-based architecture
    - Fault reporting and emergency protocols
    - System registration and addressing
    """
    
    def __init__(self, system_address: str, bus_connection=None):
        """Initialize Universal Communicator"""
        self.system_address = system_address
        self.bus_connection = bus_connection
        self.communication_log: List[CommunicationSignal] = []
        self.registered_systems: Dict[str, Dict[str, Any]] = {}
        self.active_signals: Dict[str, CommunicationSignal] = {}
        self.signal_counter = 0
        
        # Setup logging
        self.logger = logging.getLogger(f'UniversalCommunicator-{system_address}')
        
        # Register this system
        self.registered_systems[system_address] = {
            'name': f'System {system_address}',
            'address': system_address,
            'status': 'ACTIVE',
            'last_communication': datetime.now().isoformat()
        }
        
        self.logger.info(f"Universal Communicator initialized for {system_address}")
    
    def send_signal(self, target_address: str, radio_code: str, message: str = "", 
                   payload: Dict[str, Any] = None, timeout: int = 30) -> str:
        """Send communication signal to target system"""
        self.signal_counter += 1
        signal_id = f"{self.system_address}-{self.signal_counter}-{int(time.time())}"
        
        signal = CommunicationSignal(
            signal_id=signal_id,
            caller_address=self.system_address,
            target_address=target_address,
            bus_address="Bus-1",
            signal_type="communication",
            radio_code=radio_code,
            message=message,
            payload=payload or {},
            response_expected=True,
            timeout=timeout,
            timestamp=datetime.now().isoformat()
        )
        
        # Log signal
        self.communication_log.append(signal)
        self.active_signals[signal_id] = signal
        
        # Route through bus if available
        if self.bus_connection:
            try:
                self.bus_connection.send('communication', {
                    'signal_id': signal_id,
                    'caller_address': self.system_address,
                    'target_address': target_address,
                    'bus_address': 'Bus-1',
                    'signal_type': 'communication',
                    'radio_code': radio_code,
                    'message': message,
                    'payload': payload or {},
                    'response_expected': True,
                    'timeout': timeout,
                    'timestamp': signal.timestamp
                })
                self.logger.info(f"Signal sent: {signal_id} -> {target_address}")
            except Exception as e:
                self.logger.error(f"Failed to send signal: {e}")
                return None
        else:
            self.logger.warning("No bus connection available")
        
        return signal_id
    
    def send_radio_check(self, target_address: str) -> str:
        """Send radio check signal"""
        return self.send_signal(
            target_address=target_address,
            radio_code=RadioCode.RADIO_CHECK.value,
            message=f"Radio check from {self.system_address}",
            timeout=5
        )
    
    def send_status_request(self, target_address: str) -> str:
        """Send status request signal"""
        return self.send_signal(
            target_address=target_address,
            radio_code=RadioCode.STATUS.value,
            message=f"Status request from {self.system_address}",
            timeout=10
        )
    
    def send_rollcall(self) -> str:
        """Send rollcall signal to all systems"""
        return self.send_signal(
            target_address="ALL",
            radio_code=RadioCode.ROLLCALL.value,
            message=f"Rollcall from {self.system_address}",
            timeout=15
        )
    
    def send_sos_fault(self, fault_code: str, description: str) -> str:
        """Send SOS fault signal"""
        return self.send_signal(
            target_address="Bus-1",
            radio_code=RadioCode.SOS.value,
            message=f"SOS fault from {self.system_address}",
            payload={
                'fault_code': fault_code,
                'description': description,
                'reporting_address': self.system_address,
                'severity': 'CRITICAL'
            },
            timeout=5
        )
    
    def send_response(self, original_signal_id: str, radio_code: str, message: str = "", 
                     payload: Dict[str, Any] = None) -> str:
        """Send response to original signal"""
        if original_signal_id in self.active_signals:
            original_signal = self.active_signals[original_signal_id]
            
            response_signal_id = self.send_signal(
                target_address=original_signal.caller_address,
                radio_code=radio_code,
                message=message,
                payload=payload,
                timeout=30
            )
            
            # Remove from active signals
            del self.active_signals[original_signal_id]
            
            return response_signal_id
        else:
            self.logger.error(f"Original signal {original_signal_id} not found")
            return None
    
    def register_system_address(self, address: str, system_info: Dict[str, Any] = None):
        """Register a system address"""
        self.registered_systems[address] = system_info or {
            'name': f'System {address}',
            'address': address,
            'status': 'ACTIVE',
            'last_communication': datetime.now().isoformat()
        }
        self.logger.info(f"Registered system: {address}")
    
    def get_system_status(self, address: str) -> Dict[str, Any]:
        """Get status of registered system"""
        if address in self.registered_systems:
            return self.registered_systems[address]
        else:
            return {'status': 'UNKNOWN', 'address': address}
    
    def get_communication_log(self) -> List[Dict[str, Any]]:
        """Get communication log"""
        return [
            {
                'signal_id': signal.signal_id,
                'caller_address': signal.caller_address,
                'target_address': signal.target_address,
                'radio_code': signal.radio_code,
                'message': signal.message,
                'timestamp': signal.timestamp
            }
            for signal in self.communication_log
        ]
    
    def clear_communication_log(self):
        """Clear communication log"""
        self.communication_log.clear()
        self.active_signals.clear()
        self.logger.info("Communication log cleared")
    
    def get_registered_systems(self) -> Dict[str, Dict[str, Any]]:
        """Get all registered systems"""
        return self.registered_systems.copy()
    
    def broadcast_signal(self, radio_code: str, message: str = "", payload: Dict[str, Any] = None) -> List[str]:
        """Broadcast signal to all registered systems"""
        signal_ids = []
        for address in self.registered_systems.keys():
            if address != self.system_address:  # Don't send to self
                signal_id = self.send_signal(address, radio_code, message, payload)
                if signal_id:
                    signal_ids.append(signal_id)
        return signal_ids