r"""
UI Components - Modular GUI widgets for Central Command
Location: F:\The Central Command\Command Center\UI\components

Reusable tkinter-based components for the Enhanced GUI.
"""

import logging

logger = logging.getLogger(__name__)

from .system_health_dashboard import SystemHealthDashboard
from .case_management_panel import CaseManagementPanel
from .evidence_panel import EvidencePanel
from .file_drop_zone import FileDropZone

try:  # Optional dependency: requires 'requests'
    from .api_status_panel import APIStatusPanel  # type: ignore
except Exception as exc:  # pragma: no cover - optional component path
    APIStatusPanel = None  # type: ignore
    logger.warning("APIStatusPanel unavailable: %s", exc)

__all__ = [
    'SystemHealthDashboard',
    'CaseManagementPanel',
    'EvidencePanel',
    'FileDropZone',
]

if APIStatusPanel is not None:
    __all__.append('APIStatusPanel')

