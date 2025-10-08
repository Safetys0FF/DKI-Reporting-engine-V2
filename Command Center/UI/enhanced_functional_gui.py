"""Central Command GUI integrating profile dashboards with evidence intake."""
from __future__ import annotations

import os
import sys
import json
import re
import traceback
import threading
import uuid
from datetime import datetime, date
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence

try:  # Optional drag-and-drop support
    import tkinterdnd2 as tkdnd
    DND_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    tkdnd = None
    DND_AVAILABLE = False

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tag_taxonomy import normalize_tags
from central_plugin import CentralPluginAdapter
from case_session import CaseSession, SectionState, SECTION_TITLES
from profile_registry import ProfileRegistry, Profile
from profile_manager.operator_manager import OperatorManager, AccessRules, OperatorProfile
from profile_manager.auth_manager import issue_token
from ui_components import StatusBar

APP_TITLE = "Central Command"
MIN_WINDOW_SIZE = (1120, 720)
CARD_BG = "#f8fafc"
CARD_BORDER = "#cbd5f5"
LOG_MAX_LINES = 500

CASE_ID_SANITIZE_PATTERN = re.compile(r'[^A-Za-z0-9_-]+')


def sanitize_case_id(raw: str) -> str:
    """Return a canonical case identifier containing only safe characters."""
    if not raw:
        return ""
    normalized = CASE_ID_SANITIZE_PATTERN.sub('_', raw.strip())
    normalized = re.sub(r'_+', '_', normalized)
    return normalized.strip('_')


