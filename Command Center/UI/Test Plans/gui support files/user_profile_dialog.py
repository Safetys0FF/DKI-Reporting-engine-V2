#!/usr/bin/env python3
"""
User Profile Dialog - Manage agency/investigator settings, branding, and actions
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox


class UserProfileDialog:
    def __init__(self, parent, app_controller):
        self.parent = parent
        self.app = app_controller
        self.upm = getattr(app_controller, 'profile_manager', None)
        self.result = None

        self.window = tk.Toplevel(parent)
        self.window.title("User Profile")
        self.window.geometry("720x640")
        self.window.transient(parent)
        self.window.grab_set()

        self._build_ui()
        self._load_settings()
        self.window.wait_window()

    def _build_ui(self):
        main = ttk.Frame(self.window, padding="10")
        main.pack(fill='both', expand=True)

        # Actions row
        actions = ttk.Frame(main)
        actions.pack(fill='x', pady=(0, 10))
        ttk.Button(actions, text="Start New Case", command=self._start_new_case).pack(side='left')

        # Appearance
        appear = ttk.LabelFrame(main, text="Appearance", padding="10")
        appear.pack(fill='x', pady=(0, 10))
        self.theme_var = tk.StringVar(value='light')
        ttk.Radiobutton(appear, text="Light", variable=self.theme_var, value='light').pack(side='left', padx=5)
        ttk.Radiobutton(appear, text="Dark", variable=self.theme_var, value='dark').pack(side='left', padx=5)

        # Agency
        agency = ttk.LabelFrame(main, text="Agency Information", padding="10")
        agency.pack(fill='x', pady=(0, 10))
        self.agency_name = tk.StringVar()
        self.agency_license = tk.StringVar()
        self.agency_addr = tk.StringVar()
        self.agency_citystzip = tk.StringVar()
        self.agency_phone = tk.StringVar()
        self.agency_email = tk.StringVar()
        self.logo_path = tk.StringVar()
        self.slogan = tk.StringVar()

        self._row(agency, "Agency Name:", self.agency_name)
        self._row(agency, "Agency License:", self.agency_license)
        self._row(agency, "Mailing Address:", self.agency_addr)
        self._row(agency, "City/State ZIP:", self.agency_citystzip)
        self._row(agency, "Phone:", self.agency_phone)
        self._row(agency, "Email:", self.agency_email)
        # Logo selector
        lrow = ttk.Frame(agency)
        lrow.pack(fill='x', pady=2)
        ttk.Label(lrow, text="Cover Logo:").pack(side='left')
        ttk.Entry(lrow, textvariable=self.logo_path, width=50).pack(side='left', padx=5, fill='x', expand=True)
        ttk.Button(lrow, text="Browse", command=self._pick_logo).pack(side='left')
        # Slogan
        self._row(agency, "Slogan (<=100 chars):", self.slogan)

        # Investigator
        inv = ttk.LabelFrame(main, text="Investigator Information", padding="10")
        inv.pack(fill='x', pady=(0, 10))
        self.inv_name = tk.StringVar()
        self.inv_title = tk.StringVar()
        self.inv_license = tk.StringVar()
        self.inv_phone = tk.StringVar()
        self.inv_email = tk.StringVar()
        self.inv_mailing = tk.StringVar()
        self.inv_citystzip = tk.StringVar()
        self.profile_photo_path = tk.StringVar()
        self._row(inv, "Investigator Name:", self.inv_name)
        self._row(inv, "Investigator Title:", self.inv_title)
        self._row(inv, "Investigator License (required):", self.inv_license)
        self._row(inv, "Investigator Phone:", self.inv_phone)
        self._row(inv, "Investigator Email:", self.inv_email)
        self._row(inv, "Investigator Mailing Address:", self.inv_mailing)
        self._row(inv, "Investigator City/State ZIP:", self.inv_citystzip)
        # Signature image selector
        self.signature_path = tk.StringVar()
        sig_row = ttk.Frame(inv)
        sig_row.pack(fill='x', pady=2)
        ttk.Label(sig_row, text="Signature Image:").pack(side='left')
        ttk.Entry(sig_row, textvariable=self.signature_path, width=50).pack(side='left', padx=5, fill='x', expand=True)
        ttk.Button(sig_row, text="Browse", command=self._pick_signature).pack(side='left')
        # Profile photo selector
        ppr = ttk.Frame(inv)
        ppr.pack(fill='x', pady=2)
        ttk.Label(ppr, text="Profile Photo:").pack(side='left')
        ttk.Entry(ppr, textvariable=self.profile_photo_path, width=50).pack(side='left', padx=5, fill='x', expand=True)
        ttk.Button(ppr, text="Browse", command=self._pick_profile_photo).pack(side='left')

        # Admin controls
        admin = ttk.LabelFrame(main, text="Admin", padding="10")
        admin.pack(fill='x', pady=(0, 10))
        self.role_admin = tk.BooleanVar(value=False)
        ttk.Checkbutton(admin, text="Admin (primary user)", variable=self.role_admin).pack(side='left')
        ttk.Button(admin, text="Add New User", command=self._add_new_user).pack(side='right')
        # Auto-open Admin Audit toggle
        admin2 = ttk.Frame(main)
        admin2.pack(fill='x', pady=(0, 6))
        self.auto_open_audit = tk.BooleanVar(value=True)
        ttk.Checkbutton(admin2, text="Auto-open Admin Audit in Review", variable=self.auto_open_audit).pack(anchor='w')

        # Footer buttons
        footer = ttk.Frame(main)
        footer.pack(fill='x', pady=(10, 0))
        ttk.Button(footer, text="Save", command=self._save).pack(side='right', padx=5)
        ttk.Button(footer, text="Close", command=self.window.destroy).pack(side='right')

    def _row(self, parent, label, var):
        row = ttk.Frame(parent)
        row.pack(fill='x', pady=2)
        ttk.Label(row, text=label, width=26, anchor='w').pack(side='left')
        ttk.Entry(row, textvariable=var).pack(side='left', fill='x', expand=True)

    def _pick_logo(self):
        path = filedialog.askopenfilename(
            title="Select Cover Logo",
            filetypes=[
                ("Images", "*.png;*.jpg;*.jpeg;*.bmp;*.gif;*.tif;*.tiff;*.heic;*.heif"),
                ("All", "*.*"),
            ],
        )
        if path:
            self.logo_path.set(path)

    def _pick_signature(self):
        path = filedialog.askopenfilename(
            title="Select Signature Image",
            filetypes=[
                ("Images", "*.png;*.jpg;*.jpeg;*.bmp;*.gif;*.tif;*.tiff;*.heic;*.heif"),
                ("All", "*.*"),
            ],
        )
        if path:
            self.signature_path.set(path)

    def _pick_profile_photo(self):
        path = filedialog.askopenfilename(
            title="Select Profile Photo",
            filetypes=[
                ("Images", "*.png;*.jpg;*.jpeg;*.bmp;*.gif;*.tif;*.tiff;*.heic;*.heif"),
                ("All", "*.*"),
            ],
        )
        if path:
            self.profile_photo_path.set(path)

    def _load_settings(self):
        if not self.upm or not self.upm.is_authenticated():
            return
        get = self.upm.get_setting
        def g(name):
            v = get(name)
            return v if v is not None else ''
        self.agency_name.set(g('agency_name'))
        self.agency_license.set(g('agency_license'))
        self.agency_addr.set(g('agency_mailing_address') or g('mailing_address'))
        self.agency_citystzip.set(g('agency_city_state_zip') or g('city_state_zip'))
        self.agency_phone.set(g('phone'))
        self.agency_email.set(g('email'))
        self.logo_path.set(g('cover_logo_path') or g('logo_path'))
        self.slogan.set(g('slogan'))
        self.inv_name.set(g('investigator_name'))
        self.inv_title.set(g('investigator_title'))
        self.inv_license.set(g('investigator_license'))
        self.inv_phone.set(g('personal_phone'))
        self.inv_email.set(g('personal_email'))
        self.inv_mailing.set(g('personal_mailing_address'))
        self.inv_citystzip.set(g('personal_city_state_zip'))
        sp = g('signature_path')
        if sp:
            self.signature_path.set(sp)
        ppp = g('profile_photo_path')
        if ppp:
            self.profile_photo_path.set(ppp)
        self.role_admin.set((g('role') or 'user') == 'admin')
        # Auto-open Admin Audit
        ao = g('auto_open_admin_audit')
        self.auto_open_audit.set(False if (isinstance(ao, str) and ao.lower() in ('0','false','no')) else True)
        # Theme
        theme = g('theme') or 'light'
        self.theme_var.set(theme if theme in ('light', 'dark') else 'light')

    def _save(self):
        if not self.upm or not self.upm.is_authenticated():
            messagebox.showerror("Error", "No user authenticated")
            return
        if not self.inv_license.get().strip():
            messagebox.showerror("Error", "Investigator license is required")
            return
        s = self.upm.set_setting
        s('agency_name', self.agency_name.get().strip())
        s('agency_license', self.agency_license.get().strip())
        s('agency_mailing_address', self.agency_addr.get().strip())
        s('agency_city_state_zip', self.agency_citystzip.get().strip())
        s('phone', self.agency_phone.get().strip())
        s('email', self.agency_email.get().strip())
        s('cover_logo_path', self.logo_path.get().strip())
        s('slogan', (self.slogan.get() or '')[:100])
        s('investigator_name', self.inv_name.get().strip())
        s('investigator_title', self.inv_title.get().strip())
        s('investigator_license', self.inv_license.get().strip())
        s('personal_phone', self.inv_phone.get().strip())
        s('personal_email', self.inv_email.get().strip())
        s('personal_mailing_address', self.inv_mailing.get().strip())
        s('personal_city_state_zip', self.inv_citystzip.get().strip())
        s('signature_path', self.signature_path.get().strip())
        s('profile_photo_path', self.profile_photo_path.get().strip())
        s('theme', self.theme_var.get())
        s('role', 'admin' if self.role_admin.get() else 'user')
        s('auto_open_admin_audit', 'true' if self.auto_open_audit.get() else 'false')
        # Apply theme immediately
        try:
            self.app.interface_manager.apply_theme(self.theme_var.get())
        except Exception:
            pass
        # Update report generator signature immediately
        try:
            if hasattr(self.app, 'report_generator'):
                self.app.report_generator.investigator_info['signature_path'] = self.signature_path.get().strip()
        except Exception:
            pass
        messagebox.showinfo("Saved", "Profile settings saved")

    def _start_new_case(self):
        if messagebox.askyesno("Start New Case", "This will clear current case data. Proceed?"):
            try:
                self.app.reset_for_new_case()
                messagebox.showinfo("Ready", "Case cleared. Ready to start a new case.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to start new case: {e}")

    def _add_new_user(self):
        # Require admin role and password confirmation for current user
        if not self.upm or not self.upm.is_authenticated():
            messagebox.showerror("Error", "No user authenticated")
            return
        if (self.upm.get_current_role() or 'user') != 'admin':
            messagebox.showerror("Error", "Admin privileges required")
            return
        pwd = tk.simpledialog.askstring("Admin Confirmation", "Enter your password:", show='*', parent=self.window)
        if not pwd or not self.upm.verify_current_password(pwd):
            messagebox.showerror("Error", "Admin confirmation failed")
            return
        NewUserDialog(self.window, self.upm)


class NewUserDialog:
    def __init__(self, parent, upm):
        self.upm = upm
        self.window = tk.Toplevel(parent)
        self.window.title("Add New User")
        self.window.geometry("480x400")
        self.window.transient(parent)
        self.window.grab_set()

        main = ttk.Frame(self.window, padding="10")
        main.pack(fill='both', expand=True)

        self.username = tk.StringVar()
        self.password = tk.StringVar()
        self.email = tk.StringVar()
        self.full_name = tk.StringVar()
        self.company = tk.StringVar()
        self.license_number = tk.StringVar()
        self.role_admin = tk.BooleanVar(value=False)

        self._row(main, "Username:", self.username)
        self._row(main, "Password:", self.password, show='*')
        self._row(main, "Email:", self.email)
        self._row(main, "Full Name:", self.full_name)
        self._row(main, "Company:", self.company)
        self._row(main, "Investigator License:", self.license_number)
        ttk.Checkbutton(main, text="Admin (primary user)", variable=self.role_admin).pack(anchor='w', pady=(8,0))

        footer = ttk.Frame(main)
        footer.pack(fill='x', pady=(10,0))
        ttk.Button(footer, text="Create", command=self._create).pack(side='right', padx=5)
        ttk.Button(footer, text="Close", command=self.window.destroy).pack(side='right')

        self.window.wait_window()

    def _row(self, parent, label, var, show=None):
        row = ttk.Frame(parent)
        row.pack(fill='x', pady=2)
        ttk.Label(row, text=label, width=20, anchor='w').pack(side='left')
        e = ttk.Entry(row, textvariable=var, show=show)
        e.pack(side='left', fill='x', expand=True)

    def _create(self):
        if not self.username.get().strip() or not self.password.get().strip():
            messagebox.showerror("Error", "Username and password are required")
            return
        if not self.license_number.get().strip():
            messagebox.showerror("Error", "Investigator license is required")
            return
        if self.upm.create_user(self.username.get().strip(), self.password.get().strip(),
                                self.email.get().strip(), self.full_name.get().strip(),
                                self.company.get().strip(), self.license_number.get().strip()):
            # Set role for new user
            try:
                self.upm.set_setting_for_user(self.username.get().strip(), 'role', 'admin' if self.role_admin.get() else 'user')
            except Exception:
                pass
            messagebox.showinfo("Success", "User created")
            self.window.destroy()
