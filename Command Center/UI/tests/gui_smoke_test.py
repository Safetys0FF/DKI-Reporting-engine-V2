#!/usr/bin/env python3
"""Smoke-level tests for enhanced GUI helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GUI_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from enhanced_functional_gui import sanitize_case_id, InputPersistence


class InputPersistenceSmokeTest(unittest.TestCase):
    def test_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "state.json"
            persistence = InputPersistence(state_file)

            persistence.update_section("login", {"last_operator": "Alice", "last_role": "admin"})
            payload = persistence.get_section("login")

            self.assertEqual(payload.get("last_operator"), "Alice")
            self.assertEqual(payload.get("last_role"), "admin")
            self.assertTrue(state_file.exists())


class SanitizeCaseIdTest(unittest.TestCase):
    def test_sanitize_case_id(self) -> None:
        raw_value = "  Case #42 / Main Ops  "
        sanitized = sanitize_case_id(raw_value)
        self.assertEqual(sanitized, "Case_42_Main_Ops")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
