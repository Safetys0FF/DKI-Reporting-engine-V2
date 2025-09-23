#!/usr/bin/env python3
"""
DKI Engine - Central Command Runtime
Pure Central Command architecture - no UI interface
"""

import os
import sys
import logging
from datetime import datetime

# Import Warden (ECC + Gateway Controller)
sys.path.append(r"F:\The Central Command\The Warden")
from warden_main import Warden

# Import Evidence Locker
sys.path.append(r"F:\The Central Command\Evidence Locker")
from evidence_locker_main import EvidenceLocker

# Import Evidence Manager
sys.path.append(r"F:\The Central Command\The Marshall")
from evidence_manager import EvidenceManager

# Import Narrative Assembler and Mission Debrief Manager
sys.path.append(r"F:\The Central Command\Command Center\Mission Debrief")
from narrative_assembler import NarrativeAssembler
from mission_debrief_manager import MissionDebriefManager

# Import Central Command Bus
sys.path.append(r"F:\The Central Command\Command Center\Data Bus\Bus Core Design")
from bus_core import DKIReportBus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dki_engine.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Initialize Central Command System
logger.info("🚀 Initializing Central Command System...")

# Initialize Central Command Bus
logger.info("🚀 Initializing Central Command Bus...")
bus = DKIReportBus()
logger.info("✅ Central Command Bus initialized")

# Initialize Warden (ECC + Gateway Controller)
warden = Warden()
warden.start_warden()

# Initialize Evidence Locker with bus
evidence_locker = EvidenceLocker(ecc=warden.ecc, gateway=warden.gateway, bus=bus)
warden.register_evidence_locker(evidence_locker)

# Initialize Evidence Manager
evidence_manager = EvidenceManager(ecc=warden.ecc, gateway=warden.gateway)
warden.register_evidence_manager(evidence_manager)

# Initialize Narrative Assembler (Bootstrap Component) with bus
narrative_assembler = NarrativeAssembler(ecc=warden.ecc, bus=bus)

# Initialize Mission Debrief Manager (Bootstrap Component) with bus
mission_debrief_manager = MissionDebriefManager(ecc=warden.ecc, bus=bus, gateway=warden.gateway)

logger.info("✅ Central Command System initialized successfully")
logger.info("🏛️ Warden (ECC + Gateway Controller) active")
logger.info("🔐 Evidence Locker registered with Central Command Bus")
logger.info("📦 Evidence Manager registered")
logger.info("📝 Narrative Assembler (Bootstrap Component) initialized with Bus")
logger.info("🎯 Mission Debrief Manager (Bootstrap Component) initialized with Bus")
logger.info("📡 Central Command Runtime ready - listening for signals via Bus")

# Keep the runtime alive
if __name__ == "__main__":
    try:
        # Keep the Central Command System running
        while True:
            pass
    except KeyboardInterrupt:
        logger.info("🛑 Central Command Runtime shutdown")
        warden.stop_warden()
        print("Central Command Runtime shutdown")