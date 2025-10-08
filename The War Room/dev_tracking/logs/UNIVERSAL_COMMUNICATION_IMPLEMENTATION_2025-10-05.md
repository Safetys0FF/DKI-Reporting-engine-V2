# Universal Communication Implementation
## Date: October 5, 2025

## **IMPLEMENTATION PLAN: Universal Communication Standard as SOP**

Every module in the Central Command system will implement the universal communication protocol as their Standard Operating Procedure (SOP).

---

## **PHASE 1: UNIVERSAL COMMUNICATOR CLASS**

### **Core Universal Communicator:**
```python
# File: F:\The Central Command\Command Center\Data Bus\universal_communicator.py

import time
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

@dataclass
class CommunicationSignal:
    signal_id: str
    caller_address: str
    target_address: str
    bus_address: str
    signal_type: str
    radio_code: str
    message: str
    payload: Dict[str, Any]
    response_expected: bool
    timeout: int
    timestamp: str

class UniversalCommunicator:
    """
    Universal Communication Protocol for all Central Command modules
    Standard Operating Procedure (SOP) for inter-module communication
    """
    
    def __init__(self, module_address: str, bus_connection=None):
        self.module_address = module_address
        self.bus_connection = bus_connection
        self.communication_log = []
        self.active_signals = {}
        
        # Standard radio codes
        self.radio_codes = {
            "10-4": "Acknowledged - Message received and understood",
            "10-6": "Evidence Received - Evidence has been received and is being processed", 
            "10-8": "Evidence Complete - Evidence processing is complete and ready",
            "10-9": "Repeat - Please repeat your last message",
            "10-10": "Standby - Please wait, processing in progress",
            "SOS": "Emergency - System failure, immediate assistance required",
            "STATUS": "Status request - Please provide system status",
            "ROLLCALL": "Rollcall - All systems respond with status",
            "RADIO_CHECK": "Radio check - Test communication"
        }
    
    def send_signal(self, target_address: str, radio_code: str, message: str, 
                   payload: Dict[str, Any] = None, timeout: int = 30) -> Dict[str, Any]:
        """
        Send signal using universal communication protocol
        SOP for all module communication
        """
        signal_id = f"{self.module_address}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        signal = CommunicationSignal(
            signal_id=signal_id,
            caller_address=self.module_address,
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
        
        # Log the signal
        self.communication_log.append(signal)
        self.active_signals[signal_id] = signal
        
        # Send via bus if available
        if self.bus_connection:
            response = self.bus_connection.route_signal(signal)
        else:
            response = self._simulate_response(signal)
        
        # Log response
        if response:
            self.communication_log.append(response)
        
        return response
    
    def send_radio_check(self, target_address: str) -> Dict[str, Any]:
        """Send radio check to target system"""
        return self.send_signal(
            target_address=target_address,
            radio_code="RADIO_CHECK",
            message=f"Radio check to {target_address}",
            payload={"operation": "radio_check"},
            timeout=15
        )
    
    def send_status_request(self, target_address: str) -> Dict[str, Any]:
        """Send status request to target system"""
        return self.send_signal(
            target_address=target_address,
            radio_code="STATUS",
            message=f"Status request to {target_address}",
            payload={"operation": "status_request"},
            timeout=30
        )
    
    def send_sos_fault(self, fault_code: str, description: str, 
                      details: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send SOS fault signal"""
        return self.send_signal(
            target_address="Bus-1",
            radio_code="SOS",
            message=f"SOS fault from {self.module_address}: {description}",
            payload={
                "operation": "sos_fault",
                "fault_code": fault_code,
                "description": description,
                "details": details or {}
            },
            timeout=5
        )
    
    def respond_to_signal(self, signal: CommunicationSignal, 
                         radio_code: str, message: str, 
                         payload: Dict[str, Any] = None) -> Dict[str, Any]:
        """Respond to incoming signal"""
        response = CommunicationSignal(
            signal_id=f"response_{signal.signal_id}",
            caller_address=self.module_address,
            target_address=signal.caller_address,
            bus_address="Bus-1",
            signal_type="response",
            radio_code=radio_code,
            message=message,
            payload=payload or {},
            response_expected=False,
            timeout=0,
            timestamp=datetime.now().isoformat()
        )
        
        self.communication_log.append(response)
        return response
    
    def acknowledge_signal(self, signal: CommunicationSignal) -> Dict[str, Any]:
        """Acknowledge received signal"""
        return self.respond_to_signal(
            signal=signal,
            radio_code="10-4",
            message=f"Acknowledged from {self.module_address}",
            payload={"status": "acknowledged"}
        )
    
    def get_communication_log(self) -> List[Dict[str, Any]]:
        """Get communication log for this module"""
        return [
            {
                "signal_id": signal.signal_id,
                "caller": signal.caller_address,
                "target": signal.target_address,
                "radio_code": signal.radio_code,
                "message": signal.message,
                "timestamp": signal.timestamp
            }
            for signal in self.communication_log
        ]
    
    def _simulate_response(self, signal: CommunicationSignal) -> Dict[str, Any]:
        """Simulate response when bus is not available"""
        return {
            "signal_id": f"response_{signal.signal_id}",
            "caller_address": signal.target_address,
            "target_address": self.module_address,
            "radio_code": "10-4",
            "message": "Simulated response",
            "timestamp": datetime.now().isoformat()
        }
```

