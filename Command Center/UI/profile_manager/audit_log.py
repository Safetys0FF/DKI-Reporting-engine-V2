#!/usr/bin/env python3
"""
Audit Log – append-only JSONL per case. Lightweight & durable.
"""
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

def _now(): return datetime.utcnow().isoformat() + "Z"

def log_case_event(case_root: Path, event: str, **fields: Any) -> None:
    case_root.mkdir(parents=True, exist_ok=True)
    line = {"timestamp": _now(), "event": event}
    line.update(fields)
    (case_root / "audit.jsonl").open("a", encoding="utf-8").write(json.dumps(line) + "\n")
