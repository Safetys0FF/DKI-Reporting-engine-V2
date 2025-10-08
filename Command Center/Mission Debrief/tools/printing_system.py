#!/usr/bin/env python3
"""
Printing System - Direct printer integration for DKI Engine reports
Handles print preview, printer selection, and professional printing output
"""

import os
import sys
import logging
import tempfile
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

from .report_generator_adapter import ReportGeneratorAdapter

# Platform-specific printing imports
try:
    if sys.platform == "win32":
        import win32print
        import win32ui
        import win32con
        from win32api import ShellExecute
        HAVE_WIN32_PRINT = True
    else:
        HAVE_WIN32_PRINT = False
except ImportError:
    HAVE_WIN32_PRINT = False

# Cross-platform printing fallback
try:
    import subprocess
    HAVE_SUBPROCESS = True
except ImportError:
    HAVE_SUBPROCESS = False

logger = logging.getLogger(__name__)

class PrintingSystem:
    """Professional printing system for DKI Engine reports"""
    
    def __init__(self):
        self.available_printers = []
        self.default_printer = None
        self.print_settings = {
            'paper_size': 'Letter',
            'orientation': 'Portrait',
            'margins': {'top': 0.5, 'bottom': 0.5, 'left': 0.5, 'right': 0.5},
            'quality': 'High',
            'color': True,
            'duplex': False,
            'copies': 1
        }
        try:
            self.report_adapter = ReportGeneratorAdapter()
        except Exception as exc:
            logger.error(f"Report generator adapter unavailable for printing: {exc}")
            self.report_adapter = None
        self.initialize_printers()
        logger.info("Printing system initialized")
    
    def initialize_printers(self):
        """Initialize available printers based on platform"""
        try:
            if HAVE_WIN32_PRINT:
                self._initialize_windows_printers()
            else:
                self._initialize_cross_platform_printers()
        except Exception as e:
            logger.error(f"Failed to initialize printers: {e}")
            self.available_printers = ["Default System Printer"]
            self.default_printer = "Default System Printer"
    
    def _initialize_windows_printers(self):
        """Initialize printers on Windows using win32print"""
        try:
            printers = []
            printer_info = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
            
            for printer in printer_info:
                printer_name = printer[2]  # Printer name is at index 2
                printers.append(printer_name)
                logger.debug(f"Found printer: {printer_name}")
            
            self.available_printers = printers
            
            # Get default printer
            try:
                self.default_printer = win32print.GetDefaultPrinter()
            except:
                self.default_printer = printers[0] if printers else "Default Printer"
                
            logger.info(f"Initialized {len(printers)} Windows printers, default: {self.default_printer}")
            
        except Exception as e:
            logger.error(f"Windows printer initialization failed: {e}")
            self.available_printers = ["Default System Printer"]
            self.default_printer = "Default System Printer"
    
    def _initialize_cross_platform_printers(self):
        """Initialize printers on Linux/Mac using system commands"""
        try:
            if sys.platform.startswith('linux'):
                # Linux - use lpstat
                result = subprocess.run(['lpstat', '-p'], capture_output=True, text=True)
                if result.returncode == 0:
                    printers = []
                    for line in result.stdout.split('\n'):
                        if line.startswith('printer '):
                            printer_name = line.split()[1]
                            printers.append(printer_name)
                    self.available_printers = printers
                    self.default_printer = printers[0] if printers else "Default Printer"
            
            elif sys.platform == 'darwin':
                # macOS - use lpstat
                result = subprocess.run(['lpstat', '-p'], capture_output=True, text=True)
                if result.returncode == 0:
                    printers = []
                    for line in result.stdout.split('\n'):
                        if line.startswith('printer '):
                            printer_name = line.split()[1]
                            printers.append(printer_name)
                    self.available_printers = printers
                    self.default_printer = printers[0] if printers else "Default Printer"
            
            if not self.available_printers:
                self.available_printers = ["Default System Printer"]
                self.default_printer = "Default System Printer"
                
            logger.info(f"Initialized {len(self.available_printers)} cross-platform printers")
            
        except Exception as e:
            logger.error(f"Cross-platform printer initialization failed: {e}")
            self.available_printers = ["Default System Printer"]
            self.default_printer = "Default System Printer"
    
    def show_print_dialog(self, parent, report_data: Dict[str, Any]) -> bool:
        """Show print settings dialog and handle printing"""
        
        dialog = PrintDialog(parent, self, report_data)
        parent.wait_window(dialog.dialog)
        
        return dialog.print_confirmed
    
    def print_report(self, report_data: Dict[str, Any], printer_name: str = None, 
                    settings: Dict[str, Any] = None) -> bool:
        """Print report with specified settings"""
        
        try:
            # Use provided settings or defaults
            print_settings = settings or self.print_settings.copy()
            target_printer = printer_name or self.default_printer
            
            logger.info(f"Printing report to {target_printer}")
            
            # Generate temporary PDF for printing
            temp_pdf = self._create_print_pdf(report_data, print_settings)
            
            if not temp_pdf:
                raise Exception("Failed to create print-ready PDF")
            
            # Platform-specific printing
            success = False
            if HAVE_WIN32_PRINT and sys.platform == "win32":
                success = self._print_windows(temp_pdf, target_printer, print_settings)
            else:
                success = self._print_cross_platform(temp_pdf, target_printer, print_settings)
            
            # Cleanup temporary file
            try:
                os.unlink(temp_pdf)
            except:
                pass
            
            if success:
                logger.info("Report printed successfully")
                return True
            else:
                raise Exception("Printing failed")
                
        except Exception as e:
            logger.error(f"Print operation failed: {e}")
            messagebox.showerror("Print Error", f"Failed to print report: {str(e)}")
            return False
    
    def _create_print_pdf(self, report_data: Dict[str, Any], settings: Dict[str, Any]) -> Optional[str]:
        """Create optimized PDF for printing"""
        
        try:
            adapter = self.report_adapter or ReportGeneratorAdapter()
            if not adapter.is_available():
                raise RuntimeError("Report generator adapter is not available for printing")
            temp_dir = Path(tempfile.gettempdir())
            temp_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_path = temp_dir / f"dki_print_{timestamp}.pdf"
            source_payload = report_data if isinstance(report_data, dict) else {}
            base_payload = source_payload if isinstance(source_payload, dict) else {}
            sections_candidate = base_payload.get('sections') if isinstance(base_payload, dict) else None
            if not sections_candidate:
                metadata = base_payload.get('metadata') if isinstance(base_payload, dict) else None
                report_type = metadata.get('report_type') if isinstance(metadata, dict) else ''
                section_input = base_payload.get('sections') if isinstance(base_payload, dict) else None
                if section_input is None:
                    section_input = base_payload if isinstance(base_payload, dict) else {}
                base_payload = adapter.generate(section_input or {}, report_type or 'Investigative')
            adapter.export(base_payload, str(temp_path), 'PDF')
            logger.debug(f"Created print PDF: {temp_path}")
            return str(temp_path)
            
        except Exception as e:
            logger.error(f"Failed to create print PDF: {e}")
            return None
    
    def _print_windows(self, pdf_path: str, printer_name: str, settings: Dict[str, Any]) -> bool:
        """Print PDF on Windows using win32 APIs"""
        
        try:
            # Use ShellExecute to print PDF
            result = ShellExecute(
                0,                    # Parent window handle
                "print",              # Verb
                pdf_path,            # File to print
                f'/d:"{printer_name}"',  # Printer parameter
                None,                 # Working directory
                0                     # Show command
            )
            
            # ShellExecute returns > 32 on success
            if result > 32:
                logger.debug(f"Windows print command successful: {result}")
                return True
            else:
                logger.error(f"Windows print command failed: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Windows printing failed: {e}")
            return False
    
    def _print_cross_platform(self, pdf_path: str, printer_name: str, settings: Dict[str, Any]) -> bool:
        """Print PDF on Linux/Mac using system commands"""
        
        try:
            if sys.platform.startswith('linux'):
                # Linux - use lp command
                cmd = ['lp', '-d', printer_name]
                
                # Add print settings
                if settings.get('copies', 1) > 1:
                    cmd.extend(['-n', str(settings['copies'])])
                
                if settings.get('duplex', False):
                    cmd.extend(['-o', 'sides=two-sided-long-edge'])
                
                cmd.append(pdf_path)
                
            elif sys.platform == 'darwin':
                # macOS - use lpr command
                cmd = ['lpr', '-P', printer_name]
                
                # Add print settings
                if settings.get('copies', 1) > 1:
                    cmd.extend(['-#', str(settings['copies'])])
                
                cmd.append(pdf_path)
            
            else:
                # Fallback - try to open with default application
                if sys.platform == 'win32':
                    os.startfile(pdf_path, "print")
                else:
                    subprocess.run(['xdg-open', pdf_path])
                return True
            
            # Execute print command
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.debug("Cross-platform print command successful")
                return True
            else:
                logger.error(f"Print command failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Cross-platform printing failed: {e}")
            return False
    
    def preview_print(self, parent, report_data: Dict[str, Any]):
        """Show print preview dialog"""
        
        preview_dialog = PrintPreviewDialog(parent, report_data, self.print_settings)
        parent.wait_window(preview_dialog.dialog)


