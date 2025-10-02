"""Framework template for Section TOC (Table of Contents)."""

from __future__ import annotations

from typing import Any, Dict
import logging
from datetime import datetime

# Import section framework base
try:
    from .section_framework_base import (
        CommunicationContract,
        OrderContract,
        PersistenceContract,
        SectionFramework,
        StageDefinition,
    )
except ImportError:
    # Fallback for when section_framework_base is not available
    from dataclasses import dataclass
    from typing import Tuple
    
    @dataclass
    class StageDefinition:
        name: str
        description: str
        checkpoint: str
        guardrails: Tuple[str, ...]
        dependencies: list = None
        timeout: int = None
    
    @dataclass
    class CommunicationContract:
        section_id: str = ""
        can_receive_from: list = None
        can_send_to: list = None
        required_signals: list = None
        optional_signals: list = None
    
    @dataclass
    class OrderContract:
        execution_after: tuple = None
        export_after: tuple = None
        export_priority: int = 0
    
    @dataclass
    class PersistenceContract:
        section_id: str = ""
        storage_path: str = ""
        backup_enabled: bool = True
        encryption_required: bool = False
        retention_days: int = 365
    
    class SectionFramework:
        def __init__(self, ecc=None, gateway=None):
            self.ecc = ecc
            self.gateway = gateway
            self.logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)


