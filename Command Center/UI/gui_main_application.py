#!/usr/bin/env python3
"""
DKI Central Command - GUI Application
Clean GUI interface for the Central Command system
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, List, Any, Optional
import json
from datetime import datetime
import threading
import logging

# Import Central Command Plugin
sys.path.append(r"F:\The Central Command\Command Center\Start Menu\Run Time")

from central_plugin import central_plugin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dki_central_command.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DKIEngineApp:
    """Main application class for the DKI Central Command GUI"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("DKI Central Command - Investigation Report Generator")
        self.root.geometry("1400x900")
        self.root.configure(bg='#f0f0f0')
        
        # Initialize Central Command Plugin
        self.central_plugin = central_plugin
        self.central_plugin.log_event("GUI started")
        
        # Application state
        self.current_case_id = None
        self.current_case = None
        self.case_metadata: Dict[str, Any] = {}
        self.uploaded_files = []
        self.section_data = {}
        self.report_type = tk.StringVar(value="Investigative")
        self.section_name_to_id: Dict[str, str] = {}
        self.section_choices = ['section_1', 'section_3', 'section_5', 'section_8', 'section_cp', 'section_dp', 'section_toc']
        self.selected_section = tk.StringVar(value=self.section_choices[0])
        
        # Setup UI
        self.setup_ui()
        
        logger.info("DKI Central Command GUI initialized")
    
    def setup_ui(self):
        """Setup the main user interface"""
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = tk.Label(main_frame, text="DKI Central Command", 
                              font=('Arial', 20, 'bold'), bg='#f0f0f0')
        title_label.pack(pady=(0, 20))
        
        # Case management section
        case_frame = ttk.LabelFrame(main_frame, text="Case Management", padding="10")
        case_frame.pack(fill='x', pady=(0, 10))
        
        # New case button
        new_case_btn = ttk.Button(case_frame, text="New Case", command=self.new_case)
        new_case_btn.pack(side='left', padx=(0, 10))
        
        # Case ID display
        self.case_id_var = tk.StringVar(value="No case selected")
        case_id_label = ttk.Label(case_frame, textvariable=self.case_id_var)
        case_id_label.pack(side='left')
        
        # File upload section
        upload_frame = ttk.LabelFrame(main_frame, text="File Upload", padding="10")
        upload_frame.pack(fill='x', pady=(0, 10))
        
        # File selection button
        select_files_btn = ttk.Button(upload_frame, text="Select Files", command=self.select_files)
        select_files_btn.pack(side='left', padx=(0, 10))
        
        # File list
        self.file_listbox = tk.Listbox(upload_frame, height=4)
        self.file_listbox.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        # Process files button
        process_btn = ttk.Button(upload_frame, text="Process Files", command=self.process_files)
        process_btn.pack(side='right')
        
        # Status section
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        status_frame.pack(fill='x', pady=(0, 10))
        
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.pack()
        
        # Section generation
        section_frame = ttk.LabelFrame(main_frame, text="Section Generation", padding="10")
        section_frame.pack(fill='both', expand=True)
        
        section_controls = ttk.Frame(section_frame)
        section_controls.pack(fill='x', pady=(0, 10))

        ttk.Label(section_controls, text='Section:').pack(side='left', padx=(0, 5))
        section_combo = ttk.Combobox(section_controls, textvariable=self.selected_section, values=self.section_choices, state='readonly')
        section_combo.pack(side='left', padx=(0, 10))
        # Generate section button
        generate_btn = ttk.Button(section_frame, text="Generate Section", command=self.generate_section)
        generate_btn.pack(pady=(0, 10))
        
        # Section text area
        self.section_text = tk.Text(section_frame, height=15, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(section_frame, orient="vertical", command=self.section_text.yview)
        self.section_text.configure(yscrollcommand=scrollbar.set)
        
        self.section_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Bus console button
        bus_console_btn = ttk.Button(main_frame, text="Show Bus Console", command=self.show_bus_console)
        bus_console_btn.pack(pady=(10, 0))
    

        def new_case(self):
            """Create a new case"""
            try:
                case_info = {
                    "report_type": self.report_type.get(),
                    "created_at": datetime.now().isoformat(),
                    "origin": "gui"
                }
                self.current_case_id = self.central_plugin.bus.new_case(case_info)
            except Exception as exc:
                logger.error(f"Failed to initialize case on bus: {exc}")
                self.current_case_id = f"case_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            self.case_metadata = case_info
            self.case_id_var.set(f"Case ID: {self.current_case_id}")
            self.uploaded_files = []
            self.section_data = {}
            self.file_listbox.delete(0, tk.END)
            self.section_text.delete(1.0, tk.END)
            self.status_var.set("New case created")

            try:
                summary = self.central_plugin.get_case_summary(self.current_case_id)
                self.section_text.insert(tk.END, f"Case Summary: {summary}\n\n")

")
            except Exception as e:
                logger.error(f"Error getting case summary: {e}")
    def select_files(self):
        """Select files for processing"""
        files = filedialog.askopenfilenames(
            title="Select files to process",
            filetypes=[
                ("All files", "*.*"),
                ("PDF files", "*.pdf"),
                ("Image files", "*.jpg *.jpeg *.png *.tiff"),
                ("Text files", "*.txt"),
                ("Word documents", "*.docx *.doc")
            ]
        )
        
        if files:
            self.uploaded_files.extend(files)
            for file_path in files:
                filename = os.path.basename(file_path)
                self.file_listbox.insert(tk.END, filename)
            self.status_var.set(f"{len(files)} files selected")
    

def process_files(self):
    """Process uploaded files"""
    if not self.uploaded_files:
        messagebox.showwarning("No Files", "Please select files first")
        return

    self.status_var.set("Processing files...")

    def process_thread():
        try:
            processed_data = {}
            for file_path in self.uploaded_files:
                filename = os.path.basename(file_path)
                file_info = {
                    "path": file_path,
                    "name": filename,
                    "size": os.path.getsize(file_path),
                    "timestamp": datetime.now().isoformat()
                }
                result = self.central_plugin.store_file(file_info)
                processed_data[filename] = result

            try:
                self.central_plugin.bus.add_files(self.uploaded_files)
            except Exception as bus_error:
                logger.warning(f"Failed to register files with bus: {bus_error}")

            self.root.after(0, lambda: self.on_files_processed(processed_data))
        except Exception as e:
            logger.error(f"Error processing files: {e}")
            self.root.after(0, lambda: self.status_var.set(f"Error: {str(e)}"))

    threading.Thread(target=process_thread, daemon=True).start()

    def on_files_processed(self, processed_data):
        """Handle processed files"""
        self.section_data['processed_files'] = processed_data
        self.status_var.set("Files processed successfully - generating narrative snippet...")

        section_id = self.selected_section.get()
        try:
            response = self.central_plugin.generate_narrative(processed_data, section_id=section_id)
        except Exception as exc:
            logger.error(f"Narrative generation failed: {exc}")
            self.section_text.insert(tk.END, f"

[Narrative Error]: {exc}
")
            return

        summary = response.get("summary") or "No summary returned"
        self.section_text.insert(tk.END, f"

[Auto Summary - {section_id}]:
{summary}")
        messagebox.showinfo("Narrative Generated", f"Assembler responded:

{summary}")
        self.status_var.set("Narrative summary ready")

def generate_section(self):
    """Generate a section using Central Command"""
    if not self.section_data.get('processed_files'):
        messagebox.showwarning("No Data", "Please process files first")
        return

    self.status_var.set("Generating section...")

    def generate_thread():
        try:
            processed_data = self.section_data.get('processed_files', {})
            section_id = self.selected_section.get()
            response = self.central_plugin.generate_narrative(processed_data, section_id=section_id)
            self.root.after(0, lambda: self.on_section_generated(response, section_id))
        except Exception as e:
            logger.error(f"Error generating section: {e}")
            self.root.after(0, lambda: self.status_var.set(f"Error: {str(e)}"))

    threading.Thread(target=generate_thread, daemon=True).start()

    def on_section_generated(self, response, section_id):
        """Handle generated section"""
        summary = response.get("summary", "No summary available")
        self.section_text.insert(tk.END, f"

[Generated Section - {section_id}]:
{summary}")
        self.status_var.set("Section generated successfully")

    def show_bus_console(self):
        """Show bus communication console"""
        console = tk.Toplevel(self.root)
        console.title("Bus Feedback Console")
        console.geometry("600x400")

        text_area = tk.Text(console, wrap=tk.WORD)
        text_area.pack(fill='both', expand=True)

        def log(message):
            text_area.insert(tk.END, f"{message}
")
            text_area.see(tk.END)

        try:
            events = self.central_plugin.bus.get_event_log(limit=100)
        except Exception as exc:
            log(f"Failed to read bus event log: {exc}")
            return

        for event in events or []:
            timestamp = event.get('timestamp', 'unknown')
            source = event.get('source', 'unknown')
            message = event.get('message', '')
            log(f"[{timestamp}] {source}: {message}")
    def run(self):
        """Run the application"""
        self.root.mainloop()

def main():
    """Main entry point"""
    try:
        app = DKIEngineApp()
        app.run()
    except Exception as e:
        logger.error(f"Application error: {e}")
        messagebox.showerror("Error", f"Application failed to start: {str(e)}")

if __name__ == "__main__":
   