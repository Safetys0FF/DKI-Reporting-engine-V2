#!/usr/bin/env python3
"""
Watermark System - Document watermarking and security features for DKI Engine
Handles draft watermarks, confidential stamps, and document security overlays
"""

import os
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import tempfile

# PDF and image processing libraries
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.lib.colors import Color, red, blue, gray, black
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.utils import ImageReader
    HAVE_REPORTLAB = True
except ImportError:
    HAVE_REPORTLAB = False

try:
    from PIL import Image, ImageDraw, ImageFont, ImageEnhance
    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False

try:
    import PyPDF2
    from PyPDF2 import PdfWriter, PdfReader
    HAVE_PYPDF2 = True
except ImportError:
    HAVE_PYPDF2 = False

logger = logging.getLogger(__name__)

class WatermarkSystem:
    """Professional watermarking system for DKI Engine documents"""
    
    def __init__(self, watermarks_dir: str = "watermarks"):
        self.watermarks_dir = Path(watermarks_dir)
        self.watermarks_dir.mkdir(exist_ok=True)
        
        # Predefined watermark templates
        self.watermark_templates = {
            'draft': {
                'text': 'DRAFT',
                'color': {'r': 1.0, 'g': 0.0, 'b': 0.0, 'alpha': 0.3},
                'font_size': 72,
                'rotation': 45,
                'position': 'center',
                'style': 'diagonal'
            },
            'confidential': {
                'text': 'CONFIDENTIAL',
                'color': {'r': 0.8, 'g': 0.0, 'b': 0.0, 'alpha': 0.4},
                'font_size': 48,
                'rotation': 0,
                'position': 'top',
                'style': 'header_footer'
            },
            'preliminary': {
                'text': 'PRELIMINARY REPORT',
                'color': {'r': 0.0, 'g': 0.0, 'b': 1.0, 'alpha': 0.25},
                'font_size': 36,
                'rotation': 30,
                'position': 'center',
                'style': 'diagonal'
            },
            'internal_use': {
                'text': 'INTERNAL USE ONLY',
                'color': {'r': 0.5, 'g': 0.5, 'b': 0.5, 'alpha': 0.3},
                'font_size': 24,
                'rotation': 0,
                'position': 'footer',
                'style': 'footer_only'
            },
            'copy': {
                'text': 'COPY',
                'color': {'r': 0.0, 'g': 0.5, 'b': 0.0, 'alpha': 0.2},
                'font_size': 60,
                'rotation': 45,
                'position': 'center',
                'style': 'diagonal'
            },
            'not_for_distribution': {
                'text': 'NOT FOR DISTRIBUTION',
                'color': {'r': 0.8, 'g': 0.4, 'b': 0.0, 'alpha': 0.35},
                'font_size': 32,
                'rotation': 0,
                'position': 'header',
                'style': 'header_only'
            }
        }
        
        # Custom watermark settings
        self.custom_watermarks = {}
        self.load_custom_watermarks()
        
        logger.info("Watermark system initialized")
    
    def load_custom_watermarks(self):
        """Load custom watermark configurations"""
        
        try:
            import json
            custom_file = self.watermarks_dir / 'custom_watermarks.json'
            if custom_file.exists():
                with open(custom_file, 'r') as f:
                    self.custom_watermarks = json.load(f)
                logger.debug(f"Loaded {len(self.custom_watermarks)} custom watermarks")
        except Exception as e:
            logger.error(f"Failed to load custom watermarks: {e}")
    
    def save_custom_watermarks(self):
        """Save custom watermark configurations"""
        
        try:
            import json
            custom_file = self.watermarks_dir / 'custom_watermarks.json'
            with open(custom_file, 'w') as f:
                json.dump(self.custom_watermarks, f, indent=2)
            logger.debug("Saved custom watermarks")
        except Exception as e:
            logger.error(f"Failed to save custom watermarks: {e}")
    
    def apply_watermark_to_pdf(self, input_path: str, output_path: str, 
                              watermark_type: str, custom_text: str = None,
                              custom_config: Dict[str, Any] = None) -> bool:
        """Apply watermark to PDF document"""
        
        try:
            if not HAVE_REPORTLAB or not HAVE_PYPDF2:
                logger.error("Required libraries not available for PDF watermarking")
                return False
            
            # Get watermark configuration
            if custom_config:
                config = custom_config
            elif watermark_type in self.watermark_templates:
                config = self.watermark_templates[watermark_type].copy()
            elif watermark_type in self.custom_watermarks:
                config = self.custom_watermarks[watermark_type].copy()
            else:
                logger.error(f"Unknown watermark type: {watermark_type}")
                return False
            
            # Override text if provided
            if custom_text:
                config['text'] = custom_text
            
            # Create watermark overlay
            overlay_path = self._create_watermark_overlay(config)
            if not overlay_path:
                return False
            
            # Apply watermark to PDF
            success = self._apply_overlay_to_pdf(input_path, output_path, overlay_path)
            
            # Cleanup temporary overlay
            try:
                os.unlink(overlay_path)
            except:
                pass
            
            if success:
                logger.info(f"Applied {watermark_type} watermark to {output_path}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to apply watermark: {e}")
            return False
    
    def _create_watermark_overlay(self, config: Dict[str, Any]) -> Optional[str]:
        """Create watermark overlay PDF"""
        
        try:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            temp_file.close()
            
            # Create canvas
            c = canvas.Canvas(temp_file.name, pagesize=letter)
            page_width, page_height = letter
            
            # Set up watermark properties
            text = config['text']
            font_size = config.get('font_size', 48)
            rotation = config.get('rotation', 0)
            position = config.get('position', 'center')
            style = config.get('style', 'diagonal')
            
            # Set color with transparency
            color_config = config.get('color', {'r': 0.5, 'g': 0.5, 'b': 0.5, 'alpha': 0.3})
            color = Color(
                color_config['r'],
                color_config['g'],
                color_config['b'],
                alpha=color_config['alpha']
            )
            
            # Apply watermark based on style
            if style == 'diagonal':
                self._add_diagonal_watermark(c, text, font_size, rotation, color, page_width, page_height)
            elif style == 'header_footer':
                self._add_header_footer_watermark(c, text, font_size, color, page_width, page_height)
            elif style == 'header_only':
                self._add_header_watermark(c, text, font_size, color, page_width, page_height)
            elif style == 'footer_only':
                self._add_footer_watermark(c, text, font_size, color, page_width, page_height)
            elif style == 'corner':
                self._add_corner_watermark(c, text, font_size, color, page_width, page_height, position)
            else:
                # Default to center
                self._add_center_watermark(c, text, font_size, rotation, color, page_width, page_height)
            
            c.save()
            
            logger.debug(f"Created watermark overlay: {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Failed to create watermark overlay: {e}")
            return None
    
    def _add_diagonal_watermark(self, canvas_obj, text: str, font_size: int, 
                               rotation: float, color, page_width: float, page_height: float):
        """Add diagonal watermark across the page"""
        
        canvas_obj.saveState()
        
        # Set color and transparency
        canvas_obj.setFillColor(color)
        
        # Set font
        canvas_obj.setFont("Helvetica-Bold", font_size)
        
        # Calculate position (center of page)
        x = page_width / 2
        y = page_height / 2
        
        # Apply rotation and draw text
        canvas_obj.translate(x, y)
        canvas_obj.rotate(rotation)
        
        # Center the text
        text_width = canvas_obj.stringWidth(text, "Helvetica-Bold", font_size)
        canvas_obj.drawString(-text_width / 2, -font_size / 2, text)
        
        canvas_obj.restoreState()
    
    def _add_header_footer_watermark(self, canvas_obj, text: str, font_size: int,
                                    color, page_width: float, page_height: float):
        """Add watermark to header and footer"""
        
        canvas_obj.setFillColor(color)
        canvas_obj.setFont("Helvetica-Bold", font_size)
        
        text_width = canvas_obj.stringWidth(text, "Helvetica-Bold", font_size)
        
        # Header
        x = (page_width - text_width) / 2
        y = page_height - font_size - 20
        canvas_obj.drawString(x, y, text)
        
        # Footer
        y = 20
        canvas_obj.drawString(x, y, text)
    
    def _add_header_watermark(self, canvas_obj, text: str, font_size: int,
                             color, page_width: float, page_height: float):
        """Add watermark to header only"""
        
        canvas_obj.setFillColor(color)
        canvas_obj.setFont("Helvetica-Bold", font_size)
        
        text_width = canvas_obj.stringWidth(text, "Helvetica-Bold", font_size)
        x = (page_width - text_width) / 2
        y = page_height - font_size - 20
        
        canvas_obj.drawString(x, y, text)
    
    def _add_footer_watermark(self, canvas_obj, text: str, font_size: int,
                             color, page_width: float, page_height: float):
        """Add watermark to footer only"""
        
        canvas_obj.setFillColor(color)
        canvas_obj.setFont("Helvetica-Bold", font_size)
        
        text_width = canvas_obj.stringWidth(text, "Helvetica-Bold", font_size)
        x = (page_width - text_width) / 2
        y = 20
        
        canvas_obj.drawString(x, y, text)
    
    def _add_corner_watermark(self, canvas_obj, text: str, font_size: int,
                             color, page_width: float, page_height: float, position: str):
        """Add watermark to corner"""
        
        canvas_obj.setFillColor(color)
        canvas_obj.setFont("Helvetica-Bold", font_size)
        
        text_width = canvas_obj.stringWidth(text, "Helvetica-Bold", font_size)
        
        if position == 'top_left':
            x, y = 20, page_height - font_size - 20
        elif position == 'top_right':
            x, y = page_width - text_width - 20, page_height - font_size - 20
        elif position == 'bottom_left':
            x, y = 20, 20
        elif position == 'bottom_right':
            x, y = page_width - text_width - 20, 20
        else:
            # Default to top_right
            x, y = page_width - text_width - 20, page_height - font_size - 20
        
        canvas_obj.drawString(x, y, text)
    
    def _add_center_watermark(self, canvas_obj, text: str, font_size: int,
                             rotation: float, color, page_width: float, page_height: float):
        """Add centered watermark"""
        
        canvas_obj.saveState()
        
        canvas_obj.setFillColor(color)
        canvas_obj.setFont("Helvetica-Bold", font_size)
        
        # Center position
        x = page_width / 2
        y = page_height / 2
        
        canvas_obj.translate(x, y)
        if rotation:
            canvas_obj.rotate(rotation)
        
        text_width = canvas_obj.stringWidth(text, "Helvetica-Bold", font_size)
        canvas_obj.drawString(-text_width / 2, -font_size / 2, text)
        
        canvas_obj.restoreState()
    
    def _apply_overlay_to_pdf(self, input_path: str, output_path: str, overlay_path: str) -> bool:
        """Apply watermark overlay to PDF"""
        
        try:
            # Read original PDF
            with open(input_path, 'rb') as input_file:
                reader = PdfReader(input_file)
                writer = PdfWriter()
                
                # Read overlay
                with open(overlay_path, 'rb') as overlay_file:
                    overlay_reader = PdfReader(overlay_file)
                    overlay_page = overlay_reader.pages[0]
                    
                    # Apply overlay to each page
                    for page in reader.pages:
                        # Merge overlay with page
                        page.merge_page(overlay_page)
                        writer.add_page(page)
                    
                    # Write result
                    with open(output_path, 'wb') as output_file:
                        writer.write(output_file)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply overlay to PDF: {e}")
            return False
    
    def create_custom_watermark(self, name: str, config: Dict[str, Any]):
        """Create custom watermark configuration"""
        
        self.custom_watermarks[name] = config
        self.save_custom_watermarks()
        logger.info(f"Created custom watermark: {name}")
    
    def get_available_watermarks(self) -> List[str]:
        """Get list of available watermark types"""
        
        watermarks = list(self.watermark_templates.keys())
        watermarks.extend(self.custom_watermarks.keys())
        return watermarks
    
    def get_watermark_config(self, watermark_type: str) -> Optional[Dict[str, Any]]:
        """Get watermark configuration"""
        
        if watermark_type in self.watermark_templates:
            return self.watermark_templates[watermark_type].copy()
        elif watermark_type in self.custom_watermarks:
            return self.custom_watermarks[watermark_type].copy()
        else:
            return None
    
    def show_watermark_dialog(self, parent, pdf_path: str) -> bool:
        """Show watermark application dialog"""
        
        dialog = WatermarkDialog(parent, self, pdf_path)
        parent.wait_window(dialog.dialog)
        
        return dialog.watermark_applied
    
    def remove_watermarks_from_pdf(self, input_path: str, output_path: str) -> bool:
        """Attempt to remove watermarks from PDF (limited functionality)"""
        
        try:
            # This is a simplified version - full watermark removal is complex
            # and depends on how the watermark was applied
            
            with open(input_path, 'rb') as input_file:
                reader = PdfReader(input_file)
                writer = PdfWriter()
                
                # Copy pages without modifications
                # In a full implementation, this would analyze and remove overlay content
                for page in reader.pages:
                    writer.add_page(page)
                
                with open(output_path, 'wb') as output_file:
                    writer.write(output_file)
            
            logger.info(f"Processed PDF (watermark removal attempted): {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to process PDF for watermark removal: {e}")
            return False


