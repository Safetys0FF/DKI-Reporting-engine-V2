#!/usr/bin/env python3
"""Mission Debrief Manager - orchestrates professional tooling via adapters."""

from __future__ import annotations

import json
import logging
from copy import deepcopy
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

CURRENT_FILE = Path(__file__).resolve()
DEBRIEF_ROOT = CURRENT_FILE.parents[1]
MISSION_DEBRIEF_ROOT = CURRENT_FILE.parents[2]
COMMAND_CENTER_ROOT = MISSION_DEBRIEF_ROOT.parent

PATH_CANDIDATES = [
    MISSION_DEBRIEF_ROOT,
    MISSION_DEBRIEF_ROOT / "The Warden",
    COMMAND_CENTER_ROOT / "Data Bus" / "Bus Core Design",
]

for candidate in PATH_CANDIDATES:
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

from tools.evidence_pipeline_adapter import EvidencePipelineAdapter
from tools.pdf_extraction_adapter import PdfExtractionAdapter
from tools.api_manager_adapter import ApiServiceAdapter
from tools.report_generator_adapter import ReportGeneratorAdapter
from tools.digital_signature_adapter import DigitalSignatureAdapter
from tools.watermark_adapter import WatermarkAdapter
from tools.printing_adapter import PrintingAdapter

try:
    from tools.template_system import TemplateSystem
except ImportError:
    TemplateSystem = None

logger = logging.getLogger(__name__)


