"""
Initialization helper for Mission Debrief Manager.

Instantiates the Debrief Manager and its dependencies:
- Report Generator
- Digital Signature System
- Template Engine
- Watermark System
- Printing System
- OCR Flow Engine (from Processors)
"""

from __future__ import annotations

from typing import Any, Optional
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
README_PATH = CURRENT_DIR / "Debrief" / "README"
if str(README_PATH) not in sys.path:
    sys.path.insert(0, str(README_PATH))

# Import Processors tooling
CENTRAL_COMMAND_ROOT = CURRENT_DIR.parent.parent
PROCESSORS_PATH = CENTRAL_COMMAND_ROOT / "The War Room" / "Processors"
if str(PROCESSORS_PATH) not in sys.path:
    sys.path.insert(0, str(PROCESSORS_PATH))

# Import OCR Flow Engine from Processors
PROCESSORS_SOP_PATH = CENTRAL_COMMAND_ROOT / "The War Room" / "SOPs" / "READ FILES" / "Build Specs"
if str(PROCESSORS_SOP_PATH) not in sys.path:
    sys.path.insert(0, str(PROCESSORS_SOP_PATH))

try:
    from ocr_flow_engine import OCRFlowEngine
except ImportError:
    OCRFlowEngine = None

from mission_debrief_manager import MissionDebriefManager

# Import artifact production frameworks
PRODUCTIONS_PATH = CURRENT_DIR / "Debrief" / "productions"
if str(PRODUCTIONS_PATH) not in sys.path:
    sys.path.insert(0, str(PRODUCTIONS_PATH))

try:
    from section_cp_framework import SectionCPFramework
    from section_dp_framework import SectionDPFramework
except ImportError:
    SectionCPFramework = None
    SectionDPFramework = None


def init_debrief_manager(
    ecc: Optional[Any] = None,
    bus: Optional[Any] = None,
    gateway: Optional[Any] = None,
    librarian: Optional[Any] = None,
) -> MissionDebriefManager:
    """
    Instantiate the Mission Debrief Manager with the provided bus.
    
    The manager will initialize its own dependencies:
    - Report Generator (via adapter)
    - Digital Signature System
    - Template Engine
    - Watermark System
    - PDF Extraction tools
    - Artifact frameworks (Cover Page, Disclosure Page)
    """
    manager = MissionDebriefManager(
        ecc=ecc,
        bus=bus,
        gateway=gateway,
        librarian=librarian
    )
    
    # Attach OCR Flow Engine from Processors
    if OCRFlowEngine:
        manager.ocr_flow_engine = OCRFlowEngine()
    
    # Attach artifact production frameworks
    if SectionCPFramework:
        manager.cover_page_engine = SectionCPFramework(gateway=gateway, bus=bus, ecc=ecc)
    if SectionDPFramework:
        manager.disclosure_page_engine = SectionDPFramework(gateway=gateway, bus=bus, ecc=ecc)
    
    return manager


__all__ = ["init_debrief_manager"]

