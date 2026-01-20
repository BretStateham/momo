"""
Configuration Dialogs Module

Provides dialog windows for configuring idle threshold and schedule.
Uses tkinter for simple, native Windows dialogs.

Note: These dialogs must be run from the main thread or use proper
thread marshalling when called from pystray callbacks.
"""

import tkinter as tk
from tkinter import messagebox
from typing import Optional
import threading
from .settings import Settings, WeeklySchedule, DaySchedule


class ThresholdDialog:
    """Dialog for configuring the idle threshold."""
    
    def __init__(self, parent: Optional[tk.Tk] = None, current_value: int = 300):
        """
        Initialize the threshold dialog.
        
        Args:
            parent: Parent window (optional)
            current_value: Current threshold value in seconds
        """
        self._result: Optional[int] = None
        self._current_value = current_value
        self._parent = parent
        
        # Create dialog window
        if parent:
            self._dialog = tk.Toplevel(parent)
        else:
            self._dialog = tk.Tk()
        
        self._dialog.title("Configure Idle Threshold")
        self._dialog.resizable(False, False)
        
        # Set window size before centering
        self._dialog.geometry("320x180")
        
        # Make it stay on top
        self._dialog.attributes('-topmost', True)
        
        # Handle window close button
        self._dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
        self._create_widgets()
        
        # Center after creating widgets
        self._center_window()
        
        # Focus the dialog
        self._dialog.focus_force()
        self._dialog.lift()
    
    def _center_window(self):
        """Center the dialog on screen."""
        self._dialog.update_idletasks()
        width = 320
        height = 180
        x = (self._dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self._dialog.winfo_screenheight() // 2) - (height // 2)
        self._dialog.geometry(f'{width}x{height}+{x}+{y}')
    
    def _create_widgets(self):
        """Create dialog widgets."""
        # Main frame with padding
        frame = tk.Frame(self._dialog, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Label
        tk.Label(
            frame,
            text="Idle threshold (seconds):",
            font=('Segoe UI', 10)
        ).pack(anchor=tk.W)
        
        # Entry
        self._entry_var = tk.StringVar(value=str(self._current_value))
        self._entry = tk.Entry(
            frame,
            textvariable=self._entry_var,
            width=15,
            font=('Segoe UI', 10)
        )
        self._entry.pack(anchor=tk.W, pady=(5, 10))
        self._entry.select_range(0, tk.END)
        self._entry.focus_set()
        
        # Helper text
        tk.Label(
            frame,
            text="Enter the number of seconds of inactivity\nbefore moving the mouse.",
            font=('Segoe UI', 9),
            fg='gray'
        ).pack(anchor=tk.W, pady=(0, 15))
        
        # Buttons frame
        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        cancel_btn = tk.Button(
            btn_frame,
            text="Cancel",
            command=self._on_cancel,
            width=10
        )
        cancel_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        ok_btn = tk.Button(
            btn_frame,
            text="OK",
            command=self._on_ok,
            width=10
        )
        ok_btn.pack(side=tk.RIGHT)
        
        # Bind Enter key
        self._dialog.bind('<Return>', lambda e: self._on_ok())
        self._dialog.bind('<Escape>', lambda e: self._on_cancel())
    
    def _on_ok(self):
        """Handle OK button click."""
        try:
            value = int(self._entry_var.get())
            if value <= 0:
                raise ValueError("Must be positive")
            self._result = value
            self._dialog.destroy()
        except ValueError:
            messagebox.showerror(
                "Invalid Value",
                "Please enter a positive integer.",
                parent=self._dialog
            )
    
    def _on_cancel(self):
        """Handle Cancel button click."""
        self._result = None
        self._dialog.destroy()
    
    def show(self) -> Optional[int]:
        """
        Show the dialog and return the result.
        
        Returns:
            The new threshold value, or None if cancelled.
        """
        self._dialog.mainloop()
        return self._result


class ScheduleDialog:
    """Dialog for configuring the weekly schedule."""
    
    DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    def __init__(self, parent: Optional[tk.Tk] = None, schedule: Optional[WeeklySchedule] = None):
        """
        Initialize the schedule dialog.
        
        Args:
            parent: Parent window (optional)
            schedule: Current schedule configuration
        """
        self._result: Optional[WeeklySchedule] = None
        self._schedule = schedule or WeeklySchedule()
        
        # Create dialog window
        if parent:
            self._dialog = tk.Toplevel(parent)
        else:
            self._dialog = tk.Tk()
        
        self._dialog.title("Configure Schedule")
        self._dialog.resizable(False, False)
        
        # Set window size
        self._dialog.geometry("480x420")
        
        # Make it stay on top
        self._dialog.attributes('-topmost', True)
        
        # Handle window close button
        self._dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
        # Store day widgets
        self._day_vars = {}
        self._start_vars = {}
        self._end_vars = {}
        
        self._create_widgets()
        
        # Center after creating widgets
        self._center_window()
        
        # Focus the dialog
        self._dialog.focus_force()
        self._dialog.lift()
    
    def _center_window(self):
        """Center the dialog on screen."""
        self._dialog.update_idletasks()
        width = 480
        height = 420
        x = (self._dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self._dialog.winfo_screenheight() // 2) - (height // 2)
        self._dialog.geometry(f'{width}x{height}+{x}+{y}')
    
    def _create_widgets(self):
        """Create dialog widgets."""
        # Main frame with padding
        frame = tk.Frame(self._dialog, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        tk.Label(
            frame,
            text="Configure Active Schedule",
            font=('Segoe UI', 12, 'bold')
        ).pack(anchor=tk.W, pady=(0, 5))
        
        tk.Label(
            frame,
            text="MoMo will only move the mouse during the scheduled times.",
            font=('Segoe UI', 9),
            fg='gray'
        ).pack(anchor=tk.W, pady=(0, 15))
        
        # Schedule grid frame
        schedule_frame = tk.Frame(frame)
        schedule_frame.pack(fill=tk.X)
        
        # Headers
        tk.Label(schedule_frame, text="Day", font=('Segoe UI', 9, 'bold'), width=12, anchor='w').grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        tk.Label(schedule_frame, text="Enabled", font=('Segoe UI', 9, 'bold'), width=8).grid(row=0, column=1, padx=5)
        tk.Label(schedule_frame, text="Start", font=('Segoe UI', 9, 'bold'), width=10).grid(row=0, column=2, padx=5)
        tk.Label(schedule_frame, text="End", font=('Segoe UI', 9, 'bold'), width=10).grid(row=0, column=3, padx=5)
        
        # Day rows
        for i, day in enumerate(self.DAYS):
            day_schedule = self._schedule.get_day(i)
            
            # Day name
            tk.Label(schedule_frame, text=day, width=12, anchor='w').grid(row=i+1, column=0, sticky=tk.W, pady=3, padx=(0, 10))
            
            # Enabled checkbox
            enabled_var = tk.BooleanVar(value=day_schedule.enabled)
            self._day_vars[i] = enabled_var
            tk.Checkbutton(schedule_frame, variable=enabled_var).grid(row=i+1, column=1, pady=3)
            
            # Start time
            start_var = tk.StringVar(value=day_schedule.start_time)
            self._start_vars[i] = start_var
            start_entry = tk.Entry(schedule_frame, textvariable=start_var, width=8)
            start_entry.grid(row=i+1, column=2, padx=5, pady=3)
            
            # End time
            end_var = tk.StringVar(value=day_schedule.stop_time)
            self._end_vars[i] = end_var
            end_entry = tk.Entry(schedule_frame, textvariable=end_var, width=8)
            end_entry.grid(row=i+1, column=3, padx=5, pady=3)
        
        # Time format hint
        tk.Label(
            frame,
            text="Times are in 24-hour format (HH:MM). Example: 08:00, 17:00",
            font=('Segoe UI', 8),
            fg='gray'
        ).pack(anchor=tk.W, pady=(15, 15))
        
        # Buttons frame
        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        tk.Button(
            btn_frame,
            text="Reset to Defaults",
            command=self._on_reset,
            width=15
        ).pack(side=tk.LEFT)
        
        tk.Button(
            btn_frame,
            text="Cancel",
            command=self._on_cancel,
            width=10
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        tk.Button(
            btn_frame,
            text="OK",
            command=self._on_ok,
            width=10
        ).pack(side=tk.RIGHT)
        
        # Bind Escape key
        self._dialog.bind('<Escape>', lambda e: self._on_cancel())
    
    def _validate_time(self, time_str: str) -> bool:
        """Validate a time string in HH:MM format with leading zeros."""
        try:
            if not isinstance(time_str, str):
                return False
            parts = time_str.split(':')
            if len(parts) != 2:
                return False
            hours_str, minutes_str = parts[0], parts[1]
            # Enforce two-digit format for consistency
            if len(hours_str) != 2 or len(minutes_str) != 2:
                return False
            if not (hours_str.isdigit() and minutes_str.isdigit()):
                return False
            hours = int(hours_str)
            minutes = int(minutes_str)
            return 0 <= hours <= 23 and 0 <= minutes <= 59
        except (ValueError, AttributeError):
            return False
    
    def _on_ok(self):
        """Handle OK button click."""
        # Validate all times
        for i in range(7):
            start = self._start_vars[i].get()
            end = self._end_vars[i].get()
            
            if not self._validate_time(start):
                messagebox.showerror(
                    "Invalid Time",
                    f"Invalid start time for {self.DAYS[i]}. Use HH:MM format.",
                    parent=self._dialog
                )
                return
            
            if not self._validate_time(end):
                messagebox.showerror(
                    "Invalid Time",
                    f"Invalid end time for {self.DAYS[i]}. Use HH:MM format.",
                    parent=self._dialog
                )
                return
        
        # Build result schedule
        self._result = WeeklySchedule()
        for i in range(7):
            day_schedule = DaySchedule(
                enabled=self._day_vars[i].get(),
                start_time=self._start_vars[i].get(),
                stop_time=self._end_vars[i].get()
            )
            self._result.set_day(i, day_schedule)
        
        self._dialog.destroy()
    
    def _on_cancel(self):
        """Handle Cancel button click."""
        self._result = None
        self._dialog.destroy()
    
    def _on_reset(self):
        """Handle Reset to Defaults button click."""
        default_schedule = WeeklySchedule()
        for i in range(7):
            day_schedule = default_schedule.get_day(i)
            self._day_vars[i].set(day_schedule.enabled)
            self._start_vars[i].set(day_schedule.start_time)
            self._end_vars[i].set(day_schedule.stop_time)
    
    def show(self) -> Optional[WeeklySchedule]:
        """
        Show the dialog and return the result.
        
        Returns:
            The new schedule, or None if cancelled.
        """
        self._dialog.mainloop()
        return self._result


def show_threshold_dialog(current_value: int = 300) -> Optional[int]:
    """
    Show the threshold configuration dialog.
    
    Note: This runs the dialog in a separate thread to avoid blocking.
    Tkinter itself is not thread-safe, but creating a new Tk instance
    per dialog call works for simple use cases.
    
    Args:
        current_value: Current threshold in seconds
        
    Returns:
        New threshold value, or None if cancelled.
    """
    result = [None]
    
    def run_dialog():
        dialog = ThresholdDialog(None, current_value)
        result[0] = dialog.show()
    
    # Run in thread to avoid blocking issues
    thread = threading.Thread(target=run_dialog)
    thread.start()
    thread.join()
    
    return result[0]


def show_schedule_dialog(schedule: Optional[WeeklySchedule] = None) -> Optional[WeeklySchedule]:
    """
    Show the schedule configuration dialog.
    
    Note: This runs the dialog in a separate thread to avoid blocking.
    Tkinter itself is not thread-safe, but creating a new Tk instance
    per dialog call works for simple use cases.
    
    Args:
        schedule: Current schedule
        
    Returns:
        New schedule, or None if cancelled.
    """
    result = [None]
    
    def run_dialog():
        dialog = ScheduleDialog(None, schedule)
        result[0] = dialog.show()
    
    # Run in thread to avoid blocking issues
    thread = threading.Thread(target=run_dialog)
    thread.start()
    thread.join()
    
    return result[0]


def show_error(title: str, message: str) -> None:
    """
    Show an error dialog.
    
    Args:
        title: Dialog title
        message: Error message
    """
    def run_dialog():
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        messagebox.showerror(title, message)
        root.destroy()
    
    thread = threading.Thread(target=run_dialog)
    thread.start()
    thread.join()
