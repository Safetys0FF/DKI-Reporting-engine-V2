"""Initializer for Section 1 Tesseract OCR helper."""

from __future__ import annotations

from dataclasses import dataclass
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from PIL import Image
import pytesseract


@dataclass
class TesseractEngine:
    """Thin wrapper around pytesseract for Section 1 assets."""

    tessdata_dir: Optional[Path] = None

    def __post_init__(self) -> None:
        if self.tessdata_dir:
            os.environ.setdefault("TESSDATA_PREFIX", str(self.tessdata_dir))

    def extract_text(self, file_path: str) -> Dict[str, Any]:
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        blocks = []
        for idx, content in enumerate(data.get("text", [])):
            if not content.strip():
                continue
            blocks.append(
                {
                    "text": content,
                    "confidence": data.get("conf", [""])[idx],
                    "left": data.get("left", [""])[idx],
                    "top": data.get("top", [""])[idx],
                    "width": data.get("width", [""])[idx],
                    "height": data.get("height", [""])[idx],
                }
            )
        return {
            "engine_used": "tesseract",
            "text": text,
            "text_blocks": blocks,
        }


def init_tesseract(**kwargs: Any) -> TesseractEngine:
    """Return a TesseractEngine configured for Section 1."""

    tessdata = kwargs.get("tessdata_dir")
    if isinstance(tessdata, str):
        tessdata_path: Optional[Path] = Path(tessdata)
    else:
        tessdata_path = None
    return TesseractEngine(tessdata_dir=tessdata_path)


__all__ = ["init_tesseract", "TesseractEngine"]
