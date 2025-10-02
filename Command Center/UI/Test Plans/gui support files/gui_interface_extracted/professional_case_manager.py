#!/usr/bin/env python3
"""
Professional Case Management GUI
Bridges Central Command runtime systems with the mission debrief pipeline and evidence locker.
"""

import json
import logging
import os
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    from PIL import Image, ImageTk  # type: ignore
    HAS_PIL = True
except ImportError:  # pragma: no cover - optional dependency
    Image = None     # type: ignore
    ImageTk = None   # type: ignore
    HAS_PIL = False

try:
    import tkinterdnd2 as tkdnd  # type: ignore
    HAS_TKINTERDND2 = True
except ImportError:  # pragma: no cover - optional dependency
    tkdnd = None  # type: ignore
    HAS_TKINTERDND2 = False

# Ensure the Central Command runtime is reachable
RUNTIME_DIR = Path(__file__).resolve().parents[1] / "Start Menu" / "Run Time"
sys.path.append(str(RUNTIME_DIR))

from central_plugin import central_plugin  # noqa: E402  pylint: disable=wrong-import-position

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("professional_case_manager.log"),
        logging.StreamHandler(sys.stdout),
    ],
)


class ProfessionalCaseManager:
    """Interactive desktop shell for Central Command operators."""

    PROFILE_FILE = Path(__file__).with_name("user_profile.json")
    API_KEYS_FILE = Path(__file__).with_name("api_keys.json")
    WAR_ROOM_PROCESSORS = Path(r"F:/The Central Command/The War Room/Processors")

    def __init__(self) -> None:
        if HAS_TKINTERDND2:
            self.root = tkdnd.Tk()  # type: ignore[call-arg]
        else:
            self.root = tk.Tk()
        self.root.title("DKI Professional Case Management System")
        self.root.geometry("1420x920")
        self.root.configure(bg="#f5f5f5")

        self.current_user: Optional[str] = None
        self.current_case_id: Optional[str] = None
        self.case_metadata: Dict[str, Any] = {}
        self.uploaded_files: List[Path] = []
        self.audit_trail: List[Dict[str, Any]] = []
        self.profile_data: Dict[str, Any] = {}
        self.profile_picture_path: Optional[Path] = None
        self.documents: List[Dict[str, Any]] = []

        self.central_plugin = central_plugin
        self.depositions_dir = self._resolve_depositions_dir()
        self.depositions_tree: Optional[ttk.Treeview] = None
        self.depositions_path_var = tk.StringVar(value=str(self.depositions_dir))

        self.status_var = tk.StringVar(value="Ready")
        self.narrative_text_widget: Optional[tk.Text] = None
        self.mission_log_widget: Optional[tk.Text] = None
        self.tools_output: Optional[tk.Text] = None

        self.advanced_window: Optional[tk.Toplevel] = None
        self.advanced_notebook: Optional[ttk.Notebook] = None
        self.evidence_last_results: List[str] = []

        self.api_key_vars: Dict[str, tk.StringVar] = {}

        self.current_screen = "login"
        self.login_username = tk.StringVar()
        self.login_password = tk.StringVar()

        self.profile_pics_dir = Path(__file__).with_name("profile_pictures")
        self.profile_pics_dir.mkdir(exist_ok=True)

        self.setup_login_screen()
        logger.info("Professional Case Management System initialized")

    # ------------------------------------------------------------------
    # Core setup helpers
    # ------------------------------------------------------------------
    def _resolve_depositions_dir(self) -> Path:
        try:
            install_root = Path(__file__).resolve().parents[3]
        except IndexError:
            install_root = Path(__file__).resolve().parent
        output_dir = install_root / "DKI_Exports" / "Depositions"
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def clear_screen(self) -> None:
        for widget in self.root.winfo_children():
            widget.destroy()

    # ------------------------------------------------------------------
    # Login & registration
    # ------------------------------------------------------------------
    def setup_login_screen(self) -> None:
        self.clear_screen()
        self.current_screen = "login"

        container = ttk.Frame(self.root, padding=60)
        container.pack(fill="both", expand=True)

        title = tk.Label(
            container,
            text="DKI Professional Case Management",
            font=("Arial", 24, "bold"),
            bg="#f5f5f5",
        )
        title.pack(pady=(0, 30))

        login_frame = ttk.LabelFrame(container, text="Secure Access", padding=30)
        login_frame.pack()

        ttk.Label(login_frame, text="Username").pack(anchor="w", pady=(0, 4))
        ttk.Entry(login_frame, textvariable=self.login_username, width=32).pack(pady=(0, 12))

        ttk.Label(login_frame, text="Password").pack(anchor="w", pady=(0, 4))
        ttk.Entry(login_frame, textvariable=self.login_password, width=32, show="*").pack(pady=(0, 16))

        ttk.Button(login_frame, text="Login", command=self.login_user).pack(fill="x")
        ttk.Button(login_frame, text="Register New Agent", command=self.register_new_agent).pack(fill="x", pady=(10, 0))

        tk.Label(
            container,
            text="Business Name: DKI Investigation Services",
            font=("Arial", 12),
            bg="#f5f5f5",
        ).pack(pady=(24, 0))

    def login_user(self) -> None:
        username = self.login_username.get().strip()
        password = self.login_password.get().strip()
        if not username:
            messagebox.showwarning("Login", "Please provide a username")
            return
        if not password:
            messagebox.showwarning("Login", "Please provide a password")
            return

        self.current_user = username
        self.current_case_id = None
        self.login_username.set("")
        self.login_password.set("")

        self.audit_trail.append(
            {"timestamp": datetime.now().isoformat(), "action": "login", "user": username}
        )
        self.setup_dashboard()

    def register_new_agent(self) -> None:
        reg_window = tk.Toplevel(self.root)
        reg_window.title("Register New Agent")
        reg_window.geometry("420x520")

        frame = ttk.Frame(reg_window, padding=20)
        frame.pack(fill="both", expand=True)

        fields = {
            "Full Name": tk.StringVar(),
            "Username": tk.StringVar(),
            "Password": tk.StringVar(),
            "Confirm Password": tk.StringVar(),
            "Agent ID": tk.StringVar(),
            "Security Clearance": tk.StringVar(value="Standard"),
        }
        self._registration_fields = fields  # cache for process_registration

        for label, var in fields.items():
            ttk.Label(frame, text=label).pack(anchor="w", pady=(8, 2))
            show = "*" if "Password" in label else None
            ttk.Entry(frame, textvariable=var, show=show).pack(fill="x")

        ttk.Button(
            frame,
            text="Register Agent",
            command=lambda: self.process_registration(reg_window),
        ).pack(fill="x", pady=(16, 4))
        ttk.Button(frame, text="Cancel", command=reg_window.destroy).pack(fill="x")

    def process_registration(self, reg_window: tk.Toplevel) -> None:
        fields = getattr(self, "_registration_fields", {})
        full_name = fields.get("Full Name").get().strip() if fields else ""
        username = fields.get("Username").get().strip() if fields else ""
        password = fields.get("Password").get() if fields else ""
        confirm = fields.get("Confirm Password").get() if fields else ""

        if not all([full_name, username, password, confirm]):
            messagebox.showwarning("Registration", "All fields are required")
            return
        if password != confirm:
            messagebox.showerror("Registration", "Passwords do not match")
            return
        self.audit_trail.append(
            {
                "timestamp": datetime.now().isoformat(),
                "action": "register_agent",
                "user": username,
                "metadata": {"full_name": full_name},
            }
        )
        messagebox.showinfo("Registration", "Agent registered successfully")
        reg_window.destroy()

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------
    def setup_dashboard(self) -> None:
        self.clear_screen()
        self.current_screen = "dashboard"

        header = ttk.Frame(self.root, padding=20)
        header.pack(fill="x")

        user_text = self.current_user or "Unknown Agent"
        ttk.Label(header, text=f"Signed in as: {user_text}", font=("Segoe UI", 14, "bold")).pack(side="left")
        ttk.Label(header, textvariable=self.status_var).pack(side="left", padx=(20, 0))

        action_bar = ttk.Frame(header)
        action_bar.pack(side="right")
        ttk.Button(action_bar, text="Advanced Options", command=self.open_advanced_options).pack(side="left", padx=4)
        ttk.Button(action_bar, text="Change User", command=self.change_user).pack(side="left", padx=4)
        ttk.Button(action_bar, text="Log Out", command=self.logout_user).pack(side="left", padx=4)

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        overview_tab = ttk.Frame(notebook, padding=16)
        evidence_tab = ttk.Frame(notebook, padding=16)

        notebook.add(overview_tab, text="Overview")
        notebook.add(evidence_tab, text="Evidence Locker")

        self.build_overview_tab(overview_tab)
        self.build_evidence_tab(evidence_tab)

    def open_advanced_options(self) -> None:
        """Display advanced system controls in a separate window."""
        if self.advanced_window and self.advanced_window.winfo_exists():
            self.advanced_window.lift()
            self.advanced_window.focus_force()
            return

        window = tk.Toplevel(self.root)
        window.title("Advanced Operations")
        window.geometry("1180x820")
        window.protocol("WM_DELETE_WINDOW", self._close_advanced_window)

        notebook = ttk.Notebook(window)
        notebook.pack(fill="both", expand=True, padx=12, pady=12)

        mission_tab = ttk.Frame(notebook, padding=12)
        narrative_tab = ttk.Frame(notebook, padding=12)
        user_tab = ttk.Frame(notebook, padding=12)

        notebook.add(mission_tab, text="Mission Debrief")
        notebook.add(narrative_tab, text="Narrative Tools")
        notebook.add(user_tab, text="User & System Settings")

        self.build_mission_debrief_tab(mission_tab)
        self.build_narrative_tab(narrative_tab)
        self.build_user_settings_tab(user_tab)

        self.advanced_window = window
        self.advanced_notebook = notebook

    def _close_advanced_window(self) -> None:
        if self.advanced_window and self.advanced_window.winfo_exists():
            self.advanced_window.destroy()
        self.advanced_window = None
        self.advanced_notebook = None

    def build_overview_tab(self, container: ttk.Frame) -> None:
        """Build the home page with three massive click buttons"""
        
        # Main title
        title_frame = ttk.Frame(container)
        title_frame.pack(fill="x", pady=(0, 40))
        
        ttk.Label(
            title_frame,
            text="DKI Professional Case Management",
            font=("Segoe UI", 24, "bold"),
        ).pack()

        # Three compact buttons container - positioned to the right
        buttons_frame = ttk.Frame(container)
        buttons_frame.pack(side="right", fill="y", padx=50, pady=20)
        
        # Configure grid for three equal columns
        buttons_frame.columnconfigure(0, weight=1)
        buttons_frame.columnconfigure(1, weight=1) 
        buttons_frame.columnconfigure(2, weight=1)
        buttons_frame.rowconfigure(0, weight=1)

        # Button 1: Start New Case
        start_case_frame = ttk.Frame(buttons_frame, relief="raised", borderwidth=1)
        start_case_frame.grid(row=0, column=0, padx=8, pady=10, sticky="nsew")
        
        start_case_btn = tk.Button(
            start_case_frame,
            text="START NEW\nCASE",
            font=("Segoe UI", 12, "bold"),
            bg="#2E8B57",  # Sea Green
            fg="white",
            relief="raised",
            borderwidth=2,
            command=self.start_new_case,
            height=4,
            width=10
        )
        start_case_btn.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Button 2: View Case Library  
        case_library_frame = ttk.Frame(buttons_frame, relief="raised", borderwidth=1)
        case_library_frame.grid(row=0, column=1, padx=8, pady=10, sticky="nsew")
        
        case_library_btn = tk.Button(
            case_library_frame,
            text="VIEW CASE\nLIBRARY",
            font=("Segoe UI", 12, "bold"),
            bg="#4169E1",  # Royal Blue
            fg="white", 
            relief="raised",
            borderwidth=2,
            command=self.view_case_library,
            height=4,
            width=10
        )
        case_library_btn.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Button 3: User Profile
        user_profile_frame = ttk.Frame(buttons_frame, relief="raised", borderwidth=1)
        user_profile_frame.grid(row=0, column=2, padx=8, pady=10, sticky="nsew")
        
        user_profile_btn = tk.Button(
            user_profile_frame,
            text="USER\nPROFILE",
            font=("Segoe UI", 12, "bold"),
            bg="#DC143C",  # Crimson
            fg="white",
            relief="raised", 
            borderwidth=2,
            command=self.edit_user_profile,
            height=4,
            width=10
        )
        user_profile_btn.pack(fill="both", expand=True, padx=5, pady=5)

    def build_evidence_tab(self, container: ttk.Frame) -> None:
        top = ttk.Frame(container)
        top.pack(fill="x")

        ttk.Button(top, text="Upload Evidence", command=self.upload_files).pack(side="left")
        ttk.Button(top, text="Process Evidence", command=self.process_evidence).pack(side="left", padx=(8, 0))

        self.evidence_list = tk.Listbox(container, height=10)
        self.evidence_list.pack(fill="x", pady=(12, 12))

        self.evidence_output = tk.Text(container, height=12)
        self.evidence_output.pack(fill="both", expand=True)
        self.evidence_output.insert("1.0", "Processed evidence summaries will appear here.\n")
        self.evidence_output.configure(state="disabled")

    def build_mission_debrief_tab(self, container: ttk.Frame) -> None:
        path_frame = ttk.Frame(container)
        path_frame.pack(fill="x")
        ttk.Label(path_frame, text="Depositions directory:").pack(anchor="w")
        ttk.Label(path_frame, textvariable=self.depositions_path_var, foreground="#555").pack(anchor="w")

        control = ttk.Frame(container)
        control.pack(fill="x", pady=8)
        ttk.Button(control, text="Refresh", command=self.refresh_depositions_listing).pack(side="left")
        ttk.Button(control, text="Open Folder", command=self.open_depositions_directory).pack(side="left", padx=6)

        action = ttk.Frame(container)
        action.pack(fill="x", pady=(0, 8))
        ttk.Button(action, text="Process Report", command=lambda: self.trigger_mission_debrief_action("mission_debrief.process_report")).pack(side="left", padx=2)
        ttk.Button(action, text="Apply Template", command=lambda: self.trigger_mission_debrief_action("mission_debrief.apply_template")).pack(side="left", padx=2)
        ttk.Button(action, text="Add Watermark", command=lambda: self.trigger_mission_debrief_action("mission_debrief.add_watermark")).pack(side="left", padx=2)
        ttk.Button(action, text="Digital Sign", command=lambda: self.trigger_mission_debrief_action("mission_debrief.digital_sign")).pack(side="left", padx=2)
        ttk.Button(action, text="Print Report", command=lambda: self.trigger_mission_debrief_action("mission_debrief.print_report")).pack(side="left", padx=2)

        columns = ("name", "modified", "size")
        tree = ttk.Treeview(container, columns=columns, show="headings", height=12)
        tree.heading("name", text="File")
        tree.heading("modified", text="Modified")
        tree.heading("size", text="Size")
        tree.column("name", anchor="w", width=320)
        tree.column("modified", anchor="w", width=140)
        tree.column("size", anchor="e", width=100)
        tree.pack(fill="both", expand=True)
        tree.bind("<Double-1>", self._on_depositions_double_click)
        self.depositions_tree = tree
        self.refresh_depositions_listing()

        self.mission_log_widget = tk.Text(container, height=8)
        self.mission_log_widget.pack(fill="x", pady=(8, 0))
        self.mission_log_widget.insert("1.0", "Mission debrief actions will be logged here.\n")
        self.mission_log_widget.configure(state="disabled")

    def build_narrative_tab(self, container: ttk.Frame) -> None:
        frame = ttk.Frame(container)
        frame.pack(fill="x")

        ttk.Label(frame, text="Section ID").pack(side="left")
        self.narrative_section_var = tk.StringVar(value="section_1")
        section_box = ttk.Combobox(
            frame,
            textvariable=self.narrative_section_var,
            values=[
                "section_1",
                "section_3",
                "section_5",
                "section_8",
                "section_cp",
                "section_dp",
                "section_toc",
            ],
            state="readonly",
            width=18,
        )
        section_box.pack(side="left", padx=8)

        ttk.Button(frame, text="Generate Narrative", command=self.generate_narrative).pack(side="left")

        self.narrative_text_widget = tk.Text(container, height=18)
        self.narrative_text_widget.pack(fill="both", expand=True, pady=(12, 0))
        self.narrative_text_widget.insert("1.0", "Narrative output will appear here.\n")
        self.narrative_text_widget.configure(state="disabled")

    def build_user_settings_tab(self, container: ttk.Frame) -> None:
        notebook = ttk.Notebook(container)
        notebook.pack(fill="both", expand=True)

        profile_tab = ttk.Frame(notebook, padding=12)
        api_tab = ttk.Frame(notebook, padding=12)
        tools_tab = ttk.Frame(notebook, padding=12)
        session_tab = ttk.Frame(notebook, padding=12)

        notebook.add(profile_tab, text="Profile")
        notebook.add(api_tab, text="API Keys")
        notebook.add(tools_tab, text="Tools & Integrations")
        notebook.add(session_tab, text="Session")

        self.populate_profile_tab(profile_tab)
        self.populate_api_keys_tab(api_tab)
        self.populate_tools_tab(tools_tab)
        self.populate_session_tab(session_tab)

    def populate_profile_tab(self, container: ttk.Frame) -> None:
        self.load_profile_data()

        form = ttk.Frame(container)
        form.pack(fill="x")

        self.profile_vars: Dict[str, tk.StringVar] = {}
        for label, key in [
            ("Full Name", "full_name"),
            ("Email", "email"),
            ("Phone", "phone"),
            ("Title", "title"),
        ]:
            ttk.Label(form, text=label).grid(row=len(self.profile_vars), column=0, sticky="w", pady=4)
            var = tk.StringVar(value=self.profile_data.get(key, ""))
            ttk.Entry(form, textvariable=var, width=36).grid(row=len(self.profile_vars), column=1, sticky="ew", padx=(8, 0))
            self.profile_vars[key] = var
        form.columnconfigure(1, weight=1)

        photo_frame = ttk.Frame(container, padding=(0, 12))
        photo_frame.pack(anchor="w")
        ttk.Button(photo_frame, text="Upload Profile Picture", command=self.upload_profile_picture).pack(side="left")

        ttk.Button(container, text="Save Profile", command=self.save_profile_changes).pack(anchor="e", pady=(8, 0))

    def populate_api_keys_tab(self, container: ttk.Frame) -> None:
        self.load_api_keys()
        form = ttk.Frame(container)
        form.pack(fill="x")
        form.columnconfigure(1, weight=1)

        for row_index, (key, var) in enumerate(self.api_key_vars.items()):
            pretty = key.replace("_", " ").title()
            ttk.Label(form, text=f"{pretty}:").grid(row=row_index, column=0, sticky="w", pady=4)
            ttk.Entry(form, textvariable=var, show="•").grid(row=row_index, column=1, sticky="ew", pady=4, padx=(8, 0))

        button_row = ttk.Frame(container, padding=(0, 12))
        button_row.pack(fill="x")
        ttk.Button(button_row, text="Reload", command=self.load_api_keys).pack(side="left")
        ttk.Button(button_row, text="Save", command=self.save_api_keys).pack(side="left", padx=6)

    def populate_tools_tab(self, container: ttk.Frame) -> None:
        ttk.Label(container, text="Runtime tool availability", font=("Segoe UI", 11, "bold")).pack(anchor="w")

        tree = ttk.Treeview(container, columns=("status", "path"), show="headings", height=10)
        tree.heading("status", text="Status")
        tree.heading("path", text="Resource")
        tree.column("status", width=140, anchor="center")
        tree.column("path", anchor="w")
        tree.pack(fill="both", expand=True, pady=(8, 8))

        for entry in self._load_tool_catalog():
            tree.insert("", "end", values=(entry["status"], entry["path"]))

        self.tools_output = tk.Text(container, height=8)
        self.tools_output.pack(fill="x")
        self.tools_output.insert("1.0", "Tool orchestration output will appear here.\n")
        self.tools_output.configure(state="disabled")

    def populate_session_tab(self, container: ttk.Frame) -> None:
        ttk.Label(container, text=f"Signed in as: {self.current_user}").pack(anchor="w")
        ttk.Label(container, text=f"Active case: {self.current_case_id or 'None'}").pack(anchor="w", pady=(0, 8))
        ttk.Button(container, text="Switch User", command=self.change_user).pack(anchor="w", pady=4)
        ttk.Button(container, text="Log Out", command=self.logout_user).pack(anchor="w", pady=4)
        ttk.Button(container, text="Exit Application", command=self.root.destroy).pack(anchor="w", pady=4)

    # ------------------------------------------------------------------
    # Profile & API helpers
    # ------------------------------------------------------------------
    def load_profile_data(self) -> None:
        if self.PROFILE_FILE.exists():
            try:
                self.profile_data = json.loads(self.PROFILE_FILE.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                logger.warning("Profile file is corrupted; starting fresh")
                self.profile_data = {}
        else:
            self.profile_data = {}

    def save_profile_changes(self) -> None:
        for key, var in self.profile_vars.items():
            self.profile_data[key] = var.get().strip()
        self.PROFILE_FILE.write_text(json.dumps(self.profile_data, indent=2), encoding="utf-8")
        messagebox.showinfo("Profile", "Profile updated successfully")

    def upload_profile_picture(self) -> None:
        if not HAS_PIL:
            messagebox.showwarning("Profile", "Pillow is required for profile pictures")
            return
        file_path = filedialog.askopenfilename(
            title="Select profile picture",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif")],
        )
        if not file_path:
            return
        src = Path(file_path)
        dest = self.profile_pics_dir / src.name
        dest.write_bytes(src.read_bytes())
        self.profile_picture_path = dest
        messagebox.showinfo("Profile", "Profile picture updated")

    def load_api_keys(self) -> None:
        defaults = {
            "google_search_api_key": "",
            "google_search_engine_id": "",
            "google_maps_api_key": "",
            "bing_search_api_key": "",
            "public_records_api_key": "",
            "whitepages_api_key": "",
        }
        data = defaults
        if self.API_KEYS_FILE.exists():
            try:
                data.update(json.loads(self.API_KEYS_FILE.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                logger.warning("api_keys.json is corrupted; loading defaults")
        if not self.api_key_vars:
            self.api_key_vars = {key: tk.StringVar(value=value) for key, value in data.items()}
        else:
            for key, value in data.items():
                self.api_key_vars.setdefault(key, tk.StringVar()).set(value)
        for key in list(self.api_key_vars.keys()):
            if key not in data:
                self.api_key_vars[key].set("")

    def save_api_keys(self) -> None:
        payload = {key: var.get() for key, var in self.api_key_vars.items()}
        self.API_KEYS_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        messagebox.showinfo("API Keys", "Credentials saved locally")

    # ------------------------------------------------------------------
    # Evidence & mission operations
    # ------------------------------------------------------------------
    def upload_files(self) -> None:
        file_paths = filedialog.askopenfilenames(title="Select evidence files")
        if not file_paths:
            return
        for path_str in file_paths:
            path = Path(path_str)
            self.uploaded_files.append(path)
            self.evidence_list.insert("end", path.name)
        self.status_var.set(f"Queued {len(file_paths)} files for processing")

    def process_evidence(self) -> None:
        if not self.uploaded_files:
            messagebox.showwarning("Evidence", "No files selected")
            return

        def worker() -> None:
            summaries: List[str] = []
            for path in self.uploaded_files:
                payload = {
                    "file_path": str(path),
                    "timestamp": datetime.now().isoformat(),
                }
                response = self.central_plugin.send_to_bus("evidence.process_comprehensive", payload)
                summaries.append(self._format_evidence_result(path, response))
            self.evidence_last_results = summaries
            self.root.after(0, lambda: self._render_evidence_results(summaries))

        threading.Thread(target=worker, daemon=True).start()

    def _render_evidence_results(self, results: List[str]) -> None:
        if not self.evidence_output:
            return
        self.evidence_output.configure(state="normal")
        self.evidence_output.delete("1.0", "end")
        display_text = "\n".join(results) if results else "No results returned."
        self.evidence_output.insert("1.0", display_text)
        self.evidence_output.configure(state="disabled")
        self.status_var.set("Evidence processing complete")

    def _format_evidence_result(self, source_path: Path, response: Any) -> str:
        label = source_path.name
        if isinstance(response, dict):
            if "responses" in response and isinstance(response["responses"], list) and response["responses"]:
                return self._format_evidence_result(source_path, response["responses"][-1])
            if "result" in response and isinstance(response["result"], (dict, list)):
                return self._format_evidence_result(source_path, response["result"])
            error = response.get("error")
            status = response.get("status")
            message = response.get("message") or response.get("detail") or response.get("summary")
            if error:
                return f"{label}: ERROR - {error}"
            if status:
                if message:
                    return f"{label}: {status} - {message}"
                return f"{label}: {status}"
            return f"{label}: {json.dumps(response, indent=2)}"
        if isinstance(response, list) and response:
            formatted_parts = [
                self._format_evidence_result(source_path, item) if isinstance(item, (dict, list)) else f"{label}: {item}"
                for item in response
            ]
            return "\n".join(formatted_parts)
        if response in (None, ""):
            return f"{label}: No response data received"
        return f"{label}: {response}"

    def trigger_mission_debrief_action(self, topic: str) -> None:
        payload = {
            "requested_by": self.current_user,
            "timestamp": datetime.now().isoformat(),
        }
        response = self.central_plugin.send_to_bus(topic, payload)
        self._log_mission_response(topic, response)

    def _log_mission_response(self, topic: str, response: Any) -> None:
        if not self.mission_log_widget:
            return
        self.mission_log_widget.configure(state="normal")
        self.mission_log_widget.insert(
            "end",
            f"[{datetime.now().strftime('%H:%M:%S')}] {topic}: {json.dumps(response, indent=2)}\n",
        )
        self.mission_log_widget.configure(state="disabled")
        self.mission_log_widget.see("end")

    def generate_narrative(self) -> None:
        section_id = self.narrative_section_var.get()
        payload = {"section_id": section_id, "case_id": self.current_case_id}
        result = self.central_plugin.send_to_bus("narrative.generate", payload)
        if not self.narrative_text_widget:
            return
        self.narrative_text_widget.configure(state="normal")
        self.narrative_text_widget.delete("1.0", "end")
        self.narrative_text_widget.insert("1.0", json.dumps(result, indent=2))
        self.narrative_text_widget.configure(state="disabled")

    # ------------------------------------------------------------------
    # Depositions helpers
    # ------------------------------------------------------------------
    def refresh_depositions_listing(self) -> None:
        if not self.depositions_tree:
            return
        try:
            entries = [path for path in self.depositions_dir.glob("*") if path.is_file()]
            entries.sort(key=lambda item: item.stat().st_mtime, reverse=True)
        except OSError as exc:
            messagebox.showerror("Depositions", f"Unable to read directory: {exc}")
            return

        self.depositions_tree.delete(*self.depositions_tree.get_children())
        for entry in entries:
            stat = entry.stat()
            modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
            size = f"{stat.st_size / 1024:.1f} KB"
            self.depositions_tree.insert("", "end", values=(entry.name, modified, size), tags=(str(entry),))

    def open_depositions_directory(self) -> None:
        path = self.depositions_dir
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=False)
        else:
            subprocess.run(["xdg-open", str(path)], check=False)

    def _on_depositions_double_click(self, event: Any) -> None:
        if not self.depositions_tree:
            return
        item = self.depositions_tree.identify_row(event.y)
        if not item:
            return
        tags = self.depositions_tree.item(item, "tags")
        if not tags:
            return
        self._open_path(Path(tags[0]))

    def _open_path(self, path: Path) -> None:
        if not path.exists():
            messagebox.showwarning("Open", f"Path does not exist: {path}")
            return
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=False)
        else:
            subprocess.run(["xdg-open", str(path)], check=False)

    # ------------------------------------------------------------------
    # Case/session management
    # ------------------------------------------------------------------
    def start_new_case(self) -> None:
        """Create a new case folder + ID using proper case management"""
        # Paths
        DEPO_PATH = Path("F:/DKI_Exports/Depositions")
        REPO_PATH = Path("F:/DKI_Exports/Repo_InProgress")
        
        # Create case ID and folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        case_id = f"case_{timestamp}"
        case_path = DEPO_PATH / case_id
        case_path.mkdir(parents=True, exist_ok=True)
        
        # Create registry file
        registry_file = case_path / "case_registry.json"
        registry_data = {
            "status": "initialized",
            "sections": {},
            "investigator": self.current_user or "Unknown",
            "created_at": datetime.now().isoformat(),
            "case_name": f"Case {timestamp}"
        }
        registry_file.write_text(json.dumps(registry_data, indent=2))
        
        # Set current case
        self.current_case_id = case_id
        self.status_var.set(f"Started case {case_id}")
        
        # Log to audit trail
        self.audit_trail.append({
            "timestamp": datetime.now().isoformat(),
            "action": "start_case",
            "case_id": case_id,
            "case_path": str(case_path)
        })
        
        messagebox.showinfo("New Case", f"New case started:\n{case_id}\n\nFolder: {case_path}")

    def resume_case(self) -> None:
        """Let user pick from unfinished cases in repo"""
        REPO_PATH = Path("F:/DKI_Exports/Repo_InProgress")
        
        if not REPO_PATH.exists():
            messagebox.showwarning("No Cases", "No in-progress cases found.")
            return
        
        case_file = filedialog.askopenfilename(
            initialdir=REPO_PATH, 
            title="Select case to resume",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if case_file:
            case_path = Path(case_file)
            self.current_case_id = case_path.stem
            self.status_var.set(f"Resumed case {self.current_case_id}")
            
            self.audit_trail.append({
                "timestamp": datetime.now().isoformat(),
                "action": "resume_case",
                "case_id": self.current_case_id,
                "case_path": str(case_path)
            })
            
            messagebox.showinfo("Resume Case", f"Resuming case:\n{case_file}")

    def view_case_library(self) -> None:
        """Open case library window for managing open and archived cases"""
        library_window = tk.Toplevel(self.root)
        library_window.title("Case Library")
        library_window.geometry("800x600")
        library_window.configure(bg="#f5f5f5")
        
        # Header
        header_frame = ttk.Frame(library_window, padding=20)
        header_frame.pack(fill="x")
        
        ttk.Label(
            header_frame,
            text="Case Library",
            font=("Segoe UI", 18, "bold")
        ).pack(side="left")
        
        ttk.Button(
            header_frame,
            text="Refresh",
            command=lambda: self.refresh_case_library(library_window)
        ).pack(side="right")
        
        # Case list
        list_frame = ttk.Frame(library_window, padding=20)
        list_frame.pack(fill="both", expand=True)
        
        # Create treeview for cases
        columns = ("case_id", "status", "created", "investigator")
        case_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        case_tree.heading("case_id", text="Case ID")
        case_tree.heading("status", text="Status")
        case_tree.heading("created", text="Created")
        case_tree.heading("investigator", text="Investigator")
        
        case_tree.column("case_id", width=200)
        case_tree.column("status", width=100)
        case_tree.column("created", width=150)
        case_tree.column("investigator", width=150)
        
        case_tree.pack(fill="both", expand=True)
        
        # Action buttons
        action_frame = ttk.Frame(library_window, padding=20)
        action_frame.pack(fill="x")
        
        ttk.Button(
            action_frame,
            text="Open Case",
            command=lambda: self.open_selected_case(case_tree)
        ).pack(side="left", padx=5)
        
        ttk.Button(
            action_frame,
            text="Add Material",
            command=lambda: self.add_material_to_case(case_tree)
        ).pack(side="left", padx=5)
        
        ttk.Button(
            action_frame,
            text="Finalize Report",
            command=lambda: self.finalize_case_report(case_tree)
        ).pack(side="left", padx=5)
        
        ttk.Button(
            action_frame,
            text="Lookup Closed Case",
            command=self.lookup_closed_case
        ).pack(side="left", padx=5)
        
        ttk.Button(
            action_frame,
            text="Close",
            command=library_window.destroy
        ).pack(side="right", padx=5)
        
        # Load initial cases
        self.refresh_case_library(library_window)
        
        # Store reference for refresh
        library_window.case_tree = case_tree

    def refresh_case_library(self, library_window) -> None:
        """Refresh the case library using proper folder structure"""
        if not hasattr(library_window, 'case_tree'):
            return
            
        case_tree = library_window.case_tree
        case_tree.delete(*case_tree.get_children())
        
        # Use proper folder structure
        DEPO_PATH = Path("F:/DKI_Exports/Depositions")
        REPO_PATH = Path("F:/DKI_Exports/Repo_InProgress")
        
        # Add in-progress cases from Repo_InProgress
        if REPO_PATH.exists():
            try:
                for item in REPO_PATH.iterdir():
                    if item.name.startswith('case_') and item.is_file():
                        case_id = item.stem
                        created = datetime.fromtimestamp(item.stat().st_mtime).strftime("%Y-%m-%d")
                        case_tree.insert("", "end", values=(case_id, "In Progress", created, self.current_user or "Unknown"))
            except:
                pass
        
        # Add closed cases from Depositions
        if DEPO_PATH.exists():
            try:
                for item in DEPO_PATH.iterdir():
                    if item.name.startswith('case_') and item.is_dir():
                        case_id = item.name
                        created = datetime.fromtimestamp(item.stat().st_mtime).strftime("%Y-%m-%d")
                        case_tree.insert("", "end", values=(case_id, "Closed", created, self.current_user or "Unknown"))
            except:
                pass
        
        # Always add current case if exists
        if self.current_case_id:
            case_tree.insert("", "end", values=(self.current_case_id, "Active", datetime.now().strftime("%Y-%m-%d"), self.current_user or "Unknown"))

    def open_selected_case(self, case_tree) -> None:
        """Open the selected case for editing"""
        selection = case_tree.selection()
        if not selection:
            messagebox.showwarning("Case Library", "Please select a case to open")
            return
            
        item = case_tree.item(selection[0])
        case_id = item['values'][0]
        self.current_case_id = case_id
        self.status_var.set(f"Opened case {case_id}")
        messagebox.showinfo("Case Library", f"Opened case: {case_id}")

    def add_material_to_case(self, case_tree) -> None:
        """Add material to the selected case"""
        selection = case_tree.selection()
        if not selection:
            messagebox.showwarning("Case Library", "Please select a case to add material to")
            return
            
        item = case_tree.item(selection[0])
        case_id = item['values'][0]
        status = item['values'][1]
        
        if status == "Closed":
            messagebox.showwarning("Case Library", "Cannot add material to closed case")
            return
            
        messagebox.showinfo("Case Library", f"Add material functionality for case: {case_id}")

    def finalize_case_report(self, case_tree) -> None:
        """Finalize report for the selected case"""
        selection = case_tree.selection()
        if not selection:
            messagebox.showwarning("Case Library", "Please select a case to finalize")
            return
            
        item = case_tree.item(selection[0])
        case_id = item['values'][0]
        status = item['values'][1]
        
        if status == "Closed":
            messagebox.showinfo("Case Library", f"Case {case_id} is already finalized")
            return
            
        messagebox.showinfo("Case Library", f"Finalize report functionality for case: {case_id}")

    def lookup_closed_case(self) -> None:
        """Browse finalized depo archive (read-only)"""
        DEPO_PATH = Path("F:/DKI_Exports/Depositions")
        
        if not DEPO_PATH.exists():
            messagebox.showwarning("No Closed Cases", "No closed cases in Depositions.")
            return
        
        case_file = filedialog.askopenfilename(
            initialdir=DEPO_PATH, 
            title="Select closed case",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if case_file:
            messagebox.showinfo("Closed Case Lookup", f"Opened closed case:\n{case_file}\n(Read-Only)")

    def change_user(self) -> None:
        self.setup_login_screen()

    def logout_user(self) -> None:
        self.current_user = None
        self.current_case_id = None
        self._close_advanced_window()
        self.setup_login_screen()

    # ------------------------------------------------------------------
    def _load_tool_catalog(self) -> List[Dict[str, str]]:
        entries: List[Dict[str, str]] = []
        if not self.WAR_ROOM_PROCESSORS.exists():
            return entries
        for path in sorted(self.WAR_ROOM_PROCESSORS.glob("**/*")):
            if path.is_file():
                entries.append({"status": "available", "path": str(path.relative_to(self.WAR_ROOM_PROCESSORS))})
        if not entries:
            entries.append({"status": "warning", "path": "No processors detected"})
        return entries

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    try:
        app = ProfessionalCaseManager()
        app.run()
    except Exception as exc:  # pragma: no cover - UI entry point
        logger.exception("Application error")
        messagebox.showerror("Professional Case Manager", str(exc))


if __name__ == "__main__":
    main()
