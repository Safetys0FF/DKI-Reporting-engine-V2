"""Framework implementation for Section CP (Cover Page)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from section_renderers.section_cp_renderer import SectionCPRenderer

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
        self.queue_client: Optional[Any] = None
        self.storage: Optional[Any] = None
        self.fact_graph_client: Optional[Any] = None
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


class SectionCPFramework(SectionFramework):
    SECTION_ID = "section_cp"
    MAX_RERUNS = 2
    STAGES = (
        StageDefinition(
            name="intake",
            description="Pull gateway bundle, verify Section 1 signature, load branding assets.",
            checkpoint="cp_intake_logged",
            guardrails=("order_lock", "async_queue", "persistence_snapshot"),
            inputs=("case_metadata", "client_profile", "agency_profile", "branding_assets", "toolkit_results"),
            outputs=("intake_context",),
        ),
        StageDefinition(
            name="validate",
            description="Confirm investigator/license numbers, client data, contract IDs against toolkit cache.",
            checkpoint="cp_credentials_validated",
            guardrails=("credential_enforcement", "fact_graph_sync"),
            inputs=("intake_context",),
            outputs=("validated_profile",),
        ),
        StageDefinition(
            name="render",
            description="Build render tree with fixed layout, inject placeholders only when flagged.",
            checkpoint="cp_render_complete",
            guardrails=("template_hash", "style_lint", "immutability_precheck"),
            inputs=("validated_profile",),
            outputs=("render_payload",),
        ),
        StageDefinition(
            name="qa",
            description="Run compliance checks (branding lock, contact channels, signature presence).",
            checkpoint="cp_qc_result",
            guardrails=("branding_lock", "signature_required"),
            inputs=("render_payload",),
            outputs=("qa_payload",),
        ),
        StageDefinition(
            name="publish",
            description="Persist manifest, emit readiness signal, record approvals.",
            checkpoint="section_cp_completed",
            guardrails=("durable_persistence", "signal_emission"),
            inputs=("qa_payload",),
            outputs=("gateway_handoff",),
        ),
        StageDefinition(
            name="monitor",
            description="Handle revision requests via gateway while enforcing rerun guardrails.",
            checkpoint="cp_revision_processed",
            guardrails=("max_reruns", "revision_depth_cap", "fact_graph_consistency"),
        ),
    )

    COMMUNICATION = CommunicationContract(
        prepare_signal="section_1_profile.completed",
        input_channels=(
            "case_metadata",
            "client_profile",
            "agency_profile",
            "branding_assets",
            "toolkit_results",
            "section_outputs",
            "previous_sections",
        ),
        output_signal="section_cp.completed",
        revision_signal="cover_profile_revision",
    )

    ORDER = OrderContract(
        execution_after=(),
        export_after=(),
        export_priority=5,
    )

    PERSISTENCE = PersistenceContract(
        persistence_key="section_cp_manifest",
        durable_paths=("storage/sections/section_cp.json",),
    )

    FACT_GRAPH = FactGraphContract(
        publishes=("cover_profile",),
        subscribes=(),
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
            bundle = self.gateway.get_section_inputs("section_cp") if self.gateway else {}
            context = {
                "raw_inputs": bundle,
                "case_metadata": bundle.get("case_metadata", {}) or {},
                "client_profile": bundle.get("client_profile", {}) or {},
                "agency_profile": bundle.get("agency_profile", {}) or {},
                "branding_assets": bundle.get("branding_assets", {}) or {},
                "toolkit_results": bundle.get("toolkit_results", {}) or {},
                "section_outputs": bundle.get("section_outputs", {}) or {},
                "previous_sections": bundle.get("previous_sections", {}) or {},
            }
            report_type = (
                context["case_metadata"].get("report_type")
                or context["case_metadata"].get("case_type")
                or "surveillance"
            )
            context["report_type"] = str(report_type).lower()
            profile_sources = [
                context["client_profile"],
                context["agency_profile"],
                context["branding_assets"],
                context["toolkit_results"].get("client_profile", {}),
            ]
            context["basic_stats"] = {
                "has_logo": bool(self._first_nonempty(
                    *(src.get("cover_logo_path") for src in profile_sources if isinstance(src, dict))
                    or []
                )),
                "has_signature": bool(self._first_nonempty(
                    *(src.get("signature_path") for src in profile_sources if isinstance(src, dict))
                    or []
                )),
            }
            self.logger.debug("Section CP inputs loaded: %s", context["basic_stats"])
            self._last_context = context
            return context
        except Exception as exc:
            self.logger.exception("Failed to load inputs for %s: %s", self.SECTION_ID, exc)
            return self._augment_with_bus_context({})

    def build_payload(self, context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self._guard_execution("payload building")
            self._last_context = context
            case_metadata = context.get("case_metadata", {}) or {}
            toolkit_results = context.get("toolkit_results", {}) or {}
            client_profile = context.get("client_profile", {}) or {}
            agency_profile = context.get("agency_profile", {}) or {}
            branding_assets = context.get("branding_assets", {}) or {}
            toolkit_profile = toolkit_results.get("client_profile") if isinstance(toolkit_results.get("client_profile"), dict) else {}

            cover_profile = self._assemble_cover_profile(
                agency_profile,
                client_profile,
                branding_assets,
                toolkit_profile,
            )
            case_data = self._assemble_case_data(case_metadata, toolkit_results, cover_profile)
            qa_flags = self._collect_toolkit_flags(toolkit_results)
            metadata = {
                "generated_on": datetime.utcnow().isoformat(),
                "report_type": case_data.get("report_type"),
                "profile_sources": cover_profile.get("source_trace", []),
            }

            payload = {
                "report_type": case_data.get("report_type", "Investigative"),
                "case_data": case_data,
                "client_profile": cover_profile,
                "cover_logo_path": cover_profile.get("cover_logo_path") or cover_profile.get("logo_path"),
                "toolkit_results": toolkit_results,
                "qa_flags": qa_flags,
                "metadata": metadata,
                "previous_sections": context.get("previous_sections", {}),
            }
            return payload
        except Exception as exc:
            self.logger.exception("Failed to build payload for %s: %s", self.SECTION_ID, exc)
            return {"error": str(exc)}

    def publish(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self._guard_execution("publishing")
            renderer = SectionCPRenderer()
            case_sources = self._build_renderer_sources(self._last_context, payload)
            model = renderer.render_model(payload, case_sources)

            narrative_parts: List[str] = []
            for block in model.get("render_tree", []):
                if block.get("type") == "field":
                    label = block.get("label", "")
                    value = block.get("value", "")
                    narrative_parts.append(f"{label}: {value}".strip())
                elif block.get("type") in {"title", "header", "paragraph"}:
                    text = str(block.get("text", "")).strip()
                    if text:
                        narrative_parts.append(text)
            narrative = "\n".join(narrative_parts)

            result = {
                "payload": payload,
                "manifest": model.get("manifest", {}),
                "render_tree": model.get("render_tree", []),
                "narrative": narrative,
                "status": "completed",
            }

            if self.gateway:
                try:
                    self.gateway.publish_section_result("section_cp", result)
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
    def _assemble_cover_profile(
        self,
        agency_profile: Dict[str, Any],
        client_profile: Dict[str, Any],
        branding_assets: Dict[str, Any],
        toolkit_profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        merged: Dict[str, Any] = {}
        source_trace: List[str] = []

        for label, profile in (
            ("toolkit", toolkit_profile),
            ("client_profile", client_profile),
            ("agency_profile", agency_profile),
            ("branding_assets", branding_assets),
        ):
            if not isinstance(profile, dict):
                continue
            for key, value in profile.items():
                if value in (None, "", []) and key in merged:
                    continue
                merged[key] = value
            if profile:
                source_trace.append(label)

        merged.setdefault("cover_logo_path", merged.get("logo_path") or branding_assets.get("cover_logo"))
        merged.setdefault("signature_path", branding_assets.get("signature") or client_profile.get("signature_path"))
        merged.setdefault("agency_name", agency_profile.get("agency_name") or client_profile.get("agency_name"))
        merged.setdefault("agency_license", agency_profile.get("agency_license") or client_profile.get("agency_license"))
        merged.setdefault("phone", merged.get("phone") or agency_profile.get("phone") or client_profile.get("phone"))
        merged.setdefault("email", merged.get("email") or agency_profile.get("email") or client_profile.get("email"))
        merged["source_trace"] = source_trace
        return merged

    def _assemble_case_data(
        self,
        case_metadata: Dict[str, Any],
        toolkit_results: Dict[str, Any],
        cover_profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        sources: List[Dict[str, Any]] = [
            case_metadata,
            toolkit_results.get("case_metadata", {}) if isinstance(toolkit_results.get("case_metadata"), dict) else {},
            toolkit_results.get("normalized_case", {}) if isinstance(toolkit_results.get("normalized_case"), dict) else {},
        ]

        def pick(key: str, default: Optional[str] = None) -> Optional[str]:
            return self._first_nonempty(*(src.get(key) for src in sources if isinstance(src, dict)), default=default)

        report_type = pick("report_type", "Surveillance") or pick("case_type", "Surveillance")
        case_id = pick("case_id", "UNKNOWN")
        contract_date = pick("contract_date")

        case_data = {
            "case_id": case_id,
            "client_name": pick("client_name", cover_profile.get("client_name") or "Client"),
            "client_phone": pick("client_phone", cover_profile.get("phone")),
            "client_email": pick("client_email", cover_profile.get("email")),
            "client_address": pick("client_address"),
            "contract_date": contract_date,
            "report_type": report_type.title() if isinstance(report_type, str) else "Surveillance",
            "assigned_investigator": pick("assigned_investigator", cover_profile.get("investigator_name")),
            "investigator_license": pick("investigator_license", cover_profile.get("investigator_license")),
            "investigator_title": pick("investigator_title", cover_profile.get("investigator_title")),
            "agency_name": pick("agency_name", cover_profile.get("agency_name")),
            "agency_license": pick("agency_license", cover_profile.get("agency_license")),
            "agency_phone": cover_profile.get("phone") or pick("agency_phone"),
            "agency_email": cover_profile.get("email") or pick("agency_email"),
            "case_summary": pick("case_summary"),
        }
        return case_data

    def _collect_toolkit_flags(self, toolkit_results: Dict[str, Any]) -> List[str]:
        flags: List[str] = []
        for tool_name, result in toolkit_results.items():
            if not isinstance(result, dict):
                continue
            status = str(result.get("status", "")).lower()
            if status and status not in {"success", "ok", "pass", "completed"}:
                summary = result.get("summary") or result.get("message") or status
                flags.append(f"{tool_name}:{summary}")
        return flags

    def _build_renderer_sources(
        self,
        context: Dict[str, Any],
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "case_metadata": context.get("case_metadata", {}),
            "toolkit_results": context.get("toolkit_results", {}),
            "previous_sections": context.get("previous_sections", {}),
            "payload_metadata": payload.get("metadata", {}),
        }

    def _first_nonempty(self, *candidates: Optional[str], default: Optional[str] = None) -> Optional[str]:
        for candidate in candidates:
            if candidate is None:
                continue
            text = str(candidate).strip()
            if text:
                return text
        return default


__all__ = [
    "SectionCPFramework",
    "StageDefinition",
    "CommunicationContract",
    "FactGraphContract",
    "PersistenceContract",
    "OrderContract",
]
