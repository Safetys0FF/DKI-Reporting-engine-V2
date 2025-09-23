#!/usr/bin/env python3
"""
Section Control Panel - UI for managing report sections
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Any, Callable, Optional
import logging

logger = logging.getLogger(__name__)

class SectionControlPanel(ttk.Frame):
    """Panel for controlling report section generation and management"""
    
    def __init__(self, parent, on_generate_section: Callable = None, 
                 on_approve_section: Callable = None, on_next_section: Callable = None):
        super().__init__(parent)
        
        self.on_generate_section = on_generate_section
        self.on_approve_section = on_approve_section
        self.on_next_section = on_next_section
        
        self.current_section = None
        self.sections = []
        self.section_states = {}
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the section control interface"""
        
        # Section Selection
        selection_frame = ttk.LabelFrame(self, text="Section Selection", padding="10")
        selection_frame.pack(fill='x', pady=(0, 10))
        
        # Section dropdown
        ttk.Label(selection_frame, text="Current Section:").pack(anchor='w')
        self.section_var = tk.StringVar()
        self.section_combo = ttk.Combobox(selection_frame, textvariable=self.section_var, 
                                        state="readonly", width=40)
        self.section_combo.pack(fill='x', pady=(5, 10))
        
        # Section Controls
        controls_frame = ttk.LabelFrame(self, text="Section Controls", padding="10")
        controls_frame.pack(fill='x', pady=(0, 10))
        
        # Button frame
        button_frame = ttk.Frame(controls_frame)
        button_frame.pack(fill='x')
        
        # Generate Section button
        self.generate_btn = ttk.Button(
            button_frame,
            text="Generate Section",
            command=self.generate_section,
            state='disabled'
        )
        self.generate_btn.pack(side='left', padx=(0, 5))
        
        # Review Section button
        self.review_btn = ttk.Button(
            button_frame,
            text="Review Section",
            command=self.review_section,
            state='disabled'
        )
        self.review_btn.pack(side='left', padx=5)
        
        # Approve Section button
        self.approve_btn = ttk.Button(
            button_frame,
            text="Approve Section",
            command=self.approve_section,
            state='disabled'
        )
        self.approve_btn.pack(side='left', padx=5)
        
        # Next Section button
        self.next_btn = ttk.Button(
            button_frame,
            text="Next Section",
            command=self.next_section,
            state='disabled'
        )
        self.next_btn.pack(side='left', padx=5)
        
        # Section Status
        status_frame = ttk.LabelFrame(self, text="Section Status", padding="10")
        status_frame.pack(fill='x', pady=(0, 10))
        
        # Status display
        self.status_var = tk.StringVar(value="No section selected")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                               font=('Arial', 10, 'bold'))
        status_label.pack(anchor='w')
        
        # Section Progress
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, 
                                           maximum=100)
        self.progress_bar.pack(fill='x', pady=(5, 0))
        
        # Section Content Preview
        preview_frame = ttk.LabelFrame(self, text="Section Preview", padding="10")
        preview_frame.pack(fill='both', expand=True)
        
        # Content text area
        self.content_text = tk.Text(preview_frame, height=10, wrap=tk.WORD, state='disabled')
        content_scrollbar = ttk.Scrollbar(preview_frame, orient='vertical', 
                                        command=self.content_text.yview)
        self.content_text.configure(yscrollcommand=content_scrollbar.set)
        
        self.content_text.pack(side='left', fill='both', expand=True)
        content_scrollbar.pack(side='right', fill='y')
    
    def update_sections(self, sections: List[str], report_type: str = "Investigative"):
        """Update the available sections"""
        self.sections = sections
        self.section_combo['values'] = sections
        
        if sections:
            self.section_combo.set(sections[0])
            self.current_section = sections[0]
            self.generate_btn.config(state='normal')
            self.status_var.set(f"Ready to generate: {self.current_section}")
        else:
            self.generate_btn.config(state='disabled')
            self.status_var.set("No sections available")
    
    def generate_section(self):
        """Generate the current section"""
        if not self.current_section:
            messagebox.showwarning("Warning", "No section selected")
            return
        
        self.generate_btn.config(state='disabled')
        self.status_var.set(f"Generating {self.current_section}...")
        self.progress_var.set(25)
        
        # Clear previous content
        self.content_text.config(state='normal')
        self.content_text.delete(1.0, tk.END)
        self.content_text.config(state='disabled')
        
        # Call the generation callback
        if self.on_generate_section:
            self.on_generate_section(self.current_section)
    
    def review_section(self):
        """Review the current section"""
        if not self.current_section:
            messagebox.showwarning("Warning", "No section selected")
            return
        
        # Enable review mode
        self.content_text.config(state='normal')
        self.review_btn.config(state='disabled')
        self.approve_btn.config(state='normal')
        self.status_var.set(f"Reviewing {self.current_section}")
    
    def approve_section(self):
        """Approve the current section"""
        if not self.current_section:
            messagebox.showwarning("Warning", "No section selected")
            return
        
        # Mark section as approved
        self.section_states[self.current_section] = 'approved'
        self.approve_btn.config(state='disabled')
        self.next_btn.config(state='normal')
        self.status_var.set(f"✅ {self.current_section} approved")
        
        # Call approval callback
        if self.on_approve_section:
            self.on_approve_section(self.current_section)
    
    def next_section(self):
        """Move to the next section"""
        if not self.sections:
            messagebox.showwarning("Warning", "No sections available")
            return
        
        current_index = self.sections.index(self.current_section) if self.current_section in self.sections else -1
        next_index = current_index + 1
        
        if next_index < len(self.sections):
            self.current_section = self.sections[next_index]
            self.section_combo.set(self.current_section)
            self.generate_btn.config(state='normal')
            self.review_btn.config(state='disabled')
            self.approve_btn.config(state='disabled')
            self.next_btn.config(state='disabled')
            self.status_var.set(f"Ready to generate: {self.current_section}")
            
            # Clear content
            self.content_text.config(state='normal')
            self.content_text.delete(1.0, tk.END)
            self.content_text.config(state='disabled')
            
            # Call next section callback
            if self.on_next_section:
                self.on_next_section(self.current_section)
        else:
            messagebox.showinfo("Info", "All sections completed!")
    
    def update_section_content(self, content: str):
        """Update the section content preview"""
        self.content_text.config(state='normal')
        self.content_text.delete(1.0, tk.END)
        self.content_text.insert(1.0, content)
        self.content_text.config(state='disabled')
        
        self.progress_var.set(100)
        self.status_var.set(f"✅ {self.current_section} generated")
        self.generate_btn.config(state='normal')
        self.review_btn.config(state='normal')
    
    def on_section_combo_change(self, event=None):
        """Handle section dropdown change"""
        self.current_section = self.section_var.get()
        if self.current_section:
            self.generate_btn.config(state='normal')
            self.status_var.set(f"Ready to generate: {self.current_section}")
        else:
            self.generate_btn.config(state='disabled')
            self.status_var.set("No section selected")