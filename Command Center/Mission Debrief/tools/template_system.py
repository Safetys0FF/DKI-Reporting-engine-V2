#!/usr/bin/env python3
"""
Template System - Custom templates and color schemes for DKI Engine reports
Handles professional branding, custom layouts, and visual styling
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser

logger = logging.getLogger(__name__)

class TemplateSystem:
    """Professional template and styling system for DKI Engine"""
    
    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(exist_ok=True)
        
        # Built-in color schemes
        self.color_schemes = {
            'Professional Blue': {
                'primary': '#1B365D',      # Dark blue
                'secondary': '#B7C6A5',    # Light green (current)
                'accent': '#4A90A4',       # Medium blue
                'text': '#2C2C2C',         # Dark gray
                'background': '#FFFFFF',    # White
                'header_bg': '#B7C6A5',    # Light green
                'footer_bg': '#F8F9FA'     # Light gray
            },
            'Corporate Gray': {
                'primary': '#2C3E50',      # Dark blue-gray
                'secondary': '#95A5A6',    # Medium gray
                'accent': '#3498DB',       # Blue accent
                'text': '#2C2C2C',         # Dark gray
                'background': '#FFFFFF',    # White
                'header_bg': '#ECF0F1',    # Light gray
                'footer_bg': '#F8F9FA'     # Very light gray
            },
            'Legal Green': {
                'primary': '#27AE60',      # Green
                'secondary': '#E8F5E8',    # Very light green
                'accent': '#2ECC71',       # Light green
                'text': '#2C2C2C',         # Dark gray
                'background': '#FFFFFF',    # White
                'header_bg': '#E8F5E8',    # Very light green
                'footer_bg': '#F8F9FA'     # Light gray
            },
            'Executive Black': {
                'primary': '#1C1C1C',      # Almost black
                'secondary': '#4A4A4A',    # Dark gray
                'accent': '#D4AF37',       # Gold
                'text': '#2C2C2C',         # Dark gray
                'background': '#FFFFFF',    # White
                'header_bg': '#F5F5F5',    # Light gray
                'footer_bg': '#F0F0F0'     # Light gray
            },
            'Modern Purple': {
                'primary': '#6B46C1',      # Purple
                'secondary': '#E0E7FF',    # Light purple
                'accent': '#8B5CF6',       # Medium purple
                'text': '#2C2C2C',         # Dark gray
                'background': '#FFFFFF',    # White
                'header_bg': '#E0E7FF',    # Light purple
                'footer_bg': '#F8F9FA'     # Light gray
            }
        }
        
        # Built-in templates
        self.built_in_templates = {
            'Standard Investigation': self._create_standard_template(),
            'Executive Summary': self._create_executive_template(),
            'Detailed Technical': self._create_technical_template(),
            'Court Presentation': self._create_court_template(),
            'Client Friendly': self._create_client_template()
        }
        
        # Current template settings
        self.current_template = 'Standard Investigation'
        self.current_color_scheme = 'Professional Blue'
        self.custom_branding = {
            'company_name': '',
            'logo_path': '',
            'footer_text': '',
            'contact_info': '',
            'license_number': '',
            'watermark_text': ''
        }
        
        self.load_user_templates()
        logger.info("Template system initialized")
    
    def _create_standard_template(self) -> Dict[str, Any]:
        """Create standard investigation template"""
        return {
            'name': 'Standard Investigation',
            'description': 'Professional investigation report template',
            'fonts': {
                'title': {'family': 'Times New Roman', 'size': 18, 'bold': True},
                'heading': {'family': 'Times New Roman', 'size': 14, 'bold': True},
                'body': {'family': 'Times New Roman', 'size': 12, 'bold': False},
                'caption': {'family': 'Times New Roman', 'size': 10, 'italic': True}
            },
            'spacing': {
                'line_spacing': 1.15,
                'paragraph_spacing': 6,
                'section_spacing': 12,
                'page_margins': {'top': 1.0, 'bottom': 1.0, 'left': 1.0, 'right': 1.0}
            },
            'layout': {
                'header_height': 0.75,
                'footer_height': 0.5,
                'image_width': 3.25,
                'table_style': 'professional',
                'page_numbering': True,
                'watermark': False
            },
            'sections': {
                'cover_page': True,
                'table_of_contents': True,
                'executive_summary': False,
                'detailed_sections': True,
                'appendices': True,
                'disclosure_page': True
            }
        }
    
    def _create_executive_template(self) -> Dict[str, Any]:
        """Create executive summary template"""
        template = self._create_standard_template().copy()
        template.update({
            'name': 'Executive Summary',
            'description': 'Concise executive-level report template',
            'fonts': {
                'title': {'family': 'Arial', 'size': 16, 'bold': True},
                'heading': {'family': 'Arial', 'size': 12, 'bold': True},
                'body': {'family': 'Arial', 'size': 11, 'bold': False},
                'caption': {'family': 'Arial', 'size': 9, 'italic': True}
            },
            'sections': {
                'cover_page': True,
                'table_of_contents': False,
                'executive_summary': True,
                'detailed_sections': False,
                'appendices': False,
                'disclosure_page': True
            }
        })
        return template
    
    def _create_technical_template(self) -> Dict[str, Any]:
        """Create detailed technical template"""
        template = self._create_standard_template().copy()
        template.update({
            'name': 'Detailed Technical',
            'description': 'Comprehensive technical analysis template',
            'spacing': {
                'line_spacing': 1.0,
                'paragraph_spacing': 4,
                'section_spacing': 8,
                'page_margins': {'top': 0.75, 'bottom': 0.75, 'left': 0.75, 'right': 0.75}
            },
            'layout': {
                'header_height': 0.5,
                'footer_height': 0.5,
                'image_width': 4.0,
                'table_style': 'detailed',
                'page_numbering': True,
                'watermark': False
            }
        })
        return template
    
    def _create_court_template(self) -> Dict[str, Any]:
        """Create court presentation template"""
        template = self._create_standard_template().copy()
        template.update({
            'name': 'Court Presentation',
            'description': 'Formal court document template',
            'fonts': {
                'title': {'family': 'Times New Roman', 'size': 16, 'bold': True},
                'heading': {'family': 'Times New Roman', 'size': 13, 'bold': True},
                'body': {'family': 'Times New Roman', 'size': 12, 'bold': False},
                'caption': {'family': 'Times New Roman', 'size': 10, 'italic': False}
            },
            'spacing': {
                'line_spacing': 2.0,  # Double spacing for court documents
                'paragraph_spacing': 12,
                'section_spacing': 18,
                'page_margins': {'top': 1.5, 'bottom': 1.0, 'left': 1.5, 'right': 1.0}
            },
            'layout': {
                'page_numbering': True,
                'watermark': True,
                'formal_headers': True
            }
        })
        return template
    
    def _create_client_template(self) -> Dict[str, Any]:
        """Create client-friendly template"""
        template = self._create_standard_template().copy()
        template.update({
            'name': 'Client Friendly',
            'description': 'Easy-to-read client presentation template',
            'fonts': {
                'title': {'family': 'Calibri', 'size': 18, 'bold': True},
                'heading': {'family': 'Calibri', 'size': 14, 'bold': True},
                'body': {'family': 'Calibri', 'size': 12, 'bold': False},
                'caption': {'family': 'Calibri', 'size': 10, 'italic': True}
            },
            'spacing': {
                'line_spacing': 1.25,
                'paragraph_spacing': 8,
                'section_spacing': 16,
                'page_margins': {'top': 1.0, 'bottom': 1.0, 'left': 1.0, 'right': 1.0}
            },
            'layout': {
                'image_width': 3.5,
                'friendly_formatting': True,
                'summary_boxes': True
            }
        })
        return template
    
    def get_available_templates(self) -> List[str]:
        """Get list of available templates"""
        templates = list(self.built_in_templates.keys())
        
        # Add user templates
        user_templates_file = self.templates_dir / 'user_templates.json'
        if user_templates_file.exists():
            try:
                with open(user_templates_file, 'r') as f:
                    user_templates = json.load(f)
                templates.extend(user_templates.keys())
            except Exception as e:
                logger.error(f"Failed to load user templates: {e}")
        
        return templates
    
    def get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get template configuration by name"""
        
        # Check built-in templates first
        if template_name in self.built_in_templates:
            return self.built_in_templates[template_name].copy()
        
        # Check user templates
        user_templates_file = self.templates_dir / 'user_templates.json'
        if user_templates_file.exists():
            try:
                with open(user_templates_file, 'r') as f:
                    user_templates = json.load(f)
                if template_name in user_templates:
                    return user_templates[template_name].copy()
            except Exception as e:
                logger.error(f"Failed to load user template {template_name}: {e}")
        
        return None
    
    def save_custom_template(self, template_name: str, template_config: Dict[str, Any]):
        """Save custom template configuration"""
        
        user_templates_file = self.templates_dir / 'user_templates.json'
        
        # Load existing user templates
        user_templates = {}
        if user_templates_file.exists():
            try:
                with open(user_templates_file, 'r') as f:
                    user_templates = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load existing user templates: {e}")
        
        # Add new template
        user_templates[template_name] = template_config
        
        # Save updated templates
        try:
            with open(user_templates_file, 'w') as f:
                json.dump(user_templates, f, indent=2)
            logger.info(f"Saved custom template: {template_name}")
        except Exception as e:
            logger.error(f"Failed to save custom template {template_name}: {e}")
            raise
    
    def load_user_templates(self):
        """Load user-defined templates and settings"""
        
        # Load branding settings
        branding_file = self.templates_dir / 'branding.json'
        if branding_file.exists():
            try:
                with open(branding_file, 'r') as f:
                    self.custom_branding.update(json.load(f))
                logger.debug("Loaded custom branding settings")
            except Exception as e:
                logger.error(f"Failed to load branding settings: {e}")
        
        # Load current template settings
        settings_file = self.templates_dir / 'template_settings.json'
        if settings_file.exists():
            try:
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                self.current_template = settings.get('current_template', self.current_template)
                self.current_color_scheme = settings.get('current_color_scheme', self.current_color_scheme)
                logger.debug(f"Loaded template settings: {self.current_template}, {self.current_color_scheme}")
            except Exception as e:
                logger.error(f"Failed to load template settings: {e}")
    
    def save_current_settings(self):
        """Save current template and color scheme settings"""
        
        settings = {
            'current_template': self.current_template,
            'current_color_scheme': self.current_color_scheme,
            'last_updated': datetime.now().isoformat()
        }
        
        settings_file = self.templates_dir / 'template_settings.json'
        try:
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            logger.debug("Saved current template settings")
        except Exception as e:
            logger.error(f"Failed to save template settings: {e}")
    
    def save_branding_settings(self):
        """Save custom branding settings"""
        
        branding_file = self.templates_dir / 'branding.json'
        try:
            with open(branding_file, 'w') as f:
                json.dump(self.custom_branding, f, indent=2)
            logger.debug("Saved branding settings")
        except Exception as e:
            logger.error(f"Failed to save branding settings: {e}")
    
    def apply_template_to_report(self, report_data: Dict[str, Any], 
                               template_name: str = None, 
                               color_scheme: str = None) -> Dict[str, Any]:
        """Apply template and color scheme to report data"""
        
        template_name = template_name or self.current_template
        color_scheme = color_scheme or self.current_color_scheme
        
        # Get template configuration
        template_config = self.get_template(template_name)
        if not template_config:
            logger.warning(f"Template not found: {template_name}, using default")
            template_config = self.built_in_templates['Standard Investigation']
        
        # Get color scheme
        colors = self.color_schemes.get(color_scheme, self.color_schemes['Professional Blue'])
        
        # Apply template and styling to report data
        styled_report = report_data.copy()
        
        # Add template metadata
        styled_report['template'] = {
            'name': template_name,
            'color_scheme': color_scheme,
            'config': template_config,
            'colors': colors,
            'branding': self.custom_branding.copy()
        }
        
        # Apply styling to existing sections
        if 'sections' in styled_report:
            for section_id, section_data in styled_report['sections'].items():
                if isinstance(section_data, dict) and 'content' in section_data:
                    section_data['template_config'] = template_config
                    section_data['color_scheme'] = colors
        
        logger.info(f"Applied template '{template_name}' with '{color_scheme}' color scheme")
        return styled_report
    
    def show_template_editor(self, parent) -> bool:
        """Show template customization dialog"""
        
        editor = TemplateEditor(parent, self)
        parent.wait_window(editor.dialog)
        
        return editor.settings_changed


