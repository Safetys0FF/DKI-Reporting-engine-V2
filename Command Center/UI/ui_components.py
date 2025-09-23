#!/usr/bin/env python3
"""
UI Components - Reusable interface components for DKI Engine
Provides standard UI elements like toolbars, status bars, progress panels, etc.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Any, Callable, Optional, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class StatusBar(ttk.Frame):
    """Multi-section status bar with customizable sections"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.sections = {}
        self.section_vars = {}
        
        # Configure relief and border
        self.configure(relief='sunken', borderwidth=1)
    
    def add_section(self, name: str, text: str = "", weight: int = 1):
        """Add a section to the status bar"""
        
        # Create StringVar for the section
        var = tk.StringVar(value=text)
        self.section_vars[name] = var
        
        # Create label
        label = ttk.Label(
            self,
            textvariable=var,
            relief='sunken',
            anchor='w',
            padding=(5, 2)
        )
        
        # Grid the label
        col = len(self.sections)
        label.grid(row=0, column=col, sticky='ew', padx=(0, 1))
        
        # Configure column weight
        self.grid_columnconfigure(col, weight=weight)
        
        # Store section info
        self.sections[name] = {
            'label': label,
            'var': var,
            'weight': weight
        }
    
    def update_section(self, name: str, text: str):
        """Update text in a section"""
        if name in self.section_vars:
            self.section_vars[name].set(text)
    
    def get_section_text(self, name: str) -> str:
        """Get text from a section"""
        if name in self.section_vars:
            return self.section_vars[name].get()
        return ""

class ToolBar(ttk.Frame):
    """Customizable toolbar with buttons and separators"""
    
    def __init__(self, parent, button_config: List, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.buttons = {}
        self.button_config = button_config
        
        self.create_toolbar()
    
    def create_toolbar(self):
        """Create the toolbar based on configuration"""
        
        col = 0
        
        for item in self.button_config:
            if item == 'separator':
                # Add separator
                separator = ttk.Separator(self, orient='vertical')
                separator.grid(row=0, column=col, sticky='ns', padx=5, pady=2)
                col += 1
                
            elif isinstance(item, tuple) and len(item) >= 3:
                # Add button
                button_id, text, command = item[:3]
                tooltip = item[3] if len(item) > 3 else None
                
                button = ttk.Button(
                    self,
                    text=text,
                    command=command,
                    width=12
                )
                button.grid(row=0, column=col, padx=2, pady=2)
                
                # Add tooltip if provided
                if tooltip:
                    self.create_tooltip(button, tooltip)
                
                self.buttons[button_id] = button
                col += 1
    
    def enable_button(self, button_id: str):
        """Enable a specific button"""
        if button_id in self.buttons:
            self.buttons[button_id].configure(state='normal')
    
    def disable_button(self, button_id: str):
        """Disable a specific button"""
        if button_id in self.buttons:
            self.buttons[button_id].configure(state='disabled')
    
    def enable_buttons(self, button_ids: List[str]):
        """Enable multiple buttons"""
        for button_id in button_ids:
            self.enable_button(button_id)
    
    def disable_buttons(self, button_ids: List[str]):
        """Disable multiple buttons"""
        for button_id in button_ids:
            self.disable_button(button_id)
    
    def create_tooltip(self, widget, text):
        """Create a tooltip for a widget"""
        
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = tk.Label(
                tooltip,
                text=text,
                background='#ffffe0',
                relief='solid',
                borderwidth=1,
                font=('Arial', 9)
            )
            label.pack()
            
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)

class MenuManager:
    """Manages the main application menu"""
    
    def __init__(self, root, menu_config: Dict):
        self.root = root
        self.menu_config = menu_config
        self.menus = {}
    
    def create_menu(self):
        """Create the menu system"""
        
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        for menu_name, menu_items in self.menu_config.items():
            menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label=menu_name, menu=menu)
            self.menus[menu_name] = menu
            
            self.populate_menu(menu, menu_items)
    
    def populate_menu(self, menu, items):
        """Populate a menu with items"""
        
        for item_name, item_config in items.items():
            if item_name == 'separator':
                menu.add_separator()
            elif callable(item_config):
                # Submenu
                submenu = tk.Menu(menu, tearoff=0)
                menu.add_cascade(label=item_name, menu=submenu)
                # Call function to populate submenu
                item_config(submenu)
            elif isinstance(item_config, tuple):
                # Menu item with accelerator and command
                accelerator, command = item_config
                menu.add_command(
                    label=item_name,
                    accelerator=accelerator,
                    command=command
                )
                
                # Bind keyboard shortcut if provided
                if accelerator:
                    self.bind_accelerator(accelerator, command)
    
    def bind_accelerator(self, accelerator: str, command: Callable):
        """Bind keyboard accelerator to command"""
        
        # Convert accelerator string to tkinter format
        key_map = {
            'Ctrl+': '<Control-',
            'Shift+': '<Shift-',
            'Alt+': '<Alt-',
            'F1': '<F1>', 'F2': '<F2>', 'F3': '<F3>', 'F4': '<F4>',
            'F5': '<F5>', 'F6': '<F6>', 'F7': '<F7>', 'F8': '<F8>',
            'F9': '<F9>', 'F10': '<F10>', 'F11': '<F11>', 'F12': '<F12>'
        }
        
        tk_key = accelerator
        for old, new in key_map.items():
            tk_key = tk_key.replace(old, new)
        
        if not tk_key.endswith('>') and not tk_key.startswith('<F'):
            tk_key += '>'
        
        try:
            self.root.bind_all(tk_key, lambda e: command())
        except tk.TclError:
            logger.warning(f"Failed to bind accelerator: {accelerator}")

