"""
Initialization helper for The Librarian (Narrative Assembler).

Instantiates The Librarian and its dependencies:
- Narrative Assembler (core)
- Template Cache
- Document Processor  
- OSINT Engine
"""

from __future__ import annotations

from typing import Any, Optional
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
LIBRARIAN_PATH = CURRENT_DIR / "The Librarian"
if str(LIBRARIAN_PATH) not in sys.path:
    sys.path.insert(0, str(LIBRARIAN_PATH))

from narrative_assembler import NarrativeAssembler

# Import TOC production framework
MISSION_OPS_PATH = LIBRARIAN_PATH / "Mission_Ops"
if str(MISSION_OPS_PATH) not in sys.path:
    sys.path.insert(0, str(MISSION_OPS_PATH))

try:
    from section_toc_framework import SectionTOCFramework
except ImportError:
    SectionTOCFramework = None


def init_the_librarian(
    ecc: Optional[Any] = None,
    bus: Optional[Any] = None,
) -> NarrativeAssembler:
    """
    Instantiate The Librarian (Narrative Assembler) with the provided bus.
    
    The Librarian handles:
    - Narrative assembly from structured data
    - Court-safe language formatting
    - Template management
    - Section-aware content generation
    - Table of Contents generation
    """
    librarian = NarrativeAssembler(
        ecc=ecc,
        bus=bus
    )
    
    # Attach TOC production framework
    if SectionTOCFramework:
        librarian.toc_engine = SectionTOCFramework(gateway=None, bus=bus, ecc=ecc)
    
    return librarian


__all__ = ["init_the_librarian"]

