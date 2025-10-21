"""Initializer for Section 1 Reverse Continuity tool."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_CURRENT_DIR = Path(__file__).resolve().parent
_TOOLKIT_PATH = _CURRENT_DIR.parent / "Tool kit" / "tools.py"

if str(_TOOLKIT_PATH) not in sys.path:
    sys.path.insert(0, str(_TOOLKIT_PATH))

from reverse_continuity_tool import ReverseContinuityTool  # type: ignore


def init_reverse_continuity(**_: Any) -> ReverseContinuityTool:
    """Return a configured ReverseContinuityTool instance."""

    return ReverseContinuityTool()


__all__ = ["init_reverse_continuity"]
