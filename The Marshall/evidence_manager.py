#!/usr/bin/env python3
"""
Evidence Manager - Central evidence processing and management system
Handles evidence ingestion, processing, validation, and distribution to sections
"""

import os
import uuid
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from pathlib import Path

logger = logging.getLogger(__name__)

class EvidenceManager:
    """Evidence Manager with section-aware execution enforcement"""
    
    def __init__(self, ecc=None, gateway=None, evidence_builder=None):
        self.ecc = ecc
        self.gateway = gateway
        self.evidence_builder = evidence_builder
        self.logger = logging.getLogger(__name__)
        
        # Evidence processing pipeline
        self.processing_queue = []
        self.processed_evidence = {}
        self.failed_evidence = {}
        
        # Evidence validation rules
        self.validation_rules = {
            'max_file_size': 100 * 1024 * 1024,  # 100MB
            'allowed_extensions': {'.mp4', '.avi', '.mov', '.jpg', '.png', '.pdf', '.doc', '.docx', '.txt'},
            'required_metadata': ['filename', 'file_path', 'file_size', 'evidence_type']
        }
        
        self.logger.info("EvidenceManager initialized")
    
    def _call_out_to_ecc(self, operation: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Call out to ECC for permission to perform operation"""
        try:
            if not self.ecc:
                return {"permission_granted": True, "request_id": None}
            
            request_id = f"manager_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            # Emit call-out signal to ECC
            if hasattr(self.ecc, 'emit'):
                self.ecc.emit("evidence_manager.call_out", {
                    "operation": operation,
                    "request_id": request_id,
                    "data": data,
                    "timestamp": datetime.now().isoformat(),
                    "module": "evidence_manager"
                })
            
            self.logger.info(f"📞 Called out to ECC for {operation} - Request ID: {request_id}")
            return {"permission_granted": True, "request_id": request_id}
            
        except Exception as e:
            self.logger.error(f"ECC call-out failed: {e}")
            return {"permission_granted": False, "error": str(e)}
    
    def _wait_for_ecc_confirm(self, operation: str, request_id: str) -> Dict[str, Any]:
        """Wait for ECC confirmation"""
        try:
            if not self.ecc or not request_id:
                return {"confirmed": True}
            
            # In a real implementation, this would wait for ECC response
            # For now, simulate immediate confirmation
            self.logger.info(f"✅ ECC confirmed {operation} - Request ID: {request_id}")
            return {"confirmed": True, "request_id": request_id}
            
        except Exception as e:
            self.logger.error(f"ECC confirmation failed: {e}")
            return {"confirmed": False, "error": str(e)}
    
    def _send_message(self, operation: str, data: Dict[str, Any]) -> bool:
        """Send message to receiving module"""
        try:
            if not self.ecc:
                return True
            
            # Emit send message signal
            if hasattr(self.ecc, 'emit'):
                self.ecc.emit("evidence_manager.send", {
                    "operation": operation,
                    "data": data,
                    "timestamp": datetime.now().isoformat(),
                    "module": "evidence_manager"
                })
            
            self.logger.info(f"📤 Sent message for {operation}")
            return True
            
        except Exception as e:
            self.logger.error(f"Send message failed: {e}")
            return False
    
    def _send_accept_signal(self, operation: str, data: Dict[str, Any]) -> bool:
        """Send accept signal to receiving module"""
        try:
            if not self.ecc:
                return True
            
            # Emit accept signal
            if hasattr(self.ecc, 'emit'):
                self.ecc.emit("evidence_manager.accept", {
                    "operation": operation,
                    "data": data,
                    "timestamp": datetime.now().isoformat(),
                    "module": "evidence_manager"
                })
            
            self.logger.info(f"✅ Sent accept signal for {operation}")
            return True
            
        except Exception as e:
            self.logger.error(f"Accept signal failed: {e}")
            return False
    
    def _complete_handoff(self, operation: str, data: Dict[str, Any]) -> bool:
        """Complete handoff process"""
        try:
            if not self.ecc:
                return True
            
            # Emit handoff complete signal
            if hasattr(self.ecc, 'emit'):
                self.ecc.emit("evidence_manager.handoff_complete", {
                    "operation": operation,
                    "data": data,
                    "timestamp": datetime.now().isoformat(),
                    "module": "evidence_manager"
                })
            
            self.logger.info(f"🎯 Handoff complete for {operation}")
            return True
            
        except Exception as e:
            self.logger.error(f"Handoff complete failed: {e}")
            return False
    
    def _handoff_to_gateway(self, operation: str, data: Dict[str, Any]) -> bool:
        """Handoff to Gateway Controller"""
        try:
            if not self.gateway:
                self.logger.warning("Gateway Controller not available for handoff")
                return False
            
            # Register handoff with Gateway Controller
            if hasattr(self.gateway, 'register_evidence_locker_handoff'):
                self.gateway.register_evidence_locker_handoff(
                    from_module="evidence_manager",
                    to_module="gateway_controller", 
                    handoff_data={
                        "operation": operation,
                        "data": data,
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
                self.logger.info(f"🔄 Handed off to Gateway Controller for {operation}")
                return True
            else:
                self.logger.warning("Gateway Controller does not support handoff registration")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to handoff to Gateway Controller: {e}")
            return False
    
    def _handoff_to_evidence_locker(self, operation: str, data: Dict[str, Any]) -> bool:
        """Handoff to Evidence Locker Main"""
        try:
            if not self.ecc:
                return True
            
            # Emit handoff to Evidence Locker signal
            if hasattr(self.ecc, 'emit'):
                self.ecc.emit("evidence_manager.handoff_to_locker", {
                    "operation": operation,
                    "data": data,
                    "timestamp": datetime.now().isoformat(),
                    "module": "evidence_manager"
                })
            
            self.logger.info(f"🔄 Handed off to Evidence Locker for {operation}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to handoff to Evidence Locker: {e}")
            return False
    
    def _handoff_to_cell(self, cell_id: str, operation: str, data: Dict[str, Any]) -> bool:
        """Handoff to specific cell/section"""
        try:
            if not self.ecc:
                return True
            
            # Emit handoff to cell signal
            if hasattr(self.ecc, 'emit'):
                self.ecc.emit("evidence_manager.handoff_to_cell", {
                    "cell_id": cell_id,
                    "operation": operation,
                    "data": data,
                    "timestamp": datetime.now().isoformat(),
                    "module": "evidence_manager"
                })
            
            self.logger.info(f"🔄 Handed off to {cell_id} for {operation}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to handoff to {cell_id}: {e}")
            return False

    def _enforce_section_aware_execution(self, section_id: str, operation: str):
        """ENFORCES SECTION-AWARE EXECUTION - Every function begins with this check"""
        if not self.ecc:
            raise Exception(f"No ECC reference available for {operation}")
        
        if not self.ecc.can_run(section_id):
            raise Exception(f"Section {section_id} not active or blocked for {operation}")
        
        self.logger.debug(f"✅ Section {section_id} validated for {operation}")

    def ingest_evidence(self, file_path: str, section_id: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Ingest evidence file for processing - ENFORCES SECTION-AWARE EXECUTION"""
        try:
            # ECC CALL-OUT: Request permission to ingest evidence
            if self.ecc:
                call_out_result = self._call_out_to_ecc("ingest_evidence", {
                    "file_path": file_path,
                    "section_id": section_id,
                    "operation": "evidence_ingestion"
                })
                
                if not call_out_result.get("permission_granted", False):
                    raise Exception(f"ECC denied evidence ingestion permission for {file_path}")
                
                # ECC CONFIRM: Wait for confirmation
                confirm_result = self._wait_for_ecc_confirm("ingest_evidence", call_out_result.get("request_id"))
                if not confirm_result.get("confirmed", False):
                    raise Exception(f"ECC confirmation failed for evidence ingestion of {file_path}")
            
            # SECTION-AWARE EXECUTION ENFORCEMENT
            self._enforce_section_aware_execution(section_id, "evidence ingestion")
            
            # Validate file exists
            if not os.path.exists(file_path):
                raise Exception(f"Evidence file does not exist: {file_path}")
            
            # Validate file size
            file_size = os.path.getsize(file_path)
            if file_size > self.validation_rules['max_file_size']:
                raise Exception(f"File too large: {file_size} bytes (max: {self.validation_rules['max_file_size']})")
            
            # Validate file extension
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in self.validation_rules['allowed_extensions']:
                raise Exception(f"Unsupported file type: {file_ext}")
            
            # Generate evidence ID
            evidence_id = str(uuid.uuid4())
            
            # Create evidence record
            evidence_record = {
                'evidence_id': evidence_id,
                'file_path': file_path,
                'filename': os.path.basename(file_path),
                'file_size': file_size,
                'file_extension': file_ext,
                'section_id': section_id,
                'ingested_at': datetime.now().isoformat(),
                'status': 'pending',
                'metadata': metadata or {},
                'processing_log': []
            }
            
            # Add to processing queue
            self.processing_queue.append(evidence_record)
            
            self.logger.debug(f"📁 Ingested evidence {evidence_id} for {section_id}")
            self.logger.info(f"Ingested evidence {os.path.basename(file_path)} for {section_id}")
            
            # COMPLETE HANDOFF PROCESS
            # 1. SEND MESSAGE: Notify receiving modules
            self._send_message("evidence_ingested", {
                "evidence_id": evidence_id,
                "file_path": file_path,
                "section_id": section_id,
                "metadata": metadata or {}
            })
            
            # 2. HANDOFF TO EVIDENCE LOCKER: Pass to Evidence Locker for processing
            self._handoff_to_evidence_locker("evidence_ingestion_complete", {
                "evidence_id": evidence_id,
                "file_path": file_path,
                "section_id": section_id,
                "evidence_record": evidence_record
            })
            
            # 3. HANDOFF TO GATEWAY: Pass to Gateway Controller
            self._handoff_to_gateway("evidence_ingestion_complete", {
                "evidence_id": evidence_id,
                "file_path": file_path,
                "section_id": section_id,
                "evidence_record": evidence_record
            })
            
            # 4. HANDOFF TO CELL: Pass to specific cell/section
            self._handoff_to_cell(section_id, "evidence_ingestion_complete", {
                "evidence_id": evidence_id,
                "file_path": file_path,
                "section_id": section_id,
                "evidence_record": evidence_record
            })
            
            # 5. SEND ACCEPT SIGNAL: Notify receiving modules
            self._send_accept_signal("evidence_ingestion_complete", {
                "evidence_id": evidence_id,
                "file_path": file_path,
                "section_id": section_id
            })
            
            # 6. COMPLETE HANDOFF: Final confirmation
            self._complete_handoff("evidence_ingestion_handoff", {
                "evidence_id": evidence_id,
                "file_path": file_path,
                "section_id": section_id
            })
            
            return evidence_id
            
        except Exception as e:
            self.logger.error(f"Failed to ingest evidence {file_path}: {e}")
            raise

    def process_evidence(self, evidence_id: str) -> bool:
        """Process evidence through classification and validation pipeline"""
        try:
            # Find evidence record
            evidence_record = None
            for record in self.processing_queue:
                if record['evidence_id'] == evidence_id:
                    evidence_record = record
                    break
            
            if not evidence_record:
                raise Exception(f"Evidence {evidence_id} not found in processing queue")
            
            self.logger.info(f"Processing evidence {evidence_id}")
            
            # Update status
            evidence_record['status'] = 'processing'
            evidence_record['processing_log'].append({
                'timestamp': datetime.now().isoformat(),
                'action': 'processing_started'
            })
            
            # Build evidence class if builder available
            if self.evidence_builder:
                evidence_class = self.evidence_builder.build_evidence_class(
                    evidence_record['file_path'], 
                    evidence_record['section_id']
                )
                evidence_record['evidence_class'] = evidence_class
            
            # Validate evidence
            is_valid = self._validate_evidence(evidence_record)
            evidence_record['validated'] = is_valid
            
            # Update status
            if is_valid:
                evidence_record['status'] = 'processed'
                self.processed_evidence[evidence_id] = evidence_record
                self.processing_queue.remove(evidence_record)
            else:
                evidence_record['status'] = 'failed'
                self.failed_evidence[evidence_id] = evidence_record
                self.processing_queue.remove(evidence_record)
            
            evidence_record['processing_log'].append({
                'timestamp': datetime.now().isoformat(),
                'action': 'processing_completed',
                'result': 'success' if is_valid else 'failed'
            })
            
            self.logger.debug(f"✅ Processed evidence {evidence_id}")
            self.logger.info(f"Processed evidence {evidence_id} - Valid: {is_valid}")
            return is_valid
            
        except Exception as e:
            self.logger.error(f"Failed to process evidence {evidence_id}: {e}")
            return False

    def _validate_evidence(self, evidence_record: Dict[str, Any]) -> bool:
        """Validate evidence record against rules"""
        try:
            # Check required metadata
            for field in self.validation_rules['required_metadata']:
                if field not in evidence_record:
                    self.logger.error(f"Missing required field: {field}")
                    return False
            
            # Check file still exists
            if not os.path.exists(evidence_record['file_path']):
                self.logger.error(f"Evidence file no longer exists: {evidence_record['file_path']}")
                return False
            
            # Check file size hasn't changed
            current_size = os.path.getsize(evidence_record['file_path'])
            if current_size != evidence_record['file_size']:
                self.logger.error(f"File size changed: {current_size} != {evidence_record['file_size']}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Evidence validation failed: {e}")
            return False

    def distribute_evidence(self, evidence_id: str, target_section_id: str) -> bool:
        """Distribute processed evidence to target section - ENFORCES SECTION-AWARE EXECUTION"""
        try:
            # SECTION-AWARE EXECUTION ENFORCEMENT
            self._enforce_section_aware_execution(target_section_id, "evidence distribution")
            
            # Check evidence is processed
            if evidence_id not in self.processed_evidence:
                raise Exception(f"Evidence {evidence_id} not processed or not found")
            
            evidence_record = self.processed_evidence[evidence_id]
            
            # Update section assignment
            evidence_record['assigned_section'] = target_section_id
            evidence_record['distributed_at'] = datetime.now().isoformat()
            
            # Add to Gateway if available
            if self.gateway:
                # Register with evidence index
                if hasattr(self.gateway, 'evidence_index'):
                    self.gateway.evidence_index.add_file(
                        evidence_record['file_path'],
                        evidence_record.get('metadata', {}).get('tags', []),
                        'evidence_manager',
                        target_section_id
                    )
            
            self.logger.debug(f"📤 Distributed evidence {evidence_id} to {target_section_id}")
            self.logger.info(f"Distributed evidence {evidence_id} to {target_section_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to distribute evidence {evidence_id}: {e}")
            raise

    def batch_process_evidence(self, evidence_ids: List[str]) -> Dict[str, bool]:
        """Process multiple evidence items"""
        try:
            results = {}
            
            for evidence_id in evidence_ids:
                try:
                    success = self.process_evidence(evidence_id)
                    results[evidence_id] = success
                except Exception as e:
                    self.logger.error(f"Failed to process evidence {evidence_id}: {e}")
                    results[evidence_id] = False
            
            self.logger.debug(f"📊 Batch processed {len(evidence_ids)} evidence items")
            self.logger.info(f"Batch processed {len(evidence_ids)} evidence items")
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to batch process evidence: {e}")
            return {}

    def get_evidence_status(self, evidence_id: str) -> Optional[Dict[str, Any]]:
        """Get status of evidence processing"""
        # Check processing queue
        for record in self.processing_queue:
            if record['evidence_id'] == evidence_id:
                return {
                    'evidence_id': evidence_id,
                    'status': record['status'],
                    'section_id': record['section_id'],
                    'ingested_at': record['ingested_at']
                }
        
        # Check processed evidence
        if evidence_id in self.processed_evidence:
            record = self.processed_evidence[evidence_id]
            return {
                'evidence_id': evidence_id,
                'status': 'processed',
                'section_id': record['section_id'],
                'assigned_section': record.get('assigned_section'),
                'validated': record.get('validated', False),
                'ingested_at': record['ingested_at']
            }
        
        # Check failed evidence
        if evidence_id in self.failed_evidence:
            record = self.failed_evidence[evidence_id]
            return {
                'evidence_id': evidence_id,
                'status': 'failed',
                'section_id': record['section_id'],
                'ingested_at': record['ingested_at'],
                'error': 'Processing failed'
            }
        
        return None

    def get_manager_status(self) -> Dict[str, Any]:
        """Get evidence manager status"""
        return {
            'processing_queue_size': len(self.processing_queue),
            'processed_evidence_count': len(self.processed_evidence),
            'failed_evidence_count': len(self.failed_evidence),
            'ecc_connected': bool(self.ecc),
            'gateway_connected': bool(self.gateway),
            'evidence_builder_connected': bool(self.evidence_builder),
            'validation_rules': self.validation_rules
        }

    def export_evidence_report(self, output_path: str) -> bool:
        """Export evidence processing report"""
        try:
            report = {
                'export_timestamp': datetime.now().isoformat(),
                'manager_status': self.get_manager_status(),
                'processing_queue': self.processing_queue,
                'processed_evidence': self.processed_evidence,
                'failed_evidence': self.failed_evidence
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"📄 Exported evidence report to {output_path}")
            self.logger.info(f"Exported evidence report to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export evidence report: {e}")
            return False


# Usage example
def create_evidence_manager(ecc, gateway, evidence_builder=None):
    """Create evidence manager instance"""
    manager = EvidenceManager(
        ecc=ecc,
        gateway=gateway,
        evidence_builder=evidence_builder
    )
    logger.info("Evidence manager created")
    return manager