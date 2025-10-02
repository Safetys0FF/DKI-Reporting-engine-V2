
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest


def _make_section(section_id: str, title: str) -> Dict[str, Any]:
    return {
        "section_id": section_id,
        "title": title,
        "content": f"Content for {title}",
    }


class DummyECC:
    def emit(self, *args: Any, **kwargs: Any) -> None:
        return None

    def can_run(self, section_id: str) -> bool:
        return True


class StubUnavailableAdapter:
    def is_available(self) -> bool:
        return False


class StubEvidencePipelineAdapter:
    def __init__(self) -> None:
        self.manifest = [
            {
                "name": "image_001.jpg",
                "path": str(Path("/tmp/image_001.jpg")),
                "type": "image",
                "size": 1024,
                "hashes": {"sha256": "abc123"},
            }
        ]

    def is_available(self) -> bool:
        return True

    def process_batch(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "manifest": self.manifest,
            "routing": [
                {
                    "name": self.manifest[0]["name"],
                    "target_section": "section_8",
                    "engine_priority": ["easyocr"],
                }
            ],
            "errors": [],
            "processed_data": {},
        }


class StubPdfExtractionAdapter:
    def is_available(self) -> bool:
        return True

    def extract(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "result": {"files": files},
            "extracted_text": {entry.get("path", f"file_{idx}"): "text" for idx, entry in enumerate(files)},
            "errors": [],
        }


class StubReportGeneratorAdapter:
    def __init__(self) -> None:
        self.generated_payloads: List[Dict[str, Any]] = []
        self.exports: List[Dict[str, Any]] = []

    def is_available(self) -> bool:
        return True

    def generate(self, section_data: Any, report_type: str) -> Dict[str, Any]:
        sections: List[Dict[str, Any]] = []
        if isinstance(section_data, dict):
            for key, value in section_data.items():
                if isinstance(value, dict):
                    sections.append(
                        {
                            "section_id": value.get("section_id", key),
                            "title": value.get("title", key),
                            "content": value.get("content", ""),
                        }
                    )
        elif isinstance(section_data, list):
            for entry in section_data:
                if isinstance(entry, dict):
                    sections.append(entry)
        payload = {
            "cover_page": {
                "type": "cover_page",
                "content": f"{report_type} Report",
                "metadata": {"report_type": report_type},
            },
            "table_of_contents": {
                "type": "table_of_contents",
                "content": "\n".join(["TABLE OF CONTENTS", ""] + [s.get("title", "") for s in sections]),
                "metadata": {"total_sections": len(sections)},
            },
            "sections": sections,
            "disclosure_page": {
                "type": "disclosure_page",
                "content": "Disclosure",
                "metadata": {},
            },
            "metadata": {
                "report_type": report_type,
                "total_sections": len(sections),
            },
        }
        self.generated_payloads.append(payload)
        return payload

    def export(self, payload: Dict[str, Any], export_path: str, export_format: str = "PDF") -> Dict[str, Any]:
        Path(export_path).write_text(
            json.dumps({
                "format": export_format,
                "artifact": payload.get("metadata", {}).get("artifact"),
                "sections": [section.get("title") for section in payload.get("sections", [])],
            }, indent=2),
            encoding="utf-8",
        )
        export_info = {"path": export_path, "format": export_format}
        self.exports.append(export_info)
        return export_info


