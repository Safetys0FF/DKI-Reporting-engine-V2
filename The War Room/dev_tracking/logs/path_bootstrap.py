"""Utility helpers to place the repository root on sys.path for dev_tracking tools."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterable, Optional

_MARKERS: tuple[tuple[str, ...], ...] = (
    ("Gateway", "gateway_controller.py"),
    ("Processors", "document_processor.py"),
    ("UI", "main_application.py"),
)



def _iter_candidates(start: Path) -> Iterable[Path]:
    current = start.resolve()
    yield current
    yield from current.parents



def _has_marker(candidate: Path) -> bool:
    for parts in _MARKERS:
        target = candidate.joinpath(*parts)
        if target.exists():
            return True
    return False



def detect_repo_root(start: Optional[Path] = None) -> Path:
    """Locate the project root by walking up from *start* until a marker file exists."""
    start_path = (start or Path(__file__)).resolve()
    for candidate in _iter_candidates(start_path):
        if _has_marker(candidate):
            return candidate
    # Fallback: assume dev_tracking sits two levels below repo root
    return Path(__file__).resolve().parents[2]



def _append_sys_path(path: Path) -> None:
    path_str = str(path)
    if path.exists() and path_str not in sys.path:
        sys.path.insert(0, path_str)



def bootstrap_paths(current_file: Path | str) -> Path:
    """Ensure both the script directory and repository root are importable."""
    current_path = Path(current_file).resolve()
    _append_sys_path(current_path.parent)

    repo_root = detect_repo_root(current_path)
    _append_sys_path(repo_root)

    # Core subsystem directories that expose top-level modules
    subsystem_dirs = [
        repo_root / "Processors",
        repo_root / "Tools",
        repo_root / "UI",
        repo_root / "Gateway",
        repo_root / "Plugins",
        repo_root / "CoreSystem",
        repo_root / "engine_map_files",
        repo_root / "dev_tracking",
        repo_root / "CoreSystem" / "UI",
        repo_root / "CoreSystem" / "Gateway",
        repo_root / "CoreSystem" / "Processors",
        repo_root / "CoreSystem" / "Tools",
    ]
    for subdir in subsystem_dirs:
        _append_sys_path(subdir)

    tesseract_exe = repo_root / "Processors" / "tesseract.exe"
    if tesseract_exe.exists():
        tesseract_dir = str(tesseract_exe.parent)
        env_dirs = os.environ.get("PATH", "").split(os.pathsep)
        if tesseract_dir not in env_dirs:
            os.environ["PATH"] = os.pathsep.join([tesseract_dir] + env_dirs)

    return repo_root
