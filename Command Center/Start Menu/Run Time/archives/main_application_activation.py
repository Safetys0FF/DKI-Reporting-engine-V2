# main_application.py — DKI System Bootstrap

from bus_core import DKIReportBus

# Real modular controllers (internal names mapped correctly)
from extracted_the_warden import gateway_controller
from extracted_the_marshall import evidence_manager
from extracted_evidence_locker import evidence_index

# Optional: more modules to inject
# from controllers import narrative_controller, ecc_controller, etc.


def launch():
    bus = DKIReportBus()

    # Inject core runtime modules into the bus
    bus.inject_module(gateway_controller)
    bus.inject_module(evidence_manager)
    bus.inject_module(evidence_index)

    # Optional: emit a test signal
    bus.emit("boot_check", {"status": "online"})

    return bus


# If called directly — start the runtime
if __name__ == "__main__":
    bus = launch()
    print("\n[MAIN] Bus runtime launched. Listening for signals.")
