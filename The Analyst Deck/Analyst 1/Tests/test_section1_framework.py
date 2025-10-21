"""Unit tests for Section 1 framework lifecycle and OCR pipeline."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys
from typing import Any, Dict

TESTS_DIR = Path(__file__).resolve().parent
SECTION_DIR = TESTS_DIR.parent
DECK_ROOT = SECTION_DIR.parent

for path in (str(SECTION_DIR), str(DECK_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

from section_1_framework import LifecycleState, Section1Framework


class StubGateway:
    ecc: Any = None

    def __init__(self) -> None:
        self.published_payload = None
        self.emitted_signals: Dict[str, Any] = {}
        self.revisions: Dict[str, Dict[str, Any]] = {}

    def get_section_inputs(self, section_id: str) -> Dict[str, Any]:
        return {"case_id": "CASE-001", "section_needs": {"documents": 2}}

    def publish_section_result(self, section_id: str, result: Dict[str, Any]) -> None:
        self.published_payload = (section_id, result)

    def emit(self, signal: str, payload: Dict[str, Any]) -> None:
        self.emitted_signals[signal] = payload

    def log_revision(self, section_id: str, reason: str, context: Dict[str, Any]) -> None:
        self.revisions[section_id] = {"reason": reason, "context": context}


class StubCommunicator:
    def __init__(self, module_address: str) -> None:
        self.module_address = module_address
        self.bus_connection = None
        self.sent_signals: Dict[str, str] = {}

    def send_signal(self, target_address: str, radio_code: str, message: str = "", **_: Any) -> None:
        self.sent_signals[target_address] = message

    def send_sos_fault(self, fault_code: str, description: str) -> None:
        self.sent_signals[fault_code] = description


class StubDependency:
    def __init__(self, name: str) -> None:
        self.name = name
        self.shutdown_called = False

    def shutdown(self) -> None:
        self.shutdown_called = True


class StubUnstructured:
    def __init__(self, outputs: Dict[str, Any]) -> None:
        self.outputs = outputs
        self.calls: list[str] = []

    def partition(self, file_path: str):
        self.calls.append(file_path)
        return self.outputs.get(file_path, [])


class StubTesseract:
    def __init__(self, outputs: Dict[str, Dict[str, Any]]) -> None:
        self.outputs = outputs
        self.calls: list[str] = []

    def extract_text(self, file_path: str) -> Dict[str, Any]:
        self.calls.append(file_path)
        return self.outputs.get(
            file_path,
            {"text": "", "text_blocks": [], "engine_used": "tesseract"},
        )


class StubEasyOCR:
    def __init__(self, outputs: Dict[str, Dict[str, Any]]) -> None:
        self.outputs = outputs
        self.calls: list[str] = []

    def extract_text(self, file_path: str) -> Dict[str, Any]:
        self.calls.append(file_path)
        return self.outputs.get(
            file_path,
            {"text": "", "text_blocks": [], "engine_used": "easyocr"},
        )


class Section1FrameworkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.gateway = StubGateway()
        self.communicator_initializer = lambda addr: StubCommunicator(addr)

    def _build_section(self, dependency_initializers: Dict[str, Any]) -> Section1Framework:
        return Section1Framework(
            gateway=self.gateway,
            communicator_initializer=self.communicator_initializer,
            dependency_initializers=dependency_initializers,
        )

    def test_baseline_initialization_activates_section(self) -> None:
        dependency_initializers = {
            "evidence_manager": lambda **_: StubDependency("evidence_manager"),
            "northstar_protocol": lambda **_: lambda *args, **kwargs: {},
            "cochran_match": lambda **_: lambda *args, **kwargs: {},
            "reverse_continuity": lambda **_: StubDependency("reverse"),
            "metadata_processor": lambda **_: lambda *args, **kwargs: {},
            "mileage_audit": lambda **_: lambda *args, **kwargs: {},
            "section_renderer": lambda **_: StubDependency("renderer"),
            "tesseract_engine": lambda **_: StubTesseract({}),
            "unstructured_engine": lambda **_: StubUnstructured({}),
            "easyocr_engine": lambda **_: StubEasyOCR({}),
        }

        section = self._build_section(dependency_initializers)
        self.assertEqual(section.lifecycle_state(), LifecycleState.ACTIVE)
        self.assertEqual(section.baseline_report.get("status"), "passed")

    def test_rest_and_resume_transitions(self) -> None:
        section = self._build_section(
            {
                "evidence_manager": lambda **_: StubDependency("em"),
                "northstar_protocol": lambda **_: lambda *args, **kwargs: {},
                "cochran_match": lambda **_: lambda *args, **kwargs: {},
                "reverse_continuity": lambda **_: StubDependency("reverse"),
                "metadata_processor": lambda **_: lambda *args, **kwargs: {},
                "mileage_audit": lambda **_: lambda *args, **kwargs: {},
                "section_renderer": lambda **_: StubDependency("renderer"),
                "tesseract_engine": lambda **_: StubTesseract({}),
                "unstructured_engine": lambda **_: StubUnstructured({}),
                "easyocr_engine": lambda **_: StubEasyOCR({}),
            }
        )
        section.enter_rest_state("waiting for section 2")
        self.assertEqual(section.lifecycle_state(), LifecycleState.RESTING)
        section.resume_from_rest()
        self.assertEqual(section.lifecycle_state(), LifecycleState.ACTIVE)

    def test_soft_shutdown_releases_dependencies(self) -> None:
        deps = {
            "evidence_manager": lambda **_: StubDependency("em"),
            "northstar_protocol": lambda **_: lambda *args, **kwargs: {},
            "cochran_match": lambda **_: lambda *args, **kwargs: {},
            "reverse_continuity": lambda **_: StubDependency("reverse"),
            "metadata_processor": lambda **_: lambda *args, **kwargs: {},
            "mileage_audit": lambda **_: lambda *args, **kwargs: {},
            "section_renderer": lambda **_: StubDependency("renderer"),
            "tesseract_engine": lambda **_: StubTesseract({}),
            "unstructured_engine": lambda **_: StubUnstructured({}),
            "easyocr_engine": lambda **_: StubEasyOCR({}),
        }
        section = self._build_section(deps)
        report = section.soft_shutdown("test_shutdown")
        self.assertEqual(section.lifecycle_state(), LifecycleState.SHUTDOWN)
        self.assertEqual(report["status"], "completed")

    def test_ocr_pipeline_execution_order(self) -> None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as doc_file, tempfile.NamedTemporaryFile(delete=False, suffix=".png") as img_file:
            doc_path = Path(doc_file.name)
            img_path = Path(img_file.name)

        unstructured_stub = StubUnstructured(
            {
                str(doc_path): [{"text": "Doc text", "category": "Title"}],
                str(img_path): [],
            }
        )
        tesseract_stub = StubTesseract(
            {
                str(img_path): {
                    "text": "Image text",
                    "text_blocks": [{"text": "Image text", "confidence": 88}],
                    "engine_used": "tesseract",
                }
            }
        )
        easyocr_stub = StubEasyOCR({})

        section = self._build_section(
            {
                "evidence_manager": lambda **_: StubDependency("em"),
                "northstar_protocol": lambda **_: lambda *args, **kwargs: {},
                "cochran_match": lambda **_: lambda *args, **kwargs: {},
                "reverse_continuity": lambda **_: StubDependency("reverse"),
                "metadata_processor": lambda **_: lambda *args, **kwargs: {},
                "mileage_audit": lambda **_: lambda *args, **kwargs: {},
                "section_renderer": lambda **_: StubDependency("renderer"),
                "tesseract_engine": lambda **_: tesseract_stub,
                "unstructured_engine": lambda **_: unstructured_stub,
                "easyocr_engine": lambda **_: easyocr_stub,
            }
        )

        assets = [
            {"id": "DOC-1", "file_path": str(doc_path), "evidence_type": "pdf"},
            {"id": "IMG-1", "file_path": str(img_path), "evidence_type": "jpg"},
        ]

        ocr_results = section._run_ocr_pipeline(assets)
        doc_result = ocr_results["DOC-1"]
        img_result = ocr_results["IMG-1"]

        self.assertIn("unstructured", doc_result["engines_attempted"])
        self.assertEqual(doc_result["text_blocks"][0]["text"], "Doc text")

        self.assertIn("tesseract", img_result["engines_attempted"])
        self.assertEqual(img_result["text_blocks"][0]["text"], "Image text")

        Path(doc_path).unlink(missing_ok=True)
        Path(img_path).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
