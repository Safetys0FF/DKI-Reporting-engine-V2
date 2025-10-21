"""Initializer for the Section 1 renderer artifact."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_CURRENT_DIR = Path(__file__).resolve().parent
_TOOLKIT_PATH = _CURRENT_DIR.parent / "Tool kit" / "tools.py"

if str(_TOOLKIT_PATH) not in sys.path:
    sys.path.insert(0, str(_TOOLKIT_PATH))

from section_1_gateway import Section1Renderer  # type: ignore


def init_section_renderer(**_: Any) -> Section1Renderer:
    """Return a Section 1 renderer instance."""

    return Section1Renderer()


__all__ = ["init_section_renderer"]
