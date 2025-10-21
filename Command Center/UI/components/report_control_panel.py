#!/usr/bin/env python3
"""
Report Control Panel - UI for managing final report generation and export
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, List, Any, Callable, Optional
import logging

logger = logging.getLogger(__name__)

class ReportControlPanel(ttk.Frame):
    """Panel for controlling final report generation and export"""
    
    def __init__(self, parent, on_generate_report: Callable = None, 
                 on_export_report: Callable = None, on_print_report: Callable = None):
        super().__init__(parent)
        
        self.on_generate_report = on_generate_report
        self.on_export_report = on_export_report
        self.on_print_report = on_print_report
        
        self.report_ready = False
        self.sections_completed = 0
        self.total_sections = 0
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the report control interface"""
        
        # Report Status
        status_frame = ttk.LabelFrame(self, text="Report Status", padding="10")
        status_frame.pack(fill='x', pady=(0, 10))
        
        # Completion status
        self.completion_var = tk.StringVar(value="No sections completed")
        completion_label = ttk.Label(status_frame, textvariable=self.completion_var, 
                                  font=('Arial', 10, 'bold'))
        completion_label.pack(anchor='w')
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, 
                                           maximum=100)
        self.progress_bar.pack(fill='x', pady=(5, 0))
        
        # Report Generation
        generation_frame = ttk.LabelFrame(self, text="Report Generation", padding="10")
        generation_frame.pack(fill='x', pady=(0, 10))
        
        # Generate Report button
        self.generate_report_btn = ttk.Button(
            generation_frame,
            text="Generate Full Report",
            command=self.generate_report,
            state='disabled'
        )
        self.generate_report_btn.pack(pady=(0, 10))
        
        # Report preview
        preview_frame = ttk.LabelFrame(generation_frame, text="Report Preview", padding="5")
        preview_frame.pack(fill='both', expand=True)
        
        # Preview text area
        self.preview_text = tk.Text(preview_frame, height=8, wrap=tk.WORD, state='disabled')
        preview_scrollbar = ttk.Scrollbar(preview_frame, orient='vertical', 
                                        command=self.preview_text.yview)
        self.preview_text.configure(yscrollcommand=preview_scrollbar.set)
        
        self.preview_text.pack(side='left', fill='both', expand=True)
        preview_scrollbar.pack(side='right', fill='y')
        
        # Export Options
        export_frame = ttk.LabelFrame(self, text="Export Options", padding="10")
        export_frame.pack(fill='x', pady=(0, 10))
        
        # Export buttons frame
        export_buttons_frame = ttk.Frame(export_frame)
        export_buttons_frame.pack(fill='x')
        
        # PDF Export button
        self.export_pdf_btn = ttk.Button(
            export_buttons_frame,
            text="Export PDF",
            command=lambda: self.export_report('pdf'),
            state='disabled'
        )
        self.export_pdf_btn.pack(side='left', padx=(0, 5))
        
        # DOCX Export button
        self.export_docx_btn = ttk.Button(
            export_buttons_frame,
            text="Export DOCX",
            command=lambda: self.export_report('docx'),
            state='disabled'
        )
        self.export_docx_btn.pack(side='left', padx=5)
        
        # Print button
        self.print_btn = ttk.Button(
            export_buttons_frame,
            text="Print Report",
            command=self.print_report,
            state='disabled'
        )
        self.print_btn.pack(side='left', padx=5)
        
        # Advanced Options
        advanced_frame = ttk.LabelFrame(self, text="Advanced Options", padding="10")
        advanced_frame.pack(fill='x')
        
        # Options frame
        options_frame = ttk.Frame(advanced_frame)
        options_frame.pack(fill='x')
        
        # Digital Signature option
        self.signature_var = tk.BooleanVar()
        signature_check = ttk.Checkbutton(options_frame, text="Apply Digital Signature", 
                                        variable=self.signature_var)
        signature_check.pack(side='left', padx=(0, 10))
        
        # Watermark option
        self.watermark_var = tk.BooleanVar()
        watermark_check = ttk.Checkbutton(options_frame, text="Apply Watermark", 
                                        variable=self.watermark_var)
        watermark_check.pack(side='left', padx=(0, 10))
        
        # Template option
        self.template_var = tk.BooleanVar(value=True)
        template_check = ttk.Checkbutton(options_frame, text="Apply Template Styling", 
                                       variable=self.template_var)
        template_check.pack(side='left')
    
    def update_section_progress(self, completed: int, total: int):
        """Update section completion progress"""
        self.sections_completed = completed
        self.total_sections = total
        
        if total > 0:
            progress = (completed / total) * 100
            self.progress_var.set(progress)
            self.completion_var.set(f"{completed}/{total} sections completed ({progress:.1f}%)")
            
            if completed == total:
                self.generate_report_btn.config(state='normal')
                self.completion_var.set("✅ All sections completed - Ready to generate report")
        else:
            self.progress_var.set(0)
            self.completion_var.set("No sections available")
    
    def generate_report(self):
        """Generate the full report"""
        if self.sections_completed < self.total_sections:
            messagebox.showwarning("Warning", "Not all sections are completed yet")
            return
        
        self.generate_report_btn.config(state='disabled')
        
        # Clear previous preview
        self.preview_text.config(state='normal')
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.config(state='disabled')
        
        # Call the generation callback
        if self.on_generate_report:
            self.on_generate_report()
    
    def update_report_preview(self, preview_text: str):
        """Update the report preview"""
        self.preview_text.config(state='normal')
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(1.0, preview_text)
        self.preview_text.config(state='disabled')
        
        # Enable export buttons
        self.export_pdf_btn.config(state='normal')
        self.export_docx_btn.config(state='normal')
        self.print_btn.config(state='normal')
        self.report_ready = True
    
    def export_report(self, format_type: str):
        """Export report in specified format"""
        if not self.report_ready:
            messagebox.showwarning("Warning", "Report not ready for export")
            return
        
        # Get export options
        options = {
            'format': format_type,
            'signature': self.signature_var.get(),
            'watermark': self.watermark_var.get(),
            'template': self.template_var.get()
        }
        
        # Call export callback
        if self.on_export_report:
            self.on_export_report(format_type, options)
    
    def print_report(self):
        """Print the report"""
        if not self.report_ready:
            messagebox.showwarning("Warning", "Report not ready for printing")
            return
        
        # Call print callback
        if self.on_print_report:
            self.on_print_report()
    
    def show_export_success(self, format_type: str, file_path: str):
        """Show export success message"""
        messagebox.showinfo("Export Success", 
                          f"Report exported successfully as {format_type.upper()} to:\n{file_path}")
    
    def show_export_error(self, format_type: str, error_message: str):
        """Show export error message"""
        messagebox.showerror("Export Error", 
                           f"Failed to export report as {format_type.upper()}:\n{error_message}")