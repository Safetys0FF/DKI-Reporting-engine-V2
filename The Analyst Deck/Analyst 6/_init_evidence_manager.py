"""Initializer for Section 6 Evidence Manager dependency."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_CURRENT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _CURRENT_DIR.parent.parent
_MARSHALL_PATH = _REPO_ROOT / "The Marshall"

if str(_MARSHALL_PATH) not in sys.path:
    sys.path.insert(0, str(_MARSHALL_PATH))

from evidence_manager import EvidenceManager  # type: ignore


def init_evidence_manager(**kwargs: Any) -> EvidenceManager:
    """Return a Marshall EvidenceManager wired with provided bus/gateway."""

    return EvidenceManager(
        bus=kwargs.get("bus"),
        gateway=kwargs.get("gateway"),
    )


__all__ = ["init_evidence_manager"]
