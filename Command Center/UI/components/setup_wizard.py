#!/usr/bin/env python3
"""Setup Wizard - Fixed cancel handling"""
import tkinter as tk
from tkinter import ttk, messagebox
import json
from pathlib import Path
from datetime import datetime

def run_setup_wizard(parent=None, on_complete=None, profile_root=None, db_path=None, reset_state=False):
    """Run the setup wizard"""
    profile_root = Path(profile_root) if profile_root else Path(__file__).parent.parent
    db_path = Path(db_path) if db_path else (profile_root / "user_profiles.db")
    profile_json = profile_root / "user_profile.json"
    
    # Initialize managers
    profile_mgr = None
    operator_mgr = None
    
    try:
        import sys
        sys.path.insert(0, str(profile_root))
        from user_profile_manager import UserProfileManager
        profile_mgr = UserProfileManager(str(db_path))
    except Exception as e:
        pass
    
    try:
        from profile_manager.operator_manager import OperatorManager  
        operator_mgr = OperatorManager()
    except Exception as e:
        pass
    
    # Track completion
    completed = [False]
    
    # Create window
    if parent:
        win = tk.Toplevel(parent)
        win.transient(parent)
        win.grab_set()
    else:
        win = tk.Tk()
    
    win.title("Central Command - Setup")
    win.geometry("500x350")
    win.resizable(False, False)
    
    # Center window
    win.update_idletasks()
    x = (win.winfo_screenwidth() // 2) - 250
    y = (win.winfo_screenheight() // 2) - 175
    win.geometry(f"500x350+{x}+{y}")
    
    def on_cancel():
        if messagebox.askyesno("Cancel Setup", "Setup is required to use Central Command.\n\nAre you sure you want to cancel?", parent=win):
            completed[0] = False
            win.destroy()
    
    win.protocol("WM_DELETE_WINDOW", on_cancel)
    
    # UI
    header = tk.Frame(win, bg="#2c3e50", height=60)
    header.pack(fill="x")
    header.pack_propagate(False)
    tk.Label(header, text="Create Administrator Account", font=("Arial", 16, "bold"), bg="#2c3e50", fg="white").pack(pady=15)
    
    content = ttk.Frame(win, padding="20")
    content.pack(fill="both", expand=True)
    
    tk.Label(content, text="Enter credentials for the admin account:", font=("Arial", 10)).pack(anchor="w", pady=(0,15))
    
    form = ttk.Frame(content)
    form.pack(fill="x")
    
    ttk.Label(form, text="Username:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", pady=8)
    username_var = tk.StringVar()
    username_entry = ttk.Entry(form, textvariable=username_var, width=30)
    username_entry.grid(row=0, column=1, sticky="ew", pady=8, padx=(10,0))
    username_entry.focus()
    
    ttk.Label(form, text="Password:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", pady=8)
    password_var = tk.StringVar()
    ttk.Entry(form, textvariable=password_var, show="*", width=30).grid(row=1, column=1, sticky="ew", pady=8, padx=(10,0))
    
    ttk.Label(form, text="Full Name:", font=("Arial", 10)).grid(row=2, column=0, sticky="w", pady=8)
    fullname_var = tk.StringVar()
    ttk.Entry(form, textvariable=fullname_var, width=30).grid(row=2, column=1, sticky="ew", pady=8, padx=(10,0))
    
    ttk.Label(form, text="Company:", font=("Arial", 10)).grid(row=3, column=0, sticky="w", pady=8)
    company_var = tk.StringVar()
    ttk.Entry(form, textvariable=company_var, width=30).grid(row=3, column=1, sticky="ew", pady=8, padx=(10,0))
    
    form.columnconfigure(1, weight=1)
    
    def finish():
        username = username_var.get().strip()
        password = password_var.get()
        fullname = fullname_var.get().strip() or username
        company = company_var.get().strip() or fullname
        
        if not username or len(username) < 3:
            messagebox.showerror("Error", "Username must be at least 3 characters", parent=win)
            return
        if not password or len(password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters", parent=win)
            return
        
        try:
            # Save to database
            if profile_mgr:
                profile_mgr.create_user(username, password, full_name=fullname, company=company)
                profile_mgr.authenticate_user(username, password)
            
            # Save to operator manager
            if operator_mgr:
                try:
                    operator_mgr.create(name=username, role="admin", password=password)
                except:
                    pass
            
            # Save profile.json
            now = datetime.utcnow()
            profile_data = {
                "profile_id": "default",
                "user_name": fullname,
                "business_name": company,
                "contact_email": "",
                "operator_username": username,
                "preferred_workflow": "surveillance",
                "preferred_contract": "investigation_surveillance",
                "updated_at": now.isoformat() + "Z",
                "start_date": now.strftime("%Y-%m-%d"),
                "case_number": f"CASE-{now:%Y%m%d}"
            }
            profile_json.write_text(json.dumps(profile_data, indent=2))
            
            completed[0] = True
            messagebox.showinfo("Success", f"Account created: {username}", parent=win)
            win.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Setup failed: {e}", parent=win)
    
    btn_frame = ttk.Frame(content)
    btn_frame.pack(fill="x", pady=(15,0))
    ttk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side="right", padx=(5,0))
    ttk.Button(btn_frame, text="Create Account", command=finish).pack(side="right")
    
    win.bind("<Return>", lambda e: finish())
    
    # Ensure window is visible
    win.update()
    win.deiconify()
    win.lift()
    win.focus_force()
    
    # Run
    if parent:
        parent.wait_window(win)
    else:
        win.mainloop()
    
    # Call completion callback
    if on_complete:
        on_complete(profile_mgr if completed[0] else None)
    
    return None
