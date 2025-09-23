"""Framework implementation for Section DP (Disclosure & Authenticity Page)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from section_renderers.section_dp_renderer import SectionDPRenderer

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class StageDefinition:
    name: str
    description: str
    checkpoint: str
    guardrails: Tuple[str, ...] = field(default_factory=tuple)
    inputs: Tuple[str, ...] = field(default_factory=tuple)
    outputs: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CommunicationContract:
    prepare_signal: str
    input_channels: Tuple[str, ...]
    output_signal: str
    revision_signal: str


@dataclass(frozen=True)
class PersistenceContract:
    persistence_key: str
    durable_paths: Tuple[str, ...]


@dataclass(frozen=True)
class FactGraphContract:
    publishes: Tuple[str, ...]
    subscribes: Tuple[str, ...]


@dataclass(frozen=True)
class OrderContract:
    execution_after: Tuple[str, ...] = field(default_factory=tuple)
    export_after: Tuple[str, ...] = field(default_factory=tuple)
    export_priority: int = 0


class SectionFramework:
    SECTION_ID: str = ""
    MAX_RERUNS: int = 3
    STAGES: Tuple[StageDefinition, ...] = ()
    COMMUNICATION: Optional[CommunicationContract] = None
    PERSISTENCE: Optional[PersistenceContract] = None
    FACT_GRAPH: Optional[FactGraphContract] = None
    ORDER: Optional[OrderContract] = None
    IMMUTABILITY_FLAG: str = "signed_off"

    def __init__(
        self,
        gateway: Any,
        ecc: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.gateway = gateway
        self.ecc = ecc
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.revision_depth: int = 0
        self.signed_payload_id: Optional[str] = None

    def _guard_execution(self, operation: str) -> None:
        if self.ecc and not self.ecc.can_run(self.SECTION_ID):
            raise RuntimeError(f"{self.SECTION_ID} blocked for {operation} by ECC")

    def handle_revision(self, reason: str, context: Dict[str, Any]) -> None:
        if self.revision_depth >= self.MAX_RERUNS:
            raise RuntimeError(
                f"{self.SECTION_ID} exceeded max reruns ({self.MAX_RERUNS})"
            )
        self.revision_depth += 1
        self.logger.info("Revision %s triggered for %s", self.revision_depth, self.SECTION_ID)

    def lock_payload(self, payload_id: str) -> None:
        self.signed_payload_id = payload_id

    @classmethod
    def execution_dependencies(cls) -> Tuple[str, ...]:
        return cls.ORDER.execution_after if cls.ORDER else tuple()

    @classmethod
    def export_dependencies(cls) -> Tuple[str, ...]:
        return cls.ORDER.export_after if cls.ORDER else tuple()

    @classmethod
    def export_priority(cls) -> int:
        return cls.ORDER.export_priority if cls.ORDER else 0

    def load_inputs(self) -> Dict[str, Any]:
        raise NotImplementedError

    def build_payload(self, context: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def publish(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError


class SectionDPFramework(SectionFramework):
    SECTION_ID = "section_dp"
    MAX_RERUNS = 1
    STAGES = (
        StageDefinition(
            name="intake",
            description="Pull inputs, verify cover/conclusion/certification hashes, load templates.",
            checkpoint="sdp_intake_logged",
            guardrails=("order_lock", "async_queue", "persistence_snapshot"),
            inputs=("cover_profile", "conclusion_manifest", "certification_manifest", "disclosure_templates", "compliance_flags", "toolkit_results", "case_metadata"),
            outputs=("intake_context",),
        ),
        StageDefinition(
            name="compile",
            description="Assemble disclosure/authenticity text, reuse signatures, incorporate conclusion status.",
            checkpoint="sdp_compiled",
            guardrails=("template_hash", "style_lint", "fact_graph_sync"),
            inputs=("intake_context",),
            outputs=("compiled_payload",),
        ),
        StageDefinition(
            name="validate",
            description="Ensure disclosures align with certification/conclusion; log compliance flags.",
            checkpoint="sdp_validated",
            guardrails=("compliance_checks", "manual_queue_routes"),
            inputs=("compiled_payload",),
            outputs=("validated_payload",),
        ),
        StageDefinition(
            name="publish",
            description="Publish payload, emit disclosure-ready signal, record approvals.",
            checkpoint="section_dp_completed",
            guardrails=("durable_persistence", "signal_emission", "immutability"),
            inputs=("validated_payload",),
            outputs=("gateway_handoff",),
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
            "toolkit_results",
            "case_metadata",
            "previous_sections",
        ),
        output_signal="disclosure_ready",
        revision_signal="disclosure_revision",
    )

    ORDER = OrderContract(
        execution_after=("section_9",),
        export_after=("section_9",),
        export_priority=120,
    )

    PERSISTENCE = PersistenceContract(
        persistence_key="section_dp_disclosure",
        durable_paths=("storage/sections/section_dp.json",),
    )

    FACT_GRAPH = FactGraphContract(
        publishes=("disclosure_status",),
        subscribes=("cover_profile", "conclusion_manifest", "certification_manifest"),
    )

    def __init__(
        self,
        gateway: Any,
        ecc: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        super().__init__(gateway=gateway, ecc=ecc, logger=logger)
        self._last_context: Dict[str, Any] = {}

    def load_inputs(self) -> Dict[str, Any]:
        try:
            self._guard_execution("input loading")
            bundle = self.gateway.get_section_inputs("section_dp") if self.gateway else {}
            context = {
                "raw_inputs": bundle,
                "cover_profile": bundle.get("cover_profile", {}) or {},
                "conclusion_manifest": bundle.get("conclusion_manifest", {}) or {},
                "certification_manifest": bundle.get("certification_manifest", {}) or {},
                "disclosure_templates": bundle.get("disclosure_templates", {}) or {},
                "compliance_flags": bundle.get("compliance_flags", []) or [],
                "toolkit_results": bundle.get("toolkit_results", {}) or {},
                "case_metadata": bundle.get("case_metadata", {}) or {},
                "previous_sections": bundle.get("previous_sections", {}) or {},
            }
            context["report_type"] = (
                context["case_metadata"].get("report_type")
                or context["conclusion_manifest"].get("report_type")
                or "surveillance"
            ).lower()
            context["basic_stats"] = {
                "compliance_flags": len(context["compliance_flags"]),
                "templates_loaded": len(context["disclosure_templates"]),
            }
            self.logger.debug("Section DP inputs loaded: %s", context["basic_stats"])
            self._last_context = context
            return context
        except Exception as exc:
            self.logger.exception("Failed to load inputs for %s: %s", self.SECTION_ID, exc)
            return {}

    def build_payload(self, context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self._guard_execution("payload building")
            self._last_context = context
            cover_profile = context.get("cover_profile", {}) or {}
            conclusion_manifest = context.get("conclusion_manifest", {}) or {}
            certification_manifest = context.get("certification_manifest", {}) or {}
            case_metadata = context.get("case_metadata", {}) or {}
            toolkit_results = context.get("toolkit_results", {}) or {}
            previous_sections = self._merge_previous_sections(context.get("previous_sections", {}) or {}, cover_profile, conclusion_manifest, certification_manifest)

            case_data = self._assemble_case_data(case_metadata, conclusion_manifest, certification_manifest, cover_profile)
            metadata = self._assemble_metadata(conclusion_manifest, certification_manifest)
            qa_flags = self._collect_flags(context.get("compliance_flags", []), toolkit_results)

            payload = {
                "report_type": case_data.get("report_type", "Investigative"),
                "case_data": case_data,
                "previous_sections": previous_sections,
                "toolkit_results": toolkit_results,
                "metadata": metadata,
                "compliance_flags": context.get("compliance_flags", []),
                "disclosure_templates": context.get("disclosure_templates", {}),
                "cover_profile": cover_profile,
                "conclusion_manifest": conclusion_manifest,
                "certification_manifest": certification_manifest,
                "qa_flags": qa_flags,
            }
            return payload
        except Exception as exc:
            self.logger.exception("Failed to build payload for %s: %s", self.SECTION_ID, exc)
            return {"error": str(exc)}

    def publish(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self._guard_execution("publishing")
            renderer = SectionDPRenderer()
            model = renderer.render_model(payload, self._last_context)

            narrative_lines: List[str] = []
            for block in model.get("render_tree", []):
                text = str(block.get("text", "") or block.get("value", "")).strip()
                if text:
                    narrative_lines.append(text)
            narrative = "\n".join(narrative_lines)

            result = {
                "payload": payload,
                "manifest": model.get("manifest", {}),
                "render_tree": model.get("render_tree", []),
                "narrative": narrative,
                "status": "completed",
            }

            if self.gateway:
                try:
                    self.gateway.publish_section_result("section_dp", result)
                    self.gateway.emit(self.COMMUNICATION.output_signal, result)
                except Exception as emit_exc:
                    self.logger.warning("Gateway publication emitted an error: %s", emit_exc)

            return {
                "status": "published",
                "narrative": narrative,
                "manifest": model.get("manifest", {}),
            }
        except Exception as exc:
            self.logger.exception("Failed to publish for %s: %s", self.SECTION_ID, exc)
            return {"error": str(exc)}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _merge_previous_sections(
        self,
        previous_sections: Dict[str, Any],
        cover_profile: Dict[str, Any],
        conclusion_manifest: Dict[str, Any],
        certification_manifest: Dict[str, Any],
    ) -> Dict[str, Any]:
        merged = dict(previous_sections)
        if cover_profile:
            merged.setdefault(
                "section_cp",
                {
                    "manifest": {
                        "cover_profile": cover_profile,
                    }
                },
            )
        if conclusion_manifest:
            merged.setdefault("section_9", {"manifest": conclusion_manifest})
        if certification_manifest:
            merged.setdefault("section_certification", {"manifest": certification_manifest})
        return merged

    def _assemble_case_data(
        self,
        case_metadata: Dict[str, Any],
        conclusion_manifest: Dict[str, Any],
        certification_manifest: Dict[str, Any],
        cover_profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        sources: List[Dict[str, Any]] = [
            case_metadata,
            conclusion_manifest.get("case_data", {}) if isinstance(conclusion_manifest.get("case_data"), dict) else {},
            certification_manifest.get("case_data", {}) if isinstance(certification_manifest.get("case_data"), dict) else {},
        ]

        def pick(key: str, default: Optional[str] = None) -> Optional[str]:
            return self._first_nonempty(*(src.get(key) for src in sources if isinstance(src, dict)), default=default)

        report_type = pick("report_type", "Surveillance")
        case_id = pick("case_id", "UNKNOWN")
        client_name = pick("client_name", cover_profile.get("client_name") or "Client")
        investigator = pick("assigned_investigator", cover_profile.get("investigator_name"))

        case_data = {
            "case_id": case_id,
            "client_name": client_name,
            "client_phone": pick("client_phone", cover_profile.get("phone")),
            "client_email": pick("client_email", cover_profile.get("email")),
            "report_type": (report_type.title() if isinstance(report_type, str) else "Surveillance"),
            "assigned_investigator": investigator,
            "investigator_license": pick("investigator_license", cover_profile.get("investigator_license")),
            "investigator_title": pick("investigator_title", cover_profile.get("investigator_title")),
            "agency_name": pick("agency_name", cover_profile.get("agency_name")),
            "agency_license": pick("agency_license", cover_profile.get("agency_license")),
            "agency_phone": cover_profile.get("phone") or pick("agency_phone"),
            "agency_email": cover_profile.get("email") or pick("agency_email"),
            "case_summary": pick("case_summary"),
        }
        return case_data

    def _assemble_metadata(
        self,
        conclusion_manifest: Dict[str, Any],
        certification_manifest: Dict[str, Any],
    ) -> Dict[str, Any]:
        finalized = conclusion_manifest.get("finalized_timestamp") or certification_manifest.get("finalized_timestamp")
        processed = conclusion_manifest.get("generated_on") or certification_manifest.get("generated_on")
        return {
            "finalized_timestamp": finalized or processed or datetime.utcnow().isoformat(),
            "conclusion_manifest_id": conclusion_manifest.get("manifest_id"),
            "certification_manifest_id": certification_manifest.get("manifest_id"),
        }

    def _collect_flags(self, compliance_flags: Sequence[str], toolkit_results: Dict[str, Any]) -> List[str]:
        flags = list(compliance_flags or [])
        for tool_name, result in toolkit_results.items():
            if not isinstance(result, dict):
                continue
            status = str(result.get("status", "")).lower()
            if status and status not in {"success", "ok", "pass", "completed"}:
                summary = result.get("summary") or result.get("message") or status
                flags.append(f"{tool_name}:{summary}")
        return flags

    def _first_nonempty(self, *candidates: Optional[str], default: Optional[str] = None) -> Optional[str]:
        for candidate in candidates:
            if candidate is None:
                continue
            text = str(candidate).strip()
            if text:
                return text
        return default


__all__ = [
    "SectionDPFramework",
    "StageDefinition",
    "CommunicationContract",
    "FactGraphContract",
    "PersistenceContract",
    "OrderContract",
]
