"""Initializer for Section 1 North Star asset processor."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable

_CURRENT_DIR = Path(__file__).resolve().parent
_TOOLKIT_PATH = _CURRENT_DIR.parent / "Tool kit" / "tools.py"

if str(_TOOLKIT_PATH) not in sys.path:
    sys.path.insert(0, str(_TOOLKIT_PATH))

from northstar_protocol_tool import process_assets  # type: ignore


def init_northstar_protocol(**_: Any) -> Callable[..., Any]:
    """Return the North Star process_assets callable."""

    return process_assets


__all__ = ["init_northstar_protocol"]
