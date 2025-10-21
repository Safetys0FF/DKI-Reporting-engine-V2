"""Initializer for Section 4 document validation suite."""

from __future__ import annotations

import importlib
from typing import Any


def init_section4_document_validator(**_: Any):
    """Return a DocumentValidationSuite instance."""

    module = importlib.import_module("section_4_framework")
    Validator = getattr(module, "DocumentValidationSuite")
    return Validator()


__all__ = ["init_section4_document_validator"]
