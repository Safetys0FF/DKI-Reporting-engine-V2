#!/usr/bin/env python3
"""
Deduplicate entries in dev_tracking/logs/change_log.json.

Keeps the earliest occurrence of duplicate change items where duplicates are
defined by identical (file, type, description, details) fields. Preserves
chronological ordering by timestamp.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple


def canon_key(entry: Dict[str, Any]) -> Tuple[str, str, str, str]:
    """Canonical fingerprint for a change entry."""
    file = str(entry.get("file", ""))
    typ = str(entry.get("type", ""))
    desc = str(entry.get("description", ""))
    # Stable stringify of details for hashing
    details = entry.get("details", {}) or {}
    try:
        details_s = json.dumps(details, sort_keys=True, ensure_ascii=False)
    except Exception:
        details_s = str(details)
    return (file, typ, desc, details_s)


def parse_ts(ts: str) -> str:
    # Keep string format; ISO 8601 is lexicographically sortable
    return ts or ""


def main() -> None:
    root = Path.cwd()
    log_path = root / "dev_tracking" / "logs" / "change_log.json"
    if not log_path.exists():
        print("No change_log.json found at dev_tracking/logs; nothing to do.")
        return

    data: Dict[str, Any]
    try:
        data = json.loads(log_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"ERROR: Unable to read JSON: {e}")
        return

    changes: List[Dict[str, Any]] = list(data.get("changes", []))
    if not changes:
        print("No changes to process.")
        return

    # Sort ascending by timestamp to keep earliest duplicate
    try:
        changes.sort(key=lambda x: parse_ts(str(x.get("timestamp", ""))))
    except Exception:
        pass

    seen = set()
    deduped: List[Dict[str, Any]] = []
    removed = 0
    for ch in changes:
        key = canon_key(ch)
        if key in seen:
            removed += 1
            continue
        seen.add(key)
        deduped.append(ch)

    # Restore chronological order (ascending by timestamp)
    try:
        deduped.sort(key=lambda x: parse_ts(str(x.get("timestamp", ""))))
    except Exception:
        pass

    out = {
        "changes": deduped,
        "last_update": datetime.now().isoformat(),
    }
    log_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Dedup complete. Removed {removed} duplicate entries. Total now: {len(deduped)}")


if __name__ == "__main__":
    main()

