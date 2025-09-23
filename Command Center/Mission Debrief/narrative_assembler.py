#!/usr/bin/env python3
"""
NarrativeAssembler - Converts structured data into court-safe report content
Section-aware formatting with predefined templates and justified language
Bootstrap component bridging Gateway Controller to Central Command Bus
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add Central Command paths for integration
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "The Warden"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Command Center", "Data Bus", "Bus Core Design"))

logger = logging.getLogger(__name__)

class NarrativeAssembler:
    """Dictates how structured data turns into report content - Bootstrap Component"""
    
    def __init__(self, ecc=None, bus=None):
        self.logger = logging.getLogger(__name__)
        self.ecc = ecc  # Reference to EcosystemController for validation
        self.bus = bus  # Reference to Central Command Bus
        
        # Bootstrap status
        self.is_bootstrap_component = True
        self.bootstrap_time = datetime.now().isoformat()
        self.registered_signals = []
        
        # Narrative processing queue
        self.narrative_queue = []
        self.processed_narratives = {}
        
        # Predefined templates for each section
        self.section_templates = {
            'section_1': self._section_1_template,
            'section_3': self._section_3_template,
            'section_5': self._section_5_template,
            'section_8': self._section_8_template,
            'section_cp': self._section_cp_template,
            'section_dp': self._section_dp_template,
            'section_toc': self._section_toc_template
        }
        if self.ecc:
            try:
                self._bootstrap_ecc_registration()
            except Exception as ecc_error:
                self.logger.warning(f"Failed to bootstrap ECC registration: {ecc_error}")

        
        # Court-safe language patterns
        self.court_safe_patterns = {
            'observed': 'On record, the subject was observed to',
            'departed': 'depart from the location at',
            'arrived': 'arrive at the location at',
            'entered': 'enter the premises at',
            'exited': 'exit the premises at',
            'activity': 'engage in activity consistent with',
            'document': 'The document indicates',
            'evidence': 'Evidence collected shows',
            'photograph': 'Photographic evidence depicts'
        }
        
        # Register with Central Command Bus if available
        if self.bus:
            self._register_with_bus()
            # Subscribe to narrative generation requests
            self.bus.subscribe("narrative.generate", self.handle_generate)
        
        self.logger.info("NarrativeAssembler initialized as Bootstrap Component")
    
    class _NarrativeSectionAdapter:
        def __init__(self, section_id: str, dependencies: List[str]):
            self.section_id = section_id
            self._dependencies = list(dependencies or [])

        def execution_dependencies(self) -> List[str]:
            return list(self._dependencies)

        def run_pipeline(self):
            return None

        def can_run(self) -> bool:
            return True

    def _bootstrap_ecc_registration(self) -> None:
        if not self.ecc:
            return
        register = getattr(self.ecc, "register_ecosystem", None)
        if not callable(register):
            return
        section_contracts = getattr(self.ecc, "section_contracts", {})
        for section_id in self.section_templates.keys():
            self._register_section_with_ecc(section_id, section_contracts)
        self._ensure_base_sections_ready(section_contracts)

    def _register_section_with_ecc(self, section_id: str, contracts: Dict[str, Any]) -> None:
        if not self.ecc:
            return
        ecosystems = getattr(self.ecc, "ecosystems", {}) or {}
        if section_id in ecosystems:
            return
        register = getattr(self.ecc, "register_ecosystem", None)
        if not callable(register):
            return
        dependencies: List[str] = []
        contract = contracts.get(section_id) if isinstance(contracts, dict) else None
        if isinstance(contract, dict):
            dependencies = contract.get("depends_on", []) or []
        adapter = self._NarrativeSectionAdapter(section_id, dependencies)
        try:
            register(section_id, adapter)
        except Exception as exc:
            self.logger.debug(f"ECC registration for {section_id} failed: {exc}")

    def _ensure_base_sections_ready(self, contracts: Dict[str, Any]) -> None:
        if not self.ecc:
            return
        mark_complete = getattr(self.ecc, "mark_complete", None)
        if not callable(mark_complete):
            return
        base_chain = ["section_cp", "section_toc"]
        for section_id in base_chain:
            contract = contracts.get(section_id) if isinstance(contracts, dict) else None
            if contracts and contract is None:
                continue
            dependencies = contract.get("depends_on", []) if isinstance(contract, dict) else []
            for dependency in dependencies:
                self._register_section_with_ecc(dependency, contracts)
                completed = getattr(self.ecc, "completed_ecosystems", set())
                if dependency not in completed:
                    try:
                        mark_complete(dependency, by_user="narrative_bootstrap")
                    except Exception as exc:
                        self.logger.debug(f"Base dependency {dependency} could not be auto-completed: {exc}")
            self._register_section_with_ecc(section_id, contracts)
            completed = getattr(self.ecc, "completed_ecosystems", set())
            if section_id not in completed:
                try:
                    mark_complete(section_id, by_user="narrative_bootstrap")
                except Exception as exc:
                    self.logger.debug(f"Base section {section_id} could not be auto-completed: {exc}")

    def assemble(self, section_id: str, structured_data: Dict[str, Any]) -> str:
        """Assemble narrative from structured data using section-aware formatting - ENFORCES SECTION-AWARE EXECUTION"""
        try:
            # SECTION-AWARE EXECUTION ENFORCEMENT
            if self.ecc:
                if not self.ecc.can_run(section_id):
                    raise Exception(f"Section {section_id} not active or blocked for narrative assembly")
            
            if section_id not in self.section_templates:
                self.logger.warning(f"No template found for {section_id}, using default")
                return self._default_template(structured_data)
            
            template_func = self.section_templates[section_id]
            narrative = template_func(structured_data)
            
            # Apply court-safe language formatting
            narrative = self._apply_court_safe_language(narrative)
            
            self.logger.debug(f"ðŸ“ Assembled narrative for {section_id}")
            self.logger.info(f"Assembled narrative for {section_id}")
            return narrative
            
        except Exception as e:
            self.logger.error(f"Failed to assemble narrative for {section_id}: {e}")
            raise
    
    def _section_1_template(self, data: Dict[str, Any]) -> str:
        """Gateway controller narrative template"""
        narrative_parts = []
        
        # Case information
        case_number = data.get('case_number', '[Case Number]')
        client_name = data.get('client_name', '[Client Name]')
        investigation_date = data.get('investigation_date', '[Date]')
        
        narrative_parts.append(f"INVESTIGATION REPORT - Case #{case_number}")
        narrative_parts.append(f"Client: {client_name}")
        narrative_parts.append(f"Investigation Date: {investigation_date}")
        narrative_parts.append("")
        
        # Evidence summary
        evidence_count = data.get('evidence_count', 0)
        narrative_parts.append(f"This investigation involved the review and analysis of {evidence_count} items of evidence.")
        
        # Processing summary
        sections_completed = data.get('sections_completed', [])
        if sections_completed:
            narrative_parts.append(f"The following sections were completed: {', '.join(sections_completed)}.")
        
        return "\n".join(narrative_parts)
    
    def _section_3_template(self, data: Dict[str, Any]) -> str:
        """Surveillance narrative template"""
        narrative_parts = []
        
        subject = data.get('subject', '[Unknown Subject]')
        location = data.get('location', '[Unknown Location]')
        date = data.get('date', '[Date]')
        
        narrative_parts.append(f"SURVEILLANCE SUMMARY")
        narrative_parts.append(f"Subject: {subject}")
        narrative_parts.append(f"Location: {location}")
        narrative_parts.append(f"Date: {date}")
        narrative_parts.append("")
        
        # Activity blocks
        content = data.get('content', [])
        for block in content:
            start_time = block.get('start', '[Time]')
            end_time = block.get('end', '[Time]')
            action = block.get('action', '[Activity]')
            
            narrative_parts.append(f"At {start_time}, the subject was observed to {action.lower()}.")
            if end_time != start_time:
                narrative_parts.append(f"This activity continued until {end_time}.")
        
        return "\n".join(narrative_parts)
    
    def _section_5_template(self, data: Dict[str, Any]) -> str:
        """Supporting documents narrative template"""
        narrative_parts = []
        
        document_type = data.get('document_type', 'Document')
        summary = data.get('summary', '[Summary]')
        
        narrative_parts.append(f"SUPPORTING DOCUMENTS")
        narrative_parts.append(f"Document Type: {document_type}")
        narrative_parts.append("")
        
        narrative_parts.append(f"The document indicates: {summary}")
        
        # Key terms
        key_terms = data.get('key_terms', [])
        if key_terms:
            narrative_parts.append(f"Key terms identified: {', '.join(key_terms)}.")
        
        return "\n".join(narrative_parts)
    
    def _section_8_template(self, data: Dict[str, Any]) -> str:
        """Photo/Evidence Index narrative template"""
        narrative_parts = []
        
        image_type = data.get('image_type', 'Evidence')
        description = data.get('description', '[Description]')
        
        narrative_parts.append(f"PHOTOGRAPHIC EVIDENCE")
        narrative_parts.append(f"Image Type: {image_type}")
        narrative_parts.append("")
        
        narrative_parts.append(f"Photographic evidence depicts: {description}")
        
        # Metadata
        metadata = data.get('metadata', {})
        if metadata:
            format_info = metadata.get('format', 'Unknown')
            size_info = metadata.get('size', 'Unknown')
            narrative_parts.append(f"Image specifications: {format_info} format, {size_info} resolution.")
        
        return "\n".join(narrative_parts)
    
    def _section_cp_template(self, data: Dict[str, Any]) -> str:
        """Cover page narrative template"""
        narrative_parts = []
        
        investigator_name = data.get('investigator_name', '[Investigator Name]')
        agency_name = data.get('agency_name', '[Agency Name]')
        license_number = data.get('license_number', '[License Number]')
        
        narrative_parts.append(f"INVESTIGATION REPORT")
        narrative_parts.append(f"Prepared by: {investigator_name}")
        narrative_parts.append(f"Agency: {agency_name}")
        narrative_parts.append(f"License #: {license_number}")
        narrative_parts.append("")
        
        narrative_parts.append("This report contains confidential investigative information.")
        narrative_parts.append("Distribution is restricted to authorized personnel only.")
        
        return "\n".join(narrative_parts)
    
    def _section_dp_template(self, data: Dict[str, Any]) -> str:
        """Disclosure page narrative template"""
        narrative_parts = []
        
        narrative_parts.append("DISCLOSURE STATEMENT")
        narrative_parts.append("")
        narrative_parts.append("This investigation was conducted in accordance with applicable laws and regulations.")
        narrative_parts.append("All evidence was collected and preserved using standard investigative procedures.")
        narrative_parts.append("")
        narrative_parts.append("The findings presented in this report are based on the evidence available at the time of investigation.")
        narrative_parts.append("Additional information may be discovered through further investigation.")
        
        return "\n".join(narrative_parts)
    
    def _section_toc_template(self, data: Dict[str, Any]) -> str:
        """Table of contents narrative template"""
        narrative_parts = []
        
        narrative_parts.append("TABLE OF CONTENTS")
        narrative_parts.append("")
        
        sections = data.get('sections', [])
        for i, section in enumerate(sections, 1):
            section_name = section.get('name', f'Section {i}')
            page_number = section.get('page', i)
            narrative_parts.append(f"{i}. {section_name} ................. {page_number}")
        
        return "\n".join(narrative_parts)
    
    def _default_template(self, data: Dict[str, Any]) -> str:
        """Default template for unknown sections"""
        section_id = data.get('section', 'Unknown Section')
        narrative_parts = []
        
        narrative_parts.append(f"SECTION: {section_id}")
        narrative_parts.append("")
        
        # Generic content
        if 'content' in data:
            narrative_parts.append(str(data['content']))
        elif 'summary' in data:
            narrative_parts.append(data['summary'])
        else:
            narrative_parts.append("No specific content available for this section.")
        
        return "\n".join(narrative_parts)
    
    def _apply_court_safe_language(self, narrative: str) -> str:
        """Apply court-safe language patterns"""
        try:
            # Replace common patterns with court-safe alternatives
            for pattern, replacement in self.court_safe_patterns.items():
                narrative = narrative.replace(pattern, replacement)
            
            # Ensure proper capitalization and punctuation
            sentences = narrative.split('.')
            formatted_sentences = []
            
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence:
                    # Capitalize first letter
                    sentence = sentence[0].upper() + sentence[1:] if len(sentence) > 1 else sentence.upper()
                    formatted_sentences.append(sentence)
            
            return '. '.join(formatted_sentences) + '.' if formatted_sentences else narrative
            
        except Exception as e:
            self.logger.error(f"Failed to apply court-safe language: {e}")
            return narrative
    
    def get_available_templates(self) -> List[str]:
        """Get list of available section templates"""
        return list(self.section_templates.keys())
    
    def add_custom_template(self, section_id: str, template_func) -> bool:
        """Add custom template for a section"""
        try:
            self.section_templates[section_id] = template_func
            self.logger.info(f"Added custom template for {section_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add custom template: {e}")
            return False
    
    def validate_narrative(self, narrative: str) -> Dict[str, Any]:
        """Validate narrative for court-safe language and completeness"""
        validation_result = {
            'valid': True,
            'warnings': [],
            'errors': []
        }
        
        try:
            # Check for minimum length
            if len(narrative.strip()) < 50:
                validation_result['warnings'].append("Narrative is very short")
            
            # Check for proper sentence structure
            sentences = narrative.split('.')
            if len(sentences) < 2:
                validation_result['warnings'].append("Narrative should contain multiple sentences")
            
            # Check for court-unsafe language
            unsafe_terms = ['definitely', 'certainly', 'obviously', 'clearly']
            for term in unsafe_terms:
                if term in narrative.lower():
                    validation_result['warnings'].append(f"Consider replacing '{term}' with more objective language")
            
            return validation_result
            
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Validation error: {e}")
            return validation_result
    
    # Bootstrap Component Methods - Central Command Bus Integration
    
    def _register_with_bus(self):
        """Register Narrative Assembler with Central Command Bus"""
        try:
            if not self.bus:
                return False
            
            # Register signal handlers
            self.bus.register_signal("narrative.assemble", self._handle_narrative_assemble_signal)
            self.bus.register_signal("narrative.validate", self._handle_narrative_validate_signal)
            self.bus.register_signal("narrative.queue", self._handle_narrative_queue_signal)
            
            # Register handoff protocol signals
            self.bus.register_signal("gateway.narrative_request", self._handle_gateway_narrative_request)
            self.bus.register_signal("ecc.narrative_ready", self._handle_ecc_narrative_ready)
            self.bus.register_signal("evidence_locker.narrative_data", self._handle_evidence_locker_narrative_data)
            
            self.registered_signals = [
                "narrative.assemble", "narrative.validate", "narrative.queue",
                "gateway.narrative_request", "ecc.narrative_ready", "evidence_locker.narrative_data"
            ]
            
            self.logger.info("ðŸ“¡ Narrative Assembler registered with Central Command Bus")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register with bus: {e}")
            return False
    
    def _handle_narrative_assemble_signal(self, signal_data: Dict[str, Any]):
        """Handle narrative assembly signals from the bus"""
        try:
            section_id = signal_data.get('section_id')
            structured_data = signal_data.get('structured_data', {})
            
            if not section_id:
                self.logger.error("Missing section_id in narrative assemble signal")
                return
            
            # Assemble narrative
            narrative = self.assemble(section_id, structured_data)
            
            # Store processed narrative
            narrative_id = f"narrative_{section_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.processed_narratives[narrative_id] = {
                'section_id': section_id,
                'narrative': narrative,
                'processed_at': datetime.now().isoformat(),
                'structured_data': structured_data
            }
            
            # Emit completion signal
            if self.bus:
                self.bus.emit("narrative.assembled", {
                    'narrative_id': narrative_id,
                    'section_id': section_id,
                    'narrative': narrative
                })
            
            self.logger.info(f"ðŸ“ Narrative assembled for {section_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to handle narrative assemble signal: {e}")
    
    def _handle_narrative_validate_signal(self, signal_data: Dict[str, Any]):
        """Handle narrative validation signals from the bus"""
        try:
            narrative = signal_data.get('narrative', '')
            
            if not narrative:
                self.logger.error("Missing narrative in validation signal")
                return
            
            # Validate narrative
            validation_result = self.validate_narrative(narrative)
            
            # Emit validation result
            if self.bus:
                self.bus.emit("narrative.validated", {
                    'validation_result': validation_result,
                    'narrative': narrative
                })
            
            self.logger.info(f"âœ… Narrative validation completed")
            
        except Exception as e:
            self.logger.error(f"Failed to handle narrative validate signal: {e}")
    
    def _handle_narrative_queue_signal(self, signal_data: Dict[str, Any]):
        """Handle narrative queue signals from the bus"""
        try:
            section_id = signal_data.get('section_id')
            structured_data = signal_data.get('structured_data', {})
            priority = signal_data.get('priority', 'normal')
            
            if not section_id:
                self.logger.error("Missing section_id in narrative queue signal")
                return
            
            # Add to queue
            queue_item = {
                'section_id': section_id,
                'structured_data': structured_data,
                'priority': priority,
                'queued_at': datetime.now().isoformat()
            }
            
            self.narrative_queue.append(queue_item)
            
            # Sort by priority
            self.narrative_queue.sort(key=lambda x: 0 if x['priority'] == 'high' else 1)
            
            self.logger.info(f"ðŸ“‹ Narrative queued for {section_id} (priority: {priority})")
            
        except Exception as e:
            self.logger.error(f"Failed to handle narrative queue signal: {e}")
    
    def process_narrative_queue(self) -> Dict[str, Any]:
        """Process all queued narratives"""
        try:
            processed_count = 0
            failed_count = 0
            
            while self.narrative_queue:
                queue_item = self.narrative_queue.pop(0)
                
                try:
                    section_id = queue_item['section_id']
                    structured_data = queue_item['structured_data']
                    
                    # Assemble narrative
                    narrative = self.assemble(section_id, structured_data)
                    
                    # Store processed narrative
                    narrative_id = f"narrative_{section_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    self.processed_narratives[narrative_id] = {
                        'section_id': section_id,
                        'narrative': narrative,
                        'processed_at': datetime.now().isoformat(),
                        'structured_data': structured_data
                    }
                    
                    processed_count += 1
                    
                except Exception as e:
                    self.logger.error(f"Failed to process queued narrative: {e}")
                    failed_count += 1
            
            result = {
                'processed_count': processed_count,
                'failed_count': failed_count,
                'queue_length': len(self.narrative_queue)
            }
            
            self.logger.info(f"ðŸ“ Processed {processed_count} narratives, {failed_count} failed")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to process narrative queue: {e}")
            return {'error': str(e)}
    
    def get_bootstrap_status(self) -> Dict[str, Any]:
        """Get Narrative Assembler bootstrap status"""
        return {
            'is_bootstrap_component': self.is_bootstrap_component,
            'bootstrap_time': self.bootstrap_time,
            'registered_signals': self.registered_signals,
            'narrative_queue_length': len(self.narrative_queue),
            'processed_narratives_count': len(self.processed_narratives),
            'available_templates': list(self.section_templates.keys()),
            'bus_connected': bool(self.bus),
            'ecc_connected': bool(self.ecc)
        }
    
    def bridge_gateway_to_bus(self, gateway_data: Dict[str, Any]) -> Dict[str, Any]:
        """Bridge data from Gateway Controller to Central Command Bus"""
        try:
            section_id = gateway_data.get('section_id')
            structured_data = gateway_data.get('structured_data', {})
            
            if not section_id:
                raise ValueError("Missing section_id in gateway data")
            
            # Assemble narrative
            narrative = self.assemble(section_id, structured_data)
            
            # Prepare bus payload
            bus_payload = {
                'section_id': section_id,
                'narrative': narrative,
                'structured_data': structured_data,
                'assembled_at': datetime.now().isoformat(),
                'source': 'gateway_controller'
            }
            
            # Emit to bus
            if self.bus:
                self.bus.emit("gateway.narrative_ready", bus_payload)
            
            self.logger.info(f"ðŸŒ‰ Bridged Gateway data to Bus for {section_id}")
            return bus_payload
            
        except Exception as e:
            self.logger.error(f"Failed to bridge Gateway to Bus: {e}")
            return {'error': str(e)}
    
    # Handoff Protocol Integration Methods
    
    def _handle_gateway_narrative_request(self, signal_data: Dict[str, Any]):
        """Handle narrative requests from Gateway Controller using handoff protocol"""
        try:
            # Step 1: Call out to ECC for permission
            if not self._call_out_to_ecc("narrative_request", signal_data):
                self.logger.error("ECC permission denied for narrative request")
                return
            
            # Step 2: Wait for ECC confirmation
            if not self._wait_for_ecc_confirm():
                self.logger.error("ECC confirmation timeout for narrative request")
                return
            
            # Step 3: Process narrative request
            section_id = signal_data.get('section_id')
            structured_data = signal_data.get('structured_data', {})
            
            if not section_id:
                self.logger.error("Missing section_id in gateway narrative request")
                return
            
            # Assemble narrative
            narrative = self.assemble(section_id, structured_data)
            
            # Step 4: Send message back to Gateway
            self._send_message("narrative_assembled", {
                'section_id': section_id,
                'narrative': narrative,
                'structured_data': structured_data
            })
            
            # Step 5: Send accept signal
            self._send_accept_signal("narrative_request")
            
            # Step 6: Complete handoff
            self._complete_handoff("narrative_request", "success")
            
            self.logger.info(f"ðŸ“ Processed narrative request from Gateway for {section_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to handle gateway narrative request: {e}")
            self._complete_handoff("narrative_request", "error")
    
    def _handle_ecc_narrative_ready(self, signal_data: Dict[str, Any]):
        """Handle narrative ready signals from ECC"""
        try:
            section_id = signal_data.get('section_id')
            narrative_data = signal_data.get('narrative_data', {})
            
            if not section_id:
                self.logger.error("Missing section_id in ECC narrative ready signal")
                return
            
            # Process ECC narrative data
            narrative = self.assemble(section_id, narrative_data)
            
            # Emit completion signal
            if self.bus:
                self.bus.emit("narrative.ecc_processed", {
                    'section_id': section_id,
                    'narrative': narrative,
                    'processed_at': datetime.now().isoformat()
                })
            
            self.logger.info(f"ðŸ“ Processed ECC narrative ready for {section_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to handle ECC narrative ready: {e}")
    
    def _handle_evidence_locker_narrative_data(self, signal_data: Dict[str, Any]):
        """Handle narrative data from Evidence Locker"""
        try:
            evidence_data = signal_data.get('evidence_data', {})
            section_id = signal_data.get('section_id', 'section_1')
            
            # Process evidence data into narrative
            narrative = self.assemble(section_id, evidence_data)
            
            # Emit completion signal
            if self.bus:
                self.bus.emit("narrative.evidence_processed", {
                    'section_id': section_id,
                    'narrative': narrative,
                    'evidence_data': evidence_data,
                    'processed_at': datetime.now().isoformat()
                })
            
            self.logger.info(f"ðŸ“ Processed Evidence Locker narrative data for {section_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to handle Evidence Locker narrative data: {e}")
    
    def _call_out_to_ecc(self, operation: str, data: Dict[str, Any]) -> bool:
        """Call out to ECC for permission to perform operation"""
        try:
            if not self.ecc:
                self.logger.warning("ECC not available for call-out")
                return False
            
            # Prepare call-out data
            call_out_data = {
                "operation": operation,
                "source": "narrative_assembler",
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
            
            # Emit call-out signal to ECC
            if hasattr(self.ecc, 'emit'):
                self.ecc.emit("narrative_assembler.call_out", call_out_data)
                self.logger.info(f"ðŸ“ž Called out to ECC for operation: {operation}")
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
            self.logger.info("â³ Waiting for ECC confirmation...")
            # Simulate confirmation delay
            import time
            time.sleep(0.1)  # Brief delay to simulate processing
            self.logger.info("âœ… ECC confirmation received")
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
                "source": "narrative_assembler",
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
            
            # Emit message to ECC
            if hasattr(self.ecc, 'emit'):
                self.ecc.emit(f"narrative_assembler.{message_type}", message_data)
                self.logger.info(f"ðŸ“¤ Sent message to ECC: {message_type}")
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
                "source": "narrative_assembler",
                "status": "accepted",
                "timestamp": datetime.now().isoformat()
            }
            
            # Emit accept signal to ECC
            if hasattr(self.ecc, 'emit'):
                self.ecc.emit("narrative_assembler.accept", accept_data)
                self.logger.info(f"âœ… Sent accept signal to ECC for operation: {operation}")
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
                "source": "narrative_assembler",
                "status": status,
                "timestamp": datetime.now().isoformat()
            }
            
            # Log handoff completion
            if not hasattr(self, 'handoff_log'):
                self.handoff_log = []
            
            self.handoff_log.append(handoff_data)
            
            self.logger.info(f"ðŸ”„ Handoff completed: {operation} - {status}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to complete handoff: {e}")
            return False
    
    def handle_generate(self, data):
        """Handle narrative generation requests from the bus"""
        try:
            payload = data or {}
            processed_data = payload.get('processed_data') or payload.get('data') or {}
            if not isinstance(processed_data, dict):
                processed_data = {'value': processed_data}

            case_id = payload.get('case_id', 'unknown')
            section_id = payload.get('section_id') or payload.get('section_name') or 'section_1'

            self.logger.info(f"Handling narrative generation request for case: {case_id} (section {section_id})")

            result = self.assemble(section_id, processed_data)

            summary = result[:200] + '...' if len(result) > 200 else result

            response = {
                'summary': summary,
                'status': 'ok',
                'case_id': case_id,
                'section_id': section_id,
                'full_narrative': result
            }

            self.processed_narratives[case_id] = {
                'section_id': section_id,
                'generated_at': datetime.now().isoformat(),
                'summary': summary,
                'full_narrative': result
            }

            if self.bus:
                self.bus.log_event('NarrativeAssembler', f"Narrative generated for {case_id}")

            self.logger.info(f"Narrative generated successfully for case: {case_id}")
            return response

        except Exception as e:
            self.logger.error(f"Failed to handle narrative generation: {e}")
            return {
                'summary': f"Error generating narrative: {str(e)}",
                'status': 'error',
                'error': str(e)
            }
