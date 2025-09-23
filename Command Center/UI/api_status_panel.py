#!/usr/bin/env python3
"""
API Status Panel - Real-time API connectivity monitoring dashboard
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
import requests
from typing import Dict, Any, Callable, Optional
import logging

logger = logging.getLogger(__name__)

class APIStatusPanel(ttk.Frame):
    """Panel for monitoring real-time API status"""
    
    def __init__(self, parent, api_tester=None):
        super().__init__(parent)
        
        self.api_tester = api_tester
        self.api_status = {
            'openai': {'status': 'unknown', 'last_check': 'Never'},
            'google_maps': {'status': 'unknown', 'last_check': 'Never'},
            'google_gemini': {'status': 'unknown', 'last_check': 'Never'},
            'google_search': {'status': 'placeholder', 'last_check': 'Never'},
            'bing_search': {'status': 'placeholder', 'last_check': 'Never'},
            'public_records': {'status': 'placeholder', 'last_check': 'Never'},
            'whitepages': {'status': 'placeholder', 'last_check': 'Never'}
        }
        
        self.status_labels = {}
        self.indicator_labels = {}
        self.auto_refresh = True
        self.refresh_interval = 300  # 5 minutes
        
        self.setup_ui()
        self.start_monitoring()
    
    def setup_ui(self):
        """Setup the API status monitoring interface"""
        
        # Main frame
        main_frame = ttk.LabelFrame(self, text="API Status Monitor", padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(header_frame, text="Service", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky='w', padx=(0, 20))
        ttk.Label(header_frame, text="Status", font=('Arial', 10, 'bold')).grid(row=0, column=1, sticky='w', padx=(0, 20))
        ttk.Label(header_frame, text="Last Check", font=('Arial', 10, 'bold')).grid(row=0, column=2, sticky='w')
        
        # Separator
        ttk.Separator(main_frame, orient='horizontal').pack(fill='x', pady=(0, 10))
        
        # API status rows
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill='x')
        
        api_names = {
            'openai': 'OpenAI API',
            'google_maps': 'Google Maps API',
            'google_gemini': 'Google Gemini API',
            'google_search': 'Google Search API',
            'bing_search': 'Bing Search API',
            'public_records': 'Public Records API',
            'whitepages': 'WhitePages API'
        }
        
        for i, (api_key, display_name) in enumerate(api_names.items()):
            # Service name
            ttk.Label(status_frame, text=display_name).grid(row=i, column=0, sticky='w', padx=(0, 20), pady=2)
            
            # Status indicator
            indicator = tk.Label(status_frame, text="●", font=('Arial', 12), fg='gray')
            indicator.grid(row=i, column=1, sticky='w', padx=(0, 10), pady=2)
            self.indicator_labels[api_key] = indicator
            
            # Status text
            status_label = ttk.Label(status_frame, text="Unknown")
            status_label.grid(row=i, column=1, sticky='w', padx=(20, 20), pady=2)
            self.status_labels[api_key] = status_label
            
            # Last check time
            time_label = ttk.Label(status_frame, text="Never", foreground='gray')
            time_label.grid(row=i, column=2, sticky='w', pady=2)
            self.status_labels[f"{api_key}_time"] = time_label
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(15, 0))
        
        # Refresh button
        self.refresh_btn = ttk.Button(
            button_frame,
            text="Refresh Now",
            command=self.manual_refresh
        )
        self.refresh_btn.pack(side='left', padx=(0, 10))
        
        # Auto refresh toggle
        self.auto_var = tk.BooleanVar(value=True)
        self.auto_check = ttk.Checkbutton(
            button_frame,
            text="Auto-refresh (5 min)",
            variable=self.auto_var,
            command=self.toggle_auto_refresh
        )
        self.auto_check.pack(side='left')
        
        # Status summary
        self.summary_label = ttk.Label(button_frame, text="", foreground='blue')
        self.summary_label.pack(side='right')
    
    def get_status_color(self, status: str) -> str:
        """Get color for status indicator"""
        colors = {
            'working': 'green',
            'error': 'red',
            'rate_limited': 'orange',
            'placeholder': 'gray',
            'unknown': 'gray'
        }
        return colors.get(status, 'gray')
    
    def get_status_text(self, status: str) -> str:
        """Get human-readable status text"""
        texts = {
            'working': 'Connected',
            'error': 'Error',
            'rate_limited': 'Rate Limited',
            'placeholder': 'Not Configured',
            'unknown': 'Unknown'
        }
        return texts.get(status, 'Unknown')
    
    def update_status_display(self):
        """Update the visual status display"""
        working_count = 0
        total_configured = 0
        
        for api_key, status_data in self.api_status.items():
            status = status_data['status']
            last_check = status_data['last_check']
            
            # Update indicator color
            color = self.get_status_color(status)
            self.indicator_labels[api_key].config(fg=color)
            
            # Update status text
            status_text = self.get_status_text(status)
            self.status_labels[api_key].config(text=status_text)
            
            # Update last check time
            self.status_labels[f"{api_key}_time"].config(text=last_check)
            
            # Count working APIs
            if status != 'placeholder':
                total_configured += 1
                if status == 'working':
                    working_count += 1
        
        # Update summary
        if total_configured > 0:
            self.summary_label.config(
                text=f"{working_count}/{total_configured} APIs operational",
                foreground='green' if working_count == total_configured else 'orange'
            )
        else:
            self.summary_label.config(text="No APIs configured", foreground='gray')
    
    def check_api_status(self):
        """Check status of all APIs"""
        if not self.api_tester:
            return
        
        try:
            # Run API tests
            results = self.api_tester.run_all_tests()
            current_time = time.strftime("%H:%M:%S")
            
            # Update status based on results
            for api_key in self.api_status.keys():
                if api_key in results:
                    self.api_status[api_key] = {
                        'status': 'working' if results[api_key] else 'error',
                        'last_check': current_time
                    }
                elif api_key in ['google_search', 'bing_search', 'public_records', 'whitepages']:
                    # Keep placeholder status for unconfigured APIs
                    self.api_status[api_key]['last_check'] = current_time
            
            # Update display in main thread
            self.after(0, self.update_status_display)
            
        except Exception as e:
            logger.error(f"Error checking API status: {e}")
    
    def manual_refresh(self):
        """Manually refresh API status"""
        self.refresh_btn.config(state='disabled', text='Checking...')
        
        def refresh_thread():
            self.check_api_status()
            self.after(0, lambda: self.refresh_btn.config(state='normal', text='Refresh Now'))
        
        threading.Thread(target=refresh_thread, daemon=True).start()
    
    def toggle_auto_refresh(self):
        """Toggle automatic refresh"""
        self.auto_refresh = self.auto_var.get()
        logger.info(f"Auto-refresh {'enabled' if self.auto_refresh else 'disabled'}")
    
    def start_monitoring(self):
        """Start the monitoring loop"""
        def monitoring_loop():
            while True:
                if self.auto_refresh:
                    self.check_api_status()
                time.sleep(self.refresh_interval)
        
        threading.Thread(target=monitoring_loop, daemon=True).start()
        
        # Initial check
        self.after(1000, self.manual_refresh)  # Check after 1 second
    
    def set_api_tester(self, api_tester):
        """Set the API tester instance"""
        self.api_tester = api_tester
        logger.info("API tester configured for status monitoring")


if __name__ == "__main__":
    # Test the API status panel
    root = tk.Tk()
    root.title("API Status Monitor Test")
    root.geometry("600x400")
    
    panel = APIStatusPanel(root)
    panel.pack(fill='both', expand=True, padx=10, pady=10)
    
    root.mainloop()






