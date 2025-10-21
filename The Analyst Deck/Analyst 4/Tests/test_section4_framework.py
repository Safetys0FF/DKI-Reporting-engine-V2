"""Unit tests for Section 4 lifecycle wrapper."""

from __future__ import annotations

import unittest
from pathlib import Path
import sys
from typing import Any, Dict, List

TESTS_DIR = Path(__file__).resolve().parent
SECTION_DIR = TESTS_DIR.parent
DECK_ROOT = SECTION_DIR.parent

for p in (SECTION_DIR, DECK_ROOT, DECK_ROOT / "section revisions templates"):
    path_str = str(p)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from section_4_framework import Section4Framework, LifecycleState


class DummyRecordsDataSource:
    def collect(self, context: Dict[str, Any]) -> Dict[str, Any]:
        records = context.get("case_metadata", {}).get("public_records", [])
        return {
            "records": records,
            "count": len(records),
            "sources": ["court"],
            "status": "COLLECTED" if records else "EMPTY",
        }


class DummyComplianceEngine:
    def evaluate(self, records: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "PASSED", "violations": []}


class DummyDocumentValidator:
    def validate(self, documents: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "PASSED", "valid": list(documents.keys()), "invalid": []}


class StubGateway:
    ecc: Any = None

    def __init__(self) -> None:
        self.published: Dict[str, Any] = {}

    def get_section_inputs(self, section_id: str) -> Dict[str, Any]:
        return {
            "case_metadata": {
                "case_id": "CASE-004",
                "public_records": [{"id": "rec-1", "source": "court", "last_updated": "2025-09-01"}],
                "required_public_sources": ["court"],
            },
            "planning_manifest": {},
            "surveillance_manifest": {"sessions": []},
            "toolkit_results": {},
            "media_index": {
                "documents": {
                    "doc-1": {
                        "checksum": "abc",
                        "checksum_verified": True,
                        "signature_valid": True,
                        "watermark_status": "valid",
                    }
                }
            },
            "voice_transcripts": [],
        }

    def publish_section_result(self, section_id: str, result: Dict[str, Any]) -> None:
        self.published[section_id] = result

    def emit(self, signal: str, payload: Dict[str, Any]) -> None:
        self.published[(signal, "emit")] = payload


class Section4FrameworkTests(unittest.TestCase):
    def _build_section(self) -> Section4Framework:
        dependency_initializers = {
            "northstar_tool": lambda **_: type("NorthStar", (), {"process_assets": staticmethod(lambda *args, **kwargs: {"status": "SKIPPED"})}),
            "cochran_tool": lambda **_: type("Cochran", (), {"verify_identity": staticmethod(lambda *args, **kwargs: {"status": "ACCEPT"})}),
            "reverse_continuity": lambda **_: type("Reverse", (), {"run_validation": lambda self, *args, **kwargs: (True, [])}),
            "metadata_tool": lambda **_: type("Metadata", (), {"process_zip": staticmethod(lambda *args, **kwargs: {"status": "SKIPPED"})}),
            "mileage_tool": lambda **_: type("Mileage", (), {"audit_mileage": staticmethod(lambda: {"status": "SKIPPED"})}),
            "renderer_factory": lambda **_: type("Renderer", (), {"render_model": lambda self, payload, case_sources: {
                "render_tree": [],
                "manifest": {}
            }}),
            "voice_helper": lambda **_: type("Voice", (), {"summarize": staticmethod(lambda transcripts: {"formatted": None})}),
            "media_helper": lambda **_: type("Media", (), {
                "collect_media_stats": staticmethod(lambda media_index: {"images": 0, "videos": 0, "audio": 0, "documents": 0}),
                "flatten_media_records": staticmethod(lambda index: {"images": {}, "videos": {}}),
            }),
            "records_data_source": lambda **_: DummyRecordsDataSource(),
            "compliance_engine": lambda **_: DummyComplianceEngine(),
            "document_validator": lambda **_: DummyDocumentValidator(),
        }
        gateway = StubGateway()
        return Section4Framework(
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
        self.assertIn("public_records_summary", context)

    def test_publish_delegates_to_legacy(self) -> None:
        section = self._build_section()
        section.legacy.publish = lambda payload: {"status": "published"}  # type: ignore[attr-defined]
        result = section.publish({})
        self.assertEqual(result.get("status"), "published")

    def test_compliance_artifacts_present(self) -> None:
        section = self._build_section()
        context = section.load_inputs()
        payload = section.build_payload(context)
        tool_results = payload.get("tool_results", {})
        self.assertIn("public_records", tool_results)
        self.assertIn("compliance_check", tool_results)
        self.assertIn("document_validation", tool_results)
        self.assertEqual(tool_results.get("compliance_check", {}).get("status"), "PASSED")


if __name__ == "__main__":
    unittest.main()
