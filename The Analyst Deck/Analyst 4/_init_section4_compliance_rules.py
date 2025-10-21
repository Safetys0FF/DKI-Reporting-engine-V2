"""Initializer for Section 4 compliance rule engine."""

from __future__ import annotations

import importlib
from typing import Any


def init_section4_compliance_rules(**_: Any):
    """Return a ComplianceRuleEngine instance."""

    module = importlib.import_module("section_4_framework")
    Engine = getattr(module, "ComplianceRuleEngine")
    return Engine()


__all__ = ["init_section4_compliance_rules"]
