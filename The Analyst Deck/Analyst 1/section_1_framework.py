"""Framework template for Section 1 (Investigation Objectives & Case Profile)."""

from __future__ import annotations

from typing import Any, Dict

from .section_framework_base import (
    CommunicationContract,
    FactGraphContract,
    PersistenceContract,
    SectionFramework,
    StageDefinition,
)


class Section1Framework(SectionFramework):
    SECTION_ID = "section_1_profile"
    MAX_RERUNS = 2
    STAGES = (
        StageDefinition(
            name="acquire",
            description="Load intake docs, register evidence, verify file integrity.",
            checkpoint="s1_profile_acquire",
            guardrails=("order_lock", "async_queue", "persistence_snapshot"),
        ),
        StageDefinition(
            name="extract",
            description="Run strongest-first extraction for IDs, contracts, manifests.",
            checkpoint="s1_profile_extract",
            guardrails=("confidence_threshold", "fallback_logging"),
        ),
        StageDefinition(
            name="normalize",
            description="Apply parsing maps, toolkit rules (alias dedupe, continuity).",
            checkpoint="s1_profile_normalized",
            guardrails=("schema_validation", "fact_graph_sync"),
        ),
        StageDefinition(
            name="validate",
            description="Enforce Cochran/North Star, legal compliance; capture QA issues.",
            checkpoint="s1_profile_validated",
            guardrails=("continuity_checks", "manual_queue_routes"),
        ),
        StageDefinition(
            name="publish",
            description="Publish payload to gateway, emit dependency signals, record approvals.",
            checkpoint="section_1_profile_completed",
            guardrails=("durable_persistence", "signal_emission", "immutability"),
        ),
        StageDefinition(
            name="monitor",
            description="Handle revision requests while enforcing rerun guardrails.",
            checkpoint="s1_profile_revision_processed",
            guardrails=("max_reruns", "revision_depth_cap", "fact_graph_consistency"),
        ),
    )

    COMMUNICATION = CommunicationContract(
        prepare_signal="case_bundle.initialized",
        input_channels=(
            "intake_bundle",
            "extracted_metadata",
            "toolkit_cache",
            "manual_overrides",
        ),
        output_signal="section_1_profile.completed",
        revision_signal="case_metadata_revision",
    )

    ORDER = OrderContract(
        execution_after=('section_cp', 'section_toc'),
        export_after=(),
        export_priority=10,
    )

    def load_inputs(self) -> Dict[str, Any]:
        """Load inputs from Gateway - ENFORCES SECTION-AWARE EXECUTION"""
        try:
            if self.ecc:
                if not self.ecc.can_run(self.SECTION_ID):
                    raise Exception(f"Section {self.SECTION_ID} not active for input loading")
            
            # Get evidence from EvidenceManager handoff
            evidence_data = {}
            try:
                from tools.evidence_manager import EvidenceManager
                # This would be injected by the Gateway/ECC system
                if hasattr(self, 'evidence_manager') and self.evidence_manager:
                    # Get processed evidence for this section
                    processed_evidence = self.evidence_manager.processed_evidence
                    evidence_data = {
                        'processed_evidence': processed_evidence,
                        'evidence_count': len(processed_evidence)
                    }
            except ImportError:
                evidence_data = {"error": "EvidenceManager not available"}
            
            # Get section inputs from Gateway
            gateway_inputs = self.gateway.get_section_inputs("section_1")
            
            # Combine evidence handoff with gateway inputs
            combined_inputs = {
                **gateway_inputs,
                **evidence_data
            }
            
            return combined_inputs
        except Exception as e:
            self.logger.error(f"Failed to load inputs for {self.SECTION_ID}: {e}")
            return {}

    def build_payload(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Build payload with all Section 1 tools - ENFORCES SECTION-AWARE EXECUTION"""
        try:
            if self.ecc:
                if not self.ecc.can_run(self.SECTION_ID):
                    raise Exception(f"Section {self.SECTION_ID} not active for payload building")
            
            sources = [
                context.get("section_payload", {}),
                context.get("case_data", {}),
                context.get("intake_bundle", {}),
                context.get("toolkit_cache", {}),
                context.get("manual_overrides", {}),
            ]

            def first_nonempty(key: str):
                for src in sources:
                    if key in src and src[key]:
                        return src[key]
                return None

            whitelist = [
                "client_name",
                "client_address", 
                "client_phone",
                "contract_date",
                "investigation_goals",
                "subject_primary",
                "subject_secondary",
                "subject_tertiary",
                "subject_employers",
                "subject_employer_address",
                "agency_name",
                "agency_license",
                "assigned_investigator",
                "investigator_license",
                "location_of_investigation",
            ]

            payload = {}
            for key in whitelist:
                payload[key] = first_nonempty(key) or "Unknown"

            profile = context.get("profile_settings", {})
            subcontractor = context.get("subcontractor_agreement", {})
            if subcontractor.get("exists", False):
                payload["assigned_investigator"] = subcontractor.get("assigned_investigator")
                payload["investigator_license"] = subcontractor.get("investigator_license")
            elif profile.get("employee_name") and profile.get("employee_license"):
                payload["assigned_investigator"] = profile["employee_name"]
                payload["investigator_license"] = profile["employee_license"]
            else:
                payload["assigned_investigator"] = "David Krashin"
                payload["investigator_license"] = "0163814-C000480"
            payload["agency_name"] = profile.get("agency_name", "DKI Services LLC")
            payload["agency_license"] = profile.get("agency_license", "0200812-IA000307")

            # Process evidence from EvidenceManager handoff
            processed_evidence = context.get("processed_evidence", {})
            evidence_assets = []
            for evidence_id, evidence_record in processed_evidence.items():
                if evidence_record.get("section_id") == "section_1":
                    evidence_assets.append({
                        "id": evidence_id,
                        "file_path": evidence_record.get("file_path"),
                        "filename": evidence_record.get("filename"),
                        "evidence_type": evidence_record.get("metadata", {}).get("evidence_type", "unknown"),
                        "field_time": evidence_record.get("metadata", {}).get("field_time"),
                        "received_time": evidence_record.get("ingested_at")
                    })

            # Tool integrations - using local tools
            try:
                from tools.northstar_protocol_tool import process_assets as northstar_process
                payload["northstar_result"] = northstar_process(evidence_assets)
            except ImportError:
                payload["northstar_result"] = {"error": "Northstar tool not available"}

            try:
                from tools.cochran_match_tool import verify_identity
                payload["cochran_result"] = verify_identity(
                    context.get("subject", {}), context.get("intake_candidate", {})
                )
            except ImportError:
                payload["cochran_result"] = {"error": "Cochran tool not available"}

            try:
                from tools.reverse_continuity_tool import ReverseContinuityTool
                reverse_tool = ReverseContinuityTool()
                ok, log = reverse_tool.run_validation(
                    context.get("intake_summary", "") or "",
                    context.get("docs", []) or [],
                    context.get("assets_text", []) or [],
                )
                payload["reverse_continuity_result"] = {"ok": bool(ok), "log": log}
            except ImportError:
                payload["reverse_continuity_result"] = {"error": "Reverse continuity tool not available"}

            try:
                from tools.metadata_tool_v_5 import process_zip as metadata_process
                if "metadata_zip" in context:
                    metadata_process(context["metadata_zip"], context.get("metadata_output_dir", "./metadata_out"))
            except ImportError:
                pass  # Metadata processing is optional

            try:
                from tools.mileage_tool_v_2 import audit_mileage
                payload["mileage_audit"] = audit_mileage()
            except ImportError:
                payload["mileage_audit"] = {"error": "Mileage tool not available"}

            return payload

        except Exception as e:
            self.logger.error(f"Failed to build payload for {self.SECTION_ID}: {e}")
            return {"error": str(e)}

    def publish(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Publish results to Gateway and NarrativeAssembler - ENFORCES SECTION-AWARE EXECUTION"""
        try:
            if self.ecc:
                if not self.ecc.can_run(self.SECTION_ID):
                    raise Exception(f"Section {self.SECTION_ID} not active for publishing")
            
            # Generate narrative using NarrativeAssembler
            try:
                from tools.section_1_gateway import Section1Renderer
                renderer = Section1Renderer()
                model = renderer.render_model(section_payload=payload, case_sources={})
                
                section_text = "\n".join(
                    f"{blk.get('label', blk.get('text'))}: {blk['value']}"
                    if blk["type"] == "field" else str(blk["text"])
                    for blk in model["render_tree"]
                )
                narrative = section_text
            except ImportError:
                narrative = f"Section 1 Profile: {payload.get('client_name', 'Unknown Client')}"

            # Publish to Gateway
            result = {
                "payload": payload,
                "manifest": payload,
                "narrative": narrative,
                "status": "completed"
            }
            
            self.gateway.publish_section_result("section_1", result)
            self.gateway.emit("case_metadata_ready", payload)

            return {"status": "published", "narrative": narrative, "manifest": payload}

        except Exception as e:
            self.logger.error(f"Failed to publish for {self.SECTION_ID}: {e}")
            return {"error": str(e)}






