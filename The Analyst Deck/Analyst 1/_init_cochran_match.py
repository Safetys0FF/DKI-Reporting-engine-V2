"""Initializer for Section 1 Cochran identity verification."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable

_CURRENT_DIR = Path(__file__).resolve().parent
_TOOLKIT_PATH = _CURRENT_DIR.parent / "Tool kit" / "tools.py"

if str(_TOOLKIT_PATH) not in sys.path:
    sys.path.insert(0, str(_TOOLKIT_PATH))

from cochran_match_tool import verify_identity  # type: ignore


def init_cochran_match(**_: Any) -> Callable[..., Any]:
    """Return the Cochran verify_identity callable."""

    return verify_identity


__all__ = ["init_cochran_match"]
