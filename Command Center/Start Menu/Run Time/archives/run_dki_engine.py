#!/usr/bin/env python3
"""Launcher wrapper for Central Command Start Menu."""
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from main_application import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