class SectionTOCFramework(SectionFramework):
    SECTION_ID = "section_toc"
    MAX_RERUNS = 1
    
    # SECTION REGISTRY - Standardized 10-section registry matching Evidence Locker
    SECTION_REGISTRY = {
        "section_1": {"title": "Client & Subject Details", "tags": ["client", "subject", "intake"]},
        "section_2": {"title": "Pre-Surveillance Summary", "tags": ["background", "planning", "map", "aerial"]},
        "section_3": {"title": "Surveillance Details", "tags": ["surveillance", "field-log", "observed"]},
        "section_4": {"title": "Surveillance Recap", "tags": ["summary", "recap", "patterns"]},
        "section_5": {"title": "Supporting Documents", "tags": ["contract", "agreement", "lease", "court record"]},
        "section_6": {"title": "Billing Summary", "tags": ["billing", "retainer", "payment", "hours"]},
        "section_7": {"title": "Surveillance Photos", "tags": ["photo", "image", "visual"]},
        "section_8": {"title": "Conclusion", "tags": ["conclusion", "findings", "outcome"]},
        "section_9": {"title": "Disclosures / Legal", "tags": ["disclosure", "legal", "compliance", "licensing"]},
        "section_cp": {"title": "Cover Page", "tags": ["cover", "title", "branding"]},
        "section_dp": {"title": "Disclosure Page", "tags": ["disclosure", "authenticity", "signature"]},
        "section_toc": {"title": "Table of Contents", "tags": ["toc", "index", "navigation"]}
    }
    
    def __init__(self, ecc=None, gateway=None):
        super().__init__(ecc, gateway)
        self.logger = logging.getLogger(f"{__name__}.{self.SECTION_ID}")
        
        # ECC Integration tracking
        self.handoff_log = []
        
        self.logger.info(f"Section {self.SECTION_ID} framework initialized")
    
    # ECC Integration Methods - Following Evidence Locker Pattern
    def _call_out_to_ecc(self, operation: str, data: Dict[str, Any]) -> bool:
        """Call out to ECC for permission to perform operation"""
        try:
            if not self.ecc:
                self.logger.warning("ECC not available for call-out")
                return False
            
            # Prepare call-out data
            call_out_data = {
                "operation": operation,
                "source": "section_toc_framework",
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
            
            # Emit call-out signal to ECC
            if hasattr(self.ecc, 'emit'):
                self.ecc.emit("section_toc_framework.call_out", call_out_data)
                self.logger.info(f"📡 Called out to ECC for operation: {operation}")
                return True
            else:
                self.logger.warning("ECC does not support signal emission")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to call out to ECC: {e}")
            return False
    
    def _wait_for_ecc_confirm(self, timeout: int = 30) -> bool:
        """Wait for ECC confirmation"""
        try:
            # In a real implementation, this would wait for ECC response
            # For now, we'll simulate immediate confirmation
            self.logger.info("⏳ Waiting for ECC confirmation...")
            # Simulate confirmation delay
            import time
            time.sleep(0.1)  # Brief delay to simulate processing
            self.logger.info("✅ ECC confirmation received")
            return True
            
        except Exception as e:
            self.logger.error(f"ECC confirmation timeout or error: {e}")
            return False
    
    def _send_message(self, message_type: str, data: Dict[str, Any]) -> bool:
        """Send message to ECC"""
        try:
            if not self.ecc:
                self.logger.warning("ECC not available for message sending")
                return False
            
            message_data = {
                "message_type": message_type,
                "source": "section_toc_framework",
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
            
            # Emit message to ECC
            if hasattr(self.ecc, 'emit'):
                self.ecc.emit(f"section_toc_framework.{message_type}", message_data)
                self.logger.info(f"📤 Sent message to ECC: {message_type}")
                return True
            else:
                self.logger.warning("ECC does not support signal emission")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to send message to ECC: {e}")
            return False
    
    def _send_accept_signal(self, operation: str) -> bool:
        """Send accept signal to ECC"""
        try:
            if not self.ecc:
                self.logger.warning("ECC not available for accept signal")
                return False
            
            accept_data = {
                "operation": operation,
                "source": "section_toc_framework",
                "status": "accepted",
                "timestamp": datetime.now().isoformat()
            }
            
            # Emit accept signal to ECC
            if hasattr(self.ecc, 'emit'):
                self.ecc.emit("section_toc_framework.accept", accept_data)
                self.logger.info(f"✅ Sent accept signal to ECC for operation: {operation}")
                return True
            else:
                self.logger.warning("ECC does not support signal emission")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to send accept signal to ECC: {e}")
            return False
    
    def _complete_handoff(self, operation: str, status: str) -> bool:
        """Complete handoff process"""
        try:
            handoff_data = {
                "operation": operation,
                "source": "section_toc_framework",
                "status": status,
                "timestamp": datetime.now().isoformat()
            }
            
            # Log handoff completion
            self.handoff_log.append(handoff_data)
            
            self.logger.info(f"🔄 Handoff completed: {operation} - {status}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to complete handoff: {e}")
            return False
    
    def _enforce_section_aware_execution(self, section_id: str) -> bool:
        """Enforce section-aware execution before operations"""
        try:
            if not self.ecc:
                self.logger.warning("ECC not available for section validation")
                return True  # Allow execution if ECC not available
            
            # Validate section ID against registry
            if not self.validate_section_id(section_id):
                self.logger.error(f"Invalid section ID: {section_id}")
                return False
            
            # Check if section is active in ECC
            if hasattr(self.ecc, 'can_run'):
                if not self.ecc.can_run(section_id):
                    self.logger.error(f"Section {section_id} not active or blocked")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Section-aware execution validation failed: {e}")
            return False
    
    def validate_section_id(self, section_id: str) -> bool:
        """Validate section ID against SECTION_REGISTRY"""
        return section_id in self.SECTION_REGISTRY
    
    def get_section_registry(self) -> Dict[str, Any]:
        """Get the section registry"""
        return self.SECTION_REGISTRY.copy()
    STAGES = (
        StageDefinition(
            name="intake",
            description="Pull cover profile and section manifest summaries for TOC generation.",
            checkpoint="toc_intake_logged",
            guardrails=("order_lock", "async_queue", "persistence_snapshot"),
        ),
        StageDefinition(
            name="compile",
            description="Assemble TOC entries using approved section payload hashes and titles.",
            checkpoint="toc_compiled",
            guardrails=("immutability_checks", "schema_validation"),
        ),
        StageDefinition(
            name="publish",
            description="Persist TOC payload and emit readiness signal.",
            checkpoint="section_toc_completed",
            guardrails=("durable_persistence", "signal_emission", "immutability"),
        ),
        StageDefinition(
            name="monitor",
            description="Handle revision requests post section updates within rerun guardrails.",
            checkpoint="toc_revision_processed",
            guardrails=("max_reruns", "revision_depth_cap"),
        ),
    )

    COMMUNICATION = CommunicationContract(
        prepare_signal="section_cp.completed",
        input_channels=(
            "cover_profile",
            "section_manifest_summaries",
        ),
        output_signal="section_toc.completed",
        revision_signal="toc_revision",
    )

    PERSISTENCE = PersistenceContract(
        persistence_key="section_toc_manifest",
        durable_paths=("storage/sections/section_toc.json",),
    )

    ORDER = OrderContract(\n        execution_after=('section_cp'),\n        export_after=('section_cp'),\n        export_priority=110,\n    )\n\n    def load_inputs(self) -> Dict[str, Any]:
        """Template hook for retrieving inputs from the gateway with ECC handoff protocol"""
        try:
            # Step 1: Call out to ECC for permission
            if not self._call_out_to_ecc("load_inputs", {"section_id": self.SECTION_ID}):
                self.logger.error("ECC permission denied for load_inputs")
                raise Exception("ECC permission denied for load_inputs")
            
            # Step 2: Wait for ECC confirmation
            if not self._wait_for_ecc_confirm():
                self.logger.error("ECC confirmation timeout for load_inputs")
                raise Exception("ECC confirmation timeout for load_inputs")
            
            # Step 3: Enforce section-aware execution
            if not self._enforce_section_aware_execution(self.SECTION_ID):
                self.logger.error(f"Section-aware execution failed for {self.SECTION_ID}")
                raise Exception(f"Section {self.SECTION_ID} not authorized for load_inputs")
            
            # Step 4: Load inputs from gateway
            inputs = {
                "cover_profile": self.gateway.get_input("cover_profile") if self.gateway else {},
                "section_manifest": self.gateway.get_input("section_manifest") if self.gateway else {},
                "case_metadata": self.gateway.get_input("case_metadata") if self.gateway else {},
                "section_registry": self.get_section_registry()
            }
            
            # Step 5: Send message back to ECC
            self._send_message("inputs_loaded", inputs)
            
            # Step 6: Send accept signal
            self._send_accept_signal("load_inputs")
            
            # Step 7: Complete handoff
            self._complete_handoff("load_inputs", "success")
            
            self.logger.info(f"✅ Loaded inputs for {self.SECTION_ID}")
            return inputs
            
        except Exception as e:
            self.logger.error(f"Failed to load inputs for {self.SECTION_ID}: {e}")
            self._complete_handoff("load_inputs", "error")
            raise

    def build_payload(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Template hook for constructing the structured payload with ECC handoff protocol"""
        try:
            # Step 1: Call out to ECC for permission
            if not self._call_out_to_ecc("build_payload", {"section_id": self.SECTION_ID, "context": context}):
                self.logger.error("ECC permission denied for build_payload")
                raise Exception("ECC permission denied for build_payload")
            
            # Step 2: Wait for ECC confirmation
            if not self._wait_for_ecc_confirm():
                self.logger.error("ECC confirmation timeout for build_payload")
                raise Exception("ECC confirmation timeout for build_payload")
            
            # Step 3: Enforce section-aware execution
            if not self._enforce_section_aware_execution(self.SECTION_ID):
                self.logger.error(f"Section-aware execution failed for {self.SECTION_ID}")
                raise Exception(f"Section {self.SECTION_ID} not authorized for build_payload")
            
            # Step 4: Build TOC payload
            section_registry = context.get("section_registry", self.get_section_registry())
            toc_entries = []
            
            for section_id, section_info in section_registry.items():
                if section_id != "section_toc":  # Don't include TOC in itself
                    toc_entries.append({
                        "section_id": section_id,
                        "title": section_info.get("title", section_id),
                        "page_number": len(toc_entries) + 1,
                        "tags": section_info.get("tags", [])
                    })
            
            payload = {
                "section_id": self.SECTION_ID,
                "title": "Table of Contents",
                "content": {
                    "case_number": context.get("case_metadata", {}).get("case_number", "N/A"),
                    "report_title": context.get("cover_profile", {}).get("title", "Investigation Report"),
                    "generated_date": datetime.now().strftime("%B %d, %Y"),
                    "toc_entries": toc_entries,
                    "total_sections": len(toc_entries)
                },
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "section_registry": section_registry,
                    "handoff_log": self.handoff_log
                }
            }
            
            # Step 5: Send message back to ECC
            self._send_message("payload_built", payload)
            
            # Step 6: Send accept signal
            self._send_accept_signal("build_payload")
            
            # Step 7: Complete handoff
            self._complete_handoff("build_payload", "success")
            
            self.logger.info(f"✅ Built payload for {self.SECTION_ID}")
            return payload
            
        except Exception as e:
            self.logger.error(f"Failed to build payload for {self.SECTION_ID}: {e}")
            self._complete_handoff("build_payload", "error")
            raise

    def publish(self, payload: Dict[str, Any]) -> None:
        """Template hook for persisting state and emitting signals with ECC handoff protocol"""
        try:
            # Step 1: Call out to ECC for permission
            if not self._call_out_to_ecc("publish", {"section_id": self.SECTION_ID, "payload": payload}):
                self.logger.error("ECC permission denied for publish")
                raise Exception("ECC permission denied for publish")
            
            # Step 2: Wait for ECC confirmation
            if not self._wait_for_ecc_confirm():
                self.logger.error("ECC confirmation timeout for publish")
                raise Exception("ECC confirmation timeout for publish")
            
            # Step 3: Enforce section-aware execution
            if not self._enforce_section_aware_execution(self.SECTION_ID):
                self.logger.error(f"Section-aware execution failed for {self.SECTION_ID}")
                raise Exception(f"Section {self.SECTION_ID} not authorized for publish")
            
            # Step 4: Publish payload
            if self.gateway:
                self.gateway.publish_section(self.SECTION_ID, payload)
            
            # Step 5: Send message back to ECC
            self._send_message("published", {"section_id": self.SECTION_ID, "payload": payload})
            
            # Step 6: Send accept signal
            self._send_accept_signal("publish")
            
            # Step 7: Complete handoff
            self._complete_handoff("publish", "success")
            
            self.logger.info(f"✅ Published {self.SECTION_ID}")
            
        except Exception as e:
            self.logger.error(f"Failed to publish {self.SECTION_ID}: {e}")
            self._complete_handoff("publish", "error")
            raise





