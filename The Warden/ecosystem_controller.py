#!/usr/bin/env python3
"""
EcosystemController - Core orchestration system for section ecosystems
Manages section lifecycle, execution order, and inter-ecosystem communication
"""

import os
import uuid
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class EcosystemState(Enum):
    """Ecosystem execution states"""
    IDLE = "idle"
    PREPARING = "preparing"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    REVISION_REQUESTED = "revision_requested"

@dataclass(frozen=True)
class FrozenSectionData:
    """Immutable section data wrapper"""
    data: Dict[str, Any]
    completed_at: str
    completed_by: str
    revision_count: int
    
    def __post_init__(self):
        """Ensure data is also frozen"""
        object.__setattr__(self, 'data', dict(self.data))

class EcosystemController:
    """Root boot node - Core controller for managing section ecosystems and their lifecycle"""
    
    def __init__(self):
        # Boot node status
        self.is_boot_node = True
        self.boot_time = datetime.now().isoformat()
        
        # Core ecosystem management
        self.ecosystems = {}
        self.section_states = {}  # Current state of each module
        self.execution_order = []
        self.completed_ecosystems = set()
        self.failed_ecosystems = set()
        self.revision_queue = []
        
        # Immutable section data storage
        self.frozen_sections = {}  # Completed sections wrapped in FrozenSectionData
        
        # Core execution tracking
        self.current_ecosystem = None
        self.execution_history = []
        self.dependency_graph = {}
        
        # State management
        self.downstream_dependencies = {}  # Track which sections depend on each section
        
        # Section registration tracking
        self.registration_log = []
        self.active_sections = set()
        
        # Gateway reference for reverse calls (optional)
        self.gateway = None
        
        # Core engine references
        self.ocr_engine = None
        self.evidence_classifier = None
        self.evidence_index = None
        self.narrative_engine = None
        
        # Preload section contracts from StaticDataFlow
        self.section_contracts = {
            "section_cp": {"depends_on": [], "title": "Cover Page", "priority": 1},
            "section_toc": {"depends_on": ["section_cp"], "title": "Table of Contents", "priority": 2},
            "section_1": {"depends_on": ["section_toc"], "title": "Case Overview", "priority": 3},
            "section_2": {"depends_on": ["section_1"], "title": "Investigation Summary", "priority": 4},
            "section_3": {"depends_on": ["section_2"], "title": "Surveillance Operations", "priority": 5},
            "section_4": {"depends_on": ["section_3"], "title": "Evidence Analysis", "priority": 6},
            "section_5": {"depends_on": ["section_4"], "title": "Financial Records", "priority": 7},
            "section_6": {"depends_on": ["section_5"], "title": "Billing Summary", "priority": 8},
            "section_7": {"depends_on": ["section_6"], "title": "Legal Compliance", "priority": 9},
            "section_8": {"depends_on": ["section_7"], "title": "Media Documentation", "priority": 10},
            "section_dp": {"depends_on": ["section_8"], "title": "Data Processing", "priority": 11},
            "section_fr": {"depends_on": ["section_dp"], "title": "Final Report", "priority": 12}
        }
        
        self.logger = logging.getLogger(__name__)
        self.logger.debug(f" EcosystemController initialized as ROOT BOOT NODE at {self.boot_time}")
        self.logger.debug(f" Preloaded {len(self.section_contracts)} section contracts")
        self.logger.info(f"EcosystemController initialized with {len(self.section_contracts)} section contracts")
    
    def inject_gateway(self, gateway_instance):
        """Inject Gateway reference for reverse calls"""
        self.gateway = gateway_instance
        self.logger.debug(" Gateway reference injected into ECC")
        self.logger.info("Gateway reference injected into ECC")
    
    def inject_engines(self, ocr_engine=None, evidence_classifier=None, evidence_index=None, narrative_engine=None):
        """Inject core engine references"""
        if ocr_engine:
            self.ocr_engine = ocr_engine
            self.logger.debug(" OCR engine injected into ECC")
            self.logger.info("OCR engine injected into ECC")
        
        if evidence_classifier:
            self.evidence_classifier = evidence_classifier
            self.logger.debug(" Evidence classifier injected into ECC")
            self.logger.info("Evidence classifier injected into ECC")
        
        if evidence_index:
            self.evidence_index = evidence_index
            self.logger.debug(" Evidence index injected into ECC")
            self.logger.info("Evidence index injected into ECC")
        
        if narrative_engine:
            self.narrative_engine = narrative_engine
            self.logger.debug(" Narrative engine injected into ECC")
            self.logger.info("Narrative engine injected into ECC")
    
    def validate_section_id(self, section_id: str) -> bool:
        """Validate section ID exists in contracts - precondition check for any operation"""
        return section_id in self.section_contracts
    
    def enforce_gateway_check(self, section_id: str, source: str):
        """Enforce Gateway validation for public entry points"""
        # Special case: "gateway" is the Marshall/Gateway Controller, not a section
        if section_id == "gateway":
            return  # Allow gateway access without validation
        
        if section_id not in self.section_contracts:
            raise ValueError(f"{source} tried to access unknown section {section_id}")
    
    def is_case_exportable(self) -> bool:
        """Hard gate - all sections must be completed before final report generation"""
        return all(section_id in self.completed_ecosystems for section_id in self.section_contracts)
    
    def register_ecosystem(self, ecosystem_id: str, ecosystem_instance: Any) -> bool:
        """Register a section ecosystem"""
        try:
            # Precondition check
            if not self.validate_section_id(ecosystem_id):
                self.logger.error(f" Invalid section ID: {ecosystem_id}")
                return False
            
            dependencies = getattr(ecosystem_instance, 'execution_dependencies', lambda: [])()
            
            self.ecosystems[ecosystem_id] = {
                'instance': ecosystem_instance,
                'state': EcosystemState.IDLE,
                'dependencies': dependencies,
                'export_dependencies': getattr(ecosystem_instance, 'export_dependencies', lambda: [])(),
                'export_priority': getattr(ecosystem_instance, 'export_priority', lambda: 0)(),
                'revision_count': 0,
                'max_reruns': getattr(ecosystem_instance, 'MAX_RERUNS', 3),
                'registered_at': datetime.now().isoformat()
            }
            ecosystem_data = self.ecosystems[ecosystem_id]
            
            # Initialize section state
            self.section_states[ecosystem_id] = EcosystemState.IDLE
            self.active_sections.add(ecosystem_id)
            
            # Build downstream dependency tracking
            for dep in dependencies:
                if dep not in self.downstream_dependencies:
                    self.downstream_dependencies[dep] = []
                if ecosystem_id not in self.downstream_dependencies[dep]:
                    self.downstream_dependencies[dep].append(ecosystem_id)
            
            # Log registration
            registration_record = {
                'ecosystem_id': ecosystem_id,
                'registered_at': datetime.now().isoformat(),
                'dependencies': dependencies,
                'max_reruns': ecosystem_data['max_reruns']
            }
            self.registration_log.append(registration_record)
            
            self.logger.debug(f" ROOT BOOT NODE: Registered ecosystem: {ecosystem_id}")
            self.logger.info(f"Registered ecosystem: {ecosystem_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register ecosystem {ecosystem_id}: {e}")
            return False
    
    def build_execution_order(self) -> List[str]:
        """Build execution order based on dependencies"""
        try:
            # Topological sort based on execution dependencies
            visited = set()
            temp_visited = set()
            order = []
            
            def visit(ecosystem_id: str):
                if ecosystem_id in temp_visited:
                    raise RuntimeError(f"Circular dependency detected involving {ecosystem_id}")
                if ecosystem_id in visited:
                    return
                
                temp_visited.add(ecosystem_id)
                
                # Visit dependencies first
                dependencies = self.ecosystems[ecosystem_id]['dependencies']
                for dep in dependencies:
                    if dep in self.ecosystems:
                        visit(dep)
                
                temp_visited.remove(ecosystem_id)
                visited.add(ecosystem_id)
                order.append(ecosystem_id)
            
            # Visit all ecosystems
            for ecosystem_id in self.ecosystems:
                if ecosystem_id not in visited:
                    visit(ecosystem_id)
            
            self.execution_order = order
            self.logger.debug(f" Execution order: {order}")
            self.logger.info(f"Execution order built: {len(order)} sections")
            return order
            
        except Exception as e:
            self.logger.error(f"Failed to build execution order: {e}")
            return []
    
    def execute_ecosystem(self, ecosystem_id: str, context: Dict[str, Any]) -> bool:
        """Execute a single ecosystem"""
        try:
            if ecosystem_id not in self.ecosystems:
                self.logger.error(f"Ecosystem {ecosystem_id} not registered")
                return False
            
            ecosystem_data = self.ecosystems[ecosystem_id]
            ecosystem_instance = ecosystem_data['instance']
            
            # Check dependencies
            dependencies = ecosystem_data['dependencies']
            for dep in dependencies:
                if dep not in self.completed_ecosystems:
                    self.logger.warning(f" Dependency {dep} not completed for {ecosystem_id}")
                    return False
            
            # Update state
            ecosystem_data['state'] = EcosystemState.EXECUTING
            self.current_ecosystem = ecosystem_id
            
            self.logger.debug(f" Executing ecosystem: {ecosystem_id}")
            self.logger.info(f"Executing ecosystem: {ecosystem_id}")
            
            # Execute ecosystem pipeline
            if hasattr(ecosystem_instance, 'run_pipeline'):
                ecosystem_instance.run_pipeline()
            elif hasattr(ecosystem_instance, 'execute'):
                ecosystem_instance.execute(context)
            else:
                self.logger.warning(f"No execution method found for {ecosystem_id}")
                return False
            
            # Mark as completed
            ecosystem_data['state'] = EcosystemState.COMPLETED
            self.completed_ecosystems.add(ecosystem_id)
            
            # Record execution
            self.execution_history.append({
                'ecosystem_id': ecosystem_id,
                'timestamp': datetime.now().isoformat(),
                'status': 'completed'
            })
            
            self.logger.debug(f"Ecosystem {ecosystem_id} completed successfully")
            self.logger.info(f"Ecosystem {ecosystem_id} completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to execute ecosystem {ecosystem_id}: {e}")
            ecosystem_data['state'] = EcosystemState.FAILED
            self.failed_ecosystems.add(ecosystem_id)
            return False
    
    def execute_all_ecosystems(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute all ecosystems in dependency order"""
        try:
            execution_order = self.build_execution_order()
            results = {
                'completed': [],
                'failed': [],
                'skipped': []
            }
            
            for ecosystem_id in execution_order:
                if ecosystem_id in self.completed_ecosystems:
                    results['skipped'].append(ecosystem_id)
                    continue
                
                success = self.execute_ecosystem(ecosystem_id, context)
                if success:
                    results['completed'].append(ecosystem_id)
                else:
                    results['failed'].append(ecosystem_id)
            
            self.logger.debug(f" Execution complete: {len(results['completed'])} completed, {len(results['failed'])} failed")
            self.logger.info(f"Execution complete: {len(results['completed'])} completed, {len(results['failed'])} failed")
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to execute ecosystems: {e}")
            return {'completed': [], 'failed': [], 'skipped': []}
    
    def request_revision(self, ecosystem_id: str, reason: str, requester: str) -> bool:
        """Request revision of a completed ecosystem"""
        try:
            # Gateway validation check
            self.enforce_gateway_check(ecosystem_id, f"Gateway.request_revision({requester})")
            
            if ecosystem_id not in self.ecosystems:
                self.logger.error(f"Ecosystem {ecosystem_id} not registered")
                return False
            
            ecosystem_data = self.ecosystems[ecosystem_id]
            
            # Check revision limits
            if ecosystem_data['revision_count'] >= ecosystem_data['max_reruns']:
                self.logger.error(f"Ecosystem {ecosystem_id} exceeded max reruns ({ecosystem_data['max_reruns']})")
                return False
            
            # Add to revision queue
            revision_request = {
                'ecosystem_id': ecosystem_id,
                'reason': reason,
                'requester': requester,
                'timestamp': datetime.now().isoformat(),
                'revision_number': ecosystem_data['revision_count'] + 1
            }
            
            self.revision_queue.append(revision_request)
            
            # Update ecosystem state
            ecosystem_data['state'] = EcosystemState.REVISION_REQUESTED
            ecosystem_data['revision_count'] += 1
            
            # Remove from completed if it was completed
            if ecosystem_id in self.completed_ecosystems:
                self.completed_ecosystems.remove(ecosystem_id)
            
            self.logger.debug(f" Revision requested for {ecosystem_id} by {requester}")
            self.logger.info(f"Revision requested for {ecosystem_id} by {requester}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to request revision for {ecosystem_id}: {e}")
            return False
    
    def get_ecosystem_status(self, ecosystem_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific ecosystem"""
        if ecosystem_id not in self.ecosystems:
            return None
        
        ecosystem_data = self.ecosystems[ecosystem_id]
        return {
            'ecosystem_id': ecosystem_id,
            'state': ecosystem_data['state'].value,
            'dependencies': ecosystem_data['dependencies'],
            'revision_count': ecosystem_data['revision_count'],
            'max_reruns': ecosystem_data['max_reruns'],
            'registered_at': ecosystem_data['registered_at']
        }
    
    def can_run(self, section_id: str) -> bool:
        """Only allows progression if logic passes"""
        try:
            # Gateway validation check
            self.enforce_gateway_check(section_id, "Gateway.can_run")
            
            # Special case: "gateway" is the Marshall/Gateway Controller, not a section
            if section_id == "gateway":
                self.logger.info("Gateway Controller can run - operational")
                return True
            
            if section_id not in self.ecosystems:
                self.logger.error(f"Section {section_id} not registered")
                return False
            
            # Check if section is already completed
            if section_id in self.completed_ecosystems:
                self.logger.info(f"Section {section_id} already completed")
                return True
            
            # Check if section is in failed state
            if section_id in self.failed_ecosystems:
                self.logger.warning(f" Section {section_id} is in failed state")
                return False
            
            # Check dependencies
            ecosystem_data = self.ecosystems[section_id]
            dependencies = ecosystem_data['dependencies']
            
            for dep in dependencies:
                if dep not in self.completed_ecosystems:
                    self.logger.warning(f" Dependency {dep} not completed for {section_id}")
                    return False
            
            # Check revision limits
            if ecosystem_data['revision_count'] >= ecosystem_data['max_reruns']:
                self.logger.error(f" Section {section_id} exceeded max reruns ({ecosystem_data['max_reruns']})")
                return False
            
            # Check if section has custom can_run logic
            ecosystem_instance = ecosystem_data['instance']
            if hasattr(ecosystem_instance, 'can_run'):
                custom_check = ecosystem_instance.can_run()
                if not custom_check:
                    self.logger.warning(f" Section {section_id} custom can_run logic failed")
                    return False
            
            self.logger.info(f"Section {section_id} can run - all checks passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to check can_run for {section_id}: {e}")
            return False
    
    def mark_complete(self, section_id: str, by_user: str = "system") -> bool:
        """Changes state, notifies system"""
        try:
            # Gateway validation check
            self.enforce_gateway_check(section_id, f"Gateway.mark_complete({by_user})")
            
            if section_id not in self.ecosystems:
                self.logger.error(f"Section {section_id} not registered")
                return False
            
            # Update ecosystem state
            ecosystem_data = self.ecosystems[section_id]
            ecosystem_data['state'] = EcosystemState.COMPLETED
            self.section_states[section_id] = EcosystemState.COMPLETED
            
            # Add to completed set
            self.completed_ecosystems.add(section_id)
            
            # Remove from failed if it was there
            if section_id in self.failed_ecosystems:
                self.failed_ecosystems.remove(section_id)
            
            # Freeze section data to prevent mutation
            frozen_data = FrozenSectionData(
                data=ecosystem_data.get('data', {}),
                completed_at=datetime.now().isoformat(),
                completed_by=by_user,
                revision_count=ecosystem_data['revision_count']
            )
            self.frozen_sections[section_id] = frozen_data
            
            # Record completion
            completion_record = {
                'section_id': section_id,
                'completed_by': by_user,
                'timestamp': datetime.now().isoformat(),
                'completion_method': 'manual_mark_complete'
            }
            self.execution_history.append(completion_record)
            
            # Notify downstream dependencies
            self._notify_downstream_completion(section_id)
            
            self.logger.debug(f"Section {section_id} marked complete by {by_user} - DATA FROZEN")
            self.logger.info(f"Section {section_id} marked complete by {by_user}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to mark complete {section_id}: {e}")
            return False
    
    def reopen(self, section_id: str, reason: str = "manual_reopen", by_user: str = "system") -> bool:
        """Drops status, resets downstream"""
        try:
            # Gateway validation check
            self.enforce_gateway_check(section_id, f"Gateway.reopen({by_user})")
            
            if section_id not in self.ecosystems:
                self.logger.error(f"Section {section_id} not registered")
                return False
            
            # Check if section was completed
            if section_id not in self.completed_ecosystems:
                self.logger.warning(f"Section {section_id} was not completed, nothing to reopen")
                return False
            
            # Reset section state
            ecosystem_data = self.ecosystems[section_id]
            ecosystem_data['state'] = EcosystemState.IDLE
            self.section_states[section_id] = EcosystemState.IDLE
            
            # Remove from completed
            self.completed_ecosystems.remove(section_id)
            
            # Unfreeze section data to allow mutation
            if section_id in self.frozen_sections:
                del self.frozen_sections[section_id]
            
            # Increment revision count
            ecosystem_data['revision_count'] += 1
            
            # Record reopen action
            reopen_record = {
                'section_id': section_id,
                'reopened_by': by_user,
                'reason': reason,
                'timestamp': datetime.now().isoformat(),
                'revision_count': ecosystem_data['revision_count']
            }
            self.execution_history.append(reopen_record)
            
            # Reset downstream dependencies
            self._reset_downstream_dependencies(section_id)
            
            self.logger.debug(f" Section {section_id} reopened by {by_user} - reason: {reason} - DATA UNFROZEN")
            self.logger.info(f"Section {section_id} reopened by {by_user} - reason: {reason}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to reopen {section_id}: {e}")
            return False
    
    def _notify_downstream_completion(self, completed_section_id: str):
        """Notify downstream sections that a dependency has completed"""
        try:
            if completed_section_id not in self.downstream_dependencies:
                return
            
            downstream_sections = self.downstream_dependencies[completed_section_id]
            
            for downstream_section in downstream_sections:
                if downstream_section in self.ecosystems:
                    ecosystem_instance = self.ecosystems[downstream_section]['instance']
                    
                    # Notify the downstream section if it has a notification method
                    if hasattr(ecosystem_instance, 'on_dependency_completed'):
                        ecosystem_instance.on_dependency_completed(completed_section_id)
                    
                    self.logger.debug(f" Notified {downstream_section} of {completed_section_id} completion")
                    self.logger.info(f"Notified {downstream_section} of {completed_section_id} completion")
            
        except Exception as e:
            self.logger.error(f"Failed to notify downstream completion: {e}")
    
    def _reset_downstream_dependencies(self, reopened_section_id: str):
        """Reset downstream sections that depend on the reopened section"""
        try:
            if reopened_section_id not in self.downstream_dependencies:
                return
            
            downstream_sections = self.downstream_dependencies[reopened_section_id]
            
            for downstream_section in downstream_sections:
                # If downstream section was completed, reopen it too
                if downstream_section in self.completed_ecosystems:
                    self.logger.debug(f" Auto-reopening downstream section {downstream_section}")
                    self.logger.info(f"Auto-reopening downstream section {downstream_section}")
                    self.reopen(downstream_section, f"dependency_{reopened_section_id}_reopened", "system")
            
        except Exception as e:
            self.logger.error(f"Failed to reset downstream dependencies: {e}")
    
    def get_section_states(self) -> Dict[str, str]:
        """Get current state of each module"""
        return {section_id: state.value for section_id, state in self.section_states.items()}
    
    def get_boot_node_status(self) -> Dict[str, Any]:
        """Get root boot node status"""
        return {
            'is_boot_node': self.is_boot_node,
            'boot_time': self.boot_time,
            'total_ecosystems': len(self.ecosystems),
            'active_sections': list(self.active_sections),
            'completed_ecosystems': len(self.completed_ecosystems),
            'failed_ecosystems': len(self.failed_ecosystems),
            'pending_revisions': len(self.revision_queue),
            'execution_order': self.execution_order,
            'current_ecosystem': self.current_ecosystem,
            'execution_history_count': len(self.execution_history),
            'registration_log_count': len(self.registration_log),
            'section_states': self.get_section_states(),
            'downstream_dependencies': self.downstream_dependencies,
            'engine_references': {
                'ocr_engine': bool(self.ocr_engine),
                'evidence_classifier': bool(self.evidence_classifier),
                'evidence_index': bool(self.evidence_index),
                'narrative_engine': bool(self.narrative_engine)
            }
        }
    
    def get_controller_status(self) -> Dict[str, Any]:
        """Get overall controller status (alias for compatibility)"""
        return self.get_boot_node_status()
    
    def is_root_boot_node(self) -> bool:
        """Confirm this is the root boot node"""
        return self.is_boot_node
    
    def get_registration_log(self) -> List[Dict[str, Any]]:
        """Get complete registration log"""
        return self.registration_log
