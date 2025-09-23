#!/usr/bin/env python3
"""
DKI Bus Core - Central Command Architecture
100% new Central Command design - no old architecture
"""

import os
import sys
import json
from datetime import datetime
import threading
import logging
from typing import Dict, List, Any, Optional, Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dki_bus_core.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DKIReportBus:
    """Central Command Bus - Signal-based architecture"""
    
    def __init__(self):
        self.signal_registry = {}
        self.module_log = []
        self.active_modules = {}
        self.event_log: List[Dict[str, Any]] = []
        self.lock = threading.Lock()

        # Central Command state
        self.current_case_id = None
        self.current_case = None
        self.case_metadata: Dict[str, Any] = {}
        self.uploaded_files = []
        self.section_data = {}
        self.report_type = "Investigative"
        
        logger.info("Central Command Bus initialized")

    def register_signal(self, signal, handler):
        """Register signal handler"""
        with self.lock:
            if signal not in self.signal_registry:
                self.signal_registry[signal] = []
            self.signal_registry[signal].append(handler)
        logger.info(f"[BUS] Signal '{signal}' bound to {handler.__name__}")

    def subscribe(self, topic, handler):
        """Alias to maintain compatibility with pub/sub vocabulary"""
        self.register_signal(topic, handler)

    def log_event(self, source: str, message: str, level: str = "info"):
        """Record an event in the bus log"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "message": message,
            "level": level
        }
        with self.lock:
            self.event_log.append(entry)
        log_fn = getattr(logger, level.lower(), logger.info)
        log_fn(f"[BUS][{source}] {message}")

    def get_event_log(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Return recorded bus events"""
        with self.lock:
            if limit is None or limit >= len(self.event_log):
                return list(self.event_log)
            return self.event_log[-limit:]

    def send(self, topic: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to the registered handlers and return their response"""
        handlers = self.signal_registry.get(topic, [])
        if not handlers:
            logger.warning(f"[BUS] No handlers for topic: {topic}")
            return {}
        responses = []
        for handler in handlers:
            try:
                response = handler(data)
                if response is not None:
                    responses.append(response)
            except Exception as e:
                logger.error(f"[BUS] Error running handler '{handler.__name__}' for topic '{topic}': {e}")
        if not responses:
            return {}
        if len(responses) == 1 and isinstance(responses[0], dict):
            return responses[0]
        return {"responses": responses}

    def emit(self, signal, payload):
        """Emit signal to registered handlers"""
        handlers = self.signal_registry.get(signal, [])
        if not handlers:
            logger.warning(f"[BUS] No handlers for signal: {signal}")
            return
        
        for handler in handlers:
            try:
                handler(payload)
            except Exception as e:
                logger.error(f"[BUS] Error running handler '{handler.__name__}': {e}")

    def inject_module(self, module):
        """Inject module into the bus"""
        if hasattr(module, "initialize"):
            module.initialize(self)
            self.module_log.append(module.__name__)
            self.active_modules[module.__name__] = module
            logger.info(f"[BUS] Module '{module.__name__}' initialized")
        else:
            logger.warning(f"[BUS] Module '{module.__name__}' missing 'initialize()'")

    def authenticate_user(self, username: str, password: str) -> bool:
        """Authenticate user via Central Command"""
        # Emit authentication signal
        self.emit("user_authenticate", {
            "username": username,
            "password": password,
            "timestamp": datetime.now().isoformat()
        })
        return True  # Simplified for now

    def create_user(self, username: str, password: str, role: str = 'agent') -> bool:
        """Create new user via Central Command"""
        self.emit("user_create", {
            "username": username,
            "password": password,
            "role": role,
            "timestamp": datetime.now().isoformat()
        })
        return True  # Simplified for now

    def new_case(self, case_info: Dict[str, Any]) -> str:
        """Start a new case via Central Command"""
        self.current_case_id = f"CASE_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.case_metadata = case_info.copy()
        self.report_type = case_info.get('report_type', 'Investigative')
        self.uploaded_files = []
        self.section_data = {}
        
        # Emit case creation signal
        self.emit("case_create", {
            "case_id": self.current_case_id,
            "case_info": case_info,
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"New case created: {self.current_case_id}")
        return self.current_case_id

    def add_files(self, files: List[str]) -> bool:
        """Add files to current case via Central Command"""
        self.uploaded_files = files
        
        # Emit file addition signal
        self.emit("files_add", {
            "case_id": self.current_case_id,
            "files": files,
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"Added {len(files)} files to case")
        return True

    def process_files(self) -> Dict[str, Any]:
        """Process files via Central Command"""
        if not self.uploaded_files:
            logger.warning("No files to process")
            return {}
        
        # Emit file processing signal
        self.emit("files_process", {
            "case_id": self.current_case_id,
            "files": self.uploaded_files,
            "timestamp": datetime.now().isoformat()
        })
        
        # Simplified processing result
        processed_data = {
            "files_processed": len(self.uploaded_files),
            "processing_timestamp": datetime.now().isoformat(),
            "status": "completed"
        }
        
        self.section_data['processed_files'] = processed_data
        logger.info(f"Processed {len(self.uploaded_files)} files")
        return processed_data

    def generate_section(self, section_name: str) -> Dict[str, Any]:
        """Generate section via Central Command"""
        # Emit section generation signal
        self.emit("section_generate", {
            "case_id": self.current_case_id,
            "section_name": section_name,
            "report_type": self.report_type,
            "timestamp": datetime.now().isoformat()
        })
        
        # Simplified section result
        section_result = {
            "section_name": section_name,
            "content": f"Generated content for {section_name}",
            "timestamp": datetime.now().isoformat(),
            "status": "completed"
        }
        
        self.section_data[section_name] = section_result
        logger.info(f"{section_name} generated successfully")
        return section_result

    def generate_full_report(self) -> Dict[str, Any]:
        """Generate full report via Central Command"""
        if not self.section_data:
            logger.warning("No section data available")
            return {}
        
        # Emit full report generation signal
        self.emit("report_generate_full", {
            "case_id": self.current_case_id,
            "sections": list(self.section_data.keys()),
            "report_type": self.report_type,
            "timestamp": datetime.now().isoformat()
        })
        
        # Simplified report result
        report_result = {
            "case_id": self.current_case_id,
            "sections": self.section_data,
            "report_type": self.report_type,
            "generated_timestamp": datetime.now().isoformat(),
            "status": "completed"
        }
        
        logger.info("Full report generated successfully")
        return report_result

    def export_report(self, report_data: Dict[str, Any], filename: str, format_type: str) -> bool:
        """Export report via Central Command"""
        # Emit export signal
        self.emit("report_export", {
            "case_id": self.current_case_id,
            "filename": filename,
            "format_type": format_type,
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"Report exported: {filename}")
        return True

    def get_status(self) -> Dict[str, Any]:
        """Get Central Command bus status"""
        return {
            'current_case_id': self.current_case_id,
            'report_type': self.report_type,
            'uploaded_files_count': len(self.uploaded_files),
            'sections_generated': len(self.section_data),
            'active_modules': list(self.active_modules.keys()),
            'registered_signals': list(self.signal_registry.keys()),
            'event_log_size': len(self.event_log),
            'bus_status': 'online'
        }

    def reset_for_new_case(self):
        """Reset for new case via Central Command"""
        # Emit reset signal
        self.emit("case_reset", {
            "timestamp": datetime.now().isoformat()
        })
        
        self.current_case_id = None
        self.uploaded_files = []
        self.section_data = {}
        logger.info("Reset for new case")


# Central Command Module Injection Functions
def inject_gateway_controller(bus):
    """Inject gateway controller module"""
    bus.register_signal("gateway_initialize", lambda p: logger.info(f"[GATEWAY] Initialized: {p}"))
    bus.register_signal("gateway_reset", lambda p: logger.info(f"[GATEWAY] Reset: {p}"))
    logger.info("[CENTRAL COMMAND] Gateway controller injected")

def inject_evidence_manager(bus):
    """Inject evidence manager module"""
    bus.register_signal("evidence_process", lambda p: logger.info(f"[EVIDENCE] Processed: {p}"))
    bus.register_signal("evidence_validate", lambda p: logger.info(f"[EVIDENCE] Validated: {p}"))
    logger.info("[CENTRAL COMMAND] Evidence manager injected")

def inject_evidence_index(bus):
    """Inject evidence index module"""
    bus.register_signal("index_update", lambda p: logger.info(f"[INDEX] Updated: {p}"))
    bus.register_signal("index_search", lambda p: logger.info(f"[INDEX] Search: {p}"))
    logger.info("[CENTRAL COMMAND] Evidence index injected")


if __name__ == "__main__":
    # Test the Central Command bus
    bus = DKIReportBus()
    
    # Inject Central Command modules
    inject_gateway_controller(bus)
    inject_evidence_manager(bus)
    inject_evidence_index(bus)
    
    # Test signals
    bus.emit("boot_check", {"status": "online"})
    
    print("Central Command Bus initialized successfully")
    print(f"Status: {bus.get_status()}")