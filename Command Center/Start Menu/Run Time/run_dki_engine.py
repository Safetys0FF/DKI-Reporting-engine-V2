#!/usr/bin/env python3
"""Hard-coded launcher wrapper for Start Menu shortcut."""
from pathlib import Path
import sys

BASE_DIR = Path(r"F:/DKI-Report-Engine/Report Engine")
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from launch_dki_engine import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
