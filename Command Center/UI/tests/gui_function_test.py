#!/usr/bin/env python3
"""Functional tests for GUI persistence components."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import tkinter as tk

import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from enhanced_functional_gui import CaseCreationDialog, InputPersistence


class CaseCreationDialogPersistenceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        state_path = Path(self.tmpdir.name) / "gui_state.json"
        self.persistence = InputPersistence(state_path)
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self) -> None:
        try:
            self.root.destroy()
        except Exception:
            pass
        self.tmpdir.cleanup()

    def test_defaults_loaded_from_persistence(self) -> None:
        self.persistence.update_section(
            "case_creation",
            {
                "case_id_input": "persist-case-42",
                "investigator": "Casey Investigator",
                "client_name": "ACME Corp",
                "subject": "Primary Subject",
                "location": "Seattle",
                "export_root": "C:/Reports",
            },
        )

        dialog = CaseCreationDialog(
            self.root,
            default_case_id="",
            default_investigator="",
            metadata_defaults={},
            existing_ids=[],
            input_state=self.persistence,
        )
        self.root.update_idletasks()

        self.assertEqual(dialog.case_input_var.get(), "persist-case-42")
        self.assertEqual(dialog.investigator_var.get(), "Casey Investigator")
        self.assertEqual(dialog.client_var.get(), "ACME Corp")

        dialog.window.destroy()

    def test_accept_updates_persistence(self) -> None:
        dialog = CaseCreationDialog(
            self.root,
            default_case_id="",
            default_investigator="",
            metadata_defaults={},
            existing_ids=[],
            input_state=self.persistence,
        )
        self.root.update_idletasks()

        dialog.case_input_var.set("Case-123")
        dialog.investigator_var.set("Dana Agent")
        dialog.contract_var.set("2025-01-15")
        dialog.client_var.set("Client X")
        dialog.subject_var.set("Subject Y")
        dialog.location_var.set("Mars Base")
        dialog.export_root_var.set("C:/Exports")

        dialog._accept()

        state = self.persistence.get_section("case_creation")
        self.assertEqual(state.get("case_id"), "Case-123")
        self.assertEqual(state.get("investigator"), "Dana Agent")
        self.assertEqual(state.get("client_name"), "Client X")

    def test_cancel_does_not_raise(self) -> None:
        dialog = CaseCreationDialog(
            self.root,
            default_case_id="",
            default_investigator="",
            metadata_defaults={},
            existing_ids=[],
            input_state=self.persistence,
        )
        self.root.update_idletasks()
        dialog._cancel()
        self.assertIsNone(dialog.result)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
