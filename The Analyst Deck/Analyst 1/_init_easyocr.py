"""Initializer for Section 1 EasyOCR fallback."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import easyocr


@dataclass
class EasyOCREngine:
    """Wrapper around easyocr.Reader."""

    languages: Sequence[str]
    gpu: bool = False

    def __post_init__(self) -> None:
        self.reader = easyocr.Reader(list(self.languages), gpu=self.gpu)

    def extract_text(self, file_path: str) -> Dict[str, Any]:
        results = self.reader.readtext(file_path)
        blocks: List[Dict[str, Any]] = []
        for bbox, text, confidence in results:
            if not text:
                continue
            blocks.append(
                {
                    "text": text,
                    "confidence": confidence,
                    "bbox": bbox,
                }
            )
        return {
            "engine_used": "easyocr",
            "text_blocks": blocks,
            "text": " ".join(block["text"] for block in blocks),
        }


def init_easyocr(**kwargs: Any) -> EasyOCREngine:
    """Return an EasyOCREngine configured for English text."""

    languages = kwargs.get("languages") or ["en"]
    gpu = bool(kwargs.get("gpu", False))
    return EasyOCREngine(languages=languages, gpu=gpu)


__all__ = ["init_easyocr", "EasyOCREngine"]
