#!/usr/bin/env python3
"""
Baseline smoke test for the Unified Diagnostic System (UDS).

Purpose:
    - Bring the diagnostic core online in primary CAN mode.
    - Confirm the bus connection and communicator registration.
    - Exercise a minimal status call, then shut the system down cleanly.

This script is intentionally lightweight so it can be used as the
first-run system initialization check before heavier protocol suites.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Ensure the UDS package is importable when the script is invoked directly.
CURRENT_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = CURRENT_DIR.parents[2].resolve()  # points at diagnostic_manager
package_path = str(PACKAGE_ROOT)
if package_path not in sys.path:
    sys.path.insert(0, package_path)


def run_baseline() -> bool:
    print("=" * 70)
    print("UNIFIED DIAGNOSTIC SYSTEM - BASELINE SMOKE TEST")
    print("=" * 70)

    print(f"[INFO] Using UDS package root: {package_path}")

    try:
        from Unified_diagnostic_system import UnifiedDiagnosticSystem  # type: ignore
    except ImportError as exc:
        print(f"[FAIL] Unable to import UnifiedDiagnosticSystem: {exc}")
        return False

    uds = UnifiedDiagnosticSystem()
    print("[OK] UnifiedDiagnosticSystem instantiated.")

    bus_status = uds.get_bus_status()
    bus_available = bus_status.get("bus_available", False)
    bus_connected = bus_status.get("bus_connected", False)
    registered_addresses = bus_status.get("registered_addresses", [])

    print("\n[CHECK] CAN-BUS status snapshot:")
    print(f"  - Bus available : {bus_available}")
    print(f"  - Bus connected : {bus_connected}")
    print(f"  - Registered addresses : {registered_addresses}")

    if not bus_available or not bus_connected:
        print("[FAIL] CAN-BUS not available/connected; baseline test cannot continue.")
        return False

    print("\n[STEP] Launching diagnostic system (smoke baseline mode)...")
    try:
        uds.launch_diagnostic_system(smoke_mode=True)
        print("[OK] Diagnostic system launch returned successfully.")
    except Exception as exc:  # pragma: no cover - defensive logging
        print(f"[FAIL] Diagnostic system launch raised an exception: {exc}")
        return False

    status = uds.get_unified_status()
    monitoring_active = status.get("monitoring_active")
    registered_systems = status.get("registered_systems")
    print("\n[CHECK] Unified status summary:")
    print(f"  - Monitoring active : {monitoring_active}")
    print(f"  - Registered systems: {registered_systems}")

    core_module = getattr(uds, "core", None)
    comms_module = getattr(uds, "comms", None)

    if core_module is None or comms_module is None:
        print("[FAIL] Core or Comms module missing after launch; aborting baseline.")
        uds.shutdown_diagnostic_system()
        return False

    print(f"[OK] Core module online: {type(core_module).__name__}")
    print(f"[OK] Comms module online: {type(comms_module).__name__}")

    print("\n[STEP] Shutting down diagnostic system...")
    try:
        uds.shutdown_diagnostic_system()
        print("[OK] Diagnostic system shutdown completed.")
    except Exception as exc:  # pragma: no cover - defensive logging
        print(f"[WARN] Shutdown raised an exception: {exc}")

    print("\n" + "=" * 70)
    print("[PASS] Baseline smoke test completed successfully.")
    print("=" * 70)
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = run_baseline()
    if not success:
        sys.exit(1)
