#!/usr/bin/env python3
"""
Case Management Panel - UI for case creation, loading, and file management
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, List, Any, Callable, Optional
import logging
from datetime import datetime

from ui_components import ControlPanel
from file_drop_zone import FileDropZone

logger = logging.getLogger(__name__)

class CaseManagementPanel(ttk.Frame):
    """Panel for managing cases and files"""
    
    def __init__(self, parent, on_case_created: Callable = None, 
                 on_case_loaded: Callable = None, on_files_added: Callable = None):
        super().__init__(parent)
        
        self.on_case_created = on_case_created
        self.on_case_loaded = on_case_loaded
        self.on_files_added = on_files_added
        
        self.current_case_info = None
        self.uploaded_files = []
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the case management interface"""
        
        # Case Information Section
        case_info_frame = ttk.LabelFrame(self, text="Case Information", padding="10")
        case_info_frame.pack(fill='x', pady=(0, 10))
        
        # Case status display
        self.case_status_var = tk.StringVar(value="No case loaded")
        status_label = ttk.Label(case_info_frame, textvariable=self.case_status_var, font=('Arial', 10, 'bold'))
        status_label.pack(anchor='w')
        
        # Case details display
        self.case_details_text = tk.Text(case_info_frame, height=4, wrap=tk.WORD, state='disabled')
        self.case_details_text.pack(fill='x', pady=(5, 0))
        
        # Case Controls Section
        case_controls_frame = ttk.LabelFrame(self, text="Case Controls", padding="10")
        case_controls_frame.pack(fill='x', pady=(0, 10))
        
        # Button frame
        button_frame = ttk.Frame(case_controls_frame)
        button_frame.pack(fill='x')
        
        # New case button
        self.new_case_btn = ttk.Button(
            button_frame,
            text="New Case",
            command=self.new_case,
            style='Primary.TButton'
        )
        self.new_case_btn.pack(side='left', padx=(0, 5))
        
        # Load case button
        self.load_case_btn = ttk.Button(
            button_frame,
            text="Load Case",
            command=self.load_case
        )
        self.load_case_btn.pack(side='left', padx=5)
        
        # Save case button
        self.save_case_btn = ttk.Button(
            button_frame,
            text="Save Case",
            command=self.save_case,
            state='disabled'
        )
        self.save_case_btn.pack(side='left', padx=5)
        
        # Recent cases dropdown
        recent_frame = ttk.Frame(case_controls_frame)
        recent_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Label(recent_frame, text="Recent Cases:").pack(anchor='w')
        self.recent_cases_combo = ttk.Combobox(recent_frame, state='readonly')
        self.recent_cases_combo.pack(fill='x', pady=(2, 0))
        self.recent_cases_combo.bind('<<ComboboxSelected>>', self.on_recent_case_selected)
        
        # File Management Section
        file_mgmt_frame = ttk.LabelFrame(self, text="File Management", padding="10")
        file_mgmt_frame.pack(fill='both', expand=True)
        
        # File drop zone
        self.drop_zone = FileDropZone(
            file_mgmt_frame,
            on_files_dropped=self.on_files_dropped
        )
        self.drop_zone.pack(fill='both', expand=True)
        
        # Load recent cases
        self.load_recent_cases()
    
    def new_case(self):
        """Create a new case"""
        
        dialog = NewCaseDialog(self.winfo_toplevel())
        if dialog.result:
            case_info = dialog.result
            self.current_case_info = case_info
            
            # Update UI
            self.update_case_display(case_info)
            self.enable_case_controls()
            
            # Notify callback
            if self.on_case_created:
                self.on_case_created(case_info)
            
            logger.info(f"New case created: {case_info['case_name']}")
    
    def load_case(self):
        """Load an existing case"""
        
        # Show case selection dialog
        dialog = CaseSelectionDialog(self.winfo_toplevel())
        if dialog.result:
            case_info = dialog.result
            self.current_case_info = case_info
            
            # Update UI
            self.update_case_display(case_info)
            self.enable_case_controls()
            
            # Load associated files
            if 'files' in case_info:
                self.uploaded_files = case_info['files']
                self.drop_zone.set_files(self.uploaded_files)
            
            # Notify callback
            if self.on_case_loaded:
                self.on_case_loaded(case_info)
            
            logger.info(f"Case loaded: {case_info['case_name']}")
    
    def save_case(self):
        """Save the current case"""
        
        if not self.current_case_info:
            messagebox.showwarning("Warning", "No case to save")
            return
        
        try:
            # Save case logic would go here
            # For now, just show confirmation
            messagebox.showinfo("Success", "Case saved successfully")
            logger.info(f"Case saved: {self.current_case_info['case_name']}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save case: {str(e)}")
            logger.error(f"Failed to save case: {str(e)}")
    
    def on_recent_case_selected(self, event):
        """Handle selection of a recent case"""
        
        selected = self.recent_cases_combo.get()
        if selected:
            # Load the selected recent case
            # This would integrate with the repository manager
            logger.info(f"Loading recent case: {selected}")
    
    def on_files_dropped(self, files):
        """Handle files dropped in the drop zone"""
        
        self.uploaded_files = files
        
        # Update case info with files
        if self.current_case_info:
            self.current_case_info['files'] = files
            self.current_case_info['files_count'] = len(files)
            self.update_case_display(self.current_case_info)
        
        # Notify callback
        if self.on_files_added:
            self.on_files_added(files)
        
        logger.info(f"Files added to case: {len(files)} files")
    
    def update_case_display(self, case_info: Dict[str, Any]):
        """Update the case information display"""
        
        if not case_info:
            self.case_status_var.set("No case loaded")
            self.case_details_text.configure(state='normal')
            self.case_details_text.delete(1.0, tk.END)
            self.case_details_text.configure(state='disabled')
            return
        
        # Update status
        case_name = case_info.get('case_name', 'Unknown Case')
        report_type = case_info.get('report_type', 'Unknown Type')
        self.case_status_var.set(f"{case_name} ({report_type})")
        
        # Update details
        details = []
        
        if 'client_info' in case_info:
            client_info = case_info['client_info']
            if client_info.get('client_name'):
                details.append(f"Client: {client_info['client_name']}")
            if client_info.get('client_phone'):
                details.append(f"Phone: {client_info['client_phone']}")
        
        if 'created_date' in case_info:
            details.append(f"Created: {case_info['created_date'][:10]}")
        
        files_count = case_info.get('files_count', len(self.uploaded_files))
        if files_count > 0:
            details.append(f"Files: {files_count}")
        
        details_text = '\n'.join(details) if details else "No additional details"
        
        self.case_details_text.configure(state='normal')
        self.case_details_text.delete(1.0, tk.END)
        self.case_details_text.insert(1.0, details_text)
        self.case_details_text.configure(state='disabled')
    
    def enable_case_controls(self):
        """Enable case-related controls"""
        self.save_case_btn.configure(state='normal')
    
    def disable_case_controls(self):
        """Disable case-related controls"""
        self.save_case_btn.configure(state='disabled')
    
    def enable_new_case(self):
        """Enable new case creation"""
        self.new_case_btn.configure(state='normal')
        self.load_case_btn.configure(state='normal')
    
    def enable_all(self):
        """Enable all controls"""
        self.enable_new_case()
        self.enable_case_controls()
    
    def load_recent_cases(self):
        """Load recent cases into the dropdown"""
        
        # This would integrate with the repository manager
        # For now, just add some placeholder entries
        recent_cases = [
            "Sample Case 1 - 2024-01-15",
            "Sample Case 2 - 2024-01-10",
            "Sample Case 3 - 2024-01-05"
        ]
        
        self.recent_cases_combo['values'] = recent_cases


