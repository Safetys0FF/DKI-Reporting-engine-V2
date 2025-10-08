# main_application.py — DKI System Bootstrap

import logging
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from bus_core import DKIReportBus

# Real modular controllers (internal names mapped correctly)
from extracted_the_warden import gateway_controller
from extracted_the_marshall import evidence_manager
from extracted_evidence_locker import evidence_index

LOGGER = logging.getLogger(__name__)
ROOT_DIR = Path(__file__).resolve().parents[3]
EVIDENCE_CHECKOUT_PATH = ROOT_DIR / "The Marshall" / "Evidence_Checkout" / "section_controller.py"
ANALYST_DECK_PATH = ROOT_DIR / "The Analyst Deck" / "deck_bus_listener.py"


def _load_module_from_path(qualname: str, module_path: Path):
    """Generic loader for runtime modules."""
    if not module_path.exists():
        LOGGER.warning("Module not found at %s", module_path)
        return None
    spec = spec_from_file_location(qualname, module_path)
    if not spec or not spec.loader:
        LOGGER.error("Unable to create module spec for %s", module_path)
        return None
    module = module_from_spec(spec)
    try:
        spec.loader.exec_module(module)  # type: ignore[attr-defined]
    except Exception as exc:
        LOGGER.error("Failed to load %s: %s", module_path.name, exc)
        return None
    return module


def _load_evidence_checkout_module():
    return _load_module_from_path("marshall_evidence_checkout", EVIDENCE_CHECKOUT_PATH)


def _load_analyst_deck_module():
    return _load_module_from_path("analyst_deck_bus_listener", ANALYST_DECK_PATH)


def launch():
    bus = DKIReportBus()

    # Inject core runtime modules into the bus
    bus.inject_module(gateway_controller)
    bus.inject_module(evidence_manager)
    bus.inject_module(evidence_index)

    evidence_checkout_module = _load_evidence_checkout_module()
    if evidence_checkout_module is not None:
        bus.inject_module(evidence_checkout_module)
    else:
        LOGGER.warning("Evidence Checkout controller not injected; continuing without section bridge")

    analyst_deck_module = _load_analyst_deck_module()
    if analyst_deck_module is not None:
        bus.inject_module(analyst_deck_module)
    else:
        LOGGER.warning("Analyst Deck listener not injected; Analyst Deck dashboards will use stale data")

    # Optional: emit a test signal
    bus.emit("boot_check", {"status": "online"})

    return bus


# If called directly — start the runtime
if __name__ == "__main__":
    bus = launch()
    print("\n[MAIN] Bus runtime launched. Listening for signals.")
