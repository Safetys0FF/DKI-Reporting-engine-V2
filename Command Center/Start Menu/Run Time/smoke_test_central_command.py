#!/usr/bin/env python3
"""
Central Command Smoke Test - Complete Bus Network Testing
Tests Warden → Evidence Locker → Gateway Controller → Each Cell
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('smoke_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class CentralCommandSmokeTest:
    """Comprehensive smoke test for Central Command bus network"""
    
    def __init__(self):
        self.test_results = {}
        self.test_evidence_file = "test_evidence.pdf"
        self.test_sections = [
            "section_1", "section_2", "section_3", "section_4", 
            "section_5", "section_6", "section_7", "section_8"
        ]
        
        # Initialize test evidence file
        self._create_test_evidence()
        
        logger.info("Central Command Smoke Test initialized")
    
    def _create_test_evidence(self):
        """Create test evidence file"""
        try:
            with open(self.test_evidence_file, 'w') as f:
                f.write("Test evidence content for smoke testing")
            logger.info(f"Created test evidence file: {self.test_evidence_file}")
        except Exception as e:
            logger.error(f"Failed to create test evidence: {e}")
    
    def test_warden_initialization(self) -> bool:
        """Test 1: Warden (ECC + Gateway Controller) initialization"""
        try:
            logger.info("🧪 Test 1: Warden Initialization")
            
            # Initialize Warden
            warden = Warden()
            self.test_results['warden'] = warden
            
            # Start Warden
            if warden.start_warden():
                logger.info("✅ Warden initialized successfully")
                return True
            else:
                logger.error("❌ Warden failed to start")
                return False
                
        except Exception as e:
            logger.error(f"❌ Warden initialization failed: {e}")
            return False
    
    def test_evidence_locker_registration(self) -> bool:
        """Test 2: Evidence Locker registration with Warden"""
        try:
            logger.info("🧪 Test 2: Evidence Locker Registration")
            
            warden = self.test_results['warden']
            
            # Initialize Evidence Locker
            evidence_locker = EvidenceLocker(ecc=warden.warden_modules['ecc'], gateway=warden.warden_modules['gateway_controller'])
            
            # Register with Warden
            if warden.register_evidence_locker(evidence_locker):
                self.test_results['evidence_locker'] = evidence_locker
                logger.info("✅ Evidence Locker registered successfully")
                return True
            else:
                logger.error("❌ Evidence Locker registration failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Evidence Locker registration failed: {e}")
            return False
    
    def test_evidence_manager_registration(self) -> bool:
        """Test 3: Evidence Manager registration with Warden"""
        try:
            logger.info("🧪 Test 3: Evidence Manager Registration")
            
            warden = self.test_results['warden']
            
            # Initialize Evidence Manager
            evidence_manager = EvidenceManager(ecc=warden.warden_modules['ecc'], gateway=warden.warden_modules['gateway_controller'])
            
            # Register with Warden
            if warden.register_evidence_manager(evidence_manager):
                self.test_results['evidence_manager'] = evidence_manager
                logger.info("✅ Evidence Manager registered successfully")
                return True
            else:
                logger.error("❌ Evidence Manager registration failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Evidence Manager registration failed: {e}")
            return False
    
    def test_evidence_ingestion_flow(self) -> bool:
        """Test 4: Evidence ingestion through Evidence Manager"""
        try:
            logger.info("🧪 Test 4: Evidence Ingestion Flow")
            
            evidence_manager = self.test_results['evidence_manager']
            
            # Ingest test evidence
            evidence_id = evidence_manager.ingest_evidence(
                file_path=self.test_evidence_file,
                section_id="section_1",
                metadata={"test": True, "smoke_test": True}
            )
            
            if evidence_id:
                self.test_results['evidence_id'] = evidence_id
                logger.info(f"✅ Evidence ingested successfully: {evidence_id}")
                return True
            else:
                logger.error("❌ Evidence ingestion failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Evidence ingestion failed: {e}")
            return False
    
    def test_evidence_locker_processing(self) -> bool:
        """Test 5: Evidence processing through Evidence Locker"""
        try:
            logger.info("🧪 Test 5: Evidence Locker Processing")
            
            evidence_locker = self.test_results['evidence_locker']
            
            # Scan test evidence
            evidence_id = evidence_locker.scan_file(self.test_evidence_file)
            
            if evidence_id:
                self.test_results['locker_evidence_id'] = evidence_id
                logger.info(f"✅ Evidence Locker processed successfully: {evidence_id}")
                return True
            else:
                logger.error("❌ Evidence Locker processing failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Evidence Locker processing failed: {e}")
            return False
    
    def test_gateway_controller_handoff(self) -> bool:
        """Test 6: Gateway Controller handoff processing"""
        try:
            logger.info("🧪 Test 6: Gateway Controller Handoff")
            
            warden = self.test_results['warden']
            gateway = warden.warden_modules['gateway_controller']
            
            # Check Gateway status
            gateway_status = gateway.get_evidence_locker_status()
            
            if gateway_status:
                logger.info(f"✅ Gateway Controller status: {gateway_status}")
                return True
            else:
                logger.error("❌ Gateway Controller status check failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Gateway Controller handoff failed: {e}")
            return False
    
    def test_section_registration(self) -> bool:
        """Test 7: Section registration with Warden"""
        try:
            logger.info("🧪 Test 7: Section Registration")
            
            warden = self.test_results['warden']
            
            # Mock section handlers
            for section_id in self.test_sections:
                mock_handler = lambda data: logger.info(f"Mock handler for {section_id}: {data}")
                
                if warden.register_section(section_id, mock_handler):
                    logger.info(f"✅ Section {section_id} registered")
                else:
                    logger.error(f"❌ Section {section_id} registration failed")
                    return False
            
            logger.info("✅ All sections registered successfully")
            return True
                
        except Exception as e:
            logger.error(f"❌ Section registration failed: {e}")
            return False
    
    def test_cell_communication(self) -> bool:
        """Test 8: Communication to each individual cell"""
        try:
            logger.info("🧪 Test 8: Cell Communication")
            
            evidence_manager = self.test_results['evidence_manager']
            
            # Test handoff to each cell
            for section_id in self.test_sections:
                try:
                    # Test handoff to cell
                    success = evidence_manager._handoff_to_cell(
                        cell_id=section_id,
                        operation="smoke_test",
                        data={"test": True, "section": section_id}
                    )
                    
                    if success:
                        logger.info(f"✅ Handoff to {section_id} successful")
                    else:
                        logger.error(f"❌ Handoff to {section_id} failed")
                        return False
                        
                except Exception as e:
                    logger.error(f"❌ Handoff to {section_id} failed: {e}")
                    return False
            
            logger.info("✅ All cell communications successful")
            return True
                
        except Exception as e:
            logger.error(f"❌ Cell communication failed: {e}")
            return False
    
    def test_complete_bus_network(self) -> bool:
        """Test 9: Complete bus network flow"""
        try:
            logger.info("🧪 Test 9: Complete Bus Network Flow")
            
            warden = self.test_results['warden']
            evidence_manager = self.test_results['evidence_manager']
            evidence_locker = self.test_results['evidence_locker']
            
            # Test complete flow: Evidence Manager → Evidence Locker → Gateway → Cell
            test_data = {
                "operation": "complete_bus_test",
                "evidence_id": self.test_results.get('evidence_id'),
                "section_id": "section_1",
                "timestamp": datetime.now().isoformat()
            }
            
            # Test handoff through Warden
            if warden.process_handoff("evidence_manager", "evidence_locker", test_data):
                logger.info("✅ Evidence Manager → Evidence Locker handoff successful")
            else:
                logger.error("❌ Evidence Manager → Evidence Locker handoff failed")
                return False
            
            if warden.process_handoff("evidence_locker", "gateway_controller", test_data):
                logger.info("✅ Evidence Locker → Gateway Controller handoff successful")
            else:
                logger.error("❌ Evidence Locker → Gateway Controller handoff failed")
                return False
            
            if warden.process_handoff("gateway_controller", "section_1", test_data):
                logger.info("✅ Gateway Controller → Section 1 handoff successful")
            else:
                logger.error("❌ Gateway Controller → Section 1 handoff failed")
                return False
            
            logger.info("✅ Complete bus network flow successful")
            return True
                
        except Exception as e:
            logger.error(f"❌ Complete bus network test failed: {e}")
            return False
    
    def test_warden_status(self) -> bool:
        """Test 10: Warden status monitoring"""
        try:
            logger.info("🧪 Test 10: Warden Status Monitoring")
            
            warden = self.test_results['warden']
            
            # Get Warden status
            status = warden.get_warden_status()
            
            if status:
                logger.info(f"✅ Warden status: {status}")
                return True
            else:
                logger.error("❌ Warden status check failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Warden status test failed: {e}")
            return False
    
    def run_complete_smoke_test(self) -> Dict[str, bool]:
        """Run complete smoke test suite"""
        logger.info("🚀 Starting Central Command Smoke Test Suite")
        
        test_suite = [
            ("Warden Initialization", self.test_warden_initialization),
            ("Evidence Locker Registration", self.test_evidence_locker_registration),
            ("Evidence Manager Registration", self.test_evidence_manager_registration),
            ("Evidence Ingestion Flow", self.test_evidence_ingestion_flow),
            ("Evidence Locker Processing", self.test_evidence_locker_processing),
            ("Gateway Controller Handoff", self.test_gateway_controller_handoff),
            ("Section Registration", self.test_section_registration),
            ("Cell Communication", self.test_cell_communication),
            ("Complete Bus Network", self.test_complete_bus_network),
            ("Warden Status Monitoring", self.test_warden_status)
        ]
        
        results = {}
        
        for test_name, test_func in test_suite:
            try:
                result = test_func()
                results[test_name] = result
                
                if result:
                    logger.info(f"✅ {test_name}: PASSED")
                else:
                    logger.error(f"❌ {test_name}: FAILED")
                    
            except Exception as e:
                logger.error(f"❌ {test_name}: ERROR - {e}")
                results[test_name] = False
        
        # Cleanup
        self._cleanup()
        
        return results
    
    def _cleanup(self):
        """Cleanup test files"""
        try:
            if os.path.exists(self.test_evidence_file):
                os.remove(self.test_evidence_file)
                logger.info("🧹 Cleaned up test evidence file")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")


# Run smoke test
if __name__ == "__main__":
    smoke_test = CentralCommandSmokeTest()
    results = smoke_test.run_complete_smoke_test()
    
    # Print summary
    logger.info("📊 Smoke Test Summary:")
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"  {test_name}: {status}")
    
    logger.info(f"📈 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All smoke tests passed! Central Command bus network is working!")
    else:
        logger.error("⚠️ Some smoke tests failed. Check logs for details.")