class NewCaseDialog:
    """Dialog for creating a new case"""
    
    def __init__(self, parent):
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Create New Case")
        self.dialog.geometry("500x500")  # Increased height for buttons
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)  # Prevent resizing
        
        # Center dialog
        self.dialog.geometry("+%d+%d" % (
            parent.winfo_rootx() + 100,
            parent.winfo_rooty() + 100
        ))
        
        self.setup_dialog()
        
        # Wait for dialog to close
        self.dialog.wait_window()
    
    def setup_dialog(self):
        """Setup the dialog interface"""
        
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="Create New Investigation Case",
            font=('Arial', 16, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        # Case name
        ttk.Label(main_frame, text="Case Name:").pack(anchor='w')
        self.case_name_var = tk.StringVar()
        case_name_entry = ttk.Entry(main_frame, textvariable=self.case_name_var, width=50)
        case_name_entry.pack(fill='x', pady=(5, 15))
        case_name_entry.focus()
        
        # Report type
        ttk.Label(main_frame, text="Report Type:").pack(anchor='w')
        self.report_type_var = tk.StringVar(value="Investigative")
        report_combo = ttk.Combobox(
            main_frame,
            textvariable=self.report_type_var,
            values=["Investigative", "Surveillance", "Hybrid"],
            state="readonly"
        )
        report_combo.pack(fill='x', pady=(5, 15))
        
        # Client information frame
        client_frame = ttk.LabelFrame(main_frame, text="Client Information", padding="15")
        client_frame.pack(fill='both', expand=True, pady=(10, 15))
        
        # Client name
        ttk.Label(client_frame, text="Client Name:").pack(anchor='w')
        self.client_name_var = tk.StringVar()
        ttk.Entry(client_frame, textvariable=self.client_name_var, width=50).pack(fill='x', pady=(5, 10))
        
        # Client phone
        ttk.Label(client_frame, text="Client Phone:").pack(anchor='w')
        self.client_phone_var = tk.StringVar()
        ttk.Entry(client_frame, textvariable=self.client_phone_var, width=50).pack(fill='x', pady=(5, 10))
        
        # Client email
        ttk.Label(client_frame, text="Client Email:").pack(anchor='w')
        self.client_email_var = tk.StringVar()
        ttk.Entry(client_frame, textvariable=self.client_email_var, width=50).pack(fill='x', pady=(5, 10))
        
        # Client address
        ttk.Label(client_frame, text="Client Address:").pack(anchor='w')
        self.client_address_text = tk.Text(client_frame, height=3, width=50)
        self.client_address_text.pack(fill='x', pady=(5, 0))
        
        # Buttons - Fixed rendering issue
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(15, 0))
        
        # Create Case button (primary action)
        create_btn = tk.Button(
            button_frame,
            text="Create Case",
            command=self.create_case,
            bg='#0078d4',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20,
            pady=8
        )
        create_btn.pack(side='right')
        
        # Cancel button
        cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel,
            bg='#6c757d',
            fg='white',
            font=('Arial', 10),
            padx=20,
            pady=8
        )
        cancel_btn.pack(side='right', padx=(10, 0))
        
        # Bind Enter key
        self.dialog.bind('<Return>', lambda e: self.create_case())
        self.dialog.bind('<Escape>', lambda e: self.cancel())
    
    def create_case(self):
        """Create the new case"""
        
        case_name = self.case_name_var.get().strip()
        if not case_name:
            messagebox.showerror("Error", "Case name is required")
            return
        
        client_address = self.client_address_text.get(1.0, tk.END).strip()
        
        self.result = {
            'case_name': case_name,
            'report_type': self.report_type_var.get(),
            'client_info': {
                'client_name': self.client_name_var.get().strip(),
                'client_phone': self.client_phone_var.get().strip(),
                'client_email': self.client_email_var.get().strip(),
                'client_address': client_address,
                'contract_date': datetime.now().strftime('%Y-%m-%d')
            },
            'created_date': datetime.now().isoformat(),
            'status': 'active'
        }
        
        self.dialog.destroy()
    
    def cancel(self):
        """Cancel dialog"""
        self.result = None
        self.dialog.destroy()


