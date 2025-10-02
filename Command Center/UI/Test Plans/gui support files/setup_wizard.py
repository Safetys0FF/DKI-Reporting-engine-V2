#!/usr/bin/env python3
"""
Setup Wizard - First-time user setup and API key configuration
Professional onboarding experience for new users
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Dict, Optional, Callable
from user_profile_manager import UserProfileManager

logger = logging.getLogger(__name__)

class SetupWizard:
    """First-time setup wizard for new users"""
    
    def __init__(self, parent=None, on_complete: Callable = None, db_path=None):
        self.parent = parent
        self.on_complete = on_complete
        if db_path:
            self.profile_manager = UserProfileManager(db_path)
        else:
            self.profile_manager = UserProfileManager()
        
        # Setup data
        self.user_data = {}
        self.api_keys = {}
        
        # Create wizard window
        self.setup_window()
        
    def setup_window(self):
        """Create the setup wizard window"""
        self.wizard_window = tk.Toplevel(self.parent) if self.parent else tk.Tk()
        self.root = self.wizard_window  # For backward compatibility
        self.wizard_window.title("DKI Engine - First Time Setup")
        self.wizard_window.geometry("800x600")
        self.root.resizable(False, False)
        
        # Center window
        self.wizard_window.update_idletasks()
        x = (self.wizard_window.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.wizard_window.winfo_screenheight() // 2) - (600 // 2)
        self.wizard_window.geometry(f"800x600+{x}+{y}")
        
        # Make modal if parent exists
        if self.parent:
            self.wizard_window.transient(self.parent)
            self.wizard_window.grab_set()
        
        # Setup wizard pages
        self.current_page = 0
        self.pages = [
            self.create_welcome_page,
            self.create_user_info_page,
            self.create_api_keys_page,
            self.create_completion_page
        ]
        
        # Create main container
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.pack(fill='both', expand=True)
        
        # Create navigation frame
        self.nav_frame = ttk.Frame(self.main_frame)
        self.nav_frame.pack(side='bottom', fill='x', pady=(20, 0))
        
        # Navigation buttons
        self.back_btn = ttk.Button(self.nav_frame, text="← Back", command=self.go_back)
        self.back_btn.pack(side='left')
        
        self.next_btn = ttk.Button(self.nav_frame, text="Next →", command=self.go_next)
        self.next_btn.pack(side='right')
        
        self.finish_btn = ttk.Button(self.nav_frame, text="Finish", command=self.finish_setup)
        
        # Create content frame
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill='both', expand=True, pady=(0, 20))
        
        # Show first page
        self.show_page(0)
        
    def show_page(self, page_num):
        """Show specific wizard page"""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Update current page
        self.current_page = page_num
        
        # Create page content
        self.pages[page_num]()
        
        # Update navigation buttons
        self.update_navigation()
        
    def update_navigation(self):
        """Update navigation button states"""
        # Back button
        if self.current_page == 0:
            self.back_btn.config(state='disabled')
        else:
            self.back_btn.config(state='normal')
        
        # Next/Finish buttons
        if self.current_page == len(self.pages) - 1:
            self.next_btn.pack_forget()
            self.finish_btn.pack(side='right')
        else:
            self.finish_btn.pack_forget()
            self.next_btn.pack(side='right')
    
    def create_welcome_page(self):
        """Create welcome page"""
        # Title
        title = tk.Label(
            self.content_frame,
            text="Welcome to DKI Engine",
            font=('Arial', 24, 'bold'),
            fg='#2c3e50'
        )
        title.pack(pady=(50, 30))
        
        # Subtitle
        subtitle = tk.Label(
            self.content_frame,
            text="Professional Investigation Reporting System",
            font=('Arial', 14),
            fg='#7f8c8d'
        )
        subtitle.pack(pady=(0, 40))
        
        # Welcome message
        welcome_text = """
This setup wizard will help you configure DKI Engine for first use.

We'll collect some basic information and help you set up your API keys 
for internet research capabilities.

The entire process takes about 5 minutes.

