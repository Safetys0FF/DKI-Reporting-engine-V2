"""
Pull helpers for the Warden control plane.

Centralises instantiation of the EcosystemController and GatewayController
so higher-level modules (e.g., `WardenModule`) can assemble the combined
system without duplicating constructor logic.
"""

from __future__ import annotations

from typing import Any, Optional

from ecosystem_controller import EcosystemController
from gateway_controller import GatewayController


def init_ecosystem_controller(bus: Optional[Any] = None) -> EcosystemController:
    """Instantiate the EcosystemController with the provided bus."""
    return EcosystemController(bus=bus)


def init_gateway_controller(
    ecosystem_controller: EcosystemController,
    bus: Optional[Any] = None,
) -> GatewayController:
    """Instantiate the GatewayController, wiring in the ecosystem controller."""
    return GatewayController(ecosystem_controller=ecosystem_controller, bus=bus)


__all__ = [
    "init_ecosystem_controller",
    "init_gateway_controller",
]
