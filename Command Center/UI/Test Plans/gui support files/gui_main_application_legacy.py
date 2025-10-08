#!/usr/bin/env python3
"""
Evidence Panel for the Central Command GUI.
Designed to be embedded inside the main shell application.
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, Any, List
from datetime import datetime
import threading
import logging

logger = logging.getLogger(__name__)


class EvidencePanel(ttk.Frame):
    """Evidence intake, processing, and narrative generation panel."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.central_plugin = controller.central_plugin

        self.current_case_id: str | None = None
        self.uploaded_files: List[str] = []
        self.section_data: Dict[str, Any] = {}

        self.section_choices = ['section_1', 'section_3', 'section_5', 'section_8', 'section_cp', 'section_dp', 'section_toc']
        self.selected_section = tk.StringVar(value=self.section_choices[0])
        self.status_var = tk.StringVar(value='Ready')

        self._build_ui()

    def _build_ui(self):
        container = ttk.Frame(self, padding='10')
        container.pack(fill='both', expand=True)

        header = ttk.Frame(container)
        header.pack(fill='x')
        ttk.Button(header, text='New Case', command=self.new_case).pack(side='left')
        self.case_id_var = tk.StringVar(value='No case selected')
        ttk.Label(header, textvariable=self.case_id_var, font=('Arial', 10, 'bold')).pack(side='left', padx=10)

        upload_frame = ttk.LabelFrame(container, text='File Upload', padding='10')
        upload_frame.pack(fill='x', pady=(10, 10))
        ttk.Button(upload_frame, text='Select Files', command=self.select_files).pack(side='left')
        self.file_listbox = tk.Listbox(upload_frame, height=4)
        self.file_listbox.pack(side='left', fill='x', expand=True, padx=(10, 0))
        ttk.Button(upload_frame, text='Process Files', command=self.process_files).pack(side='left', padx=10)

        status_frame = ttk.Frame(container)
        status_frame.pack(fill='x')
        ttk.Label(status_frame, textvariable=self.status_var).pack(anchor='w')

        section_frame = ttk.LabelFrame(container, text='Section Generation', padding='10')
        section_frame.pack(fill='both', expand=True, pady=(10, 0))

        controls_frame = ttk.Frame(section_frame)
        controls_frame.pack(fill='x')
        ttk.Label(controls_frame, text='Section:').pack(side='left')
        section_combo = ttk.Combobox(controls_frame, textvariable=self.selected_section, values=self.section_choices, state='readonly')
        section_combo.pack(side='left', padx=(5, 10))
        ttk.Button(controls_frame, text='Generate Section', command=self.generate_section).pack(side='left')

        self.section_text = tk.Text(section_frame, height=20, wrap=tk.WORD)
        self.section_text.pack(fill='both', expand=True, pady=(10, 0))

        ttk.Button(container, text='Show Bus Console', command=self.show_bus_console).pack(pady=(10, 0))

    def new_case(self):
        case_info = {
            'report_type': self.controller.report_type,
            'created_at': datetime.now().isoformat(),
            'origin': 'gui'
        }
        case_id = self.controller.new_case(case_info)
        self.current_case_id = case_id
        self.case_id_var.set(f'Case ID: {case_id}')
        self.uploaded_files.clear()
        self.section_data.clear()
        self.file_listbox.delete(0, tk.END)
        self.section_text.delete(1.0, tk.END)
        self.status_var.set('New case created')
        summary = self.controller.get_case_summary(case_id)
        formatted = self._format_summary(summary)
        if formatted:
            self.section_text.insert(tk.END, formatted + '\n\n')

    def select_files(self):
        files = filedialog.askopenfilenames(title='Select files')
        if not files:
            return
        self.uploaded_files.extend(files)
        for file_path in files:
            self.file_listbox.insert(tk.END, os.path.basename(file_path))
        self.status_var.set(f'{len(self.uploaded_files)} files selected')

    def process_files(self):
        if not self.uploaded_files:
            messagebox.showwarning('No Files', 'Please select files first')
            return
        if not self.current_case_id:
            messagebox.showwarning('No Case', 'Create a case before processing files')
            return
        self.status_var.set('Processing files...')

        def worker():
            try:
                processed_data: Dict[str, Any] = {}
                for file_path in self.uploaded_files:
                    info = {
                        'path': file_path,
                        'name': os.path.basename(file_path),
                        'size': os.path.getsize(file_path),
                        'timestamp': datetime.now().isoformat()
                    }
                    processed_data[info['name']] = self.controller.store_file(info)
                self.controller.register_files(self.uploaded_files)
                self.section_data['processed_files'] = processed_data
                self.after(0, lambda: self._after_processing(processed_data))
            except Exception as exc:
                logger.error('Error processing files: %s', exc)
                self.after(0, lambda: self.status_var.set(f'Error: {exc}'))

        threading.Thread(target=worker, daemon=True).start()

    def _after_processing(self, processed_data):
        self.status_var.set('Files processed. Narrative summary ready.')
        section_id = self.selected_section.get()
        response = self.controller.generate_narrative(processed_data, section_id)
        self._display_narrative(response, prefix='Auto Summary')

    def generate_section(self):
        processed = self.section_data.get('processed_files')
        if not processed:
            messagebox.showwarning('No Data', 'Process files before generating a section')
            return
        section_id = self.selected_section.get()
        self.status_var.set(f'Generating section {section_id}...')

        def worker():
            response = self.controller.generate_narrative(processed, section_id)
            self.after(0, lambda: self._display_narrative(response, prefix=f'Generated Section - {section_id}'))

        threading.Thread(target=worker, daemon=True).start()

    def _display_narrative(self, response, prefix):
        if isinstance(response, dict):
            if response.get('status') == 'ok':
                summary = response.get('summary', 'No summary')
                self.section_text.insert(tk.END, f'\n\n[{prefix}]:\n{summary}')
                self.status_var.set('Narrative generated successfully')
            else:
                error = response.get('error', 'Unknown error')
                self.section_text.insert(tk.END, f'\n\n[{prefix} Error]: {error}')
                self.status_var.set(f'Error: {error}')
        else:
            self.section_text.insert(tk.END, f'\n\n[{prefix}]: {response}')
            self.status_var.set('Narrative result returned')

    def show_bus_console(self):
        console = tk.Toplevel(self)
        console.title('Bus Event Log')
        console.geometry('700x400')
        text_area = tk.Text(console, wrap=tk.WORD)
        text_area.pack(fill='both', expand=True)
        events = self.controller.get_bus_events(limit=200)
        if not events:
            text_area.insert(tk.END, 'No recent events')
            return
        for event in events:
            ts = event.get('timestamp', 'unknown')
            source = event.get('source', 'unknown')
            msg = event.get('message', '')
            text_area.insert(tk.END, f'[{ts}] {source}: {msg}\n')
            text_area.see(tk.END)

    def _format_summary(self, summary):
        if not summary:
            return ''
        if isinstance(summary, str):
            return summary
        if isinstance(summary, dict):
            parts = [f'{key}: {value}' for key, value in summary.items()]
            return 'Case Summary\n' + '\n'.join(parts)
        return str(summary)


if __name__ == '__main__':
    from central_plugin import central_plugin

    class _Controller:
        def __init__(self):
            self.central_plugin = central_plugin
            self.report_type = 'Investigative'
            self.current_case_id = None

        def new_case(self, info):
            self.current_case_id = self.central_plugin.bus.new_case(info)
            return self.current_case_id

        def get_case_summary(self, case_id):
            return self.central_plugin.get_case_summary(case_id)

        def store_file(self, info):
            return self.central_plugin.store_file(info)

        def register_files(self, files):
            try:
                self.central_plugin.bus.add_files(files)
            except Exception:
                pass

        def generate_narrative(self, processed, section_id):
            return self.central_plugin.generate_narrative(processed, section_id)

        def get_bus_events(self, limit=100):
            return self.central_plugin.bus.get_event_log(limit)

    root = tk.Tk()
    root.title('Evidence Panel Preview')
    panel = EvidencePanel(root, _Controller())
    panel.pack(fill='both', expand=True)
    root.mainloop()
