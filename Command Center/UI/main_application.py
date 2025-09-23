#!/usr/bin/env python3
"""
DKI Engine - Main Application Entry Point
Comprehensive reporting engine for investigation reports with OCR, AI, and multi-format input processing
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, List, Any, Optional
import json
from datetime import datetime
import threading
import logging
import socket
import urllib.request
import urllib.error

# Import our custom modules
from document_processor import DocumentProcessor
from gateway_controller import GatewayController
from master_toolkit_engine import MasterToolKitEngine
from report_generator import ReportGenerator
from file_drop_zone import FileDropZone
from repository_manager import RepositoryManager
from user_profile_manager import UserProfileManager
from setup_wizard import SetupWizard
from config import get_config
# Import Central Command Plugin
from central_plugin import central_plugin

# Import premium features
from printing_system import PrintingSystem
from template_system import TemplateSystem
from digital_signature_system import DigitalSignatureSystem
from watermark_system import WatermarkSystem

# Import network monitoring
from api_status_panel import APIStatusPanel
from api_tester import APITester

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dki_engine.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DKIEngineApp:
    """Main application class for the DKI Investigation Reporting Engine"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("DKI Engine - Investigation Report Generator")
        self.root.geometry("1400x900")
        self.root.configure(bg='#f0f0f0')
        
        # Load configuration
        self.config = get_config()
        
        # Initialize core components
        self.document_processor = DocumentProcessor()
        self.gateway_controller = GatewayController()
        self.toolkit_engine = MasterToolKitEngine()
        self.report_generator = ReportGenerator()
        self.repository_manager = RepositoryManager()
        
        # Initialize user profile manager with correct database path
        db_path = os.path.join(self.repository_manager.repo_root, "user_profiles.db")
        self.profile_manager = UserProfileManager(db_path)
        
        # Initialize premium features
        self.printing_system = PrintingSystem()
        self.template_system = TemplateSystem()
        self.signature_system = DigitalSignatureSystem()
        self.watermark_system = WatermarkSystem()
        
        # Initialize network monitoring
        self.api_tester = None
        self.api_status_panel = None
        
        # Application state
        self.current_case_id = None
        self.current_case = None
        self.case_metadata: Dict[str, Any] = {}
        self.uploaded_files = []
        self.section_data = {}
        self.report_type = tk.StringVar(value="Investigative")
        self.section_name_to_id: Dict[str, str] = {}
        
        # Setup UI first (keep original UI for now)
        self.setup_ui()
        
        # Then check for first-time setup (after UI is ready)
        self.root.after(100, self.check_first_time_setup)
        
        # Start internet connectivity monitoring
        self.root.after(2000, self.update_internet_status)  # Start after 2 seconds
        
        logger.info("DKI Engine Application initialized")
    
    def check_first_time_setup(self):
        """Check if this is first-time setup and run wizard if needed"""
        if not self.profile_manager.has_users():
            logger.info("No users found - running first-time setup")
            self.run_setup_wizard()
        else:
            logger.info("User profile exists - skipping setup wizard")
            # Show login dialog
            self.show_login_dialog()
    
    def run_setup_wizard(self):
        """Run the first-time setup wizard"""
        def on_setup_complete(profile_manager):
            self.profile_manager = profile_manager
            # Connect profile manager to toolkit engine for API keys
            self.toolkit_engine.set_user_profile_manager(profile_manager)
            logger.info("Setup completed successfully")
        
        db_path = os.path.join(self.repository_manager.repo_root, "user_profiles.db")
        wizard = SetupWizard(self.root, on_setup_complete, db_path)
        wizard.run()
    
    def show_login_dialog(self):
        """Show login dialog for existing users"""
        login_window = tk.Toplevel(self.root)
        login_window.title("DKI Engine - Login")
        login_window.geometry("400x300")
        login_window.resizable(False, False)
        
        # Center window
        login_window.update_idletasks()
        x = (login_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (login_window.winfo_screenheight() // 2) - (300 // 2)
        login_window.geometry(f"400x300+{x}+{y}")
        
        # Make modal
        login_window.transient(self.root)
        login_window.grab_set()
        
        # Login form
        main_frame = ttk.Frame(login_window, padding="30")
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title = tk.Label(main_frame, text="Welcome to DKI Engine", font=('Arial', 16, 'bold'))
        title.pack(pady=(0, 30))
        
        # Username
        ttk.Label(main_frame, text="Username:", font=('Arial', 11)).pack(anchor='w')
        username_var = tk.StringVar()
        username_entry = ttk.Entry(main_frame, textvariable=username_var, width=30, font=('Arial', 11))
        username_entry.pack(fill='x', pady=(5, 15))
        username_entry.focus()
        
        # Password
        ttk.Label(main_frame, text="Password:", font=('Arial', 11)).pack(anchor='w')
        password_var = tk.StringVar()
        password_entry = ttk.Entry(main_frame, textvariable=password_var, show='*', width=30, font=('Arial', 11))
        password_entry.pack(fill='x', pady=(5, 20))
        
        # Error label
        error_var = tk.StringVar()
        error_label = tk.Label(main_frame, textvariable=error_var, fg='red', font=('Arial', 10))
        error_label.pack(pady=(0, 10))
        
        def do_login():
            username = username_var.get().strip()
            password = password_var.get()
            
            if not username or not password:
                error_var.set("Please enter both username and password")
                return
            
            if self.profile_manager.authenticate_user(username, password):
                # Connect profile manager to toolkit engine for API keys
                self.toolkit_engine.set_user_profile_manager(self.profile_manager)
                try:
                    # Prompt for API keys if missing
                    self._ensure_api_keys_after_login()
                except Exception:
                    pass
                login_window.destroy()
                logger.info(f"User {username} logged in successfully")
            else:
                error_var.set("Invalid username or password")
        
        def on_enter(event):
            do_login()
        
        # Bind Enter key
        password_entry.bind('<Return>', on_enter)
        username_entry.bind('<Return>', on_enter)
        
        # Login button
        login_btn = ttk.Button(main_frame, text="Login", command=do_login)
        login_btn.pack(pady=10)
        
        # New user button
        def create_new_user():
            login_window.destroy()
            self.run_setup_wizard()
        
        new_user_btn = ttk.Button(main_frame, text="Create New User", command=create_new_user)
        new_user_btn.pack(pady=5)

    def _ensure_api_keys_after_login(self):
        """If key services are missing keys, prompt user to enter them."""
        try:
            from api_key_dialog import APIKeyDialog
        except Exception:
            return
        if not self.profile_manager or not self.profile_manager.is_authenticated():
            return
        keys = {}
        try:
            keys = self.profile_manager.get_api_keys() or {}
        except Exception:
            keys = {}
        missing = []
        required = ['openai_api', 'microsoft_copilot_api', 'google_gemini_api', 'google_search_api', 'google_search_engine_id', 'google_maps_api', 'bing_search_api', 'public_records_api', 'whitepages_api']
        for svc in required:
            v = keys.get(svc) or keys.get(svc + '_key')
            if not v:
                missing.append(svc)
        if missing:
            APIKeyDialog(self.root, self.profile_manager, required_services=required)
            # Reconnect to propagate any new keys to toolkit engine
            try:
                self.toolkit_engine.set_user_profile_manager(self.profile_manager)
            except Exception:
                pass
        
        # Initialize API monitoring after login
        self.initialize_api_monitoring()
    
    def setup_ui(self):
        """Setup the main user interface"""
        
        # Main menu
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Case", command=self.new_case)
        file_menu.add_command(label="Load Case", command=self.load_case)
        file_menu.add_command(label="Save Case", command=self.save_case)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # User menu
        user_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="User", menu=user_menu)
        user_menu.add_command(label="Profile & API Settings", command=self.show_profile_settings)
        user_menu.add_separator()
        user_menu.add_command(label="Logout", command=self.logout_user)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="OCR Settings", command=self.ocr_settings)
        tools_menu.add_command(label="AI Configuration", command=self.ai_config)
        tools_menu.add_command(label="API Status Monitor", command=self.show_api_status_monitor)
        tools_menu.add_separator()
        tools_menu.add_command(label="Print Report", command=self.print_report)
        tools_menu.add_command(label="Digital Signature", command=self.show_signature_dialog)
        tools_menu.add_command(label="Add Watermark", command=self.show_watermark_dialog)
        tools_menu.add_command(label="Template Editor", command=self.show_template_editor)
        tools_menu.add_command(label="Export Settings", command=self.export_settings)
        tools_menu.add_separator()
        tools_menu.add_command(label="Light Mode", command=lambda: self._apply_theme_main('light'))
        tools_menu.add_command(label="Dark Mode", command=lambda: self._apply_theme_main('dark'))
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        header_frame.columnconfigure(1, weight=1)  # Make middle column expandable
        
        ttk.Label(header_frame, text="DKI Investigation Reporting Engine", 
                 font=('Arial', 16, 'bold')).grid(row=0, column=0, sticky=tk.W)
        
        # Internet connectivity status
        self.internet_status = tk.StringVar(value="🔄 Checking connection...")
        status_label = ttk.Label(header_frame, textvariable=self.internet_status, 
                               font=('Arial', 10), foreground='blue')
        status_label.grid(row=0, column=2, sticky=tk.E, padx=(10, 0))
        
        # Report type selection
        ttk.Label(header_frame, text="Report Type:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        report_combo = ttk.Combobox(header_frame, textvariable=self.report_type, 
                                   values=["Investigative", "Surveillance", "Hybrid"])
        report_combo.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=(5, 0))
        report_combo.bind('<<ComboboxSelected>>', self.on_report_type_change)
        
        # Left panel - File management with drop zone
        left_panel = ttk.LabelFrame(main_frame, text="Document Management", padding="10")
        left_panel.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        left_panel.columnconfigure(0, weight=1)
        left_panel.rowconfigure(0, weight=1)
        
        # File drop zone
        self.drop_zone = FileDropZone(
            left_panel,
            on_files_dropped=self.on_files_dropped
        )
        self.drop_zone.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Process files button
        ttk.Button(left_panel, text="Process All Files", 
                  command=self.process_files).grid(row=1, column=0, sticky=(tk.W, tk.E), pady=10)
        
        # Right panel - Report generation
        right_panel = ttk.LabelFrame(main_frame, text="Report Generation", padding="10")
        right_panel.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(1, weight=1)
        
        # Section selection
        sections_frame = ttk.Frame(right_panel)
        sections_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        sections_frame.columnconfigure(1, weight=1)
        
        ttk.Label(sections_frame, text="Current Section:").grid(row=0, column=0, sticky=tk.W)
        self.current_section = tk.StringVar(value="Section 1 - Investigation Objectives")
        self.section_combo = ttk.Combobox(sections_frame, textvariable=self.current_section, 
                                         state="readonly", width=40)
        self.section_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0))
        
        # Section content area
        content_frame = ttk.Frame(right_panel)
        content_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(0, weight=1)
        
        self.section_text = tk.Text(content_frame, wrap=tk.WORD, height=20)
        text_scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=self.section_text.yview)
        self.section_text.configure(yscrollcommand=text_scrollbar.set)
        
        self.section_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        text_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Control buttons
        button_frame = ttk.Frame(right_panel)
        button_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Button(button_frame, text="Generate Section", 
                  command=self.generate_section).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(button_frame, text="Review Section", 
                  command=self.review_section).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Next Section", 
                  command=self.next_section).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="Generate Full Report", 
                  command=self.generate_full_report).grid(row=0, column=3, padx=(5, 0))
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Initialize section list
        self.update_section_list()
    
    def update_section_list(self):
        """Update the section dropdown based on report type"""
        report_type = self.report_type.get()
        sections_info = self.gateway_controller.report_types.get(report_type, {}).get('sections', [])
        display_names = [name for _, name in sections_info]
        self.section_name_to_id = {name: section_id for section_id, name in sections_info}
        self.section_combo['values'] = display_names
        if display_names:
            self.section_combo.set(display_names[0])
        elif self.section_combo['values']:
            self.section_combo.set(self.section_combo['values'][0])
    
    def _build_case_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        case_name = self.case_metadata.get('case_name') or self.current_case_id or 'ACTIVE_CASE'
        payload['case_name'] = case_name
        payload['client_profile'] = self.case_metadata.get('client_profile', {}).copy()
        if self.current_case_id:
            payload['case_id'] = self.current_case_id
        if 'report_type' in self.case_metadata:
            payload['report_type'] = self.case_metadata['report_type']
        return payload

    def _ensure_gateway_case_initialized(self, override_report_type: Optional[str] = None):
        desired_type = override_report_type or self.report_type.get()
        if desired_type:
            self.case_metadata['report_type'] = desired_type
        current_type = getattr(self.gateway_controller, 'current_report_type', None)
        if current_type != desired_type:
            try:
                payload = self._build_case_payload()
                self.gateway_controller.initialize_case(desired_type, payload)
            except Exception as exc:
                logger.warning(f"Gateway initialization skipped: {exc}")

    def on_report_type_change(self, event=None):
        """Handle report type change"""
        self.update_section_list()
        self.case_metadata['report_type'] = self.report_type.get()
        self._ensure_gateway_case_initialized()
        self.status_var.set(f"Report type changed to {self.report_type.get()}")
    
    def new_case(self):
        """Start a new case"""
        if self.current_case_id and messagebox.askyesno("New Case", "Start a new case? Current work will be saved automatically."):
            # Auto-save current case
            self.auto_save_case()
        
        # Create new case dialog
        dialog = NewCaseDialog(self.root, self.repository_manager)
        if dialog.result:
            case_info = dialog.result
            self.case_metadata = {
                'case_name': case_info['case_name'],
                'report_type': case_info['report_type'],
                'client_profile': case_info.get('client_info', {}).copy()
            }
            self.current_case = None
            self.gateway_controller.reset_gateway()

            # Create new case in repository
            self.current_case_id = self.repository_manager.create_case(
                case_info['case_name'],
                case_info['report_type'],
                case_info['client_info']
            )
            self.case_metadata['case_id'] = self.current_case_id
            
            # Update UI
            self.report_type.set(case_info['report_type'])
            self._ensure_gateway_case_initialized(case_info['report_type'])
            self.uploaded_files.clear()
            self.section_data.clear()
            self.drop_zone.set_files([])
            self.section_text.delete(1.0, tk.END)
            self.update_section_list()
            
            # Enable file upload and show next step guidance
            # Note: File upload is handled by the drop zone - no separate button needed
            self.status_var.set(f"✅ New case created: {self.current_case_id} - Ready for file upload")
            
            # Show next step guidance
            messagebox.showinfo("Case Created", 
                              f"✅ Case '{case_info['case_name']}' created successfully!\n\n"
                              f"📁 Next: Upload files using the file drop zone or 'Browse Files' button.\n"
                              f"📝 Then click 'Process All Files' to begin analysis.")
            
            logger.info(f"New case created: {self.current_case_id} - File upload enabled")
    
    def load_case(self):
        """Load an existing case"""
        filename = filedialog.askopenfilename(
            title="Load Case",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r') as f:
                    case_data = json.load(f)
                
                self.current_case = filename
                self.case_metadata = case_data.get('case_metadata', {
                    'case_name': case_data.get('case_name', os.path.splitext(os.path.basename(filename))[0]),
                    'client_profile': case_data.get('client_info', {})
                })
                if 'report_type' not in self.case_metadata:
                    self.case_metadata['report_type'] = case_data.get('report_type', 'Investigative')
                self.current_case_id = case_data.get('case_id', self.current_case_id)
                if self.current_case_id:
                    self.case_metadata['case_id'] = self.current_case_id
                self.gateway_controller.reset_gateway()
                self.report_type.set(self.case_metadata.get('report_type', 'Investigative'))
                self._ensure_gateway_case_initialized()
                self.uploaded_files = case_data.get('uploaded_files', [])
                self.section_data = case_data.get('section_data', {})
                
                # Update UI
                self.update_section_list()
                self.files_listbox.delete(0, tk.END)
                for file_info in self.uploaded_files:
                    self.files_listbox.insert(tk.END, f"{file_info['type']}: {file_info['name']}")
                
                self.status_var.set(f"Case loaded: {os.path.basename(filename)}")
                logger.info(f"Case loaded: {filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load case: {str(e)}")
                logger.error(f"Failed to load case: {str(e)}")
    
    def save_case(self):
        """Save the current case"""
        if not self.current_case:
            filename = filedialog.asksaveasfilename(
                title="Save Case",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if not filename:
                return
            self.current_case = filename
        
        try:
            case_data = {
                'report_type': self.report_type.get(),
                'uploaded_files': self.uploaded_files,
                'section_data': self.section_data,
                'case_metadata': self.case_metadata,
                'case_id': self.current_case_id,
                'case_name': self.case_metadata.get('case_name'),
                'created_date': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            with open(self.current_case, 'w') as f:
                json.dump(case_data, f, indent=2)
            
            self.status_var.set(f"Case saved: {os.path.basename(self.current_case)}")
            logger.info(f"Case saved: {self.current_case}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save case: {str(e)}")
            logger.error(f"Failed to save case: {str(e)}")
    
    def on_files_dropped(self, files):
        """Handle files dropped in the drop zone"""
        self.uploaded_files = files
        
        if files and self.current_case_id:
            # Save files to case repository
            self.repository_manager.save_case_files(self.current_case_id, files)
            self.status_var.set(f"Added {len(files)} files to case")
        elif files:
            self.status_var.set(f"Files ready - Create a case to save them")
        else:
            self.status_var.set("Ready")
    
    def process_files(self):
        """Process all uploaded files with integrated media processing"""
        if not self.uploaded_files:
            messagebox.showwarning("Warning", "No files to process")
            return
        
        self.status_var.set("Processing files...")
        self._ensure_gateway_case_initialized()
        
        def process_thread():
            try:
                # Process files in background thread
                processed_data = self.document_processor.process_files(self.uploaded_files)
                
                # Check for media files and process them
                media_files = []
                for file_info in self.uploaded_files:
                    file_path = file_info['path'] if isinstance(file_info, dict) else file_info
                    if self._is_media_file(file_path):
                        media_files.append(file_path)
                
                if media_files:
                    logger.info(f"Found {len(media_files)} media files for processing")
                    self.status_var.set(f"Processing {len(media_files)} media files...")
                    
                    # Process media files using the gateway controller's media engine
                    try:
                        media_results = self.gateway_controller.media_engine.process_media_batch(media_files, {
                            'extract_text': True,
                            'detect_faces': True,
                            'extract_frames': True,
                            'frame_count': 5,
                            'analyze_audio': True,
                            'detect_motion': True
                        })
                        
                        # Add media results to processed data
                        processed_data['media_processing_results'] = media_results
                        processed_data['media_files_processed'] = len(media_files)

                        self._merge_audio_results(processed_data, media_results)
                        
                        logger.info(f"Media processing completed: {len(media_results)} files processed")
                        
                    except Exception as e:
                        logger.error(f"Media processing failed: {e}")
                        processed_data['media_processing_error'] = str(e)
                
                # Update UI in main thread
                self.root.after(0, lambda: self.on_files_processed(processed_data))
                
            except Exception as e:
                error_msg = str(e)  # Capture error in local scope
                self.root.after(0, lambda: self.on_processing_error(error_msg))
        
        threading.Thread(target=process_thread, daemon=True).start()
    
    def _merge_audio_results(self, processed_data: Dict[str, Any], media_results: Dict[str, Any]):
        '''Attach media-engine audio outputs (transcripts, metadata) to processed data.'''
        if not media_results:
            return

        audio_bucket = processed_data.setdefault('audio', {})
        files_bucket = processed_data.get('files', {})

        path_to_id: Dict[str, str] = {}
        for file_id, record in files_bucket.items():
            info = (record or {}).get('file_info', {})
            media_path = info.get('path') if isinstance(info, dict) else None
            if media_path:
                path_to_id[media_path] = file_id

        for file_id, record in audio_bucket.items():
            info = (record or {}).get('file_info', {})
            media_path = info.get('path') if isinstance(info, dict) else None
            if media_path and media_path not in path_to_id:
                path_to_id[media_path] = file_id

        for media_path, result in media_results.items():
            if not isinstance(result, dict):
                continue
            if result.get('file_type') != 'audio':
                continue

            clip_payload: Dict[str, Any] = {
                'file_info': result.get('file_info'),
                'duration': result.get('duration'),
                'sample_rate': result.get('sample_rate'),
                'channels': result.get('channels'),
                'transcript': result.get('transcript'),
                'transcription': result.get('transcription'),
                'transcription_segments': result.get('transcription_segments'),
                'transcription_model': result.get('transcription_model'),
                'transcription_generated_at': result.get('transcription_generated_at'),
            }

            transcription_payload = result.get('transcription')
            if isinstance(transcription_payload, dict):
                summary = transcription_payload.get('summary') or transcription_payload.get('text')
                if summary:
                    clip_payload['summary'] = summary

            file_id = path_to_id.get(media_path)
            if not file_id:
                file_info = result.get('file_info') or {}
                uploaded = file_info.get('uploaded_date') or datetime.now().isoformat()
                name = file_info.get('name') or os.path.basename(media_path)
                file_id = self.document_processor._generate_file_id({
                    'name': name,
                    'path': media_path,
                    'uploaded_date': uploaded
                })
                path_to_id[media_path] = file_id

            audio_bucket[file_id] = clip_payload

    def _is_media_file(self, file_path: str) -> bool:
        """Check if a file is a media file (image or video)"""
        media_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp',
                          '.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm', '.m4v',
                          '.mp3', '.wav', '.m4a', '.aac', '.ogg', '.wma', '.flac'}
        
        file_ext = os.path.splitext(file_path.lower())[1]
        return file_ext in media_extensions
    
    def on_files_processed(self, processed_data):
        """Handle completion of file processing"""
        self.section_data['processed_files'] = processed_data
        self.status_var.set("Files processed successfully - Ready for section generation")
        
        # Auto-enable section generation
        self.update_section_list()
        # Note: Section generation is handled through the section list interface
        
        # Show next step guidance
        messagebox.showinfo("Next Step", 
                          f"✅ Processed {len(processed_data)} files successfully!\n\n"
                          f"📝 Next: Select a section and click 'Generate Section' to begin report generation.")
        
        logger.info(f"Processed {len(processed_data)} files - Section generation enabled")
    
    def on_processing_error(self, error_msg):
        """Handle file processing error"""
        self.status_var.set("File processing failed")
        messagebox.showerror("Error", f"File processing failed: {error_msg}")
        logger.error(f"File processing failed: {error_msg}")
    
    def generate_section(self):
        """Generate the current section"""
        current_section = (self.current_section.get() or '').strip()
        if not current_section:
            values = list(self.section_combo['values'])
            if values:
                current_section = values[0]
                self.current_section.set(current_section)
        self._ensure_gateway_case_initialized()
        self.status_var.set(f"Generating {current_section}...")
        
        def generate_thread():
            try:
                # Get processed data
                processed_data = self.section_data.get('processed_files', {})
                
                # For Section 8, prompt for manual notes per video item (max 150 chars)
                if isinstance(current_section, str) and 'section 8' in current_section.lower():
                    try:
                        manual_notes = self._prompt_video_notes(processed_data)
                        if manual_notes:
                            processed_data['manual_notes'] = manual_notes
                            # Persist updated processed data back
                            self.section_data['processed_files'] = processed_data
                    except Exception as e:
                        logger.warning(f"Media notes prompt skipped: {e}")
                
                # Generate section using gateway controller
                section_result = self.gateway_controller.generate_section(
                    current_section, 
                    processed_data, 
                    self.report_type.get()
                )
                
                # Update UI in main thread
                self.root.after(0, lambda: self.on_section_generated(current_section, section_result))
                
            except Exception as e:
                error_msg = str(e)  # Capture error in local scope
                self.root.after(0, lambda: self.on_generation_error(error_msg))
        
        threading.Thread(target=generate_thread, daemon=True).start()

    def _prompt_video_notes(self, processed_data: Dict[str, Any]) -> Dict[str, str]:
        """Prompt the user to add brief notes under each video (<=150 chars)."""
        videos = list((processed_data.get('videos') or {}).items())
        media = videos
        if not media:
            return {}
        
        # Build a simple modal dialog stepping through items
        notes: Dict[str, str] = {}
        idx = 0
        
        dlg = tk.Toplevel(self.root)
        dlg.title("Section 8 Video Notes")
        dlg.geometry("600x240")
        dlg.transient(self.root)
        dlg.grab_set()
        
        lbl_title = ttk.Label(dlg, text="Add a short note for each video (optional)", font=('Arial', 12, 'bold'))
        lbl_title.pack(pady=(10, 10))
        
        var_label = tk.StringVar()
        lbl_item = ttk.Label(dlg, textvariable=var_label)
        lbl_item.pack(pady=(0, 8))
        
        var_text = tk.StringVar()
        entry = ttk.Entry(dlg, textvariable=var_text, width=70)
        entry.pack(pady=(0, 10))
        
        info = ttk.Label(dlg, text="Max 150 chars. Leave blank to skip.")
        info.pack()
        
        btn_frame = ttk.Frame(dlg)
        btn_frame.pack(pady=(10, 10))
        
        def update_view():
            if idx < len(media):
                mid, data = media[idx]
                name = (data.get('file_info', {}) or {}).get('name') or mid
                var_label.set(f"Video: {name}")
                var_text.set(notes.get(mid, ''))
                entry.icursor(tk.END)
                entry.focus_set()
            else:
                dlg.destroy()
        
        def on_next():
            nonlocal idx
            txt = var_text.get().strip()
            if len(txt) > 150:
                txt = txt[:150]
            if txt:
                mid = media[idx][0]
                notes[mid] = txt
            idx += 1
            update_view()
        
        def on_skip():
            nonlocal idx
            idx += 1
            update_view()
        
        def on_finish():
            dlg.destroy()
        
        ttk.Button(btn_frame, text="Next", command=on_next).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Skip", command=on_skip).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Finish", command=on_finish).pack(side='left', padx=5)
        
        # Allow Enter for Next
        dlg.bind('<Return>', lambda e: on_next())
        
        update_view()
        self.root.wait_window(dlg)
        return notes
    
    def on_section_generated(self, section_name, section_result):
        """Handle completion of section generation"""
        self.section_data[section_name] = section_result
        self.section_text.delete(1.0, tk.END)
        self.section_text.insert(1.0, section_result.get('content', ''))
        self.status_var.set(f"{section_name} generated successfully")
        logger.info(f"{section_name} generated")
    
    def on_generation_error(self, error_msg):
        """Handle section generation error"""
        self.status_var.set("Section generation failed")
        messagebox.showerror("Error", f"Section generation failed: {error_msg}")
        logger.error(f"Section generation failed: {error_msg}")
    
    def review_section(self):
        """Review the current section"""
        current_section = self.current_section.get()
        content = self.section_text.get(1.0, tk.END).strip()
        
        if not content:
            messagebox.showwarning("Warning", "No content to review")
            return
        
        # Show review dialog
        result = messagebox.askyesnocancel(
            "Section Review",
            f"Review {current_section}:\n\nApprove this section?",
            icon='question'
        )
        
        if result is True:  # Yes - approve
            try:
                # Notify gateway for approval gating and assembly caching
                self.gateway_controller.approve_section(current_section)
            except Exception as e:
                logger.warning(f"Gateway approval error: {e}")
            self.section_data[current_section + '_approved'] = True
            self.status_var.set(f"{current_section} approved")
            logger.info(f"{current_section} approved")
        elif result is False:  # No - needs revision
            self.status_var.set(f"{current_section} needs revision")
            logger.info(f"{current_section} flagged for revision")
        # Cancel - do nothing
    
    def next_section(self):
        """Move to the next section"""
        sections = list(self.section_combo['values'])
        current = self.current_section.get()
        
        if current in sections:
            current_idx = sections.index(current)
            if current_idx < len(sections) - 1:
                next_section = sections[current_idx + 1]
                self.current_section.set(next_section)
                
                # Load section content if it exists
                if next_section in self.section_data:
                    content = self.section_data[next_section].get('content', '')
                    self.section_text.delete(1.0, tk.END)
                    self.section_text.insert(1.0, content)
                else:
                    self.section_text.delete(1.0, tk.END)
                
                self.status_var.set(f"Moved to {next_section}")
            else:
                messagebox.showinfo("Info", "This is the last section")
    
    def generate_full_report(self):
        """Generate the complete report"""
        if not self.section_data:
            messagebox.showwarning("Warning", "No section data available")
            return
        
        self.status_var.set("Generating full report...")
        
        def generate_thread():
            try:
                # Generate full report
                report_result = self.report_generator.generate_full_report(
                    self.section_data,
                    self.report_type.get()
                )
                
                # Update UI in main thread
                self.root.after(0, lambda: self.on_full_report_generated(report_result))
                
            except Exception as e:
                error_msg = str(e)  # Capture error in local scope
                self.root.after(0, lambda: self.on_generation_error(error_msg))
        
        threading.Thread(target=generate_thread, daemon=True).start()
    
    def on_full_report_generated(self, report_result):
        """Handle completion of full report generation"""
        self.status_var.set("Full report generated successfully")
        
        # Show export options
        export_options = ["PDF", "DOCX", "Both"]
        choice = messagebox.askyesnocancel(
            "Export Report",
            "Report generated successfully!\n\nExport as PDF?",
            icon='question'
        )
        
        if choice is not None:
            export_format = "pdf" if choice else "docx"
            self.export_report(report_result, export_format)
    
    def export_report(self, report_data, format_type):
        """Export the report in specified format"""
        filename = filedialog.asksaveasfilename(
            title="Export Report",
            defaultextension=f".{format_type}",
            filetypes=[(f"{format_type.upper()} files", f"*.{format_type}")]
        )
        
        if filename:
            try:
                self.report_generator.export_report(report_data, filename, format_type)
                self.status_var.set(f"Report exported: {os.path.basename(filename)}")
                messagebox.showinfo("Success", f"Report exported successfully to {filename}")
                logger.info(f"Report exported: {filename}")
                try:
                    self._save_audit_artifacts(report_data, filename)
                except Exception as e:
                    logger.warning(f"Audit save failed: {e}")
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {str(e)}")
                logger.error(f"Export failed: {str(e)}")

    def _save_audit_artifacts(self, report_data, report_filename):
        """Save admin-facing audit bundle alongside the exported report for authenticity.
        This includes processing logs, lookup cache, and per-section internal audits.
        """
        import json, os
        base, _ = os.path.splitext(report_filename)
        audit_path = base + "_audit.json"
        # Collect section internal audits
        sections = []
        try:
            for sec in report_data.get('sections', []) or []:
                entry = {
                    'section_id': sec.get('section_id'),
                    'section_name': sec.get('section_name'),
                }
                rd = sec.get('render_data') or {}
                manifest = rd.get('manifest') or {}
                # Identity & continuity sidebars
                if 'internal_identity_verification' in manifest:
                    entry['internal_identity_verification'] = manifest.get('internal_identity_verification')
                if 'internal_sidebar' in manifest:
                    entry['internal_sidebar'] = manifest.get('internal_sidebar')
                # Mileage audit if present on this section
                if 'internal_mileage_audit' in sec:
                    entry['internal_mileage_audit'] = sec.get('internal_mileage_audit')
                sections.append(entry)
        except Exception:
            pass

        # Processing log and cache
        try:
            processing_log = self.gateway_controller.get_processing_log()
        except Exception:
            processing_log = []
        try:
            lookup_cache = getattr(self.gateway_controller, 'lookup_cache', {})
        except Exception:
            lookup_cache = {}

        # User and profile
        try:
            user = self.profile_manager.get_user_info() or {}
            role = self.profile_manager.get_current_role() or 'user'
            auto_open = self.profile_manager.get_setting('auto_open_admin_audit')
        except Exception:
            user, role, auto_open = {}, 'user', None

        # Compute basic flag count to update user stats
        flags_count = 0
        try:
            for entry in sections:
                idv = entry.get('internal_identity_verification')
                if isinstance(idv, dict) and idv.get('verified') is False:
                    flags_count += 1
                ms = entry.get('internal_mileage_audit', {})
                if isinstance(ms, dict):
                    for a in ms.get('audits', []) or []:
                        if a.get('error'):
                            flags_count += 1
                side = entry.get('internal_sidebar', {})
                if isinstance(side, dict):
                    counts = side.get('counts', {})
                    if counts.get('windows', 0) > 0 and counts.get('matches', 0) == 0:
                        flags_count += 1
        except Exception:
            pass

        bundle = {
            'report_file': os.path.basename(report_filename),
            'generated_timestamp': report_data.get('metadata', {}).get('generated_timestamp'),
            'case_id': report_data.get('metadata', {}).get('case_id'),
            'user': user,
            'user_role': role,
            'profile_settings': {
                'auto_open_admin_audit': auto_open
            },
            'processing_log': processing_log,
            'lookup_cache': lookup_cache,
            'sections': sections,
            'flags_count': flags_count,
        }
        with open(audit_path, 'w', encoding='utf-8') as f:
            json.dump(bundle, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"Audit bundle saved to {audit_path}")

        # Update user stats if flags present
        try:
            if flags_count > 0 and self.profile_manager and self.profile_manager.is_authenticated():
                self.profile_manager.increment_setting_int('audit_flags_total', flags_count)
                self.profile_manager.increment_setting_int('audit_flagged_reports_total', 1)
        except Exception as e:
            logger.warning(f"Failed to update user audit stats: {e}")

    def export_final_bundle(self):
        """Prompt for a destination folder and export a final bundle:
        - Creates 'Final Report' and 'Audit Trail' subfolders
        - Exports DOCX, PDF, and RTF to Final Report
        - Writes audit JSON to Audit Trail
        - Creates Final_Bundle.zip containing both
        """
        from tkinter import filedialog
        import os, zipfile, datetime
        # Generate full report first
        try:
            report_data = self.report_generator.generate_full_report(self.section_data, self.report_type.get())
        except Exception as e:
            messagebox.showerror("Final Export", f"Failed to generate full report: {e}")
            return
        target_dir = filedialog.askdirectory(title="Select Final Export Folder")
        if not target_dir:
            return
        final_dir = os.path.join(target_dir, 'Final Report')
        audit_dir = os.path.join(target_dir, 'Audit Trail')
        os.makedirs(final_dir, exist_ok=True)
        os.makedirs(audit_dir, exist_ok=True)
        # Base name
        meta = report_data.get('metadata', {})
        base = f"{meta.get('case_id','Report')}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        pdf_path = os.path.join(final_dir, base + '.pdf')
        docx_path = os.path.join(final_dir, base + '.docx')
        rtf_path = os.path.join(final_dir, base + '.rtf')
        # Export
        try:
            self.report_generator.export_report(report_data, pdf_path, 'pdf')
        except Exception as e:
            logger.warning(f"PDF export failed: {e}")
        try:
            self.report_generator.export_report(report_data, docx_path, 'docx')
        except Exception as e:
            logger.warning(f"DOCX export failed: {e}")
        try:
            self.report_generator.export_rtf(report_data, rtf_path)
        except Exception as e:
            logger.warning(f"RTF export failed: {e}")
        # Audit bundle into audit_dir
        try:
            audit_path = os.path.join(audit_dir, base + '_audit.json')
            # Reuse logic but target path directly
            report_filename = os.path.join(final_dir, base + '.pdf')
            # Save using existing builder then move
            self._save_audit_artifacts(report_data, report_filename)
            # Move file if different destination
            default_audit = os.path.splitext(report_filename)[0] + '_audit.json'
            if os.path.exists(default_audit) and default_audit != audit_path:
                try:
                    import shutil
                    shutil.move(default_audit, audit_path)
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"Failed to save audit bundle: {e}")
        # Zip bundle
        try:
            bundle_zip = os.path.join(target_dir, 'Final_Bundle.zip')
            with zipfile.ZipFile(bundle_zip, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
                for root, _, files in os.walk(final_dir):
                    for fn in files:
                        full = os.path.join(root, fn)
                        arc = os.path.relpath(full, target_dir)
                        zf.write(full, arc)
                for root, _, files in os.walk(audit_dir):
                    for fn in files:
                        full = os.path.join(root, fn)
                        arc = os.path.relpath(full, target_dir)
                        zf.write(full, arc)
            logger.info(f"Bundle zip created: {bundle_zip}")
            messagebox.showinfo("Final Export", f"Final export bundle created:\n{target_dir}")
        except Exception as e:
            logger.warning(f"Failed to create bundle zip: {e}")

    def _apply_theme_main(self, mode: str):
        # Basic background switcher for main window
        try:
            if mode == 'dark':
                self.root.configure(bg='#1e1e1e')
            else:
                self.root.configure(bg='#ffffff')
        except Exception:
            pass

    def reset_for_new_case(self):
        """Clear current case state and reset gateway for a new case."""
        try:
            self.gateway_controller.reset_gateway()
        except Exception:
            pass
        self.current_case_id = None
        self.uploaded_files = []
        self.section_data = {}
        try:
            self.status_var.set("Ready for a new case")
        except Exception:
            pass
        try:
            self.section_text.delete(1.0, tk.END)
        except Exception:
            pass

    # ---------------- Auto Run Orchestration ---------------- #
    def start_autorun(self, mode: str):
        """Start automatic section generation per selected mode.
        Modes: 'Semi-Auto' (pause after each section), '3/4 Auto' (pause after Sec 5), 'Full Auto' (pause at end).
        """
        import threading
        self.status_var.set(f"Auto Run: {mode}")
        def run():
            try:
                processed_data = self.section_data.get('processed_files', {})
                if not processed_data:
                    self.root.after(0, lambda: messagebox.showwarning("Auto Run", "Please process files before starting auto run."))
                    return
                report_type = self.report_type.get()
                sections = self.gateway_controller.report_types[report_type]['sections']
                pause_every = (mode == 'Semi-Auto')
                pause_at_5 = (mode == '3/4 Auto')
                pause_at_end = (mode == 'Full Auto')
                for sid, name in sections:
                    try:
                        sec_result = self.gateway_controller.generate_section(name, processed_data, report_type)
                    except Exception as e:
                        error_msg = str(e)  # Capture error in local scope
                        self.root.after(0, lambda: self.on_generation_error(error_msg))
                        return
                    self.root.after(0, lambda n=name, r=sec_result: self.on_section_generated(n, r))

                    do_pause = False
                    if pause_every:
                        do_pause = True
                    elif pause_at_5 and sid == 'section_5':
                        do_pause = True
                    elif pause_at_end and (sid == sections[-1][0]):
                        do_pause = True

                    if do_pause:
                        if not self._prompt_section_review_and_approval(name):
                            break
                    else:
                        try:
                            self.gateway_controller.approve_section(name)
                        except Exception:
                            pass

                # On full auto, assemble at end
                if pause_at_end:
                    self.root.after(0, lambda: self.generate_full_report())
                self.status_var.set("Auto Run complete")
            except Exception as e:
                error_msg = str(e)  # Capture error in local scope
                self.root.after(0, lambda: self.on_generation_error(error_msg))
        threading.Thread(target=run, daemon=True).start()

    def _prompt_section_review_and_approval(self, section_name: str) -> bool:
        import threading
        decision = {'ok': False, 'cancel': False}
        evt = threading.Event()
        def ask():
            res = messagebox.askyesnocancel("Section Review", f"Review completed for {section_name}?\n\nApprove this section?", icon='question')
            if res is True:
                try:
                    self.gateway_controller.approve_section(section_name)
                except Exception:
                    pass
                decision['ok'] = True
            elif res is None:
                decision['cancel'] = True
            evt.set()
        self.root.after(0, ask)
        evt.wait()
        return decision['ok'] and not decision['cancel']
    
    def ocr_settings(self):
        """Open OCR settings dialog"""
        messagebox.showinfo("OCR Settings", "OCR settings dialog - To be implemented")
    
    def ai_config(self):
        """Open AI configuration dialog"""
        messagebox.showinfo("AI Configuration", "AI configuration dialog - To be implemented")
    
    def export_settings(self):
        """Open export settings dialog"""
        messagebox.showinfo("Export Settings", "Export settings dialog - To be implemented")
    
    def auto_save_case(self):
        """Auto-save current case data"""
        if self.current_case_id and self.section_data:
            try:
                # Save section data
                for section_name, section_content in self.section_data.items():
                    self.repository_manager.save_section_data(
                        self.current_case_id, 
                        section_name, 
                        section_content
                    )
                
                logger.info(f"Auto-saved case: {self.current_case_id}")
            except Exception as e:
                logger.error(f"Auto-save failed: {str(e)}")
    
        # Redirect to consolidated profile settings instead of problematic UserProfileDialog
        self.show_profile_settings()
    
    def show_profile_settings(self):
        """Show consolidated profile and API settings"""
        if not self.profile_manager or not self.profile_manager.is_authenticated():
            messagebox.showwarning("Profile Settings", "Please login first")
            return
        
        # Create profile settings window
        profile_window = tk.Toplevel(self.root)
        profile_window.title("Profile & API Settings")
        profile_window.geometry("800x600")
        profile_window.transient(self.root)
        profile_window.grab_set()
        
        # Create notebook for tabs
        notebook = ttk.Notebook(profile_window)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Profile Info Tab
        profile_frame = ttk.Frame(notebook)
        notebook.add(profile_frame, text="Profile Information")
        
        # Get current user info
        user_info = self.profile_manager.get_user_info()
        
        ttk.Label(profile_frame, text="User Profile", font=('Arial', 14, 'bold')).pack(pady=(10, 20))
        
        info_frame = ttk.Frame(profile_frame)
        info_frame.pack(fill='x', padx=20)
        
        ttk.Label(info_frame, text="Username:", font=('Arial', 11, 'bold')).grid(row=0, column=0, sticky='w', pady=5)
        ttk.Label(info_frame, text=user_info.get('username', 'N/A')).grid(row=0, column=1, sticky='w', padx=(10, 0), pady=5)
        
        ttk.Label(info_frame, text="Full Name:", font=('Arial', 11, 'bold')).grid(row=1, column=0, sticky='w', pady=5)
        ttk.Label(info_frame, text=user_info.get('full_name', 'N/A')).grid(row=1, column=1, sticky='w', padx=(10, 0), pady=5)
        
        ttk.Label(info_frame, text="Email:", font=('Arial', 11, 'bold')).grid(row=2, column=0, sticky='w', pady=5)
        ttk.Label(info_frame, text=user_info.get('email', 'N/A')).grid(row=2, column=1, sticky='w', padx=(10, 0), pady=5)
        
        ttk.Label(info_frame, text="Company:", font=('Arial', 11, 'bold')).grid(row=3, column=0, sticky='w', pady=5)
        ttk.Label(info_frame, text=user_info.get('company', 'N/A')).grid(row=3, column=1, sticky='w', padx=(10, 0), pady=5)
        
        # API Keys Tab
        api_frame = ttk.Frame(notebook)
        notebook.add(api_frame, text="API Keys")
        
        self._setup_api_keys_tab(api_frame, profile_window)
        
        # Close button
        ttk.Button(profile_window, text="Close", command=profile_window.destroy).pack(pady=10)

    def _setup_api_keys_tab(self, parent, window):
        """Setup API keys configuration tab"""
        # This is the existing API keys setup logic
        self.show_api_keys_settings_content(parent, window)
    
    def show_api_keys_settings_content(self, parent=None, window=None):
        """API keys settings content - can be used in tab or standalone"""
        if parent is None:
            # Standalone window mode (legacy)
            window = tk.Toplevel(self.root)
            window.title("API Keys Settings")
            window.geometry("800x600")
            window.transient(self.root)
            window.grab_set()
            parent = window
    
    def show_api_keys_settings(self):
        """Show API keys settings dialog"""
        if not self.profile_manager.is_authenticated():
            messagebox.showerror("Error", "No user logged in")
            return
        
        # Create API keys window
        api_window = tk.Toplevel(self.root)
        api_window.title("API Keys Settings")
        api_window.geometry("700x500")
        api_window.resizable(False, False)
        
        # Center window
        api_window.update_idletasks()
        x = (api_window.winfo_screenwidth() // 2) - (700 // 2)
        y = (api_window.winfo_screenheight() // 2) - (500 // 2)
        api_window.geometry(f"700x500+{x}+{y}")
        
        # Make modal
        api_window.transient(self.root)
        api_window.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(api_window, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title = tk.Label(main_frame, text="API Keys Configuration", font=('Arial', 16, 'bold'))
        title.pack(pady=(0, 20))
        
        # Get current API keys
        current_keys = self.profile_manager.get_api_keys()
        
        # Create notebook for different services with visible tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill='both', expand=True, pady=10)
        
        # Style the notebook tabs to be more visible
        style = ttk.Style()
        style.configure('TNotebook.Tab', padding=[20, 10], font=('Arial', 10, 'bold'))
        
        # API key variables
        api_vars = {}
        
        # Google Services tab
        google_frame = ttk.Frame(notebook, padding="20")
        notebook.add(google_frame, text="🔍 Google Services")
        
        ttk.Label(google_frame, text="Google Search API Key:", font=('Arial', 11, 'bold')).pack(anchor='w', pady=(0, 5))
        api_vars['google_search_api'] = tk.StringVar(value=current_keys.get('google_search_api', ''))
        ttk.Entry(google_frame, textvariable=api_vars['google_search_api'], width=70, font=('Arial', 10)).pack(fill='x', pady=(0, 10))
        
        ttk.Label(google_frame, text="Custom Search Engine ID:", font=('Arial', 11, 'bold')).pack(anchor='w', pady=(0, 5))
        api_vars['google_search_engine_id'] = tk.StringVar(value=current_keys.get('google_search_engine_id', ''))
        ttk.Entry(google_frame, textvariable=api_vars['google_search_engine_id'], width=70, font=('Arial', 10)).pack(fill='x', pady=(0, 10))
        
        ttk.Label(google_frame, text="Google Maps API Key:", font=('Arial', 11, 'bold')).pack(anchor='w', pady=(0, 5))
        api_vars['google_maps_api'] = tk.StringVar(value=current_keys.get('google_maps_api', ''))
        ttk.Entry(google_frame, textvariable=api_vars['google_maps_api'], width=70, font=('Arial', 10)).pack(fill='x', pady=(0, 10))
        
        # AI Services tab
        ai_frame = ttk.Frame(notebook, padding="20")
        notebook.add(ai_frame, text="🤖 AI Services")
        
        ttk.Label(ai_frame, text="OpenAI API Key (ChatGPT):", font=('Arial', 11, 'bold')).pack(anchor='w', pady=(0, 5))
        api_vars['openai_api'] = tk.StringVar(value=current_keys.get('openai_api', ''))
        ttk.Entry(ai_frame, textvariable=api_vars['openai_api'], width=70, font=('Arial', 10)).pack(fill='x', pady=(0, 10))
        
        ttk.Label(ai_frame, text="Google Gemini API Key:", font=('Arial', 11, 'bold')).pack(anchor='w', pady=(0, 5))
        api_vars['google_gemini_api'] = tk.StringVar(value=current_keys.get('google_gemini_api', ''))
        ttk.Entry(ai_frame, textvariable=api_vars['google_gemini_api'], width=70, font=('Arial', 10)).pack(fill='x', pady=(0, 10))
        
        # Other Services tab
        other_frame = ttk.Frame(notebook, padding="20")
        notebook.add(other_frame, text="🌐 Other Services")
        
        ttk.Label(other_frame, text="Bing Search API Key:", font=('Arial', 11, 'bold')).pack(anchor='w', pady=(0, 5))
        api_vars['bing_search_api'] = tk.StringVar(value=current_keys.get('bing_search_api', ''))
        ttk.Entry(other_frame, textvariable=api_vars['bing_search_api'], width=70, font=('Arial', 10)).pack(fill='x', pady=(0, 10))
        
        ttk.Label(other_frame, text="Public Records API Key:", font=('Arial', 11, 'bold')).pack(anchor='w', pady=(0, 5))
        api_vars['public_records_api'] = tk.StringVar(value=current_keys.get('public_records_api', ''))
        ttk.Entry(other_frame, textvariable=api_vars['public_records_api'], width=70, font=('Arial', 10)).pack(fill='x', pady=(0, 10))
        
        ttk.Label(other_frame, text="WhitePages API Key:", font=('Arial', 11, 'bold')).pack(anchor='w', pady=(0, 5))
        api_vars['whitepages_api'] = tk.StringVar(value=current_keys.get('whitepages_api', ''))
        ttk.Entry(other_frame, textvariable=api_vars['whitepages_api'], width=70, font=('Arial', 10)).pack(fill='x', pady=(0, 10))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        def save_api_keys():
            saved_count = 0
            for service, var in api_vars.items():
                key = var.get().strip()
                # Save all keys (empty or not) to allow clearing
                if self.profile_manager.save_api_key(service, key):
                    if key:  # Count only non-empty keys
                        saved_count += 1
            
            # Always allow saving (even with empty keys)
            self.toolkit_engine.set_user_profile_manager(self.profile_manager)
            if saved_count > 0:
                messagebox.showinfo("Success", f"Saved {saved_count} API keys successfully")
            else:
                messagebox.showinfo("Success", "API key settings saved (no keys entered)")
            api_window.destroy()
        
        ttk.Button(button_frame, text="Save API Keys", command=save_api_keys).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=api_window.destroy).pack(side='left', padx=5)
    
    def logout_user(self):
        """Logout current user"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.profile_manager.logout()
            self.toolkit_engine.set_user_profile_manager(None)
            messagebox.showinfo("Logged Out", "You have been logged out successfully")
    
    # ==================== NETWORK MONITORING ====================
    
    def initialize_api_monitoring(self):
        """Initialize API monitoring with current user's API keys"""
        try:
            if self.profile_manager and self.profile_manager.current_user:
                api_keys = self.profile_manager.get_api_keys()
                self.api_tester = APITester(api_keys)
                logger.info("API monitoring initialized with user keys")
            else:
                logger.warning("No user logged in - API monitoring not initialized")
        except Exception as e:
            logger.error(f"Failed to initialize API monitoring: {e}")
    
    def show_api_status_monitor(self):
        """Show API status monitoring window"""
        if not self.api_tester:
            self.initialize_api_monitoring()
        
        # Create API status window
        status_window = tk.Toplevel(self.root)
        status_window.title("API Status Monitor - Network Agent")
        status_window.geometry("600x500")
        status_window.transient(self.root)
        status_window.grab_set()
        
        # Create API status panel
        api_panel = APIStatusPanel(status_window, self.api_tester)
        api_panel.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Add status summary at bottom
        summary_frame = ttk.Frame(status_window)
        summary_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        ttk.Label(summary_frame, text="System Architect Compliance:", font=('Arial', 10, 'bold')).pack(anchor='w')
        ttk.Label(summary_frame, text="API Sequence: ChatGPT → Gemini → Google Maps", foreground='blue').pack(anchor='w')
        
        def show_detailed_status():
            """Show detailed API status information"""
            try:
                status = self.api_tester.get_api_status_summary()
                detail_window = tk.Toplevel(status_window)
                detail_window.title("Detailed API Status")
                detail_window.geometry("500x400")
                
                text_widget = tk.Text(detail_window, wrap=tk.WORD)
                scrollbar = ttk.Scrollbar(detail_window, orient="vertical", command=text_widget.yview)
                text_widget.configure(yscrollcommand=scrollbar.set)
                
                text_widget.pack(side='left', fill='both', expand=True)
                scrollbar.pack(side='right', fill='y')
                
                # Format status information
                status_text = "=== DKI Report Engine API Status ===\n\n"
                status_text += f"Individual Tests: {status['individual_tests']}\n\n"
                status_text += f"Sequence Test: {status['sequence_test']}\n\n"
                status_text += f"System Architect Compliance: {status['system_architect_compliance']}\n\n"
                status_text += "Recommendations:\n"
                for rec in status['recommendations']:
                    status_text += f"• {rec}\n"
                
                text_widget.insert('1.0', status_text)
                text_widget.config(state='disabled')
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to get detailed status: {e}")
        
        ttk.Button(summary_frame, text="Show Detailed Status", command=show_detailed_status).pack(anchor='e', pady=(5, 0))
    
    # ==================== PREMIUM FEATURES ====================
    
    def print_report(self):
        """Print current report"""
        try:
            if not self.section_data:
                messagebox.showwarning("Print", "No report data available. Generate a report first.")
                return
            
            # Generate report data for printing
            report_data = self.report_generator.generate_full_report(self.section_data, self.report_type.get())
            
            # Show print dialog
            success = self.printing_system.show_print_dialog(self.root, report_data)
            
            if success:
                self.status_var.set("Report sent to printer")
            
        except Exception as e:
            logger.error(f"Print operation failed: {e}")
            messagebox.showerror("Print Error", f"Failed to print report: {str(e)}")
    
    def show_signature_dialog(self):
        """Show digital signature dialog"""
        try:
            # Check if we have a report to sign
            if not self.section_data:
                messagebox.showwarning("Digital Signature", "No report available. Generate a report first.")
                return
            
            # Generate temporary PDF for signing
            temp_pdf = self._create_temp_pdf_for_signing()
            if not temp_pdf:
                messagebox.showerror("Error", "Failed to create PDF for signing")
                return
            
            # Show signature dialog
            success = self.signature_system.show_signature_dialog(self.root, temp_pdf)
            
            if success:
                self.status_var.set("Document signed successfully")
            
            # Cleanup temp file
            try:
                os.unlink(temp_pdf)
            except:
                pass
                
        except Exception as e:
            logger.error(f"Digital signature failed: {e}")
            messagebox.showerror("Signature Error", f"Failed to apply signature: {str(e)}")
    
    def show_watermark_dialog(self):
        """Show watermark dialog"""
        try:
            # Check if we have a report to watermark
            if not self.section_data:
                messagebox.showwarning("Watermark", "No report available. Generate a report first.")
                return
            
            # Generate temporary PDF for watermarking
            temp_pdf = self._create_temp_pdf_for_watermarking()
            if not temp_pdf:
                messagebox.showerror("Error", "Failed to create PDF for watermarking")
                return
            
            # Show watermark dialog
            success = self.watermark_system.show_watermark_dialog(self.root, temp_pdf)
            
            if success:
                self.status_var.set("Watermark applied successfully")
            
            # Cleanup temp file
            try:
                os.unlink(temp_pdf)
            except:
                pass
                
        except Exception as e:
            logger.error(f"Watermark application failed: {e}")
            messagebox.showerror("Watermark Error", f"Failed to apply watermark: {str(e)}")
    
    def show_template_editor(self):
        """Show template and color scheme editor"""
        try:
            success = self.template_system.show_template_editor(self.root)
            
            if success:
                self.status_var.set("Template settings updated")
                messagebox.showinfo("Template Editor", "Template and color scheme settings have been updated!")
                
        except Exception as e:
            logger.error(f"Template editor failed: {e}")
            messagebox.showerror("Template Error", f"Failed to open template editor: {str(e)}")
    
    def _create_temp_pdf_for_signing(self) -> Optional[str]:
        """Create temporary PDF file for digital signing"""
        try:
            import tempfile
            
            # Generate report data
            report_data = self.report_generator.generate_full_report(self.section_data, self.report_type.get())
            
            # Apply current template
            styled_report = self.template_system.apply_template_to_report(report_data)
            
            # Create temporary PDF
            temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            temp_file.close()
            
            # Export to PDF
            self.report_generator.export_report(styled_report, temp_file.name, 'pdf')
            
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Failed to create temp PDF for signing: {e}")
            return None
    
    def _create_temp_pdf_for_watermarking(self) -> Optional[str]:
        """Create temporary PDF file for watermarking"""
        try:
            import tempfile
            
            # Generate report data
            report_data = self.report_generator.generate_full_report(self.section_data, self.report_type.get())
            
            # Apply current template
            styled_report = self.template_system.apply_template_to_report(report_data)
            
            # Create temporary PDF
            temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            temp_file.close()
            
            # Export to PDF
            self.report_generator.export_report(styled_report, temp_file.name, 'pdf')
            
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Failed to create temp PDF for watermarking: {e}")
            return None
            self.root.quit()  # Close application
    
    def test_internet_connectivity(self) -> bool:
        """Test internet connectivity with multiple fallback methods"""
        try:
            # Method 1: Try to connect to Google DNS
            socket.create_connection(("8.8.8.8", 53), timeout=3).close()
            return True
        except (socket.error, socket.timeout):
            pass
        
        try:
            # Method 2: Try to connect to Cloudflare DNS
            socket.create_connection(("1.1.1.1", 53), timeout=3).close()
            return True
        except (socket.error, socket.timeout):
            pass
        
        try:
            # Method 3: Try HTTP request to a reliable endpoint
            req = urllib.request.Request("https://www.google.com", headers={'User-Agent': 'DKI-Engine/1.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.getcode() == 200
        except (urllib.error.URLError, socket.timeout):
            pass
        
        return False
    
    def update_internet_status(self):
        """Update internet connectivity status and schedule next check"""
        def check_connectivity():
            try:
                if self.test_internet_connectivity():
                    self.root.after(0, lambda: self.internet_status.set("🌐 Online"))
                else:
                    self.root.after(0, lambda: self.internet_status.set("🚫 Offline"))
            except Exception as e:
                self.root.after(0, lambda: self.internet_status.set("⚠️ Error"))
                logger.warning(f"Connectivity check error: {e}")
        
        # Run connectivity check in background thread to avoid UI blocking
        threading.Thread(target=check_connectivity, daemon=True).start()
        
        # Schedule next check in 30 seconds
        self.root.after(30000, self.update_internet_status)
    
    def run(self):
        """Run the application"""
        logger.info("Starting DKI Engine Application")
        self.root.mainloop()


class NewCaseDialog:
    """Dialog for creating a new case"""
    
    def __init__(self, parent, repository_manager):
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("New Case")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 100, parent.winfo_rooty() + 100))
        
        self.setup_dialog()
        
        # Wait for dialog to close
        self.dialog.wait_window()
    
    def setup_dialog(self):
        """Setup the dialog interface"""
        
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="Create New Case",
            font=('Arial', 16, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        # Case name
        ttk.Label(main_frame, text="Case Name:").pack(anchor='w')
        self.case_name_var = tk.StringVar()
        case_name_entry = ttk.Entry(main_frame, textvariable=self.case_name_var, width=50)
        case_name_entry.pack(fill='x', pady=(5, 15))
        case_name_entry.focus()
        
        # Report type
        ttk.Label(main_frame, text="Report Type:").pack(anchor='w')
        self.report_type_var = tk.StringVar(value="Investigative")
        report_combo = ttk.Combobox(
            main_frame,
            textvariable=self.report_type_var,
            values=["Investigative", "Surveillance", "Hybrid"],
            state="readonly"
        )
        report_combo.pack(fill='x', pady=(5, 15))
        
        # Client information frame
        client_frame = ttk.LabelFrame(main_frame, text="Client Information", padding="10")
        client_frame.pack(fill='both', expand=True, pady=(10, 15))
        
        # Client name
        ttk.Label(client_frame, text="Client Name:").pack(anchor='w')
        self.client_name_var = tk.StringVar()
        ttk.Entry(client_frame, textvariable=self.client_name_var, width=50).pack(fill='x', pady=(5, 10))
        
        # Client phone
        ttk.Label(client_frame, text="Client Phone:").pack(anchor='w')
        self.client_phone_var = tk.StringVar()
        ttk.Entry(client_frame, textvariable=self.client_phone_var, width=50).pack(fill='x', pady=(5, 10))
        
        # Client address
        ttk.Label(client_frame, text="Client Address:").pack(anchor='w')
        self.client_address_var = tk.StringVar()
        address_entry = tk.Text(client_frame, height=3, width=50)
        address_entry.pack(fill='x', pady=(5, 0))
        self.client_address_text = address_entry
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(15, 0))
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel
        ).pack(side='right', padx=(10, 0))
        
        ttk.Button(
            button_frame,
            text="Create Case",
            command=self.create_case
        ).pack(side='right')
        
        # Bind Enter key
        self.dialog.bind('<Return>', lambda e: self.create_case())
        self.dialog.bind('<Escape>', lambda e: self.cancel())
    
    def create_case(self):
        """Create the new case"""
        
        case_name = self.case_name_var.get().strip()
        if not case_name:
            messagebox.showerror("Error", "Case name is required")
            return
        
        client_address = self.client_address_text.get(1.0, tk.END).strip()
        
        self.result = {
            'case_name': case_name,
            'report_type': self.report_type_var.get(),
            'client_info': {
                'client_name': self.client_name_var.get().strip(),
                'client_phone': self.client_phone_var.get().strip(),
                'client_address': client_address,
                'contract_date': datetime.now().strftime('%Y-%m-%d')
            }
        }
        
        self.dialog.destroy()
    
    def cancel(self):
        """Cancel dialog"""
        self.result = None
        self.dialog.destroy()


if __name__ == "__main__":
    app = DKIEngineApp()
    app.run()
