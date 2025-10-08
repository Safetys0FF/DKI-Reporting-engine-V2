#!/usr/bin/env python3
"""
Auth Manager – issues/validates short-lived case-bound tokens (scaffold).
Defaults to permissive mode until enabled.
"""
from __future__ import annotations
import json, secrets, string
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

DEV_TRACK = Path(r"F:\The Central Command\The War Room\dev_tracking")
TOKENS = DEV_TRACK / "auth_tokens"
TOKENS.mkdir(parents=True, exist_ok=True)

def _now_iso(): return datetime.utcnow().isoformat() + "Z"
def _token(): return "".join(secrets.choice(string.ascii_letters+string.digits) for _ in range(32))

def _path(token_id: str) -> Path: return TOKENS / f"{token_id}.json"
def _write(path: Path, data: Dict[str, Any]): path.write_text(json.dumps(data, indent=2), encoding="utf-8")
def _read(path: Path) -> Optional[Dict[str,Any]]:
    if not path.exists(): return None
    try: return json.loads(path.read_text(encoding="utf-8"))
    except Exception: return None

def issue_token(operator_id: str, case_id: str, role: str, hours: int = 24) -> Dict[str, Any]:
    token_id = _token()
    payload = {
        "token_id": token_id,
        "operator_id": operator_id,
        "case_id": case_id,
        "role": role,
        "issued": _now_iso(),
        "expires": (datetime.utcnow()+timedelta(hours=hours)).isoformat()+"Z",
        "status": "active"
    }
    _write(_path(token_id), payload)
    return payload

def validate_token(token_id: str, case_id: Optional[str] = None) -> Optional[Dict[str,Any]]:
    data = _read(_path(token_id))
    if not data or data.get("status") != "active": return None
    if case_id and data.get("case_id") != case_id: return None
    # expiry soft-check (permissive by default)
    try:
        exp = datetime.fromisoformat(data["expires"].replace("Z",""))
        if exp < datetime.utcnow(): return None
    except Exception:
        pass
    return data

def revoke_token(token_id: str, reason: str = "manual") -> bool:
    data = _read(_path(token_id))
    if not data: return False
    data["status"] = "revoked"
    data["revoked_at"] = _now_iso()
    data["revoked_reason"] = reason
    _write(_path(token_id), data)
    return True