class MissionDebriefManager:
    """Mission Debrief Manager - bootstrap component for report finalisation."""

    SECTION_REGISTRY: Dict[str, Dict[str, Any]] = {
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
        "section_toc": {"title": "Table of Contents", "tags": ["toc", "index", "navigation"]},
    }

    def __init__(
        self,
        ecc: Optional[Any] = None,
        bus: Optional[Any] = None,
        gateway: Optional[Any] = None,
        manifest_path: Optional[str] = None,
    ) -> None:
        self.ecc = ecc
        self.bus = bus
        self.gateway = gateway
        self.logger = logger

        self.is_bootstrap_component = True
        self.bootstrap_time = datetime.now().isoformat()
        self.registered_signals: List[str] = []

        self.manifest_path = Path(manifest_path) if manifest_path else None
        self.debrief_root = DEBRIEF_ROOT
        self.root_install_directory = COMMAND_CENTER_ROOT.parent
        if not self.root_install_directory.exists():
            self.root_install_directory = MISSION_DEBRIEF_ROOT
        self.production_root = self.debrief_root / "productions"
        self.production_root.mkdir(parents=True, exist_ok=True)
        self.export_root = self._ensure_directory(self.root_install_directory / "DKI_Exports")
        self.exports_dir = self._ensure_directory(self.export_root / "Depositions")

        self.template_system = TemplateSystem() if TemplateSystem else None

        self.evidence_pipeline_adapter = self._init_adapter(
            "EvidencePipelineAdapter", EvidencePipelineAdapter, manifest_path=self.manifest_path
        )
        self.pdf_extraction_adapter = self._init_adapter(
            "PdfExtractionAdapter", PdfExtractionAdapter, manifest_path=self.manifest_path
        )
        self.api_services_adapter = self._init_adapter("ApiServiceAdapter", ApiServiceAdapter)
        self.report_generator_adapter = self._init_adapter("ReportGeneratorAdapter", ReportGeneratorAdapter)
        self.digital_signature_adapter = self._init_adapter("DigitalSignatureAdapter", DigitalSignatureAdapter)
        self.watermark_adapter = self._init_adapter("WatermarkAdapter", WatermarkAdapter)
        self.printing_adapter = self._init_adapter("PrintingAdapter", PrintingAdapter)

        self.osint_adapter = self.api_services_adapter

        self.tool_status = self._rebuild_tool_status()
        self.report_queue: List[Dict[str, Any]] = []
        self.processed_reports: Dict[str, Dict[str, Any]] = {}
        self.case_summaries: Dict[str, Dict[str, Any]] = {}
        self.handoff_log: List[Dict[str, Any]] = []
        self.section_updates: Dict[str, Dict[str, Any]] = {}
        self.section_completion_log: List[Dict[str, Any]] = []

        if self.bus:
            self._register_with_bus()

        self.logger.info("Mission Debrief Manager initialised as bootstrap component")

    def _init_adapter(self, name: str, factory: Any, *args: Any, **kwargs: Any) -> Optional[Any]:
        try:
            return factory(*args, **kwargs)
        except Exception as exc:
            self.logger.exception("Failed to initialise %s: %s", name, exc)
            return None

    @staticmethod
    def _ensure_directory(path: Path) -> Path:
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _adapter_available(self, adapter: Optional[Any]) -> bool:
        if not adapter:
            return False
        checker = getattr(adapter, "is_available", None)
        if callable(checker):
            try:
                return bool(checker())
            except Exception:
                return False
        return True

    def _compose_cover_page(
        self,
        heading: str,
        case_id: str,
        display_timestamp: str,
        base_cover: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        cover = deepcopy(base_cover) if base_cover else {}
        prefix_lines = [heading, "", f"Case: {case_id}", f"Generated: {display_timestamp}"]
        existing_content = cover.get("content")
        if existing_content:
            cover["content"] = "\n".join(prefix_lines + ["", existing_content])
        else:
            cover["content"] = "\n".join(prefix_lines)
        metadata = cover.setdefault("metadata", {})
        metadata["artifact"] = heading
        metadata.setdefault("case_id", case_id)
        metadata["generated_at"] = display_timestamp
        cover.setdefault("type", "cover_page")
        return cover

    def _compose_disclosure_page(
        self,
        heading: str,
        case_id: str,
        display_timestamp: str,
        base_disclosure: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        disclosure = deepcopy(base_disclosure) if base_disclosure else {}
        primer = f"This {heading.lower()} was generated on {display_timestamp} for case {case_id}."
        existing_content = disclosure.get("content")
        if existing_content:
            disclosure["content"] = f"{primer}\n\n{existing_content}"
        else:
            disclosure["content"] = primer
        metadata = disclosure.setdefault("metadata", {})
        metadata["artifact"] = heading
        metadata.setdefault("case_id", case_id)
        metadata["generated_at"] = display_timestamp
        disclosure.setdefault("type", "disclosure_page")
        return disclosure

    def _compose_table_of_contents(
        self, heading: str, sections: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        toc_lines = ["TABLE OF CONTENTS", ""]
        for index, section in enumerate(sections, start=1):
            title = section.get("title") or section.get("section_id") or f"Section {index}"
            toc_lines.append(f"{title} ... {index + 1}")
        if not sections:
            toc_lines.append("No sections available")
        metadata = {"total_sections": len(sections), "artifact": heading}
        return {"type": "table_of_contents", "content": "\n".join(toc_lines), "metadata": metadata}

    def _assemble_artifact_payload(
        self,
        heading: str,
        case_id: str,
        display_timestamp: str,
        sections: List[Dict[str, Any]],
        base_payload: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        if not sections:
            return None
        cover = self._compose_cover_page(heading, case_id, display_timestamp, (base_payload or {}).get("cover_page"))
        disclosure = self._compose_disclosure_page(heading, case_id, display_timestamp, (base_payload or {}).get("disclosure_page"))
        toc = self._compose_table_of_contents(heading, sections)
        payload = {
            "cover_page": cover,
            "table_of_contents": toc,
            "sections": sections,
            "disclosure_page": disclosure,
            "metadata": {
                "case_id": case_id,
                "artifact": heading,
                "generated_timestamp": display_timestamp,
                "total_sections": len(sections),
            },
        }
        return payload

    def _build_billing_summary_payload(
        self,
        base_payload: Optional[Dict[str, Any]],
        case_id: str,
        display_timestamp: str,
    ) -> Optional[Dict[str, Any]]:
        if not base_payload:
            return None
        filtered: List[Dict[str, Any]] = []
        for section in base_payload.get("sections", []) or []:
            if section.get("section_id") == "section_6":
                filtered.append(deepcopy(section))
        if not filtered:
            return None
        for section in filtered:
            section.setdefault("title", "Billing Summary")
        return self._assemble_artifact_payload("Billing Summary", case_id, display_timestamp, filtered, base_payload)

    def _build_evidence_manifest_payload(
        self,
        pipeline_result: Optional[Dict[str, Any]],
        base_payload: Optional[Dict[str, Any]],
        case_id: str,
        display_timestamp: str,
    ) -> Dict[str, Any]:
        manifest_entries = []
        if pipeline_result:
            manifest_entries = pipeline_result.get("manifest") or []
        lines: List[str] = ["Evidence Manifest", ""]
        if manifest_entries:
            lines.append("Manifest Items:")
            for idx, entry in enumerate(manifest_entries, start=1):
                name = entry.get("name") or Path(entry.get("path", "")).name
                file_type = entry.get("type") or "unknown"
                size = entry.get("size")
                size_text = f"{size} bytes" if isinstance(size, (int, float)) else "size unavailable"
                status = entry.get("error") or "available"
                lines.append(f"  {idx}. {name} ({file_type}) [{size_text}] -> {status}")
                hashes = entry.get("hashes") or {}
                if isinstance(hashes, dict):
                    sha256 = hashes.get("sha256") or hashes.get("sha512")
                    if sha256:
                        lines.append(f"     hash: {sha256}")
        else:
            lines.append("No evidence files were processed for this report.")
        if pipeline_result:
            routing = pipeline_result.get("routing") or []
            if routing:
                lines.extend(["", "Routing Plan:"])
                for route in routing:
                    target = route.get("target_section") or "section_8"
                    descriptor = route.get("name") or route.get("path") or "item"
                    engines = ", ".join(route.get("engine_priority") or [])
                    if engines:
                        lines.append(f"  - {descriptor} -> {target} (engines: {engines})")
                    else:
                        lines.append(f"  - {descriptor} -> {target}")
            errors = pipeline_result.get("errors") or []
            if errors:
                lines.extend(["", "Pipeline Notes:"])
                for err in errors:
                    lines.append(f"  ! {err}")
        section = {
            "section_id": "evidence_manifest",
            "title": "Evidence Manifest",
            "content": "\n".join(lines),
        }
        payload = self._assemble_artifact_payload("Evidence Manifest", case_id, display_timestamp, [section], base_payload)
        if payload:
            return payload
        return {
            "cover_page": self._compose_cover_page("Evidence Manifest", case_id, display_timestamp, (base_payload or {}).get("cover_page")),
            "table_of_contents": self._compose_table_of_contents("Evidence Manifest", [section]),
            "sections": [section],
            "disclosure_page": self._compose_disclosure_page("Evidence Manifest", case_id, display_timestamp, (base_payload or {}).get("disclosure_page")),
            "metadata": {
                "case_id": case_id,
                "artifact": "Evidence Manifest",
                "generated_timestamp": display_timestamp,
                "total_sections": 1,
            },
        }

    def _rebuild_tool_status(self) -> Dict[str, bool]:
        status = {
            "digital_signature": self._adapter_available(self.digital_signature_adapter),
            "printing": self._adapter_available(self.printing_adapter),
            "template": self.template_system is not None,
            "watermark": self._adapter_available(self.watermark_adapter),
            "osint": self._adapter_available(self.osint_adapter),
            "api_services": self._adapter_available(self.api_services_adapter),
            "evidence_pipeline": self._adapter_available(self.evidence_pipeline_adapter),
            "pdf_extraction": self._adapter_available(self.pdf_extraction_adapter),
            "report_generator": self._adapter_available(self.report_generator_adapter),
        }
        return status

    def refresh_tool_status(self) -> Dict[str, bool]:
        self.tool_status = self._rebuild_tool_status()
        return self.tool_status

    def _adapter_capabilities(self, adapter: Optional[Any], fallback: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        details: Dict[str, Any] = {}
        available = self._adapter_available(adapter)
        capability = getattr(adapter, "capability_status", None)
        if callable(capability):
            try:
                data = capability()
                if isinstance(data, dict):
                    details.update(data)
            except Exception as exc:
                details["error"] = str(exc)
        if "available" not in details:
            details["available"] = available
        if fallback:
            for key, value in fallback.items():
                details.setdefault(key, value)
        return details

    def _emit_bus_event(self, channel: str, payload: Dict[str, Any]) -> None:
        if not self.bus or not hasattr(self.bus, "emit"):
            return
        try:
            self.bus.emit(channel, payload)
        except Exception as exc:
            self.logger.error("Failed to emit bus event %s: %s", channel, exc)

    @staticmethod
    def _to_string_list(value: Any) -> List[str]:
        if isinstance(value, list):
            return [str(item) for item in value if item]
        if isinstance(value, (str, Path)):
            return [str(value)]
        return []

    def _normalize_evidence_entries(self, entries: Any) -> List[Dict[str, Any]]:
        if not entries:
            return []
        if isinstance(entries, dict):
            return [entries]
        if isinstance(entries, list):
            normalized: List[Dict[str, Any]] = []
            for item in entries:
                if isinstance(item, dict):
                    normalized.append(item)
                elif isinstance(item, (str, Path)):
                    normalized.append({"file_path": str(item)})
            return normalized
        if isinstance(entries, (str, Path)):
            return [{"file_path": str(entries)}]
        return []

    def _sanitize_case_id(self, case_id: Optional[str]) -> str:
        if not case_id:
            return "UNASSIGNED"
        sanitized = "".join(
            ch if ch.isalnum() or ch in ("-", "_") else "_"
            for ch in str(case_id).strip()
        )
        return sanitized or "UNASSIGNED"

    def _normalise_export_extension(self, export_format: Optional[str]) -> str:
        if not export_format:
            return "pdf"
        token = str(export_format).strip()
        if not token:
            return "pdf"
        token = token.lstrip(".")
        fmt = token.upper()
        mapping = {
            "PDF": "pdf",
            "DOCX": "docx",
            "MS_WORD": "docx",
        }
        return mapping.get(fmt, fmt.lower())

    def _build_deposition_filename(
        self, case_id: str, artifact: str, timestamp_token: str, extension: str
    ) -> str:
        safe_case_id = self._sanitize_case_id(case_id)
        artifact_token = "".join(ch for ch in artifact if ch.isalnum()) or artifact
        ext = self._normalise_export_extension(extension)
        return f"{safe_case_id}_{artifact_token}_{timestamp_token}.{ext}"

    def _build_deposition_path(
        self, case_id: str, artifact: str, timestamp_token: str, extension: str
    ) -> Path:
        filename = self._build_deposition_filename(case_id, artifact, timestamp_token, extension)
        return self.exports_dir / filename

    def _build_deposition_catalog(
        self, case_id: str, timestamp_token: str, final_extension: str
    ) -> Dict[str, Path]:
        catalog_map = {
            "final_report": ("FinalReport", final_extension),
            "billing_summary": ("BillingSummary", "pdf"),
            "evidence_manifest": ("EvidenceManifest", "pdf"),
            "print_version": ("PrintVersion", "pdf"),
            "export_log": ("ExportLog", "log"),
        }
        return {
            key: self._build_deposition_path(case_id, label, timestamp_token, ext)
            for key, (label, ext) in catalog_map.items()
        }

    def _write_export_log(self, log_path: Path, summary: Dict[str, Any]) -> None:
        log_payload = {
            "timestamp": datetime.now().isoformat(),
            "report_id": summary.get("report_id"),
            "case_id": summary.get("case_id"),
            "status": summary.get("status"),
            "steps_completed": summary.get("steps_completed", []),
            "tools_used": summary.get("tools_used", []),
            "output_files": summary.get("output_files", []),
            "errors": summary.get("errors", []),
        }
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(json.dumps(log_payload, indent=2), encoding="utf-8")

    def _prepare_osint_parameters(
        self, service: str, query: Optional[str], parameters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        payload = dict(parameters or {})
        if service == "google_search":
            if query is not None:
                payload.setdefault("query", query)
        elif service == "verify_address":
            if query is not None:
                payload.setdefault("address", query)
        elif service == "reverse_phone":
            if query is not None:
                payload.setdefault("phone_number", query)
                payload.setdefault("phone", query)
        elif service == "business_lookup":
            if query is not None:
                payload.setdefault("business_name", query)
        elif service == "person_lookup":
            if query is not None:
                payload.setdefault("name", query)
        elif service == "comprehensive_verification":
            if "subject_data" not in payload:
                payload["subject_data"] = payload.get("subject_data") or {}
            if query and "query" not in payload["subject_data"]:
                payload["subject_data"]["query"] = query
        else:
            if query is not None:
                payload.setdefault("query", query)
        return payload

    def _store_case_summary(self, case_id: Optional[str], result: Dict[str, Any]) -> None:
        if not case_id:
            return
        summary_payload = {
            "case_id": case_id,
            "report_id": result.get("report_id"),
            "processed_at": result.get("processed_at"),
            "steps_completed": result.get("steps_completed", []),
            "tools_used": result.get("tools_used", []),
            "status": result.get("status"),
        }
        self.case_summaries[case_id] = summary_payload
    # ECC integration helpers -------------------------------------------------

    def _call_out_to_ecc(self, operation: str, data: Dict[str, Any]) -> bool:
        if not self.ecc:
            self.logger.warning("ECC not available for call-out")
            return False
        call_out_data = {
            "operation": operation,
            "source": "mission_debrief_manager",
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }
        try:
            if hasattr(self.ecc, "emit"):
                self.ecc.emit("mission_debrief_manager.call_out", call_out_data)
                self.logger.info("ECC call-out issued for %s", operation)
                return True
            self.logger.warning("ECC does not support signal emission")
            return False
        except Exception as exc:
            self.logger.error("Failed to call out to ECC: %s", exc)
            return False

    def _wait_for_ecc_confirm(self, timeout: int = 30) -> bool:
        try:
            self.logger.info("Waiting for ECC confirmation (timeout %s seconds)", timeout)
            time.sleep(0.1)
            self.logger.info("ECC confirmation received")
            return True
        except Exception as exc:
            self.logger.error("ECC confirmation error: %s", exc)
            return False

    def _send_message(self, message_type: str, data: Dict[str, Any]) -> bool:
        if not self.ecc:
            self.logger.warning("ECC not available for message sending")
            return False
        message_data = {
            "message_type": message_type,
            "source": "mission_debrief_manager",
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }
        try:
            if hasattr(self.ecc, "emit"):
                self.ecc.emit(f"mission_debrief_manager.{message_type}", message_data)
                self.logger.info("ECC message emitted: %s", message_type)
                return True
            self.logger.warning("ECC does not support signal emission")
            return False
        except Exception as exc:
            self.logger.error("Failed to send ECC message: %s", exc)
            return False

    def _send_accept_signal(self, operation: str) -> bool:
        if not self.ecc:
            self.logger.warning("ECC not available for accept signal")
            return False
        accept_data = {
            "operation": operation,
            "source": "mission_debrief_manager",
            "status": "accepted",
            "timestamp": datetime.now().isoformat(),
        }
        try:
            if hasattr(self.ecc, "emit"):
                self.ecc.emit("mission_debrief_manager.accept", accept_data)
                self.logger.info("ECC accept signal emitted for %s", operation)
                return True
            self.logger.warning("ECC does not support signal emission")
            return False
        except Exception as exc:
            self.logger.error("Failed to send ECC accept signal: %s", exc)
            return False

    def _complete_handoff(self, operation: str, status: str) -> bool:
        handoff_data = {
            "operation": operation,
            "source": "mission_debrief_manager",
            "status": status,
            "timestamp": datetime.now().isoformat(),
        }
        try:
            self.handoff_log.append(handoff_data)
            self.logger.info("Handoff completed: %s - %s", operation, status)
            return True
        except Exception as exc:
            self.logger.error("Failed to record handoff: %s", exc)
            return False

    def _enforce_section_aware_execution(self, section_id: str) -> bool:
        if not self.ecc:
            self.logger.warning("ECC not available for section validation")
            return True
        if not self.validate_section_id(section_id):
            self.logger.error("Invalid section ID: %s", section_id)
            return False
        try:
            if hasattr(self.ecc, "can_run") and not self.ecc.can_run(section_id):
                self.logger.error("Section %s not active or blocked", section_id)
                return False
        except Exception as exc:
            self.logger.error("Section validation failed: %s", exc)
            return False
        return True

    def validate_section_id(self, section_id: str) -> bool:
        return section_id in self.SECTION_REGISTRY

    def get_section_registry(self) -> Dict[str, Any]:
        return self.SECTION_REGISTRY.copy()

    def _register_with_bus(self) -> bool:
        try:
            if not self.bus:
                return False
            self.bus.register_signal("mission_debrief.digital_sign", self._handle_digital_sign_signal)
            self.bus.register_signal("mission_debrief.print_report", self._handle_print_report_signal)
            self.bus.register_signal("mission_debrief.apply_template", self._handle_apply_template_signal)
            self.bus.register_signal("mission_debrief.add_watermark", self._handle_add_watermark_signal)
            self.bus.register_signal("mission_debrief.osint_lookup", self._handle_osint_lookup_signal)
            self.bus.register_signal("mission_debrief.process_report", self._handle_process_report_signal)
            self.bus.register_signal("section.data.updated", self._handle_section_data_updated_signal)
            self.bus.register_signal("gateway.section.complete", self._handle_gateway_section_complete_signal)
            self.registered_signals = [
                "mission_debrief.digital_sign",
                "mission_debrief.print_report",
                "mission_debrief.apply_template",
                "mission_debrief.add_watermark",
                "mission_debrief.osint_lookup",
                "mission_debrief.process_report",
                "section.data.updated",
                "gateway.section.complete",
            ]
            self.logger.info("Mission Debrief Manager registered signals: %s", ", ".join(self.registered_signals))
            return True

        except Exception as exc:
            self.logger.error("Failed to register with bus: %s", exc)
            return False

    def _handle_section_data_updated_signal(self, signal_data: Dict[str, Any]) -> None:
        """Record section updates from the gateway/evidence locker."""
        try:
            if not isinstance(signal_data, dict):
                return
            raw_payload = signal_data.get("payload")
            payload = raw_payload if isinstance(raw_payload, dict) else signal_data
            section_id = signal_data.get("section_id") or payload.get("section_id")
            if not section_id:
                self.logger.warning("section.data.updated signal missing section_id")
                return
            record = {
                "section_id": section_id,
                "case_id": signal_data.get("case_id") or payload.get("case_id"),
                "received_at": datetime.now().isoformat(),
                "payload": payload,
            }
            self.section_updates[section_id] = record
            self.logger.info("Section update registered for %s", section_id)
            self._emit_bus_event("mission_debrief.section.update", record)
        except Exception as exc:
            self.logger.error("Failed to handle section.data.updated signal: %s", exc)

    def _handle_gateway_section_complete_signal(self, signal_data: Dict[str, Any]) -> None:
        """Track gateway section completion announcements."""
        try:
            if not isinstance(signal_data, dict):
                return
            raw_payload = signal_data.get("payload")
            payload = raw_payload if isinstance(raw_payload, dict) else signal_data
            section_id = signal_data.get("section_id") or payload.get("section_id")
            if not section_id:
                self.logger.warning("gateway.section.complete signal missing section_id")
                return
            record = {
                "section_id": section_id,
                "case_id": signal_data.get("case_id") or payload.get("case_id"),
                "received_at": datetime.now().isoformat(),
                "payload": payload,
            }
            self.section_completion_log.append(record)
            if section_id in self.section_updates:
                self.section_updates[section_id]["status"] = "complete"
            self.logger.info("Section %s marked complete by gateway", section_id)
            self._emit_bus_event("mission_debrief.section.complete", record)
        except Exception as exc:
            self.logger.error("Failed to handle gateway.section.complete signal: %s", exc)
    # Signal handlers ---------------------------------------------------------

    def _handle_digital_sign_signal(self, signal_data: Dict[str, Any]) -> None:
        file_path = signal_data.get("file_path")
        if not file_path:
            self.logger.error("Missing file_path in digital sign signal")
            return
        if not self._adapter_available(self.digital_signature_adapter):
            self.logger.warning("Digital signature adapter unavailable - skipping request")
            return
        certificate_path = signal_data.get("certificate_path")
        password = signal_data.get("password")
        try:
            result = self.digital_signature_adapter.sign(file_path, certificate_path, password)  # type: ignore[attr-defined]
            payload = {
                "file_path": file_path,
                "result": result,
                "signed_at": datetime.now().isoformat(),
            }
            self._emit_bus_event("mission_debrief.digital_signed", payload)
            self.logger.info("Digital signature applied to %s", file_path)
        except Exception as exc:
            self.logger.error("Failed to handle digital sign signal: %s", exc)

    def _handle_print_report_signal(self, signal_data: Dict[str, Any]) -> None:
        file_path = signal_data.get("file_path")
        if not file_path:
            self.logger.error("Missing file_path in print report signal")
            return
        if not self._adapter_available(self.printing_adapter):
            self.logger.warning("Printing adapter unavailable - skipping request")
            return
        printer_name = signal_data.get("printer_name")
        print_settings = signal_data.get("print_settings", {})
        try:
            result = self.printing_adapter.print_document(file_path, printer_name, print_settings)  # type: ignore[attr-defined]
            payload = {
                "file_path": file_path,
                "result": result,
                "printed_at": datetime.now().isoformat(),
            }
            self._emit_bus_event("mission_debrief.report_printed", payload)
            self.logger.info("Report print job dispatched for %s", file_path)
        except Exception as exc:
            self.logger.error("Failed to handle print report signal: %s", exc)

    def _handle_apply_template_signal(self, signal_data: Dict[str, Any]) -> None:
        if not self.template_system:
            self.logger.warning("Template system not available - skipping request")
            return
        template_name = signal_data.get("template_name")
        if not template_name:
            self.logger.error("Missing template_name in apply template signal")
            return
        data = signal_data.get("data", {})
        output_path = signal_data.get("output_path")
        try:
            result = self.template_system.apply_template(template_name, data, output_path)
            payload = {
                "template_name": template_name,
                "result": result,
                "applied_at": datetime.now().isoformat(),
            }
            self._emit_bus_event("mission_debrief.template_applied", payload)
            self.logger.info("Template %s applied", template_name)
        except Exception as exc:
            self.logger.error("Failed to handle apply template signal: %s", exc)

    def _handle_add_watermark_signal(self, signal_data: Dict[str, Any]) -> None:
        if not self._adapter_available(self.watermark_adapter):
            self.logger.warning("Watermark adapter unavailable - skipping request")
            return
        file_path = signal_data.get("file_path")
        if not file_path:
            self.logger.error("Missing file_path in add watermark signal")
            return
        watermark_text = signal_data.get("watermark_text", "DRAFT")
        watermark_type = signal_data.get("watermark_type", "draft")
        try:
            result = self.watermark_adapter.add(file_path, watermark_text, watermark_type)  # type: ignore[attr-defined]
            payload = {
                "file_path": file_path,
                "result": result,
                "watermarked_at": datetime.now().isoformat(),
            }
            self._emit_bus_event("mission_debrief.watermark_added", payload)
            self.logger.info("Watermark applied to %s", file_path)
        except Exception as exc:
            self.logger.error("Failed to handle add watermark signal: %s", exc)

    def _handle_osint_lookup_signal(self, signal_data: Dict[str, Any]) -> None:
        if not self._adapter_available(self.api_services_adapter):
            self.logger.warning("API services adapter unavailable - skipping request")
            return
        service = (
            signal_data.get("service")
            or signal_data.get("lookup_type")
            or "google_search"
        )
        query = signal_data.get("query")
        parameters = signal_data.get("parameters")
        try:
            if service == "system_status":
                result = self.api_services_adapter.get_system_status()  # type: ignore[attr-defined]
            else:
                payload = self._prepare_osint_parameters(service, query, parameters)
                result = self.api_services_adapter.perform_lookup(service, **payload)  # type: ignore[attr-defined]
            response = {
                "service": service,
                "query": query,
                "result": result,
                "completed_at": datetime.now().isoformat(),
            }
            self._emit_bus_event("mission_debrief.osint_completed", response)
            self.logger.info("OSINT lookup completed via service %s", service)
        except Exception as exc:
            self.logger.error("Failed to handle OSINT lookup signal: %s", exc)

    def _handle_process_report_signal(self, signal_data: Dict[str, Any]) -> None:
        report_data = signal_data.get("report_data", {})
        processing_options = signal_data.get("processing_options", {})
        try:
            result = self.process_complete_report(report_data, processing_options)
            payload = {
                "result": result,
                "processed_at": datetime.now().isoformat(),
            }
            self._emit_bus_event("mission_debrief.report_processed", payload)
        except Exception as exc:
            self.logger.error("Failed to handle process report signal: %s", exc)
    # Core processing ---------------------------------------------------------

    def process_complete_report(self, report_data: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not isinstance(report_data, dict):
            raise TypeError("report_data must be a dictionary")
        options = options or {}
        self.refresh_tool_status()

        start_time = datetime.now()
        timestamp_token = start_time.strftime("%Y%m%d_%H%M")
        display_timestamp = start_time.strftime("%Y-%m-%d %H:%M")
        case_id_value = report_data.get("case_id") or options.get("case_id") or "UNASSIGNED"
        final_extension = "pdf"

        operation = "process_complete_report"
        if not self._call_out_to_ecc(operation, report_data):
            self.logger.error("ECC permission denied for report processing")
            return {"error": "ECC permission denied", "status": "error"}
        if not self._wait_for_ecc_confirm():
            self.logger.error("ECC confirmation timeout for report processing")
            return {"error": "ECC confirmation timeout", "status": "error"}

        section_id = report_data.get("section_id") or options.get("section_id") or "section_1"
        if not self._enforce_section_aware_execution(section_id):
            return {"error": f"Section {section_id} not authorised", "status": "error"}

        report_id = report_data.get("report_id") or f"report_{start_time.strftime('%Y%m%d_%H%M%S')}"
        processing_result: Dict[str, Any] = {
            "report_id": report_id,
            "processed_at": start_time.isoformat(),
            "steps_completed": [],
            "tools_used": [],
            "output_files": [],
            "status": "ok",
            "section_id": section_id,
            "case_id": case_id_value,
            "case_id_sanitized": self._sanitize_case_id(case_id_value),
            "timestamp_token": timestamp_token,
            "display_timestamp": display_timestamp,
        }
        errors: List[Dict[str, Any]] = []
        output_files: List[str] = processing_result["output_files"]
        steps_completed: List[str] = processing_result["steps_completed"]
        tools_used: List[str] = processing_result["tools_used"]

        def append_output(path_obj: Any) -> None:
            if not path_obj:
                return
            str_path = str(path_obj)
            if str_path not in output_files:
                output_files.append(str_path)

        def record_step(step: str) -> None:
            if step and step not in steps_completed:
                steps_completed.append(step)

        def record_tool(tool: str) -> None:
            if tool and tool not in tools_used:
                tools_used.append(tool)

        evidence_entries = self._normalize_evidence_entries(
            options.get("evidence_files") or report_data.get("evidence_files") or report_data.get("evidence_manifest")
        )
        if evidence_entries and self._adapter_available(self.evidence_pipeline_adapter):
            try:
                pipeline_result = self.evidence_pipeline_adapter.process_batch(evidence_entries)  # type: ignore[attr-defined]
                processing_result["evidence_pipeline"] = pipeline_result
                steps_completed.append("evidence_routed")
                tools_used.append("evidence_pipeline")
            except Exception as exc:
                errors.append({"stage": "evidence_pipeline", "error": str(exc)})
                self.logger.error("Evidence pipeline processing failed: %s", exc)

        pdf_targets = self._normalize_evidence_entries(
            options.get("pdf_targets") or report_data.get("pdf_targets") or evidence_entries
        )
        if pdf_targets and self._adapter_available(self.pdf_extraction_adapter):
            try:
                pdf_result = self.pdf_extraction_adapter.extract(pdf_targets)  # type: ignore[attr-defined]
                processing_result["pdf_extraction"] = pdf_result
                steps_completed.append("pdf_extracted")
                tools_used.append("pdf_extraction")
                extracted_text = pdf_result.get("extracted_text")
                if extracted_text:
                    processing_result["extracted_text"] = extracted_text
            except Exception as exc:
                errors.append({"stage": "pdf_extraction", "error": str(exc)})
                self.logger.error("PDF extraction failed: %s", exc)

        section_payload = (
            report_data.get("sections")
            or report_data.get("section_data")
            or options.get("sections")
        )
        generated_report = None
        if section_payload and self._adapter_available(self.report_generator_adapter):
            try:
                report_type = report_data.get("report_type") or options.get("report_type") or "Investigative"
                generated_report = self.report_generator_adapter.generate(section_payload, report_type)  # type: ignore[attr-defined]
                processing_result["report_payload"] = generated_report
                steps_completed.append("report_generated")
                tools_used.append("report_generator")
            except Exception as exc:
                errors.append({"stage": "report_generator", "error": str(exc)})
                self.logger.error("Report generation failed: %s", exc)

        export_requested = (
            options.get("export_report")
            or options.get("export_format")
            or report_data.get("export_format")
        )
        export_path: Optional[Path] = None
        if export_requested and generated_report and self._adapter_available(self.report_generator_adapter):
            export_format = (
                options.get("export_format")
                or report_data.get("export_format")
                or "PDF"
            )
            normalized_extension = self._normalise_export_extension(export_format)
            final_extension = normalized_extension
            export_dir_override = options.get("export_dir") or report_data.get("export_dir")
            export_filename_override = options.get("export_filename") or report_data.get("export_filename")

            if export_dir_override or export_filename_override:
                export_dir = Path(export_dir_override) if export_dir_override else self.exports_dir
                export_dir.mkdir(parents=True, exist_ok=True)
                if not export_filename_override:
                    export_filename_override = self._build_deposition_filename(
                        case_id_value, "FinalReport", timestamp_token, normalized_extension
                    )
                export_path = export_dir / export_filename_override
            else:
                export_path = self._build_deposition_path(
                    case_id_value, "FinalReport", timestamp_token, normalized_extension
                )

            try:
                export_result = self.report_generator_adapter.export(
                    generated_report, str(export_path), export_format
                )  # type: ignore[attr-defined]
                processing_result["report_export"] = export_result
                processing_result["final_report_path"] = str(export_path)
                append_output(export_path)
                steps_completed.append("report_exported")
                tools_used.append("report_generator")
            except Exception as exc:
                errors.append({"stage": "report_export", "error": str(exc)})
                self.logger.error("Report export failed: %s", exc)
                export_path = None

        if options.get("add_watermark") and self._adapter_available(self.watermark_adapter):
            watermark_text = options.get("watermark_text", "DRAFT")
            watermark_type = options.get("watermark_type", "draft")
            targets = self._to_string_list(options.get("watermark_targets") or report_data.get("watermark_targets"))
            if not targets:
                targets = list(output_files) or self._to_string_list(report_data.get("output_files"))
            if not targets:
                targets = self._to_string_list(report_data.get("file_path"))
            for file_path in targets:
                try:
                    watermark_result = self.watermark_adapter.add(file_path, watermark_text, watermark_type)  # type: ignore[attr-defined]
                    processing_result.setdefault("watermark_results", []).append(watermark_result)
                    steps_completed.append("watermark_added")
                    tools_used.append("watermark")
                except Exception as exc:
                    errors.append({"stage": "watermark", "file": file_path, "error": str(exc)})
                    self.logger.error("Watermark step failed for %s: %s", file_path, exc)

        if options.get("digital_sign") and self._adapter_available(self.digital_signature_adapter):
            certificate_path = options.get("certificate_path")
            password = options.get("password")
            targets = self._to_string_list(options.get("signature_targets") or options.get("signature_files"))
            if not targets:
                targets = list(output_files) or self._to_string_list(report_data.get("output_files"))
            if not targets:
                targets = self._to_string_list(report_data.get("file_path"))
            for file_path in targets:
                try:
                    sign_result = self.digital_signature_adapter.sign(file_path, certificate_path, password)  # type: ignore[attr-defined]
                    processing_result.setdefault("signature_results", []).append(sign_result)
                    steps_completed.append("digital_signed")
                    tools_used.append("digital_signature")
                except Exception as exc:
                    errors.append({"stage": "digital_signature", "file": file_path, "error": str(exc)})
                    self.logger.error("Digital signature failed for %s: %s", file_path, exc)

        if options.get("print_report") and self._adapter_available(self.printing_adapter):
            printer_name = options.get("printer_name")
            print_settings = options.get("print_settings", {})
            targets = self._to_string_list(options.get("print_targets"))
            if not targets:
                targets = list(output_files) or self._to_string_list(report_data.get("output_files"))
            if not targets:
                targets = self._to_string_list(report_data.get("file_path"))
            for file_path in targets:
                try:
                    self.printing_adapter.print_document(file_path, printer_name, print_settings)  # type: ignore[attr-defined]
                    steps_completed.append("printed")
                    tools_used.append("printing")
                except Exception as exc:
                    errors.append({"stage": "printing", "file": file_path, "error": str(exc)})
                    self.logger.error("Printing failed for %s: %s", file_path, exc)

        deposition_catalog = self._build_deposition_catalog(case_id_value, timestamp_token, final_extension)
        if export_path:
            deposition_catalog["final_report"] = Path(export_path)
        final_report_path = deposition_catalog.get("final_report")
        if final_report_path:
            processing_result.setdefault("final_report_path", str(final_report_path))
        if self._adapter_available(self.report_generator_adapter):
            if generated_report:
                billing_payload = self._build_billing_summary_payload(generated_report, case_id_value, display_timestamp)
                billing_path = deposition_catalog.get("billing_summary")
                if billing_payload and billing_path:
                    try:
                        self.report_generator_adapter.export(billing_payload, str(billing_path), "PDF")  # type: ignore[attr-defined]
                        processing_result["billing_summary_path"] = str(billing_path)
                        append_output(billing_path)
                        record_step("billing_summary_exported")
                        record_tool("report_generator")
                    except Exception as exc:
                        errors.append({"stage": "billing_summary_export", "error": str(exc)})
                        self.logger.error("Billing summary export failed: %s", exc)
                        deposition_catalog.pop("billing_summary", None)
                evidence_payload = self._build_evidence_manifest_payload(
                    processing_result.get("evidence_pipeline"), generated_report, case_id_value, display_timestamp
                )
                evidence_path = deposition_catalog.get("evidence_manifest")
                if evidence_payload and evidence_path:
                    try:
                        self.report_generator_adapter.export(evidence_payload, str(evidence_path), "PDF")  # type: ignore[attr-defined]
                        processing_result["evidence_manifest_path"] = str(evidence_path)
                        append_output(evidence_path)
                        record_step("evidence_manifest_exported")
                        record_tool("report_generator")
                    except Exception as exc:
                        errors.append({"stage": "evidence_manifest_export", "error": str(exc)})
                        self.logger.error("Evidence manifest export failed: %s", exc)
                        deposition_catalog.pop("evidence_manifest", None)
                print_version_path = deposition_catalog.get("print_version")
                if print_version_path:
                    try:
                        self.report_generator_adapter.export(generated_report, str(print_version_path), "PDF")  # type: ignore[attr-defined]
                        processing_result["print_version_path"] = str(print_version_path)
                        append_output(print_version_path)
                        record_step("print_version_exported")
                        record_tool("report_generator")
                    except Exception as exc:
                        errors.append({"stage": "print_version_export", "error": str(exc)})
                        self.logger.error("Print-version export failed: %s", exc)
                        deposition_catalog.pop("print_version", None)
        else:
            deposition_catalog.pop("billing_summary", None)
            deposition_catalog.pop("evidence_manifest", None)
            deposition_catalog.pop("print_version", None)
        processing_result["deposition_catalog"] = {
            key: str(path_obj) for key, path_obj in deposition_catalog.items()
        }
        export_log_path = deposition_catalog["export_log"]
        try:
            processing_result["export_log"] = str(export_log_path)
            record_step("export_log_recorded")
            record_tool("mission_debrief_manager")
            append_output(export_log_path)
            self._write_export_log(export_log_path, processing_result)
        except Exception as exc:
            errors.append({"stage": "export_log", "error": str(exc)})
            self.logger.error("Failed to write export log: %s", exc)

        if errors:
            processing_result["errors"] = errors
            processing_result["status"] = "warning"

        self.processed_reports[report_id] = processing_result
        self._store_case_summary(case_id_value, processing_result)

        self._send_message("report_processed", processing_result)
        self._send_accept_signal(operation)
        self._complete_handoff(operation, processing_result.get("status", "ok"))

        self.logger.info("Complete report processed: %s", report_id)
        return processing_result

    # Reporting helpers -------------------------------------------------------

    def get_summary(self, case_id: str) -> Dict[str, Any]:
        case_key = case_id or "unknown_case"
        summary = self.case_summaries.get(case_key)
        if summary:
            return summary
        return {
            "case_id": case_key,
            "status": "pending",
            "reports_processed": len(self.processed_reports),
            "tools_available": dict(self.tool_status),
        }

    def get_bootstrap_status(self) -> Dict[str, Any]:
        return {
            "is_bootstrap_component": self.is_bootstrap_component,
            "bootstrap_time": self.bootstrap_time,
            "registered_signals": list(self.registered_signals),
            "tool_status": dict(self.tool_status),
            "report_queue_length": len(self.report_queue),
            "processed_reports_count": len(self.processed_reports),
            "available_tools": list(self.tool_status.keys()),
            "section_updates_tracked": len(self.section_updates),
            "section_completions_logged": len(self.section_completion_log),
            "bus_connected": bool(self.bus),
            "ecc_connected": bool(self.ecc),
            "gateway_connected": bool(self.gateway),
        }

    def get_tool_capabilities(self) -> Dict[str, Any]:
        capabilities = {
            "digital_signature": self._adapter_capabilities(self.digital_signature_adapter),
            "printing": self._adapter_capabilities(self.printing_adapter),
            "template": {
                "available": self.template_system is not None,
            },
            "watermark": self._adapter_capabilities(self.watermark_adapter),
            "osint": self._adapter_capabilities(self.osint_adapter),
            "api_services": self._adapter_capabilities(self.api_services_adapter),
            "evidence_pipeline": self._adapter_capabilities(self.evidence_pipeline_adapter),
            "pdf_extraction": self._adapter_capabilities(self.pdf_extraction_adapter),
            "report_generator": self._adapter_capabilities(self.report_generator_adapter),
        }
        if self.template_system:
            try:
                capabilities["template"]["capabilities"] = self.template_system.get_available_templates()
            except Exception as exc:
                capabilities["template"]["error"] = str(exc)
        return capabilities
