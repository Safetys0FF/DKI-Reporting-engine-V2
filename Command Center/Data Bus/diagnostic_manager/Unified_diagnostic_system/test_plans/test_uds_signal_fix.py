#!/usr/bin/env python3
"""
UDS Signal Fix Validation Test
Tests that UDS sends correct signal names (diagnostic.rollcall, diagnostic.radio_check)
and that signal handlers are properly registered.

This test validates UDS internal operation only - no parent modules required.
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Add UDS to path
uds_path = Path(__file__).parent.parent
sys.path.insert(0, str(uds_path))
sys.path.insert(0, str(uds_path.parent.parent / "Bus Core Design"))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("UDS_Signal_Test")

def test_signal_names():
    """Test that UDS sends signals with correct diagnostic.* prefix"""
    logger.info("=" * 60)
    logger.info("TEST 1: Validate Signal Names")
    logger.info("=" * 60)
    
    try:
        from comms import CommsSystem
        
        # Create mock orchestrator with system_registry
        class MockOrchestrator:
            def __init__(self):
                self.system_registry = {
                    "1-1": {"name": "Evidence Locker", "status": "active"},
                    "2-1": {"name": "Warden", "status": "active"},
                    "3-1": {"name": "Mission Debrief", "status": "active"}
                }
        
        # Track signals sent to bus
        sent_signals = []
        
        class MockBus:
            def send(self, signal_type, data):
                sent_signals.append({
                    'signal_type': signal_type,
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                })
                logger.info(f"  Mock Bus received: {signal_type}")
            
            def register_signal(self, signal_name, handler):
                logger.info(f"  Mock Bus registered handler for: {signal_name}")
        
        # Create comms with mock bus
        mock_orchestrator = MockOrchestrator()
        mock_bus = MockBus()
        
        comms = CommsSystem(
            orchestrator=mock_orchestrator,
            bus_connection=mock_bus,
            communicator=None
        )
        
        # Test rollcall transmission
        logger.info("\nTesting rollcall transmission...")
        sent_signals.clear()
        comms.transmit_rollcall()
        
        # Validate all signals use diagnostic.rollcall prefix
        rollcall_signals = [s for s in sent_signals if 'rollcall' in s['signal_type'].lower()]
        if rollcall_signals:
            for sig in rollcall_signals:
                if sig['signal_type'] == 'diagnostic.rollcall':
                    logger.info(f"  ✓ PASS: Rollcall uses correct prefix: {sig['signal_type']}")
                else:
                    logger.error(f"  ✗ FAIL: Rollcall uses wrong prefix: {sig['signal_type']}")
                    return False
        else:
            logger.error("  ✗ FAIL: No rollcall signals transmitted")
            return False
        
        # Test radio check transmission
        logger.info("\nTesting radio check transmission...")
        sent_signals.clear()
        comms.transmit_radio_check("1-1")
        
        # Validate radio check uses diagnostic.radio_check prefix
        radio_signals = [s for s in sent_signals if 'radio' in s['signal_type'].lower()]
        if radio_signals:
            for sig in radio_signals:
                if sig['signal_type'] == 'diagnostic.radio_check':
                    logger.info(f"  ✓ PASS: Radio check uses correct prefix: {sig['signal_type']}")
                else:
                    logger.error(f"  ✗ FAIL: Radio check uses wrong prefix: {sig['signal_type']}")
                    return False
        else:
            logger.error("  ✗ FAIL: No radio check signals transmitted")
            return False
        
        logger.info("\n✓ TEST 1 PASSED: All signals use correct diagnostic.* prefix")
        return True
        
    except Exception as e:
        logger.error(f"✗ TEST 1 FAILED: {e}", exc_info=True)
        return False


def test_signal_handlers():
    """Test that UDS registers correct signal handlers"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: Validate Signal Handler Registration")
    logger.info("=" * 60)
    
    try:
        from comms import CommsSystem
        
        # Track registered handlers
        registered_handlers = {}
        
        class MockBus:
            def send(self, signal_type, data):
                pass
            
            def register_signal(self, signal_name, handler):
                registered_handlers[signal_name] = handler
                logger.info(f"  Registered: {signal_name}")
        
        # Create comms with mock bus
        mock_bus = MockBus()
        
        comms = CommsSystem(
            orchestrator=None,
            bus_connection=mock_bus,
            communicator=None
        )
        
        # Check required handlers are registered
        required_handlers = [
            'communication',
            'diagnostic.rollcall',
            'fault.report',
            'fault.sos',
            'rollcall_response',
            'radio_check_response',
            'auto_registration'
        ]
        
        logger.info("\nValidating required handlers...")
        all_registered = True
        for handler_name in required_handlers:
            if handler_name in registered_handlers:
                logger.info(f"  ✓ {handler_name} - registered")
            else:
                logger.error(f"  ✗ {handler_name} - MISSING")
                all_registered = False
        
        if all_registered:
            logger.info("\n✓ TEST 2 PASSED: All required handlers registered")
            return True
        else:
            logger.error("\n✗ TEST 2 FAILED: Some handlers missing")
            return False
        
    except Exception as e:
        logger.error(f"✗ TEST 2 FAILED: {e}", exc_info=True)
        return False


