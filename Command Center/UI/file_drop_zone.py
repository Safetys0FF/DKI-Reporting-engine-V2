#!/usr/bin/env python3
"""
File Drop Zone - Modern drag-and-drop interface for DKI Engine
Provides intuitive file upload with visual feedback and progress tracking
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
try:
    import tkinterdnd2 as tkdnd
    DRAG_DROP_AVAILABLE = True
except ImportError:
    tkdnd = None
    DRAG_DROP_AVAILABLE = False
from typing import List, Dict, Any, Callable, Optional
import os
import threading
from pathlib import Path
import mimetypes
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class FileDropZone(tk.Frame):
    """Modern drag-and-drop file upload zone with visual feedback"""
    
    def __init__(self, parent, on_files_dropped: Callable = None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.on_files_dropped = on_files_dropped
        self.uploaded_files = []
        self.is_dragging = False
        
        # Supported file types
        self.supported_extensions = {
            'pdf': ['.pdf'],
            'image': ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.heic', '.heif'],
            'video': ['.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv'],
            'audio': ['.mp3', '.wav', '.m4a', '.aac', '.ogg', '.wma', '.flac'],
            'document': ['.docx', '.doc', '.txt', '.rtf'],
            'spreadsheet': ['.xlsx', '.xls', '.csv'],
            'archive': ['.zip', '.rar', '.7z']
        }
        
        self.setup_ui()
        self.setup_drag_drop()
    
    def setup_ui(self):
        """Setup the drop zone user interface"""
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Main drop zone frame
        self.drop_frame = tk.Frame(
            self,
            bg='#f8f9fa',
            relief='ridge',
            bd=2,
            cursor='hand2'
        )
        self.drop_frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        self.drop_frame.grid_columnconfigure(0, weight=1)
        self.drop_frame.grid_rowconfigure(0, weight=1)
        
        # Drop zone content
        content_frame = tk.Frame(self.drop_frame, bg='#f8f9fa')
        content_frame.grid(row=0, column=0, pady=50)
        
        # Drop zone icon (using text as placeholder)
        self.icon_label = tk.Label(
            content_frame,
            text="📁",
            font=('Arial', 48),
            bg='#f8f9fa',
            fg='#6c757d'
        )
        self.icon_label.pack(pady=(0, 20))
        
        # Drop zone title
        self.title_label = tk.Label(
            content_frame,
            text="Drop Files Here",
            font=('Arial', 18, 'bold'),
            bg='#f8f9fa',
            fg='#495057'
        )
        self.title_label.pack(pady=(0, 10))
        
        # Drop zone subtitle
        self.subtitle_label = tk.Label(
            content_frame,
            text="or click to browse",
            font=('Arial', 12),
            bg='#f8f9fa',
            fg='#6c757d'
        )
        self.subtitle_label.pack(pady=(0, 20))
        
        # Supported formats info
        formats_text = "Supports: PDF, Images, Videos, Documents, Spreadsheets"
        self.formats_label = tk.Label(
            content_frame,
            text=formats_text,
            font=('Arial', 10),
            bg='#f8f9fa',
            fg='#868e96'
        )
        self.formats_label.pack()
        
        # Browse button
        self.browse_btn = tk.Button(
            content_frame,
            text="Browse Files",
            font=('Arial', 11),
            bg='#007bff',
            fg='white',
            relief='flat',
            padx=20,
            pady=8,
            cursor='hand2',
            command=self.browse_files
        )
        self.browse_btn.pack(pady=(20, 0))
        
        # File list frame
        self.file_list_frame = tk.Frame(self)
        self.file_list_frame.grid(row=1, column=0, sticky='ew', padx=10, pady=(0, 10))
        self.file_list_frame.grid_columnconfigure(0, weight=1)
        
        # File list header
        self.list_header = tk.Label(
            self.file_list_frame,
            text="Uploaded Files (0)",
            font=('Arial', 12, 'bold'),
            anchor='w'
        )
        self.list_header.grid(row=0, column=0, sticky='w', pady=(0, 5))
        
        # File list with scrollbar
        list_container = tk.Frame(self.file_list_frame)
        list_container.grid(row=1, column=0, sticky='ew')
        list_container.grid_columnconfigure(0, weight=1)
        
        self.file_listbox = tk.Listbox(
            list_container,
            height=6,
            font=('Arial', 10),
            selectmode=tk.EXTENDED
        )
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.file_listbox.yview)
        self.file_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.file_listbox.grid(row=0, column=0, sticky='ew')
        scrollbar.grid(row=0, column=1, sticky='ns')
        
        # File list controls
        controls_frame = tk.Frame(self.file_list_frame)
        controls_frame.grid(row=2, column=0, sticky='ew', pady=(5, 0))
        
        self.remove_btn = tk.Button(
            controls_frame,
            text="Remove Selected",
            font=('Arial', 10),
            bg='#dc3545',
            fg='white',
            relief='flat',
            padx=15,
            pady=5,
            command=self.remove_selected_files
        )
        self.remove_btn.pack(side='left', padx=(0, 10))
        
        self.clear_btn = tk.Button(
            controls_frame,
            text="Clear All",
            font=('Arial', 10),
            bg='#6c757d',
            fg='white',
            relief='flat',
            padx=15,
            pady=5,
            command=self.clear_all_files
        )
        self.clear_btn.pack(side='left')
        
        # Progress frame (initially hidden)
        self.progress_frame = tk.Frame(self)
        self.progress_frame.grid(row=2, column=0, sticky='ew', padx=10, pady=(0, 10))
        self.progress_frame.grid_remove()  # Hide initially
        
        self.progress_label = tk.Label(
            self.progress_frame,
            text="Processing files...",
            font=('Arial', 10)
        )
        self.progress_label.pack(pady=(0, 5))
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode='indeterminate',
            length=300
        )
        self.progress_bar.pack()
        
        # Bind click events
        self.drop_frame.bind("<Button-1>", lambda e: self.browse_files())
        self.icon_label.bind("<Button-1>", lambda e: self.browse_files())
        self.title_label.bind("<Button-1>", lambda e: self.browse_files())
        self.subtitle_label.bind("<Button-1>", lambda e: self.browse_files())
    
    def setup_drag_drop(self):
        """Setup drag and drop functionality"""
        
        if DRAG_DROP_AVAILABLE:
            try:
                # Enable drag and drop
                self.drop_frame.drop_target_register(tkdnd.DND_FILES)
                self.drop_frame.dnd_bind('<<DropEnter>>', self.on_drag_enter)
                self.drop_frame.dnd_bind('<<DropLeave>>', self.on_drag_leave)
                self.drop_frame.dnd_bind('<<Drop>>', self.on_drop)
            
                logger.info("Drag and drop enabled")
                
            except Exception as e:
                logger.warning(f"Drag and drop setup failed: {e}")
        else:
            logger.warning("tkinterdnd2 not available, drag-and-drop disabled")
            # Update UI to indicate drag-drop not available
            self.subtitle_label.config(text="Click to browse files")
    
    def on_drag_enter(self, event):
        """Handle drag enter event"""
        self.is_dragging = True
        self.drop_frame.config(bg='#e3f2fd', relief='solid', bd=3)
        self.icon_label.config(text="📂", bg='#e3f2fd')
        self.title_label.config(text="Drop Files Now", bg='#e3f2fd', fg='#1976d2')
        self.subtitle_label.config(bg='#e3f2fd', fg='#1976d2')
        self.formats_label.config(bg='#e3f2fd')
        
        # Update all child widgets
        for widget in [self.icon_label, self.title_label, self.subtitle_label, self.formats_label]:
            widget.config(bg='#e3f2fd')
    
    def on_drag_leave(self, event):
        """Handle drag leave event"""
        self.is_dragging = False
        self.reset_drop_zone_appearance()
    
    def on_drop(self, event):
        """Handle file drop event"""
        self.is_dragging = False
        self.reset_drop_zone_appearance()
        
        # Get dropped files
        files = self.tk.splitlist(event.data)
        self.add_files(files)
    
    def reset_drop_zone_appearance(self):
        """Reset drop zone to normal appearance"""
        bg_color = '#f8f9fa'
        self.drop_frame.config(bg=bg_color, relief='ridge', bd=2)
        self.icon_label.config(text="📁", bg=bg_color, fg='#6c757d')
        self.title_label.config(text="Drop Files Here", bg=bg_color, fg='#495057')
        self.subtitle_label.config(text="or click to browse", bg=bg_color, fg='#6c757d')
        self.formats_label.config(bg=bg_color)
        
        # Update all child widgets
        for widget in [self.icon_label, self.title_label, self.subtitle_label, self.formats_label]:
            widget.config(bg=bg_color)
    
    def browse_files(self):
        """Open file browser dialog"""
        
        filetypes = [
            ("All supported", "*.pdf *.jpg *.jpeg *.png *.tiff *.mp4 *.mov *.docx *.xlsx"),
            ("PDF files", "*.pdf"),
            ("Image files", "*.jpg *.jpeg *.png *.tiff *.bmp *.heic"),
            ("Video files", "*.mp4 *.mov *.avi *.mkv"),
            ("Document files", "*.docx *.doc *.txt *.rtf"),
            ("Spreadsheet files", "*.xlsx *.xls *.csv"),
            ("All files", "*.*")
        ]
        
        files = filedialog.askopenfilenames(
            title="Select files for processing",
            filetypes=filetypes
        )
        
        if files:
            self.add_files(files)
    
    def add_files(self, file_paths: List[str]):
        """Add files to the upload list"""
        
        added_count = 0
        
        for file_path in file_paths:
            if self.is_file_supported(file_path) and file_path not in [f['path'] for f in self.uploaded_files]:
                
                file_info = self.get_file_info(file_path)
                self.uploaded_files.append(file_info)
                
                # Add to listbox
                display_name = f"{file_info['type'].upper()}: {file_info['name']} ({self.format_file_size(file_info['size'])})"
                self.file_listbox.insert(tk.END, display_name)
                
                added_count += 1
        
        # Update file count
        self.update_file_count()
        
        # Show feedback
        if added_count > 0:
            self.show_temporary_feedback(f"Added {added_count} file(s)")
            
            # Notify callback
            if self.on_files_dropped:
                self.on_files_dropped(self.uploaded_files)
        
        logger.info(f"Added {added_count} files to drop zone")
    
    def is_file_supported(self, file_path: str) -> bool:
        """Check if file type is supported"""
        
        ext = Path(file_path).suffix.lower()
        
        for file_type, extensions in self.supported_extensions.items():
            if ext in extensions:
                return True
        
        return False
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get detailed file information"""
        
        path_obj = Path(file_path)
        ext = path_obj.suffix.lower()
        
        # Determine file type
        file_type = 'unknown'
        for ftype, extensions in self.supported_extensions.items():
            if ext in extensions:
                file_type = ftype
                break
        
        return {
            'path': file_path,
            'name': path_obj.name,
            'type': file_type,
            'size': path_obj.stat().st_size,
            'extension': ext,
            'mime_type': mimetypes.guess_type(file_path)[0],
            'uploaded_date': datetime.now().isoformat()
        }
    
    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        
        return f"{size_bytes:.1f} TB"
    
    def remove_selected_files(self):
        """Remove selected files from the list"""
        
        selected_indices = self.file_listbox.curselection()
        
        if not selected_indices:
            messagebox.showinfo("No Selection", "Please select files to remove")
            return
        
        # Remove in reverse order to maintain indices
        for index in reversed(selected_indices):
            del self.uploaded_files[index]
            self.file_listbox.delete(index)
        
        self.update_file_count()
        
        # Notify callback
        if self.on_files_dropped:
            self.on_files_dropped(self.uploaded_files)
    
    def clear_all_files(self):
        """Clear all files from the list"""
        
        if not self.uploaded_files:
            return
        
        if messagebox.askyesno("Clear All", "Remove all files from the list?"):
            self.uploaded_files.clear()
            self.file_listbox.delete(0, tk.END)
            self.update_file_count()
            
            # Notify callback
            if self.on_files_dropped:
                self.on_files_dropped(self.uploaded_files)
    
    def update_file_count(self):
        """Update the file count display"""
        count = len(self.uploaded_files)
        self.list_header.config(text=f"Uploaded Files ({count})")
    
    def show_temporary_feedback(self, message: str, duration: int = 2000):
        """Show temporary feedback message"""
        
        # Create feedback label if it doesn't exist
        if not hasattr(self, 'feedback_label'):
            self.feedback_label = tk.Label(
                self,
                text="",
                font=('Arial', 10),
                fg='#28a745',
                bg=self['bg']
            )
            self.feedback_label.grid(row=3, column=0, pady=(0, 5))
        
        # Show message
        self.feedback_label.config(text=message)
        self.feedback_label.grid()
        
        # Hide after duration
        self.after(duration, lambda: self.feedback_label.grid_remove())
    
    def show_progress(self, message: str = "Processing files..."):
        """Show progress indicator"""
        
        self.progress_label.config(text=message)
        self.progress_frame.grid()
        self.progress_bar.start(10)
    
    def hide_progress(self):
        """Hide progress indicator"""
        
        self.progress_bar.stop()
        self.progress_frame.grid_remove()
    
    def get_files_by_type(self, file_type: str) -> List[Dict[str, Any]]:
        """Get files of a specific type"""
        return [f for f in self.uploaded_files if f['type'] == file_type]
    
    def get_all_files(self) -> List[Dict[str, Any]]:
        """Get all uploaded files"""
        return self.uploaded_files.copy()
    
    def set_files(self, files: List[Dict[str, Any]]):
        """Set the file list (for loading saved cases)"""
        
        self.uploaded_files = files.copy()
        
        # Update listbox
        self.file_listbox.delete(0, tk.END)
        for file_info in self.uploaded_files:
            display_name = f"{file_info['type'].upper()}: {file_info['name']} ({self.format_file_size(file_info['size'])})"
            self.file_listbox.insert(tk.END, display_name)
        
        self.update_file_count()


