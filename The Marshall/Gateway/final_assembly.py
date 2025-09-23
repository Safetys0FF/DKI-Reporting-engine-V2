#!/usr/bin/env python3
"""
Final Assembly Manager

Implements an in-memory assembly cache for sectional catch-and-review, then
compiles a final report artifact using ReportGenerator. Mirrors the intent of
the spec in "12. Final Assembly.txt" (callbox signals, readiness, and export
handoff) with a practical Python implementation that fits the current codebase.
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from report_generator import ReportGenerator

logger = logging.getLogger(__name__)


class FinalAssemblyManager:
    """
    Manages section outputs and approval states, then assembles the full report.

    - add_section_output: store section render outputs from gateway
    - mark_section_state: track approval/completion for lifecycle checks
    - assemble_final_report: build final report dict via ReportGenerator
    - deduplicate_and_clean: optional extra structural cleanup
    """

    def __init__(self):
        self.section_outputs: Dict[str, Dict[str, Any]] = {}
        self.section_states: Dict[str, str] = {}
        self.signal_log: List[Dict[str, Any]] = []
        self.last_compiled: Optional[Dict[str, Any]] = None

    # --------------------------- Signal Handling --------------------------- #
    def push_signal(self, signal_type: str, payload: Optional[Dict[str, Any]] = None):
        entry = {
            "type": signal_type,
            "timestamp": datetime.now().isoformat(),
            "payload": payload or {},
        }
        self.signal_log.append(entry)
        logger.debug(f"FinalAssembly signal: {signal_type} | payload={payload}")

    # ------------------------- Section State/Output ----------------------- #
    def add_section_output(self, section_id: str, output: Dict[str, Any]):
        """Store/replace a section's generated output payload."""
        if not section_id:
            raise ValueError("section_id is required")
        if not isinstance(output, dict):
            raise ValueError("output must be a dict from gateway/renderer")
        self.section_outputs[section_id] = output
        logger.info(f"Cached output for {section_id}")

    def mark_section_state(self, section_id: str, state: str):
        """Set workflow state for a section (e.g., completed/approved/revision)."""
        if not section_id:
            raise ValueError("section_id is required")
        self.section_states[section_id] = state
        logger.debug(f"Section {section_id} -> state set to {state}")

    def get_ready_sections(self) -> Dict[str, Dict[str, Any]]:
        """Return outputs for sections that are at least completed."""
        ready: Dict[str, Dict[str, Any]] = {}
        for sid, out in self.section_outputs.items():
            state = self.section_states.get(sid, "")
            if state in {"completed", "approved"}:
                ready[sid] = out
        return ready

    # ----------------------------- Assembly ------------------------------- #
    def assemble_final_report(self, report_type: str, case_snapshot: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Build the final report dictionary using section outputs currently
        cached. Returns the compiled report (does not perform export).
        """
        generator = ReportGenerator()

        # The ReportGenerator expects a dict keyed by section ids or dicts with
        # 'section_id' metadata. Using the gateway section output objects works.
        section_data = self.get_ready_sections()

        if case_snapshot:
            # Some generator metadata extraction relies on this bag
            section_data = {**section_data, "_case_meta": case_snapshot}

        report = generator.generate_full_report(section_data, report_type)

        # Optional extra structural cleanup pass before handing to UI
        report["sections"] = self._deduplicate_and_clean_sections(report.get("sections", []))

        self.last_compiled = report
        logger.info(
            f"Final report assembled: type={report_type} sections={len(report.get('sections', []))}"
        )
        return report

    # --------------------------- Cleanup Helpers -------------------------- #
    def _deduplicate_and_clean_sections(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Light-weight structural cleanup pass:
        - Remove exact duplicate section bodies that appear multiple times
        - Collapse repeated blank lines in content
        Keeps first occurrence of a duplicated content block.
        """
        seen_hashes = set()
        cleaned: List[Dict[str, Any]] = []

        for sec in sections:
            content = (sec or {}).get("content", "")
            normalized = self._normalize_text(content)
            content_hash = hash(normalized)
            if content_hash in seen_hashes:
                # skip duplicate block
                continue
            seen_hashes.add(content_hash)

            sec_copy = dict(sec)
            sec_copy["content"] = normalized
            cleaned.append(sec_copy)

        return cleaned

    @staticmethod
    def _normalize_text(text: str) -> str:
        # Collapse 3+ newlines -> 2 newlines for readability
        import re
        t = text.replace("\r\n", "\n").replace("\r", "\n")
        t = re.sub(r"\n{3,}", "\n\n", t)
        return t.strip()

