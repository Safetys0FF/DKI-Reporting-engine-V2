"""Unit tests for Section 5 lifecycle wrapper."""

from __future__ import annotations

import unittest
from pathlib import Path
import sys
from typing import Any, Dict

TESTS_DIR = Path(__file__).resolve().parent
SECTION_DIR = TESTS_DIR.parent
DECK_ROOT = SECTION_DIR.parent

for p in (SECTION_DIR, DECK_ROOT, DECK_ROOT / "section revisions templates"):
    path_str = str(p)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from section_5_framework import Section5Framework, LifecycleState


class StubGateway:
    ecc: Any = None

    def __init__(self) -> None:
        self.published: Dict[str, Any] = {}

    def get_section_inputs(self, section_id: str) -> Dict[str, Any]:
        return {
            "case_metadata": {"case_id": "CASE-005"},
            "planning_manifest": {},
            "document_index": [],
            "toolkit_results": {},
        }

    def publish_section_result(self, section_id: str, result: Dict[str, Any]) -> None:
        self.published[section_id] = result

    def emit(self, signal: str, payload: Dict[str, Any]) -> None:
        self.published[(signal, "emit")] = payload


class Section5FrameworkTests(unittest.TestCase):
    def _build_section(self) -> Section5Framework:
        dependency_initializers = {
            "cochran_tool": lambda **_: type("Cochran", (), {"verify_identity": staticmethod(lambda *args, **kwargs: {"status": "ACCEPT"})}),
            "reverse_continuity": lambda **_: type("Reverse", (), {"run_validation": lambda self, *args, **kwargs: (True, [])}),
            "metadata_tool": lambda **_: type("Metadata", (), {"process_zip": staticmethod(lambda *args, **kwargs: {"status": "SKIPPED"})}),
            "renderer_factory": lambda **_: type("Renderer", (), {"render_model": lambda self, payload, case_sources: {
                "render_tree": [],
                "manifest": {}
            }}),
        }
        gateway = StubGateway()
        return Section5Framework(
            gateway=gateway,
            communicator_initializer=lambda addr: None,
            dependency_initializers=dependency_initializers,
        )

    def test_baseline_initialization(self) -> None:
        section = self._build_section()
        self.assertEqual(section.lifecycle_state(), LifecycleState.ACTIVE)
        self.assertEqual(section.baseline_report.get("status"), "passed")

    def test_load_inputs(self) -> None:
        section = self._build_section()
        context = section.load_inputs()
        self.assertIn("case_metadata", context)

    def test_publish_delegates_to_legacy(self) -> None:
        section = self._build_section()
        section.legacy.publish = lambda payload: {"status": "published"}  # type: ignore[attr-defined]
        result = section.publish({})
        self.assertEqual(result.get("status"), "published")


if __name__ == "__main__":
    unittest.main()
