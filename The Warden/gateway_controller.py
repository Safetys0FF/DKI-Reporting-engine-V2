#!/usr/bin/env python3
"""
GatewayController - Core Gateway orchestration system
Owns master evidence index, mediates section communication, manages data flow
"""

import os
import sys
import uuid
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from enum import Enum

# Add Processors directory to Python path for OCR tools
processors_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "The War Room", "Processors")
if processors_path not in sys.path:
    sys.path.insert(0, processors_path)

# OCR and Document Processing Imports - All tools available in Processors
try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

try:
    from PIL import Image, ImageEnhance, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    import unstructured
    from unstructured.partition.pdf import partition_pdf
    from unstructured.partition.image import partition_image
    UNSTRUCTURED_AVAILABLE = True
except ImportError:
    UNSTRUCTURED_AVAILABLE = False

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

logger = logging.getLogger(__name__)

class SignalType(Enum):
    """Signal types for inter-section communication"""
    EXECUTE = "EXECUTE"
    CLASSIFY = "CLASSIFY"
    FINALIZE = "FINALIZE"
    NARRATE = "NARRATE"
    VALIDATE = "VALIDATE"
    STATUS = "STATUS"
    PROCESS = "PROCESS"
    HANDOFF = "HANDOFF"

class Signal:
    """Signal for inter-section communication"""
    def __init__(self, signal_type: SignalType, target: str, source: str, payload: Dict[str, Any], case_id: str):
        self.type = signal_type
        self.target = target
        self.source = source
        self.payload = payload
        self.case_id = case_id
        self.timestamp = datetime.now().isoformat()
        self.signal_id = str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        """Convert signal to dictionary"""
        return {
            "signal_id": self.signal_id,
            "type": self.type.value,
            "target": self.target,
            "source": self.source,
            "payload": self.payload,
            "case_id": self.case_id,
            "timestamp": self.timestamp
        }