class WatermarkDialog:
    """Watermark application dialog"""
    
    def __init__(self, parent, watermark_system: WatermarkSystem, pdf_path: str):
        self.parent = parent
        self.watermark_system = watermark_system
        self.pdf_path = pdf_path
        self.watermark_applied = False
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Apply Watermark")
        self.dialog.geometry("500x600")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (250)
        y = (self.dialog.winfo_screenheight() // 2) - (300)
        self.dialog.geometry(f"500x600+{x}+{y}")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup watermark dialog UI"""
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Watermark selection
        select_frame = ttk.LabelFrame(main_frame, text="Select Watermark Type", padding="10")
        select_frame.pack(fill='x', pady=(0, 10))
        
        watermarks = self.watermark_system.get_available_watermarks()
        
        self.watermark_var = tk.StringVar(value=watermarks[0] if watermarks else "")
        
        for watermark in watermarks:
            ttk.Radiobutton(
                select_frame,
                text=watermark.replace('_', ' ').title(),
                variable=self.watermark_var,
                value=watermark,
                command=self.on_watermark_changed
            ).pack(anchor='w', pady=2)
        
        # Custom text
        text_frame = ttk.LabelFrame(main_frame, text="Custom Text (Optional)", padding="10")
        text_frame.pack(fill='x', pady=(0, 10))
        
        self.custom_text_var = tk.StringVar()
        ttk.Entry(text_frame, textvariable=self.custom_text_var, width=50).pack(fill='x')
        
        ttk.Label(
            text_frame,
            text="Leave blank to use default text for selected watermark type",
            font=('TkDefaultFont', 8),
            foreground='gray'
        ).pack(anchor='w', pady=(5, 0))
        
        # Preview frame
        preview_frame = ttk.LabelFrame(main_frame, text="Watermark Preview", padding="10")
        preview_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        self.preview_text = tk.Text(
            preview_frame,
            height=12,
            wrap='word',
            state='disabled',
            font=('Consolas', 9)
        )
        
        preview_scroll = ttk.Scrollbar(preview_frame, orient='vertical', command=self.preview_text.yview)
        self.preview_text.configure(yscrollcommand=preview_scroll.set)
        
        self.preview_text.pack(side='left', fill='both', expand=True)
        preview_scroll.pack(side='right', fill='y')
        
        # Custom watermark button
        custom_frame = ttk.Frame(main_frame)
        custom_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Button(
            custom_frame,
            text="Create Custom Watermark",
            command=self.create_custom_watermark
        ).pack(side='left')
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x')
        
        ttk.Button(
            button_frame,
            text="Preview",
            command=self.preview_watermark
        ).pack(side='left')
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel_watermark
        ).pack(side='right')
        
        ttk.Button(
            button_frame,
            text="Apply Watermark",
            command=self.apply_watermark
        ).pack(side='right', padx=(0, 5))
        
        # Initialize preview
        self.update_preview()
    
    def on_watermark_changed(self):
        """Handle watermark type change"""
        self.update_preview()
    
    def update_preview(self):
        """Update watermark preview"""
        
        watermark_type = self.watermark_var.get()
        if not watermark_type:
            return
        
        config = self.watermark_system.get_watermark_config(watermark_type)
        if not config:
            return
        
        # Display configuration
        preview_content = f"Watermark Type: {watermark_type.replace('_', ' ').title()}\n\n"
        preview_content += f"Text: {config.get('text', 'N/A')}\n"
        preview_content += f"Font Size: {config.get('font_size', 'N/A')}pt\n"
        preview_content += f"Rotation: {config.get('rotation', 'N/A')}°\n"
        preview_content += f"Position: {config.get('position', 'N/A')}\n"
        preview_content += f"Style: {config.get('style', 'N/A')}\n"
        
        color_config = config.get('color', {})
        preview_content += f"\nColor:\n"
        preview_content += f"  Red: {color_config.get('r', 0.0):.2f}\n"
        preview_content += f"  Green: {color_config.get('g', 0.0):.2f}\n"
        preview_content += f"  Blue: {color_config.get('b', 0.0):.2f}\n"
        preview_content += f"  Transparency: {color_config.get('alpha', 1.0):.2f}\n"
        
        preview_content += f"\nDescription:\n"
        if watermark_type == 'draft':
            preview_content += "Large red 'DRAFT' text diagonally across each page"
        elif watermark_type == 'confidential':
            preview_content += "Red 'CONFIDENTIAL' text at top and bottom of each page"
        elif watermark_type == 'preliminary':
            preview_content += "Blue 'PRELIMINARY REPORT' text diagonally across each page"
        elif watermark_type == 'internal_use':
            preview_content += "Gray 'INTERNAL USE ONLY' text at bottom of each page"
        elif watermark_type == 'copy':
            preview_content += "Green 'COPY' text diagonally across each page"
        elif watermark_type == 'not_for_distribution':
            preview_content += "Orange 'NOT FOR DISTRIBUTION' text at top of each page"
        else:
            preview_content += "Custom watermark configuration"
        
        # Update preview
        self.preview_text.config(state='normal')
        self.preview_text.delete('1.0', 'end')
        self.preview_text.insert('1.0', preview_content)
        self.preview_text.config(state='disabled')
    
    def create_custom_watermark(self):
        """Show custom watermark creation dialog"""
        
        custom_dialog = CustomWatermarkDialog(self.dialog, self.watermark_system)
        self.dialog.wait_window(custom_dialog.dialog)
        
        if custom_dialog.watermark_created:
            # Refresh watermark list
            self.dialog.destroy()
            self.__init__(self.parent, self.watermark_system, self.pdf_path)
    
    def preview_watermark(self):
        """Preview watermark effect"""
        
        # This would show a preview of the watermarked document
        # For now, show configuration info
        watermark_type = self.watermark_var.get()
        custom_text = self.custom_text_var.get().strip()
        
        message = f"Watermark Preview:\n\n"
        message += f"Type: {watermark_type.replace('_', ' ').title()}\n"
        if custom_text:
            message += f"Custom Text: {custom_text}\n"
        message += f"\nThis watermark will be applied to all pages of the PDF document.\n\n"
        message += "Full visual preview coming in future update."
        
        messagebox.showinfo("Watermark Preview", message)
    
    def apply_watermark(self):
        """Apply watermark to PDF"""
        
        try:
            watermark_type = self.watermark_var.get()
            custom_text = self.custom_text_var.get().strip() or None
            
            if not watermark_type:
                messagebox.showerror("Error", "Please select a watermark type")
                return
            
            # Choose output location
            output_path = filedialog.asksaveasfilename(
                title="Save Watermarked PDF",
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")]
            )
            
            if not output_path:
                return
            
            # Apply watermark
            success = self.watermark_system.apply_watermark_to_pdf(
                self.pdf_path,
                output_path,
                watermark_type,
                custom_text
            )
            
            if success:
                self.watermark_applied = True
                messagebox.showinfo("Success", f"Watermark applied successfully!\nSaved as: {output_path}")
                self.dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to apply watermark")
                
        except Exception as e:
            logger.error(f"Failed to apply watermark: {e}")
            messagebox.showerror("Error", f"Watermark application failed: {str(e)}")
    
    def cancel_watermark(self):
        """Cancel watermark operation"""
        self.watermark_applied = False
        self.dialog.destroy()


class CustomWatermarkDialog:
    """Custom watermark creation dialog"""
    
    def __init__(self, parent, watermark_system: WatermarkSystem):
        self.parent = parent
        self.watermark_system = watermark_system
        self.watermark_created = False
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Create Custom Watermark")
        self.dialog.geometry("450x500")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (225)
        y = (self.dialog.winfo_screenheight() // 2) - (250)
        self.dialog.geometry(f"450x500+{x}+{y}")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup custom watermark creation UI"""
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Basic settings
        basic_frame = ttk.LabelFrame(main_frame, text="Basic Settings", padding="10")
        basic_frame.pack(fill='x', pady=(0, 10))
        
        # Name
        ttk.Label(basic_frame, text="Watermark Name:").grid(row=0, column=0, sticky='w', pady=2)
        self.name_var = tk.StringVar()
        ttk.Entry(basic_frame, textvariable=self.name_var, width=30).grid(row=0, column=1, sticky='ew', pady=2)
        
        # Text
        ttk.Label(basic_frame, text="Watermark Text:").grid(row=1, column=0, sticky='w', pady=2)
        self.text_var = tk.StringVar()
        ttk.Entry(basic_frame, textvariable=self.text_var, width=30).grid(row=1, column=1, sticky='ew', pady=2)
        
        basic_frame.columnconfigure(1, weight=1)
        
        # Appearance settings
        appearance_frame = ttk.LabelFrame(main_frame, text="Appearance", padding="10")
        appearance_frame.pack(fill='x', pady=(0, 10))
        
        # Font size
        ttk.Label(appearance_frame, text="Font Size:").grid(row=0, column=0, sticky='w', pady=2)
        self.font_size_var = tk.IntVar(value=48)
        ttk.Spinbox(
            appearance_frame,
            from_=12,
            to=144,
            textvariable=self.font_size_var,
            width=10
        ).grid(row=0, column=1, sticky='w', pady=2)
        
        # Rotation
        ttk.Label(appearance_frame, text="Rotation (degrees):").grid(row=1, column=0, sticky='w', pady=2)
        self.rotation_var = tk.IntVar(value=45)
        ttk.Spinbox(
            appearance_frame,
            from_=-180,
            to=180,
            textvariable=self.rotation_var,
            width=10
        ).grid(row=1, column=1, sticky='w', pady=2)
        
        # Transparency
        ttk.Label(appearance_frame, text="Transparency:").grid(row=2, column=0, sticky='w', pady=2)
        self.transparency_var = tk.DoubleVar(value=0.3)
        ttk.Scale(
            appearance_frame,
            from_=0.1,
            to=1.0,
            variable=self.transparency_var,
            orient='horizontal',
            length=150
        ).grid(row=2, column=1, sticky='ew', pady=2)
        
        # Color
        color_frame = ttk.Frame(appearance_frame)
        color_frame.grid(row=3, column=0, columnspan=2, sticky='ew', pady=5)
        
        ttk.Label(color_frame, text="Color:").pack(side='left')
        self.color_var = tk.StringVar(value="#FF0000")  # Red
        self.color_button = tk.Button(
            color_frame,
            text="Choose Color",
            bg=self.color_var.get(),
            command=self.choose_color,
            width=15
        )
        self.color_button.pack(side='right')
        
        appearance_frame.columnconfigure(1, weight=1)
        
        # Position settings
        position_frame = ttk.LabelFrame(main_frame, text="Position & Style", padding="10")
        position_frame.pack(fill='x', pady=(0, 10))
        
        # Style
        ttk.Label(position_frame, text="Style:").grid(row=0, column=0, sticky='w', pady=2)
        self.style_var = tk.StringVar(value="diagonal")
        style_combo = ttk.Combobox(
            position_frame,
            textvariable=self.style_var,
            values=["diagonal", "header_footer", "header_only", "footer_only", "corner"],
            state='readonly'
        )
        style_combo.grid(row=0, column=1, sticky='ew', pady=2)
        
        # Position
        ttk.Label(position_frame, text="Position:").grid(row=1, column=0, sticky='w', pady=2)
        self.position_var = tk.StringVar(value="center")
        position_combo = ttk.Combobox(
            position_frame,
            textvariable=self.position_var,
            values=["center", "top", "bottom", "header", "footer", "top_left", "top_right", "bottom_left", "bottom_right"],
            state='readonly'
        )
        position_combo.grid(row=1, column=1, sticky='ew', pady=2)
        
        position_frame.columnconfigure(1, weight=1)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel_creation
        ).pack(side='right')
        
        ttk.Button(
            button_frame,
            text="Create Watermark",
            command=self.create_watermark
        ).pack(side='right', padx=(0, 5))
    
    def choose_color(self):
        """Choose watermark color"""
        
        color = colorchooser.askcolor(
            title="Choose Watermark Color",
            initialcolor=self.color_var.get()
        )
        
        if color[1]:  # color[1] is the hex value
            self.color_var.set(color[1])
            self.color_button.config(bg=color[1])
    
    def create_watermark(self):
        """Create the custom watermark"""
        
        try:
            name = self.name_var.get().strip()
            text = self.text_var.get().strip()
            
            # Validate inputs
            if not name:
                messagebox.showerror("Error", "Watermark name is required")
                return
            
            if not text:
                messagebox.showerror("Error", "Watermark text is required")
                return
            
            # Convert hex color to RGB
            hex_color = self.color_var.get()
            rgb = tuple(int(hex_color[i:i+2], 16)/255.0 for i in (1, 3, 5))
            
            # Create configuration
            config = {
                'text': text,
                'color': {
                    'r': rgb[0],
                    'g': rgb[1], 
                    'b': rgb[2],
                    'alpha': self.transparency_var.get()
                },
                'font_size': self.font_size_var.get(),
                'rotation': self.rotation_var.get(),
                'position': self.position_var.get(),
                'style': self.style_var.get()
            }
            
            # Save custom watermark
            self.watermark_system.create_custom_watermark(name, config)
            
            self.watermark_created = True
            messagebox.showinfo("Success", f"Custom watermark '{name}' created successfully!")
            self.dialog.destroy()
            
        except Exception as e:
            logger.error(f"Failed to create custom watermark: {e}")
            messagebox.showerror("Error", f"Failed to create watermark: {str(e)}")
    
    def cancel_creation(self):
        """Cancel watermark creation"""
        self.watermark_created = False
        self.dialog.destroy()


# Test the watermark system
if __name__ == "__main__":
    print("🔒 Testing DKI Engine Watermark System...")
    
    watermark_system = WatermarkSystem()
    
    print(f"Available Watermarks: {watermark_system.get_available_watermarks()}")
    print(f"Watermark Templates: {list(watermark_system.watermark_templates.keys())}")
    
    if HAVE_REPORTLAB and HAVE_PYPDF2:
        print("✅ PDF watermarking available")
    else:
        print("⚠️  PDF watermarking requires reportlab and PyPDF2")
    
    print("✅ Watermark system initialized successfully!")








