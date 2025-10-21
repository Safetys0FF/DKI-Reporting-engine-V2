"""Initializer for Section 6 body text switchboard."""

from __future__ import annotations

import importlib
from typing import Any, Callable


def init_section6_switchboard(**_: Any) -> Callable[[str], Any]:
    """Return a factory that creates BodyTextSwitchboard instances."""

    module = importlib.import_module("section_6_framework")

    def factory(mode: str) -> Any:
        return module.BodyTextSwitchboard(mode)

    return factory


__all__ = ["init_section6_switchboard"]
