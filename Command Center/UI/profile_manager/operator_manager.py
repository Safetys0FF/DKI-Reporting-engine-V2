#!/usr/bin/env python3
"""
Operator Manager – profile CRUD, case assignment, timebox/extend/revoke,
and policy evaluation (defers to access_rules.json). Defaults to permissive
mode so it doesn’t block current development.
"""
from __future__ import annotations
import json, secrets, string
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List

BASE_DIR = Path(__file__).resolve().parent
INSTALL_ROOT = BASE_DIR.parents[3]
DEV_TRACK = INSTALL_ROOT / "The War Room" / "dev_tracking"
DEFAULT_RULES = BASE_DIR / "profile_access_rules.json"
RULES_PATH = DEFAULT_RULES if DEFAULT_RULES.exists() else DEV_TRACK / "access_rules.json"
OPERATORS_DIR = DEV_TRACK / "operators"
OPERATORS_DIR.mkdir(parents=True, exist_ok=True)

# ---------- Model ----------
@dataclass
class OperatorProfile:
    operator_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role: str = "field_operator"
    status: str = "active"     # active | inactive | revoked
    assigned_cases: Optional[List[str]] = None
    access: Optional[Dict[str, Any]] = None  # issued/expires/reactivations
    audit_log: Optional[List[Dict[str, Any]]] = None

    def to_dict(self) -> Dict[str, Any]:
        out = asdict(self)
        out["assigned_cases"] = self.assigned_cases or []
        out["access"] = self.access or {}
        out["audit_log"] = self.audit_log or []
        return out

# ---------- Utilities ----------
def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"

def _id(prefix: str) -> str:
    token = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
    return f"{prefix}-{token}"

def _read_json(path: Path, default: Any) -> Any:
    if not path.exists(): return default
    try: return json.loads(path.read_text(encoding="utf-8"))
    except Exception: return default

def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

# ---------- Rules ----------
class AccessRules:
    def __init__(self, path: Path = RULES_PATH):
        self.path = path
        self.reload()

    def reload(self):
        data = _read_json(self.path, {})
        self.enabled = bool(data.get("enabled", False))
        self.default_expiration_hours = int(data.get("default_expiration_hours", 24))
        self.multi_operator_locking = bool(data.get("multi_operator_locking", False))
        self.roles: Dict[str, Dict[str, bool]] = data.get("roles", {})
        self.actions: Dict[str, List[str]] = data.get("actions", {})

    def is_allowed(self, role: str, action: str) -> bool:
        if not self.enabled:
            return True  # permissive until enforcement is turned on
        # action mapping first
        allowed_roles = self.actions.get(action)
        if allowed_roles is not None:
            return role in allowed_roles
        # fall back to role capability if action not mapped
        caps = self.roles.get(role, {})
        flag = {
            "approve_section": "can_approve",
            "export_report": "can_export",
            "upload_evidence": "can_upload",
            "delete_evidence": "can_delete",
            "assign_operator": "can_assign_operators",
            "lock_case": "can_lock_case",
            "process_evidence": "can_upload",
            "add_field_notes": "can_upload"  # treat notes as upload-like
        }.get(action)
        return bool(flag and caps.get(flag, False))

# ---------- Manager ----------
class OperatorManager:
    def __init__(self, rules: Optional[AccessRules] = None):
        self.rules = rules or AccessRules()

    # ---- Profile CRUD ----
    def _path(self, operator_id: str) -> Path:
        return OPERATORS_DIR / f"{operator_id}.json"

    def create(self, *, name: str, email: str | None = None, phone: str | None = None,
               role: str = "field_operator") -> OperatorProfile:
        operator_id = _id("OPR")
        profile = OperatorProfile(
            operator_id=operator_id,
            name=name, email=email, phone=phone, role=role,
            status="active",
            assigned_cases=[],
            access={"issued": _now_iso(), "expires": None, "reactivations": 0},
            audit_log=[{"event": "create_operator", "timestamp": _now_iso()}]
        )
        _write_json(self._path(operator_id), profile.to_dict())
        return profile

    def get(self, operator_id: str) -> Optional[OperatorProfile]:
        data = _read_json(self._path(operator_id), None)
        if not data: return None
        return OperatorProfile(**data)

    def update(self, profile: OperatorProfile) -> None:
        _write_json(self._path(profile.operator_id), profile.to_dict())

    def list_all(self) -> List[OperatorProfile]:
        out = []
        for f in OPERATORS_DIR.glob("OPR-*.json"):
            data = _read_json(f, None)
            if data:
                out.append(OperatorProfile(**data))
        return out

    # ---- Assignment / Access windows ----
    def assign_to_case(self, operator_id: str, case_id: str,
                       hours: Optional[int] = None) -> OperatorProfile:
        prof = self.get(operator_id)
        if not prof: raise ValueError("Operator not found")
        if case_id not in (prof.assigned_cases or []):
            prof.assigned_cases.append(case_id)
        # timebox
        hrs = hours if hours is not None else self.rules.default_expiration_hours
        expires = (datetime.utcnow() + timedelta(hours=hrs)).isoformat() + "Z"
        prof.access = prof.access or {}
        prof.access["issued"] = _now_iso()
        prof.access["expires"] = expires
        prof.audit_log = (prof.audit_log or []) + [{
            "event": "assign_case", "case": case_id, "expires": expires, "timestamp": _now_iso()
        }]
        self.update(prof)
        return prof

    def extend_access(self, operator_id: str, hours: int) -> OperatorProfile:
        prof = self.get(operator_id)
        if not prof: raise ValueError("Operator not found")
        # base on now or current expiry
        cur_exp = prof.access.get("expires") if prof.access else None
        base = datetime.utcnow()
        if cur_exp:
            try: base = datetime.fromisoformat(cur_exp.replace("Z",""))
            except Exception: pass
        new_exp = (base + timedelta(hours=hours)).isoformat() + "Z"
        prof.access["expires"] = new_exp
        prof.audit_log.append({"event":"extend_access","hours":hours,"new_expires":new_exp,"timestamp":_now_iso()})
        self.update(prof)
        return prof

    def deactivate(self, operator_id: str, reason: str = "manual") -> OperatorProfile:
        prof = self.get(operator_id)
        if not prof: raise ValueError("Operator not found")
        prof.status = "inactive"
        prof.audit_log.append({"event":"deactivate","reason":reason,"timestamp":_now_iso()})
        self.update(prof)
        return prof

    def reactivate(self, operator_id: str, hours: Optional[int] = None) -> OperatorProfile:
        prof = self.get(operator_id)
        if not prof: raise ValueError("Operator not found")
        prof.status = "active"
        prof.access["reactivations"] = int(prof.access.get("reactivations",0)) + 1
        self.assign_to_case(operator_id, prof.assigned_cases[-1] if prof.assigned_cases else "UNASSIGNED",
                            hours=hours)
        prof.audit_log.append({"event":"reactivate","timestamp":_now_iso()})
        self.update(prof)
        return prof

    # ---- Policy checks (no-op when disabled) ----
    def is_allowed(self, user_role: str, action: str) -> bool:
        return self.rules.is_allowed(user_role, action)
