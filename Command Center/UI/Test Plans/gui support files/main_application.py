#!/usr/bin/env python3
"""
Central Command GUI Shell
Hosts the evidence panel and placeholder tabs for legacy components.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, List
import logging

from central_plugin import central_plugin
from evidence_panel import EvidencePanel

logger = logging.getLogger(__name__)


class CentralCommandController:
    """Shared controller that wraps the central_plugin interfaces."""

    def __init__(self):
        self.central_plugin = central_plugin
        self.report_type = "Investigative"
        self.current_case_id: str | None = None

    # ------------------------------- case management -------------------
    def new_case(self, case_info: Dict[str, Any]) -> str:
        case_id = self.central_plugin.bus.new_case(case_info)
        self.current_case_id = case_id
        return case_id

    def get_case_summary(self, case_id: str) -> Any:
        return self.central_plugin.get_case_summary(case_id)

    # -------------------------------- evidence -------------------------
    def store_file(self, file_info: Dict[str, Any]):
        return self.central_plugin.store_file(file_info)

    def register_files(self, files: List[str]):
        try:
            self.central_plugin.bus.add_files(files)
        except Exception as exc:
            logger.warning("Failed to register files with bus: %s", exc)

    def generate_narrative(self, processed_data: Dict[str, Any], section_id: str):
        return self.central_plugin.generate_narrative(processed_data, section_id)

    # -------------------------------- bus logs -------------------------
    def get_bus_events(self, limit: int = 100):
        try:
            return self.central_plugin.bus.get_event_log(limit)
        except Exception as exc:
            logger.error("Failed to read bus events: %s", exc)
            return []


class CentralCommandApp(tk.Tk):
    """Root application window."""

    def __init__(self):
        super().__init__()
        self.title("DKI Central Command - Investigation Report Generator")
        self.geometry("1400x900")

        self.controller = CentralCommandController()

        self._build_menu()
        self._build_layout()

    def _build_menu(self):
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New Case", command=self._new_case)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)

    def _build_layout(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True)

        evidence_tab = EvidencePanel(notebook, self.controller)
        notebook.add(evidence_tab, text="Evidence & Narrative")

        placeholders = {
            "Case Management": "This panel is being migrated to the new architecture.",
            "Reports": "Report builder integration coming soon.",
            "System Health": "Health dashboard will return after telemetry wiring.",
            "Setup Wizard": "Setup wizard will be re-enabled shortly.",
            "User Profiles": "User profile management is under refurbishment.",
            "API Status": "API status monitoring will reconnect soon."
        }

        for title, message in placeholders.items():
            frame = ttk.Frame(notebook)
            ttk.Label(frame, text=message, padding=20, justify='center').pack(fill='both', expand=True)
            notebook.add(frame, text=title)

        status_frame = ttk.Frame(self, relief=tk.SUNKEN)
        status_frame.pack(fill='x')
        ttk.Label(status_frame, text="Central Command bus ready", anchor='w').pack(fill='x')

    def _new_case(self):
        if messagebox.askyesno("New Case", "Create a new case? This will clear current data."):
            notebook = self.children.get('!notebook')
            if notebook:
                evidence_panel = notebook.nametowidget(notebook.tabs()[0])
                evidence_panel.new_case()

    def _show_about(self):
        messagebox.showinfo(
            "About",
            "DKI Central Command\nNew architecture preview"
        )


def main():
    logging.basicConfig(level=logging.INFO)
    app = CentralCommandApp()
    app.mainloop()


if __name__ == "__main__":
    main()

