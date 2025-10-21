"""Initializer for Section 1 mileage audit helper."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable

_CURRENT_DIR = Path(__file__).resolve().parent
_TOOLKIT_PATH = _CURRENT_DIR.parent / "Tool kit" / "tools.py"

if str(_TOOLKIT_PATH) not in sys.path:
    sys.path.insert(0, str(_TOOLKIT_PATH))

from mileage_tool_v_2 import audit_mileage  # type: ignore


def init_mileage_audit(**_: Any) -> Callable[..., Any]:
    """Return the mileage audit callable."""

    return audit_mileage


__all__ = ["init_mileage_audit"]
