#!/usr/bin/env python3
"""
Import API keys into a UserProfileManager account so users don't have to
retype keys at login. Keys are read from a JSON or TXT file and saved into
the per-user encrypted store.

Usage examples:
  python dev_tracking/tools/import_keys_to_profile.py --username alice --password secret \
      --db user_profiles.db --keys api_keys.json

  # Create user if missing, then import
  python dev_tracking/tools/import_keys_to_profile.py --username alice --password secret \
      --create --keys api_keys.json

  # List existing users
  python dev_tracking/tools/import_keys_to_profile.py --db user_profiles.db --list-users
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any

DEV_TRACKING_DIR = Path(__file__).resolve().parents[1]
if str(DEV_TRACKING_DIR) not in sys.path:
    sys.path.insert(0, str(DEV_TRACKING_DIR))

from path_bootstrap import bootstrap_paths

bootstrap_paths(__file__)

from user_profile_manager import UserProfileManager


SERVICE_KEY_MAP = {
    # Primary names used by SetupWizard/UserProfileManager
    'openai_api_key': 'openai_api',
    'openai_api': 'openai_api',
    'google_gemini_api_key': 'google_gemini_api',
    'google_gemini_api': 'google_gemini_api',
    'google_maps_api_key': 'google_maps_api',
    'google_maps_api': 'google_maps_api',
    'google_search_api_key': 'google_search_api',
    'google_search_api': 'google_search_api',
    'google_search_engine_id': 'google_search_engine_id',
    'bing_search_api_key': 'bing_search_api',
    'bing_search_api': 'bing_search_api',
    'public_records_api_key': 'public_records_api',
    'public_records_api': 'public_records_api',
    'whitepages_api_key': 'whitepages_api',
    'whitepages_api': 'whitepages_api',
}


def load_keys(keys_path: Path) -> Dict[str, str]:
    """Load keys from JSON or TXT file.
    For TXT, uses simple label-next-line parsing.
    """
    if not keys_path.exists():
        raise SystemExit(f"Keys file not found: {keys_path}")
    if keys_path.suffix.lower() == '.json':
        try:
            data = json.loads(keys_path.read_text(encoding='utf-8'))
        except Exception as e:
            raise SystemExit(f"Invalid JSON in {keys_path}: {e}")
        # Normalize
        out: Dict[str, str] = {}
        for k, v in (data or {}).items():
            if not isinstance(v, str):
                continue
            mapped = SERVICE_KEY_MAP.get(k)
            if mapped and v and not str(v).startswith('your_'):
                out[mapped] = v
        return out

    # Fallback: simple TXT parser (label + next non-empty line)
    text = keys_path.read_text(encoding='utf-8', errors='ignore')
    lines = [ln.strip() for ln in text.splitlines()]
    out: Dict[str, str] = {}
    label_map = {
        'chatgpt': 'openai_api',
        'openai': 'openai_api',
        'gemini': 'google_gemini_api',
        'google gemini': 'google_gemini_api',
        'google maps': 'google_maps_api',
        'maps': 'google_maps_api',
        'google search': 'google_search_api',
        'custom search': 'google_search_api',
        'cse id': 'google_search_engine_id',
        'cx': 'google_search_engine_id',
        'bing': 'bing_search_api',
    }
    i = 0
    while i < len(lines):
        low = lines[i].lower()
        target = None
        for k, dest in label_map.items():
            if k in low:
                target = dest
                break
        if target:
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines):
                out[target] = lines[j].strip()
                i = j
        i += 1
    return out


def list_users(db_path: Path) -> None:
    import sqlite3
    if not db_path.exists():
        print(f"No DB found at {db_path}")
        return
    try:
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        cur.execute('SELECT username, created_date, last_login FROM users ORDER BY id ASC')
        rows = cur.fetchall()
        conn.close()
        if not rows:
            print("No users found.")
            return
        print("Users:")
        for u, created, last in rows:
            print(f"- {u} (created: {created or 'N/A'}, last_login: {last or 'N/A'})")
    except Exception as e:
        print(f"Failed to list users: {e}")


def main() -> int:
    p = argparse.ArgumentParser(description='Import API keys into a user profile')
    p.add_argument('--db', default='user_profiles.db', help='Path to user profiles DB')
    p.add_argument('--keys', default='api_keys.json', help='Path to keys file (json or txt)')
    p.add_argument('--username')
    p.add_argument('--password')
    p.add_argument('--create', action='store_true', help='Create user if missing')
    p.add_argument('--list-users', action='store_true', help='List existing users and exit')
    args = p.parse_args()

    db_path = Path(args.db)
    keys_path = Path(args.keys)

    if args.list_users:
        list_users(db_path)
        return 0

    if not args.username or not args.password:
        raise SystemExit('Missing --username/--password')

    keys = load_keys(keys_path)
    if not keys:
        print('No usable keys found in', keys_path)
        return 1

    upm = UserProfileManager(str(db_path))

    # Create user if requested and missing
    try:
        # Uses internal helper to find user id
        user_id = upm._get_user_id_by_username(args.username)
    except Exception:
        user_id = None
    if args.create and not user_id:
        ok = upm.create_user(args.username, args.password)
        if not ok:
            raise SystemExit('Failed to create user')

    if not upm.authenticate_user(args.username, args.password):
        raise SystemExit('Authentication failed — wrong username/password?')

    saved = 0
    for svc, key in keys.items():
        try:
            if upm.save_api_key(svc, key):
                saved += 1
        except Exception:
            pass

    print(f"Imported {saved} key(s) for user {args.username} into {db_path}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

