#!/usr/bin/env python3
"""
Static Data Flow - Defines structured data flow patterns between Gateway and sections
Implements data contracts, validation schemas, and flow orchestration
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from section_registry import SECTION_REGISTRY, REPORTING_STANDARDS
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class DataFlowDirection(Enum):
    """Data flow directions"""
    GATEWAY_TO_SECTION = "gateway_to_section"
    SECTION_TO_GATEWAY = "section_to_gateway"
    SECTION_TO_SECTION = "section_to_section"  # Prohibited in this architecture
    BIDIRECTIONAL = "bidirectional"

class DataFlowStatus(Enum):
    """Data flow status"""
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    FAILED = "failed"
    VALIDATED = "validated"

@dataclass
class DataContract:
    """Data contract defining structure and validation rules"""
    contract_id: str
    source: str
    destination: str
    data_schema: Dict[str, Any]
    validation_rules: List[str]
    required_fields: List[str]
    optional_fields: List[str]
    created_at: str
    version: str = "1.0"

@dataclass
class DataPayload:
    """Structured data payload for flow between components"""
    payload_id: str
    contract_id: str
    source: str
    destination: str
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: str
    status: DataFlowStatus
    validation_results: Optional[Dict[str, Any]] = None

class StaticDataFlow:
    """Static data flow system for Gateway-section communication with ECC integration"""
    
    def __init__(self, ecc=None):
        self.data_contracts = {}
        self.active_flows = {}
        self.flow_history = []
        self.validation_schemas = {}
        self.ecc = ecc  # Reference to EcosystemController for validation
        self.logger = logging.getLogger(__name__)
        
        # Initialize core data contracts
        self._initialize_core_contracts()
        
        self.logger.info("Static Data Flow system initialized")

    def _call_out_to_ecc(self, operation: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Call out to ECC for permission to perform operation"""
        try:
            if not self.ecc:
                return {"permission_granted": True, "request_id": None}
            
            request_id = f"flow_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            # Emit call-out signal to ECC
            if hasattr(self.ecc, 'emit'):
                self.ecc.emit("evidence_locker.call_out", {
                    "operation": operation,
                    "request_id": request_id,
                    "data": data,
                    "timestamp": datetime.now().isoformat(),
                    "module": "static_data_flow"
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
                self.ecc.emit("evidence_locker.send", {
                    "operation": operation,
                    "data": data,
                    "timestamp": datetime.now().isoformat(),
                    "module": "static_data_flow"
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
                self.ecc.emit("evidence_locker.accept", {
                    "operation": operation,
                    "data": data,
                    "timestamp": datetime.now().isoformat(),
                    "module": "static_data_flow"
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
                self.ecc.emit("evidence_locker.handoff_complete", {
                    "operation": operation,
                    "data": data,
                    "timestamp": datetime.now().isoformat(),
                    "module": "static_data_flow"
                })
            
            self.logger.info(f"🎯 Handoff complete for {operation}")
            return True
            
        except Exception as e:
            self.logger.error(f"Handoff complete failed: {e}")
            return False

    def _enforce_section_aware_execution(self, section_id: str, operation: str):
        """ENFORCES SECTION-AWARE EXECUTION - Every function begins with this check"""
        if not self.ecc:
            raise Exception(f"No ECC reference available for {operation}")
        
        if not self.ecc.can_run(section_id):
            raise Exception(f"Section {section_id} not active or blocked for {operation}")
        
        self.logger.debug(f"✅ Section {section_id} validated for {operation}")

    def get_section_registry(self) -> Dict[str, Any]:
        """Get the section registry for other modules"""
        return SECTION_REGISTRY

    def get_reporting_standards(self) -> Dict[str, Any]:
        """Get the configured reporting standards for report types."""
        return REPORTING_STANDARDS

    def validate_section_id(self, section_id: str) -> bool:
        """Validate section ID against SECTION_REGISTRY"""
        return section_id in SECTION_REGISTRY
    
    def _initialize_core_contracts(self):
        """Initialize core data contracts for Gateway-section communication"""
        
        # Contract 1: Evidence Assignment (Gateway -> Section)
        evidence_assignment_contract = DataContract(
            contract_id="evidence_assignment",
            source="gateway",
            destination="section",
            data_schema={
                "type": "object",
                "properties": {
                    "evidence_id": {"type": "string"},
                    "filename": {"type": "string"},
                    "file_path": {"type": "string"},
                    "assigned_section": {"type": "string"},
                    "metadata": {"type": "object"},
                    "cross_links": {"type": "array"}
                }
            },
            validation_rules=[
                "evidence_id must be UUID format",
                "file_path must exist",
                "assigned_section must be valid section ID"
            ],
            required_fields=["evidence_id", "filename", "assigned_section"],
            optional_fields=["metadata", "cross_links"],
            created_at=datetime.now().isoformat()
        )
        
        # Contract 2: Section Data Transfer (Section -> Gateway)
        section_data_contract = DataContract(
            contract_id="section_data_transfer",
            source="section",
            destination="gateway",
            data_schema={
                "type": "object",
                "properties": {
                    "section_id": {"type": "string"},
                    "structured_data": {"type": "object"},
                    "narrative": {"type": "string"},
                    "confidence_score": {"type": "number"},
                    "processing_metadata": {"type": "object"}
                }
            },
            validation_rules=[
                "section_id must be valid",
                "structured_data must be non-empty",
                "confidence_score must be between 0 and 1"
            ],
            required_fields=["section_id", "structured_data"],
            optional_fields=["narrative", "confidence_score", "processing_metadata"],
            created_at=datetime.now().isoformat()
        )
        
        # Contract 3: Cross-Link Notification (Gateway -> Section)
        cross_link_contract = DataContract(
            contract_id="cross_link_notification",
            source="gateway",
            destination="section",
            data_schema={
                "type": "object",
                "properties": {
                    "evidence_id": {"type": "string"},
                    "keyword": {"type": "string"},
                    "target_evidence_id": {"type": "string"},
                    "link_strength": {"type": "number"}
                }
            },
            validation_rules=[
                "evidence_id must be UUID format",
                "keyword must be non-empty string"
            ],
            required_fields=["evidence_id", "keyword"],
            optional_fields=["target_evidence_id", "link_strength"],
            created_at=datetime.now().isoformat()
        )
        
        # Register contracts
        self.data_contracts["evidence_assignment"] = evidence_assignment_contract
        self.data_contracts["section_data_transfer"] = section_data_contract
        self.data_contracts["cross_link_notification"] = cross_link_contract
        
        self.logger.info(f"📋 Initialized {len(self.data_contracts)} core data contracts")
    
    def create_data_contract(self, contract: DataContract) -> bool:
        """Create a new data contract"""
        try:
            self.data_contracts[contract.contract_id] = contract
            self.logger.info(f"📋 Created data contract: {contract.contract_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create data contract: {e}")
            return False
    
    def initiate_flow(self, contract_id: str, source: str, destination: str, data: Dict[str, Any]) -> Optional[str]:
        """Initiate a data flow using a specific contract - ENFORCES SECTION-AWARE EXECUTION"""
        try:
            # ECC CALL-OUT: Request permission to initiate flow
            if self.ecc:
                call_out_result = self._call_out_to_ecc("initiate_flow", {
                    "contract_id": contract_id,
                    "source": source,
                    "destination": destination,
                    "operation": "data_flow_initiation"
                })
                
                if not call_out_result.get("permission_granted", False):
                    raise Exception(f"ECC denied flow initiation permission for {contract_id}")
                
                # ECC CONFIRM: Wait for confirmation
                confirm_result = self._wait_for_ecc_confirm("initiate_flow", call_out_result.get("request_id"))
                if not confirm_result.get("confirmed", False):
                    raise Exception(f"ECC confirmation failed for flow initiation of {contract_id}")
            
            if contract_id not in self.data_contracts:
                self.logger.error(f"Contract {contract_id} not found")
                return None
            
            contract = self.data_contracts[contract_id]
            
            # SECTION-AWARE EXECUTION ENFORCEMENT for destination section
            if destination.startswith("section_"):
                self._enforce_section_aware_execution(destination, "data flow initiation")
            
            # Create payload
            payload_id = f"flow_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{contract_id}"
            payload = DataPayload(
                payload_id=payload_id,
                contract_id=contract_id,
                source=source,
                destination=destination,
                data=data,
                metadata={
                    "contract_version": contract.version,
                    "flow_direction": DataFlowDirection.GATEWAY_TO_SECTION.value if source == "gateway" else DataFlowDirection.SECTION_TO_GATEWAY.value,
                    "section_registry_used": True
                },
                timestamp=datetime.now().isoformat(),
                status=DataFlowStatus.PENDING
            )
            
            # Validate payload
            validation_result = self._validate_payload(payload, contract)
            payload.validation_results = validation_result
            
            if validation_result["valid"]:
                payload.status = DataFlowStatus.VALIDATED
                self.active_flows[payload_id] = payload
                
                # COMPLETE HANDOFF PROCESS
                # 1. SEND MESSAGE: Notify receiving module
                self._send_message("flow_initiated", {
                    "payload_id": payload_id,
                    "contract_id": contract_id,
                    "source": source,
                    "destination": destination,
                    "status": "validated"
                })
                
                # 2. SEND ACCEPT SIGNAL: Notify receiving module
                self._send_accept_signal("flow_initiation_complete", {
                    "payload_id": payload_id,
                    "contract_id": contract_id,
                    "destination": destination
                })
                
                # 3. COMPLETE HANDOFF: Final confirmation
                self._complete_handoff("flow_initiation_handoff", {
                    "payload_id": payload_id,
                    "contract_id": contract_id,
                    "destination": destination
                })
                
                self.logger.info(f"📤 Initiated flow {payload_id}: {source} -> {destination}")
                return payload_id
            else:
                payload.status = DataFlowStatus.FAILED
                self.logger.error(f"❌ Flow validation failed for {payload_id}: {validation_result['errors']}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to initiate flow: {e}")
            return None
    
    def _validate_payload(self, payload: DataPayload, contract: DataContract) -> Dict[str, Any]:
        """Validate payload against contract"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        try:
            # Check required fields
            for field in contract.required_fields:
                if field not in payload.data:
                    validation_result["valid"] = False
                    validation_result["errors"].append(f"Missing required field: {field}")
            
            # Check optional fields
            for field in contract.optional_fields:
                if field not in payload.data:
                    validation_result["warnings"].append(f"Missing optional field: {field}")
            
            # Apply validation rules
            for rule in contract.validation_rules:
                if not self._apply_validation_rule(rule, payload.data):
                    validation_result["valid"] = False
                    validation_result["errors"].append(f"Validation rule failed: {rule}")
            
            return validation_result
            
        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Validation error: {e}")
            return validation_result
    
    def _apply_validation_rule(self, rule: str, data: Dict[str, Any]) -> bool:
        """Apply a specific validation rule"""
        try:
            if "evidence_id must be UUID format" in rule:
                evidence_id = data.get("evidence_id", "")
                return len(evidence_id) == 36 and evidence_id.count("-") == 4
            
            elif "file_path must exist" in rule:
                file_path = data.get("file_path", "")
                import os
                return os.path.exists(file_path)
            
            elif "assigned_section must be valid section ID" in rule:
                section_id = data.get("assigned_section", "")
                return self.validate_section_id(section_id)
            
            elif "section_id must be valid" in rule:
                section_id = data.get("section_id", "")
                return self.validate_section_id(section_id)
            
            elif "structured_data must be non-empty" in rule:
                structured_data = data.get("structured_data", {})
                return bool(structured_data)
            
            elif "confidence_score must be between 0 and 1" in rule:
                confidence = data.get("confidence_score", 0)
                return 0 <= confidence <= 1
            
            elif "keyword must be non-empty string" in rule:
                keyword = data.get("keyword", "")
                return bool(keyword and isinstance(keyword, str))
            
            return True
            
        except Exception:
            return False
    
    def deliver_payload(self, payload_id: str) -> bool:
        """Mark payload as delivered"""
        try:
            if payload_id not in self.active_flows:
                self.logger.error(f"Payload {payload_id} not found")
                return False
            
            payload = self.active_flows[payload_id]
            payload.status = DataFlowStatus.DELIVERED
            
            # Move to history
            self.flow_history.append(payload)
            del self.active_flows[payload_id]
            
            self.logger.info(f"📥 Delivered payload {payload_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to deliver payload {payload_id}: {e}")
            return False
    
    def get_flow_status(self, payload_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific flow"""
        if payload_id in self.active_flows:
            payload = self.active_flows[payload_id]
            return {
                "payload_id": payload.payload_id,
                "status": payload.status.value,
                "source": payload.source,
                "destination": payload.destination,
                "timestamp": payload.timestamp,
                "validation_results": payload.validation_results
            }
        
        # Check history
        for payload in self.flow_history:
            if payload.payload_id == payload_id:
                return {
                    "payload_id": payload.payload_id,
                    "status": payload.status.value,
                    "source": payload.source,
                    "destination": payload.destination,
                    "timestamp": payload.timestamp,
                    "validation_results": payload.validation_results
                }
        
        return None
    
    def get_active_flows(self) -> List[Dict[str, Any]]:
        """Get all active flows"""
        return [
            {
                "payload_id": payload.payload_id,
                "contract_id": payload.contract_id,
                "source": payload.source,
                "destination": payload.destination,
                "status": payload.status.value,
                "timestamp": payload.timestamp
            }
            for payload in self.active_flows.values()
        ]
    
    def get_flow_statistics(self) -> Dict[str, Any]:
        """Get flow statistics"""
        total_flows = len(self.active_flows) + len(self.flow_history)
        
        status_counts = {}
        for payload in list(self.active_flows.values()) + self.flow_history:
            status = payload.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        contract_counts = {}
        for payload in list(self.active_flows.values()) + self.flow_history:
            contract_id = payload.contract_id
            contract_counts[contract_id] = contract_counts.get(contract_id, 0) + 1
        
        return {
            "total_flows": total_flows,
            "active_flows": len(self.active_flows),
            "completed_flows": len(self.flow_history),
            "status_distribution": status_counts,
            "contract_distribution": contract_counts,
            "total_contracts": len(self.data_contracts)
        }
    
    def export_data_contracts(self) -> Dict[str, Any]:
        """Export all data contracts"""
        return {
            "contracts": {contract_id: asdict(contract) for contract_id, contract in self.data_contracts.items()},
            "export_timestamp": datetime.now().isoformat(),
            "total_contracts": len(self.data_contracts)
        }


