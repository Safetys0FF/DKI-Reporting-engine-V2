"""Framework implementation for Section TOC (Table of Contents)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from section_renderers.section_toc_renderer import SectionTOCRenderer

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
class OrderContract:
    execution_after: Tuple[str, ...] = field(default_factory=tuple)
    export_after: Tuple[str, ...] = field(default_factory=tuple)
    export_priority: int = 0


SECTION_TITLES = {
    "investigative": {
        "section_cp": "Cover Page",
        "section_toc": "Table of Contents",
        "section_1": "Investigation Objective",
        "section_2": "Preliminary Case Review",
        "section_3": "Investigative Details",
        "section_4": "Review of Surveillance Sessions",
        "section_5": "Review of Supporting Documents",
        "section_6": "Billing Summary",
        "section_7": "Conclusion",
        "section_8": "Investigation Evidence Review",
        "section_9": "Certification",
        "section_dp": "Disclosure Page",
    },
    "surveillance": {
        "section_cp": "Cover Page",
        "section_toc": "Table of Contents",
        "section_1": "Surveillance Objectives",
        "section_2": "Pre-Surveillance Planning",
        "section_3": "Investigation Details",
        "section_4": "Review of Surveillance Sessions",
        "section_5": "Review of Supporting Documents",
        "section_6": "Billing Summary",
        "section_7": "Conclusion",
        "section_8": "Investigation Evidence Review",
        "section_dp": "Disclosure Page",
    },
    "hybrid": {
        "section_cp": "Cover Page",
        "section_toc": "Table of Contents",
        "section_1": "Investigation Objective",
        "section_2": "Preliminary Case Review",
        "section_3": "Investigative Details",
        "section_4": "Review of Surveillance Sessions",
        "section_5": "Review of Supporting Documents",
        "section_6": "Billing Summary",
        "section_7": "Conclusion",
        "section_8": "Investigation Evidence Review",
        "section_dp": "Disclosure Page",
    },
}


class SectionFramework:
    SECTION_ID: str = ""
    MAX_RERUNS: int = 3
    STAGES: Tuple[StageDefinition, ...] = ()
    COMMUNICATION: Optional[CommunicationContract] = None
    PERSISTENCE: Optional[PersistenceContract] = None
    ORDER: Optional[OrderContract] = None

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


class SectionTOCFramework(SectionFramework):
    SECTION_ID = "section_toc"
    MAX_RERUNS = 1
    STAGES = (
        StageDefinition(
            name="intake",
            description="Pull cover profile and section manifest summaries for TOC generation.",
            checkpoint="toc_intake_logged",
            guardrails=("order_lock", "async_queue", "persistence_snapshot"),
            inputs=("case_metadata", "section_manifest_summaries", "previous_sections", "report_sections"),
            outputs=("intake_context",),
        ),
        StageDefinition(
            name="compile",
            description="Assemble TOC entries using approved section payload hashes and titles.",
            checkpoint="toc_compiled",
            guardrails=("immutability_checks", "schema_validation"),
            inputs=("intake_context",),
            outputs=("compiled_entries",),
        ),
        StageDefinition(
            name="publish",
            description="Persist TOC payload and emit readiness signal.",
            checkpoint="section_toc_completed",
            guardrails=("durable_persistence", "signal_emission", "immutability"),
            inputs=("compiled_entries",),
            outputs=("gateway_handoff",),
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
            "case_metadata",
            "section_manifest_summaries",
            "report_sections",
            "previous_sections",
            "toolkit_results",
        ),
        output_signal="section_toc.completed",
        revision_signal="toc_revision",
    )

    PERSISTENCE = PersistenceContract(
        persistence_key="section_toc_manifest",
        durable_paths=("storage/sections/section_toc.json",),
    )

    ORDER = OrderContract(
        execution_after=("section_cp",),
        export_after=("section_cp",),
        export_priority=8,
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
            bundle = self.gateway.get_section_inputs("section_toc") if self.gateway else {}
            context = {
                "raw_inputs": bundle,
                "case_metadata": bundle.get("case_metadata", {}) or {},
                "section_manifest_summaries": bundle.get("section_manifest_summaries", {}) or {},
                "report_sections": bundle.get("report_sections", []) or [],
                "previous_sections": bundle.get("previous_sections", {}) or {},
                "toolkit_results": bundle.get("toolkit_results", {}) or {},
            }
            report_type = (
                context["case_metadata"].get("report_type")
                or context["case_metadata"].get("case_type")
                or "surveillance"
            )
            context["report_type"] = str(report_type).lower()
            context["basic_stats"] = {
                "declared_sections": len(context["report_sections"]),
                "completed_sections": sum(
                    1 for summary in context["section_manifest_summaries"].values()
                    if isinstance(summary, dict) and summary.get("status") in {"completed", "ready"}
                ),
            }
            self.logger.debug("Section TOC inputs loaded: %s", context["basic_stats"])
            self._last_context = context
            return context
        except Exception as exc:
            self.logger.exception("Failed to load inputs for %s: %s", self.SECTION_ID, exc)
            return {}

    def build_payload(self, context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self._guard_execution("payload building")
            self._last_context = context
            case_metadata = context.get("case_metadata", {}) or {}
            summaries = context.get("section_manifest_summaries", {}) or {}
            report_sections = context.get("report_sections", []) or []
            previous_sections = context.get("previous_sections", {}) or {}
            toolkit_results = context.get("toolkit_results", {}) or {}

            report_type = (case_metadata.get("report_type") or case_metadata.get("case_type") or "surveillance").lower()
            ordered_sections = self._determine_section_order(report_type, report_sections)

            start_page = 3
            current_page = start_page
            entries: List[Dict[str, Any]] = []
            qa_flags: List[str] = []

            for section_id in ordered_sections:
                summary = summaries.get(section_id) if isinstance(summaries, dict) else None
                completed = bool(self._section_available(section_id, summary, previous_sections))
                title = self._resolve_title(section_id, report_type, summary)
                page_estimate = self._page_estimate(summary)

                entry = {
                    "section_id": section_id,
                    "title": title,
                    "page": current_page,
                    "page_estimate": page_estimate,
                    "available": completed,
                }
                entries.append(entry)
                if not completed:
                    qa_flags.append(f"missing:{section_id}")
                current_page += page_estimate

            metadata = {
                "generated_on": datetime.utcnow().isoformat(),
                "section_count": len(entries),
                "report_type": report_type,
            }

            payload = {
                "report_type": report_type.title(),
                "entries": entries,
                "start_page": start_page,
                "qa_flags": qa_flags,
                "metadata": metadata,
                "toolkit_results": toolkit_results,
            }
            return payload
        except Exception as exc:
            self.logger.exception("Failed to build payload for %s: %s", self.SECTION_ID, exc)
            return {"error": str(exc)}

    def publish(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self._guard_execution("publishing")
            renderer = SectionTOCRenderer()
            model = renderer.render_model(payload, self._last_context)

            narrative_lines: List[str] = []
            for block in model.get("render_tree", []):
                text = str(block.get("text", "")).strip()
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
                    self.gateway.publish_section_result("section_toc", result)
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
    def _determine_section_order(self, report_type: str, declared: Sequence[str]) -> List[str]:
        if declared:
            return list(dict.fromkeys(declared))
        mapping = SECTION_TITLES.get(report_type.lower()) or SECTION_TITLES["surveillance"]
        return list(mapping.keys())

    def _resolve_title(self, section_id: str, report_type: str, summary: Optional[Dict[str, Any]]) -> str:
        title = None
        if isinstance(summary, dict):
            title = summary.get("title") or summary.get("heading")
        if not title:
            mapping = SECTION_TITLES.get(report_type.lower()) or SECTION_TITLES["surveillance"]
            title = mapping.get(section_id)
        if not title:
            title = section_id.replace("_", " ").title()
        return title

    def _section_available(
        self,
        section_id: str,
        summary: Optional[Dict[str, Any]],
        previous_sections: Dict[str, Any],
    ) -> bool:
        if isinstance(summary, dict) and summary.get("status") in {"completed", "ready"}:
            return True
        if previous_sections and section_id in previous_sections:
            return True
        return False

    def _page_estimate(self, summary: Optional[Dict[str, Any]]) -> int:
        if isinstance(summary, dict):
            candidates = [
                summary.get("page_estimate"),
                summary.get("estimated_pages"),
                summary.get("page_count"),
                summary.get("pages"),
            ]
            for candidate in candidates:
                try:
                    value = int(candidate)
                    if value > 0:
                        return value
                except (TypeError, ValueError):
                    continue
        return 1


__all__ = [
    "SectionTOCFramework",
    "StageDefinition",
    "CommunicationContract",
    "PersistenceContract",
    "OrderContract",
]
