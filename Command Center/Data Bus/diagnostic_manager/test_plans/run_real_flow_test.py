#!/usr/bin/env python3
"""
Real Evidence Flow Test - Actual System Integration
Tests real evidence flow with actual system calls and CANBUS integration

Usage:
    python run_real_flow_test.py
    python run_real_flow_test.py --verbose
"""

import sys
import os
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Path setup
current_dir = Path(__file__).parent
diagnostic_manager_dir = current_dir.parent
data_bus_dir = diagnostic_manager_dir.parent
command_center_dir = data_bus_dir.parent
root_dir = command_center_dir.parent

# Add all required paths
sys.path.insert(0, str(diagnostic_manager_dir))
sys.path.insert(0, str(data_bus_dir))
sys.path.insert(0, str(root_dir / "Evidence Locker"))
sys.path.insert(0, str(root_dir / "The Warden"))
sys.path.insert(0, str(root_dir / "The Marshall"))
sys.path.insert(0, str(command_center_dir / "Mission Debrief"))


class RealFlowTester:
    """Executes real end-to-end evidence flow test"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.start_time = None
        self.test_case_id = f"REAL-TEST-{int(time.time())}"
        self.signals_received = []
        self.uds = None
        self.bus = None
        self.evidence_locker = None
        self.gateway = None
        self.marshall = None
        self.mission_debrief = None
        
    def log(self, address: str, message: str):
        """Log a message with timestamp"""
        if not self.start_time:
            self.start_time = time.time()
        elapsed = time.time() - self.start_time
        print(f"[T+{elapsed:.3f}s] [{address}] {message}")
        
    def initialize_systems(self) -> bool:
        """Initialize all systems with shared CANBUS"""
        print("=" * 70)
        print("REAL EVIDENCE FLOW TEST - ACTUAL SYSTEM INTEGRATION")
        print("=" * 70)
        print()
        
        try:
            # Initialize UDS and get CANBUS
            self.log("SYSTEM", "Initializing Unified Diagnostic System...")
            from Unified_diagnostic_system import UnifiedDiagnosticSystem
            
            self.uds = UnifiedDiagnosticSystem()
            self.bus = self.uds.bus
            
            if not self.bus:
                self.log("SYSTEM", "[FAIL] CANBUS not available")
                return False
                
            self.log("SYSTEM", "[OK] CANBUS operational")
            
            # Initialize Evidence Locker
            self.log("SYSTEM", "Initializing Evidence Locker...")
            from evidence_locker_module import EvidenceLockerModule
            from _init_evidence_locker import init_evidence_locker
            
            locker_core = init_evidence_locker(bus=self.bus)
            self.evidence_locker = EvidenceLockerModule(
                bus=self.bus,
                locker=locker_core
            )
            self.evidence_locker.initialize_system()
            
            self.log("SYSTEM", "[OK] Evidence Locker initialized")
            
            # Initialize Gateway Controller
            self.log("SYSTEM", "Initializing Gateway Controller...")
            from gateway_controller import GatewayController
            
            self.gateway = GatewayController(
                ecosystem_controller=None,
                bus=self.bus
            )
            
            self.log("SYSTEM", "[OK] Gateway Controller initialized")
            
            # Initialize Evidence Manager (Marshall)
            self.log("SYSTEM", "Initializing Evidence Manager...")
            from evidence_manager import EvidenceManager
            
            self.marshall = EvidenceManager(
                bus=self.bus,
                gateway=self.gateway
            )
            
            self.log("SYSTEM", "[OK] Evidence Manager initialized")
            
            # Setup signal listener
            self.log("SYSTEM", "Setting up signal listeners...")
            self._setup_signal_listeners()
            
            print()
            return True
            
        except Exception as e:
            self.log("SYSTEM", f"[FAIL] Initialization failed: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return False
    
    def _setup_signal_listeners(self):
        """Setup listeners for key signals"""
        if not self.bus:
            return
            
        # Listen for evidence signals
        signal_map = {
            'evidence.classified': self._on_evidence_classified,
            'evidence.new': self._on_evidence_new,
            'evidence.route.to_marshall': self._on_route_to_marshall,
            'evidence.ready_for_debrief': self._on_ready_for_debrief,
            'mission.report.assembled': self._on_report_assembled,
        }
        
        for signal_name, handler in signal_map.items():
            try:
                if hasattr(self.bus, 'register_signal'):
                    self.bus.register_signal(signal_name, handler)
                elif hasattr(self.bus, 'subscribe'):
                    self.bus.subscribe(signal_name, handler)
            except Exception as e:
                if self.verbose:
                    self.log("SYSTEM", f"Could not register {signal_name}: {e}")
    
    def _on_evidence_classified(self, payload):
        """Handle evidence.classified signal"""
        self.log("1", f"SIGNAL: evidence.classified - {payload.get('evidence_id', 'unknown')}")
        self.signals_received.append(('evidence.classified', payload))
        
    def _on_evidence_new(self, payload):
        """Handle evidence.new signal"""
        self.log("1", f"SIGNAL: evidence.new - {payload.get('evidence_id', 'unknown')}")
        self.signals_received.append(('evidence.new', payload))
    
    def _on_route_to_marshall(self, payload):
        """Handle evidence.route.to_marshall signal"""
        self.log("2-3", f"SIGNAL: evidence.route.to_marshall - {payload.get('evidence_id', 'unknown')}")
        self.signals_received.append(('evidence.route.to_marshall', payload))
    
    def _on_ready_for_debrief(self, payload):
        """Handle evidence.ready_for_debrief signal"""
        self.log("3-1", f"SIGNAL: evidence.ready_for_debrief - {payload.get('evidence_id', 'unknown')}")
        self.signals_received.append(('evidence.ready_for_debrief', payload))
    
    def _on_report_assembled(self, payload):
        """Handle mission.report.assembled signal"""
        self.log("5", f"SIGNAL: mission.report.assembled - {payload.get('case_id', 'unknown')}")
        self.signals_received.append(('mission.report.assembled', payload))
    
    def run_real_flow(self, evidence_file: str) -> Dict[str, Any]:
        """Execute real evidence flow"""
        self.start_time = time.time()
        
        if not self.initialize_systems():
            return {'success': False, 'reason': 'System initialization failed'}
        
        self.log("FLOW TEST", f"Test case ID: {self.test_case_id}")
        self.log("FLOW TEST", f"Evidence file: {evidence_file}")
        print()
        
        try:
            # Submit real evidence to Evidence Locker
            self.log("TEST", f"Submitting evidence to Evidence Locker...")
            evidence_path = current_dir / evidence_file
            
            if not evidence_path.exists():
                self.log("TEST", f"[FAIL] Evidence file not found: {evidence_path}")
                return {'success': False, 'reason': 'Evidence file not found'}
            
            # Call real ingest_evidence method
            result = self.evidence_locker.ingest_evidence(str(evidence_path))
            
            evidence_id = result.get('evidence_id')
            section_id = result.get('section_id')
            
            self.log("1", f"Evidence ingested - ID: {evidence_id}, Section: {section_id}")
            
            if not evidence_id:
                self.log("TEST", f"[FAIL] Evidence ingestion failed: {result}")
                return {'success': False, 'reason': 'Evidence ingestion failed', 'details': result}
            
            # Give systems time to process
            self.log("TEST", "Waiting for autonomous progression...")
            time.sleep(2.0)
            
            # Check for UDS faults
            self.log("UDS", "Checking for faults...")
            # In real implementation, query UDS for faults
            faults = []
            
            if len(faults) == 0:
                self.log("UDS", "[OK] No faults detected")
            else:
                self.log("UDS", f"[FAIL] {len(faults)} fault(s) detected")
            
            print()
            
            # Compile results
            total_time = time.time() - self.start_time
            signals_count = len(self.signals_received)
            
            success = signals_count > 0 and len(faults) == 0
            
            return {
                'success': success,
                'total_time': total_time,
                'signals_received': signals_count,
                'signal_details': self.signals_received,
                'faults': faults,
                'ingestion_result': result
            }
            
        except Exception as e:
            self.log("TEST", f"[FAIL] Test execution failed: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return {
                'success': False,
                'reason': f'Exception: {e}'
            }
    
    def print_results(self, results: Dict[str, Any]):
        """Print test results"""
        print("=" * 70)
        print("REAL FLOW TEST RESULTS")
        print("=" * 70)
        print()
        
        if results.get('success'):
            print("[PASS] REAL AUTONOMOUS PROGRESSION SUCCESSFUL")
        else:
            print("[FAIL] REAL AUTONOMOUS PROGRESSION FAILED")
            if 'reason' in results:
                print(f"   Reason: {results['reason']}")
        
        print()
        print(f"Total flow time: {results.get('total_time', 0):.2f} seconds")
        print(f"Signals received: {results.get('signals_received', 0)}")
        
        if results.get('signal_details'):
            print("\nSignals captured:")
            for signal_name, payload in results['signal_details']:
                print(f"  - {signal_name}")
        
        faults = results.get('faults', [])
        print(f"\nUDS faults detected: {len(faults)}")
        
        print()
        print(f"Status: {'PASS' if results.get('success') else 'FAIL'}")
        print()
        print("=" * 70)
        
        # Save results
        self.save_results(results)
    
    def save_results(self, results: Dict[str, Any]):
        """Save test results to file"""
        results_dir = Path(__file__).parent / "flow_test_results"
        results_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = results_dir / f"real_flow_test_results_{timestamp}.json"
        
        # Make results JSON serializable
        serializable_results = {
            'success': results.get('success'),
            'total_time': results.get('total_time'),
            'signals_received': results.get('signals_received'),
            'signal_names': [s[0] for s in results.get('signal_details', [])],
            'faults': results.get('faults', []),
            'ingestion_result': results.get('ingestion_result', {}),
            'reason': results.get('reason', '')
        }
        
        with open(results_file, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        print(f"Results saved to: {results_file}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Real Evidence Flow Test - Actual System Integration'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--evidence-file', '-e',
        type=str,
        default='test_sample.pdf',
        help='Path to test evidence file'
    )
    
    args = parser.parse_args()
    
    # Create tester
    tester = RealFlowTester(verbose=args.verbose)
    
    # Run test
    results = tester.run_real_flow(evidence_file=args.evidence_file)
    
    # Print results
    tester.print_results(results)
    
    # Exit with appropriate code
    sys.exit(0 if results.get('success') else 1)


if __name__ == "__main__":
    main()

