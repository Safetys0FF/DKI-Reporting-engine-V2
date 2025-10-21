#!/usr/bin/env python3
"""
User Profile Manager

Provides a minimal but production-appropriate credential and API-key store so
the Setup Wizard, smoke harness, and import utilities can all share the same
backend.  The API mirrors the expectations recorded in the dev-tracking
handoffs (`create_user`, `authenticate_user`, `save_api_key`, `get_api_keys`,
`get_user_info`, `_get_user_id_by_username`, etc.).
"""
from __future__ import annotations

import hashlib
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULT_DB_NAME = "user_profiles.db"
PBKDF2_ROUNDS = 200_000


class UserProfileManager:
    """Lightweight credential/API key manager backed by SQLite."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        base_dir = Path(db_path).resolve() if db_path else Path(__file__).resolve().parent / DEFAULT_DB_NAME
        if base_dir.is_dir():
            self.db_path = base_dir / DEFAULT_DB_NAME
        else:
            self.db_path = base_dir
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._active_user_id: Optional[int] = None
        self._active_username: Optional[str] = None
        self._initialize_db()

    # -- database helpers -------------------------------------------------
    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize_db(self) -> None:
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                password_salt TEXT NOT NULL,
                email TEXT,
                full_name TEXT,
                company TEXT,
                license_number TEXT,
                profile_picture TEXT,
                created_date TEXT,
                last_login TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                service TEXT NOT NULL,
                api_key TEXT NOT NULL,
                updated_at TEXT,
                UNIQUE(user_id, service),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        conn.commit()
        conn.close()

    # -- password hashing -------------------------------------------------
    @staticmethod
    def _hash_password(password: str, salt: Optional[bytes] = None) -> Dict[str, str]:
        if salt is None:
            salt = os.urandom(16)
        derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ROUNDS)
        return {
            "salt": salt.hex(),
            "hash": derived.hex(),
        }

    @staticmethod
    def _verify_password(password: str, salt_hex: str, hash_hex: str) -> bool:
        salt = bytes.fromhex(salt_hex)
        test = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ROUNDS).hex()
        # Use hmac.compare_digest or fallback to simple comparison
        try:
            import hmac
            return hmac.compare_digest(test, hash_hex)
        except (ImportError, AttributeError):
            return test == hash_hex

    # -- user management --------------------------------------------------
    def create_user(
        self,
        username: str,
        password: str,
        *,
        email: Optional[str] = None,
        full_name: Optional[str] = None,
        company: Optional[str] = None,
        license_number: Optional[str] = None,
        profile_picture: Optional[str] = None,
    ) -> bool:
        """Create user if missing; returns True on success/exists."""
        username = username.strip()
        if not username or not password:
            return False

        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        if row:
            conn.close()
            return True  # already exists

        hashed = self._hash_password(password)
        now = datetime.utcnow().isoformat()
        cur.execute(
            """
            INSERT INTO users (username, password_hash, password_salt, email,
                               full_name, company, license_number, profile_picture, created_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                username,
                hashed["hash"],
                hashed["salt"],
                email,
                full_name,
                company,
                license_number,
                profile_picture,
                now,
            ),
        )
        conn.commit()
        conn.close()
        return True

    def authenticate_user(self, username: str, password: str) -> bool:
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, password_hash, password_salt FROM users WHERE username = ?",
            (username,),
        )
        row = cur.fetchone()
        if not row:
            conn.close()
            return False
        if not self._verify_password(password, row["password_salt"], row["password_hash"]):
            conn.close()
            return False

        self._active_user_id = int(row["id"])
        self._active_username = username
        cur.execute(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), self._active_user_id),
        )
        conn.commit()
        conn.close()
        return True

    def _ensure_active_user(self) -> int:
        if self._active_user_id is None:
            raise RuntimeError("No authenticated user. Call authenticate_user first.")
        return self._active_user_id

    def _get_user_id_by_username(self, username: str) -> Optional[int]:
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        conn.close()
        return int(row["id"]) if row else None

    # -- API key management ----------------------------------------------
    def save_api_key(self, service: str, api_key: str) -> bool:
        service = service.strip().lower()
        if not service or not api_key:
            return False
        user_id = self._ensure_active_user()
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO api_keys (user_id, service, api_key, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, service) DO UPDATE SET
                api_key = excluded.api_key,
                updated_at = excluded.updated_at
            """,
            (user_id, service, api_key, datetime.utcnow().isoformat()),
        )
        conn.commit()
        conn.close()
        return True

    def save_api_keys(self, payload: Dict[str, str]) -> int:
        count = 0
        for svc, key in (payload or {}).items():
            try:
                if self.save_api_key(svc, key):
                    count += 1
            except Exception:
                continue
        return count

    def get_api_keys(self) -> Dict[str, str]:
        user_id = self._ensure_active_user()
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT service, api_key FROM api_keys WHERE user_id = ?", (user_id,))
        rows = cur.fetchall()
        conn.close()
        return {row["service"]: row["api_key"] for row in rows}
    
    def update_profile_picture(self, picture_path: str) -> bool:
        """Update the profile picture for the active user"""
        user_id = self._ensure_active_user()
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET profile_picture = ? WHERE id = ?",
            (picture_path, user_id)
        )
        conn.commit()
        conn.close()
        return True

    # -- profile helpers --------------------------------------------------
    def get_user_info(self) -> Dict[str, Any]:
        """Return info for the active user (or first user if none authenticated)."""
        conn = self._connect()
        cur = conn.cursor()
        target_id = self._active_user_id
        if target_id is None:
            cur.execute("SELECT * FROM users ORDER BY id ASC LIMIT 1")
        else:
            cur.execute("SELECT * FROM users WHERE id = ?", (target_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return {}
        return {
            "id": row["id"],
            "username": row["username"],
            "email": row["email"],
            "full_name": row["full_name"],
            "company": row["company"],
            "license_number": row["license_number"],
            "profile_picture": row["profile_picture"] if "profile_picture" in row.keys() else None,
            "created_date": row["created_date"],
            "last_login": row["last_login"],
        }
