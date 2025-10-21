"""Initializers for Analyst Deck tool dependencies.

Each initializer returns a ready-to-use callable or object sourced from the
authoritative War Room / Analyst Deck tool implementations. Centralising the
logic keeps section engines lightweight while ensuring all tooling is loaded
through a common entry-point in line with UDS requirements.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable, Dict


_ROOT = Path(__file__).resolve().parent
_TOOLKIT_DIR = _ROOT / "Tool kit" / "tools.py"
_COMMAND_CENTER_DATA_BUS = _ROOT.parent / "Command Center" / "Data Bus"
_MARSHALL_DIR = _ROOT.parent / "The Marshall"

for _path in (_TOOLKIT_DIR, _COMMAND_CENTER_DATA_BUS, _MARSHALL_DIR):
    path_str = str(_path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


def init_evidence_manager(**kwargs: Any) -> Any:
    """Return an EvidenceManager instance wired for analyst sections."""
    from evidence_manager import EvidenceManager  # type: ignore

    bus = kwargs.get("bus")
    gateway = kwargs.get("gateway")
    return EvidenceManager(bus=bus, gateway=gateway)


def init_northstar_protocol_tool(**kwargs: Any) -> Callable[..., Any]:
    """Return the North Star asset processor."""
    from northstar_protocol_tool import process_assets  # type: ignore

    return process_assets


def init_cochran_match_tool(**kwargs: Any) -> Callable[..., Any]:
    """Return the Cochran identity verification helper."""
    from cochran_match_tool import verify_identity  # type: ignore

    return verify_identity


def init_reverse_continuity_tool(**kwargs: Any) -> Any:
    """Return a Reverse Continuity tool instance."""
    from reverse_continuity_tool import ReverseContinuityTool  # type: ignore

    return ReverseContinuityTool()


def init_metadata_tool(**kwargs: Any) -> Callable[..., Any]:
    """Return the metadata processing helper."""
    from metadata_tool_v_5 import process_zip  # type: ignore

    return process_zip


def init_mileage_tool(**kwargs: Any) -> Callable[..., Any]:
    """Return the mileage auditing helper."""
    from mileage_tool_v_2 import audit_mileage  # type: ignore

    return audit_mileage


def init_section_renderer(section_name: str) -> Callable[..., Any]:
    """Return a renderer factory for the given section."""
    mapping: Dict[str, str] = {
        "section_1": "section_1_gateway",
        "section_2": "section_2_renderer",
        "section_3": "section_3_renderer",
        "section_4": "section_4_renderer",
        "section_5": "section_5_renderer",
        "section_6": "section_6_billing",
        "section_7": "section_7_renderer",
        "section_8": "section_8_renderer",
    }
    module_name = mapping.get(section_name)
    if not module_name:
        raise ValueError(f"No renderer registered for {section_name}")

    module = __import__(module_name, fromlist=["SectionRenderer"])
    renderer_cls = getattr(module, "SectionRenderer", None)
    if renderer_cls is None:
        renderer_cls = getattr(module, "Section1Renderer", None)
    if renderer_cls is None:
        raise AttributeError(f"{module_name} does not expose a SectionRenderer")
    return renderer_cls


__all__ = [
    "init_evidence_manager",
    "init_northstar_protocol_tool",
    "init_cochran_match_tool",
    "init_reverse_continuity_tool",
    "init_metadata_tool",
    "init_mileage_tool",
    "init_section_renderer",
]