---

## **PHASE 2: MODULE INTEGRATION**

### **Evidence Locker Integration:**
```python
# File: F:\The Central Command\Evidence Locker\evidence_locker_main.py

from universal_communicator import UniversalCommunicator

class EvidenceLocker:
    def __init__(self):
        # Initialize universal communicator
        self.communicator = UniversalCommunicator("1-1", bus_connection=self.bus)
        
        # Existing initialization code...
    
    def process_evidence(self, evidence_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process evidence using universal communication protocol"""
        try:
            # Send evidence received signal
            self.communicator.send_signal(
                target_address="2-1",  # ECC
                radio_code="10-6",
                message="Evidence received for processing",
                payload={"evidence_data": evidence_data}
            )
            
            # Process evidence
            result = self._process_evidence_internal(evidence_data)
            
            # Send evidence complete signal
            self.communicator.send_signal(
                target_address="2-1",  # ECC
                radio_code="10-8",
                message="Evidence processing complete",
                payload={"result": result}
            )
            
            return result
            
        except Exception as e:
            # Send SOS fault with real line number
            error_location = self._get_error_location()
            fault_code = f"1-1-30-{self._get_line_number()}"
            self.communicator.send_sos_fault(
                fault_code=fault_code,
                description=f"Evidence processing error: {str(e)} at {error_location}",
                details={"error": str(e), "evidence_data": evidence_data, "location": error_location}
            )
            raise
    
    def _get_line_number(self) -> int:
        """Get current line number for fault reporting"""
        import inspect
        frame = inspect.currentframe()
        # Get the calling frame (where the error occurred)
        caller_frame = frame.f_back.f_back if frame.f_back else frame
        return caller_frame.f_lineno
    
    def _get_error_location(self) -> str:
        """Get detailed error location including function name"""
        import inspect
        frame = inspect.currentframe()
        caller_frame = frame.f_back.f_back if frame.f_back else frame
        
        filename = caller_frame.f_code.co_filename.split('\\')[-1]  # Just filename
        function_name = caller_frame.f_code.co_name
        line_number = caller_frame.f_lineno
        
        return f"{filename}:{function_name}:{line_number}"
```

### **ECC Integration:**
```python
# File: F:\The Central Command\The Warden\ecosystem_controller.py

from universal_communicator import UniversalCommunicator

class EcosystemController:
    def __init__(self):
        # Initialize universal communicator
        self.communicator = UniversalCommunicator("2-1", bus_connection=self.bus)
        
        # Existing initialization code...
    
    def validate_section(self, section_id: str) -> bool:
        """Validate section using universal communication protocol"""
        try:
            # Send status request to section
            response = self.communicator.send_status_request(f"4-{section_id}")
            
            if response and response.get("radio_code") == "10-4":
                return True
            else:
            # Send SOS fault with real line number
            error_location = self._get_error_location()
            fault_code = f"2-1-20-{self._get_line_number()}"
            self.communicator.send_sos_fault(
                fault_code=fault_code,
                description=f"Section {section_id} validation failed at {error_location}",
                details={"section_id": section_id, "response": response, "location": error_location}
            )
                return False
                
        except Exception as e:
            # Send SOS fault
            fault_code = f"2-1-30-{self._get_line_number()}"
            self.communicator.send_sos_fault(
                fault_code=fault_code,
                description=f"Section validation error: {str(e)}",
                details={"section_id": section_id, "error": str(e)}
            )
            raise
```

