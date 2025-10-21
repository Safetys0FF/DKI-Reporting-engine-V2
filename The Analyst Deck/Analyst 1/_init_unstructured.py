"""Initializer for Section 1 Unstructured document processor."""

from __future__ import annotations

from dataclasses import dataclass
import sys
from pathlib import Path
from typing import Any, Dict, List

from unstructured.partition.auto import partition


@dataclass
class UnstructuredEngine:
    """Wrapper around unstructured.partition.auto.partition."""

    def partition(self, file_path: str) -> List[Dict[str, Any]]:
        elements = partition(filename=file_path, strategy="fast")
        output: List[Dict[str, Any]] = []
        for element in elements:
            text = getattr(element, "text", "")
            if not text:
                continue
            output.append(
                {
                    "category": element.category,
                    "text": text,
                    "metadata": getattr(element, "metadata", None),
                }
            )
        return output


def init_unstructured(**_: Any) -> UnstructuredEngine:
    """Return an UnstructuredEngine instance."""

    return UnstructuredEngine()


__all__ = ["init_unstructured", "UnstructuredEngine"]