Click "Next" to begin setup.
        """.strip()
        
        message = tk.Label(
            self.content_frame,
            text=welcome_text,
            font=('Arial', 12),
            justify='center',
            wraplength=600
        )
        message.pack(pady=20)
        
        # Features list
        features_frame = ttk.LabelFrame(self.content_frame, text="What you'll get:", padding="20")
        features_frame.pack(pady=30, padx=50, fill='x')
        
        features = [
            "✓ Secure user profile with encrypted API key storage",
            "✓ Internet research capabilities (Google, Bing, Maps)",
            "✓ Professional report generation",
            "✓ Case management and file organization",
            "✓ Multi-format document processing (PDF, images, video)"
        ]
        
        for feature in features:
            feature_label = tk.Label(
                features_frame,
                text=feature,
                font=('Arial', 11),
                anchor='w'
            )
            feature_label.pack(fill='x', pady=2)
    
    def create_user_info_page(self):
        """Create user information page"""
        # Title
        title = tk.Label(
            self.content_frame,
            text="Create Your User Profile",
            font=('Arial', 18, 'bold'),
            fg='#2c3e50'
        )
        title.pack(pady=(20, 30))
        
        # Form frame
        form_frame = ttk.Frame(self.content_frame)
        form_frame.pack(pady=20, padx=100, fill='x')
        
        # Username (required)
        ttk.Label(form_frame, text="Username *", font=('Arial', 11, 'bold')).grid(row=0, column=0, sticky='w', pady=5)
        self.username_var = tk.StringVar()
        username_entry = ttk.Entry(form_frame, textvariable=self.username_var, width=30, font=('Arial', 11))
        username_entry.grid(row=0, column=1, sticky='ew', pady=5, padx=(10, 0))
        username_entry.focus()
        
        # Password (required)
        ttk.Label(form_frame, text="Password *", font=('Arial', 11, 'bold')).grid(row=1, column=0, sticky='w', pady=5)
        self.password_var = tk.StringVar()
        password_entry = ttk.Entry(form_frame, textvariable=self.password_var, show='*', width=30, font=('Arial', 11))
        password_entry.grid(row=1, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Confirm Password (required)
        ttk.Label(form_frame, text="Confirm Password *", font=('Arial', 11, 'bold')).grid(row=2, column=0, sticky='w', pady=5)
        self.confirm_password_var = tk.StringVar()
        confirm_entry = ttk.Entry(form_frame, textvariable=self.confirm_password_var, show='*', width=30, font=('Arial', 11))
        confirm_entry.grid(row=2, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Full Name
        ttk.Label(form_frame, text="Full Name", font=('Arial', 11)).grid(row=3, column=0, sticky='w', pady=5)
        self.full_name_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.full_name_var, width=30, font=('Arial', 11)).grid(row=3, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Email
        ttk.Label(form_frame, text="Email", font=('Arial', 11)).grid(row=4, column=0, sticky='w', pady=5)
        self.email_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.email_var, width=30, font=('Arial', 11)).grid(row=4, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Company
        ttk.Label(form_frame, text="Company", font=('Arial', 11)).grid(row=5, column=0, sticky='w', pady=5)
        self.company_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.company_var, width=30, font=('Arial', 11)).grid(row=5, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # License Number
        ttk.Label(form_frame, text="License Number", font=('Arial', 11)).grid(row=6, column=0, sticky='w', pady=5)
        self.license_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.license_var, width=30, font=('Arial', 11)).grid(row=6, column=1, sticky='ew', pady=5, padx=(10, 0))
        
        # Configure grid weights
        form_frame.columnconfigure(1, weight=1)
        
        # Required fields note
        note = tk.Label(
            self.content_frame,
            text="* Required fields",
            font=('Arial', 10),
            fg='#e74c3c'
        )
        note.pack(pady=(20, 0))
    
    def create_api_keys_page(self):
        """Create API keys configuration page"""
        # Title
        title = tk.Label(
            self.content_frame,
            text="Configure API Keys",
            font=('Arial', 18, 'bold'),
            fg='#2c3e50'
        )
        title.pack(pady=(20, 20))
        
        # Description
        desc = tk.Label(
            self.content_frame,
            text="Enter your API keys to enable internet research capabilities.\nYou can skip this step and add them later in Settings.",
            font=('Arial', 11),
            justify='center'
        )
        desc.pack(pady=(0, 20))
        
        # Create notebook for API key categories
        notebook = ttk.Notebook(self.content_frame)
        notebook.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Google Services tab
        google_frame = ttk.Frame(notebook, padding="20")
        notebook.add(google_frame, text="Google Services")
        
        # Google Search API
        ttk.Label(google_frame, text="Google Search API Key:", font=('Arial', 11, 'bold')).pack(anchor='w', pady=(0, 5))
        self.google_search_var = tk.StringVar()
        google_search_entry = ttk.Entry(google_frame, textvariable=self.google_search_var, width=60, font=('Arial', 10))
        google_search_entry.pack(fill='x', pady=(0, 10))
        
        ttk.Label(google_frame, text="Custom Search Engine ID:", font=('Arial', 11, 'bold')).pack(anchor='w', pady=(0, 5))
        self.google_engine_var = tk.StringVar()
        ttk.Entry(google_frame, textvariable=self.google_engine_var, width=60, font=('Arial', 10)).pack(fill='x', pady=(0, 10))
        
        ttk.Label(google_frame, text="Google Maps API Key:", font=('Arial', 11, 'bold')).pack(anchor='w', pady=(0, 5))
        self.google_maps_var = tk.StringVar()
        ttk.Entry(google_frame, textvariable=self.google_maps_var, width=60, font=('Arial', 10)).pack(fill='x', pady=(0, 10))
        
        # Google instructions
        google_info = tk.Text(google_frame, height=4, wrap='word', font=('Arial', 9))
        google_info.pack(fill='x', pady=(10, 0))
        google_info.insert('1.0', 
            "To get Google API keys:\n"
            "1. Go to Google Cloud Console (console.cloud.google.com)\n"
            "2. Create a project and enable Custom Search API and Maps API\n"
            "3. Create credentials and copy the API keys here"
        )
        google_info.config(state='disabled')
        
        # AI Services tab
        ai_frame = ttk.Frame(notebook, padding="20")
        notebook.add(ai_frame, text="AI Services")
        
        ttk.Label(ai_frame, text="OpenAI API Key (ChatGPT):", font=('Arial', 11, 'bold')).pack(anchor='w', pady=(0, 5))
        self.openai_var = tk.StringVar()
        ttk.Entry(ai_frame, textvariable=self.openai_var, width=60, font=('Arial', 10)).pack(fill='x', pady=(0, 10))
        
        ttk.Label(ai_frame, text="Google Gemini API Key:", font=('Arial', 11, 'bold')).pack(anchor='w', pady=(0, 5))
        self.gemini_var = tk.StringVar()
        ttk.Entry(ai_frame, textvariable=self.gemini_var, width=60, font=('Arial', 10)).pack(fill='x', pady=(0, 10))
        
        # AI instructions
        ai_info = tk.Text(ai_frame, height=4, wrap='word', font=('Arial', 9))
        ai_info.pack(fill='x', pady=(10, 0))
        ai_info.insert('1.0', 
            "AI API Keys for advanced analysis:\n"
            "• OpenAI: Get from platform.openai.com (for ChatGPT analysis)\n"
            "• Google Gemini: Get from ai.google.dev (for Google AI analysis)\n"
            "These enable intelligent document analysis and content generation."
        )
        ai_info.config(state='disabled')
        
        # Other Services tab
        other_frame = ttk.Frame(notebook, padding="20")
        notebook.add(other_frame, text="Other Services")
        
        ttk.Label(other_frame, text="Bing Search API Key:", font=('Arial', 11, 'bold')).pack(anchor='w', pady=(0, 5))
        self.bing_search_var = tk.StringVar()
        ttk.Entry(other_frame, textvariable=self.bing_search_var, width=60, font=('Arial', 10)).pack(fill='x', pady=(0, 10))
        
        ttk.Label(other_frame, text="Public Records API Key:", font=('Arial', 11, 'bold')).pack(anchor='w', pady=(0, 5))
        self.public_records_var = tk.StringVar()
        ttk.Entry(other_frame, textvariable=self.public_records_var, width=60, font=('Arial', 10)).pack(fill='x', pady=(0, 10))
        
        ttk.Label(other_frame, text="WhitePages API Key:", font=('Arial', 11, 'bold')).pack(anchor='w', pady=(0, 5))
        self.whitepages_var = tk.StringVar()
        ttk.Entry(other_frame, textvariable=self.whitepages_var, width=60, font=('Arial', 10)).pack(fill='x', pady=(0, 10))
        
        # Skip option
        skip_frame = ttk.Frame(self.content_frame)
        skip_frame.pack(pady=10)
        
        self.skip_api_var = tk.BooleanVar()
        skip_check = ttk.Checkbutton(
            skip_frame,
            text="Skip API key setup (I'll add them later)",
            variable=self.skip_api_var
        )
        skip_check.pack()
    
    def create_completion_page(self):
        """Create setup completion page"""
        # Title
        title = tk.Label(
            self.content_frame,
            text="Setup Complete!",
            font=('Arial', 24, 'bold'),
            fg='#27ae60'
        )
        title.pack(pady=(50, 30))
        
        # Success message
        message = tk.Label(
            self.content_frame,
            text="Your DKI Engine profile has been created successfully.",
            font=('Arial', 14),
            fg='#2c3e50'
        )
        message.pack(pady=(0, 30))
        
        # Summary frame
        summary_frame = ttk.LabelFrame(self.content_frame, text="Setup Summary", padding="20")
        summary_frame.pack(pady=20, padx=50, fill='x')
        
        # User info summary
        user_info = f"Username: {self.user_data.get('username', 'N/A')}\n"
        user_info += f"Full Name: {self.user_data.get('full_name', 'Not provided')}\n"
        user_info += f"Company: {self.user_data.get('company', 'Not provided')}\n"
        
        api_count = len([k for k in self.api_keys.values() if k.strip()])
        user_info += f"API Keys Configured: {api_count}"
        
        summary_label = tk.Label(
            summary_frame,
            text=user_info,
            font=('Arial', 11),
            justify='left',
            anchor='w'
        )
        summary_label.pack(fill='x')
        
        # Next steps
        next_steps = tk.Label(
            self.content_frame,
            text="Click 'Finish' to start using DKI Engine!",
            font=('Arial', 12, 'bold'),
            fg='#2c3e50'
        )
        next_steps.pack(pady=30)
    
    def validate_user_info(self) -> bool:
        """Validate user information"""
        username = self.username_var.get().strip()
        password = self.password_var.get()
        confirm_password = self.confirm_password_var.get()
        
        if not username:
            messagebox.showerror("Error", "Username is required")
            return False
        
        if len(username) < 3:
            messagebox.showerror("Error", "Username must be at least 3 characters")
            return False
        
        if not password:
            messagebox.showerror("Error", "Password is required")
            return False
        
        if len(password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters")
            return False
        
        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match")
            return False
        
        # Store user data
        self.user_data = {
            'username': username,
            'password': password,
            'email': self.email_var.get().strip(),
            'full_name': self.full_name_var.get().strip(),
            'company': self.company_var.get().strip(),
            'license_number': self.license_var.get().strip()
        }
        
        return True
    
    def collect_api_keys(self):
        """Collect API keys from form"""
        if self.skip_api_var.get():
            self.api_keys = {}
            return
        
        self.api_keys = {
            'google_search_api': self.google_search_var.get().strip(),
            'google_search_engine_id': self.google_engine_var.get().strip(),
            'google_maps_api': self.google_maps_var.get().strip(),
            'openai_api': self.openai_var.get().strip(),
            'google_gemini_api': self.gemini_var.get().strip(),
            'bing_search_api': self.bing_search_var.get().strip(),
            'public_records_api': self.public_records_var.get().strip(),
            'whitepages_api': self.whitepages_var.get().strip()
        }
    
    def go_back(self):
        """Go to previous page"""
        if self.current_page > 0:
            self.show_page(self.current_page - 1)
    
    def go_next(self):
        """Go to next page"""
        # Validate current page
        if self.current_page == 1:  # User info page
            if not self.validate_user_info():
                return
        elif self.current_page == 2:  # API keys page
            self.collect_api_keys()
        
        # Go to next page
        if self.current_page < len(self.pages) - 1:
            self.show_page(self.current_page + 1)
    
    def finish_setup(self):
        """Complete the setup process"""
        try:
            # Create user profile
            success = self.profile_manager.create_user(
                username=self.user_data['username'],
                password=self.user_data['password'],
                email=self.user_data['email'],
                full_name=self.user_data['full_name'],
                company=self.user_data['company'],
                license_number=self.user_data['license_number']
            )
            
            if not success:
                messagebox.showerror("Error", "Failed to create user profile")
                return
            
            # Authenticate user
            if not self.profile_manager.authenticate_user(
                self.user_data['username'], 
                self.user_data['password']
            ):
                messagebox.showerror("Error", "Failed to authenticate new user")
                return
            
            # Save API keys
            for service, key in self.api_keys.items():
                if key.strip():
                    self.profile_manager.save_api_key(service, key)
            
            # Setup complete
            logger.info(f"Setup completed for user: {self.user_data['username']}")
            
            # Close wizard window (not the main application!)
            if hasattr(self, 'wizard_window') and self.wizard_window:
                self.wizard_window.destroy()
            
            # Call completion callback
            if self.on_complete:
                self.on_complete(self.profile_manager)
            
        except Exception as e:
            logger.error(f"Setup failed: {str(e)}")
            messagebox.showerror("Error", f"Setup failed: {str(e)}")
    
    def run(self):
        """Run the setup wizard"""
        self.root.mainloop()


def run_setup_wizard(parent=None, on_complete=None):
    """Convenience function to run setup wizard"""
    wizard = SetupWizard(parent, on_complete)
    wizard.run()
    return wizard


if __name__ == "__main__":
    # Test the setup wizard
    logging.basicConfig(level=logging.INFO)
    
    def on_setup_complete(profile_manager):
        print("✅ Setup completed!")
        user_info = profile_manager.get_user_info()
        print(f"User: {user_info['username']}")
        api_keys = profile_manager.get_api_keys()
        print(f"API Keys: {len(api_keys)}")
    
    run_setup_wizard(on_complete=on_setup_complete)
