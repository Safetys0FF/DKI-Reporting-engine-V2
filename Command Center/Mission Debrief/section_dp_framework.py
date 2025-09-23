"""Framework template for Section DP (Disclosure & Authenticity Page)."""

from __future__ import annotations

from typing import Any, Dict

from .section_framework_base import (
    CommunicationContract,
    FactGraphContract,
    OrderContract,
    PersistenceContract,
    SectionFramework,
    StageDefinition,
)


class SectionDPFramework(SectionFramework):
    SECTION_ID = "section_dp"
    MAX_RERUNS = 1
    STAGES = (
        StageDefinition(
            name="intake",
            description="Pull inputs, verify cover/conclusion/certification hashes, load templates.",
            checkpoint="sdp_intake_logged",
            guardrails=("order_lock", "async_queue", "persistence_snapshot"),
        ),
        StageDefinition(
            name="compile",
            description="Assemble disclosure/authenticity text, reuse signatures, incorporate conclusion status.",
            checkpoint="sdp_compiled",
            guardrails=("template_hash", "style_lint", "fact_graph_sync"),
        ),
        StageDefinition(
            name="validate",
            description="Ensure disclosures align with certification/conclusion; log compliance flags.",
            checkpoint="sdp_validated",
            guardrails=("compliance_checks", "manual_queue_routes"),
        ),
        StageDefinition(
            name="publish",
            description="Publish payload, emit disclosure-ready signal, record approvals.",
            checkpoint="section_dp_completed",
            guardrails=("durable_persistence", "signal_emission", "immutability"),
        ),
        StageDefinition(
            name="monitor",
            description="Handle revisions while enforcing rerun guardrails.",
            checkpoint="sdp_revision_processed",
            guardrails=("max_reruns", "revision_depth_cap"),
        ),
    )

    COMMUNICATION = CommunicationContract(
        prepare_signal="section_9.completed",
        input_channels=(
            "cover_profile",
            "conclusion_manifest",
            "certification_manifest",
            "disclosure_templates",
            "compliance_flags",
        ),
        output_signal="disclosure_ready",
        revision_signal="disclosure_revision",
    )

    ORDER = OrderContract(\n        execution_after=('gateway', 'section_cp', 'section_toc', 'section_1', 'section_2', 'section_3', 'section_4', 'section_5', 'section_6', 'section_7', 'section_8', 'section_9'),\n        export_after=('section_1', 'section_2', 'section_3', 'section_4', 'section_5', 'section_8', 'section_7', 'section_6', 'section_9', 'section_cp', 'section_toc'),\n        export_priority=120,\n    )\n\n    PERSISTENCE = PersistenceContract(
        persistence_key="section_dp_disclosure",
        durable_paths=("storage/sections/section_dp.json",),
    )

    FACT_GRAPH = FactGraphContract(
        publishes=("disclosure_status",),
        subscribes=("cover_profile", "conclusion_manifest", "certification_manifest"),
    )

    def load_inputs(self) -> Dict[str, Any]:
        """Template hook for retrieving inputs from the gateway."""
        raise NotImplementedError

    def build_payload(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Template hook for constructing the structured payload."""
        raise NotImplementedError

    def publish(self, payload: Dict[str, Any]) -> None:
        """Template hook for persisting state and emitting signals."""
        raise NotImplementedError