class LoginDialog:
    """Operator selection dialog with optional operator-manager integration."""

    def __init__(
        self,
        parent: tk.Tk,
        default_name: str,
        *,
        operators: Optional[List[OperatorProfile]] = None,
        manager: Optional[OperatorManager] = None,
    ) -> None:
        self.manager = manager
        self.operators = operators or []
        self.result: Optional[object] = None
        self.selected_profile: Optional[OperatorProfile] = None

        self.window = tk.Toplevel(parent)
        self.window.title("Central Command Login")
        self.window.transient(parent)
        self.window.resizable(False, False)
        self.window.grab_set()

        container = ttk.Frame(self.window, padding=12)
        container.pack(fill="both", expand=True)

        existing_frame = ttk.LabelFrame(container, text="Available Operators", padding=12)
        existing_frame.pack(fill="both", expand=True)
        existing_frame.columnconfigure(0, weight=1)
        existing_frame.rowconfigure(0, weight=1)

        self.listbox = tk.Listbox(existing_frame, height=8, exportselection=False)
        self.listbox.grid(row=0, column=0, sticky="nsew")
        for profile in self.operators:
            display = f"{profile.name} ({profile.role})"
            self.listbox.insert(tk.END, display)
        self.listbox.bind("<<ListboxSelect>>", self._on_select)
        self.listbox.bind("<Double-Button-1>", lambda _e: self._accept())

        if not self.operators:
            self.listbox.insert(tk.END, "No operators registered yet")
            self.listbox.configure(state="disabled")

        scroll = ttk.Scrollbar(existing_frame, orient="vertical", command=self.listbox.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.listbox.configure(yscrollcommand=scroll.set)

        new_frame = ttk.LabelFrame(container, text="Create Operator", padding=12)
        new_frame.pack(fill="x", pady=(12, 0))
        ttk.Label(new_frame, text="Name").grid(row=0, column=0, sticky="w")
        self.new_name_var = tk.StringVar(value=default_name or "")
        ttk.Entry(new_frame, textvariable=self.new_name_var, width=32).grid(row=0, column=1, sticky="ew")
        new_frame.columnconfigure(1, weight=1)

        ttk.Label(new_frame, text="Role").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.role_var = tk.StringVar(value="field_operator")
        ttk.Combobox(
            new_frame,
            textvariable=self.role_var,
            state="readonly",
            values=["field_operator", "supervisor", "admin"],
            width=30,
        ).grid(row=1, column=1, sticky="ew", pady=(6, 0))

        button_row = ttk.Frame(container)
        button_row.pack(fill="x", pady=(14, 0))
        ttk.Button(button_row, text="Cancel", command=self._cancel).pack(side="right")
        ttk.Button(button_row, text="Continue", command=self._accept).pack(side="right", padx=(8, 0))

        self.window.bind("<Return>", lambda _e: self._accept())
        self.window.protocol("WM_DELETE_WINDOW", self._cancel)
        parent.wait_window(self.window)

    def _on_select(self, _event: object) -> None:
        if not self.operators:
            return
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            self.selected_profile = self.operators[index]
            self.new_name_var.set(self.selected_profile.name)
            self.role_var.set(self.selected_profile.role or "field_operator")
        else:
            self.selected_profile = None

    def _accept(self) -> None:
        if self.manager:
            if self.selected_profile is not None:
                self.result = self.selected_profile
                self.window.destroy()
                return
            name = self.new_name_var.get().strip()
            if not name:
                messagebox.showwarning(APP_TITLE, "Enter an operator name or select an existing profile.")
                return
            try:
                profile = self.manager.create(name=name, role=self.role_var.get())
            except Exception as exc:
                messagebox.showerror(APP_TITLE, f"Could not create operator:\n{exc}")
                return
            self.result = profile
        else:
            name = self.new_name_var.get().strip()
            if not name:
                messagebox.showwarning(APP_TITLE, "Enter an operator name to continue.")
                return
            self.result = name
        self.window.destroy()

    def _cancel(self) -> None:
        self.result = None
        self.window.destroy()

    def show(self) -> Optional[object]:
        return self.result


class CaseCreationDialog:
    """Wizard dialog for collecting the details required to start a new case."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        default_case_id: str = "",
        default_investigator: str = "",
        subcontractor: bool = False,
        contract_signed: Optional[str] = None,
        export_root: Optional[str] = None,
        metadata_defaults: Optional[Dict[str, Any]] = None,
        existing_ids: Optional[Iterable[str]] = None,
    ) -> None:
        self.result: Optional[Dict[str, Any]] = None
        self._existing_ids = {sanitize_case_id(item).lower() for item in (existing_ids or []) if item}

        self.window = tk.Toplevel(parent)
        self.window.title("Start New Case")
        self.window.transient(parent)
        self.window.resizable(False, False)
        self.window.grab_set()

        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)

        container = ttk.Frame(self.window, padding=16)
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)

        basics = ttk.LabelFrame(container, text="Case Basics", padding=12)
        basics.grid(row=0, column=0, sticky="ew")
        basics.columnconfigure(1, weight=1)

        self.case_input_var = tk.StringVar(value=default_case_id)
        self.case_preview_var = tk.StringVar(value=sanitize_case_id(default_case_id))
        self.case_warning_var = tk.StringVar(value="")

        ttk.Label(basics, text="Case Number").grid(row=0, column=0, sticky="w")
        case_entry = ttk.Entry(basics, textvariable=self.case_input_var, width=32)
        case_entry.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        ttk.Label(basics, text="Canonical ID:").grid(row=1, column=0, sticky="w", pady=(2, 0))
        ttk.Label(basics, textvariable=self.case_preview_var, foreground="#2563eb").grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(2, 0))
        ttk.Label(basics, textvariable=self.case_warning_var, foreground="#dc2626").grid(row=2, column=0, columnspan=2, sticky="w")

        self.investigator_var = tk.StringVar(value=default_investigator)
        ttk.Label(basics, text="Investigator").grid(row=3, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(basics, textvariable=self.investigator_var).grid(row=3, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

        self.subcontractor_var = tk.BooleanVar(value=subcontractor)
        ttk.Checkbutton(basics, text="Subcontractor engagement", variable=self.subcontractor_var).grid(row=4, column=0, columnspan=2, sticky="w", pady=(8, 0))

        self.contract_var = tk.StringVar(value=contract_signed or "")
        ttk.Label(basics, text="Contract signed (YYYY-MM-DD)").grid(row=5, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(basics, textvariable=self.contract_var).grid(row=5, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

        details = ttk.LabelFrame(container, text="Additional Details", padding=12)
        details.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        details.columnconfigure(1, weight=1)

        metadata_defaults = metadata_defaults or {}
        self.client_var = tk.StringVar(value=str(metadata_defaults.get("client_name") or ""))
        self.subject_var = tk.StringVar(value=str(metadata_defaults.get("subject") or ""))
        self.location_var = tk.StringVar(value=str(metadata_defaults.get("location") or ""))
        self.export_root_var = tk.StringVar(value=str(export_root or ""))

        ttk.Label(details, text="Client").grid(row=0, column=0, sticky="w")
        ttk.Entry(details, textvariable=self.client_var).grid(row=0, column=1, sticky="ew", padx=(8, 0))
        ttk.Label(details, text="Subject").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(details, textvariable=self.subject_var).grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))
        ttk.Label(details, text="Location").grid(row=2, column=0, sticky="w")
        ttk.Entry(details, textvariable=self.location_var).grid(row=2, column=1, sticky="ew", padx=(8, 0))
        ttk.Label(details, text="Export root").grid(row=3, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(details, textvariable=self.export_root_var).grid(row=3, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

        buttons = ttk.Frame(container)
        buttons.grid(row=2, column=0, sticky="e", pady=(16, 0))
        ttk.Button(buttons, text="Cancel", command=self._cancel).pack(side="right")
        ttk.Button(buttons, text="Create Case", command=self._accept).pack(side="right", padx=(8, 0))

        case_entry.focus_set()
        self.case_input_var.trace_add("write", self._sync_case_preview)
        self.window.bind("<Return>", lambda _e: self._accept())
        self.window.protocol("WM_DELETE_WINDOW", self._cancel)
        parent.wait_window(self.window)

    def _sync_case_preview(self, *_: object) -> None:
        preview = sanitize_case_id(self.case_input_var.get())
        self.case_preview_var.set(preview or "(will be generated)")
        if preview and preview.lower() in self._existing_ids:
            self.case_warning_var.set("A case with this ID already exists.")
        else:
            self.case_warning_var.set("")

    def _accept(self) -> None:
        raw_case = self.case_input_var.get().strip()
        case_id = sanitize_case_id(raw_case)
        if not case_id:
            messagebox.showwarning(APP_TITLE, "Case identifier cannot be empty.")
            return
        if case_id.lower() in self._existing_ids:
            messagebox.showwarning(APP_TITLE, f"Case identifier '{case_id}' already exists.")
            return

        contract_value = self.contract_var.get().strip()
        if contract_value:
            try:
                date.fromisoformat(contract_value)
            except ValueError:
                messagebox.showwarning(APP_TITLE, "Contract signed date must use YYYY-MM-DD format.")
                return

        investigator = self.investigator_var.get().strip() or "Investigator"
        metadata: Dict[str, Any] = {
            "client_name": self.client_var.get().strip() or None,
            "subject": self.subject_var.get().strip() or None,
            "location": self.location_var.get().strip() or None,
        }

        self.result = {
            "case_id": case_id,
            "investigator": investigator,
            "subcontractor": bool(self.subcontractor_var.get()),
            "contract_signed": contract_value or None,
            "export_root": self.export_root_var.get().strip() or None,
            "metadata": {k: v for k, v in metadata.items() if v},
        }
        self.window.destroy()

    def _cancel(self) -> None:
        self.result = None
        self.window.destroy()

    def show(self) -> Optional[Dict[str, Any]]:
        return self.result


class ProfileEditor:
    """Modal dialog allowing analysts to tweak the profile JSON."""

    FIELD_DEFS = [
        ("user_name", "User Name"),
        ("business_name", "Business Name"),
        ("business_address", "Business Address"),
        ("city_state", "City / State"),
        ("email", "Email"),
        ("phone", "Phone"),
        ("agency_license", "Agency License"),
        ("investigator_license", "Investigator License"),
        ("labor_rate", "Hourly Rate"),
        ("preferred_workflow", "Preferred Workflow"),
        ("preferred_intake_form", "Preferred Intake Form"),
    ]

    def __init__(self, parent: tk.Tk, profile_data: Dict[str, object]) -> None:
        self.window = tk.Toplevel(parent)
        self.window.title("Edit Analyst Profile")
        self.window.transient(parent)
        self.window.grab_set()

        self._data = dict(profile_data)
        self._vars: Dict[str, tk.StringVar] = {}

        main = ttk.Frame(self.window, padding=12)
        main.pack(fill="both", expand=True)

        for key, label in self.FIELD_DEFS:
            row = ttk.Frame(main)
            row.pack(fill="x", pady=4)
            ttk.Label(row, text=label, width=24).pack(side="left")
            value = "" if self._data.get(key) is None else str(self._data.get(key))
            var = tk.StringVar(value=value)
            ttk.Entry(row, textvariable=var).pack(side="left", fill="x", expand=True)
            self._vars[key] = var

        button_row = ttk.Frame(main)
        button_row.pack(fill="x", pady=(12, 0))
        ttk.Button(button_row, text="Cancel", command=self._cancel).pack(side="right", padx=(8, 0))
        ttk.Button(button_row, text="Save", command=self._save).pack(side="right")

        self.result: Optional[Dict[str, object]] = None
        self.window.protocol("WM_DELETE_WINDOW", self._cancel)
        parent.wait_window(self.window)

    def _cancel(self) -> None:
        self.result = None
        self.window.destroy()

    def _save(self) -> None:
        updated = dict(self._data)
        for key, _label in self.FIELD_DEFS:
            raw = self._vars[key].get().strip()
            if key == "labor_rate":
                if raw:
                    try:
                        updated[key] = float(raw)
                    except ValueError:
                        messagebox.showerror(APP_TITLE, "Hourly rate must be numeric.")
                        return
                else:
                    updated[key] = None
            else:
                updated[key] = raw
        self.result = updated
        self.window.destroy()

    def show(self) -> Optional[Dict[str, object]]:
        return self.result


class EvidenceCard:
    """Drag-and-drop card representing a single evidence file."""

    def __init__(
        self,
        parent: tk.Widget,
        path: str,
        categories: List[Dict[str, object]],
        on_advertise,
        on_scan,
        on_remove,
        suggestion: Optional[Dict[str, Any]] = None,
        case_label: Optional[str] = None,
        case_id: Optional[str] = None,
    ) -> None:
        self.parent = parent
        self.path = path
        self.categories = categories
        self.on_advertise = on_advertise
        self.on_scan = on_scan
        self.on_remove = on_remove
        self.suggestion = suggestion or {}
        self.case_label = case_label
        self.case_id = case_id

        self.frame = tk.Frame(
            parent,
            bg=CARD_BG,
            bd=1,
            relief="solid",
            highlightbackground=CARD_BORDER,
            highlightcolor=CARD_BORDER,
            highlightthickness=1,
            padx=12,
            pady=10,
        )

        self.category_var = tk.StringVar()
        self.manual_tags_var = tk.StringVar()
        self.case_label_var = tk.StringVar(value=self._format_case_label())

        self._build()
        self._populate_categories()

    def _build(self) -> None:
        top_row = tk.Frame(self.frame, bg=CARD_BG)
        top_row.grid(row=0, column=0, sticky="ew")
        top_row.columnconfigure(0, weight=1)

        tk.Label(
            top_row,
            text=os.path.basename(self.path),
            font=("Segoe UI", 11, "bold"),
            bg=CARD_BG,
            fg="#1f2933",
        ).grid(row=0, column=0, sticky="w")
        ttk.Button(top_row, text="Remove", width=10, command=self._handle_remove).grid(row=0, column=1, sticky="e")

        tk.Label(
            self.frame,
            text=self.path,
            bg=CARD_BG,
            fg="#5f6a7a",
            font=("Segoe UI", 9),
        ).grid(row=1, column=0, sticky="w", pady=(2, 4))

        self.case_badge = tk.Label(
            self.frame,
            textvariable=self.case_label_var,
            bg=CARD_BG,
            fg="#2563eb",
            font=("Segoe UI", 9, "bold"),
        )
        self.case_badge.grid(row=2, column=0, sticky="w", pady=(0, 6))

        meta_frame = tk.Frame(self.frame, bg=CARD_BG)
        meta_frame.grid(row=3, column=0, sticky="ew", pady=(2, 8))
        meta_frame.columnconfigure(1, weight=1)

        tk.Label(meta_frame, text="Category:", bg=CARD_BG, fg="#1f2933").grid(row=0, column=0, sticky="w")
        self.category_combo = ttk.Combobox(meta_frame, textvariable=self.category_var, state="readonly", height=12)
        self.category_combo.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        self.category_combo.bind("<<ComboboxSelected>>", self._update_category_details)

        tk.Label(meta_frame, text="Manual tags:", bg=CARD_BG, fg="#1f2933").grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(meta_frame, textvariable=self.manual_tags_var).grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(6, 0))

        self.detail_label = tk.Label(
            self.frame,
            text="",
            bg=CARD_BG,
            fg="#3a3f44",
            justify="left",
            wraplength=460,
            font=("Segoe UI", 9),
        )
        self.detail_label.grid(row=4, column=0, sticky="ew", pady=(4, 10))

        button_row = tk.Frame(self.frame, bg=CARD_BG)
        button_row.grid(row=5, column=0, sticky="ew")
        button_row.columnconfigure((0, 1), weight=1)

        ttk.Button(button_row, text="Advertise Need", command=self._handle_advertise).grid(row=0, column=0, padx=4, sticky="ew")
        ttk.Button(button_row, text="Scan Evidence", command=self._handle_scan).grid(row=0, column=1, padx=4, sticky="ew")

    def _populate_categories(self) -> None:
        options = []
        suggested_slug = self.suggestion.get("category")
        default_slug = suggested_slug
        for entry in self.categories:
            slug = str(entry.get("slug"))
            label = str(entry.get("label", slug))
            options.append(f"{label} ({slug})")
            if default_slug is None:
                default_slug = slug
        self.category_combo["values"] = options
        if default_slug:
            self.set_category(default_slug)
        manual_tags = self.suggestion.get("manual_tags") or []
        if manual_tags:
            self.manual_tags_var.set(", ".join(manual_tags))

    def set_case_context(self, case_label: Optional[str], case_id: Optional[str]) -> None:
        self.case_label = case_label
        self.case_id = case_id
        self.case_label_var.set(self._format_case_label())

    def apply_suggestion(self) -> Optional[str]:
        slug: Optional[str] = None
        if self.suggestion:
            slug = self.suggestion.get("category")
            manual_tags = self.suggestion.get("manual_tags") or self.suggestion.get("tags")
            if manual_tags:
                self.manual_tags_var.set(", ".join(manual_tags))
        if slug:
            self.set_category(slug)
        else:
            self._update_category_details()
        return slug

    def _format_case_label(self) -> str:
        label = self.case_label or "Unassigned"
        identifier = self.case_id
        if identifier and identifier not in label:
            return f"Assigned case: {label} ({identifier})"
        return f"Assigned case: {label}"

    def set_category(self, slug: str) -> None:
        for idx, entry in enumerate(self.categories):
            if entry.get("slug") == slug:
                display = self.category_combo["values"][idx]
                self.category_var.set(display)
                self._update_category_details()
                return

    def _selected_slug(self) -> Optional[str]:
        value = self.category_var.get()
        if not value:
            return None
        if "(" in value and value.endswith(")"):
            return value[value.rfind("(") + 1 : -1]
        return value

    def _current_tags(self) -> List[str]:
        raw = self.manual_tags_var.get().strip()
        if not raw:
            return []
        return [item.strip() for item in raw.split(",") if item.strip()]

    def _lookup_category(self, slug: Optional[str]) -> Dict[str, object]:
        for entry in self.categories:
            if str(entry.get("slug")) == str(slug):
                return entry
        return {}

    def _update_category_details(self, event: Optional[tk.Event] = None) -> None:
        slug = self._selected_slug()
        entry = self._lookup_category(slug)
        tags = ", ".join(entry.get("tags", [])) or "n/a"
        aliases = ", ".join(entry.get("aliases", [])) or "n/a"
        primary = entry.get("primary_section") or "n/a"
        related = ", ".join(entry.get("related_sections", [])) or "n/a"
        detail = (
            f"Primary tags: {tags}\n"
            f"Aliases: {aliases}\n"
            f"Primary section: {primary}\n"
            f"Related sections: {related}"
        )
        self.detail_label.configure(text=detail)

    def _handle_advertise(self) -> None:
        slug = self._selected_slug()
        if slug:
            self.on_advertise(self, slug, self._current_tags())

    def _handle_scan(self) -> None:
        slug = self._selected_slug()
        if slug:
            self.on_scan(self, slug, self._current_tags())

    def _handle_remove(self) -> None:
        self.on_remove(self)

    def destroy(self) -> None:
        self.frame.destroy()


class EnhancedDKIGUI:
    """Main GUI class used by gui_main_application."""

    def __init__(self) -> None:
        self.root = tkdnd.Tk() if DND_AVAILABLE else tk.Tk()
        self.root.title(APP_TITLE)
        self.root.minsize(*MIN_WINDOW_SIZE)
        self.root.geometry("1280x820")
        self.root.configure(bg="#0f172a")
        ttk.Style(self.root).theme_use("clam")

        self.profile_registry = ProfileRegistry(Path(__file__).resolve().parent)
        self.profile_data: Dict[str, object] = self.profile_registry.get_raw_profile()
        self.profile: Profile = self.profile_registry.load_profile()
        self.operator_name: str = self.profile.display_name

        self.plugin: Optional[CentralPluginAdapter] = None
        self.categories: List[Dict[str, object]] = []
        self.cards: List[EvidenceCard] = []
        self.current_report: Optional[Dict[str, Any]] = None

        self.report_text: Optional[ScrolledText] = None
        self.home_profile_text = tk.StringVar()
        self.home_case_text = tk.StringVar()
        self.log_area: Optional[ScrolledText] = None
        self.status_bar: Optional[StatusBar] = None
        self.spaces: Dict[str, tk.Widget] = {}
        self.nav_buttons: Dict[str, ttk.Button] = {}
        self.active_space: Optional[str] = None
        self.case_overview: Dict[str, List[Dict[str, Any]]] = {"open": [], "archived": []}
        self.case_summary_text = tk.StringVar(value="No cases loaded yet.")
        self.workspace_case_text = tk.StringVar(value="No case selected")
        self.workspace_overview_text = tk.StringVar(value="Select a case to view details.")
        self.workspace_drop_message = tk.StringVar(value="Drop evidence files here or click to browse")
        self.operator_label_var = tk.StringVar(value=f"Operator: {self.operator_name}")
        self.bus_state_var = tk.StringVar(value="Bus: pending")
        self.status_message_var = tk.StringVar(value="Initializing UI...")
        self.active_space_title = tk.StringVar(value="Home Overview")
        self.home_status_var = tk.StringVar(value="Ready")
        self.home_active_case_var = tk.StringVar(value="No active case")
        self.home_bus_health_var = tk.StringVar(value="Connection: pending")
        self.home_job_summary_var = tk.StringVar(value="Jobs: none queued")
        self.home_operator_summary_var = tk.StringVar(value="Operator: n/a")
        self.home_activity_tree: Optional[ttk.Treeview] = None
        self.background_jobs: Dict[str, Dict[str, Any]] = {}
        self._gui_bus_handlers_registered = False
        self._home_refresh_after_id: Optional[str] = None
        self.access_rules: Optional[AccessRules] = None
        self.operator_manager: Optional[OperatorManager] = None
        self.operator_profile: Optional[OperatorProfile] = None
        self.operator_token_payload: Optional[Dict[str, Any]] = None
        self.operator_feature_enabled: bool = False
        self.operator_profiles_cache: List[OperatorProfile] = []
        self._initialize_operator_scaffold()
        self.active_case_id: Optional[str] = None
        self.active_case_data: Optional[Dict[str, Any]] = None
        self.workspace_recent_limit = 6
        self.cases_canvas: Optional[tk.Canvas] = None
        self.case_list_frame: Optional[ttk.Frame] = None
        self.case_list_window: Optional[int] = None
        self.category_label_lookup: Dict[str, str] = {}
        self.card_case_map: Dict[EvidenceCard, Optional[str]] = {}
        self.cards_window: Optional[int] = None
        self.review_case_label = tk.StringVar(value="No case selected")
        self.review_status_text = tk.StringVar(value="Select a case to view sections.")
        self.review_ready_text = tk.StringVar(value="Readiness: n/a")
        self.review_tree: Optional[ttk.Treeview] = None
        self.review_payload_text: Optional[ScrolledText] = None
        self.review_draft_text: Optional[ScrolledText] = None
        self.review_summary_text: Optional[ScrolledText] = None
        self.review_sections: List[Dict[str, Any]] = []
        self.review_section_map: Dict[str, Dict[str, Any]] = {}
        self.review_manual_edits: Dict[str, str] = {}
        self.review_selected_section: Optional[str] = None
        self.current_review_payload: Optional[Dict[str, Any]] = None
        self.review_ready_label: Optional[tk.Label] = None
        self.case_snapshots: Dict[str, List[Dict[str, Any]]] = {}
        self._review_bus_handlers_registered = False
        self._prompt_new_case = self._prompt_new_case_dialog

        self._build_layout()
        self._initialize_plugin()
        self._refresh_report_summary()
        self._set_operator(self.operator_name)
        self._refresh_home_overview()
        self._show_login_dialog(initial=True)

    def _initialize_operator_scaffold(self) -> None:
        try:
            self.access_rules = AccessRules()
            self.operator_manager = OperatorManager(self.access_rules)
            self.operator_feature_enabled = bool(getattr(self.access_rules, 'enabled', False))
        except Exception as exc:
            self.access_rules = None
            self.operator_manager = None
            self.operator_feature_enabled = False
            self._append_log(f"Operator management scaffold unavailable: {exc}")
            return

        try:
            self.operator_profiles_cache = self.operator_manager.list_all()
        except Exception as exc:
            self.operator_profiles_cache = []
            self._append_log(f"Unable to read operator profiles: {exc}")

        if not self.operator_profiles_cache:
            default_name = self.profile.display_name or self.operator_name or 'Analyst'
            try:
                profile = self.operator_manager.create(name=default_name)
                self.operator_profiles_cache.append(profile)
            except Exception as exc:
                self._append_log(f"Failed to bootstrap operator profile: {exc}")

        if self.operator_profiles_cache and not self.operator_profile:
            self.operator_profile = self.operator_profiles_cache[0]
            self.operator_name = self.operator_profile.name

    # -- Layout ---------------------------------------------------------
    def _build_layout(self) -> None:
        """Construct the primary window layout with header, navigation, and content panes."""
        self._build_menu()

        style = ttk.Style(self.root)
        style.configure("MainArea.TFrame", background="#f8fafc")
        style.configure("Header.TFrame", background="#0f172a")
        style.configure("Quick.TButton", padding=(12, 6), font=("Segoe UI", 10, "bold"))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=1)
        self.root.rowconfigure(2, weight=0)

        header = ttk.Frame(self.root, style="Header.TFrame", padding=(22, 18, 22, 14))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        header.columnconfigure(1, weight=1)

        title_label = tk.Label(
            header,
            text=APP_TITLE,
            fg="#e2e8f0",
            bg="#0f172a",
            font=("Segoe UI", 20, "bold"),
        )
        title_label.grid(row=0, column=0, sticky="w")

        self.view_label = tk.Label(
            header,
            textvariable=self.active_space_title,
            fg="#94a3b8",
            bg="#0f172a",
            font=("Segoe UI", 11),
        )
        self.view_label.grid(row=1, column=0, sticky="w", pady=(4, 0))

        bus_label = tk.Label(
            header,
            textvariable=self.bus_state_var,
            fg="#60a5fa",
            bg="#0f172a",
            font=("Segoe UI", 10, "italic"),
        )
        bus_label.grid(row=0, column=1, sticky="e")

        self.operator_label = tk.Label(
            header,
            textvariable=self.operator_label_var,
            fg="#cbd5f5",
            bg="#0f172a",
            font=("Segoe UI", 10),
        )
        self.operator_label.grid(row=1, column=1, sticky="e")

        quick_bar = ttk.Frame(header, padding=(0, 10, 0, 0), style="Header.TFrame")
        quick_bar.grid(row=2, column=0, columnspan=2, sticky="ew")
        for idx, (label, command) in enumerate((
            ("New Case", self._prompt_new_case),
            ("Open Workspace", self._open_workspace_tab),
            ("Refresh Overview", self._refresh_case_overview),
        )):
            btn = ttk.Button(quick_bar, text=label, style="Quick.TButton", command=command)
            btn.grid(row=0, column=idx, padx=(0 if idx == 0 else 10, 0))

        status_label = tk.Label(
            header,
            textvariable=self.status_message_var,
            fg="#cbd5f5",
            bg="#0f172a",
            font=("Segoe UI", 10),
        )
        status_label.grid(row=3, column=0, columnspan=2, sticky="w", pady=(6, 0))

        paned = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        paned.grid(row=1, column=0, sticky="nsew")

        nav_container = tk.Frame(paned, bg="#0f172a", width=240)
        content_container = ttk.Frame(paned, style="MainArea.TFrame", padding=(24, 24))
        paned.add(nav_container, weight=0)
        paned.add(content_container, weight=1)

        content_container.columnconfigure(0, weight=1)
        content_container.rowconfigure(0, weight=1)

        stack_frame = ttk.Frame(content_container, style="MainArea.TFrame")
        stack_frame.grid(row=0, column=0, sticky="nsew")
        stack_frame.columnconfigure(0, weight=1)
        stack_frame.rowconfigure(0, weight=1)

        tab_definitions = [
            ("home", "Home Overview", self._build_home_tab),
            ("cases", "Case Library", self._build_cases_tab),
            ("workspace", "Workspace", self._build_workspace_tab),
            ("review", "Review Console", self._build_review_tab),
            ("assembly", "Assembly Studio", self._build_assembly_tab),
        ]

        self._nav_tab_order = [(key, title) for key, title, _ in tab_definitions]
        self.spaces = {}
        self.spaces_titles = {key: title for key, title, _ in tab_definitions}

        for key, _title, builder in tab_definitions:
            frame = ttk.Frame(stack_frame, style="MainArea.TFrame")
            frame.grid(row=0, column=0, sticky="nsew")
            builder(frame)
            self.spaces[key] = frame

        self._build_touch_nav(nav_container)
        self._select_tab("home")

        self.status_bar = StatusBar(self.root)
        self.status_bar.grid(row=2, column=0, sticky="ew")
        self.status_bar.add_section("profile", f"Operator: {self.operator_name}", weight=1)
        self.status_bar.add_section("status", self.status_message_var.get(), weight=2)
        self.status_bar.add_section("bus", self.bus_state_var.get(), weight=1)
        self.status_bar.add_section("cards", "Evidence cards: 0", weight=1)
        self.status_bar.add_section("jobs", "Jobs: 0 queued", weight=1)
    def _build_menu(self) -> None:
        menubar = tk.Menu(self.root)

        profile_menu = tk.Menu(menubar, tearoff=0)
        profile_menu.add_command(label="Switch Operator", command=self._show_login_dialog)
        profile_menu.add_command(label="Edit Profile", command=self._open_profile_editor)
        menubar.add_cascade(label="Profile", menu=profile_menu)

        navigate_menu = tk.Menu(menubar, tearoff=0)
        navigate_menu.add_command(label="Home", command=lambda: self._select_tab("home"))
        navigate_menu.add_command(label="Cases", command=lambda: self._select_tab("cases"))
        navigate_menu.add_command(label="Workspace", command=lambda: self._select_tab("workspace"))
        navigate_menu.add_command(label="Review", command=lambda: self._select_tab("review"))
        navigate_menu.add_command(label="Assembly", command=lambda: self._select_tab("assembly"))
        menubar.add_cascade(label="Navigate", menu=navigate_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=lambda: messagebox.showinfo(APP_TITLE, "Central Command GUI build 2025.10"))
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    def _build_touch_nav(self, parent: tk.Widget) -> None:
        for child in parent.winfo_children():
            child.destroy()

        parent.configure(bg="#10172a")
        self.nav_buttons.clear()

        style = ttk.Style(self.root)
        style.configure("NavPrimary.TButton", padding=(18, 14), font=("Segoe UI", 11, "bold"), anchor="w")
        style.map("NavPrimary.TButton", background=[("disabled", "#2563eb")], foreground=[("disabled", "#f8fafc")])

        tk.Label(
            parent,
            text="Command Navigation",
            bg="#10172a",
            fg="#e2e8f0",
            font=("Segoe UI", 13, "bold"),
            justify="left",
        ).pack(fill="x", padx=18, pady=(24, 12))

        subtitle = tk.Label(
            parent,
            text="Choose a workspace to continue.",
            bg="#10172a",
            fg="#94a3b8",
            font=("Segoe UI", 10),
            justify="left",
        )
        subtitle.pack(fill="x", padx=18, pady=(0, 18))

        for key, label in getattr(self, '_nav_tab_order', []):
            button = ttk.Button(parent, text=label, style="NavPrimary.TButton", command=lambda k=key: self._select_tab(k))
            button.pack(fill="x", padx=18, pady=(0, 12))
            self.nav_buttons[key] = button

        tk.Frame(parent, bg="#10172a").pack(expand=True, fill="both")

    def _select_tab(self, key: str) -> None:
        target = self.spaces.get(key)
        if not target:
            return

        target.tkraise()
        self.active_space = key
        self.active_space_title.set(self.spaces_titles.get(key, key.title()))

        for space_key, button in self.nav_buttons.items():
            if space_key == key:
                button.state(["disabled"])
            else:
                button.state(["!disabled"])
    def _build_home_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=2)
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(1, weight=1)

        status_card = ttk.LabelFrame(parent, text="System Status", padding=18)
        status_card.grid(row=0, column=0, sticky="ew", padx=(0, 18), pady=(0, 18))
        status_card.columnconfigure(1, weight=1)
        ttk.Label(status_card, text="Current State", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(status_card, textvariable=self.home_status_var).grid(row=0, column=1, sticky="w")
        ttk.Label(status_card, text="Bus Health", font=("Segoe UI", 11, "bold")).grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Label(status_card, textvariable=self.home_bus_health_var).grid(row=1, column=1, sticky="w", pady=(8, 0))
        ttk.Label(status_card, text="Jobs", font=("Segoe UI", 11, "bold")).grid(row=2, column=0, sticky="w", pady=(8, 0))
        ttk.Label(status_card, textvariable=self.home_job_summary_var).grid(row=2, column=1, sticky="w", pady=(8, 0))
        ttk.Label(status_card, text="Operator", font=("Segoe UI", 11, "bold")).grid(row=3, column=0, sticky="w", pady=(8, 0))
        ttk.Label(status_card, textvariable=self.home_operator_summary_var).grid(row=3, column=1, sticky="w", pady=(8, 0))
        ttk.Label(status_card, text="Active Case", font=("Segoe UI", 11, "bold")).grid(row=4, column=0, sticky="w", pady=(8, 0))
        ttk.Label(status_card, textvariable=self.home_active_case_var).grid(row=4, column=1, sticky="w", pady=(8, 0))

        profile_card = ttk.LabelFrame(parent, text="Analyst Profile", padding=18)
        profile_card.grid(row=1, column=0, sticky="nsew", padx=(0, 18))
        profile_card.columnconfigure(0, weight=1)
        ttk.Label(profile_card, textvariable=self.home_profile_text, justify="left").grid(row=0, column=0, sticky="w")

        defaults_card = ttk.LabelFrame(parent, text="Case Defaults", padding=18)
        defaults_card.grid(row=2, column=0, sticky="ew", padx=(0, 18), pady=(18, 0))
        defaults_card.columnconfigure(0, weight=1)
        ttk.Label(defaults_card, textvariable=self.home_case_text, justify="left").grid(row=0, column=0, sticky="w")
        actions_row = ttk.Frame(defaults_card)
        actions_row.grid(row=1, column=0, sticky="w", pady=(12, 0))
        ttk.Button(actions_row, text="Open Workspace", command=self._open_workspace_tab).pack(side="left")
        ttk.Button(actions_row, text="Refresh Profile", command=self._refresh_home_overview).pack(side="left", padx=(12, 0))

        activity_card = ttk.LabelFrame(parent, text="Recent Automation Activity", padding=12)
        activity_card.grid(row=0, column=1, rowspan=3, sticky="nsew")
        activity_card.columnconfigure(0, weight=1)
        activity_card.rowconfigure(0, weight=1)

        columns = ("timestamp", "source", "message")
        tree = ttk.Treeview(activity_card, columns=columns, show="headings", height=12)
        tree.heading("timestamp", text="Time")
        tree.heading("source", text="Source")
        tree.heading("message", text="Summary")
        tree.column("timestamp", width=150, anchor="w")
        tree.column("source", width=120, anchor="w")
        tree.column("message", anchor="w")
        tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(activity_card, orient="vertical", command=tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        tree.configure(yscrollcommand=scrollbar.set)
        self.home_activity_tree = tree

        refresh_bar = ttk.Frame(activity_card)
        refresh_bar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        ttk.Button(refresh_bar, text="Refresh Activity", command=self._refresh_home_overview).pack(side="right")

        empty_notice = ttk.Label(activity_card, text="Automation events will appear here as the system processes tasks.", foreground="#6366f1")
        empty_notice.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        empty_notice.configure(anchor="center")
        tree._empty_notice = empty_notice  # type: ignore[attr-defined]

        self._refresh_home_overview()
    def _build_cases_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        style = ttk.Style(self.root)
        style.configure("CaseSummary.TLabel", font=("Segoe UI", 10))
        style.configure("CaseCard.TFrame", padding=18, relief="raised")
        style.configure("CaseTitle.TLabel", font=("Segoe UI", 14, "bold"))
        style.configure("CaseMeta.TLabel", font=("Segoe UI", 10))
        style.configure("CaseStatusOpen.TLabel", foreground="#047857", font=("Segoe UI", 10, "bold"))
        style.configure("CaseStatusClosed.TLabel", foreground="#7c3aed", font=("Segoe UI", 10, "bold"))
        style.configure("TouchAction.TButton", padding=(20, 14), font=("Segoe UI", 12, "bold"))
        style.configure("CaseAction.TButton", padding=(16, 10), font=("Segoe UI", 11, "bold"))

        header = ttk.Frame(parent, padding=(0, 0, 0, 12))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        ttk.Label(header, textvariable=self.case_summary_text, style="CaseSummary.TLabel", wraplength=520, justify="left").grid(row=0, column=0, sticky="w")

        actions = ttk.Frame(header)
        actions.grid(row=0, column=1, sticky="e", padx=(12, 0))
        ttk.Button(actions, text="Start New Case", style="TouchAction.TButton", command=self._open_workspace_tab).pack(side="left")
        ttk.Button(actions, text="Refresh List", style="TouchAction.TButton", command=self._refresh_case_overview).pack(side="left", padx=(12, 0))

        canvas_holder = ttk.Frame(parent)
        canvas_holder.grid(row=1, column=0, sticky="nsew")
        canvas_holder.columnconfigure(0, weight=1)
        canvas_holder.rowconfigure(0, weight=1)

        self.cases_canvas = tk.Canvas(canvas_holder, highlightthickness=0, bg="#f3f4f6")
        self.cases_canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(canvas_holder, orient="vertical", command=self.cases_canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.cases_canvas.configure(yscrollcommand=scrollbar.set)

        self.case_list_frame = ttk.Frame(self.cases_canvas, padding=(12, 12))
        self.case_list_window = self.cases_canvas.create_window((0, 0), window=self.case_list_frame, anchor="nw")
        self.case_list_frame.columnconfigure(0, weight=1)

        self.case_list_frame.bind("<Configure>", lambda _e: self.cases_canvas.configure(scrollregion=self.cases_canvas.bbox("all")))
        self.cases_canvas.bind("<Configure>", lambda event: self.cases_canvas.itemconfigure(self.case_list_window, width=event.width))

        self._render_case_lists(self.case_overview)


    def _refresh_case_overview(self) -> None:
        overview = self._collect_case_overview()
        self.case_overview = overview
        open_cases = overview.get("open", [])
        archived_cases = overview.get("archived", [])
        summary_parts = [f"Open cases: {len(open_cases)}", f"Archived: {len(archived_cases)}"]
        latest = None
        if open_cases:
            latest = open_cases[0].get("last_seen_display")
        elif archived_cases:
            latest = archived_cases[0].get("last_seen_display")
        if latest and latest != "n/a":
            summary_parts.append(f"Last activity: {latest}")
        self.case_summary_text.set(" | ".join(summary_parts))
        container = getattr(self, "case_list_frame", None)
        if container and container.winfo_exists():
            self._render_case_lists(overview)

        if self.active_case_id:
            current_case = self._find_case_by_id(overview, self.active_case_id)
            if current_case:
                self._set_active_case(current_case, navigate=False)
            else:
                fallback = open_cases[0] if open_cases else (archived_cases[0] if archived_cases else None)
                self._set_active_case(fallback, navigate=False)
        else:
            fallback = open_cases[0] if open_cases else (archived_cases[0] if archived_cases else None)
            self._set_active_case(fallback, navigate=False)

        if self.status_bar:
            self.status_bar.update_section("status", f"Cases loaded: {len(open_cases)} open")
        self._schedule_home_refresh()

    def _collect_case_overview(self) -> Dict[str, List[Dict[str, Any]]]:
        overview: Dict[str, List[Dict[str, Any]]] = {"open": [], "archived": []}
        try:
            defaults = self.profile.payload.get("case_defaults", {}) if self.profile else {}
        except Exception:
            defaults = {}
        entries: List[Dict[str, Any]] = []
        if self.plugin:
            try:
                entries = self.plugin.list_scanned_evidence()
            except Exception as exc:
                self._append_log(f"Failed to load scanned evidence: {exc}")
        groups: Dict[str, Dict[str, Any]] = {}
        for entry in entries:
            response = entry.get("response") or {}
            case_info = response.get("case") if isinstance(response.get("case"), dict) else {}
            case_id = (
                response.get("case_id")
                or case_info.get("id")
                or response.get("case_number")
                or entry.get("case_id")
                or entry.get("case_number")
                or defaults.get("case_number")
            )
            if not case_id:
                case_id = f"case-{len(groups) + 1}"
            record = groups.setdefault(
                case_id,
                {
                    "case_id": case_id,
                    "display_name": case_info.get("name") or response.get("case_name") or case_id,
                    "client": case_info.get("client") or response.get("client_name") or defaults.get("client_name") or self.profile_data.get("business_name", "Client"),
                    "subject": case_info.get("subject") or response.get("subject") or defaults.get("subject") or "Primary Subject",
                    "status": (case_info.get("status") or response.get("status") or "open").lower(),
                    "evidence": [],
                    "tags": set(),
                    "categories": set(),
                    "last_seen": None,
                    "last_seen_sort": None,
                },
            )
            record["display_name"] = case_info.get("name") or response.get("case_name") or record["display_name"]
            record["client"] = case_info.get("client") or response.get("client_name") or record["client"]
            record["subject"] = case_info.get("subject") or response.get("subject") or record["subject"]
            record["status"] = (case_info.get("status") or response.get("status") or record["status"]).lower()
            record["evidence"].append(entry)
            record["tags"].update(entry.get("tags", []))
            slug = response.get("category") or entry.get("category")
            if slug:
                record["categories"].add(slug)
            timestamp = entry.get("timestamp") or response.get("timestamp") or response.get("updated_at") or response.get("created_at")
            dt = self._parse_timestamp(timestamp)
            if dt is not None:
                if record["last_seen"] is None or dt > record["last_seen"]:
                    record["last_seen"] = dt
                    record["last_seen_sort"] = dt.timestamp()
        archived_states = {"closed", "archived", "complete", "completed", "inactive"}
        for record in groups.values():
            record["evidence_count"] = len(record["evidence"])
            record["tags"] = sorted({tag.strip() for tag in record["tags"] if tag})
            record["categories"] = sorted({cat for cat in record["categories"] if cat})
            record["last_seen_display"] = self._format_timestamp(record.get("last_seen"))
            record["status_label"] = record["status"].upper()
            target = "archived" if record["status"] in archived_states else "open"
            overview[target].append(record)
        if not overview["open"]:
            if defaults:
                fallback_id = defaults.get("case_number") or "workspace-case"
                overview["open"].append(
                    {
                        "case_id": fallback_id,
                        "display_name": defaults.get("case_number") or "Workspace Case",
                        "client": defaults.get("client_name") or self.profile_data.get("business_name", "Client"),
                        "subject": defaults.get("subject") or "Primary Subject",
                        "status": "open",
                        "status_label": "OPEN",
                        "evidence": [],
                        "evidence_count": 0,
                        "tags": [],
                        "categories": [],
                        "last_seen": None,
                        "last_seen_display": "n/a",
                        "last_seen_sort": None,
                    }
                )
            elif not entries:
                overview["open"].append(
                    {
                        "case_id": "workspace-case",
                        "display_name": "Workspace Case",
                        "client": self.profile_data.get("business_name", "Client"),
                        "subject": "Primary Subject",
                        "status": "open",
                        "status_label": "OPEN",
                        "evidence": [],
                        "evidence_count": 0,
                        "tags": [],
                        "categories": [],
                        "last_seen": None,
                        "last_seen_display": "n/a",
                        "last_seen_sort": None,
                    }
                )
        overview["open"].sort(key=lambda item: item.get("last_seen_sort") or -1, reverse=True)
        overview["archived"].sort(key=lambda item: item.get("last_seen_sort") or -1, reverse=True)
        return overview

    def _render_case_lists(self, overview: Dict[str, List[Dict[str, Any]]]) -> None:
        container = getattr(self, "case_list_frame", None)
        if not container or not container.winfo_exists():
            return
        for child in container.winfo_children():
            child.destroy()
        self._render_case_section(
            container,
            "Active Cases",
            overview.get("open", []),
            "No open cases yet. Start a new workspace or scan evidence to begin.",
        )
        self._render_case_section(
            container,
            "Archived Cases",
            overview.get("archived", []),
            "No archived cases yet. Exports will appear here when completed.",
        )

    def _render_case_section(self, parent: ttk.Frame, title: str, cases: List[Dict[str, Any]], empty_message: str) -> None:
        section = ttk.LabelFrame(parent, text=title, padding=16)
        section.pack(fill="x", expand=True, pady=(0, 12))
        section.columnconfigure(0, weight=1)
        if not cases:
            ttk.Label(section, text=empty_message, style="CaseMeta.TLabel", justify="left", wraplength=680).grid(row=0, column=0, sticky="w")
            return
        for idx, case_data in enumerate(cases):
            archived = title.lower().startswith("archived")
            self._build_case_card(section, case_data, archived=archived)
            if idx < len(cases) - 1:
                ttk.Separator(section, orient="horizontal").pack(fill="x", pady=6)

    def _build_case_card(self, parent: ttk.Frame, case_data: Dict[str, Any], *, archived: bool = False) -> None:
        card = ttk.Frame(parent, style="CaseCard.TFrame")
        card.pack(fill="x", expand=True, pady=6)
        card.columnconfigure(0, weight=1)
        title = case_data.get("display_name") or case_data.get("case_id")
        ttk.Label(card, text=title, style="CaseTitle.TLabel").grid(row=0, column=0, sticky="w")
        status_style = "CaseStatusClosed.TLabel" if archived else "CaseStatusOpen.TLabel"
        ttk.Label(card, text=case_data.get("status_label", "ARCHIVED" if archived else "OPEN"), style=status_style).grid(row=0, column=1, sticky="e")
        meta_lines = [
            f"Case ID: {case_data.get('case_id', 'n/a')}",
            f"Client: {case_data.get('client', 'n/a')}",
            f"Subject: {case_data.get('subject', 'n/a')}",
            f"Evidence items: {case_data.get('evidence_count', 0)}",
            f"Last activity: {case_data.get('last_seen_display', 'n/a')}",
        ]
        ttk.Label(card, text="\n".join(meta_lines), style="CaseMeta.TLabel", justify="left", wraplength=720).grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 4))
        tags = case_data.get("tags") or []
        tag_text = ", ".join(tags[:12]) + (" ..." if len(tags) > 12 else "") if tags else "No tags recorded yet."
        ttk.Label(card, text=f"Tags: {tag_text}", style="CaseMeta.TLabel", justify="left", wraplength=720).grid(row=2, column=0, columnspan=2, sticky="w")
        action_row = ttk.Frame(card)
        action_row.grid(row=3, column=0, columnspan=2, sticky="w", pady=(12, 0))
        if archived:
            ttk.Button(action_row, text="View Summary", style="CaseAction.TButton", command=lambda d=case_data: self._view_case_summary(d)).pack(side="left")
            ttk.Button(action_row, text="Reopen in Workspace", style="CaseAction.TButton", command=lambda d=case_data: self._open_case_workspace(d)).pack(side="left", padx=(12, 0))
        else:
            ttk.Button(action_row, text="Open Workspace", style="CaseAction.TButton", command=lambda d=case_data: self._open_case_workspace(d)).pack(side="left")
            ttk.Button(action_row, text="View Summary", style="CaseAction.TButton", command=lambda d=case_data: self._view_case_summary(d)).pack(side="left", padx=(12, 0))

    def _format_timestamp(self, value: Optional[Any]) -> str:
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M")
        if isinstance(value, str):
            parsed = self._parse_timestamp(value)
            if parsed:
                return parsed.strftime("%Y-%m-%d %H:%M")
        return "n/a"

    def _parse_timestamp(self, value: Optional[Any]) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        cleaned = str(value).strip()
        if not cleaned:
            return None
        if cleaned.endswith("Z") and not cleaned.endswith("+00:00"):
            cleaned = cleaned[:-1] + "+0000"
        formats = [
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d",
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(cleaned, fmt)
                if dt.tzinfo:
                    dt = dt.astimezone().replace(tzinfo=None)
                return dt
            except ValueError:
                continue
        return None


    def _open_case_workspace(self, case_data: Dict[str, Any]) -> None:
        self._set_active_case(case_data, navigate=True)

    def _find_case_by_id(
        self,
        overview: Dict[str, List[Dict[str, Any]]],
        case_id: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        if not case_id:
            return None
        target = str(case_id)
        for bucket in ("open", "archived"):
            for record in overview.get(bucket, []):
                if str(record.get("case_id")) == target:
                    return record
        return None

    def _set_active_case(self, case_data: Optional[Dict[str, Any]], *, navigate: bool = False) -> None:
        if not case_data:
            self.active_case_data = None
            self.active_case_id = None
            self.workspace_case_text.set("No case selected")
            self.workspace_overview_text.set("Select a case to view details.")
            self.workspace_drop_message.set("Drop evidence files here or click to browse")
            self._apply_workspace_card_filter()
            self._refresh_review_view(None)
            if self.active_space == "workspace" and self.status_bar:
                self.status_bar.update_section("status", "Workspace ready")
            if navigate:
                self._select_tab("workspace")
            self._renew_operator_token(self.operator_profile)
            return

        self.active_case_data = case_data
        case_identifier = case_data.get("case_id") or case_data.get("case_number") or ""
        self.active_case_id = case_identifier
        label = case_data.get("display_name") or case_identifier or "Case"
        if case_identifier:
            self.workspace_case_text.set(f"{label} ({case_identifier})")
        else:
            self.workspace_case_text.set(label)
        self.workspace_drop_message.set(f"Drop evidence for {label} or click to browse")
        self.workspace_overview_text.set(self._format_workspace_overview(case_data))
        self._apply_workspace_card_filter()
        self._refresh_review_view(case_identifier)
        self._renew_operator_token(self.operator_profile)

        if navigate:
            if self.status_bar:
                self.status_bar.update_section("status", f"Workspace loaded: {label}")
            self._append_log(f"Workspace activated for case {label}.")
            self._select_tab("workspace")
        elif self.active_space == "workspace" and self.status_bar:
            self.status_bar.update_section("status", f"Workspace loaded: {label}")

    def _apply_workspace_card_filter(self) -> None:
        active = self.active_case_id
        row = 0
        for card in self.cards:
            card_case = self.card_case_map.get(card)
            should_display = not active or card_case == active
            if should_display:
                card.frame.grid(row=row, column=0, sticky="ew", pady=6, padx=4)
                row += 1
            else:
                card.frame.grid_remove()
        self._sync_card_count()

    def _refresh_review_view(self, case_id: Optional[str] = None) -> None:
        if not self.review_tree or not self.review_payload_text or not self.review_draft_text:
            return
        if case_id is None:
            case_id = self.active_case_id
        previous_section = self.review_selected_section
        for item in self.review_tree.get_children():
            self.review_tree.delete(item)
        self.review_sections = []
        self.review_section_map = {}
        self._clear_review_display()
        if not case_id or not self.plugin:
            self.review_case_label.set("No case selected")
            self.review_status_text.set("Select a case to view sections.")
            return

        self.review_case_label.set(str(case_id))
        updates: List[Dict[str, Any]] = []
        completions: List[Dict[str, Any]] = []
        case_summary: Optional[Dict[str, Any]] = None
        try:
            updates = self.plugin.get_section_updates(case_id)
        except Exception as exc:
            self._append_log(f"Failed to fetch section updates: {exc}")
        try:
            completions = self.plugin.get_section_completion_log(case_id)
        except Exception as exc:
            self._append_log(f"Failed to fetch section completions: {exc}")
        try:
            case_summary = self.plugin.get_case_summary(case_id)
        except Exception as exc:
            self._append_log(f"Failed to fetch case summary: {exc}")

        rows = self._prepare_review_rows(case_id, updates, completions)
        self.review_sections = rows
        selection_item = None
        for row in rows:
            preview = row["summary"]
            if len(preview) > 90:
                preview = preview[:87].rstrip() + "..."
            status_lower = str(row.get("status", "")).lower()
            payload = row.get("payload") or {}
            if "complete" in status_lower or "ready" in status_lower:
                tags = ("complete",)
            elif payload.get("draft"):
                tags = ("draft",)
            elif "pending" in status_lower or "await" in status_lower:
                tags = ("pending",)
            else:
                tags = ("blocked",)
            item = self.review_tree.insert(
                "",
                "end",
                values=(row["title"], row["status"], row["updated_display"], preview),
                tags=tags,
            )
            self.review_section_map[item] = row
            if selection_item is None and row.get("section_id") == previous_section:
                selection_item = item

        status_line = ""
        if case_summary and isinstance(case_summary, dict):
            status_text = case_summary.get("status") or "pending"
            steps = case_summary.get("steps_completed") or []
            status_line = f"Case status: {status_text}" if status_text else "Case summary available"
            if steps:
                status_line += f" \u2022 Steps completed: {len(steps)}"

        snapshots = self.case_snapshots.get(str(case_id), [])
        if snapshots:
            latest_snapshot = snapshots[-1]
            snapshot_stamp = self._format_timestamp(
                latest_snapshot.get("timestamp") or latest_snapshot.get("created_at") or latest_snapshot.get("updated_at")
            )
            snapshot_line = f"Snapshots: {len(snapshots)}" + (f" (last {snapshot_stamp})" if snapshot_stamp != "n/a" else "")
            status_line = f"{status_line} \u2022 {snapshot_line}" if status_line else snapshot_line

        if rows:
            self.review_status_text.set(status_line or f"{len(rows)} section updates recorded.")
            if selection_item is None:
                selection_item = next(iter(self.review_section_map.keys()))
            row = self.review_section_map[selection_item]
            self.review_tree.selection_set(selection_item)
            self.review_tree.focus(selection_item)
            self._populate_review_detail(row)
        else:
            self.review_status_text.set(status_line or "No section updates received yet.")
            self.review_tree.selection_remove(self.review_tree.selection())
            self._set_review_readiness(None)

    def _prepare_review_rows(
        self,
        case_id: str,
        updates: List[Dict[str, Any]],
        completions: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        completion_index: Dict[str, Dict[str, Any]] = {}
        for entry in completions:
            section_id = entry.get("section_id") or (entry.get("payload") or {}).get("section_id")
            entry_case = entry.get("case_id") or (entry.get("payload") or {}).get("case_id")
            if section_id and (not entry_case or entry_case == case_id):
                completion_index[section_id] = entry
        rows: List[Dict[str, Any]] = []
        for record in updates:
            payload = record.get("payload") or {}
            section_id = record.get("section_id") or payload.get("section_id") or "section"
            title = payload.get("title") or payload.get("section_label") or payload.get("section_name") or section_id
            status = payload.get("status") or payload.get("state")
            if not status and section_id in completion_index:
                status = "complete"
            updated_raw = record.get("received_at") or payload.get("updated_at") or payload.get("timestamp")
            updated_display = self._format_timestamp(updated_raw) if updated_raw else "n/a"
            summary_parts: List[str] = []
            for key in ("summary", "description", "notes"):
                value = payload.get(key)
                if isinstance(value, str) and value.strip():
                    summary_parts.append(value.strip())
                    break
            if not summary_parts:
                needs = payload.get("needs") or payload.get("tags") or []
                if isinstance(needs, (list, tuple)) and needs:
                    summary_parts.append(", ".join(str(item) for item in needs))
            if not summary_parts and payload.get("status_message"):
                summary_parts.append(str(payload.get("status_message")))
            row = {
                "section_id": section_id,
                "title": title,
                "status": str(status).title() if status else ("Complete" if section_id in completion_index else "Updated"),
                "updated_display": updated_display,
                "updated_raw": updated_raw,
                "summary": summary_parts[0] if summary_parts else "",
                "payload": payload,
                "completion": completion_index.get(section_id),
            }
            rows.append(row)
        for section_id, completion in completion_index.items():
            if not any(row["section_id"] == section_id for row in rows):
                payload = completion.get("payload") or {}
                updated_raw = completion.get("received_at") or payload.get("completed_at")
                rows.append(
                    {
                        "section_id": section_id,
                        "title": payload.get("section_label") or payload.get("title") or section_id,
                        "status": str(payload.get("status") or "complete").title(),
                        "updated_display": self._format_timestamp(updated_raw) if updated_raw else "n/a",
                        "updated_raw": updated_raw,
                        "summary": payload.get("summary") or "Section marked complete.",
                        "payload": payload,
                        "completion": completion,
                    }
                )
        rows.sort(key=lambda row: (row.get("updated_raw") or "", row["section_id"]))
        return rows

    def _clear_review_display(self) -> None:
        self.review_selected_section = None
        self.current_review_payload = None
        if self.review_draft_text:
            self.review_draft_text.configure(state="normal")
            self.review_draft_text.delete("1.0", tk.END)
            self.review_draft_text.insert("1.0", "Select a section to review the narrative draft.")
            self.review_draft_text.configure(state="disabled")
        if self.review_payload_text:
            self.review_payload_text.configure(state="normal")
            self.review_payload_text.delete("1.0", tk.END)
            self.review_payload_text.insert("1.0", "Select a section to see payload details.")
            self.review_payload_text.configure(state="disabled")
        self._set_summary_placeholder()
        self._set_review_readiness(None)

    def _populate_review_detail(self, row: Dict[str, Any]) -> None:
        if not self.review_draft_text or not self.review_payload_text:
            return
        section_id = row.get("section_id") or "section"
        self.review_selected_section = section_id
        raw_payload = row.get("payload")
        self.current_review_payload = raw_payload if isinstance(raw_payload, dict) else {}
        payload = self.current_review_payload
        manual_draft = self.review_manual_edits.get(section_id)
        draft_source = manual_draft if manual_draft is not None else (
            payload.get("draft")
            or payload.get("narrative")
            or payload.get("summary")
            or payload.get("description")
        )
        if not draft_source:
            draft_source = ""
        self.review_draft_text.configure(state="normal")
        self.review_draft_text.delete("1.0", tk.END)
        if draft_source:
            self.review_draft_text.insert("1.0", draft_source if draft_source.endswith("\n") else draft_source + "\n")
        else:
            self.review_draft_text.insert("1.0", "No narrative draft received yet.")
        self.review_draft_text.configure(state="normal")
        self.review_draft_text.edit_modified(False)

        metadata_lines = [
            f"Section: {row.get('title', section_id)} ({section_id})",
            f"Status: {row.get('status', 'n/a')}",
            f"Last update: {row.get('updated_display', 'n/a')}",
        ]
        case_id = payload.get("case_id") or row.get("case_id")
        if case_id:
            metadata_lines.append(f"Case ID: {case_id}")
        completion = row.get("completion")
        if completion and isinstance(completion, dict):
            completed_at = completion.get("received_at") or (completion.get("payload") or {}).get("completed_at")
            metadata_lines.append(f"Marked complete: {self._format_timestamp(completed_at)}")
        metadata_lines.append("")
        metadata_lines.append("Payload:")
        self.review_payload_text.configure(state="normal")
        self.review_payload_text.delete("1.0", tk.END)
        self.review_payload_text.insert("1.0", "\n".join(metadata_lines))
        self.review_payload_text.insert(tk.END, "\n")
        self.review_payload_text.insert(tk.END, json.dumps(payload, indent=2, default=str))
        self.review_payload_text.configure(state="disabled")

        payload_points = self._collect_summary_points(payload)
        if payload_points:
            bullets = "\n".join(f"- {point}" for point in payload_points[:5])
            self._update_summary_text(bullets, header="Payload highlights")
        else:
            self._set_summary_placeholder()

        self._set_review_readiness(row)

    def _set_review_readiness(self, row: Optional[Dict[str, Any]]) -> None:
        if not self.review_ready_label:
            return
        if not row:
            self.review_ready_text.set("Readiness: n/a")
            self.review_ready_label.configure(fg="#6b7280")
            return
        status = str(row.get("status", "")).lower()
        payload = row.get("payload") or {}
        if "complete" in status or "ready" in status:
            text = "Readiness: Ready for Assembly"
            color = "#15803d"
        elif payload.get("draft"):
            text = "Readiness: Draft available for review"
            color = "#2563eb"
        else:
            text = "Readiness: Awaiting narrative payload"
            color = "#b91c1c"
        self.review_ready_text.set(text)
        self.review_ready_label.configure(fg=color)

    def _copy_review_draft(self) -> None:
        if not self.review_draft_text:
            return
        draft = self.review_draft_text.get("1.0", tk.END).strip()
        if not draft:
            messagebox.showinfo(APP_TITLE, "No narrative draft available to copy.")
            return
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(draft)
            self.root.update_idletasks()
            self._append_log(f"Copied narrative draft for {self.review_selected_section or 'section'}.")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, f"Failed to copy narrative draft: {exc}")

    def _save_review_edit(self) -> None:
        if not self.review_draft_text or not self.review_selected_section:
            messagebox.showinfo(APP_TITLE, "Select a section before saving edits.")
            return
        draft = self.review_draft_text.get("1.0", tk.END).strip()
        if draft:
            self.review_manual_edits[self.review_selected_section] = draft
            note = f"Draft edits stored for {self.review_selected_section}."
        else:
            self.review_manual_edits.pop(self.review_selected_section, None)
            note = f"Cleared stored draft for {self.review_selected_section}."
        self._append_log(note)
        if self.status_bar:
            self.status_bar.update_section("status", note)

    def _set_summary_placeholder(self) -> None:
        if not self.review_summary_text:
            return
        self.review_summary_text.configure(state="normal")
        self.review_summary_text.delete("1.0", tk.END)
        self.review_summary_text.insert("1.0", "Select 'Summarize Draft' to generate an overview for the active section.")
        self.review_summary_text.configure(state="disabled")

    def _update_summary_text(self, content: str, *, header: Optional[str] = None) -> None:
        if not self.review_summary_text:
            return
        self.review_summary_text.configure(state="normal")
        self.review_summary_text.delete("1.0", tk.END)
        if header:
            self.review_summary_text.insert("1.0", header + "\n\n")
            self.review_summary_text.insert(tk.END, content.strip())
        else:
            self.review_summary_text.insert("1.0", content.strip())
        if not content.endswith("\n"):
            self.review_summary_text.insert(tk.END, "\n")
        self.review_summary_text.configure(state="disabled")

    def _collect_summary_points(self, payload: Dict[str, Any]) -> List[str]:
        points: List[str] = []
        if not isinstance(payload, dict):
            return points
        keys = ("summary", "highlights", "key_findings", "notes", "flags", "alerts", "actions", "recommendations")
        seen: set[str] = set()

        def add_point(value: str) -> None:
            cleaned = value.strip()
            if not cleaned:
                return
            lower = cleaned.lower()
            if lower in seen:
                return
            seen.add(lower)
            points.append(cleaned)

        for key in keys:
            addable = payload.get(key)
            for entry in self._normalize_summary_value(addable):
                add_point(entry)

        metadata = payload.get("metadata")
        if isinstance(metadata, dict):
            for label_key in ("location", "subject", "date", "time", "status", "priority"):
                value = metadata.get(label_key)
                if isinstance(value, str):
                    add_point(f"{label_key.replace('_', ' ').title()}: {value}")
        return points

    def _normalize_summary_value(self, value: Any, *, _depth: int = 0) -> List[str]:
        if _depth > 3 or value is None:
            return []
        results: List[str] = []
        if isinstance(value, str):
            for chunk in re.split(r"[;\r\n]+", value):
                chunk = chunk.strip()
                if chunk:
                    results.append(chunk)
        elif isinstance(value, (int, float)):
            results.append(str(value))
        elif isinstance(value, list):
            for item in value:
                results.extend(self._normalize_summary_value(item, _depth=_depth + 1))
        elif isinstance(value, dict):
            title = value.get("title") or value.get("name") or value.get("label")
            synopsis = value.get("summary") or value.get("description") or value.get("notes")
            if title and synopsis:
                results.append(f"{title}: {synopsis}")
            elif title:
                results.append(str(title))
            elif synopsis:
                results.append(str(synopsis))
            for sub_key, sub_value in value.items():
                if sub_key in ("title", "name", "label", "summary", "description", "notes"):
                    continue
                results.extend(self._normalize_summary_value(sub_value, _depth=_depth + 1))
        return results

    def _summarize_review_draft(self) -> None:
        if not self.review_draft_text or not self.review_summary_text:
            return
        if not self.review_selected_section:
            messagebox.showinfo(APP_TITLE, "Select a section before generating a summary.")
            return
        draft = self.review_draft_text.get("1.0", tk.END).strip()
        payload = self.current_review_payload or {}
        auto_summary = self._generate_auto_summary(draft, payload)
        if not auto_summary:
            messagebox.showinfo(APP_TITLE, "No narrative content available to summarize.")
            return
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        self._update_summary_text(auto_summary, header=f"Auto summary generated {timestamp}")
        self._append_log(f"Summary generated for {self.review_selected_section}.")
        if self.status_bar:
            self.status_bar.update_section("status", f"Summary generated for {self.review_selected_section}")

    def _generate_auto_summary(self, draft_text: str, payload: Dict[str, Any]) -> str:
        points = self._collect_summary_points(payload)
        text_sentences = self._extract_summary_sentences(draft_text, limit=3)
        lines: List[str] = []
        for point in points[:5]:
            lines.append(f"- {point}")
        if text_sentences:
            if lines:
                lines.append("")
            for sentence in text_sentences:
                lines.append(f"- {sentence}")
        return "\n".join(lines).strip()
    def _extract_summary_sentences(self, text: str, *, limit: int = 3) -> List[str]:
        cleaned = (text or "").strip()
        if not cleaned:
            return []
        sentences = [seg.strip() for seg in re.split(r"(?<=[.!?])\s+", cleaned) if seg.strip()]
        if not sentences:
            return []
        if len(sentences) <= limit:
            return sentences
        keywords = {"subject", "client", "observed", "location", "date", "time", "vehicle", "summary", "finding", "evidence", "activity"}
        scored = []
        total = len(sentences)
        for idx, sentence in enumerate(sentences):
            lower = sentence.lower()
            score = 1.0
            if idx == 0:
                score += 1.5
            if idx == total - 1:
                score += 0.8
            score += sum(0.3 for kw in keywords if kw in lower)
            if len(sentence) > 320:
                score -= 0.6
            scored.append((score, idx, sentence))
        top = sorted(scored, key=lambda item: item[0], reverse=True)[:limit]
        top.sort(key=lambda item: item[1])
        return [sentence for _, _, sentence in top]

    def _register_review_bus_handlers(self) -> None:
        if self._review_bus_handlers_registered:
            return
        bus = getattr(self.plugin, "bus", None)
        if not bus:
            return
        try:
            bus.register_signal("section.data.updated", self._handle_review_signal)
            bus.register_signal("mission_debrief.section.update", self._handle_review_signal)
            bus.register_signal("mission_debrief.section.complete", self._handle_review_signal)
            bus.register_signal("case.snapshot", self._handle_case_snapshot_signal)
            self._review_bus_handlers_registered = True
        except Exception as exc:
            self._append_log(f"Failed to register review bus handlers: {exc}")

    def _register_gui_bus_handlers(self) -> None:
        if not self.plugin or not getattr(self.plugin, 'bus', None):
            return
        if self._gui_bus_handlers_registered:
            return
        bus = self.plugin.bus
        signal_map = {
            'narrative.assembled': self._handle_gui_narrative_assembled,
            'section.data.updated': self._handle_gui_section_data,
            'mission_debrief.section.complete': self._handle_gui_mission_complete,
            'mission_debrief.process_report': self._handle_gui_report_processed,
            'gateway.status': self._handle_gui_gateway_status,
            'locker.status': self._handle_gui_gateway_status,
        }
        for signal, handler in signal_map.items():
            try:
                bus.register_signal(signal, handler)
            except Exception as exc:
                self._append_log(f"Unable to register GUI handler for {signal}: {exc}")
        self._gui_bus_handlers_registered = True

    def _schedule_home_refresh(self, message: Optional[str] = None, *, bus_state: Optional[str] = None) -> None:
        if not hasattr(self, 'root'):
            return
        if self._home_refresh_after_id:
            try:
                self.root.after_cancel(self._home_refresh_after_id)
            except Exception:
                pass
            self._home_refresh_after_id = None

        def _update() -> None:
            if message:
                self._update_status(message, bus_state=bus_state)
            elif bus_state is not None:
                self.bus_state_var.set(f"Bus: {bus_state}")
                self.home_bus_health_var.set(f"Connection: {bus_state.title()}")
            self.home_status_var.set(self.status_message_var.get())
            self._refresh_home_overview()
            self._home_refresh_after_id = None

        self._home_refresh_after_id = self.root.after(60, _update)

    def _renew_operator_token(self, profile: Optional[OperatorProfile]) -> None:
        if not profile or not self.operator_manager:
            self.operator_token_payload = None
            return
        try:
            target_case = self.active_case_id or 'GLOBAL'
            self.operator_token_payload = issue_token(profile.operator_id, target_case, profile.role or 'field_operator', hours=24)
        except Exception as exc:
            self.operator_token_payload = None
            self._append_log(f"Failed to issue operator token: {exc}")

    def _handle_gui_narrative_assembled(self, payload: Dict[str, Any]) -> None:
        section = payload.get('section_id') or payload.get('section') or 'section'
        message = f"Narrative ready for {section}"
        self._append_log(message)
        self._schedule_home_refresh(message)

    def _handle_gui_section_data(self, payload: Dict[str, Any]) -> None:
        section = payload.get('section_id') or payload.get('section') or 'section'
        status = payload.get('status') or payload.get('state') or 'updated'
        message = f"Section {section} {status}"
        self._schedule_home_refresh(message)

    def _handle_gui_mission_complete(self, payload: Dict[str, Any]) -> None:
        section = payload.get('section_id') or payload.get('section') or 'section'
        message = f"Professional tools completed for {section}"
        self._schedule_home_refresh(message)

    def _handle_gui_report_processed(self, payload: Dict[str, Any]) -> None:
        outcome = payload.get('status') or 'processed'
        message = f"Mission Debrief report {outcome}"
        self._schedule_home_refresh(message)

    def _handle_gui_gateway_status(self, payload: Dict[str, Any]) -> None:
        status = payload.get('status') or payload.get('state') or 'unknown'
        message = f"Gateway status: {status}"
        bus_state = payload.get('status') or payload.get('state') or 'connected'
        self._schedule_home_refresh(message, bus_state='connected' if bus_state else None)

    def _handle_review_signal(self, payload: Dict[str, Any]) -> None:
        if not isinstance(payload, dict):
            return None
        case_id = payload.get("case_id")
        inner = payload.get("payload")
        if not case_id and isinstance(inner, dict):
            case_id = inner.get("case_id")
        if not case_id:
            case_id = self.active_case_id

        def refresh() -> None:
            target = case_id or self.active_case_id
            if target:
                active = self.active_case_id
                if not active or str(target) == str(active):
                    self._refresh_review_view(str(target))

        try:
            self.root.after(0, refresh)
        except Exception:
            refresh()
        return None

    def _handle_case_snapshot_signal(self, payload: Dict[str, Any]) -> None:
        if not isinstance(payload, dict):
            return None
        case_id = (
            payload.get("case_id")
            or (payload.get("payload") or {}).get("case_id")
            or payload.get("case_number")
        )
        if not case_id:
            return None
        case_key = str(case_id)
        snapshots = self.case_snapshots.setdefault(case_key, [])
        snapshots.append(dict(payload))
        if len(snapshots) > 50:
            self.case_snapshots[case_key] = snapshots[-50:]

        def refresh() -> None:
            if self.active_case_id and str(self.active_case_id) == case_key:
                self._refresh_review_view(case_key)

        try:
            self.root.after(0, refresh)
        except Exception:
            refresh()
        return None
    def _on_review_select(self, _event) -> None:
        if not self.review_tree:
            return
        selection = self.review_tree.selection()
        if not selection:
            self.review_selected_section = None
            self._clear_review_display()
            return
        item_id = selection[0]
        row = self.review_section_map.get(item_id)
        if not row:
            self.review_selected_section = None
            self._clear_review_display()
            return
        self._populate_review_detail(row)

    def _format_workspace_overview(self, case_data: Dict[str, Any]) -> str:
        client = case_data.get("client", "n/a")
        subject = case_data.get("subject", "n/a")
        status = case_data.get("status_label", case_data.get("status", "OPEN"))
        evidence_count = case_data.get("evidence_count", 0)
        last_seen = case_data.get("last_seen_display", "n/a")
        lines = [
            f"Client: {client}",
            f"Subject: {subject}",
            f"Status: {status}",
            f"Evidence items: {evidence_count}",
            f"Last activity: {last_seen}",
        ]

        categories = case_data.get("categories") or []
        if categories:
            labels = [self.category_label_lookup.get(slug, slug) for slug in categories]
            display = ", ".join(labels[:8])
            if len(labels) > 8:
                display += " ..."
            lines.append(f"Categories: {display}")

        tags = case_data.get("tags") or []
        if tags:
            tag_display = ", ".join(tags[:10])
            if len(tags) > 10:
                tag_display += " ..."
            lines.append(f"Tags: {tag_display}")


        evidence_entries = list(case_data.get("evidence") or [])
        if evidence_entries:
            lines.append("")
            lines.append("Recent Evidence:")
            evidence_entries.sort(key=self._evidence_sort_key, reverse=True)
            for entry in evidence_entries[: self.workspace_recent_limit]:
                name = entry.get("name") or os.path.basename(entry.get("file_path") or "") or "Evidence item"
                slug = entry.get("category") or (entry.get("response") or {}).get("category")
                label = entry.get("display_label") or (self.category_label_lookup.get(slug, slug) if slug else "")
                timestamp = entry.get("timestamp")
                if not timestamp:
                    response = entry.get("response") or {}
                    timestamp = response.get("timestamp") or response.get("updated_at") or response.get("created_at")
                stamp_text = self._format_timestamp(timestamp)
                bullet = f" - {name}"
                if label:
                    bullet += f" [{label}]"
                if stamp_text != "n/a":
                    bullet += f" ({stamp_text})"
                lines.append(bullet)
        else:
            lines.append("No evidence scanned for this case yet.")

        return "\n".join(lines).strip()

    def _evidence_sort_key(self, record: Dict[str, Any]) -> datetime:
        timestamp = record.get("timestamp")
        dt = self._parse_timestamp(timestamp)
        if dt is None:
            response = record.get("response") or {}
            for key in ("timestamp", "updated_at", "created_at"):
                dt = self._parse_timestamp(response.get(key))
                if dt is not None:
                    break
        return dt or datetime.min

    def _view_case_summary(self, case_data: Dict[str, Any]) -> None:
        case_id = case_data.get("case_id") or ""
        label = case_data.get("display_name") or case_id or "Case Summary"
        summary_lines = [
            f"Case: {label}",
            f"Client: {case_data.get('client', 'n/a')}",
            f"Subject: {case_data.get('subject', 'n/a')}",
            f"Evidence items: {case_data.get('evidence_count', 0)}",
            f"Last activity: {case_data.get('last_seen_display', 'n/a')}",
        ]
        summary_detail = None
        if self.plugin and case_id:
            try:
                summary_detail = self.plugin.get_case_summary(case_id)
            except Exception as exc:
                self._append_log(f"Case summary unavailable for {case_id}: {exc}")
        if isinstance(summary_detail, dict) and summary_detail:
            status = summary_detail.get("status") or summary_detail.get("state")
            if status:
                summary_lines.append(f"Status: {status}")
            sections = summary_detail.get("sections")
            if isinstance(sections, dict) and sections:
                summary_lines.append("")
                summary_lines.append("Sections:")
                for name, value in list(sections.items())[:6]:
                    snippet = ""
                    if isinstance(value, str):
                        stripped = value.strip()
                        snippet = stripped.splitlines()[0][:80] if stripped else ""
                    summary_lines.append(f" - {name}" + (f": {snippet}" if snippet else ""))
        messagebox.showinfo(APP_TITLE, "\n".join(summary_lines))
        self._append_log(f"Displayed summary for case {label}.")


    def _build_review_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        header = ttk.Frame(parent, padding=(18, 12))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(1, weight=1)
        ttk.Label(header, text="Case Review", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(header, textvariable=self.review_case_label).grid(row=0, column=1, sticky="w")
        ttk.Button(header, text="Refresh", command=lambda: self._refresh_review_view(self.active_case_id)).grid(row=0, column=2, sticky="e")
        self.review_ready_label = tk.Label(header, textvariable=self.review_ready_text, font=("Segoe UI", 10), fg="#6b7280")
        self.review_ready_label.grid(row=1, column=0, columnspan=3, sticky="w", pady=(4, 0))

        body = ttk.Frame(parent, padding=(18, 0, 18, 18))
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=2)
        body.columnconfigure(1, weight=3)
        body.rowconfigure(1, weight=1)

        ttk.Label(body, textvariable=self.review_status_text, style="CaseMeta.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        columns = ("section", "status", "updated", "summary")
        tree_container = ttk.Frame(body)
        tree_container.grid(row=1, column=0, sticky="nsew")
        tree_container.columnconfigure(0, weight=1)
        tree_container.rowconfigure(0, weight=1)

        self.review_tree = ttk.Treeview(tree_container, columns=columns, show="headings", height=12)
        self.review_tree.heading("section", text="Section")
        self.review_tree.heading("status", text="Status")
        self.review_tree.heading("updated", text="Last Update")
        self.review_tree.heading("summary", text="Summary")
        self.review_tree.column("section", width=220, anchor="w")
        self.review_tree.column("status", width=110, anchor="w")
        self.review_tree.column("updated", width=150, anchor="w")
        self.review_tree.column("summary", width=320, anchor="w")
        self.review_tree.bind("<<TreeviewSelect>>", self._on_review_select)
        self.review_tree.tag_configure("complete", foreground="#15803d")
        self.review_tree.tag_configure("draft", foreground="#2563eb")
        self.review_tree.tag_configure("pending", foreground="#b45309")
        self.review_tree.tag_configure("blocked", foreground="#b91c1c")

        tree_scroll = ttk.Scrollbar(tree_container, orient="vertical", command=self.review_tree.yview)
        self.review_tree.configure(yscrollcommand=tree_scroll.set)
        self.review_tree.grid(row=0, column=0, sticky="nsew")
        tree_scroll.grid(row=0, column=1, sticky="ns")

        detail_pane = ttk.Frame(body)
        detail_pane.grid(row=1, column=1, sticky="nsew", padx=(12, 0))
        detail_pane.columnconfigure(0, weight=1)
        detail_pane.rowconfigure(0, weight=3)
        detail_pane.rowconfigure(1, weight=2)
        detail_pane.rowconfigure(2, weight=2)

        narrative_frame = ttk.LabelFrame(detail_pane, text="Narrative Draft", padding=12)
        narrative_frame.grid(row=0, column=0, sticky="nsew")
        narrative_frame.columnconfigure(0, weight=1)
        narrative_frame.rowconfigure(1, weight=1)

        narrative_toolbar = ttk.Frame(narrative_frame)
        narrative_toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Button(narrative_toolbar, text="Save Draft Edits", command=self._save_review_edit).pack(side="right")
        ttk.Button(narrative_toolbar, text="Summarize Draft", command=self._summarize_review_draft).pack(side="right", padx=(0, 6))
        ttk.Button(narrative_toolbar, text="Copy Draft", command=self._copy_review_draft).pack(side="right", padx=(0, 6))

        self.review_draft_text = ScrolledText(narrative_frame, wrap="word", font=("Segoe UI", 11))
        self.review_draft_text.grid(row=1, column=0, sticky="nsew")
        self.review_draft_text.configure(state="disabled")

        summary_frame = ttk.LabelFrame(detail_pane, text="Auto Summary", padding=12)
        summary_frame.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        summary_frame.columnconfigure(0, weight=1)
        summary_frame.rowconfigure(0, weight=1)

        self.review_summary_text = ScrolledText(summary_frame, wrap="word", state="disabled", font=("Segoe UI", 10))
        self.review_summary_text.grid(row=0, column=0, sticky="nsew")
        self._set_summary_placeholder()

        meta_frame = ttk.LabelFrame(detail_pane, text="Telemetry & Payload", padding=12)
        meta_frame.grid(row=2, column=0, sticky="nsew", pady=(12, 0))
        meta_frame.columnconfigure(0, weight=1)
        meta_frame.rowconfigure(0, weight=1)

        self.review_payload_text = ScrolledText(meta_frame, wrap="word", state="disabled", font=("Consolas", 10))
        self.review_payload_text.grid(row=0, column=0, sticky="nsew")

        ttk.Label(body, text="Select a section to see payload details.", style="CaseMeta.TLabel").grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 0))

        self._clear_review_display()
    def _build_workspace_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(3, weight=1)
        parent.rowconfigure(4, weight=0)

        header = ttk.Frame(parent, padding=(0, 0, 0, 12))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(1, weight=1)
        ttk.Label(header, text="Active Case", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(header, textvariable=self.workspace_case_text, font=("Segoe UI", 12)).grid(row=0, column=1, sticky="w")

        summary_frame = ttk.LabelFrame(parent, text="Case Overview", padding=12)
        summary_frame.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        ttk.Label(summary_frame, textvariable=self.workspace_overview_text, justify="left", wraplength=760).pack(anchor="w")

        drop_frame = ttk.Frame(parent)
        drop_frame.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        drop_frame.columnconfigure(0, weight=1)
        drop_area = tk.Frame(
            drop_frame,
            height=110,
            bg="#eef2f9",
            highlightbackground=CARD_BORDER,
            highlightcolor=CARD_BORDER,
            highlightthickness=2,
        )
        drop_area.grid(row=0, column=0, sticky="ew")
        drop_area.columnconfigure(0, weight=1)
        drop_area.rowconfigure(0, weight=1)
        tk.Label(
            drop_area,
            textvariable=self.workspace_drop_message,
            bg="#eef2f9",
            fg="#334155",
            font=("Segoe UI", 12, "bold"),
        ).place(relx=0.5, rely=0.35, anchor="center")
        tk.Button(
            drop_area,
            text="Browse Files",
            command=self._browse_files,
            bg="#2563eb",
            fg="white",
            relief="flat",
            padx=18,
            pady=6,
        ).place(relx=0.5, rely=0.65, anchor="center")
        drop_area.bind("<Button-1>", lambda _event: self._browse_files())
        if DND_AVAILABLE:
            drop_area.drop_target_register(tkdnd.DND_FILES)
            drop_area.dnd_bind("<<Drop>>", self._handle_drop_event)

        cards_container = ttk.Frame(parent)
        cards_container.grid(row=3, column=0, sticky="nsew")
        cards_container.columnconfigure(0, weight=1)
        cards_container.rowconfigure(0, weight=1)

        self.cards_canvas = tk.Canvas(cards_container, highlightthickness=0)
        self.cards_canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(cards_container, orient="vertical", command=self.cards_canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.cards_canvas.configure(yscrollcommand=scrollbar.set)

        self.cards_frame = ttk.Frame(self.cards_canvas)
        self.cards_window = self.cards_canvas.create_window((0, 0), window=self.cards_frame, anchor="nw")
        self.cards_frame.columnconfigure(0, weight=1)
        self.cards_frame.bind("<Configure>", lambda _e: self.cards_canvas.configure(scrollregion=self.cards_canvas.bbox("all")))
        self.cards_canvas.bind(
            "<Configure>",
            lambda event: self.cards_canvas.itemconfigure(self.cards_window, width=event.width),
        )

        log_frame = ttk.LabelFrame(parent, text="Mission Log", padding=12)
        log_frame.grid(row=4, column=0, sticky="ew", pady=(6, 0))
        log_frame.columnconfigure(0, weight=1)
        self.log_area = ScrolledText(
            log_frame,
            wrap="word",
            state="disabled",
            font=("Consolas", 10),
            height=6,
        )
        self.log_area.grid(row=0, column=0, sticky="ew")

    def _build_assembly_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(parent)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Button(toolbar, text="Generate Report Summary", command=self._generate_report).pack(side="left")
        ttk.Button(toolbar, text="Export Report...", command=self._export_report).pack(side="left", padx=(8, 0))

        self.report_text = ScrolledText(parent, wrap="word", state="disabled", font=("Consolas", 10))
        self.report_text.grid(row=1, column=0, sticky="nsew")

    # -- Profile actions ------------------------------------------------
    def _set_operator(self, name: str) -> None:
        self.operator_name = name
        profile_text = f"Operator: {name}"
        self.operator_label_var.set(profile_text)
        self.home_operator_summary_var.set(profile_text)
        if getattr(self, 'operator_label', None):
            self.operator_label.configure(textvariable=self.operator_label_var)
        if self.status_bar:
            self.status_bar.update_section("profile", profile_text)
        self._schedule_home_refresh()

    def _prompt_new_case_dialog(self) -> None:
        if not self.plugin:
            messagebox.showerror(APP_TITLE, "Central Plugin unavailable. Restart the GUI and try again.")
            return

        defaults: Dict[str, Any] = {}
        try:
            if isinstance(self.profile_data, dict):
                defaults = dict(self.profile_data.get("case_defaults", {}) or {})
        except Exception:
            defaults = {}

        metadata_defaults = {
            "client_name": defaults.get("client_name"),
            "subject": defaults.get("subject"),
            "location": defaults.get("location"),
        }

        existing_ids: List[str] = []
        try:
            existing_records = self.plugin.list_cases()
            for record in existing_records or []:
                if not isinstance(record, dict):
                    continue
                for key in ("case_id", "case", "id"):
                    value = record.get(key)
                    if value:
                        existing_ids.append(str(value))
                        break
        except Exception as exc:
            self._append_log(f"Unable to fetch existing cases: {exc}")

        if self.case_overview:
            for bucket in self.case_overview.values():
                for record in bucket or []:
                    if isinstance(record, dict):
                        cid = record.get("case_id") or record.get("case_number")
                        if cid:
                            existing_ids.append(str(cid))
        if self.active_case_id:
            existing_ids.append(self.active_case_id)

        dialog = CaseCreationDialog(
            self.root,
            default_case_id=str(defaults.get("case_number") or ""),
            default_investigator=self.operator_name
            or getattr(self.profile, "display_name", "")
            or "Investigator",
            subcontractor=bool(defaults.get("subcontractor", False)),
            contract_signed=str(defaults.get("sign_date") or "") or None,
            export_root=defaults.get("export_root"),
            metadata_defaults=metadata_defaults,
            existing_ids=existing_ids,
        )

        payload = dialog.show()
        if not payload:
            return

        try:
            session = self.plugin.start_case(
                case_id=payload["case_id"],
                investigator=payload["investigator"],
                subcontractor=payload["subcontractor"],
                contract_signed=payload["contract_signed"],
                export_root=payload["export_root"],
                metadata=payload["metadata"],
            )
        except Exception as exc:
            self._append_log(f"Failed to start case {payload['case_id']}: {exc}")
            messagebox.showerror(APP_TITLE, f"Unable to start case:\n{exc}")
            return

        self._append_log(f"New case created: {payload['case_id']}")
        self._refresh_case_overview()
        record = self._find_case_by_id(self.case_overview, session.case_id)
        if record is None:
            record = {
                "case_id": session.case_id,
                "status": getattr(session, "status", "in_progress"),
                "display_name": getattr(session, "display_name", session.case_id),
                "case_session": session,
            }
            self.case_overview.setdefault("open", []).insert(0, record)
        self._set_active_case(record, navigate=True)
    def _show_login_dialog(self, initial: bool = False) -> None:
        operators: List[OperatorProfile] = []
        if self.operator_manager:
            try:
                operators = self.operator_manager.list_all()
                self.operator_profiles_cache = operators
            except Exception as exc:
                self._append_log(f"Failed to load operator profiles: {exc}")
        dialog = LoginDialog(
            self.root,
            self.operator_name,
            operators=operators,
            manager=self.operator_manager,
        )
        result = dialog.show()
        if isinstance(result, OperatorProfile):
            self.operator_profile = result
            self._renew_operator_token(result)
            self._set_operator(result.name)
            self._append_log(f"Operator switched to {result.name}.")
        elif isinstance(result, str) and result:
            self.operator_profile = None
            self.operator_token_payload = None
            self._set_operator(result)
            self._append_log(f"Operator switched to {result}.")
        elif initial and not self.operator_name:
            fallback = self.profile.display_name or "Analyst"
            self.operator_profile = None
            self.operator_token_payload = None
            self._set_operator(fallback)
    def _open_profile_editor(self) -> None:
        editor = ProfileEditor(self.root, dict(self.profile_data))
        result = editor.show()
        if not result:
            return
        try:
            self.profile = self.profile_registry.save_profile(result)
            self.profile_data = dict(result)
            self._set_operator(self.profile.display_name)
            self._refresh_home_overview()
            self._refresh_case_overview()
            self._append_log("Profile updated.")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, f"Failed to save profile:\n{exc}")

    def _refresh_home_overview(self) -> None:
        profile_payload = getattr(self.profile, "payload", {}) if self.profile else {}
        reporting = profile_payload.get("reporting", {})
        defaults = profile_payload.get("case_defaults", {})
        profile_lines = [
            f"Display Name: {self.profile.display_name}",
            f"Business: {self.profile_data.get('business_name', 'n/a')}",
            f"Agency License: {self.profile_data.get('agency_license', 'n/a')}",
            f"Email: {self.profile_data.get('email', 'n/a')}",
            f"Phone: {self.profile_data.get('phone', 'n/a')}",
            f"Preferred Workflow: {reporting.get('default', 'n/a')}",
        ]
        self.home_profile_text.set("\n".join(profile_lines))

        case_lines = [
            f"Case Number: {defaults.get('case_number', 'n/a')}",
            f"Client Name: {defaults.get('client_name', 'n/a')}",
            f"Subject: {defaults.get('subject', 'n/a')}",
            f"Location: {defaults.get('location', 'n/a')}",
            f"Sign Date: {defaults.get('sign_date', 'n/a')}  |  Start Date: {defaults.get('start_date', 'n/a')}",
            f"Default Contract: {defaults.get('default_contract', defaults.get('default', 'n/a'))}",
        ]
        self.home_case_text.set("\n".join(case_lines))

        active_label = "No active case"
        if self.active_case_data:
            case_id = self.active_case_data.get('case_id') or self.active_case_data.get('case_number') or 'n/a'
            display = self.active_case_data.get('display_name') or case_id
            status = self.active_case_data.get('status') or 'in progress'
            active_label = f"{display} ({case_id}) - {status}"
        elif self.active_case_id:
            active_label = f"{self.active_case_id} - workspace ready"
        self.home_active_case_var.set(active_label)

        status_message = self.status_message_var.get() or "Ready"
        self.home_status_var.set(status_message)

        bus_state = "connected" if self.plugin and getattr(self.plugin, 'bus', None) else "disconnected"
        self.bus_state_var.set(f"Bus: {bus_state}")
        self.home_bus_health_var.set(f"Connection: {bus_state.title()}")

        self.home_operator_summary_var.set(f"Operator: {self.operator_name}")

        job_count = len(getattr(self, 'background_jobs', {}))
        running = sum(1 for record in getattr(self, 'background_jobs', {}).values() if str(record.get('status')).lower() in {'queued', 'running', 'pending'})
        failed = sum(1 for record in getattr(self, 'background_jobs', {}).values() if str(record.get('status')).lower() in {'failed', 'error'})
        parts: List[str] = []
        if job_count:
            parts.append(f"{job_count} total")
        if running:
            parts.append(f"{running} active")
        if failed:
            parts.append(f"{failed} failed")
        self.home_job_summary_var.set("Jobs: " + (", ".join(parts) if parts else "none queued"))

        tree = self.home_activity_tree
        if tree is not None:
            tree.delete(*tree.get_children())
            entries: List[Dict[str, Any]] = []
            if self.plugin:
                try:
                    entries = self.plugin.get_activity_log(limit=15)
                except Exception as exc:
                    self._append_log(f"Activity log fetch failed: {exc}")
                    entries = []
            if entries:
                if hasattr(tree, '_empty_notice'):
                    tree._empty_notice.configure(text="")
                    try:
                        tree._empty_notice.grid_remove()
                    except Exception:
                        pass
                for entry in entries:
                    timestamp = entry.get('timestamp') or '-'
                    source = entry.get('source') or '-'
                    message = entry.get('message') or ''
                    if len(message) > 120:
                        message = message[:117].rstrip() + '...'
                    tree.insert('', 'end', values=(timestamp, source, message))
            else:
                if hasattr(tree, '_empty_notice'):
                    tree._empty_notice.configure(
                        text="No recent automation activity. When evidence is processed or narratives are generated they will appear here.",
                        foreground="#94a3b8",
                    )
                    try:
                        tree._empty_notice.grid()
                    except Exception:
                        pass

    def _open_workspace_tab(self) -> None:
        self._select_tab("workspace")

    # -- Backend init ---------------------------------------------------
    def _initialize_plugin(self) -> None:
        try:
            self.plugin = CentralPluginAdapter()
            self.categories = self.plugin.get_available_tag_categories()
            self.category_label_lookup = {
                entry.get("slug"): entry.get("label") or entry.get("slug")
                for entry in self.categories
                if entry.get("slug")
            }
            self._register_review_bus_handlers()
            self._register_gui_bus_handlers()
            try:
                bus_snapshots = self.plugin.bus.get_case_snapshots() if hasattr(self.plugin.bus, "get_case_snapshots") else []
                if isinstance(bus_snapshots, list):
                    for snapshot in bus_snapshots:
                        if isinstance(snapshot, dict):
                            case_key = snapshot.get("case_id") or snapshot.get("case_number") or snapshot.get("case")
                            if case_key:
                                entries = self.case_snapshots.setdefault(str(case_key), [])
                                entries.append(dict(snapshot))
                                if len(entries) > 50:
                                    self.case_snapshots[str(case_key)] = entries[-50:]
            except Exception as exc:
                self._append_log(f"Unable to load existing case snapshots: {exc}")
            self._refresh_case_overview()
            self._refresh_review_view(self.active_case_id)
            bus_state = "connected" if self.plugin and self.plugin.bus else "disconnected"
            self._update_status("Ready", bus_state=bus_state)
            self._append_log("Central Plugin initialized. Tag taxonomy loaded.")
        except Exception as exc:  # pragma: no cover - defensive
            self._update_status("Initialization failed", bus_state="error")
            self._append_log("Failed to initialize Central Plugin:")
            self._append_log(traceback.format_exc())
            messagebox.showerror(APP_TITLE, f"Failed to initialize Central Plugin:\n{exc}")

    # -- File intake ----------------------------------------------------
    def _browse_files(self) -> None:
        paths = filedialog.askopenfilenames(title="Select evidence files")
        if paths:
            self._add_cards(list(paths))

    def _handle_drop_event(self, event) -> None:  # pragma: no cover - requires drag/drop runtime
        paths = self._extract_drop_paths(event.data)
        if paths:
            self._add_cards(paths)

    @staticmethod
    def _extract_drop_paths(data: str) -> List[str]:
        if not data:
            return []
        results: List[str] = []
        current = ""
        in_brace = False
        for char in data:
            if char == "{":
                in_brace = True
                current = ""
                continue
            if char == "}":
                in_brace = False
                if current:
                    results.append(current.strip())
                current = ""
                continue
            if char == " " and not in_brace:
                if current:
                    results.append(current.strip())
                    current = ""
            else:
                current += char
        if current:
            results.append(current.strip())
        return [os.path.abspath(path) for path in results]

    def _add_cards(self, paths: List[str]) -> None:
        added = 0
        existing_paths = {card.path for card in self.cards}

        for path in paths:
            normalized = os.path.abspath(path)
            if normalized not in existing_paths and os.path.isfile(normalized):
                suggestion = None
                if self.plugin:
                    try:
                        suggestion = self.plugin.suggest_category_for_file(normalized)
                    except Exception as exc:
                        self._append_log(f"Category suggestion failed for {os.path.basename(normalized)}: {exc}")
                active_case_id = self.active_case_id or None
                if active_case_id == "":
                    active_case_id = None
                if self.active_case_data and not active_case_id:
                    active_case_id = self.active_case_data.get("case_id") or None
                active_case_label = None
                if self.active_case_data:
                    active_case_label = self.active_case_data.get("display_name") or self.active_case_data.get("case_id")
                if not active_case_label and active_case_id:
                    active_case_label = active_case_id
                card = EvidenceCard(
                    parent=self.cards_frame,
                    path=normalized,
                    categories=self.categories,
                    on_advertise=self._advertise_card_need,
                    on_scan=self._scan_card,
                    on_remove=self._remove_card,
                    suggestion=suggestion,
                    case_label=active_case_label,
                    case_id=active_case_id,
                )
                self.cards.append(card)
                self.card_case_map[card] = active_case_id
                existing_paths.add(normalized)
                added += 1
                applied_slug = card.apply_suggestion()
                if suggestion and suggestion.get("category"):
                    label = suggestion.get("label") or suggestion.get("category")
                    case_context = active_case_label or active_case_id or "unassigned"
                    self._append_log(f"Suggested category '{label}' for {os.path.basename(normalized)} (case: {case_context}).")
                if applied_slug and self.plugin:
                    try:
                        tags_for_advertise = suggestion.get("tags") if isinstance(suggestion, dict) else None
                        kwargs: Dict[str, Any] = {"tags": tags_for_advertise}
                        if active_case_id:
                            kwargs["case_id"] = active_case_id
                        result = self.plugin.advertise_category_need(applied_slug, **kwargs)
                        if result:
                            case_context = active_case_label or active_case_id or "unassigned"
                            self._append_log(f"Auto-advertised {applied_slug} for {os.path.basename(normalized)} (case: {case_context}).")
                    except Exception as exc:
                        self._append_log(f"Auto advertisement failed for {os.path.basename(normalized)}: {exc}")
            else:
                reasons: List[str] = []
                if normalized in existing_paths:
                    reasons.append("already loaded")
                if not os.path.isfile(normalized):
                    reasons.append("missing on disk")
                if not reasons:
                    reasons.append("unknown")
                self._append_log(f"Skipped {path} ({', '.join(reasons)}).")
        if added:
            self._apply_workspace_card_filter()
            self._append_log(f"Added {added} evidence card(s).")
        else:
            self._append_log("No new files added (duplicates skipped).")

    def _remove_card(self, card: EvidenceCard) -> None:
        if card in self.cards:
            card.destroy()
            self.cards.remove(card)
            self.card_case_map.pop(card, None)
            case_context = card.case_label or card.case_id or "unassigned"
            self._append_log(f"Removed card for {os.path.basename(card.path)} (case: {case_context}).")
            self._apply_workspace_card_filter()

    # -- Card interactions ----------------------------------------------
    def _advertise_card_need(self, card: EvidenceCard, slug: str, extra_tags: Iterable[str]) -> None:
        if not self.plugin:
            messagebox.showerror(APP_TITLE, "Central Plugin unavailable. Restart the GUI and try again.")
            return
        try:
            tags_payload = list(extra_tags)
            kwargs: Dict[str, Any] = {"tags": tags_payload}
            case_id = card.case_id or self.active_case_id
            if case_id:
                kwargs["case_id"] = case_id
            result = self.plugin.advertise_category_need(slug, **kwargs)
            case_context = card.case_label or case_id or "unassigned"
            self._append_log(f"Advertised category '{slug}' for {os.path.basename(card.path)} (case: {case_context}): {result}")
            self._update_status(f"Advertised {slug}")
        except Exception as exc:
            self._append_log(f"Failed to advertise {slug}: {exc}")
            messagebox.showerror(APP_TITLE, f"Failed to advertise category need:\n{exc}")

    def _scan_card(self, card: EvidenceCard, slug: str, extra_tags: Iterable[str]) -> None:
        if not self.plugin:
            messagebox.showerror(APP_TITLE, "Central Plugin unavailable. Restart the GUI and try again.")
            return
        payload: Dict[str, Any] = {
            "file_path": card.path,
            "name": os.path.basename(card.path),
            "category": slug,
        }
        case_id = card.case_id or self.active_case_id
        case_record: Optional[Dict[str, Any]] = None
        if case_id:
            payload["case_id"] = case_id
            case_record = self._find_case_by_id(self.case_overview, case_id)
            if not case_record and self.active_case_data and self.active_case_id == case_id:
                case_record = self.active_case_data
            case_payload = {"id": case_id}
            display_name = (case_record or {}).get("display_name") if case_record else None
            if not display_name:
                display_name = card.case_label or case_id
            if display_name:
                case_payload["name"] = display_name
            client_name = (case_record or {}).get("client") if case_record else None
            if client_name:
                case_payload["client"] = client_name
            subject_name = (case_record or {}).get("subject") if case_record else None
            if subject_name:
                case_payload["subject"] = subject_name
            payload["case"] = case_payload
        tags_list = list(extra_tags)
        if tags_list:
            payload["tags"] = tags_list
            payload["extra_tags"] = tags_list
        try:
            response = self.plugin.scan_evidence(payload)
            case_context = card.case_label or case_id or "unassigned"
            self._append_log(
                f"Scan submitted for '{os.path.basename(card.path)}' in category '{slug}' (case: {case_context}): {response}"
            )
            self._update_status(f"Scanned {os.path.basename(card.path)}")
        except Exception as exc:
            self._append_log(f"Evidence scan failed for {card.path}: {exc}")
            messagebox.showerror(APP_TITLE, f"Evidence scan failed:\n{exc}")
            return

        self._refresh_report_summary()
        self._refresh_case_overview()

    # -- Logging / status -----------------------------------------------
    def _update_report_text(self, content: str) -> None:
        if not self.report_text:
            return
        self.report_text.configure(state="normal")
        self.report_text.delete("1.0", tk.END)
        self.report_text.insert(tk.END, content)
        self.report_text.configure(state="disabled")

    def _refresh_report_summary(self) -> None:
        if not self.plugin:
            return
        try:
            report = self.plugin.generate_full_report()
        except Exception as exc:
            self._append_log(f"Report summary refresh failed: {exc}")
            return
        self.current_report = report
        text_content = report.get("report_text", "")
        if text_content:
            self._update_report_text(text_content)
        elif self.report_text:
            self.report_text.configure(state="normal")
            self.report_text.delete("1.0", tk.END)
            self.report_text.configure(state="disabled")

    def _generate_report(self) -> None:
        self._refresh_report_summary()
        if self.current_report:
            sections = len(self.current_report.get("sections", {}))
            self._append_log(f"Generated report with {sections} section summaries.")
            self._select_tab("assembly")
        else:
            messagebox.showinfo(APP_TITLE, "No report content available yet.")

    def _export_report(self) -> None:
        if not self.current_report:
            messagebox.showinfo(APP_TITLE, "Generate a report summary before exporting.")
            return
        default_name = f"central_command_report_{datetime.now():%Y%m%d_%H%M%S}.txt"
        target_path = filedialog.asksaveasfilename(
            title="Export Report",
            defaultextension=".txt",
            initialfile=default_name,
            filetypes=[("Text Report", "*.txt"), ("All Files", "*.*")],
        )
        if not target_path:
            return
        try:
            exported = self.plugin.export_report(self.current_report, file_path=target_path)
        except Exception as exc:
            self._append_log(f"Report export failed: {exc}")
            messagebox.showerror(APP_TITLE, f"Report export failed: {exc}")
            return
        self._append_log(f"Report exported to {exported}.")
        messagebox.showinfo(APP_TITLE, f"Report saved to\n{exported}")

    def _append_log(self, message: str) -> None:
        if not self.log_area:
            return
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted = f"[{timestamp}] {message}\n"
        self.log_area.configure(state="normal")
        self.log_area.insert(tk.END, formatted)
        self.log_area.configure(state="disabled")
        self.log_area.see(tk.END)
        self._truncate_log()

    def _truncate_log(self) -> None:
        if not self.log_area:
            return
        line_count = int(self.log_area.index('end-1c').split('.')[0])
        if line_count <= LOG_MAX_LINES:
            return
        self.log_area.configure(state="normal")
        self.log_area.delete('1.0', f"{line_count - LOG_MAX_LINES}.0")
        self.log_area.configure(state="disabled")

    def _update_status(self, message: str, *, bus_state: Optional[str] = None) -> None:
        self.status_message_var.set(message)
        if bus_state is not None:
            self.bus_state_var.set(f"Bus: {bus_state}")

        if self.status_bar:
            self.status_bar.update_section("status", message)
            if bus_state is not None:
                self.status_bar.update_section("bus", self.bus_state_var.get())
        self._sync_card_count()
    def _sync_card_count(self) -> None:
        active = self.active_case_id
        if active:
            visible = sum(1 for card in self.cards if self.card_case_map.get(card) == active)
            summary = f"Evidence cards: {visible}/{len(self.cards)}"
        else:
            summary = f"Evidence cards: {len(self.cards)}"
        if self.status_bar:
            self.status_bar.update_section("cards", summary)

    # -- Tk mainloop ----------------------------------------------------
    def mainloop(self) -> None:
        self.root.mainloop()


def main(argv: Sequence[str] | None = None) -> int:
    try:
        gui = EnhancedDKIGUI()
        gui.mainloop()
    except Exception:
        traceback.print_exc()
        return 1
    return 0


EnhancedFunctionalGUI = EnhancedDKIGUI
EnhancedDKIGUIApp = EnhancedDKIGUI


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())











