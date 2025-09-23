"""Compatibility wrapper to expose bootstrap helpers to dev_tracking tools."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve().parent / "logs" / "path_bootstrap.py"
_spec = importlib.util.spec_from_file_location("dev_tracking_logs_path_bootstrap", _MODULE_PATH)
_module = importlib.util.module_from_spec(_spec)
if _spec and _spec.loader:
    _spec.loader.exec_module(_module)  # type: ignore[attr-defined]
else:
    raise ImportError(f"Unable to load path bootstrap module from {_MODULE_PATH}")

bootstrap_paths = _module.bootstrap_paths  # type: ignore[attr-defined]
detect_repo_root = _module.detect_repo_root  # type: ignore[attr-defined]
