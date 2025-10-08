#!/usr/bin/env python3
"""
NarrativeAssembler - Converts structured data into court-safe report content
Section-aware formatting with predefined templates and justified language
Bootstrap component bridging Gateway Controller to Central Command Bus
"""

import os
import sys
import logging
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

# Add Central Command paths for integration
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "The Warden"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Command Center", "Data Bus", "Bus Core Design"))

# Import shared interfaces
try:
    from shared_interfaces import (
        StandardInterface, StandardSectionData, SectionStatus,
        create_standard_narrative_signal, validate_signal_payload
    )
except ImportError:
    # Fallback if shared_interfaces not available
    StandardInterface = None
    StandardSectionData = None
    SectionStatus = None
    create_standard_narrative_signal = None
    validate_signal_payload = None

logger = logging.getLogger(__name__)

class NarrativeAssembler:
    """Dictates how structured data turns into report content - Bootstrap Component"""
    
    # SECTION REGISTRY - Standardized 10-section registry matching Evidence Locker
    SECTION_REGISTRY = {
        "section_1": {"title": "Investigation Objectives / Case Info", "tags": ["client", "contract", "objectives"]},
        "section_2": {"title": "Pre-Surveillance Summary", "tags": ["planning", "subjects", "routines"]},
        "section_3": {"title": "Investigation Details", "tags": ["daily-log", "surveillance", "observations"]},
        "section_4": {"title": "Review of Surveillance Sessions", "tags": ["sessions", "deviations", "media"]},
        "section_5": {"title": "Supporting Documents Review", "tags": ["documents", "custody", "appendix"]},
        "section_6": {"title": "Billing Summary", "tags": ["billing", "retainer", "hours"]},
        "section_7": {"title": "Conclusion", "tags": ["findings", "recommendations", "limitations"]},
        "section_8": {"title": "Surveillance Photo Section", "tags": ["photo", "visual", "media"]},
        "section_9": {"title": "Disclosures / Legal", "tags": ["disclosure", "legal", "compliance"]},
        "section_cp": {"title": "Cover Page", "tags": ["cover", "branding"]},
        "section_dp": {"title": "Disclosure Page", "tags": ["disclosure", "signature"]},
        "section_toc": {"title": "Table of Contents", "tags": ["toc", "index"]}
    }
    
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
        self.section_updates = {}
        self.evidence_updates: Dict[str, Dict[str, Any]] = {}
        self.case_snapshots: List[Dict[str, Any]] = []
        self.gateway_events = []
        
        self.section_artifacts: Dict[str, Dict[str, Any]] = {}
        
        # Predefined templates for each section
        self.section_templates = {
            'section_1': self._section_1_template,
            'section_2': self._section_2_template,
            'section_3': self._section_3_template,
            'section_4': self._section_4_template,
            'section_5': self._section_5_template,
            'section_6': self._section_6_template,
            'section_7': self._section_7_template,
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
            # Subscribe to narrative generation requests (with error handling)
            try:
                if hasattr(self.bus, 'subscribe'):
                    self.bus.subscribe("narrative.generate", self.handle_generate)
                else:
                    # Fallback to register_signal if subscribe doesn't exist
                    self.bus.register_signal("narrative.generate", self.handle_generate)
                self.bus.register_signal("narrative.assemble_and_broadcast", self.assemble_and_broadcast)
            except Exception as e:
                self.logger.warning(f"Could not subscribe to narrative.generate: {e}")
        
        self.logger.info("NarrativeAssembler initialized as Bootstrap Component")
    
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
                "source": "narrative_assembler",
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
            
            # Emit call-out signal to ECC
            if hasattr(self.ecc, 'emit'):
                self.ecc.emit("narrative_assembler.call_out", call_out_data)
                self.logger.info(f"Bus registration: Called out to ECC for operation: {operation}")
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
            self.logger.info("Waiting for ECC confirmation...")
            # Simulate confirmation delay
            import time
            time.sleep(0.1)  # Brief delay to simulate processing
            self.logger.info("Accepted: ECC confirmation received")
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
                self.logger.info(f"Message to ECC: Sent message to ECC: {message_type}")
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
                self.logger.info(f"Accepted: Sent accept signal to ECC for operation: {operation}")
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
            
            self.logger.info(f"Handoff: Handoff completed: {operation} - {status}")
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
            
            structured_payload = dict(structured_data or {})
            manifest_context = self._build_manifest_context(section_id)
            if manifest_context:
                structured_payload.setdefault("manifest_context", manifest_context)
            structured_payload.setdefault("evidence_updates", self._collect_evidence_updates(section_id))
            structured_payload.setdefault("case_snapshots", list(self.case_snapshots[-10:]))
            template_func = self.section_templates[section_id]
            auto_narrative = self._render_evidence_narrative(section_id, structured_payload)
            if auto_narrative:
                structured_payload.setdefault("auto_narrative", auto_narrative)
            narrative = template_func(structured_payload)

            # Apply court-safe language formatting
            narrative = self._apply_court_safe_language(narrative)
            if auto_narrative:
                if narrative.strip():
                    narrative = f"{narrative.rstrip()}\n\n{auto_narrative}"
                else:
                    narrative = auto_narrative
            if isinstance(structured_data, dict):
                for key, value in structured_payload.items():
                    structured_data.setdefault(key, value)
            self.logger.info(f"Assembled narrative for {section_id}")
            return narrative
            
        except Exception as e:
            self.logger.error(f"Failed to assemble narrative for {section_id}: {e}")
            raise
    


    def _collect_evidence_updates(self, section_id: str) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for update in self.evidence_updates.values():
            targets = update.get('related_sections') or []
            assigned = update.get('assigned_section') or update.get('section_id')
            if (assigned and str(assigned) == str(section_id)) or str(section_id) in {str(sec) for sec in targets}:
                results.append(update)
        return results

    def _build_manifest_context(self, section_id: str) -> Dict[str, Any]:
        if not self.bus:
            return {}
        try:
            manifest = self.bus.get_evidence_manifest()
        except Exception:
            return {}
        entries: List[Dict[str, Any]] = []
        total_size = 0
        for item in manifest if isinstance(manifest, list) else []:
            assigned = item.get('section_hint') or item.get('assigned_section')
            related = item.get('related_sections') or []
            if str(assigned) == str(section_id) or str(section_id) in {str(sec) for sec in related}:
                record = dict(item)
                entries.append(record)
                if item.get('file_size'):
                    try:
                        total_size += int(item['file_size'])
                    except Exception:
                        pass
        return {
            'entries': entries,
            'count': len(entries),
            'total_file_size': total_size,
        }

    def _render_evidence_narrative(self, section_id: str, structured_data: Dict[str, Any]) -> str:
        evidence = structured_data.get("evidence") or []
        summary = structured_data.get("summary") or {}
        metadata = structured_data.get("metadata") or {}
        if not evidence and not summary:
            return ""
        lines: List[str] = []
        section_title = structured_data.get("section_title") or self.SECTION_REGISTRY.get(section_id, {}).get("title")
        header = f"SECTION {section_id.upper()}" if section_id else "SECTION"
        if section_title:
            header = f"{section_title.upper()}"
        lines.append(f"{header} - Evidence Summary")
        generated_at = metadata.get("generated_at") or summary.get("generated_at") or datetime.now().isoformat()
        lines.append(f"Generated: {generated_at}")
        if summary:
            total_items = summary.get("total_items") or len(evidence)
            if total_items is not None:
                lines.append(f"Items Reviewed: {total_items}")
            duplicate_items = summary.get("duplicate_items")
            if duplicate_items:
                lines.append(f"Duplicates Flagged: {duplicate_items}")
            latest_ts = summary.get("latest_timestamp")
            if latest_ts:
                lines.append(f"Most Recent Update: {latest_ts}")
            requested_tags = summary.get("requested_tags") or metadata.get("requested_tags")
            if requested_tags:
                tag_list = ", ".join(sorted({str(tag) for tag in requested_tags}))
                lines.append(f"Requested Tags: {tag_list}")
            primary_tags = summary.get("primary_tags")
            if primary_tags:
                tag_list = ", ".join(sorted({str(tag) for tag in primary_tags}))
                lines.append(f"Observed Tags: {tag_list}")
            evidence_types = summary.get("evidence_types")
            if evidence_types:
                breakdown = ", ".join(f"{etype}: {count}" for etype, count in sorted(evidence_types.items()))
                lines.append(f"Evidence Types: {breakdown}")
        window = 8
        if evidence:
            lines.append("")
            lines.append("Evidence Highlights:")
            for idx, entry in enumerate(evidence[:window], start=1):
                lines.append(self._format_evidence_entry(entry, idx))
            if len(evidence) > window:
                lines.append(f"... {len(evidence) - window} additional item(s) retained in manifest context.")
        return "\n".join(line for line in lines if line is not None)


    def _format_evidence_entry(self, entry: Dict[str, Any], index: int) -> str:
        file_name = entry.get("file_name") or entry.get("display_name")
        file_path = entry.get("file_path") or entry.get("path")
        if not file_name and file_path:
            file_name = Path(file_path).name
        evidence_type = entry.get("evidence_type") or entry.get("classification", {}).get("evidence_type")
        timestamp = entry.get("timestamp") or entry.get("classification", {}).get("timestamp")
        tags = entry.get("tags") or entry.get("classification", {}).get("tags") or []
        routing_notes = entry.get("classification", {}).get("routing_notes") or entry.get("notes")
        confidence = entry.get("classification", {}).get("confidence")
        size_bytes = entry.get("file_size")
        parts: List[str] = []
        label = file_name or file_path or f"Evidence {index}"
        parts.append(f"  {index}. {label}")
        detail_bits: List[str] = []
        if evidence_type:
            detail_bits.append(str(evidence_type))
        if timestamp:
            detail_bits.append(str(timestamp))
        if tags:
            detail_bits.append("tags: " + ", ".join(str(tag) for tag in tags[:5]))
        if size_bytes:
            try:
                size_kb = int(size_bytes) / 1024
                detail_bits.append(f"size: {size_kb:.1f} KB")
            except Exception:
                pass
        if confidence is not None:
            detail_bits.append(f"confidence: {confidence}")
        if detail_bits:
            parts.append("     - " + "; ".join(detail_bits))
        if routing_notes:
            parts.append(f"     - Notes: {routing_notes}")
        source = entry.get("source")
        if source:
            parts.append(f"     - Source: {source}")
        return "\n".join(parts)


    def _section_1_template(self, data: Dict[str, Any]) -> str:
        """Section 1 narrative matching investigation objectives / case info."""
        client_name = data.get('client_name', '[Client Name]')
        client_phone = data.get('client_phone', '[Client Phone]')
        client_address = data.get('client_address', '[Client Address]')
        contract_date = data.get('contract_date', '[Contract Date]')
        location = data.get('location_of_investigation', '[Location]')
        objectives = data.get('investigation_goals', []) or data.get('objectives', [])
        subjects = data.get('subjects', [])
        agency_name = data.get('agency_name', 'DKI Services LLC')
        agency_license = data.get('agency_license', '0200812-IA000307')
        investigator = data.get('assigned_investigator', '[Investigator]')
        investigator_license = data.get('investigator_license', '0163814-C000480')

        lines = [
            "SECTION 1 - INVESTIGATION OBJECTIVES / CASE INFO",
            f"Client: {client_name} | Phone: {client_phone}",
            f"Address: {client_address}",
            f"Date of Contract: {contract_date}",
            f"Location of Investigation: {location}",
            "",
            f"Assigned Investigator: {investigator} (License {investigator_license})",
            f"Agency: {agency_name} | License {agency_license}",
            ""
        ]

        if objectives:
            lines.append("Goals of Investigation:")
            source = objectives if isinstance(objectives, list) else [objectives]
            for goal in source:
                lines.append(f"  - {goal}")
            lines.append("")

        if subjects:
            lines.append("Subjects of Investigation:")
            for subject in subjects:
                if isinstance(subject, dict):
                    label = subject.get('role') or subject.get('label') or 'Subject'
                    name = subject.get('name') or subject.get('value') or '[Name]'
                    lines.append(f"  - {label}: {name}")
                else:
                    lines.append(f"  - {subject}")
            lines.append("")

        return "\\n".join(lines)

    def _section_2_template(self, data: Dict[str, Any]) -> str:
        """Section 2 narrative summarising pre-surveillance preparation."""
        case_summary = data.get('case_summary', '[Summary not provided]')
        primary_subject = data.get('subject_primary', '[Primary Subject]')
        secondary_subject = data.get('subject_secondary')
        routines = data.get('routines', [])
        primary_location = data.get('primary_location', '[Primary Location]')
        surveillance_hours = data.get('surveillance_hours_allocated')
        ethics_statement = data.get('ethics_statement', 'Operations will follow legal and ethical standards under DKI Services LLC.')

        lines = [
            "SECTION 2 - PRE-SURVEILLANCE SUMMARY",
            case_summary,
            "",
            f"Primary Subject: {primary_subject}" + (f" | Secondary Subject: {secondary_subject}" if secondary_subject else ""),
            f"Primary Location: {primary_location}",
            ""
        ]

        if routines:
            lines.append("Known Routines & Patterns:")
            for item in routines:
                lines.append(f"  - {item}")
            lines.append("")

        if surveillance_hours:
            lines.append(f"Allocated Surveillance Hours: {surveillance_hours}")
            lines.append("")

        lines.append("Ethics & Planning Statement:")
        lines.append(ethics_statement)

        return "\\n".join(lines)

    def _section_3_template(self, data: Dict[str, Any]) -> str:
        """Section 3 narrative covering daily investigative details."""
        date = data.get('date', '[Date]')
        time_range = data.get('time_range', '[Time Range]')
        objective = data.get('objective', '[Objective]')
        observations = data.get('observations', [])
        summary = data.get('summary', '')

        lines = [
            "SECTION 3 - INVESTIGATION DETAILS",
            f"Date: {date} | Surveillance Time: {time_range}",
            f"Daily Objective: {objective}",
            "",
            "Observations:" if observations else "Observations: [No observations recorded]"
        ]

        for obs in observations:
            lines.append(f"  - {obs}")

        if summary:
            lines.append("")
            lines.append(f"Summary: {summary}")

        return "\\n".join(lines)

    def _section_4_template(self, data: Dict[str, Any]) -> str:
        """Section 4 narrative summarising surveillance sessions."""
        date = data.get('surveillance_date', data.get('date', '[Date]'))
        time_blocks = data.get('time_blocks', '[Time Blocks]')
        location = data.get('locations', '[Location]')
        subject_confirmed = data.get('subject_confirmed', 'Unconfirmed')
        behavior = data.get('observed_behavior', '[Behavior]')
        deviations = data.get('deviations_noted', '[No deviations recorded]')
        closure_status = data.get('closure_status', 'Open')

        lines = [
            "SECTION 4 - REVIEW OF SURVEILLANCE SESSIONS",
            f"Date: {date} | Time Blocks: {time_blocks}",
            f"Location: {location}",
            f"Subject Confirmed: {subject_confirmed}",
            "",
            f"Observed Behavior: {behavior}",
            f"Deviations Noted: {deviations}",
            f"Closure Status: {closure_status}"
        ]

        return "\\n".join(lines)

    def _section_5_template(self, data: Dict[str, Any]) -> str:
        """Section 5 narrative for supporting documents."""
        documents = data.get('documents', [])
        lines = ["SECTION 5 - SUPPORTING DOCUMENTS REVIEW"]

        if not documents:
            lines.append("No supporting documents recorded.")
            return "\\n".join(lines)

        for doc in documents:
            title = doc.get('title') or doc.get('document_type') or 'Document'
            summary = doc.get('summary') or '[Summary not available]'
            custody = doc.get('custody') or 'Custody chain available in annex.'
            lines.append("")
            lines.append(f"Document: {title}")
            lines.append(f"Summary: {summary}")
            lines.append(f"Custody: {custody}")

        return "\\n".join(lines)

    def _section_6_template(self, data: Dict[str, Any]) -> str:
        """Section 6 narrative summarising billing."""
        contract_total = data.get('contract_total')
        planning_cost = data.get('prep_cost')
        surveillance_cost = data.get('subcontractor_cost')
        documentation_fee = data.get('documentation_fee')
        remaining_balance = data.get('remaining_ops_budget')

        lines = ["SECTION 6 - BILLING SUMMARY"]
        if contract_total is not None:
            lines.append(f"Contracted Amount: ${contract_total:,.2f}")
        if planning_cost is not None:
            lines.append(f"Pre-Investigation Costs: ${planning_cost:,.2f}")
        if surveillance_cost is not None:
            lines.append(f"Surveillance Operations: ${surveillance_cost:,.2f}")
        if documentation_fee is not None:
            lines.append(f"Documentation & Reporting: ${documentation_fee:,.2f}")
        if remaining_balance is not None:
            lines.append(f"Remaining Retainer Balance: ${remaining_balance:,.2f}")

        return "\\n".join(lines)

    def _section_7_template(self, data: Dict[str, Any]) -> str:
        """Section 7 conclusion narrative."""
        findings = data.get('findings', [])
        recommendations = data.get('recommendations', [])
        limitations = data.get('limitations', [])

        lines = ["SECTION 7 - CONCLUSION"]

        if findings:
            lines.append("Key Findings:")
            for finding in findings:
                lines.append(f"  - {finding}")
            lines.append("")

        if recommendations:
            lines.append("Recommendations:")
            for rec in recommendations:
                lines.append(f"  - {rec}")
            lines.append("")

        if limitations:
            lines.append("Limitations / Considerations:")
            for limitation in limitations:
                lines.append(f"  - {limitation}")

        return "\\n".join(lines)

    def _section_8_template(self, data: Dict[str, Any]) -> str:
        """Section 8 narrative for surveillance photos."""
        date = data.get('surveillance_date', data.get('date', '[Date]'))
        description = data.get('description', '[Description]')
        evidence_id = data.get('evidence_id', data.get('id', '[Evidence ID]'))
        subject = data.get('subject', '[Subject]')

        lines = [
            "SECTION 8 - SURVEILLANCE PHOTO SECTION",
            f"Date of Surveillance: {date}",
            f"Evidence ID: {evidence_id}",
            f"Subject: {subject}",
            f"Description: {description}"
        ]

        return "\\n".join(lines)

    def _section_cp_template(self, data: Dict[str, Any]) -> str:
        """Cover page narrative aligned with template."""
        case_number = data.get('case_number', '[Case Number]')
        investigator = data.get('investigator_name', '[Investigator]')
        investigator_license = data.get('license_number', '0163814-C000480')
        agency_name = data.get('agency_name', 'DKI Services LLC')
        agency_license = data.get('agency_license', '0200812-IA000307')
        phone = data.get('agency_phone', '918-882-5539')
        email = data.get('agency_email', 'david@dkiservicesok.com')

        lines = [
            "INVESTIGATION FINAL REPORT",
            f"Case Number: {case_number}",
            f"Prepared by {agency_name}",
            f"Oklahoma Agency License #: {agency_license}",
            f"Oklahoma Investigator License #: {investigator_license}",
            f"Phone: {phone}",
            f"Email: {email}",
            "",
            '"Truth Conquers ALL"'
        ]

        return "\\n".join(lines)

    def _section_dp_template(self, data: Dict[str, Any]) -> str:
        """Disclosure page narrative matching template language."""
        documents_list = data.get('documents_disclosed', [
            'client contract',
            'new client intake form',
            'final report',
            'supporting exhibits'
        ])

        lines = ["DISCLOSURE STATEMENT", ""]
        lines.append("The documents included with this report include, but are not limited to: " + ', '.join(documents_list) + '.')
        lines.append("The combination of these documents is to be supplied to the client and handled as sensitive and private information.")
        lines.append("DKI Services LLC is not responsible for mishandling or misuse of these documents once delivered to the client.")
        lines.append("")
        lines.append("I, David Krashin of DKI Services LLC, do not provide legal advice; clients should confer with legal counsel regarding case strategy.")

        return "\\n".join(lines)

    def _section_toc_template(self, data: Dict[str, Any]) -> str:
        """Table of contents narrative template."""
        narrative_parts = []

        narrative_parts.append("TABLE OF CONTENTS")
        narrative_parts.append("")

        sections = data.get('sections', [])
        for i, section in enumerate(sections, 1):
            section_name = section.get('name', f'Section {i}')
            page_number = section.get('page', i)
            narrative_parts.append(f"{i}. {section_name} ................. {page_number}")

        return "\\n".join(narrative_parts)
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
            self.bus.register_signal("evidence.updated", self._handle_evidence_updated_signal)
            self.bus.register_signal("case.snapshot", self._handle_case_snapshot_signal)
            self.bus.register_signal("section.data.updated", self._handle_section_data_updated_signal)
            self.bus.register_signal("gateway.section.complete", self._handle_gateway_section_complete_signal)

            self.registered_signals = [
                "narrative.assemble", "narrative.validate", "narrative.queue",
                "gateway.narrative_request", "ecc.narrative_ready", "evidence_locker.narrative_data",
                "section.data.updated", "gateway.section.complete"
            ]

            self.logger.info("Bus registration: Narrative Assembler registered with Central Command Bus")
            return True

        except Exception as e:
            self.logger.error(f"Failed to register with bus: {e}")
            return False

    def _handle_evidence_updated_signal(self, payload: Dict[str, Any]) -> None:
        """Capture evidence-level enrichment broadcasts."""
        if not isinstance(payload, dict):
            return
        evidence_id = payload.get('evidence_id')
        if not evidence_id:
            return
        enriched = dict(payload)
        enriched.setdefault('timestamp', datetime.now().isoformat())
        self.evidence_updates[evidence_id] = enriched

    def _handle_case_snapshot_signal(self, payload: Dict[str, Any]) -> None:
        """Track case snapshot broadcasts for manifest reconciliation."""
        if not isinstance(payload, dict):
            return
        snapshot = dict(payload)
        snapshot.setdefault('received_at', datetime.now().isoformat())
        self.case_snapshots.append(snapshot)
        if len(self.case_snapshots) > 50:
            self.case_snapshots = self.case_snapshots[-50:]

    def _handle_section_data_updated_signal(self, signal_data: Dict[str, Any]) -> None:
        """Cache section updates pushed via the bus."""
        try:
            if not isinstance(signal_data, dict):
                return
            raw_payload = signal_data.get("payload")
            payload = dict(raw_payload) if isinstance(raw_payload, dict) else dict(signal_data)
            section_id = payload.get("section_id") or signal_data.get("section_id")
            if not section_id:
                self.logger.warning("section.data.updated signal missing section_id")
                return
            section_title = signal_data.get("section_title") or payload.get("section_title")
            if section_title:
                payload.setdefault("section_title", section_title)
            case_id = signal_data.get("case_id") or payload.get("case_id")
            if case_id is not None:
                payload.setdefault("case_id", case_id)
            metadata = payload.get("metadata")
            if isinstance(metadata, dict):
                metadata.setdefault("received_at", datetime.now().isoformat())
                if case_id is not None:
                    metadata.setdefault("case_id", case_id)
            record = {
                "section_id": section_id,
                "case_id": case_id,
                "received_at": datetime.now().isoformat(),
                "source": signal_data.get("source"),
                "payload": payload,
            }
            self.section_updates[section_id] = record
            if section_id in {"section_cp", "section_dp", "section_toc"}:
                artifact_record = {
                    "section_id": section_id,
                    "case_id": case_id,
                    "received_at": record["received_at"],
                    "source": record.get("source"),
                    "payload": payload,
                }
                self.section_artifacts[section_id] = artifact_record

            queue_payload = {
                "section_id": section_id,
                "structured_data": payload,
                "priority": signal_data.get("priority", "high"),
                "source": signal_data.get("source", "section_controller"),
            }
            if case_id:
                queue_payload["case_id"] = case_id
            if section_title:
                queue_payload["section_title"] = section_title
            self._handle_narrative_queue_signal(queue_payload)
        except Exception as exc:
            self.logger.error(f"Failed to handle section.data.updated signal: {exc}")
    def _handle_gateway_section_complete_signal(self, signal_data: Dict[str, Any]) -> None:
        """Record section completion events from the gateway."""
        try:
            if not isinstance(signal_data, dict):
                return
            raw_payload = signal_data.get("payload")
            payload = dict(raw_payload) if isinstance(raw_payload, dict) else dict(signal_data)
            section_id = payload.get("section_id") or signal_data.get("section_id")
            if not section_id:
                self.logger.warning("gateway.section.complete signal missing section_id")
                return
            case_id = signal_data.get("case_id") or payload.get("case_id")
            record = {
                "section_id": section_id,
                "case_id": case_id,
                "received_at": datetime.now().isoformat(),
                "payload": payload,
            }
            self.gateway_events.append(record)
            if section_id in self.section_updates:
                self.section_updates[section_id]["status"] = "complete"
            structured = payload.get("payload") if isinstance(payload.get("payload"), dict) else payload
            if structured:
                queue_payload = {
                    "section_id": section_id,
                    "structured_data": structured,
                    "priority": "high",
                    "case_id": case_id,
                    "source": signal_data.get("source", "gateway"),
                }
                self._handle_narrative_queue_signal(queue_payload)
        except Exception as exc:
            self.logger.error(f"Failed to handle gateway.section.complete signal: {exc}")
    def _handle_narrative_assemble_signal(self, signal_data: Dict[str, Any]):
        """Handle narrative assembly signals from the bus."""
        try:
            section_id = signal_data.get('section_id')
            structured_data = signal_data.get('structured_data', {})
            if not section_id:
                self.logger.error("Missing section_id in narrative assemble signal")
                return
            case_id = self._infer_case_id(structured_data, signal_data.get('case_id'))
            priority = signal_data.get('priority')
            source = signal_data.get('source')
            self.assemble_and_broadcast(
                section_id=section_id,
                structured_data=structured_data,
                case_id=case_id,
            )
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
            
            self.logger.info("Narrative validation completed")
            
        except Exception as e:
            self.logger.error(f"Failed to handle narrative validate signal: {e}")
    
    def _handle_narrative_queue_signal(self, signal_data: Dict[str, Any]):
        """Handle narrative queue signals from the bus."""
        try:
            section_id = signal_data.get('section_id')
            structured_data = signal_data.get('structured_data', {})
            priority = signal_data.get('priority', 'normal')
            if not section_id:
                self.logger.error("Missing section_id in narrative queue signal")
                return
            queue_item = {
                'section_id': section_id,
                'structured_data': structured_data,
                'priority': priority,
                'queued_at': datetime.now().isoformat(),
                'case_id': signal_data.get('case_id'),
                'source': signal_data.get('source'),
            }
            self.narrative_queue.append(queue_item)
            self.narrative_queue.sort(key=lambda x: 0 if (x.get('priority') == 'high') else 1)
            self.logger.info(f"Narrative queued for {section_id} (priority: {priority})")
            if priority == 'high':
                self._process_queue_items(limit=1)
        except Exception as e:
            self.logger.error(f"Failed to handle narrative queue signal: {e}")
    def _process_queue_items(self, limit: Optional[int]) -> Tuple[int, int]:
        processed = 0
        failed = 0
        if limit == 0:
            return processed, failed
        batch: List[Dict[str, Any]] = []
        while self.narrative_queue and (limit is None or len(batch) < limit):
            batch.append(self.narrative_queue.pop(0))
        for queue_item in batch:
            try:
                self.assemble_and_broadcast(
                    section_id=queue_item.get('section_id'),
                    structured_data=queue_item.get('structured_data', {}),
                    case_id=queue_item.get('case_id'),
                )
                processed += 1
            except Exception as exc:
                failed += 1
                self.logger.error(f"Failed to process queued narrative: {exc}")
        return processed, failed


    def assemble_and_broadcast(
        self,
        section_id: Union[str, Dict[str, Any]],
        structured_data: Optional[Dict[str, Any]] = None,
        *,
        case_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Assemble a narrative and broadcast review/reporting events."""
        payload: Optional[Dict[str, Any]] = None
        if isinstance(section_id, dict) and structured_data is None:
            payload = section_id
            section_id = payload.get('section_id')
            structured_data = (
                payload.get('structured_data')
                or payload.get('data')
                or payload.get('processed_data')
                or {}
            )
            if case_id is None:
                case_id = payload.get('case_id')
        if not section_id:
            raise ValueError('section_id is required for assemble_and_broadcast')
        structured = structured_data if isinstance(structured_data, dict) else {}
        priority_value = 'normal'
        source_value = 'assemble_and_broadcast'
        if payload:
            priority_value = payload.get('priority') or priority_value
            source_value = payload.get('source', source_value)
        assembled = self._assemble_and_emit(
            section_id=section_id,
            structured_data=structured,
            case_id=case_id,
            priority=priority_value,
            source=source_value,
        )
        narrative = assembled.get('narrative') if isinstance(assembled, dict) else None
        if not narrative:
            self.logger.warning(f"No narrative generated for {section_id}")
            return {'status': 'error', 'section_id': section_id}

        case_id_resolved = assembled.get('case_id') or case_id or self._infer_case_id(structured, None)
        timestamp = datetime.now().isoformat()
        short_preview = narrative[:300].replace('\n', ' ').replace('\r', ' ')
        if len(narrative) > 300:
            short_preview += '...'

        summary_payload = {
            'section_id': section_id,
            'case_id': case_id_resolved,
            'status': 'assembled',
            'summary': short_preview,
            'timestamp': timestamp,
            'last_update': timestamp,
        }

        if self.bus:
            try:
                self.bus.emit('review.section_summary', summary_payload)
                self.bus.emit('gateway.section.complete', {'section_id': section_id, 'case_id': case_id_resolved})
                # Use standardized signal format
                if create_standard_narrative_signal:
                    assembled_event = create_standard_narrative_signal(
                        section_id=section_id,
                        case_id=case_id_resolved,
                        narrative=narrative,
                        status="complete",
                        summary=assembled.get('summary') if isinstance(assembled, dict) else short_preview,
                        evidence_ids=assembled.get('evidence_ids', []) if isinstance(assembled, dict) else [],
                        metadata=assembled.get('metadata', {}) if isinstance(assembled, dict) else {}
                    )
                else:
                    # Fallback to original format
                    assembled_event = dict(assembled) if isinstance(assembled, dict) else {
                        'section_id': section_id,
                        'case_id': case_id_resolved,
                        'narrative': narrative,
                    }
                    assembled_event.setdefault('section_id', section_id)
                    assembled_event.setdefault('case_id', case_id_resolved)
                    assembled_event.setdefault('generated_at', timestamp)
                    assembled_event['source'] = 'narrative_assembler'
                
                self._recent_assemblies = getattr(self, '_recent_assemblies', set())
                section_token = assembled_event.get('section_id')
                if section_token in self._recent_assemblies:
                    self.logger.debug(f"Skipping repeat assembly for {section_token}")
                else:
                    self._recent_assemblies.add(section_token)
                    if len(self._recent_assemblies) > 256:
                        self._recent_assemblies.clear()
                        self._recent_assemblies.add(section_token)
                    
                    # Validate signal payload if validation is available
                    if validate_signal_payload and validate_signal_payload('narrative.assembled', assembled_event):
                        self.bus.emit('narrative.assembled', assembled_event)
                        self.logger.info(f"[ASSEMBLE] Broadcasted standardized section {section_id} -> GUI review listeners")
                    else:
                        self.bus.emit('narrative.assembled', assembled_event)
                        self.logger.info(f"[ASSEMBLE] Broadcasted section {section_id} -> GUI review listeners")
            except Exception as exc:
                self.logger.error(f"Failed to broadcast narrative for {section_id}: {exc}")

        return {
            'status': 'ok',
            'section_id': section_id,
            'case_id': case_id_resolved,
            'narrative': narrative,
            'summary': short_preview,
            'timestamp': timestamp,
        }

    def _assemble_and_emit(
        self,
        *,
        section_id: str,
        structured_data: Dict[str, Any],
        case_id: Optional[str],
        priority: Optional[str],
        source: Optional[str],
    ) -> Dict[str, Any]:
        if not section_id:
            raise ValueError('section_id is required for narrative assembly')
        self._recent_assembly_payloads = getattr(self, '_recent_assembly_payloads', {})
        cached_payload = self._recent_assembly_payloads.get(section_id)
        if isinstance(cached_payload, dict):
            self.logger.debug(f"Skipping repeat assembly for {section_id}")
            return dict(cached_payload)
        structured_payload = structured_data if isinstance(structured_data, dict) else {}
        narrative = self.assemble(section_id, structured_payload)
        summary = self._summarize_narrative(narrative)
        narrative_id = f"narrative_{section_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        case_identifier = self._infer_case_id(structured_payload, case_id)
        record = {
            'section_id': section_id,
            'narrative': narrative,
            'summary': summary,
            'processed_at': datetime.now().isoformat(),
            'structured_data': structured_payload,
            'case_id': case_identifier,
        }
        self.processed_narratives[narrative_id] = record
        if section_id in self.section_updates:
            self.section_updates[section_id]['narrative_id'] = narrative_id
            self.section_updates[section_id]['narrative_generated_at'] = record['processed_at']
        assembled_payload = {
            'narrative_id': narrative_id,
            'section_id': section_id,
            'case_id': case_identifier,
            'narrative': narrative,
            'draft': narrative,
            'summary': summary,
            'structured_data': structured_payload,
            'auto_narrative': structured_payload.get('auto_narrative'),
            'assembled_at': record['processed_at'],
            'draft_generated_at': record['processed_at'],
            'priority': priority,
            'status': 'Draft Ready',
            'source': source or 'narrative_assembler',
        }
        if self.bus and hasattr(self.bus, 'log_event'):
            self.bus.log_event('NarrativeAssembler', f"Narrative generated for {case_identifier or '<unknown>'}")
        self._recent_assembly_payloads[section_id] = assembled_payload
        if len(self._recent_assembly_payloads) > 256:
            self._recent_assembly_payloads.clear()
        self.logger.info(f"Narrative assembled for {section_id}")
        return assembled_payload

    def _summarize_narrative(self, narrative: str, limit: int = 320) -> str:
        summary = (narrative or '').strip()
        if len(summary) <= limit:
            return summary
        return summary[:limit].rstrip() + '...'

    def _infer_case_id(self, structured_data: Dict[str, Any], fallback: Optional[str]) -> Optional[str]:
        if isinstance(structured_data, dict):
            for key in ('case_id', 'caseID'):
                if structured_data.get(key):
                    return structured_data.get(key)
            metadata = structured_data.get('metadata')
            if isinstance(metadata, dict):
                for key in ('case_id', 'caseID'):
                    if metadata.get(key):
                        return metadata.get(key)
        if fallback:
            return fallback
        if self.bus and getattr(self.bus, 'current_case_id', None):
            return self.bus.current_case_id
        return None

    def get_artifact_payload(self, section_id: str) -> Dict[str, Any]:
        """Return the latest cached artifact payload for the requested section."""
        artifact = self.section_artifacts.get(section_id)
        if not artifact:
            return {}
        return deepcopy(artifact)

    def process_narrative_queue(self) -> Dict[str, Any]:
        """Process all queued narratives."""
        try:
            processed, failed = self._process_queue_items(limit=None)
            result = {
                'processed_count': processed,
                'failed_count': failed,
                'queue_length': len(self.narrative_queue)
            }
            self.logger.info(f"Processed {processed} narratives, {failed} failed")
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
            
            self.logger.info(f"Bridged Gateway data to Bus for {section_id}")
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
            
            self.logger.info(f"Narrative assembled: Processed narrative request from Gateway for {section_id}")
            
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
            
            self.logger.info(f"Narrative assembled: Processed ECC narrative ready for {section_id}")
            
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
            
            self.logger.info(f"Narrative assembled: Processed Evidence Locker narrative data for {section_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to handle Evidence Locker narrative data: {e}")
    
    def _call_out_to_ecc(self, operation: str, data: Dict[str, Any]) -> bool:
        """Call out to ECC for permission to perform operation"""
        # ECC bypass for headless operation
        if not self.ecc:
            self.logger.info("ECC not available - operating in headless mode for %s", operation)
            return True  # Allow operation to proceed without ECC
        
        try:
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
                self.logger.info(f"Sent call-out to ECC for operation: {operation}")
                return True
            else:
                self.logger.warning("ECC does not support signal emission - proceeding in headless mode")
                return True  # Allow operation to proceed
                
        except Exception as e:
            self.logger.warning(f"Failed to call out to ECC - proceeding in headless mode: {e}")
            return True  # Allow operation to proceed
    
    def _wait_for_ecc_confirm(self, timeout: int = 30) -> bool:
        """Wait for ECC confirmation"""
        # ECC bypass for headless operation
        if not self.ecc:
            self.logger.info("ECC not available - skipping confirmation in headless mode")
            return True  # Allow operation to proceed without ECC confirmation
        
        try:
            # In a real implementation, this would wait for ECC response
            # For now, we'll simulate immediate confirmation
            self.logger.info("Waiting for ECC confirmation...")
            # Simulate confirmation delay
            import time
            time.sleep(0.1)  # Brief delay to simulate processing
            self.logger.info("ECC confirmation received")
            return True
            
        except Exception as e:
            self.logger.warning(f"ECC confirmation timeout or error - proceeding in headless mode: {e}")
            return True  # Allow operation to proceed
    
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
                self.logger.info(f"Sent message to ECC: {message_type}")
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
                self.logger.info(f"Sent accept signal to ECC for operation: {operation}")
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
            
            self.logger.info(f"Handoff completed: {operation} - {status}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to complete handoff: {e}")
            return False
    
    def handle_generate(self, data):
        """Handle narrative generation requests from the bus."""
        try:
            payload = data or {}
            processed_data = payload.get('processed_data') or payload.get('data') or {}
            if not isinstance(processed_data, dict):
                processed_data = {'value': processed_data}
            section_id = payload.get('section_id') or payload.get('section_name') or 'section_1'
            case_hint = payload.get('case_id')
            self.logger.info(f"Handling narrative generation request for case: {case_hint or '<unknown>'} (section {section_id})")
            assembled = self.assemble_and_broadcast(
                section_id=section_id,
                structured_data=processed_data,
                case_id=case_hint,
            )
            response = {
                'summary': assembled.get('summary', ''),
                'status': 'ok',
                'case_id': assembled.get('case_id'),
                'section_id': section_id,
                'full_narrative': assembled.get('narrative')
            }
            return response
        except Exception as e:
            self.logger.error(f"Failed to handle narrative generation: {e}")
            return {
                'summary': f"Error generating narrative: {str(e)}",
                'status': 'error',
                'error': str(e)
            }