### **Mission Debrief Integration:**
```python
# File: F:\The Central Command\Command Center\Mission Debrief\Debrief\README\mission_debrief_manager.py

from universal_communicator import UniversalCommunicator

class MissionDebriefManager:
    def __init__(self):
        # Initialize universal communicator
        self.communicator = UniversalCommunicator("3-1", bus_connection=self.bus)
        
        # Existing initialization code...
    
    def generate_report(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate report using universal communication protocol"""
        try:
            # Send report generation request
            self.communicator.send_signal(
                target_address="3-2",  # Librarian
                radio_code="10-4",
                message="Report generation request",
                payload={"case_data": case_data}
            )
            
            # Generate report
            report = self._generate_report_internal(case_data)
            
            # Send report complete signal
            self.communicator.send_signal(
                target_address="Bus-1",
                radio_code="10-8",
                message="Report generation complete",
                payload={"report": report}
            )
            
            return report
            
        except Exception as e:
            # Send SOS fault
            fault_code = f"3-1-30-{self._get_line_number()}"
            self.communicator.send_sos_fault(
                fault_code=fault_code,
                description=f"Report generation error: {str(e)}",
                details={"case_data": case_data, "error": str(e)}
            )
            raise
```

---

## **PHASE 3: BUS CORE INTEGRATION**

### **Enhanced Bus Core:**
```python
# File: F:\The Central Command\Command Center\Data Bus\Bus Core Design\bus_core.py

from universal_communicator import UniversalCommunicator, CommunicationSignal

class DKIReportBus:
    def __init__(self):
        # Initialize universal communicator
        self.communicator = UniversalCommunicator("Bus-1")
        
        # Existing initialization code...
    
    def route_signal(self, signal: CommunicationSignal) -> Dict[str, Any]:
        """Route signal using universal communication protocol"""
        try:
            # Log signal
            self.communicator.communication_log.append(signal)
            
            # Route to target
            if signal.target_address == "Bus-1":
                return self._handle_bus_signal(signal)
            else:
                return self._route_to_target(signal)
                
        except Exception as e:
            # Send SOS fault
            fault_code = f"Bus-1-20-{self._get_line_number()}"
            self.communicator.send_sos_fault(
                fault_code=fault_code,
                description=f"Signal routing error: {str(e)}",
                details={"signal": signal, "error": str(e)}
            )
            raise
    
    def broadcast_rollcall(self) -> Dict[str, Any]:
        """Broadcast rollcall to all systems"""
        rollcall_results = {}
        
        for address in self.get_registered_addresses():
            if address != "Bus-1":
                response = self.communicator.send_signal(
                    target_address=address,
                    radio_code="ROLLCALL",
                    message=f"Rollcall to {address}",
                    payload={"operation": "rollcall"},
                    timeout=60
                )
                rollcall_results[address] = response
        
        return rollcall_results
```

---

## **PHASE 4: GUI INTEGRATION**

### **GUI Health Monitor Integration:**
```python
# File: F:\The Central Command\Command Center\enhanced_functional_gui.py

from universal_communicator import UniversalCommunicator

class EnhancedFunctionalGUI:
    def __init__(self):
        # Initialize universal communicator
        self.communicator = UniversalCommunicator("7-1", bus_connection=self.bus)
        
        # Existing initialization code...
    
    def update_health_monitor(self):
        """Update health monitor using universal communication protocol"""
        health_status = {}
        
        # Check all systems
        for address in self.get_system_addresses():
            try:
                response = self.communicator.send_radio_check(address)
                
                if response and response.get("radio_code") == "10-4":
                    health_status[address] = {"status": "OK", "code": "00"}
                else:
                    health_status[address] = {"status": "ERROR", "code": response.get("fault_code", "XX")}
                    
            except Exception as e:
                health_status[address] = {"status": "FAILURE", "code": "90"}
        
        # Update GUI display
        self._update_health_display(health_status)
    
    def _update_health_display(self, health_status: Dict[str, Dict[str, str]]):
        """Update health monitor display"""
        for address, status in health_status.items():
            if status["status"] == "OK":
                color = "green"
            elif status["status"] == "ERROR":
                color = "yellow"
            else:  # FAILURE
                color = "red"
            
            self.health_monitor.update_status(address, status["status"], status["code"], color)
```

---

## **IMPLEMENTATION CHECKLIST:**

### **Phase 1: Core Infrastructure** ✅
- [x] Universal Communicator class
- [x] Communication signal structure
- [x] Radio code definitions
- [x] Fault reporting system

### **Phase 2: Module Integration** 🔄
- [ ] Evidence Locker modules
- [ ] ECC and Gateway Controller
- [ ] Mission Debrief modules
- [ ] Analyst Deck sections
- [ ] Marshall modules
- [ ] War Room modules

### **Phase 3: Bus Integration** 🔄
- [ ] Enhanced bus_core.py
- [ ] Signal routing system
- [ ] Rollcall system
- [ ] Communication logging

### **Phase 4: GUI Integration** 🔄
- [ ] Health monitor updates
- [ ] Advanced diagnostics interface
- [ ] Real-time status display
- [ ] Fault notification system

This creates a **universal communication standard** that every module implements as their SOP, ensuring consistent, reliable communication across the entire Central Command system!
