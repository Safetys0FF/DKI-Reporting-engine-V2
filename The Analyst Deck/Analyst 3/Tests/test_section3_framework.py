"""Unit tests for Section 3 lifecycle wrapper."""

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

from section_3_framework import Section3Framework, LifecycleState


class DummyAudioTranscriber:
    def transcribe_batch(self, audio_index: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "id": key,
                "name": key,
                "summary": f"Audio transcript for {key}",
                "status": "transcribed",
            }
            for key in audio_index
        ]


class DummyVideoAnalyzer:
    def analyze_batch(self, video_index: Dict[str, Any]) -> Dict[str, Any]:
        return {
            key: {"id": key, "status": "analyzed", "duration": meta.get("duration")}
            for key, meta in video_index.items()
        }


class DummyTrackerDecoder:
    def decode(self, tracker_exports: Any) -> Dict[str, Any]:
        return {"status": "decoded", "tracks": [{"id": "T1", "points": 2}]}


class StubGateway:
    ecc: Any = None

    def __init__(self) -> None:
        self.published: Dict[str, Any] = {}

    def get_section_inputs(self, section_id: str) -> Dict[str, Any]:
        return {
            "case_metadata": {"case_id": "CASE-003"},
            "subject_manifest": [],
            "planning_manifest": {},
            "field_logs": [],
            "media_index": {
                "audio": {
                    "A1": {"file_path": str(TESTS_DIR / "fixtures" / "audio1.wav"), "duration": 30}
                },
                "videos": {
                    "V1": {"file_path": str(TESTS_DIR / "fixtures" / "video1.mp4"), "duration": 45, "frame_rate": 30}
                },
                "documents": {
                    "D1": {"checksum": "abc", "checksum_verified": True}
                },
            },
            "voice_transcripts": [],
            "toolkit_results": {"tracker_exports": [{"id": "T1", "points": [1, 2]}]},
        }

    def publish_section_result(self, section_id: str, result: Dict[str, Any]) -> None:
        self.published[section_id] = result

    def emit(self, signal: str, payload: Dict[str, Any]) -> None:
        self.published[(signal, "emit")] = payload


class Section3FrameworkTests(unittest.TestCase):
    def _build_section(self) -> Section3Framework:
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
            "audio_transcriber": lambda **_: DummyAudioTranscriber(),
            "video_analyzer": lambda **_: DummyVideoAnalyzer(),
            "tracker_decoder": lambda **_: DummyTrackerDecoder(),
        }
        gateway = StubGateway()
        return Section3Framework(
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
        self.assertTrue(context.get("voice_transcripts"))

    def test_publish_delegates_to_legacy(self) -> None:
        section = self._build_section()
        section.legacy.publish = lambda payload: {"status": "published"}  # type: ignore[attr-defined]
        result = section.publish({})
        self.assertEqual(result.get("status"), "published")

    def test_tool_results_include_new_artifacts(self) -> None:
        section = self._build_section()
        context = section.load_inputs()
        payload = section.build_payload(context)
        tool_results = payload.get("tool_results", {})
        self.assertIn("video_analysis", tool_results)
        self.assertIn("tracker_summary", tool_results)
        self.assertIn("audio_transcription", tool_results)
        audio_status = tool_results.get("audio_transcription", {})
        self.assertGreaterEqual(audio_status.get("count", 0), 1)


if __name__ == "__main__":
    unittest.main()