class PrintDialog:
    """Print settings dialog"""
    
    def __init__(self, parent, printing_system: PrintingSystem, report_data: Dict[str, Any]):
        self.parent = parent
        self.printing_system = printing_system
        self.report_data = report_data
        self.print_confirmed = False
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Print Report")
        self.dialog.geometry("450x500")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (500 // 2)
        self.dialog.geometry(f"450x500+{x}+{y}")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup print dialog UI"""
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Printer selection
        printer_frame = ttk.LabelFrame(main_frame, text="Printer", padding="5")
        printer_frame.pack(fill='x', pady=(0, 10))
        
        self.printer_var = tk.StringVar(value=self.printing_system.default_printer)
        printer_combo = ttk.Combobox(
            printer_frame,
            textvariable=self.printer_var,
            values=self.printing_system.available_printers,
            state='readonly'
        )
        printer_combo.pack(fill='x')
        
        # Print settings
        settings_frame = ttk.LabelFrame(main_frame, text="Print Settings", padding="5")
        settings_frame.pack(fill='x', pady=(0, 10))
        
        # Paper size
        paper_frame = ttk.Frame(settings_frame)
        paper_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(paper_frame, text="Paper Size:").pack(side='left')
        self.paper_var = tk.StringVar(value="Letter")
        paper_combo = ttk.Combobox(
            paper_frame,
            textvariable=self.paper_var,
            values=["Letter", "A4", "Legal", "A3"],
            state='readonly',
            width=10
        )
        paper_combo.pack(side='right')
        
        # Orientation
        orient_frame = ttk.Frame(settings_frame)
        orient_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(orient_frame, text="Orientation:").pack(side='left')
        self.orientation_var = tk.StringVar(value="Portrait")
        orient_combo = ttk.Combobox(
            orient_frame,
            textvariable=self.orientation_var,
            values=["Portrait", "Landscape"],
            state='readonly',
            width=10
        )
        orient_combo.pack(side='right')
        
        # Quality
        quality_frame = ttk.Frame(settings_frame)
        quality_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(quality_frame, text="Quality:").pack(side='left')
        self.quality_var = tk.StringVar(value="High")
        quality_combo = ttk.Combobox(
            quality_frame,
            textvariable=self.quality_var,
            values=["Draft", "Normal", "High"],
            state='readonly',
            width=10
        )
        quality_combo.pack(side='right')
        
        # Copies
        copies_frame = ttk.Frame(settings_frame)
        copies_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(copies_frame, text="Copies:").pack(side='left')
        self.copies_var = tk.IntVar(value=1)
        copies_spin = ttk.Spinbox(
            copies_frame,
            from_=1,
            to=99,
            textvariable=self.copies_var,
            width=10
        )
        copies_spin.pack(side='right')
        
        # Options
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="5")
        options_frame.pack(fill='x', pady=(0, 10))
        
        self.color_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Color printing",
            variable=self.color_var
        ).pack(anchor='w')
        
        self.duplex_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            options_frame,
            text="Print on both sides (duplex)",
            variable=self.duplex_var
        ).pack(anchor='w')
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Button(
            button_frame,
            text="Preview",
            command=self.preview_report
        ).pack(side='left', padx=(0, 5))
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel_print
        ).pack(side='right')
        
        ttk.Button(
            button_frame,
            text="Print",
            command=self.confirm_print
        ).pack(side='right', padx=(0, 5))
    
    def preview_report(self):
        """Show print preview"""
        settings = self.get_print_settings()
        self.printing_system.preview_print(self.dialog, self.report_data)
    
    def get_print_settings(self) -> Dict[str, Any]:
        """Get current print settings from dialog"""
        return {
            'paper_size': self.paper_var.get(),
            'orientation': self.orientation_var.get(),
            'quality': self.quality_var.get(),
            'copies': self.copies_var.get(),
            'color': self.color_var.get(),
            'duplex': self.duplex_var.get(),
            'margins': {'top': 0.5, 'bottom': 0.5, 'left': 0.5, 'right': 0.5}
        }
    
    def confirm_print(self):
        """Confirm and execute print"""
        try:
            printer_name = self.printer_var.get()
            settings = self.get_print_settings()
            
            success = self.printing_system.print_report(
                self.report_data,
                printer_name,
                settings
            )
            
            if success:
                self.print_confirmed = True
                messagebox.showinfo("Print Success", "Report sent to printer successfully!")
                self.dialog.destroy()
            else:
                messagebox.showerror("Print Failed", "Failed to send report to printer.")
                
        except Exception as e:
            logger.error(f"Print confirmation failed: {e}")
            messagebox.showerror("Print Error", f"Print operation failed: {str(e)}")
    
    def cancel_print(self):
        """Cancel print operation"""
        self.print_confirmed = False
        self.dialog.destroy()


class PrintPreviewDialog:
    """Print preview dialog showing how the report will look when printed"""
    
    def __init__(self, parent, report_data: Dict[str, Any], print_settings: Dict[str, Any]):
        self.parent = parent
        self.report_data = report_data
        self.print_settings = print_settings
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Print Preview")
        self.dialog.geometry("800x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400)
        y = (self.dialog.winfo_screenheight() // 2) - (300)
        self.dialog.geometry(f"800x600+{x}+{y}")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup preview dialog UI"""
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Preview info
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill='x', pady=(0, 10))
        
        info_text = f"Print Preview - {self.print_settings.get('paper_size', 'Letter')} {self.print_settings.get('orientation', 'Portrait')}"
        ttk.Label(info_frame, text=info_text, font=('TkDefaultFont', 10, 'bold')).pack()
        
        # Preview area (simplified - would show actual PDF preview in full implementation)
        preview_frame = ttk.LabelFrame(main_frame, text="Preview", padding="5")
        preview_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Simplified preview text (in full implementation, would render PDF)
        preview_text = tk.Text(
            preview_frame,
            wrap='word',
            state='disabled',
            bg='white',
            font=('Times New Roman', 10)
        )
        preview_text.pack(fill='both', expand=True)
        
        # Add sample content
        self._populate_preview(preview_text)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x')
        
        ttk.Button(
            button_frame,
            text="Close",
            command=self.dialog.destroy
        ).pack(side='right')
    
    def _populate_preview(self, text_widget):
        """Populate preview with sample content"""
        
        text_widget.config(state='normal')
        
        # Sample preview content
        preview_content = f"""
DKI ENGINE INVESTIGATION REPORT
{'='*50}

Case Information:
- Case ID: {self.report_data.get('metadata', {}).get('case_id', 'CASE-001')}
- Report Type: {self.report_data.get('metadata', {}).get('report_type', 'Investigation')}
- Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

Print Settings:
- Paper Size: {self.print_settings.get('paper_size', 'Letter')}
- Orientation: {self.print_settings.get('orientation', 'Portrait')}
- Quality: {self.print_settings.get('quality', 'High')}
- Copies: {self.print_settings.get('copies', 1)}

This preview shows how your report will appear when printed.
The actual report will contain all sections, images, and 
professional formatting as generated by the DKI Engine.

Note: This is a simplified preview. The actual printed 
report will include full content, images, tables, and 
professional formatting.
        """
        
        text_widget.insert('1.0', preview_content.strip())
        text_widget.config(state='disabled')


# Test the printing system
if __name__ == "__main__":
    # Test printing system
    print("🖨️ Testing DKI Engine Printing System...")
    
    printing_system = PrintingSystem()
    
    print(f"Available Printers: {printing_system.available_printers}")
    print(f"Default Printer: {printing_system.default_printer}")
    
    # Test data
    test_report = {
        'metadata': {
            'case_id': 'TEST-001',
            'report_type': 'Investigation',
            'generated_date': datetime.now().isoformat()
        },
        'cover_page': {
            'content': 'TEST REPORT\n\nGenerated by DKI Engine\nPrinting System Test'
        },
        'sections': []
    }
    
    print("✅ Printing system initialized successfully!")