class TemplateEditor:
    """Template and color scheme editor dialog"""
    
    def __init__(self, parent, template_system: TemplateSystem):
        self.parent = parent
        self.template_system = template_system
        self.settings_changed = False
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Template & Color Scheme Editor")
        self.dialog.geometry("700x600")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (350)
        y = (self.dialog.winfo_screenheight() // 2) - (300)
        self.dialog.geometry(f"700x600+{x}+{y}")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup template editor UI"""
        
        # Create notebook for tabs
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Template selection tab
        template_frame = ttk.Frame(notebook)
        notebook.add(template_frame, text="Templates")
        self.setup_template_tab(template_frame)
        
        # Color scheme tab
        color_frame = ttk.Frame(notebook)
        notebook.add(color_frame, text="Color Schemes")
        self.setup_color_tab(color_frame)
        
        # Branding tab
        branding_frame = ttk.Frame(notebook)
        notebook.add(branding_frame, text="Branding")
        self.setup_branding_tab(branding_frame)
        
        # Custom template tab
        custom_frame = ttk.Frame(notebook)
        notebook.add(custom_frame, text="Custom Template")
        self.setup_custom_tab(custom_frame)
        
        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        ttk.Button(
            button_frame,
            text="Preview",
            command=self.preview_template
        ).pack(side='left')
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel_changes
        ).pack(side='right')
        
        ttk.Button(
            button_frame,
            text="Apply",
            command=self.apply_changes
        ).pack(side='right', padx=(0, 5))
    
    def setup_template_tab(self, parent):
        """Setup template selection tab"""
        
        # Template selection
        select_frame = ttk.LabelFrame(parent, text="Select Template", padding="10")
        select_frame.pack(fill='x', pady=(0, 10))
        
        self.template_var = tk.StringVar(value=self.template_system.current_template)
        
        templates = self.template_system.get_available_templates()
        for template in templates:
            ttk.Radiobutton(
                select_frame,
                text=template,
                variable=self.template_var,
                value=template,
                command=self.on_template_changed
            ).pack(anchor='w', pady=2)
        
        # Template preview
        preview_frame = ttk.LabelFrame(parent, text="Template Preview", padding="10")
        preview_frame.pack(fill='both', expand=True)
        
        self.template_preview = tk.Text(
            preview_frame,
            height=15,
            wrap='word',
            state='disabled',
            font=('Consolas', 9)
        )
        
        preview_scroll = ttk.Scrollbar(preview_frame, orient='vertical', command=self.template_preview.yview)
        self.template_preview.configure(yscrollcommand=preview_scroll.set)
        
        self.template_preview.pack(side='left', fill='both', expand=True)
        preview_scroll.pack(side='right', fill='y')
        
        # Initialize preview
        self.update_template_preview()
    
    def setup_color_tab(self, parent):
        """Setup color scheme tab"""
        
        # Color scheme selection
        select_frame = ttk.LabelFrame(parent, text="Select Color Scheme", padding="10")
        select_frame.pack(fill='x', pady=(0, 10))
        
        self.color_var = tk.StringVar(value=self.template_system.current_color_scheme)
        
        for scheme_name in self.template_system.color_schemes.keys():
            ttk.Radiobutton(
                select_frame,
                text=scheme_name,
                variable=self.color_var,
                value=scheme_name,
                command=self.on_color_changed
            ).pack(anchor='w', pady=2)
        
        # Color preview
        preview_frame = ttk.LabelFrame(parent, text="Color Preview", padding="10")
        preview_frame.pack(fill='both', expand=True)
        
        self.color_preview_frame = ttk.Frame(preview_frame)
        self.color_preview_frame.pack(fill='both', expand=True)
        
        # Initialize color preview
        self.update_color_preview()
    
    def setup_branding_tab(self, parent):
        """Setup branding customization tab"""
        
        # Company information
        company_frame = ttk.LabelFrame(parent, text="Company Information", padding="10")
        company_frame.pack(fill='x', pady=(0, 10))
        
        # Company name
        ttk.Label(company_frame, text="Company Name:").grid(row=0, column=0, sticky='w', pady=2)
        self.company_name_var = tk.StringVar(value=self.template_system.custom_branding.get('company_name', ''))
        ttk.Entry(company_frame, textvariable=self.company_name_var, width=40).grid(row=0, column=1, sticky='ew', pady=2, padx=(5, 0))
        
        # Contact info
        ttk.Label(company_frame, text="Contact Info:").grid(row=1, column=0, sticky='w', pady=2)
        self.contact_info_var = tk.StringVar(value=self.template_system.custom_branding.get('contact_info', ''))
        ttk.Entry(company_frame, textvariable=self.contact_info_var, width=40).grid(row=1, column=1, sticky='ew', pady=2, padx=(5, 0))
        
        # License number
        ttk.Label(company_frame, text="License Number:").grid(row=2, column=0, sticky='w', pady=2)
        self.license_var = tk.StringVar(value=self.template_system.custom_branding.get('license_number', ''))
        ttk.Entry(company_frame, textvariable=self.license_var, width=40).grid(row=2, column=1, sticky='ew', pady=2, padx=(5, 0))
        
        company_frame.columnconfigure(1, weight=1)
        
        # Logo and assets
        assets_frame = ttk.LabelFrame(parent, text="Logo & Assets", padding="10")
        assets_frame.pack(fill='x', pady=(0, 10))
        
        # Logo path
        logo_frame = ttk.Frame(assets_frame)
        logo_frame.pack(fill='x', pady=2)
        
        ttk.Label(logo_frame, text="Logo File:").pack(side='left')
        self.logo_path_var = tk.StringVar(value=self.template_system.custom_branding.get('logo_path', ''))
        ttk.Entry(logo_frame, textvariable=self.logo_path_var, width=35).pack(side='left', padx=(5, 5), fill='x', expand=True)
        ttk.Button(logo_frame, text="Browse", command=self.browse_logo).pack(side='right')
        
        # Footer text
        footer_frame = ttk.LabelFrame(parent, text="Footer Text", padding="10")
        footer_frame.pack(fill='both', expand=True)
        
        self.footer_text = tk.Text(footer_frame, height=6, wrap='word')
        self.footer_text.pack(fill='both', expand=True)
        self.footer_text.insert('1.0', self.template_system.custom_branding.get('footer_text', ''))
    
    def setup_custom_tab(self, parent):
        """Setup custom template creation tab"""
        
        info_label = ttk.Label(
            parent,
            text="Custom template creation coming in future update.\nFor now, customize existing templates using the other tabs.",
            font=('TkDefaultFont', 10),
            justify='center'
        )
        info_label.pack(expand=True)
    
    def on_template_changed(self):
        """Handle template selection change"""
        self.update_template_preview()
    
    def on_color_changed(self):
        """Handle color scheme change"""
        self.update_color_preview()
    
    def update_template_preview(self):
        """Update template preview display"""
        
        template_name = self.template_var.get()
        template_config = self.template_system.get_template(template_name)
        
        if template_config:
            preview_text = f"Template: {template_name}\n"
            preview_text += f"Description: {template_config.get('description', 'No description')}\n\n"
            
            preview_text += "Fonts:\n"
            fonts = template_config.get('fonts', {})
            for font_type, font_config in fonts.items():
                preview_text += f"  {font_type}: {font_config.get('family', 'N/A')} {font_config.get('size', 'N/A')}pt"
                if font_config.get('bold'): preview_text += " Bold"
                if font_config.get('italic'): preview_text += " Italic"
                preview_text += "\n"
            
            preview_text += "\nSpacing:\n"
            spacing = template_config.get('spacing', {})
            for spacing_type, value in spacing.items():
                preview_text += f"  {spacing_type}: {value}\n"
            
            preview_text += "\nLayout Options:\n"
            layout = template_config.get('layout', {})
            for layout_type, value in layout.items():
                preview_text += f"  {layout_type}: {value}\n"
            
            # Update preview
            self.template_preview.config(state='normal')
            self.template_preview.delete('1.0', 'end')
            self.template_preview.insert('1.0', preview_text)
            self.template_preview.config(state='disabled')
    
    def update_color_preview(self):
        """Update color scheme preview"""
        
        # Clear existing preview
        for widget in self.color_preview_frame.winfo_children():
            widget.destroy()
        
        scheme_name = self.color_var.get()
        colors = self.template_system.color_schemes.get(scheme_name, {})
        
        # Create color swatches
        row = 0
        for color_name, color_value in colors.items():
            # Color name label
            ttk.Label(
                self.color_preview_frame,
                text=f"{color_name.replace('_', ' ').title()}:",
                width=15
            ).grid(row=row, column=0, sticky='w', pady=2)
            
            # Color swatch
            swatch_frame = tk.Frame(
                self.color_preview_frame,
                bg=color_value,
                width=50,
                height=25,
                relief='solid',
                borderwidth=1
            )
            swatch_frame.grid(row=row, column=1, pady=2, padx=(5, 10))
            swatch_frame.grid_propagate(False)
            
            # Color value label
            ttk.Label(
                self.color_preview_frame,
                text=color_value,
                font=('Consolas', 9)
            ).grid(row=row, column=2, sticky='w', pady=2)
            
            row += 1
    
    def browse_logo(self):
        """Browse for logo file"""
        
        filename = filedialog.askopenfilename(
            title="Select Logo File",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            self.logo_path_var.set(filename)
    
    def preview_template(self):
        """Preview template with current settings"""
        
        # This would show a preview of how the template looks
        # For now, show a simple message
        messagebox.showinfo(
            "Template Preview",
            f"Preview for template '{self.template_var.get()}' with color scheme '{self.color_var.get()}'\n\n"
            "Full preview functionality coming in future update."
        )
    
    def apply_changes(self):
        """Apply template and branding changes"""
        
        try:
            # Update current template and color scheme
            self.template_system.current_template = self.template_var.get()
            self.template_system.current_color_scheme = self.color_var.get()
            
            # Update branding settings
            self.template_system.custom_branding.update({
                'company_name': self.company_name_var.get(),
                'contact_info': self.contact_info_var.get(),
                'license_number': self.license_var.get(),
                'logo_path': self.logo_path_var.get(),
                'footer_text': self.footer_text.get('1.0', 'end-1c')
            })
            
            # Save settings
            self.template_system.save_current_settings()
            self.template_system.save_branding_settings()
            
            self.settings_changed = True
            messagebox.showinfo("Success", "Template and branding settings saved successfully!")
            self.dialog.destroy()
            
        except Exception as e:
            logger.error(f"Failed to apply template changes: {e}")
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
    
    def cancel_changes(self):
        """Cancel changes and close dialog"""
        self.settings_changed = False
        self.dialog.destroy()


# Test the template system
if __name__ == "__main__":
    print("🎨 Testing DKI Engine Template System...")
    
    template_system = TemplateSystem()
    
    print(f"Available Templates: {template_system.get_available_templates()}")
    print(f"Available Color Schemes: {list(template_system.color_schemes.keys())}")
    print(f"Current Template: {template_system.current_template}")
    print(f"Current Color Scheme: {template_system.current_color_scheme}")
    
    print("✅ Template system initialized successfully!")








