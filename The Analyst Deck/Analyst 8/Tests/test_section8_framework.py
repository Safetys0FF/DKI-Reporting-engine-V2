"""Unit tests for Section 8 lifecycle wrapper."""

from __future__ import annotations

import unittest
from pathlib import Path
import sys
from typing import Any, Dict

TESTS_DIR = Path(__file__).resolve().parent
SECTION_DIR = TESTS_DIR.parent
DECK_ROOT = SECTION_DIR.parent

for path in (SECTION_DIR, DECK_ROOT, DECK_ROOT / "section revisions templates"):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from section_8_framework import Section8Framework, LifecycleState


class StubGateway:
    ecc: Any = None

    def __init__(self) -> None:
        self.published: Dict[str, Any] = {}

    def get_section_inputs(self, section_id: str) -> Dict[str, Any]:
        assert section_id == "section_8"
        sample_path = TESTS_DIR / "fixtures" / "sample.jpg"
        return {
            "case_metadata": {
                "case_id": "CASE-008",
                "contract_history": [{"type": "surveillance"}],
                "assets": [],
            },
            "media_index": {
                "images": {
                    "IMG-1": {
                        "file_info": {"path": str(sample_path)},
                        "processing_timestamp": "2025-10-10T08:00:00",
                        "metadata": {"source": "unit"},
                    }
                },
                "videos": {},
                "audio": {
                    "AUD-1": {
                        "summary": "Audio memo summary",
                        "duration": 30,
                        "processing_timestamp": "2025-10-10T08:05:00",
                    }
                },
            },
            "section_manifests": {},
            "toolkit_results": {},
            "manual_annotations": ["Verify capture location"],
        }

    def publish_section_result(self, section_id: str, result: Dict[str, Any]) -> None:
        self.published[section_id] = result


class Section8FrameworkTests(unittest.TestCase):
    def _build_section(self) -> Section8Framework:
        gateway = StubGateway()
        return Section8Framework(
            gateway=gateway,
            communicator_initializer=lambda addr: None,
        )

    def test_baseline_initialization(self) -> None:
        section = self._build_section()
        self.assertEqual(section.lifecycle_state(), LifecycleState.ACTIVE)
        self.assertEqual(section.baseline_report.get("status"), "passed")

    def test_build_payload_contains_enriched_fields(self) -> None:
        section = self._build_section()
        context = section.load_inputs()
        payload = section.build_payload(context)
        self.assertIn("images", payload)
        self.assertIn("catalog_summary", payload)
        self.assertIn("tool_results", payload)
        self.assertIn("media_catalog_summary", payload["tool_results"])

    def test_publish_returns_status(self) -> None:
        section = self._build_section()
        context = section.load_inputs()
        payload = section.build_payload(context)
        result = section.publish(payload)
        self.assertEqual(result.get("status"), "published")


if __name__ == "__main__":
    unittest.main()