def test_uds_initialization():
    """Test that UDS initializes with correct bus integration"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: Validate UDS Initialization")
    logger.info("=" * 60)
    
    try:
        # Test import and basic structure
        logger.info("\nImporting UDS components...")
        from __init__ import UnifiedDiagnosticSystem
        import core
        import auth
        import comms
        import enforcement
        import recovery
        
        logger.info("  ✓ All core modules imported successfully")
        
        # Verify module structure
        logger.info("\nValidating module classes...")
        assert hasattr(core, 'CoreSystem'), "CoreSystem not found"
        assert hasattr(auth, 'AuthSystem'), "AuthSystem not found"
        assert hasattr(comms, 'CommsSystem'), "CommsSystem not found"
        assert hasattr(enforcement, 'EnforcementSystem'), "EnforcementSystem not found"
        assert hasattr(recovery, 'RecoverySystem'), "RecoverySystem not found"
        
        logger.info("  ✓ All module classes present")
        
        logger.info("\n✓ TEST 3 PASSED: UDS structure validated")
        return True
        
    except Exception as e:
        logger.error(f"✗ TEST 3 FAILED: {e}", exc_info=True)
        return False


def test_evidence_locker_handlers():
    """Test that Evidence Locker module has diagnostic handlers"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 4: Validate Evidence Locker Handlers")
    logger.info("=" * 60)
    
    try:
        # Import Evidence Locker module
        evidence_locker_path = Path(__file__).parent.parent.parent.parent.parent.parent / "Evidence Locker"
        sys.path.insert(0, str(evidence_locker_path))
        
        from evidence_locker_module import EvidenceLockerModule
        
        # Check that the module has the required handler methods
        required_methods = [
            '_handle_rollcall',
            '_handle_radio_check',
            '_handle_auto_registration'
        ]
        
        logger.info("\nValidating Evidence Locker handler methods...")
        all_present = True
        for method_name in required_methods:
            if hasattr(EvidenceLockerModule, method_name):
                logger.info(f"  ✓ {method_name} - present")
            else:
                logger.error(f"  ✗ {method_name} - MISSING")
                all_present = False
        
        if all_present:
            logger.info("\n✓ TEST 4 PASSED: Evidence Locker has diagnostic handlers")
            return True
        else:
            logger.error("\n✗ TEST 4 FAILED: Evidence Locker missing handlers")
            return False
        
    except Exception as e:
        logger.error(f"✗ TEST 4 FAILED: {e}", exc_info=True)
        return False


def main():
    """Run all UDS signal fix validation tests"""
    logger.info("\n" + "=" * 80)
    logger.info("UDS SIGNAL FIX VALIDATION TEST SUITE")
    logger.info("Testing signal name corrections and handler registration")
    logger.info("=" * 80)
    
    results = {
        "Signal Names": test_signal_names(),
        "Signal Handlers": test_signal_handlers(),
        "UDS Initialization": test_uds_initialization(),
        "Evidence Locker Handlers": test_evidence_locker_handlers()
    }
    
    # Print summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    
    passed = 0
    failed = 0
    
    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    logger.info(f"\nTotal: {passed} passed, {failed} failed")
    
    if failed == 0:
        logger.info("\n✓✓✓ ALL TESTS PASSED - Signal fix validated ✓✓✓")
        return 0
    else:
        logger.error(f"\n✗✗✗ {failed} TEST(S) FAILED ✗✗✗")
        return 1


if __name__ == "__main__":
    sys.exit(main())


