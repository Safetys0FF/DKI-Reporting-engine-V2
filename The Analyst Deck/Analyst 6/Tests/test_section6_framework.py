"""Unit tests for the Section 6 lifecycle wrapper."""

from __future__ import annotations

import unittest
from pathlib import Path
import sys
from typing import Any, Dict


TESTS_DIR = Path(__file__).resolve().parent
SECTION_DIR = TESTS_DIR.parent
DECK_ROOT = SECTION_DIR.parent

for path in (str(SECTION_DIR), str(DECK_ROOT), str(DECK_ROOT / "section revisions templates")):
    if path not in sys.path:
        sys.path.insert(0, path)

from section_6_framework import Section6Framework, LifecycleState


class StubGateway:
    ecc: Any = None

    def __init__(self) -> None:
        self.inputs_called = False
        self.published: Dict[str, Any] = {}
        self.emitted: Dict[str, Any] = {}

    def get_section_inputs(self, section_id: str) -> Dict[str, Any]:
        self.inputs_called = True
        return {
            "case_metadata": {"case_id": "CASE-001"},
            "contract_terms": {},
            "planning_manifest": {},
            "surveillance_manifest": {"sessions": []},
            "toolkit_results": {},
        }

    def publish_section_result(self, section_id: str, result: Dict[str, Any]) -> None:
        self.published[section_id] = result

    def emit(self, signal: str, payload: Dict[str, Any]) -> None:
        self.emitted[signal] = payload


class StubDependency:
    def __init__(self) -> None:
        self.shutdown_called = False

    def shutdown(self) -> None:
        self.shutdown_called = True


class Section6FrameworkTests(unittest.TestCase):
    def _build_section(self) -> Section6Framework:
        dependency_initializers = {
            "evidence_manager": lambda **_: StubDependency(),
            "timestamp_engine": lambda **_: StubDependency(),
            "billing_renderer": lambda **_: type("Renderer", (), {"__call__": lambda self: self})(),
            "reverse_continuity": lambda **_: type("Reverse", (), {"__call__": lambda self: self})(),
            "metadata_processor": lambda **_: type("MetadataTool", (), {"process_zip": staticmethod(lambda *args, **kwargs: {"status": "SKIPPED"})}),
            "mileage_tool": lambda **_: type("MileageTool", (), {"audit_mileage": staticmethod(lambda: {"status": "SKIPPED"})}),
            "switchboard_factory": lambda **_: lambda mode: type("Switchboard", (), {
                "get_title": lambda self: "Section 6",
                "get_summary_rules": lambda self: [],
                "is_field_visible": lambda self: True,
                "include_voice_notes": lambda self: False,
                "show_mileage_statement": lambda self: "",
            })(),
            "voice_helper": lambda **_: type("VoiceHelper", (), {})(),
            "media_helper": lambda **_: type("MediaHelper", (), {})(),
        }
        gateway = StubGateway()
        return Section6Framework(
            gateway=gateway,
            communicator_initializer=lambda addr: None,
            dependency_initializers=dependency_initializers,
        )

    def test_baseline_initialization(self) -> None:
        section = self._build_section()
        self.assertEqual(section.lifecycle_state(), LifecycleState.ACTIVE)
        self.assertEqual(section.baseline_report.get("status"), "passed")

    def test_load_inputs_delegates_to_legacy(self) -> None:
        section = self._build_section()
        context = section.load_inputs()
        self.assertTrue(section.legacy._last_context)  # type: ignore[attr-defined]
        self.assertIn("case_metadata", context)

    def test_build_payload_and_publish_delegate(self) -> None:
        section = self._build_section()
        section.legacy.build_payload = lambda ctx: {"case_id": "CASE-001"}  # type: ignore[assignment]
        section.legacy.publish = lambda payload: {"status": "published"}  # type: ignore[assignment]
        payload = section.build_payload({"dummy": True})
        self.assertEqual(payload.get("case_id"), "CASE-001")
        result = section.publish(payload)
        self.assertEqual(result.get("status"), "published")

    def test_soft_shutdown_marks_state(self) -> None:
        section = self._build_section()
        report = section.soft_shutdown("test")
        self.assertEqual(section.lifecycle_state(), LifecycleState.SHUTDOWN)
        self.assertEqual(report.get("status"), "completed")


if __name__ == "__main__":
    unittest.main()
