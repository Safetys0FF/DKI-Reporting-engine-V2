#!/usr/bin/env python3
"""
DKI Engine - Central Command Runtime
Pure Central Command architecture - no UI interface
"""

import os
import sys
import logging
import subprocess
import time
import threading
from datetime import datetime
from pathlib import Path

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
from importlib.util import spec_from_file_location, module_from_spec

LIBRARIAN_DIR = Path(r"F:/The Central Command/Command Center/Mission Debrief/The Librarian")
DEBRIEF_DIR = Path(r"F:/The Central Command/Command Center/Mission Debrief/Debrief/README")


def _load_class(module_name: str, module_path: Path, attr_name: str):
    spec = spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load spec for {module_name} from {module_path}")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        return getattr(module, attr_name)
    except AttributeError as exc:
        raise ImportError(f"{attr_name} not found in {module_path}") from exc


NarrativeAssembler = _load_class("narrative_assembler", LIBRARIAN_DIR / "narrative_assembler.py", "NarrativeAssembler")
MissionDebriefManager = _load_class("mission_debrief_manager", DEBRIEF_DIR / "mission_debrief_manager.py", "MissionDebriefManager")

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

# ========================================================================
# PHASE 1: CANBUS INITIALIZATION
# ========================================================================
logger.info("=" * 80)
logger.info("PHASE 1: CANBUS INITIALIZATION")
logger.info("=" * 80)

bus = DKIReportBus()
logger.info("✓ CANBUS created - waiting for Bus-1 stabilization...")

# Wait for Bus-1 stabilization ready message
if hasattr(bus, 'wait_for_ready'):
    if bus.wait_for_ready(timeout=15.0):
        logger.info("✓ Bus-1 stabilization complete - CANBUS ready")
    else:
        logger.error("❌ Bus-1 stabilization timeout")
        sys.exit(1)
else:
    time.sleep(10)
    logger.info("✓ CANBUS stabilization period complete")

# ========================================================================
# PHASE 2: DIAG-1 INITIALIZATION
# ========================================================================
logger.info("=" * 80)
logger.info("PHASE 2: DIAG-1 INITIALIZATION")
logger.info("=" * 80)

# Import and create UDS instance
sys.path.insert(0, str(Path(r"F:\The Central Command\Command Center\Data Bus\diagnostic_manager\Unified_diagnostic_system")))
try:
    from __init__ import UnifiedDiagnosticSystem
    
    logger.info("Creating DIAG-1 instance with shared CANBUS...")
    uds = UnifiedDiagnosticSystem(bus_connection=bus)
    logger.info("✓ DIAG-1 instance created and signal handlers registered")
    
except Exception as e:
    logger.error(f"❌ Failed to create DIAG-1: {e}")
    import traceback
    logger.error(traceback.format_exc())
    sys.exit(1)

# Signal handlers for DIAG-1 communication
diag_ready = threading.Event()
system_test_complete = threading.Event()
test_results = {}

def on_diag_ready(data):
    """Handle DIAG-1 ready signal"""
    logger.info("✓ DIAG-1 ready signal received")
    diag_ready.set()

def on_system_test_complete(data):
    """Handle system test completion from DIAG-1"""
    global test_results
    logger.info("=" * 80)
    logger.info("✓ DIAG-1 SYSTEM TEST COMPLETE")
    logger.info("=" * 80)
    test_results = data
    logger.info(f"  Total systems: {data.get('total_systems', 0)}")
    logger.info(f"  Passed: {data.get('passed', 0)}")
    logger.info(f"  Failed: {data.get('failed', 0)}")
    if data.get('fault_report'):
        logger.warning(f"  Fault Report: {data.get('fault_report')}")
    system_test_complete.set()

# Register signal handlers
bus.register_signal('diag.ready', on_diag_ready)
bus.register_signal('diag.test_complete', on_system_test_complete)

# Send initialize command to DIAG-1
logger.info("Sending initialization command to DIAG-1...")
bus.emit('diag.initialize', {
    'source': 'main_application',
    'timestamp': datetime.now().isoformat(),
    'command': 'initialize_and_stabilize'
})

# Wait for DIAG-1 ready confirmation
logger.info("Waiting for DIAG-1 ready signal...")
if not diag_ready.wait(timeout=30):
    logger.error("❌ DIAG-1 initialization timeout")
    sys.exit(1)

logger.info("✓ DIAG-1 initialized and ready")

# ========================================================================
# PHASE 3: PARENT MODULE INITIALIZATION
# ========================================================================
logger.info("=" * 80)
logger.info("PHASE 3: PARENT MODULE INITIALIZATION & SELF-TEST")
logger.info("=" * 80)

# Broadcast initialize command to all parent modules
logger.info("Broadcasting initialization command to parent modules...")
bus.emit('system.initialize', {
    'source': 'main_application',
    'timestamp': datetime.now().isoformat(),
    'command': 'initialize_and_self_test',
    'report_to': 'DIAG-1'
})

# Wait for DIAG-1 to collect reports and send results
logger.info("Waiting for DIAG-1 to collect test results from parent modules...")
if not system_test_complete.wait(timeout=120):
    logger.error("=" * 80)
    logger.error("❌ SYSTEM TEST TIMEOUT - Modules did not complete self-tests")
    logger.error("=" * 80)
    sys.exit(1)

# ========================================================================
# PHASE 4: EVALUATION & HANDOFF
# ========================================================================
logger.info("=" * 80)
logger.info("PHASE 4: SYSTEM EVALUATION")
logger.info("=" * 80)

if test_results.get('failed', 0) > 0:
    logger.error("❌ SYSTEM TEST FAILED - Not all modules passed self-test")
    logger.error(f"Fault Report: {test_results.get('fault_report', 'No details')}")
    sys.exit(1)

logger.info("=" * 80)
logger.info("✓ ALL SYSTEMS PASSED - System is operational")
logger.info("=" * 80)
logger.info("🚀 Central Command Runtime ready - all systems operational")

# Keep the runtime alive
if __name__ == "__main__":
    try:
        # Keep the Central Command System running
        while True:
            pass
    except KeyboardInterrupt:
        logger.info("🛑 Central Command Runtime shutdown")
        # Shutdown UDS gracefully
        try:
            if 'uds' in locals():
                logger.info("Shutting down UDS...")
                uds.shutdown_diagnostic_system()
        except Exception as e:
            logger.error(f"Error during UDS shutdown: {e}")
        print("Central Command Runtime shutdown")
