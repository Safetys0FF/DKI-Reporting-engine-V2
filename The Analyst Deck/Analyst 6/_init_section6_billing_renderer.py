"""Initializer for Section 6 billing renderer."""

from __future__ import annotations

import importlib
from typing import Any


def init_section6_billing_renderer(**_: Any):
    """Return the Section6BillingRenderer class."""

    module = importlib.import_module("section_6_framework")
    return module.Section6BillingRenderer


__all__ = ["init_section6_billing_renderer"]