@pytest.fixture()
def mission_debrief_manager(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import importlib.util
    import sys
    import types

    module_path = Path(__file__).resolve().parents[1] / "Debrief" / "README" / "mission_debrief_manager.py"
    spec = importlib.util.spec_from_file_location("mission_debrief_manager_for_tests", module_path)
    mdm = importlib.util.module_from_spec(spec)
    assert spec.loader is not None

    for name in list(sys.modules.keys()):
        if name == "tools" or name.startswith("tools."):
            sys.modules.pop(name, None)

    tools_pkg = types.ModuleType("tools")
    sys.modules.setdefault("tools", tools_pkg)
    stub_classes = {
        "tools.evidence_pipeline_adapter": "EvidencePipelineAdapter",
        "tools.pdf_extraction_adapter": "PdfExtractionAdapter",
        "tools.api_manager_adapter": "ApiServiceAdapter",
        "tools.report_generator_adapter": "ReportGeneratorAdapter",
        "tools.digital_signature_adapter": "DigitalSignatureAdapter",
        "tools.watermark_adapter": "WatermarkAdapter",
        "tools.printing_adapter": "PrintingAdapter",
    }
    for module_name, class_name in stub_classes.items():
        module = types.ModuleType(module_name)
        setattr(module, class_name, type(class_name, (), {}))
        sys.modules[module_name] = module
        setattr(tools_pkg, module_name.split(".")[1], module)

    spec.loader.exec_module(mdm)

    fake_command_center = tmp_path / "Command Center"
    fake_command_center.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(mdm, "COMMAND_CENTER_ROOT", fake_command_center)
    monkeypatch.setattr(mdm.MissionDebriefManager, "_init_adapter", lambda self, name, factory, *args, **kwargs: None)
    monkeypatch.setattr(mdm.time, "sleep", lambda *_args, **_kwargs: None)

    manager = mdm.MissionDebriefManager(ecc=DummyECC(), bus=None, gateway=None)
    manager.root_install_directory = tmp_path
    manager.export_root = manager._ensure_directory(tmp_path / "DKI_Exports")
    manager.exports_dir = manager._ensure_directory(manager.export_root / "Depositions")

    manager.report_generator_adapter = StubReportGeneratorAdapter()
    manager.evidence_pipeline_adapter = StubEvidencePipelineAdapter()
    manager.pdf_extraction_adapter = StubPdfExtractionAdapter()
    manager.watermark_adapter = StubUnavailableAdapter()
    manager.digital_signature_adapter = StubUnavailableAdapter()
    manager.printing_adapter = StubUnavailableAdapter()
    manager.api_services_adapter = StubUnavailableAdapter()
    manager.osint_adapter = manager.api_services_adapter
    manager.template_system = None

    manager.refresh_tool_status()
    return manager



def test_deposition_catalog_exports_all_artifacts(mission_debrief_manager: Any, tmp_path: Path):
    manager = mission_debrief_manager

    sections = {
        f"section_{idx}": _make_section(f"section_{idx}", f"Section {idx}")
        for idx in range(1, 10)
    }
    report_data = {
        "case_id": "CASE001",
        "section_id": "section_1",
        "sections": sections,
        "evidence_files": [
            {"path": str(tmp_path / "doc.txt"), "name": "doc.txt", "type": "document"}
        ],
    }
    (tmp_path / "doc.txt").write_text("evidence", encoding="utf-8")

    options = {
        "export_report": True,
        "add_watermark": False,
        "digital_sign": False,
        "print_report": False,
    }

    result = manager.process_complete_report(report_data, options)

    catalog = result["deposition_catalog"]
    required_keys = {"final_report", "billing_summary", "evidence_manifest", "print_version", "export_log"}
    assert required_keys.issubset(catalog.keys())

    created_paths = {key: Path(path) for key, path in catalog.items()}
    for key, path in created_paths.items():
        assert path.exists(), f"expected artifact for {key}"
        content = path.read_text(encoding="utf-8")
        assert content.strip(), f"empty content for {key}"

    assert result["status"] == "ok"
    assert result["billing_summary_path"] == str(created_paths["billing_summary"])
    assert result["evidence_manifest_path"] == str(created_paths["evidence_manifest"])
    assert result["print_version_path"] == str(created_paths["print_version"])

    log_data = json.loads(Path(result["export_log"]).read_text(encoding="utf-8"))
    assert log_data["case_id"] == "CASE001"
    assert log_data["status"] == "ok"
    for step in ("billing_summary_exported", "evidence_manifest_exported", "print_version_exported", "export_log_recorded"):
        assert step in log_data["steps_completed"], f"missing {step} in log"
    for artifact_path in created_paths.values():
        assert str(artifact_path) in log_data["output_files"]
