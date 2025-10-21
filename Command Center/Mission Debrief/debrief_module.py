#!/usr/bin/env python3
"""
DebriefModule - shell wrapper for Mission Debrief Manager and Librarian.

This scaffold creates a single point of contact for the report finalisation
stack (cover page, disclosures, narratives) without altering current
behaviour.  It keeps references to the live Mission Debrief Manager and
Librarian instances and exposes placeholders for the upcoming fault relay
and lifecycle management.

No runtime wiring is changed – the existing modules continue to register
their own CAN bus communicators.  The wrapper simply prepares a consistent
surface so that future refactors can move the orchestration responsibilities
here.
"""

from __future__ import annotations

import logging
from typing import Optional, Any

try:
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'Data Bus', 'Bus Core Design'))
    from universal_communicator import UniversalCommunicator  # type: ignore
except ImportError:  # pragma: no cover
    UniversalCommunicator = None  # type: ignore


class DebriefModule:
    """Container for Mission Debrief Manager + Librarian coordination."""

    MODULE_ADDRESS = "3-1"

    def __init__(
        self,
        *,
        bus: Optional[Any] = None,
        communicator: Optional[Any] = None,
    ) -> None:
        self.logger = logging.getLogger("DebriefModule")
        self.bus = bus
        self.communicator = communicator

        # Actual components are attached by the existing boot logic.
        self.debrief_manager: Optional[Any] = None
        self.librarian: Optional[Any] = None

        if self.communicator is None and bus and UniversalCommunicator:
            self.logger.debug(
                "DebriefModule ready to assume CAN ownership of %s when "
                "migration work begins.", self.MODULE_ADDRESS
            )

    # ------------------------------------------------------------------ #
    # Attachment helpers
    # ------------------------------------------------------------------ #
    def attach_debrief_manager(self, manager: Any) -> None:
        """Keep a reference to the Mission Debrief Manager."""
        self.debrief_manager = manager
        self.logger.debug("Mission Debrief Manager attached to DebriefModule.")

    def attach_librarian(self, librarian: Any) -> None:
        """Keep a reference to the Librarian narrative assembler."""
        self.librarian = librarian
        self.logger.debug("Librarian attached to DebriefModule.")

    # ------------------------------------------------------------------ #
    # Fault relay scaffold
    # ------------------------------------------------------------------ #
    def relay_fault(self, section_address: str, fault_payload: dict) -> None:
        """
        Placeholder fault relay.

        Future work will forward faults for cover / TOC / disclosure sections
        through this module.  For now we log the request to verify wiring.
        """
        self.logger.debug(
            "DebriefModule relay_fault invoked for %s (payload keys: %s)",
            section_address,
            list(fault_payload.keys()),
        )

    # ------------------------------------------------------------------ #
    # Lifecycle hooks
    # ------------------------------------------------------------------ #
    def start(self) -> None:
        """Stub lifecycle hook."""
        self.logger.debug("DebriefModule.start() invoked (no-op placeholder).")

    def stop(self) -> None:
        """Stub lifecycle hook."""
        self.logger.debug("DebriefModule.stop() invoked (no-op placeholder).")