# Example usage widget
class FileDropZoneDemo(tk.Tk):
    """Demo application for the file drop zone"""
    
    def __init__(self):
        super().__init__()
        
        self.title("DKI Engine - File Drop Zone Demo")
        self.geometry("600x500")
        
        # Create drop zone
        self.drop_zone = FileDropZone(
            self,
            on_files_dropped=self.on_files_changed
        )
        self.drop_zone.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready - Drop files or click to browse")
        status_bar = tk.Label(
            self,
            textvariable=self.status_var,
            relief='sunken',
            anchor='w',
            font=('Arial', 10)
        )
        status_bar.pack(side='bottom', fill='x')
    
    def on_files_changed(self, files):
        """Handle file list changes"""
        
        if files:
            total_size = sum(f['size'] for f in files)
            size_str = self.drop_zone.format_file_size(total_size)
            self.status_var.set(f"{len(files)} files loaded - Total size: {size_str}")
        else:
            self.status_var.set("Ready - Drop files or click to browse")


if __name__ == "__main__":
    # Run demo
    try:
        app = FileDropZoneDemo()
        app.mainloop()
    except Exception as e:
        print(f"Demo failed: {e}")
        print("Note: tkinterdnd2 required for drag-and-drop functionality")
        print("Install with: pip install tkinterdnd2")