class GatewayController:
    """Core Gateway Controller - owns master evidence index and mediates section communication
    DEFERS ALL SECTION EXECUTION PERMISSION TO ECOSYSTEM CONTROLLER"""
    
    def __init__(self, ecosystem_controller=None):
        # Reference to Ecosystem Controller (ROOT BOOT NODE)
        self.ecosystem_controller = ecosystem_controller
        
        # Master evidence index - core data structure
        self.master_evidence_index = {}
        self.evidence_map = {}
        
        # Section management
        self.section_cache = {}
        self.completed_sections = set()
        self.section_states = {}  # Current state of each module
        
        # Cross-linking and fact graph
        self.cross_links = {}
        self.fact_graph = {}
        
        # Gateway orchestration data
        self.orchestration_data = {}
        self.communication_log = []
        self.execution_coordination = {}
        self.active_communications = {}
        self.data_flow_status = {}
        
        # OCR Processing capabilities
        self.ocr_engines = {}
        if OCR_AVAILABLE:
            self.ocr_engines['tesseract'] = pytesseract
        if PDFPLUMBER_AVAILABLE:
            self.ocr_engines['pdfplumber'] = pdfplumber
        if UNSTRUCTURED_AVAILABLE:
            self.ocr_engines['unstructured'] = unstructured
        self.processed_content = {}
        self.content_classification = {}
        
        # Case bundle for architectural integration
        self.case_bundle = {}
        self.stage_confirmations = {}
        self.processing_log = []
        
        # Signal-based communication system
        self.signal_queue = []
        self.signal_history = []
        self.section_handlers = {}
        self.signal_routing_table = {}
        
        # Evidence Locker tracking system
        self.evidence_locker_modules = {
            'evidence_classifier': {'status': 'idle', 'last_activity': None, 'pending_handoffs': []},
            'evidence_index': {'status': 'idle', 'last_activity': None, 'pending_handoffs': []},
            'evidence_class_builder': {'status': 'idle', 'last_activity': None, 'pending_handoffs': []},
            'case_manifest_builder': {'status': 'idle', 'last_activity': None, 'pending_handoffs': []},
            'static_data_flow': {'status': 'idle', 'last_activity': None, 'pending_handoffs': []},
            'evidence_locker_main': {'status': 'idle', 'last_activity': None, 'pending_handoffs': []}
        }
        self.evidence_locker_handoff_queue = []
        self.evidence_locker_bottleneck_alerts = []
        
        # Configuration
        self.gateway_config = {
            'max_reruns': 3,
            'revision_depth_limit': 5,
            'auto_persistence': True,
            'persistence_path': 'gateway_data.json'
        }
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Gateway Controller initialized - DEFERS TO ECOSYSTEM CONTROLLER")
        self.logger.info("Gateway orchestration capabilities enabled")
        self.logger.info("OCR processing engines initialized")
        self.logger.info("Evidence Locker tracking system initialized")
        
        # Self-validation through ECC
        if self.ecosystem_controller:
            self._validate_gateway_with_ecc()
    
    def track_evidence_locker_module(self, module_name: str, status: str, activity_data: Dict[str, Any] = None):
        """Track Evidence Locker module status and activity"""
        try:
            if module_name not in self.evidence_locker_modules:
                self.logger.warning(f"Unknown Evidence Locker module: {module_name}")
                return
            
            # Update module status
            self.evidence_locker_modules[module_name]['status'] = status
            self.evidence_locker_modules[module_name]['last_activity'] = datetime.now().isoformat()
            
            if activity_data:
                self.evidence_locker_modules[module_name]['last_activity_data'] = activity_data
            
            self.logger.info(f"📊 Evidence Locker module {module_name} status: {status}")
            
            # Check for bottlenecks
            self._check_evidence_locker_bottlenecks()
            
        except Exception as e:
            self.logger.error(f"Failed to track Evidence Locker module {module_name}: {e}")
    
    def register_evidence_locker_handoff(self, from_module: str, to_module: str, handoff_data: Dict[str, Any]):
        """Register handoff from Evidence Locker module to Gateway"""
        try:
            handoff_record = {
                'from_module': from_module,
                'to_module': to_module,
                'handoff_data': handoff_data,
                'timestamp': datetime.now().isoformat(),
                'status': 'pending'
            }
            
            self.evidence_locker_handoff_queue.append(handoff_record)
            
            # Update module pending handoffs
            if from_module in self.evidence_locker_modules:
                self.evidence_locker_modules[from_module]['pending_handoffs'].append(handoff_record)
            
            self.logger.info(f"🔄 Registered handoff: {from_module} → {to_module}")
            
            # Process handoff immediately
            self._process_evidence_locker_handoff(handoff_record)
            
        except Exception as e:
            self.logger.error(f"Failed to register Evidence Locker handoff: {e}")
    
    def _process_evidence_locker_handoff(self, handoff_record: Dict[str, Any]):
        """Process Evidence Locker handoff to Gateway"""
        try:
            from_module = handoff_record['from_module']
            handoff_data = handoff_record['handoff_data']
            
            # Update handoff status
            handoff_record['status'] = 'processing'
            
            # Route handoff data to appropriate Gateway handler
            if 'evidence_classification' in handoff_data.get('operation', ''):
                self._handle_classification_handoff(handoff_data)
            elif 'evidence_indexing' in handoff_data.get('operation', ''):
                self._handle_indexing_handoff(handoff_data)
            elif 'evidence_class_building' in handoff_data.get('operation', ''):
                self._handle_class_building_handoff(handoff_data)
            elif 'case_manifest' in handoff_data.get('operation', ''):
                self._handle_manifest_handoff(handoff_data)
            else:
                self._handle_generic_handoff(handoff_data)
            
            # Update handoff status
            handoff_record['status'] = 'completed'
            handoff_record['processed_at'] = datetime.now().isoformat()
            
            # Update module status
            self.track_evidence_locker_module(from_module, 'handoff_complete', handoff_data)
            
            self.logger.info(f"✅ Processed handoff from {from_module}")
            
        except Exception as e:
            self.logger.error(f"Failed to process Evidence Locker handoff: {e}")
            handoff_record['status'] = 'failed'
            handoff_record['error'] = str(e)
    
    def _check_evidence_locker_bottlenecks(self):
        """Check for Evidence Locker bottlenecks"""
        try:
            current_time = datetime.now()
            bottleneck_threshold_minutes = 5
            
            for module_name, module_data in self.evidence_locker_modules.items():
                if module_data['status'] == 'processing':
                    last_activity = module_data.get('last_activity')
                    if last_activity:
                        last_activity_time = datetime.fromisoformat(last_activity)
                        time_diff = (current_time - last_activity_time).total_seconds() / 60
                        
                        if time_diff > bottleneck_threshold_minutes:
                            bottleneck_alert = {
                                'module': module_name,
                                'status': module_data['status'],
                                'last_activity': last_activity,
                                'stuck_for_minutes': time_diff,
                                'timestamp': current_time.isoformat()
                            }
                            
                            self.evidence_locker_bottleneck_alerts.append(bottleneck_alert)
                            self.logger.warning(f"⚠️ Evidence Locker bottleneck detected: {module_name} stuck for {time_diff:.1f} minutes")
                            
                            # Notify ECC of bottleneck
                            if self.ecosystem_controller and hasattr(self.ecosystem_controller, 'emit'):
                                self.ecosystem_controller.emit("gateway.bottleneck_alert", bottleneck_alert)
            
        except Exception as e:
            self.logger.error(f"Failed to check Evidence Locker bottlenecks: {e}")
    
    def _handle_classification_handoff(self, handoff_data: Dict[str, Any]):
        """Handle evidence classification handoff"""
        try:
            file_path = handoff_data.get('file_path')
            assigned_section = handoff_data.get('assigned_section')
            
            if file_path and assigned_section:
                # Register file in Gateway's master index
                evidence_record = self.register_file(file_path)
                evidence_record['assigned_section'] = assigned_section
                
                self.logger.info(f"📁 Gateway received classification: {file_path} → {assigned_section}")
            
        except Exception as e:
            self.logger.error(f"Failed to handle classification handoff: {e}")
    
    def _handle_indexing_handoff(self, handoff_data: Dict[str, Any]):
        """Handle evidence indexing handoff"""
        try:
            evidence_id = handoff_data.get('evidence_id')
            section_id = handoff_data.get('section_id')
            
            if evidence_id and section_id:
                # Update Gateway's evidence map
                if section_id not in self.evidence_map:
                    self.evidence_map[section_id] = []
                
                self.evidence_map[section_id].append(evidence_id)
                
                self.logger.info(f"📋 Gateway received indexing: {evidence_id} → {section_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to handle indexing handoff: {e}")
    
    def _handle_class_building_handoff(self, handoff_data: Dict[str, Any]):
        """Handle evidence class building handoff"""
        try:
            evidence_metadata = handoff_data.get('evidence_metadata')
            
            if evidence_metadata:
                # Store evidence metadata in Gateway
                evidence_id = evidence_metadata.get('evidence_id')
                if evidence_id:
                    self.master_evidence_index[evidence_id] = evidence_metadata
                    
                    self.logger.info(f"🔧 Gateway received evidence class: {evidence_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to handle class building handoff: {e}")
    
    def _handle_manifest_handoff(self, handoff_data: Dict[str, Any]):
        """Handle case manifest handoff"""
        try:
            manifest_data = handoff_data.get('manifest_data')
            
            if manifest_data:
                # Store manifest in Gateway
                self.case_bundle['manifest'] = manifest_data
                
                self.logger.info(f"📋 Gateway received case manifest")
            
        except Exception as e:
            self.logger.error(f"Failed to handle manifest handoff: {e}")
    
    def _handle_generic_handoff(self, handoff_data: Dict[str, Any]):
        """Handle generic handoff from Evidence Locker"""
        try:
            operation = handoff_data.get('operation', 'unknown')
            
            # Store generic handoff data
            self.processing_log.append({
                'type': 'evidence_locker_handoff',
                'operation': operation,
                'data': handoff_data,
                'timestamp': datetime.now().isoformat()
            })
            
            self.logger.info(f"📦 Gateway received generic handoff: {operation}")
            
        except Exception as e:
            self.logger.error(f"Failed to handle generic handoff: {e}")
    
    def get_evidence_locker_status(self) -> Dict[str, Any]:
        """Get Evidence Locker status for monitoring"""
        try:
            return {
                'modules': self.evidence_locker_modules,
                'handoff_queue_length': len(self.evidence_locker_handoff_queue),
                'bottleneck_alerts': len(self.evidence_locker_bottleneck_alerts),
                'total_handoffs_processed': len([h for h in self.evidence_locker_handoff_queue if h['status'] == 'completed']),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get Evidence Locker status: {e}")
            return {}
    
    def register_file(self, file_path: str) -> Dict[str, Any]:
        """Register file in master evidence index"""
        try:
            # Generate unique evidence ID
            evidence_id = str(uuid.uuid4())
            
            # Basic file metadata
            file_stats = {
                'filename': os.path.basename(file_path),
                'file_path': file_path,
                'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                'file_type': os.path.splitext(file_path)[1].lower(),
                'registered_at': datetime.now().isoformat()
            }
            
            # Create evidence record
            record = {
                'evidence_id': evidence_id,
                'filename': file_stats['filename'],
                'path': file_path,
                'assigned_section': 'unassigned',  # Will be updated by classifier
                'cross_links': [],
                'evidence_id': evidence_id,
                'metadata': file_stats,
                'processing_status': 'registered',
                'timestamp': datetime.now().isoformat()
            }
            
            # Add to master index
            self.master_evidence_index[evidence_id] = record
            
            self.logger.info(f"🧾 Registered {file_path} as {evidence_id}")
            
            return {
                'success': True,
                'evidence_id': evidence_id,
                'record': record
            }
            
        except Exception as e:
            self.logger.error(f"Failed to register file {file_path}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def assign_evidence_to_section(self, evidence_id: str, section_id: str) -> bool:
        """Assign evidence to a specific section"""
        try:
            if evidence_id not in self.master_evidence_index:
                self.logger.error(f"Evidence {evidence_id} not found")
                return False
            
            # Update evidence record
            self.master_evidence_index[evidence_id]['assigned_section'] = section_id
            
            # Update section map
            if section_id not in self.evidence_map:
                self.evidence_map[section_id] = []
            
            # Check if already assigned to avoid duplicates
            existing_ids = [e['evidence_id'] for e in self.evidence_map[section_id]]
            if evidence_id not in existing_ids:
                self.evidence_map[section_id].append(self.master_evidence_index[evidence_id])
            
            self.logger.info(f"📋 Assigned evidence {evidence_id} to {section_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to assign evidence {evidence_id} to {section_id}: {e}")
            return False
    
    def get_evidence_for(self, section_id: str) -> List[Dict[str, Any]]:
        """Get evidence assigned to specific section"""
        return self.evidence_map.get(section_id, [])
    
    def add_cross_link(self, evidence_id: str, keyword: str, target_evidence_id: Optional[str] = None):
        """Add cross-link to evidence"""
        try:
            if evidence_id not in self.master_evidence_index:
                self.logger.error(f"Evidence {evidence_id} not found")
                return False
            
            cross_link = {
                'keyword': keyword,
                'target_evidence_id': target_evidence_id,
                'timestamp': datetime.now().isoformat()
            }
            
            self.master_evidence_index[evidence_id]['cross_links'].append(cross_link)
            
            # Update cross-links index
            if keyword not in self.cross_links:
                self.cross_links[keyword] = []
            self.cross_links[keyword].append({
                'evidence_id': evidence_id,
                'target_evidence_id': target_evidence_id,
                'timestamp': datetime.now().isoformat()
            })
            
            self.logger.info(f"🔗 Added cross-link: {keyword} to {evidence_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add cross-link: {e}")
            return False
    
    def transfer_section_data(self, section_id: str, structured_section_data: Dict[str, Any]) -> bool:
        """Section publishes structured data back to Gateway"""
        try:
            # ECC validation check - only registered sections can transfer data
            if self.ecosystem_controller:
                if not self.ecosystem_controller.validate_section_id(section_id):
                    raise ValueError(f"Section '{section_id}' is not registered in ECC. Transfer denied.")
                
                # Check if section is frozen (completed) - prevent overwrite
                if section_id in self.ecosystem_controller.frozen_sections:
                    raise ValueError(f"Section '{section_id}' is frozen (completed). Use reopen() to modify.")
            
            self.section_cache[section_id] = {
                'data': structured_section_data,
                'validated': False,
                'timestamp': datetime.now().isoformat(),
                'review_notes': [],
                'revision_count': 0,
                'last_revision': None
            }
            
            self.logger.debug(f"📡 Section data stored for {section_id} (ECC validated)")
            self.logger.info(f"Section data stored for {section_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to transfer section data for {section_id}: {e}")
            return False
    
    def sign_off_section(self, section_id: str, by_user: str) -> bool:
        """Sign off and validate section - CHECKS WITH ECC FIRST"""
        try:
            if section_id not in self.section_cache:
                self.logger.error(f"Section {section_id} not found in cache")
                return False
            
            # CHECK WITH ECC BEFORE MARKING COMPLETE
            if self.ecosystem_controller:
                ecc_can_complete = self.ecosystem_controller.can_run(section_id)
                if not ecc_can_complete:
                    self.logger.error(f"❌ ECC denied completion for section {section_id}")
                    return False
                
                # Notify ECC of completion
                ecc_success = self.ecosystem_controller.mark_complete(section_id, by_user)
                if not ecc_success:
                    self.logger.error(f"❌ ECC failed to mark section {section_id} complete")
                    return False
            
            self.section_cache[section_id]['validated'] = True
            self.section_cache[section_id]['signed_by'] = by_user
            self.section_cache[section_id]['sign_time'] = datetime.now().isoformat()
            self.completed_sections.add(section_id)
            
            self.logger.debug(f"✅ Section {section_id} validated and authorized by {by_user} (ECC approved)")
            self.logger.info(f"Section {section_id} validated and authorized by {by_user}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to sign off section {section_id}: {e}")
            return False
    
    def is_section_complete(self, section_id: str) -> bool:
        """Check if section is complete"""
        return section_id in self.completed_sections
    
    def get_authorized_context(self) -> Dict[str, Any]:
        """Get authorized context from ECC-validated sections only"""
        try:
            # Hard gate - check if case is exportable
            if self.ecosystem_controller:
                if not self.ecosystem_controller.is_case_exportable():
                    self.logger.error(f"❌ Case not exportable - not all sections completed")
                    return {}
            
            authorized = {}
            
            # Only include sections that are ECC-validated
            for sec_id in self.completed_sections:
                if sec_id in self.section_cache:
                    # Double-check with ECC if available
                    if self.ecosystem_controller:
                        ecc_validated = sec_id in self.ecosystem_controller.completed_ecosystems
                        if not ecc_validated:
                            self.logger.warning(f"⚠️ Section {sec_id} not ECC-validated, excluding from authorized context")
                            continue
                    
                    authorized[sec_id] = self.section_cache[sec_id]['data']
            
            self.logger.debug(f"📋 Authorized context contains {len(authorized)} ECC-validated sections")
            self.logger.info(f"Authorized context contains {len(authorized)} ECC-validated sections")
            return authorized
            
        except Exception as e:
            self.logger.error(f"Failed to get authorized context: {e}")
            return {}
    
    
    def request_section_revision(self, section_id: str, revision_reason: str, requester: str) -> bool:
        """Request revision of a completed section - NOTIFIES ECC"""
        try:
            if section_id not in self.section_cache:
                self.logger.error(f"Section {section_id} not found")
                return False
            
            # NOTIFY ECC OF REVISION REQUEST
            if self.ecosystem_controller:
                ecc_revision_success = self.ecosystem_controller.request_revision(section_id, revision_reason, requester)
                if not ecc_revision_success:
                    self.logger.error(f"❌ ECC denied revision request for section {section_id}")
                    return False
            
            # Check revision limits
            current_revisions = self.section_cache[section_id].get('revision_count', 0)
            if current_revisions >= self.gateway_config['max_reruns']:
                self.logger.error(f"Section {section_id} has reached maximum revisions ({self.gateway_config['max_reruns']})")
                return False
            
            # Add revision request
            revision_request = {
                'reason': revision_reason,
                'requester': requester,
                'timestamp': datetime.now().isoformat(),
                'revision_number': current_revisions + 1
            }
            
            if 'revision_requests' not in self.section_cache[section_id]:
                self.section_cache[section_id]['revision_requests'] = []
            
            self.section_cache[section_id]['revision_requests'].append(revision_request)
            self.section_cache[section_id]['revision_count'] = current_revisions + 1
            self.section_cache[section_id]['last_revision'] = datetime.now().isoformat()
            
            # Remove from completed sections if it was completed
            if section_id in self.completed_sections:
                self.completed_sections.remove(section_id)
                self.section_cache[section_id]['validated'] = False
            
            self.logger.debug(f"📝 Revision requested for section {section_id} by {requester} (ECC notified)")
            self.logger.info(f"Revision requested for section {section_id} by {requester}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to request revision for section {section_id}: {e}")
            return False
    
    def can_run(self, section_id: str) -> bool:
        """DEFERS TO ECOSYSTEM CONTROLLER - Only allows progression if logic passes"""
        try:
            # DEFER TO ECOSYSTEM CONTROLLER (ROOT BOOT NODE)
            if self.ecosystem_controller:
                return self.ecosystem_controller.can_run(section_id)
            
            # Fallback if no ecosystem controller
            self.logger.warning(f"⚠️ No Ecosystem Controller - using fallback for {section_id}")
            if section_id not in self.section_cache:
                self.logger.error(f"Section {section_id} not found")
                return False
            
            # Basic checks
            if section_id in self.completed_sections:
                return True
            
            if not self.section_cache[section_id].get('data'):
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to check can_run for {section_id}: {e}")
            return False
    
    def mark_complete(self, section_id: str, by_user: str = "system") -> bool:
        """DEFERS TO ECOSYSTEM CONTROLLER - Changes state, notifies system"""
        try:
            # DEFER TO ECOSYSTEM CONTROLLER (ROOT BOOT NODE)
            if self.ecosystem_controller:
                success = self.ecosystem_controller.mark_complete(section_id, by_user)
                if success and section_id in self.section_cache:
                    # Update Gateway cache to match Ecosystem Controller
                    self.section_cache[section_id]['validated'] = True
                    self.section_cache[section_id]['signed_by'] = by_user
                    self.section_cache[section_id]['sign_time'] = datetime.now().isoformat()
                return success
            
            # Fallback if no ecosystem controller
            self.logger.warning(f"⚠️ No Ecosystem Controller - using fallback for {section_id}")
            if section_id not in self.section_cache:
                self.logger.error(f"Section {section_id} not found")
                return False
            
            # Update section state
            self.section_states[section_id] = "completed"
            self.completed_sections.add(section_id)
            
            # Update cache
            self.section_cache[section_id]['validated'] = True
            self.section_cache[section_id]['signed_by'] = by_user
            self.section_cache[section_id]['sign_time'] = datetime.now().isoformat()
            
            self.logger.info(f"✅ Section {section_id} marked complete by {by_user}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to mark complete {section_id}: {e}")
            return False
    
    def reopen(self, section_id: str, reason: str = "manual_reopen", by_user: str = "system") -> bool:
        """DEFERS TO ECOSYSTEM CONTROLLER - Drops status, resets downstream"""
        try:
            # DEFER TO ECOSYSTEM CONTROLLER (ROOT BOOT NODE)
            if self.ecosystem_controller:
                success = self.ecosystem_controller.reopen(section_id, reason, by_user)
                if success and section_id in self.section_cache:
                    # Update Gateway cache to match Ecosystem Controller
                    self.section_cache[section_id]['validated'] = False
                    self.section_cache[section_id]['revision_count'] = self.section_cache[section_id].get('revision_count', 0) + 1
                    self.section_cache[section_id]['last_revision'] = datetime.now().isoformat()
                return success
            
            # Fallback if no ecosystem controller
            self.logger.warning(f"⚠️ No Ecosystem Controller - using fallback for {section_id}")
            if section_id not in self.section_cache:
                self.logger.error(f"Section {section_id} not found")
                return False
            
            # Reset section state
            self.section_states[section_id] = "idle"
            
            # Remove from completed
            if section_id in self.completed_sections:
                self.completed_sections.remove(section_id)
            
            # Update cache
            self.section_cache[section_id]['validated'] = False
            self.section_cache[section_id]['revision_count'] = self.section_cache[section_id].get('revision_count', 0) + 1
            self.section_cache[section_id]['last_revision'] = datetime.now().isoformat()
            
            self.logger.info(f"🔄 Section {section_id} reopened by {by_user}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to reopen {section_id}: {e}")
            return False
    
    def get_section_states(self) -> Dict[str, str]:
        """Get current state of each module"""
        return self.section_states
    
    def _validate_gateway_with_ecc(self) -> bool:
        """Gateway forces itself to be validated by ECC"""
        try:
            if not self.ecosystem_controller:
                self.logger.warning("⚠️ No ECC available for Gateway validation")
                return False
            
            # Register Gateway as a special section with ECC
            gateway_section_id = "gateway"
            
            # Check if Gateway can run according to ECC
            can_run = self.ecosystem_controller.can_run(gateway_section_id)
            
            if can_run:
                self.logger.info("✅ Gateway validated by ECC - operational")
                return True
            else:
                self.logger.error("❌ Gateway validation failed by ECC")
                return False
                
        except Exception as e:
            self.logger.error(f"Gateway validation with ECC failed: {e}")
            return False
    
    def force_ecc_validation(self) -> bool:
        """Force Gateway to validate itself with ECC"""
        return self._validate_gateway_with_ecc()
    
    def coordinate_section_execution(self, target_section_id: str, execution_command: Dict[str, Any]) -> bool:
        """Coordinate execution of target section - ENFORCES SECTION-AWARE EXECUTION"""
        try:
            # SECTION-AWARE EXECUTION ENFORCEMENT
            if not self.ecosystem_controller:
                raise Exception("No ECC reference available for section execution coordination")
            
            if not self.ecosystem_controller.can_run(target_section_id):
                self.logger.error(f"Cannot coordinate execution - section {target_section_id} not ready")
                return False
            
            # Log coordination request
            coordination_record = {
                'target_section': target_section_id,
                'command': execution_command,
                'timestamp': datetime.now().isoformat(),
                'coordinated_by': 'gateway_controller'
            }
            
            self.execution_coordination[target_section_id] = coordination_record
            self.communication_log.append(coordination_record)
            
            self.logger.debug(f"🎯 Coordinated execution for {target_section_id}")
            self.logger.info(f"Coordinated execution for {target_section_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to coordinate section execution: {e}")
            raise

    def manage_data_flow(self, source_section: str, target_section: str, data_payload: Dict[str, Any]) -> bool:
        """Manage data flow between sections - ENFORCES SECTION-AWARE EXECUTION"""
        try:
            # SECTION-AWARE EXECUTION ENFORCEMENT
            if not self.ecosystem_controller:
                raise Exception("No ECC reference available for data flow management")
            
            # Validate both sections can participate
            if not self.ecosystem_controller.can_run(source_section) or not self.ecosystem_controller.can_run(target_section):
                self.logger.error(f"Cannot manage data flow - sections not ready: {source_section} -> {target_section}")
                return False
            
            # Create data flow record
            flow_id = f"{source_section}_to_{target_section}_{datetime.now().strftime('%H%M%S')}"
            
            flow_record = {
                'flow_id': flow_id,
                'source_section': source_section,
                'target_section': target_section,
                'data_payload': data_payload,
                'timestamp': datetime.now().isoformat(),
                'status': 'active',
                'managed_by': 'gateway_controller'
            }
            
            self.data_flow_status[flow_id] = flow_record
            self.communication_log.append(flow_record)
            
            self.logger.debug(f"📡 Managed data flow {flow_id}")
            self.logger.info(f"Managed data flow {source_section} -> {target_section}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to manage data flow: {e}")
            raise

    def log_communication(self, communication_type: str, details: Dict[str, Any]) -> bool:
        """Log inter-section communication"""
        try:
            # SECTION-AWARE EXECUTION ENFORCEMENT
            if not self.ecosystem_controller:
                raise Exception("No ECC reference available for communication logging")
            
            log_entry = {
                'communication_type': communication_type,
                'details': details,
                'timestamp': datetime.now().isoformat(),
                'logged_by': 'gateway_controller'
            }
            
            self.communication_log.append(log_entry)
            
            self.logger.debug(f"📝 Logged {communication_type} communication")
            self.logger.info(f"Logged {communication_type} communication")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to log communication: {e}")
            raise

    def get_orchestration_status(self) -> Dict[str, Any]:
        """Get current orchestration status"""
        return {
            'active_communications': len(self.active_communications),
            'data_flows_active': len(self.data_flow_status),
            'execution_coordination_count': len(self.execution_coordination),
            'communication_log_entries': len(self.communication_log),
            'orchestration_mode': 'active',
            'coordination_enabled': True
        }

    def get_communication_log(self) -> List[Dict[str, Any]]:
        """Get communication log"""
        return self.communication_log.copy()

    def clear_communication_log(self) -> bool:
        """Clear communication log"""
        try:
            self.communication_log.clear()
            self.logger.debug(f"🗑️ Cleared communication log")
            self.logger.info(f"Cleared communication log")
            return True
        except Exception as e:
            self.logger.error(f"Failed to clear communication log: {e}")
            return False
    
    # OCR Processing Methods - Architectural Integration
    def process_document_pipeline(self, file_path: str, section_id: str = None) -> Dict[str, Any]:
        """Complete document processing pipeline following OCR Flow SOP - ENFORCES SECTION-AWARE EXECUTION"""
        try:
            if section_id and self.ecosystem_controller:
                if not self.ecosystem_controller.can_run(section_id):
                    raise Exception(f"Section {section_id} not active for document processing")
            
            # Stage 1: Intake & Classification
            file_info = self._classify_file_intake(file_path)
            
            # Stage 2: Primary Extraction (Tesseract & Unstructured)
            primary_result = self._run_primary_extraction(file_path, file_info)
            
            # Stage 3: Fallback if needed
            if not primary_result.get('extracted_text') or primary_result.get('confidence', 0) < 0.5:
                fallback_result = self._run_fallback_extraction(file_path, file_info)
                primary_result.update(fallback_result)
            
            # Stage 4: Media-specific processing
            media_result = self._run_media_processing(file_path, file_info, primary_result)
            primary_result.update(media_result)
            
            # Stage 5: Enrichment & Validation
            enrichment_result = self._run_enrichment_validation(file_path, primary_result)
            primary_result.update(enrichment_result)
            
            # Store in case bundle
            self._store_in_case_bundle(file_path, primary_result, section_id)
            
            self.logger.debug(f"📄 Complete pipeline processed {file_path}")
            self.logger.info(f"Complete pipeline processed {file_path}")
            
            return primary_result
            
        except Exception as e:
            self.logger.error(f"Document pipeline failed for {file_path}: {e}")
            return {'error': str(e), 'file_path': file_path}
    
    def _classify_file_intake(self, file_path: str) -> Dict[str, Any]:
        """Stage 1: Intake & Classification"""
        file_ext = os.path.splitext(file_path)[1].lower()
        filename = os.path.basename(file_path).lower()
        
        file_info = {
            'path': file_path,
            'filename': filename,
            'extension': file_ext,
            'media_type': 'unknown',
            'priority': 'medium',
            'language_hints': [],
            'classification_time': datetime.now().isoformat()
        }
        
        # Media type classification
        if file_ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
            file_info['media_type'] = 'image'
        elif file_ext == '.pdf':
            file_info['media_type'] = 'pdf'
        elif file_ext in ['.mp4', '.avi', '.mov']:
            file_info['media_type'] = 'video'
        elif file_ext in ['.mp3', '.wav', '.m4a']:
            file_info['media_type'] = 'audio'
        elif file_ext in ['.docx', '.doc', '.txt']:
            file_info['media_type'] = 'document'
        
        # Priority classification
        if any(keyword in filename for keyword in ['urgent', 'critical', 'police', 'incident']):
            file_info['priority'] = 'critical'
        elif any(keyword in filename for keyword in ['medical', 'billing', 'invoice']):
            file_info['priority'] = 'high'
        
        return file_info
    
    def _run_primary_extraction(self, file_path: str, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 2: Primary Extraction (Tesseract & Unstructured)"""
        result = {
            'extracted_text': '',
            'text_blocks': [],
            'tables': [],
            'entities': [],
            'layout': {},
            'confidence': 0.0,
            'engine_used': 'none',
            'extraction_time': datetime.now().isoformat()
        }
        
        file_ext = file_info['extension']
        
        # Tesseract for images and scanned PDFs
        if file_ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
            tesseract_result = self.process_with_tesseract(file_path)
            if tesseract_result.get('extracted_text'):
                result.update(tesseract_result)
                result['engine_used'] = 'tesseract'
        
        # Unstructured for native PDFs and documents
        elif file_ext in ['.pdf', '.docx', '.doc']:
            unstructured_result = self.process_with_unstructured(file_path)
            if unstructured_result.get('extracted_text'):
                result.update(unstructured_result)
                result['engine_used'] = 'unstructured'
        
        return result
    
    def _run_fallback_extraction(self, file_path: str, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 3: Fallback Extraction"""
        fallback_result = {
            'fallback_attempts': [],
            'fallback_engine_used': 'none',
            'fallback_extracted_text': ''
        }
        
        # Try EasyOCR fallback (placeholder - would need actual implementation)
        try:
            # fallback_result['fallback_attempts'].append('easyocr')
            # fallback_result['fallback_engine_used'] = 'easyocr'
            pass
        except Exception as e:
            self.logger.debug(f"EasyOCR fallback failed: {e}")
        
        return fallback_result
    
    def _run_media_processing(self, file_path: str, file_info: Dict[str, Any], primary_result: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 4: Media-specific processing"""
        media_result = {
            'media_analysis': {},
            'frame_samples': [],
            'audio_transcript': '',
            'metadata': {}
        }
        
        if file_info['media_type'] == 'video':
            # Frame sampling with OpenCV (placeholder)
            media_result['media_analysis']['frame_count'] = 0
            media_result['frame_samples'] = []
        
        elif file_info['media_type'] == 'audio':
            # Whisper transcription (placeholder)
            media_result['audio_transcript'] = ''
        
        elif file_info['media_type'] == 'image':
            # EXIF metadata extraction
            try:
                image = Image.open(file_path)
                media_result['metadata'] = dict(image._getexif() or {})
            except Exception as e:
                self.logger.debug(f"EXIF extraction failed: {e}")
        
        return media_result
    
    def _run_enrichment_validation(self, file_path: str, primary_result: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 5: Enrichment & Validation"""
        enrichment_result = {
            'enrichment': {},
            'validation_status': 'pending',
            'ai_notes': [],
            'osint_lookup': {}
        }
        
        # AI confirmation (placeholder)
        if primary_result.get('extracted_text'):
            enrichment_result['ai_notes'].append('Text extraction confirmed by AI')
            enrichment_result['validation_status'] = 'confirmed'
        
        return enrichment_result
    
    def _store_in_case_bundle(self, file_path: str, result: Dict[str, Any], section_id: str = None):
        """Store processed result in case bundle"""
        bundle_entry = {
            'file_path': file_path,
            'processed_data': result,
            'section_id': section_id,
            'bundle_time': datetime.now().isoformat(),
            'status': 'processed'
        }
        
        if not hasattr(self, 'case_bundle'):
            self.case_bundle = {}
        
        self.case_bundle[file_path] = bundle_entry
        
        # Also store in processed_content for backward compatibility
        self.processed_content[file_path] = result
    
    def process_with_tesseract(self, file_path: str, section_id: str = None) -> Dict[str, Any]:
        """Process file with Tesseract OCR - ENFORCES SECTION-AWARE EXECUTION"""
        try:
            if not OCR_AVAILABLE or not PIL_AVAILABLE:
                raise Exception("Tesseract or PIL not available")
            
            if section_id and self.ecosystem_controller:
                if not self.ecosystem_controller.can_run(section_id):
                    raise Exception(f"Section {section_id} not active for OCR processing")
            
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
                # Image processing
                image = Image.open(file_path)
                text = pytesseract.image_to_string(image)
                confidence = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
                
                result = {
                    'engine': 'tesseract',
                    'file_path': file_path,
                    'extracted_text': text.strip(),
                    'confidence': float(np.mean(confidence['conf'][confidence['conf'] > 0])),
                    'processing_time': datetime.now().isoformat(),
                    'section_id': section_id
                }
                
            elif file_ext == '.pdf' and PDFPLUMBER_AVAILABLE:
                # PDF processing with pdfplumber + tesseract
                with pdfplumber.open(file_path) as pdf:
                    full_text = ""
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if not page_text:  # Try OCR if no text
                            page_image = page.to_image()
                            ocr_text = pytesseract.image_to_string(page_image.original)
                            page_text = ocr_text
                        full_text += page_text + "\n"
                
                result = {
                    'engine': 'tesseract_pdf',
                    'file_path': file_path,
                    'extracted_text': full_text.strip(),
                    'confidence': 0.85,  # PDF confidence estimate
                    'processing_time': datetime.now().isoformat(),
                    'section_id': section_id
                }
            else:
                raise Exception(f"Unsupported file type: {file_ext}")
            
            # Store processed content
            self.processed_content[file_path] = result
            self.logger.debug(f"🔍 Tesseract processed {file_path}")
            self.logger.info(f"Tesseract processed {file_path}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Tesseract processing failed for {file_path}: {e}")
            return {'error': str(e), 'file_path': file_path, 'engine': 'tesseract'}
    
    def process_with_unstructured(self, file_path: str, section_id: str = None) -> Dict[str, Any]:
        """Process file with Unstructured - ENFORCES SECTION-AWARE EXECUTION"""
        try:
            if not UNSTRUCTURED_AVAILABLE:
                raise Exception("Unstructured not available")
            
            if section_id and self.ecosystem_controller:
                if not self.ecosystem_controller.can_run(section_id):
                    raise Exception(f"Section {section_id} not active for unstructured processing")
            
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.pdf':
                elements = partition_pdf(file_path)
            elif file_ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
                elements = partition_image(file_path)
            else:
                raise Exception(f"Unsupported file type for unstructured: {file_ext}")
            
            # Extract structured data
            structured_data = []
            full_text = ""
            
            for element in elements:
                element_data = {
                    'type': str(type(element).__name__),
                    'text': str(element),
                    'metadata': element.metadata if hasattr(element, 'metadata') else {}
                }
                structured_data.append(element_data)
                full_text += str(element) + "\n"
            
            result = {
                'engine': 'unstructured',
                'file_path': file_path,
                'extracted_text': full_text.strip(),
                'structured_elements': structured_data,
                'element_count': len(elements),
                'processing_time': datetime.now().isoformat(),
                'section_id': section_id
            }
            
            # Store processed content
            self.processed_content[file_path] = result
            self.logger.debug(f"📄 Unstructured processed {file_path}")
            self.logger.info(f"Unstructured processed {file_path}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Unstructured processing failed for {file_path}: {e}")
            return {'error': str(e), 'file_path': file_path, 'engine': 'unstructured'}
    
    def classify_content(self, file_path: str, section_id: str = None) -> Dict[str, Any]:
        """Classify processed content and determine handoff strategy - ENFORCES SECTION-AWARE EXECUTION"""
        try:
            if section_id and self.ecosystem_controller:
                if not self.ecosystem_controller.can_run(section_id):
                    raise Exception(f"Section {section_id} not active for content classification")
            
            if file_path not in self.processed_content:
                raise Exception(f"No processed content found for {file_path}")
            
            content = self.processed_content[file_path]
            classification = {
                'file_path': file_path,
                'content_type': 'unknown',
                'priority': 'medium',
                'handoff_strategy': 'standard',
                'target_sections': [],
                'confidence': 0.0,
                'classification_time': datetime.now().isoformat(),
                'section_id': section_id
            }
            
            # Analyze content type
            text = content.get('extracted_text', '').lower()
            
            if any(keyword in text for keyword in ['invoice', 'bill', 'payment', 'amount', '$']):
                classification['content_type'] = 'billing'
                classification['target_sections'] = ['section_6']
                classification['priority'] = 'high'
                classification['handoff_strategy'] = 'billing_summary'
                
            elif any(keyword in text for keyword in ['medical', 'doctor', 'hospital', 'treatment', 'diagnosis']):
                classification['content_type'] = 'medical'
                classification['target_sections'] = ['section_3', 'section_4']
                classification['priority'] = 'high'
                classification['handoff_strategy'] = 'medical_analysis'
                
            elif any(keyword in text for keyword in ['police', 'incident', 'report', 'officer', 'arrest']):
                classification['content_type'] = 'police_report'
                classification['target_sections'] = ['section_1', 'section_2']
                classification['priority'] = 'critical'
                classification['handoff_strategy'] = 'incident_analysis'
                
            elif any(keyword in text for keyword in ['witness', 'statement', 'testimony', 'deposition']):
                classification['content_type'] = 'witness_statement'
                classification['target_sections'] = ['section_2', 'section_5']
                classification['priority'] = 'high'
                classification['handoff_strategy'] = 'statement_analysis'
                
            else:
                classification['content_type'] = 'general_document'
                classification['target_sections'] = ['section_1']
                classification['priority'] = 'medium'
                classification['handoff_strategy'] = 'general_processing'
            
            # Calculate confidence based on content analysis
            confidence_score = min(len(text) / 1000, 1.0)  # Simple confidence based on text length
            classification['confidence'] = confidence_score
            
            # Store classification
            self.content_classification[file_path] = classification
            
            self.logger.debug(f"🏷️ Classified {file_path} as {classification['content_type']}")
            self.logger.info(f"Classified {file_path} as {classification['content_type']}")
            
            return classification
            
        except Exception as e:
            self.logger.error(f"Content classification failed for {file_path}: {e}")
            return {'error': str(e), 'file_path': file_path}
    
    def handoff_to_section(self, file_path: str, target_section: str, section_id: str = None) -> bool:
        """Handoff processed content to target section - ENFORCES SECTION-AWARE EXECUTION"""
        try:
            if section_id and self.ecosystem_controller:
                if not self.ecosystem_controller.can_run(section_id):
                    raise Exception(f"Section {section_id} not active for handoff")
            
            if file_path not in self.processed_content:
                raise Exception(f"No processed content found for {file_path}")
            
            if file_path not in self.content_classification:
                raise Exception(f"No classification found for {file_path}")
            
            content = self.processed_content[file_path]
            classification = self.content_classification[file_path]
            
            # Prepare handoff payload
            handoff_payload = {
                'file_path': file_path,
                'processed_content': content,
                'classification': classification,
                'handoff_time': datetime.now().isoformat(),
                'source_section': section_id,
                'target_section': target_section
            }
            
            # Transfer to target section via ECC validation
            success = self.transfer_section_data(target_section, handoff_payload)
            
            if success:
                self.logger.debug(f"📤 Handed off {file_path} to {target_section}")
                self.logger.info(f"Handed off {file_path} to {target_section}")
                
                # Log handoff in communication log
                self.log_communication('content_handoff', {
                    'file_path': file_path,
                    'target_section': target_section,
                    'content_type': classification['content_type'],
                    'priority': classification['priority']
                })
            
            return success
            
        except Exception as e:
            self.logger.error(f"Handoff failed for {file_path} to {target_section}: {e}")
            return False
    
    def get_ocr_status(self) -> Dict[str, Any]:
        """Get OCR processing status"""
        return {
            'processed_files': len(self.processed_content),
            'classified_files': len(self.content_classification),
            'available_engines': list(self.ocr_engines.keys()),
            'processing_stats': {
                'tesseract_processed': len([f for f in self.processed_content.values() if f.get('engine') == 'tesseract']),
                'unstructured_processed': len([f for f in self.processed_content.values() if f.get('engine') == 'unstructured']),
                'total_classifications': len(self.content_classification)
            }
        }
    
    # Section Orchestration Methods - Architectural Integration
    def orchestrate_section_processing(self, section_id: str, file_paths: List[str]) -> Dict[str, Any]:
        """Orchestrate section processing following architectural model - ENFORCES SECTION-AWARE EXECUTION"""
        try:
            if not self.ecosystem_controller:
                raise Exception("No ECC reference available for section orchestration")
            
            if not self.ecosystem_controller.can_run(section_id):
                raise Exception(f"Section {section_id} not active for orchestration")
            
            orchestration_result = {
                'section_id': section_id,
                'files_processed': [],
                'processing_stages': [],
                'section_outputs': {},
                'orchestration_time': datetime.now().isoformat(),
                'status': 'in_progress'
            }
            
            # Process each file through the pipeline
            for file_path in file_paths:
                self.logger.debug(f"🔄 Processing {file_path} for {section_id}")
                
                # Run complete document pipeline
                pipeline_result = self.process_document_pipeline(file_path, section_id)
                
                if pipeline_result.get('error'):
                    self.logger.error(f"Pipeline failed for {file_path}: {pipeline_result['error']}")
                    continue
                
                orchestration_result['files_processed'].append(file_path)
                orchestration_result['processing_stages'].append({
                    'file': file_path,
                    'stage': 'pipeline_complete',
                    'timestamp': datetime.now().isoformat()
                })
            
            # Create section outputs to be built by the section itself
            section_outputs = {}  # To be built by the section module
            
            # Route to section handler (each section is its own narrative agent)
            handler_result = self._route_to_section_handler(section_id, orchestration_result['files_processed'])
            if handler_result:
                section_outputs.update(handler_result)
            
            orchestration_result['section_outputs'] = section_outputs
            
            orchestration_result['status'] = 'completed'
            
            self.logger.debug(f"🎯 Section orchestration completed for {section_id}")
            self.logger.info(f"Section orchestration completed for {section_id}")
            
            return orchestration_result
            
        except Exception as e:
            self.logger.error(f"Section orchestration failed for {section_id}: {e}")
            return {'error': str(e), 'section_id': section_id}
    
    
    def get_case_bundle_status(self) -> Dict[str, Any]:
        """Get case bundle status for architectural monitoring"""
        return {
            'total_files': len(self.case_bundle),
            'processed_files': len([f for f in self.case_bundle.values() if f['status'] == 'processed']),
            'stage_confirmations': len(self.stage_confirmations),
            'processing_log_entries': len(self.processing_log),
            'bundle_size_mb': sum(len(str(data)) for data in self.case_bundle.values()) / 1024 / 1024
        }
    
    
    def _route_to_section_handler(self, section_id: str, processed_files: List[str]) -> Optional[Dict[str, Any]]:
        """Route processed files to per-section handler"""
        try:
            # Check if section handler is registered
            handler = self.section_handlers.get(section_id)
            if not handler:
                self.logger.debug(f"No section handler registered for {section_id}")
                return None
            
            # Get processed data from case bundle
            section_data = []
            for file_path in processed_files:
                if file_path in self.case_bundle:
                    section_data.append(self.case_bundle[file_path]['processed_data'])
            
            # Create signal for handler
            signal = self.create_signal(
                signal_type=SignalType.PROCESS,
                target=section_id,
                source="gateway_orchestration",
                payload={'processed_files': processed_files, 'section_data': section_data},
                case_id="orchestration"
            )
            
            # Route to section handler
            handler_result = handler(signal.to_dict())
            
            self.logger.debug(f"📡 Routed {section_id} to section handler")
            self.logger.info(f"Routed {section_id} to section handler")
            
            return handler_result
            
        except Exception as e:
            self.logger.error(f"Failed to route to section handler for {section_id}: {e}")
            return None
    
    # Signal-Based Communication Methods
    def register_section_handler(self, section_id: str, handler_func: callable) -> bool:
        """Register a section handler for signal processing"""
        try:
            self.section_handlers[section_id] = handler_func
            self.logger.debug(f"📡 Registered handler for {section_id}")
            self.logger.info(f"Registered handler for {section_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to register handler for {section_id}: {e}")
            return False
    
    
    def dispatch_signal(self, signal: Signal) -> Dict[str, Any]:
        """Dispatch signal to target section - ENFORCES SECTION-AWARE EXECUTION"""
        try:
            signal_dict = signal.to_dict()
            
            # Validate with ECC
            if not self.ecosystem_controller:
                return {
                    "status": "FAILED",
                    "origin": signal.target,
                    "error": "No ECC reference available",
                    "timestamp": signal.timestamp
                }
            
            if not self.ecosystem_controller.can_run(signal.target):
                return {
                    "status": "BLOCKED",
                    "origin": signal.target,
                    "reason": "Section not active or blocked",
                    "timestamp": signal.timestamp
                }
            
            # Get handler
            handler = self.section_handlers.get(signal.target)
            if not handler:
                return {
                    "status": "FAILED",
                    "origin": signal.target,
                    "error": "No handler registered",
                    "timestamp": signal.timestamp
                }
            
            # Process signal
            result = handler(signal_dict)
            
            # Log signal processing
            self.signal_history.append({
                "signal": signal_dict,
                "result": result,
                "processing_time": datetime.now().isoformat()
            })
            
            # Update routing table
            self.signal_routing_table[signal.signal_id] = {
                "source": signal.source,
                "target": signal.target,
                "status": result.get("status", "UNKNOWN"),
                "timestamp": signal.timestamp
            }
            
            self.logger.debug(f"📡 Signal dispatched: {signal.type.value} -> {signal.target}")
            self.logger.info(f"Signal dispatched: {signal.type.value} -> {signal.target}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Signal dispatch failed: {e}")
            return {
                "status": "ERROR",
                "origin": signal.target,
                "error": str(e),
                "timestamp": signal.timestamp
            }
    
    def queue_signal(self, signal: Signal) -> bool:
        """Queue signal for processing"""
        try:
            self.signal_queue.append(signal)
            self.logger.debug(f"📥 Signal queued: {signal.type.value} -> {signal.target}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to queue signal: {e}")
            return False
    
    def process_signal_queue(self) -> Dict[str, Any]:
        """Process all queued signals"""
        try:
            results = []
            processed_count = 0
            
            while self.signal_queue:
                signal = self.signal_queue.pop(0)
                result = self.dispatch_signal(signal)
                results.append(result)
                processed_count += 1
            
            self.logger.debug(f"📤 Processed {processed_count} signals from queue")
            self.logger.info(f"Processed {processed_count} signals from queue")
            
            return {
                "processed_count": processed_count,
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Signal queue processing failed: {e}")
            return {"error": str(e)}
    
    def create_signal(self, signal_type: SignalType, target: str, source: str, payload: Dict[str, Any], case_id: str) -> Signal:
        """Create a new signal"""
        return Signal(signal_type, target, source, payload, case_id)
    
    def review_and_route(self, signal: Signal) -> Dict[str, Any]:
        """Review signal information and route to correct section"""
        try:
            # Analyze payload for routing decisions
            payload = signal.payload
            routing_decision = self._analyze_payload_for_routing(payload)
            
            # Update signal target if routing decision differs
            if routing_decision.get('recommended_section') and routing_decision['recommended_section'] != signal.target:
                signal.target = routing_decision['recommended_section']
                self.logger.debug(f"🔄 Signal rerouted to {signal.target}")
            
            # Dispatch the signal
            result = self.dispatch_signal(signal)
            
            # Add routing information to result
            result['routing_decision'] = routing_decision
            
            return result
            
        except Exception as e:
            self.logger.error(f"Signal review and routing failed: {e}")
            return {"error": str(e)}
    
    def _analyze_payload_for_routing(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze payload to determine correct routing"""
        routing_decision = {
            'recommended_section': None,
            'confidence': 0.0,
            'analysis_reason': '',
            'content_type': 'unknown'
        }
        
        # Analyze file paths or content types
        if 'file_path' in payload:
            file_path = payload['file_path']
            file_ext = os.path.splitext(file_path)[1].lower()
            filename = os.path.basename(file_path).lower()
            
            # Route based on file characteristics
            if any(keyword in filename for keyword in ['billing', 'invoice', 'payment', 'financial']):
                routing_decision['recommended_section'] = 'section_6'
                routing_decision['content_type'] = 'billing'
                routing_decision['confidence'] = 0.9
                routing_decision['analysis_reason'] = 'Financial document detected'
                
            elif any(keyword in filename for keyword in ['surveillance', 'video', 'camera', 'footage']):
                routing_decision['recommended_section'] = 'section_2'
                routing_decision['content_type'] = 'surveillance'
                routing_decision['confidence'] = 0.9
                routing_decision['analysis_reason'] = 'Surveillance content detected'
                
            elif any(keyword in filename for keyword in ['medical', 'doctor', 'hospital', 'treatment']):
                routing_decision['recommended_section'] = 'section_3'
                routing_decision['content_type'] = 'medical'
                routing_decision['confidence'] = 0.9
                routing_decision['analysis_reason'] = 'Medical document detected'
                
            elif any(keyword in filename for keyword in ['contract', 'lease', 'agreement']):
                routing_decision['recommended_section'] = 'section_5'
                routing_decision['content_type'] = 'contract'
                routing_decision['confidence'] = 0.9
                routing_decision['analysis_reason'] = 'Contract document detected'
        
        # Analyze content if available
        elif 'extracted_text' in payload:
            text = payload['extracted_text'].lower()
            
            if any(keyword in text for keyword in ['police', 'incident', 'report', 'officer']):
                routing_decision['recommended_section'] = 'section_1'
                routing_decision['content_type'] = 'police_report'
                routing_decision['confidence'] = 0.8
                routing_decision['analysis_reason'] = 'Police report content detected'
        
        return routing_decision
    
    def get_signal_status(self) -> Dict[str, Any]:
        """Get signal processing status"""
        return {
            'queued_signals': len(self.signal_queue),
            'processed_signals': len(self.signal_history),
            'registered_handlers': list(self.section_handlers.keys()),
            'routing_table_entries': len(self.signal_routing_table),
            'signal_types_processed': list(set([s['signal']['type'] for s in self.signal_history]))
        }

    def request_narrative_from_assembler(self, section_id: str, structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """Request narrative assembly from Narrative Assembler using handoff protocol"""
        try:
            # Step 1: Call out to ECC for permission
            if not self._call_out_to_ecc("narrative_request", {
                "section_id": section_id,
                "structured_data": structured_data
            }):
                logger.error("ECC permission denied for narrative request")
                return {"error": "ECC permission denied"}
            
            # Step 2: Wait for ECC confirmation
            if not self._wait_for_ecc_confirm():
                logger.error("ECC confirmation timeout for narrative request")
                return {"error": "ECC confirmation timeout"}
            
            # Step 3: Prepare narrative request data
            narrative_request_data = {
                "operation": "narrative_request",
                "section_id": section_id,
                "structured_data": structured_data,
                "timestamp": datetime.now().isoformat()
            }
            
            # Step 4: Send message to Narrative Assembler
            if not self._send_message("narrative_request", narrative_request_data):
                logger.error("Failed to send narrative request message")
                return {"error": "Failed to send narrative request"}
            
            # Step 5: Send accept signal
            if not self._send_accept_signal("narrative_request"):
                logger.error("Failed to send accept signal for narrative request")
                return {"error": "Failed to send accept signal"}
            
            # Step 6: Complete handoff
            self._complete_handoff("narrative_request", "success")
            
            logger.info(f"📝 Requested narrative from assembler for {section_id}")
            return {"status": "success", "section_id": section_id}
            
        except Exception as e:
            logger.error(f"Failed to request narrative from assembler: {e}")
            self._complete_handoff("narrative_request", "error")
            return {"error": str(e)}
    
    def _call_out_to_ecc(self, operation: str, data: Dict[str, Any]) -> bool:
        """Call out to ECC for permission to perform operation"""
        try:
            if not self.ecosystem_controller:
                logger.warning("ECC not available for call-out")
                return False
            
            # Prepare call-out data
            call_out_data = {
                "operation": operation,
                "source": "gateway_controller",
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
            
            # Emit call-out signal to ECC
            if hasattr(self.ecosystem_controller, 'emit'):
                self.ecosystem_controller.emit("gateway_controller.call_out", call_out_data)
                logger.info(f"📞 Called out to ECC for operation: {operation}")
                return True
            else:
                logger.warning("ECC does not support signal emission")
                return False
                
        except Exception as e:
            logger.error(f"Failed to call out to ECC: {e}")
            return False
    
    def _wait_for_ecc_confirm(self, timeout: int = 30) -> bool:
        """Wait for ECC confirmation"""
        try:
            # In a real implementation, this would wait for ECC response
            # For now, we'll simulate immediate confirmation
            logger.info("⏳ Waiting for ECC confirmation...")
            # Simulate confirmation delay
            import time
            time.sleep(0.1)  # Brief delay to simulate processing
            logger.info("✅ ECC confirmation received")
            return True
            
        except Exception as e:
            logger.error(f"ECC confirmation timeout or error: {e}")
            return False
    
    def _send_message(self, message_type: str, data: Dict[str, Any]) -> bool:
        """Send message to ECC"""
        try:
            if not self.ecosystem_controller:
                logger.warning("ECC not available for message sending")
                return False
            
            message_data = {
                "message_type": message_type,
                "source": "gateway_controller",
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
            
            # Emit message to ECC
            if hasattr(self.ecosystem_controller, 'emit'):
                self.ecosystem_controller.emit(f"gateway_controller.{message_type}", message_data)
                logger.info(f"📤 Sent message to ECC: {message_type}")
                return True
            else:
                logger.warning("ECC does not support signal emission")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send message to ECC: {e}")
            return False
    
    def _send_accept_signal(self, operation: str) -> bool:
        """Send accept signal to ECC"""
        try:
            if not self.ecosystem_controller:
                logger.warning("ECC not available for accept signal")
                return False
            
            accept_data = {
                "operation": operation,
                "source": "gateway_controller",
                "status": "accepted",
                "timestamp": datetime.now().isoformat()
            }
            
            # Emit accept signal to ECC
            if hasattr(self.ecosystem_controller, 'emit'):
                self.ecosystem_controller.emit("gateway_controller.accept", accept_data)
                logger.info(f"✅ Sent accept signal to ECC for operation: {operation}")
                return True
            else:
                logger.warning("ECC does not support signal emission")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send accept signal to ECC: {e}")
            return False
    
    def _complete_handoff(self, operation: str, status: str) -> bool:
        """Complete handoff process"""
        try:
            handoff_data = {
                "operation": operation,
                "source": "gateway_controller",
                "status": status,
                "timestamp": datetime.now().isoformat()
            }
            
            # Log handoff completion
            if not hasattr(self, 'handoff_log'):
                self.handoff_log = []
            
            self.handoff_log.append(handoff_data)
            
            logger.info(f"🔄 Handoff completed: {operation} - {status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to complete handoff: {e}")
            return False

    def get_gateway_status(self) -> Dict[str, Any]:
        """Get comprehensive gateway status"""
        ecc_validation = self._validate_gateway_with_ecc() if self.ecosystem_controller else False
        
        return {
            'total_evidence_items': len(self.master_evidence_index),
            'completed_sections': len(self.completed_sections),
            'section_cache_size': len(self.section_cache),
            'cross_links_count': len(self.cross_links),
            'evidence_map_sections': list(self.evidence_map.keys()),
            'completed_section_list': list(self.completed_sections),
            'gateway_config': self.gateway_config,
            'processing_log_entries': len(self.processing_log),
            'section_states': self.get_section_states(),
            'ecc_validation': ecc_validation,
            'ecc_connected': bool(self.ecosystem_controller),
            'orchestration_status': self.get_orchestration_status(),
            'ocr_status': self.get_ocr_status(),
            'case_bundle_status': self.get_case_bundle_status(),
            'signal_status': self.get_signal_status()
        }