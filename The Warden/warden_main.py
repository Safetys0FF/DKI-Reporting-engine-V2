#!/usr/bin/env python3
"""Bootstrap entry point for the Warden control plane."""

import logging
from time import sleep

from warden_module import Warden

logger = logging.getLogger("Warden")
logging.basicConfig(level=logging.INFO)


def main() -> int:
    warden = Warden()
    if not warden.start():
        logger.error("Failed to start Warden Central Command System")
        return 1

    logger.info("Warden Central Command System ready")
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutdown signal received")
        warden.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
