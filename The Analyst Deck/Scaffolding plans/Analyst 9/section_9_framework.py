"""Framework template for Section 9 (Certification & Disclaimers)."""

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
            
            return self._augment_with_bus_context(combined_inputs)
        except Exception as e:
            self.logger.error(f"Failed to load inputs for {self.SECTION_ID}: {e}")
            return self._augment_with_bus_context({})

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







