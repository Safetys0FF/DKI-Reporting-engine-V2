#!/usr/bin/env python3
"""
Central Command Smoke Test - Simple Version
Tests Warden -> Evidence Locker -> Gateway Controller -> Each Cell
"""

import os
import sys
import logging
from datetime import datetime

# Import Central Command System
sys.path.append(r"F:\The Central Command\The Warden")
from warden_main import Warden

sys.path.append(r"F:\The Central Command\Evidence Locker")
from evidence_locker_main import EvidenceLocker

sys.path.append(r"F:\The Central Command\The Marshall")
from evidence_manager import EvidenceManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_central_command():
    """Simple smoke test for Central Command"""
    logger.info("Starting Central Command Smoke Test")
    
    try:
        # Test 1: Initialize Warden
        logger.info("Test 1: Initializing Warden...")
        warden = Warden()
        warden.start_warden()
        logger.info("SUCCESS: Warden initialized")
        
        # Test 2: Initialize Evidence Locker
        logger.info("Test 2: Initializing Evidence Locker...")
        evidence_locker = EvidenceLocker(ecc=warden.ecc, gateway=warden.gateway)
        warden.register_evidence_locker(evidence_locker)
        logger.info("SUCCESS: Evidence Locker registered")
        
        # Test 3: Initialize Evidence Manager
        logger.info("Test 3: Initializing Evidence Manager...")
        evidence_manager = EvidenceManager(ecc=warden.ecc, gateway=warden.gateway)
        warden.register_evidence_manager(evidence_manager)
        logger.info("SUCCESS: Evidence Manager registered")
        
        # Test 4: Create test evidence
        logger.info("Test 4: Creating test evidence...")
        test_file = "test_evidence.txt"
        with open(test_file, 'w') as f:
            f.write("Test evidence content")
        logger.info("SUCCESS: Test evidence created")
        
        # Test 5: Test evidence ingestion
        logger.info("Test 5: Testing evidence ingestion...")
        evidence_id = evidence_manager.ingest_evidence(test_file, "section_1")
        logger.info(f"SUCCESS: Evidence ingested with ID: {evidence_id}")
        
        # Test 6: Test evidence locker processing
        logger.info("Test 6: Testing evidence locker processing...")
        locker_evidence_id = evidence_locker.scan_file(test_file)
        logger.info(f"SUCCESS: Evidence Locker processed with ID: {locker_evidence_id}")
        
        # Test 7: Test handoff processing
        logger.info("Test 7: Testing handoff processing...")
        warden.process_handoff("evidence_manager", "evidence_locker", {"test": True})
        logger.info("SUCCESS: Handoff processed")
        
        # Test 8: Test section registration
        logger.info("Test 8: Testing section registration...")
        for i in range(1, 9):
            section_id = f"section_{i}"
            mock_handler = lambda data: logger.info(f"Mock handler for {section_id}")
            warden.register_section(section_id, mock_handler)
        logger.info("SUCCESS: All sections registered")
        
        # Test 9: Test cell communication
        logger.info("Test 9: Testing cell communication...")
        for i in range(1, 9):
            section_id = f"section_{i}"
            evidence_manager._handoff_to_cell(section_id, "test", {"test": True})
        logger.info("SUCCESS: All cell communications successful")
        
        # Test 10: Test Warden status
        logger.info("Test 10: Testing Warden status...")
        status = warden.get_warden_status()
        logger.info(f"SUCCESS: Warden status retrieved: {len(status)} items")
        
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)
        
        logger.info("ALL TESTS PASSED! Central Command bus network is working!")
        return True
        
    except Exception as e:
        logger.error(f"TEST FAILED: {e}")
        return False

if __name__ == "__main__":
    success = test_central_command()
    if success:
        print("SUCCESS: All smoke tests passed!")
    else:
        print("FAILURE: Some smoke tests failed!")











