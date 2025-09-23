#!/usr/bin/env python3
"""
Sync DevTracker JSON logs (in dev_tracking/) into dev_tracking/logs/ for
DEESCALATION visibility. Creates the target files if missing.
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


def read_json(p: Path) -> Dict[str, Any]:
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        return {}


def write_json(p: Path, data: Dict[str, Any]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')


def merge(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(a)
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = merge(out[k], v)
        elif isinstance(v, list) and isinstance(out.get(k), list):
            out[k] = out[k] + v
        else:
            out[k] = v
    return out


def main() -> int:
    root = Path.cwd()
    src_dir = root / 'dev_tracking'
    dst_dir = src_dir / 'logs'

    files = ['change_log.json', 'file_states.json', 'progression_log.json']

    for name in files:
        src = src_dir / name
        dst = dst_dir / name
        src_data = read_json(src)
        dst_data = read_json(dst)
        if not src_data and not dst_data:
            # Initialize empty structure if nothing exists
            if name == 'change_log.json':
                out = {'changes': [], 'last_update': datetime.now().isoformat()}
            elif name == 'file_states.json':
                out = {'files': {}, 'last_scan': datetime.now().isoformat()}
            else:
                out = {'power_components': {}, 'features_built': {}, 'fixes_applied': {}, 'last_update': datetime.now().isoformat()}
        else:
            out = merge(dst_data, src_data)
            # Stamp
            key = 'last_update' if name != 'file_states.json' else 'last_scan'
            out[key] = datetime.now().isoformat()

        write_json(dst, out)
        print(f"Synced {name} -> {dst}")

    return 0


if __name__ == '__main__':
    raise SystemExit(main())

