#!/usr/bin/env python3
"""ReportGenerator - modern DKI Central Command export module.

Builds final reports from assembled narratives and evidence.
Compatible with ECC / Central Command Bus.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add path for shared interfaces
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))

# Import shared interfaces
try:
    from shared_interfaces import (
        StandardInterface, StandardSectionData, StandardEvidenceData,
        create_standard_report_signal, validate_signal_payload
    )
except ImportError:
    # Fallback if shared_interfaces not available
    StandardInterface = None
    StandardSectionData = None
    StandardEvidenceData = None
    create_standard_report_signal = None
    validate_signal_payload = None

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Modern report generator for ECC-based architecture."""

    def __init__(self, ecc: Optional[Any] = None, bus: Optional[Any] = None, output_dir: Optional[str] = None) -> None:
        self.ecc = ecc
        self.bus = bus
        self.output_dir = output_dir or os.path.join("F:\\The Central Command\\Generated Reports")
        os.makedirs(self.output_dir, exist_ok=True)

        if self.bus and hasattr(self.bus, "register_signal"):
            try:
                self.bus.register_signal("report.generate", self.handle_generate)
                self.bus.register_signal("report.export", self.handle_export)
                logger.info("ReportGenerator registered with Central Command Bus")
            except Exception as exc:
                logger.warning("Bus registration failed: %s", exc)

    # ------------------------------------------------------------------
    # Main generation routine
    # ------------------------------------------------------------------
    def generate_full_report(
        self,
        evidence: Optional[Dict[str, Any]] = None,
        sections: Optional[Dict[str, str]] = None,
        case_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a unified text report from provided sections."""

        case_token = case_id or f"CASE-{datetime.now():%Y%m%d%H%M%S}"
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        report_path = Path(self.output_dir) / f"{case_token}_FinalReport.txt"

        try:
            # Normalize sections data using standardized interface
            if StandardInterface and sections:
                sections = {k: StandardInterface.normalize_section_content(v) for k, v in sections.items()}
            
            header = [
                "DKI SERVICES - FINAL REPORT",
                f"Generated: {timestamp}",
                f"Case ID: {case_token}",
                "",
                "=" * 80,
                "",
            ]
            body: List[str] = []

            if sections:
                for sid, text in sections.items():
                    body.append(f"[{sid.upper()}]")
                    body.append(text.strip())
                    body.append("")

            if evidence:
                body.append("")
                body.append("EVIDENCE INDEX:")
                for eid, item in evidence.items():
                    label = item.get("filename") or item.get("file_path") or eid
                    body.append(f" - {eid}: {label}")

            with open(report_path, "w", encoding="utf-8") as handle:
                handle.write("\n".join(header + body).rstrip() + "\n")

            # Create standardized report payload
            if create_standard_report_signal:
                payload = create_standard_report_signal(
                    case_id=case_token,
                    report_id=f"report_{case_token}_{timestamp.replace('-', '').replace(':', '').replace(' ', '_')}",
                    status="complete",
                    report_path=str(report_path),
                    sections=sections,
                    evidence=evidence
                )
            else:
                # Fallback to original format
                payload = {
                    "status": "ok",
                    "case_id": case_token,
                "report_path": str(report_path),
                "generated_at": timestamp,
            }
            logger.info("Report generated: %s", report_path)

            if self.bus and hasattr(self.bus, "emit"):
                self.bus.emit("report.generated", payload)
            return payload
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Report generation failed: %s", exc)
            return {"status": "error", "error": str(exc), "case_id": case_token}

    # ------------------------------------------------------------------
    # Bus handlers
    # ------------------------------------------------------------------
    def handle_generate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle bus signal to generate report."""
        return self.generate_full_report(
            evidence=payload.get("evidence"),
            sections=payload.get("sections"),
            case_id=payload.get("case_id"),
        )

    def handle_export(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle export request (future: DOCX/PDF/ZIP)."""
        result = self.generate_full_report(
            evidence=payload.get("evidence"),
            sections=payload.get("sections"),
            case_id=payload.get("case_id"),
        )
        if result.get("status") == "ok":
            logger.info("Report exported successfully")
        return result


# Convenience factory

def create_report_generator(ecc: Optional[Any] = None, bus: Optional[Any] = None, output_dir: Optional[str] = None) -> ReportGenerator:
    generator = ReportGenerator(ecc=ecc, bus=bus, output_dir=output_dir)
    logger.info("ReportGenerator instance created")
    return generator
