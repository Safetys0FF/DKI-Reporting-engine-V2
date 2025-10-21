#!/usr/bin/env python3
"""
System Health Dashboard - Comprehensive system performance monitoring interface
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
import psutil
import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class SystemHealthDashboard(ttk.Frame):
    """Dashboard for monitoring comprehensive system health and performance"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.system_metrics = {
            'cpu_percent': 0,
            'memory_percent': 0,
            'disk_usage': 0,
            'network_activity': {'sent': 0, 'recv': 0},
            'process_count': 0,
            'uptime': 0
        }
        
        self.performance_history = {
            'cpu': [],
            'memory': [],
            'timestamps': []
        }
        
        self.monitoring_active = True
        self.refresh_interval = 2  # seconds
        
        self.setup_ui()
        self.start_monitoring()
    
    def setup_ui(self):
        """Setup the system health dashboard interface"""
        
        # Main container
        main_frame = ttk.LabelFrame(self, text="System Health Dashboard", padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Top row - Key metrics
        metrics_frame = ttk.Frame(main_frame)
        metrics_frame.pack(fill='x', pady=(0, 15))
        
        # CPU Usage
        cpu_frame = ttk.LabelFrame(metrics_frame, text="CPU Usage", padding="10")
        cpu_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        self.cpu_var = tk.StringVar(value="0%")
        self.cpu_label = ttk.Label(cpu_frame, textvariable=self.cpu_var, font=('Arial', 14, 'bold'))
        self.cpu_label.pack()
        
        self.cpu_progress = ttk.Progressbar(cpu_frame, length=100, mode='determinate')
        self.cpu_progress.pack(fill='x', pady=(5, 0))
        
        # Memory Usage
        memory_frame = ttk.LabelFrame(metrics_frame, text="Memory Usage", padding="10")
        memory_frame.pack(side='left', fill='both', expand=True, padx=5)
        
        self.memory_var = tk.StringVar(value="0%")
        self.memory_label = ttk.Label(memory_frame, textvariable=self.memory_var, font=('Arial', 14, 'bold'))
        self.memory_label.pack()
        
        self.memory_progress = ttk.Progressbar(memory_frame, length=100, mode='determinate')
        self.memory_progress.pack(fill='x', pady=(5, 0))
        
        # Disk Usage
        disk_frame = ttk.LabelFrame(metrics_frame, text="Disk Usage", padding="10")
        disk_frame.pack(side='left', fill='both', expand=True, padx=(5, 0))
        
        self.disk_var = tk.StringVar(value="0%")
        self.disk_label = ttk.Label(disk_frame, textvariable=self.disk_var, font=('Arial', 14, 'bold'))
        self.disk_label.pack()
        
        self.disk_progress = ttk.Progressbar(disk_frame, length=100, mode='determinate')
        self.disk_progress.pack(fill='x', pady=(5, 0))
        
        # Middle row - System information
        info_frame = ttk.LabelFrame(main_frame, text="System Information", padding="10")
        info_frame.pack(fill='x', pady=(0, 15))
        
        info_grid = ttk.Frame(info_frame)
        info_grid.pack(fill='x')
        
        # System info labels
        ttk.Label(info_grid, text="Processes:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky='w', padx=(0, 10))
        self.processes_var = tk.StringVar(value="0")
        ttk.Label(info_grid, textvariable=self.processes_var).grid(row=0, column=1, sticky='w', padx=(0, 30))
        
        ttk.Label(info_grid, text="Network Sent:", font=('Arial', 10, 'bold')).grid(row=0, column=2, sticky='w', padx=(0, 10))
        self.net_sent_var = tk.StringVar(value="0 MB")
        ttk.Label(info_grid, textvariable=self.net_sent_var).grid(row=0, column=3, sticky='w', padx=(0, 30))
        
        ttk.Label(info_grid, text="Uptime:", font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky='w', padx=(0, 10))
        self.uptime_var = tk.StringVar(value="0:00:00")
        ttk.Label(info_grid, textvariable=self.uptime_var).grid(row=1, column=1, sticky='w', padx=(0, 30))
        
        ttk.Label(info_grid, text="Network Recv:", font=('Arial', 10, 'bold')).grid(row=1, column=2, sticky='w', padx=(0, 10))
        self.net_recv_var = tk.StringVar(value="0 MB")
        ttk.Label(info_grid, textvariable=self.net_recv_var).grid(row=1, column=3, sticky='w', padx=(0, 30))
        
        # Bottom row - Performance graph (simplified text representation)
        graph_frame = ttk.LabelFrame(main_frame, text="Performance Trend", padding="10")
        graph_frame.pack(fill='both', expand=True)
        
        # Performance text display
        self.performance_text = tk.Text(graph_frame, height=8, width=80, font=('Courier', 9))
        self.performance_text.pack(fill='both', expand=True)
        
        # Scrollbar for performance text
        scrollbar = ttk.Scrollbar(graph_frame, orient="vertical", command=self.performance_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.performance_text.configure(yscrollcommand=scrollbar.set)
        
        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill='x', pady=(10, 0))
        
        self.pause_btn = ttk.Button(
            control_frame,
            text="Pause Monitoring",
            command=self.toggle_monitoring
        )
        self.pause_btn.pack(side='left', padx=(0, 10))
        
        self.clear_btn = ttk.Button(
            control_frame,
            text="Clear History",
            command=self.clear_history
        )
        self.clear_btn.pack(side='left')
        
        # Status indicator
        self.status_var = tk.StringVar(value="Monitoring Active")
        status_label = ttk.Label(control_frame, textvariable=self.status_var, foreground='green')
        status_label.pack(side='right')
    
    def collect_system_metrics(self):
        """Collect current system performance metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.system_metrics['cpu_percent'] = cpu_percent
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.system_metrics['memory_percent'] = memory.percent
            
            # Disk usage (for current drive)
            disk = psutil.disk_usage('/')
            self.system_metrics['disk_usage'] = (disk.used / disk.total) * 100
            
            # Network activity
            net_io = psutil.net_io_counters()
            self.system_metrics['network_activity'] = {
                'sent': net_io.bytes_sent / (1024 * 1024),  # MB
                'recv': net_io.bytes_recv / (1024 * 1024)   # MB
            }
            
            # Process count
            self.system_metrics['process_count'] = len(psutil.pids())
            
            # System uptime
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            self.system_metrics['uptime'] = uptime_seconds
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def update_display(self):
        """Update the dashboard display with current metrics"""
        try:
            # Update CPU
            cpu_percent = self.system_metrics['cpu_percent']
            self.cpu_var.set(f"{cpu_percent:.1f}%")
            self.cpu_progress['value'] = cpu_percent
            
            # Color coding for CPU
            if cpu_percent > 80:
                self.cpu_label.config(foreground='red')
            elif cpu_percent > 60:
                self.cpu_label.config(foreground='orange')
            else:
                self.cpu_label.config(foreground='green')
            
            # Update Memory
            memory_percent = self.system_metrics['memory_percent']
            self.memory_var.set(f"{memory_percent:.1f}%")
            self.memory_progress['value'] = memory_percent
            
            # Color coding for Memory
            if memory_percent > 80:
                self.memory_label.config(foreground='red')
            elif memory_percent > 60:
                self.memory_label.config(foreground='orange')
            else:
                self.memory_label.config(foreground='green')
            
            # Update Disk
            disk_percent = self.system_metrics['disk_usage']
            self.disk_var.set(f"{disk_percent:.1f}%")
            self.disk_progress['value'] = disk_percent
            
            # Color coding for Disk
            if disk_percent > 90:
                self.disk_label.config(foreground='red')
            elif disk_percent > 75:
                self.disk_label.config(foreground='orange')
            else:
                self.disk_label.config(foreground='green')
            
            # Update system info
            self.processes_var.set(str(self.system_metrics['process_count']))
            
            net_sent = self.system_metrics['network_activity']['sent']
            net_recv = self.system_metrics['network_activity']['recv']
            self.net_sent_var.set(f"{net_sent:.1f} MB")
            self.net_recv_var.set(f"{net_recv:.1f} MB")
            
            # Format uptime
            uptime_seconds = self.system_metrics['uptime']
            hours = int(uptime_seconds // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            seconds = int(uptime_seconds % 60)
            self.uptime_var.set(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            
            # Update performance history
            current_time = time.strftime("%H:%M:%S")
            self.performance_history['cpu'].append(cpu_percent)
            self.performance_history['memory'].append(memory_percent)
            self.performance_history['timestamps'].append(current_time)
            
            # Keep only last 50 entries
            if len(self.performance_history['cpu']) > 50:
                self.performance_history['cpu'].pop(0)
                self.performance_history['memory'].pop(0)
                self.performance_history['timestamps'].pop(0)
            
            # Update performance text display
            self.update_performance_display()
            
        except Exception as e:
            logger.error(f"Error updating display: {e}")
    
    def update_performance_display(self):
        """Update the performance trend display"""
        try:
            self.performance_text.delete(1.0, tk.END)
            
            # Add header
            self.performance_text.insert(tk.END, "Performance History (Last 50 readings):\n")
            self.performance_text.insert(tk.END, "-" * 60 + "\n")
            self.performance_text.insert(tk.END, f"{'Time':<10} {'CPU%':<8} {'Memory%':<10} {'Status':<15}\n")
            self.performance_text.insert(tk.END, "-" * 60 + "\n")
            
            # Add recent history
            for i in range(len(self.performance_history['timestamps'])):
                timestamp = self.performance_history['timestamps'][i]
                cpu = self.performance_history['cpu'][i]
                memory = self.performance_history['memory'][i]
                
                # Determine status
                if cpu > 80 or memory > 80:
                    status = "HIGH USAGE"
                elif cpu > 60 or memory > 60:
                    status = "MODERATE"
                else:
                    status = "NORMAL"
                
                line = f"{timestamp:<10} {cpu:<8.1f} {memory:<10.1f} {status:<15}\n"
                self.performance_text.insert(tk.END, line)
            
            # Auto-scroll to bottom
            self.performance_text.see(tk.END)
            
        except Exception as e:
            logger.error(f"Error updating performance display: {e}")
    
    def toggle_monitoring(self):
        """Toggle monitoring on/off"""
        self.monitoring_active = not self.monitoring_active
        
        if self.monitoring_active:
            self.pause_btn.config(text="Pause Monitoring")
            self.status_var.set("Monitoring Active")
            logger.info("System monitoring resumed")
        else:
            self.pause_btn.config(text="Resume Monitoring")
            self.status_var.set("Monitoring Paused")
            logger.info("System monitoring paused")
    
    def clear_history(self):
        """Clear performance history"""
        self.performance_history = {
            'cpu': [],
            'memory': [],
            'timestamps': []
        }
        self.performance_text.delete(1.0, tk.END)
        self.performance_text.insert(tk.END, "Performance history cleared.\n")
        logger.info("Performance history cleared")
    
    def start_monitoring(self):
        """Start the system monitoring loop"""
        def monitoring_loop():
            while True:
                if self.monitoring_active:
                    self.collect_system_metrics()
                    self.after(0, self.update_display)
                time.sleep(self.refresh_interval)
        
        threading.Thread(target=monitoring_loop, daemon=True).start()
        logger.info("System health monitoring started")


if __name__ == "__main__":
    # Test the system health dashboard
    root = tk.Tk()
    root.title("System Health Dashboard Test")
    root.geometry("800x600")
    
    dashboard = SystemHealthDashboard(root)
    dashboard.pack(fill='both', expand=True, padx=10, pady=10)
    
    root.mainloop()






