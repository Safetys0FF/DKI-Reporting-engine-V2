#!/usr/bin/env python3
"""
Warden Main - Central Command Control System
Bootstrap script for ECC (Ecosystem Controller) and Gateway Controller
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# Import Warden components
from ecosystem_controller import EcosystemController
from gateway_controller import GatewayController

# System Controller Interfaces (to be injected)
ECC = None
GATEWAY = None

logger = logging.getLogger("Warden")
logging.basicConfig(level=logging.INFO)

class Warden:
    """Central Command Control System - ECC + Gateway Controller"""
    
    def __init__(self, bus=None):
        global ECC, GATEWAY
        
        # Initialize ECC (Ecosystem Controller)
        ECC = EcosystemController(bus=bus)
        
        # Initialize Gateway Controller with ECC reference
        GATEWAY = GatewayController(ecosystem_controller=ECC, bus=bus)
        
        # Store references
        self.ecc = ECC
        self.gateway = GATEWAY
        self.bus = bus
        
        # Initialize Warden tracking
        self.warden_modules = {
            'ecc': {'status': 'active', 'last_activity': None, 'handoffs_processed': 0},
            'gateway_controller': {'status': 'active', 'last_activity': None, 'handoffs_processed': 0}
        }
        
        # Warden communication log
        self.communication_log = []
        self.handoff_queue = []
        
        logger.info("🏛️ Warden initialized - Central Command Control System")
        logger.info("✅ ECC (Ecosystem Controller) active")
        logger.info("✅ Gateway Controller active")
    
    def register_evidence_locker(self, evidence_locker):
        """Register Evidence Locker with Warden"""
        try:
            # Store reference
            self.evidence_locker = evidence_locker
            
            logger.info("🔐 Evidence Locker registered with Warden")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register Evidence Locker: {e}")
            return False
    
    def register_evidence_manager(self, evidence_manager):
        """Register Evidence Manager with Warden"""
        try:
            # Store reference
            self.evidence_manager = evidence_manager
            
            logger.info("📦 Evidence Manager registered with Warden")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register Evidence Manager: {e}")
            return False
    
    def register_section(self, section_id: str, section_handler):
        """Register section handler with Warden"""
        try:
            # Store reference
            if not hasattr(self, 'sections'):
                self.sections = {}
            self.sections[section_id] = section_handler
            
            logger.info(f"📋 Section {section_id} registered with Warden")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register section {section_id}: {e}")
            return False
    
    def process_handoff(self, from_module: str, to_module: str, handoff_data: Dict[str, Any]):
        """Process handoff between modules"""
        try:
            handoff_record = {
                'from_module': from_module,
                'to_module': to_module,
                'handoff_data': handoff_data,
                'timestamp': datetime.now().isoformat(),
                'status': 'processing'
            }
            
            self.handoff_queue.append(handoff_record)
            
            # Log handoff
            logger.info(f"🔄 Handoff: {from_module} → {to_module}")
            
            # Update module status
            if from_module in self.warden_modules:
                self.warden_modules[from_module]['handoffs_processed'] += 1
                self.warden_modules[from_module]['last_activity'] = datetime.now().isoformat()
            
            handoff_record['status'] = 'completed'
            
            logger.info(f"🔄 Warden processed handoff: {from_module} → {to_module}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to process handoff: {e}")
            return False
    
    def get_warden_status(self) -> Dict[str, Any]:
        """Get Warden status for monitoring"""
        try:
            return {
                'warden_modules': self.warden_modules,
                'handoff_queue_length': len(self.handoff_queue),
                'total_handoffs_processed': len([h for h in self.handoff_queue if h['status'] == 'completed']),
                'ecc_status': ECC.get_boot_node_status() if ECC else {},
                'gateway_status': GATEWAY.get_evidence_locker_status() if GATEWAY else {},
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get Warden status: {e}")
            return {}
    
    def start_warden(self):
        """Start Warden Central Command System"""
        try:
            logger.info("🚀 Starting Warden Central Command System...")
            
            # ECC and Gateway are already initialized in __init__
            logger.info("✅ ECC initialized")
            logger.info("✅ Gateway Controller initialized")
            
            logger.info("🏛️ Warden Central Command System active")
            logger.info("📡 Listening for signals and handoffs...")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start Warden: {e}")
            return False
    
    def stop_warden(self):
        """Stop Warden Central Command System"""
        try:
            logger.info("🛑 Stopping Warden Central Command System...")
            
            # ECC and Gateway will be cleaned up automatically
            logger.info("✅ ECC shutdown")
            logger.info("✅ Gateway Controller shutdown")
            
            logger.info("🏛️ Warden Central Command System stopped")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop Warden: {e}")
            return False


# Bootstrap for Central Command
if __name__ == "__main__":
    # Initialize Warden
    warden = Warden()
    
    # Start Warden
    if warden.start_warden():
        logger.info("🏛️ Warden Central Command System ready")
        logger.info("📡 ECC and Gateway Controller active")
        
        # Keep Warden running
        try:
            while True:
                pass
        except KeyboardInterrupt:
            logger.info("🛑 Shutdown signal received")
            warden.stop_warden()
    else:
        logger.error("❌ Failed to start Warden Central Command System")
