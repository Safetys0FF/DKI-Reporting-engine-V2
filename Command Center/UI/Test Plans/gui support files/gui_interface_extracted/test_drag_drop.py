#!/usr/bin/env python3
"""
Simple test script to verify drag and drop functionality
"""

import tkinter as tk
from tkinter import ttk
import os

# Try to import tkinterdnd2
try:
    import tkinterdnd2 as tkdnd
    HAS_TKINTERDND2 = True
    print("✅ tkinterdnd2 is available")
except ImportError:
    HAS_TKINTERDND2 = False
    print("❌ tkinterdnd2 not available")

def on_file_drop(event):
    """Handle file drop"""
    print(f"📁 Files dropped: {event.data}")
    
    # Parse file paths correctly - handle multiple files with spaces
    data = event.data.strip()
    
    # Split by '} {' pattern to separate individual file paths
    if '} {' in data:
        # Multiple files - split by '} {' pattern
        file_paths = data.split('} {')
        # Clean up the first and last entries
        file_paths[0] = file_paths[0].lstrip('{')
        file_paths[-1] = file_paths[-1].rstrip('}')
    else:
        # Single file or no separator found
        file_paths = [data.strip('{}')]
    
    # Process each file path
    success_count = 0
    for file_path in file_paths:
        file_path = file_path.strip()
        if file_path and os.path.exists(file_path):
            filename = os.path.basename(file_path)
            print(f"✅ Added: {filename}")
            success_count += 1
        elif file_path:
            print(f"❌ File not found: {file_path}")
    
    print(f"📊 Successfully processed {success_count} out of {len(file_paths)} files")

def main():
    """Create test window"""
    if HAS_TKINTERDND2:
        root = tkdnd.Tk()
    else:
        root = tk.Tk()
    
    root.title("Drag & Drop Test")
    root.geometry("400x300")
    
    # Create drop area
    drop_frame = tk.Frame(root, bg='#e8f4fd', relief='solid', borderwidth=2, height=200)
    drop_frame.pack(fill='both', expand=True, padx=20, pady=20)
    
    # Add canvas for dashed border
    canvas = tk.Canvas(drop_frame, bg='#e8f4fd', highlightthickness=0)
    canvas.pack(fill='both', expand=True, padx=2, pady=2)
    
    # Draw dashed border
    canvas.create_rectangle(2, 2, 398, 198, outline='#007bff', dash=(5, 5), width=2)
    
    # Add label
    label = tk.Label(canvas, text="📁 Drop files here\n\n(Multiple files supported)\n\nTest drag and drop", 
                    font=('Arial', 12), bg='#e8f4fd', fg='#666666')
    canvas.create_window(200, 100, window=label)
    
    if HAS_TKINTERDND2:
        # Register drop target
        canvas.drop_target_register(tkdnd.DND_FILES)
        canvas.dnd_bind('<<Drop>>', on_file_drop)
        print("✅ Drag and drop registered")
    else:
        print("❌ No drag and drop available")
    
    root.mainloop()

if __name__ == "__main__":
    main()
