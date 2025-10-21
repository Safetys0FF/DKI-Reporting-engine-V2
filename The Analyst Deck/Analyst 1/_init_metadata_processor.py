"""Initializer for Section 1 metadata processing helper."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable

_CURRENT_DIR = Path(__file__).resolve().parent
_TOOLKIT_PATH = _CURRENT_DIR.parent / "Tool kit" / "tools.py"

if str(_TOOLKIT_PATH) not in sys.path:
    sys.path.insert(0, str(_TOOLKIT_PATH))

from metadata_tool_v_5 import process_zip  # type: ignore


def init_metadata_processor(**_: Any) -> Callable[..., Any]:
    """Return the metadata ZIP processing callable."""

    return process_zip


__all__ = ["init_metadata_processor"]