class ProgressPanel(ttk.Frame):
    """Progress panel with message and progress bar"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.is_visible = False
        
        # Message label
        self.message_var = tk.StringVar(value="Processing...")
        self.message_label = ttk.Label(self, textvariable=self.message_var)
        self.message_label.pack(side='left', padx=(5, 10))
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(
            self,
            mode='indeterminate',
            length=200
        )
        self.progress_bar.pack(side='left', padx=(0, 5))
        
        # Cancel button (optional)
        self.cancel_button = ttk.Button(
            self,
            text="Cancel",
            command=self.on_cancel
        )
        self.cancel_button.pack(side='right', padx=(10, 5))
        
        self.cancel_callback = None
    
    def show(self):
        """Show the progress panel"""
        if not self.is_visible:
            self.grid()
            self.is_visible = True
    
    def hide(self):
        """Hide the progress panel"""
        if self.is_visible:
            self.grid_remove()
            self.is_visible = False
            self.stop_progress()
    
    def start_progress(self):
        """Start the progress animation"""
        self.progress_bar.start(10)
    
    def stop_progress(self):
        """Stop the progress animation"""
        self.progress_bar.stop()
    
    def set_message(self, message: str):
        """Set the progress message"""
        self.message_var.set(message)
    
    def set_cancel_callback(self, callback: Callable):
        """Set callback for cancel button"""
        self.cancel_callback = callback
    
    def on_cancel(self):
        """Handle cancel button click"""
        if self.cancel_callback:
            self.cancel_callback()
        self.hide()

class NotificationManager:
    """Manages temporary notifications/toasts"""
    
    def __init__(self, parent):
        self.parent = parent
        self.notifications = []
    
    def show_notification(self, message: str, type: str = "info", duration: int = 3000):
        """Show a temporary notification"""
        
        # Colors for different notification types
        colors = {
            'info': {'bg': '#d1ecf1', 'fg': '#0c5460', 'border': '#bee5eb'},
            'success': {'bg': '#d4edda', 'fg': '#155724', 'border': '#c3e6cb'},
            'warning': {'bg': '#fff3cd', 'fg': '#856404', 'border': '#ffeaa7'},
            'error': {'bg': '#f8d7da', 'fg': '#721c24', 'border': '#f5c6cb'}
        }
        
        color_scheme = colors.get(type, colors['info'])
        
        # Create notification window
        notification = tk.Toplevel(self.parent)
        notification.wm_overrideredirect(True)
        notification.configure(bg=color_scheme['border'])
        
        # Position notification
        x = self.parent.winfo_rootx() + self.parent.winfo_width() - 350
        y = self.parent.winfo_rooty() + 50 + len(self.notifications) * 70
        notification.wm_geometry(f"+{x}+{y}")
        
        # Create notification content
        frame = tk.Frame(
            notification,
            bg=color_scheme['bg'],
            padx=15,
            pady=10
        )
        frame.pack(fill='both', expand=True, padx=2, pady=2)
        
        # Message label
        label = tk.Label(
            frame,
            text=message,
            bg=color_scheme['bg'],
            fg=color_scheme['fg'],
            font=('Arial', 10),
            wraplength=300
        )
        label.pack(side='left', fill='both', expand=True)
        
        # Close button
        close_btn = tk.Button(
            frame,
            text="×",
            bg=color_scheme['bg'],
            fg=color_scheme['fg'],
            font=('Arial', 12, 'bold'),
            relief='flat',
            padx=5,
            command=lambda: self.close_notification(notification)
        )
        close_btn.pack(side='right')
        
        # Store notification
        self.notifications.append(notification)
        
        # Auto-close after duration
        notification.after(duration, lambda: self.close_notification(notification))
        
        # Fade in effect (simplified)
        notification.attributes('-alpha', 0.0)
        self.fade_in(notification)
    
    def fade_in(self, window, alpha=0.0):
        """Fade in animation for notification"""
        if alpha < 1.0:
            alpha += 0.1
            window.attributes('-alpha', alpha)
            window.after(50, lambda: self.fade_in(window, alpha))
    
    def close_notification(self, notification):
        """Close a notification"""
        if notification in self.notifications:
            self.notifications.remove(notification)
            notification.destroy()
            self.reposition_notifications()
    
    def reposition_notifications(self):
        """Reposition remaining notifications"""
        for i, notification in enumerate(self.notifications):
            x = self.parent.winfo_rootx() + self.parent.winfo_width() - 350
            y = self.parent.winfo_rooty() + 50 + i * 70
            notification.wm_geometry(f"+{x}+{y}")

class ControlPanel(ttk.LabelFrame):
    """Base class for control panels"""
    
    def __init__(self, parent, title: str, **kwargs):
        super().__init__(parent, text=title, padding="10", **kwargs)
        
        self.controls = {}
        self.enabled = True
    
    def add_button(self, name: str, text: str, command: Callable, 
                   style: str = None, tooltip: str = None) -> ttk.Button:
        """Add a button to the control panel"""
        
        button = ttk.Button(self, text=text, command=command)
        if style:
            button.configure(style=style)
        
        self.controls[name] = button
        
        if tooltip:
            self.create_tooltip(button, tooltip)
        
        return button
    
    def add_label(self, name: str, text: str) -> ttk.Label:
        """Add a label to the control panel"""
        
        label = ttk.Label(self, text=text)
        self.controls[name] = label
        return label
    
    def add_entry(self, name: str, textvariable: tk.StringVar = None) -> ttk.Entry:
        """Add an entry widget to the control panel"""
        
        entry = ttk.Entry(self, textvariable=textvariable)
        self.controls[name] = entry
        return entry
    
    def enable_control(self, name: str):
        """Enable a specific control"""
        if name in self.controls:
            self.controls[name].configure(state='normal')
    
    def disable_control(self, name: str):
        """Disable a specific control"""
        if name in self.controls:
            self.controls[name].configure(state='disabled')
    
    def enable_all(self):
        """Enable all controls"""
        self.enabled = True
        for control in self.controls.values():
            if hasattr(control, 'configure'):
                control.configure(state='normal')
    
    def disable_all(self):
        """Disable all controls"""
        self.enabled = False
        for control in self.controls.values():
            if hasattr(control, 'configure'):
                control.configure(state='disabled')
    
    def create_tooltip(self, widget, text):
        """Create a tooltip for a widget"""
        
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = tk.Label(
                tooltip,
                text=text,
                background='#ffffe0',
                relief='solid',
                borderwidth=1,
                font=('Arial', 9)
            )
            label.pack()
            
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)

class TabManager(ttk.Notebook):
    """Enhanced notebook widget with tab management"""
    
    def __init__(self, parent, tab_config: List[Tuple], **kwargs):
        super().__init__(parent, **kwargs)
        
        self.tabs = {}
        self.tab_config = tab_config
        
        self.create_tabs()
    
    def create_tabs(self):
        """Create tabs based on configuration"""
        
        for tab_id, tab_text, tab_creator in self.tab_config:
            # Create tab frame
            tab_frame = ttk.Frame(self)
            
            # Call creator function to populate tab
            if callable(tab_creator):
                tab_creator(tab_frame)
            
            # Add tab to notebook
            self.add(tab_frame, text=tab_text)
            self.tabs[tab_id] = tab_frame
    
    def select_tab(self, tab_id: str):
        """Select a specific tab"""
        if tab_id in self.tabs:
            self.select(self.tabs[tab_id])
    
    def get_current_tab_id(self) -> str:
        """Get the ID of the currently selected tab"""
        current_tab = self.select()
        for tab_id, tab_frame in self.tabs.items():
            if str(tab_frame) == current_tab:
                return tab_id
        return ""
    
    def enable_tab(self, tab_id: str):
        """Enable a specific tab"""
        if tab_id in self.tabs:
            tab_index = list(self.tabs.keys()).index(tab_id)
            self.tab(tab_index, state='normal')
    
    def disable_tab(self, tab_id: str):
        """Disable a specific tab"""
        if tab_id in self.tabs:
            tab_index = list(self.tabs.keys()).index(tab_id)
            self.tab(tab_index, state='disabled')

