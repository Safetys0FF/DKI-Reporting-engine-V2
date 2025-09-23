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
                 on_approve_section: Callable = None, on_next_section: Callable = None,
                 on_section_selected: Callable[[str], None] = None,
                 on_section_generated: Callable = None, on_section_approved: Callable = None):
        super().__init__(parent)
        
        if on_generate_section is None and on_section_generated is not None:
            on_generate_section = on_section_generated
        if on_approve_section is None and on_section_approved is not None:
            on_approve_section = on_section_approved
        
        self.on_generate_section = on_generate_section
        self.on_approve_section = on_approve_section
        self.on_next_section = on_next_section
        self.on_section_selected = on_section_selected
        
        self.current_section = None
        self.sections: List[str] = []
        self.section_states: Dict[str, str] = {}
        self.current_plan: Optional[Dict[str, Any]] = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the section control interface"""
        
        # Section Selection
        selection_frame = ttk.LabelFrame(self, text="Section Selection", padding="10")
        selection_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(selection_frame, text="Current Section:").pack(anchor='w')
        self.section_var = tk.StringVar()
        self.section_combo = ttk.Combobox(selection_frame, textvariable=self.section_var, 
                                        state="readonly", width=40)
        self.section_combo.pack(fill='x', pady=(5, 10))
        self.section_combo.bind('<<ComboboxSelected>>', self._handle_section_selection)
        
        # Section Controls
        controls_frame = ttk.LabelFrame(self, text="Section Controls", padding="10")
        controls_frame.pack(fill='x', pady=(0, 10))
        
        button_frame = ttk.Frame(controls_frame)
        button_frame.pack(fill='x')
        
        self.generate_btn = ttk.Button(
            button_frame,
            text="Generate Section",
            command=self.generate_section,
            state='disabled'
        )
        self.generate_btn.pack(side='left', padx=(0, 5))
        
        self.review_btn = ttk.Button(
            button_frame,
            text="Review Section",
            command=self.review_section,
            state='disabled'
        )
        self.review_btn.pack(side='left', padx=5)
        
        self.approve_btn = ttk.Button(
            button_frame,
            text="Approve Section",
            command=self.approve_section,
            state='disabled'
        )
        self.approve_btn.pack(side='left', padx=5)
        
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
        
        self.status_var = tk.StringVar(value="No section selected")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                               font=('Arial', 10, 'bold'))
        status_label.pack(anchor='w')
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill='x', pady=(5, 0))
        
        # Section Content Preview
        preview_frame = ttk.LabelFrame(self, text="Section Preview", padding="10")
        preview_frame.pack(fill='both', expand=True)
        
        self.content_text = tk.Text(preview_frame, height=10, wrap=tk.WORD, state='disabled')
        content_scrollbar = ttk.Scrollbar(preview_frame, orient='vertical', command=self.content_text.yview)
        self.content_text.configure(yscrollcommand=content_scrollbar.set)
        
        self.content_text.pack(side='left', fill='both', expand=True)
        content_scrollbar.pack(side='right', fill='y')
        
        # Parsing guidance panel
        parsing_frame = ttk.LabelFrame(self, text="Parsing Guidance", padding="10")
        parsing_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        self.parsing_text = tk.Text(parsing_frame, height=12, wrap=tk.WORD, state='disabled')
        parsing_scroll = ttk.Scrollbar(parsing_frame, orient='vertical', command=self.parsing_text.yview)
        self.parsing_text.configure(yscrollcommand=parsing_scroll.set)
        self.parsing_text.pack(side='left', fill='both', expand=True)
        parsing_scroll.pack(side='right', fill='y')
    
    def update_sections(self, sections: List[str], report_type: str = "Investigative"):
        """Update the available sections"""
        self.sections = sections
        self.section_combo['values'] = sections
        
        if sections:
            self.section_combo.set(sections[0])
            self.current_section = sections[0]
            self.generate_btn.config(state='normal')
            self.status_var.set(f"Ready to generate: {self.current_section}")
            self._notify_section_selected()
        else:
            self.generate_btn.config(state='disabled')
            self.status_var.set("No sections available")
            self.update_parsing_plan(None)
    
    def generate_section(self):
        """Generate the current section"""
        if not self.current_section:
            messagebox.showwarning("Warning", "No section selected")
            return
        
        self.generate_btn.config(state='disabled')
        self.status_var.set(f"Generating {self.current_section}...")
        self.progress_var.set(25)
        
        self.content_text.config(state='normal')
        self.content_text.delete(1.0, tk.END)
        self.content_text.config(state='disabled')
        
        if self.on_generate_section:
            self.on_generate_section(self.current_section)
    
    def review_section(self):
        """Review the current section"""
        if not self.current_section:
            messagebox.showwarning("Warning", "No section selected")
            return
        
        self.content_text.config(state='normal')
        self.review_btn.config(state='disabled')
        self.approve_btn.config(state='normal')
        self.status_var.set(f"Reviewing {self.current_section}")
    
    def approve_section(self):
        """Approve the current section"""
        if not self.current_section:
            messagebox.showwarning("Warning", "No section selected")
            return
        
        self.section_states[self.current_section] = 'approved'
        self.approve_btn.config(state='disabled')
        self.next_btn.config(state='normal')
        self.status_var.set(f"? {self.current_section} approved")
        
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
            
            self.content_text.config(state='normal')
            self.content_text.delete(1.0, tk.END)
            self.content_text.config(state='disabled')
            self.update_parsing_plan(None)
            self._notify_section_selected()
        else:
            messagebox.showinfo("Info", "No more sections to process")
    
    def update_section_content(self, section_name: str, content: str):
        """Update the preview area with generated content."""
        self.current_section = section_name
        self.section_combo.set(section_name)
        self.content_text.config(state='normal')
        self.content_text.delete(1.0, tk.END)
        self.content_text.insert(1.0, content or '')
        self.content_text.config(state='disabled')
        self.review_btn.config(state='normal')
        self.status_var.set(f"{section_name} generated successfully")
        self.progress_var.set(100)
        self._notify_section_selected()
    
    def update_parsing_plan(self, plan: Optional[Dict[str, Any]]):
        """Display parsing plan guidance for the active section."""
        self.current_plan = plan
        self.parsing_text.config(state='normal')
        self.parsing_text.delete(1.0, tk.END)
        if not plan:
            self.parsing_text.insert(1.0, "No parsing plan available for this section yet.")
            self.parsing_text.config(state='disabled')
            return
        
        def _format_value(value: Any) -> str:
            if isinstance(value, dict):
                return '\n'.join([f"    - {k}: {v}" for k, v in value.items()])
            if isinstance(value, list):
                return '\n'.join([f"    - {item}" for item in value])
            return f"    - {value}"
        
        self.parsing_text.insert(tk.END, "Inputs:\n")
        for key, value in (plan.get('inputs') or {}).items():
            self.parsing_text.insert(tk.END, f"  {key}:\n{_format_value(value)}\n")
        
        triggers = plan.get('openai_triggers') or []
        if triggers:
            self.parsing_text.insert(tk.END, "\nOpenAI Triggers:\n")
            for trig in triggers:
                self.parsing_text.insert(tk.END, f"  - {trig.get('id')} ({trig.get('when')}): {trig.get('description')}\n")
        
        checklist = plan.get('ui_checklist') or []
        if checklist:
            self.parsing_text.insert(tk.END, "\nUI Checklist:\n")
            for item in checklist:
                self.parsing_text.insert(tk.END, f"  - {item}\n")
        
        results = plan.get('results') or plan.get('parsing_results') or []
        if results:
            self.parsing_text.insert(tk.END, "\nLatest Trigger Results:\n")
            for res in results:
                self.parsing_text.insert(tk.END, f"  - {res.get('id')}: {res.get('status')} ({res.get('notes', '')})\n")
        
        mapping = plan.get('mapping_document')
        if mapping:
            self.parsing_text.insert(tk.END, f"\nMapping Document: {mapping}\n")
        
        self.parsing_text.config(state='disabled')
    
    # ------------------------------------------------------------------
    def _handle_section_selection(self, event=None):
        selection = self.section_combo.get()
        if not selection:
            return
        self.current_section = selection
        self.generate_btn.config(state='normal')
        self.status_var.set(f"Ready to generate: {self.current_section}")
        self._notify_section_selected()
    
    def _notify_section_selected(self):
        if self.on_section_selected and self.current_section:
            try:
                self.on_section_selected(self.current_section)
            except Exception as exc:
                logger.debug(f"Section selection callback failed: {exc}")