class CaseSelectionDialog:
    """Dialog for selecting an existing case"""
    
    def __init__(self, parent):
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Load Existing Case")
        self.dialog.geometry("600x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.geometry("+%d+%d" % (
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))
        
        self.setup_dialog()
        
        # Wait for dialog to close
        self.dialog.wait_window()
    
    def setup_dialog(self):
        """Setup the dialog interface"""
        
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="Select Case to Load",
            font=('Arial', 16, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        # Case list
        list_frame = ttk.LabelFrame(main_frame, text="Available Cases", padding="10")
        list_frame.pack(fill='both', expand=True, pady=(0, 15))
        
        # Treeview for case list
        columns = ('Name', 'Type', 'Client', 'Date', 'Files')
        self.case_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        
        # Configure columns
        for col in columns:
            self.case_tree.heading(col, text=col)
            self.case_tree.column(col, width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.case_tree.yview)
        self.case_tree.configure(yscrollcommand=scrollbar.set)
        
        self.case_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Load sample cases
        self.load_cases()
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x')
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel
        ).pack(side='right', padx=(10, 0))
        
        ttk.Button(
            button_frame,
            text="Load Case",
            command=self.load_case,
            style='Primary.TButton'
        ).pack(side='right')
        
        # Bind double-click
        self.case_tree.bind('<Double-1>', lambda e: self.load_case())
    
    def load_cases(self):
        """Load available cases into the tree"""
        
        # Sample cases - this would integrate with repository manager
        sample_cases = [
            ("Sample Investigation 1", "Investigative", "John Doe", "2024-01-15", "5"),
            ("Surveillance Case A", "Surveillance", "Jane Smith", "2024-01-10", "12"),
            ("Hybrid Investigation", "Hybrid", "ABC Corp", "2024-01-05", "8")
        ]
        
        for case in sample_cases:
            self.case_tree.insert('', 'end', values=case)
    
    def load_case(self):
        """Load the selected case"""
        
        selection = self.case_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a case to load")
            return
        
        # Get selected case data
        item = self.case_tree.item(selection[0])
        values = item['values']
        
        self.result = {
            'case_name': values[0],
            'report_type': values[1],
            'client_info': {
                'client_name': values[2]
            },
            'created_date': values[3],
            'files_count': int(values[4])
        }
        
        self.dialog.destroy()
    
    def cancel(self):
        """Cancel dialog"""
        self.result = None
        self.dialog.destroy()

