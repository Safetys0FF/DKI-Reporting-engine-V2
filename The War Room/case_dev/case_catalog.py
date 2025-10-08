"""Case catalog persistence helpers for Central Command GUI."""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT_DIR = Path(__file__).resolve().parents[2]
UI_DIR = ROOT_DIR / "Command Center" / "UI"
if str(UI_DIR) not in sys.path:
    sys.path.insert(0, str(UI_DIR))

from case_session import CaseSession

CASE_DEV_ROOT = Path(__file__).resolve().parent
CATALOG_INDEX_FILE = CASE_DEV_ROOT / "catalog_index.json"
SESSION_FILENAME = "session.json"
ARTIFACTS_FILENAME = "artifacts.json"
METADATA_FILENAME = "metadata.json"

LOCK_FILENAME = "lock.json"

_SANITIZE_PATTERN = re.compile(r"[^A-Za-z0-9_-]+")


def _sanitize_case_id(case_id: str) -> str:
    """Convert a case id to a filesystem-friendly slug."""
    case_id = case_id.strip()
    if not case_id:
        raise ValueError("case_id cannot be empty")
    sanitized = _SANITIZE_PATTERN.sub("_", case_id)
    return sanitized


def _case_folder(case_id: str) -> Path:
    return CASE_DEV_ROOT / _sanitize_case_id(case_id)


def _load_index() -> Dict[str, Any]:
    if CATALOG_INDEX_FILE.exists():
        try:
            return json.loads(CATALOG_INDEX_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"cases": {}}


def _save_index(index: Dict[str, Any]) -> None:
    CATALOG_INDEX_FILE.write_text(json.dumps(index, indent=2, sort_keys=True), encoding="utf-8")


def ensure_case_folder(case_id: str) -> Path:
    folder = _case_folder(case_id)
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _session_path(case_id: str) -> Path:
    return ensure_case_folder(case_id) / SESSION_FILENAME


def _artifacts_path(case_id: str) -> Path:
    return ensure_case_folder(case_id) / ARTIFACTS_FILENAME


def _metadata_path(case_id: str) -> Path:
    return ensure_case_folder(case_id) / METADATA_FILENAME


def _lock_path(case_id: str) -> Path:
    return ensure_case_folder(case_id) / LOCK_FILENAME


def save_session(session: CaseSession, *, artifacts: Optional[Dict[str, Any]] = None) -> None:
    """Persist the current session state and catalog entry."""
    session.mark_saved(status=session.status)
    folder = ensure_case_folder(session.case_id)
    _session_path(session.case_id).write_text(json.dumps(session.to_dict(), indent=2), encoding="utf-8")

    approved_sections, total_sections = session.approval_counts()
    metadata = {
        "case_id": session.case_id,
        "investigator": session.investigator,
        "subcontractor": session.subcontractor,
        "contract_signed": session.contract_signed.isoformat() if session.contract_signed else None,
        "status": session.status,
        "created_at": session.created_at.isoformat(),
        "last_saved": session.last_saved.isoformat(),
        "export_root": session.export_settings.export_root,
        "approved_sections": approved_sections,
        "total_sections": total_sections,
    }
    _metadata_path(session.case_id).write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    if artifacts is not None:
        _artifacts_path(session.case_id).write_text(json.dumps(artifacts, indent=2), encoding="utf-8")

    index = _load_index()
    cases = index.setdefault("cases", {})
    cases[session.case_id] = {
        "folder": str(folder),
        "status": session.status,
        "investigator": session.investigator,
        "subcontractor": session.subcontractor,
        "contract_signed": metadata["contract_signed"],
        "last_saved": metadata["last_saved"],
        "export_root": metadata["export_root"],
        "approved_sections": metadata.get("approved_sections"),
        "total_sections": metadata.get("total_sections"),
    }
    _save_index(index)


def load_session(case_id: str) -> Optional[CaseSession]:
    session_file = _case_folder(case_id) / SESSION_FILENAME
    if not session_file.exists():
        return None
    payload = json.loads(session_file.read_text(encoding="utf-8"))
    return CaseSession.from_dict(payload)


def load_metadata(case_id: str) -> Optional[Dict[str, Any]]:
    meta_file = _case_folder(case_id) / METADATA_FILENAME
    if not meta_file.exists():
        return None
    return json.loads(meta_file.read_text(encoding="utf-8"))


def load_artifacts(case_id: str) -> Optional[Dict[str, Any]]:
    art_file = _case_folder(case_id) / ARTIFACTS_FILENAME
    if not art_file.exists():
        return None
    return json.loads(art_file.read_text(encoding="utf-8"))


def list_cases(*, status: Optional[str] = None) -> List[Dict[str, Any]]:
    index = _load_index()
    results: List[Dict[str, Any]] = []
    for case_id, entry in index.get("cases", {}).items():
        if status and entry.get("status") != status:
            continue
        results.append({"case_id": case_id, **entry})
    results.sort(key=lambda item: item.get("last_saved", ""), reverse=True)
    return results


def delete_case(case_id: str, *, remove_files: bool = False) -> None:
    index = _load_index()
    if case_id in index.get("cases", {}):
        index["cases"].pop(case_id)
        _save_index(index)
    if remove_files:
        folder = _case_folder(case_id)
        if folder.exists():
            for child in folder.iterdir():
                if child.is_file():
                    child.unlink(missing_ok=True)
            try:
                folder.rmdir()
            except OSError:
                pass


def touch_case(case_id: str) -> None:
    """Update the index timestamp when external work occurs."""
    index = _load_index()
    cases = index.setdefault("cases", {})
    entry = cases.setdefault(case_id, {"folder": str(ensure_case_folder(case_id))})
    entry["last_saved"] = datetime.utcnow().isoformat()
    _save_index(index)


def get_lock_info(case_id: str) -> Optional[Dict[str, Any]]:
    lock_file = _lock_path(case_id)
    if not lock_file.exists():
        return None
    try:
        return json.loads(lock_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def set_lock_info(case_id: str, payload: Dict[str, Any]) -> None:
    lock_file = _lock_path(case_id)
    lock_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def clear_lock(case_id: str) -> None:
    lock_file = _lock_path(case_id)
    lock_file.unlink(missing_ok=True)



__all__ = [
    "save_session",
    "load_session",
    "load_metadata",
    "load_artifacts",
    "list_cases",
    "delete_case",
    "touch_case",
    "ensure_case_folder",
    "CASE_DEV_ROOT",
    "get_lock_info",
    "set_lock_info",
    "clear_lock",
]
