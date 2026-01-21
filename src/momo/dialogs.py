"""
Configuration Dialogs Module

Provides dialog windows for configuring idle threshold and schedule.
Uses tkinter for simple, native Windows dialogs.

Note: These dialogs must be run from the main thread or use proper
thread marshalling when called from pystray callbacks.
"""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional
import threading
from .settings import Settings, WeeklySchedule, DaySchedule


class ConfigurationDialog:
    """Unified configuration dialog for MoMo settings."""

    DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    def __init__(
        self,
        parent: Optional[tk.Tk] = None,
        settings: Optional[Settings] = None,
        autostart_enabled: bool = False,
    ):
        self._settings = settings or Settings()
        self._result: Optional[Settings] = None

        if parent:
            self._dialog = tk.Toplevel(parent)
        else:
            self._dialog = tk.Tk()

        self._dialog.title("MoMo - Mouse Mover")
        self._dialog.resizable(False, False)
        self._dialog.geometry("720x560")
        self._dialog.attributes('-topmost', True)
        self._dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)

        self._autostart_var = tk.BooleanVar(value=autostart_enabled)
        self._threshold_var = tk.StringVar(value=str(self._settings.idle_threshold_seconds))

        self._day_vars = {}
        self._start_vars = {}
        self._end_vars = {}

        self._apply_style()
        self._create_widgets()
        self._center_window()

        self._dialog.focus_force()
        self._dialog.lift()

    def _apply_style(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except tk.TclError:
            # If the 'clam' theme is not available, fall back to default.
            pass

        style.configure('Header.TLabel', font=('Segoe UI', 14, 'bold'))
        style.configure('Subheader.TLabel', font=('Segoe UI', 10), foreground='#666666')
        style.configure('Section.TLabelframe', padding=(12, 8))
        style.configure('Section.TLabelframe.Label', font=('Segoe UI', 10, 'bold'))
        style.configure('Primary.TButton', font=('Segoe UI', 10, 'bold'))

    def _center_window(self) -> None:
        self._dialog.update_idletasks()
        width = 720
        height = 560
        x = (self._dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self._dialog.winfo_screenheight() // 2) - (height // 2)
        self._dialog.geometry(f'{width}x{height}+{x}+{y}')

    def _create_widgets(self) -> None:
        container = ttk.Frame(self._dialog, padding=20)
        container.pack(fill=tk.BOTH, expand=True)

        header = ttk.Label(container, text="MoMo - Mouse Mover", style='Header.TLabel')
        header.pack(anchor=tk.W)
        subheader = ttk.Label(
            container,
            text="Configure idle threshold, schedule, and startup behavior.",
            style='Subheader.TLabel'
        )
        subheader.pack(anchor=tk.W, pady=(2, 14))

        notebook = ttk.Notebook(container)
        notebook.pack(fill=tk.BOTH, expand=True)

        general_tab = ttk.Frame(notebook, padding=12)
        schedule_tab = ttk.Frame(notebook, padding=12)
        notebook.add(general_tab, text="General")
        notebook.add(schedule_tab, text="Schedule")

        general_group = ttk.LabelFrame(general_tab, text="Idle Detection", style='Section.TLabelframe')
        general_group.pack(fill=tk.X, pady=(0, 12))

        ttk.Label(general_group, text="Idle threshold (seconds):").grid(row=0, column=0, sticky=tk.W)
        threshold_entry = ttk.Entry(general_group, textvariable=self._threshold_var, width=12)
        threshold_entry.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        ttk.Label(
            general_group,
            text="Move the mouse after this many seconds of inactivity.",
            foreground='#666666'
        ).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(4, 0))

        startup_group = ttk.LabelFrame(general_tab, text="Startup", style='Section.TLabelframe')
        startup_group.pack(fill=tk.X)

        ttk.Checkbutton(
            startup_group,
            text="Start with Windows",
            variable=self._autostart_var
        ).pack(anchor=tk.W)
        ttk.Label(
            startup_group,
            text="Enable this to launch MoMo when you sign in.",
            foreground='#666666'
        ).pack(anchor=tk.W, pady=(4, 0))

        self._build_schedule_tab(schedule_tab)

        button_row = ttk.Frame(container)
        button_row.pack(fill=tk.X, pady=(12, 0))

        reset_button = ttk.Button(button_row, text="Reset Schedule", command=self._on_reset)
        reset_button.pack(side=tk.LEFT)

        cancel_button = ttk.Button(button_row, text="Cancel", command=self._on_cancel)
        cancel_button.pack(side=tk.RIGHT, padx=(8, 0))

        ok_button = ttk.Button(button_row, text="Save", style='Primary.TButton', command=self._on_ok)
        ok_button.pack(side=tk.RIGHT)

        self._dialog.bind('<Return>', lambda e: self._on_ok())
        self._dialog.bind('<Escape>', lambda e: self._on_cancel())

    def _build_schedule_tab(self, parent: ttk.Frame) -> None:
        schedule_group = ttk.LabelFrame(parent, text="Active Schedule", style='Section.TLabelframe')
        schedule_group.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            schedule_group,
            text="MoMo will only move the mouse during the scheduled times.",
            foreground='#666666'
        ).pack(anchor=tk.W, pady=(0, 10))

        grid = ttk.Frame(schedule_group)
        grid.pack(fill=tk.X)

        ttk.Label(grid, text="Day", width=12).grid(row=0, column=0, sticky=tk.W, padx=(0, 8))
        ttk.Label(grid, text="Enabled", width=8).grid(row=0, column=1, padx=5)
        ttk.Label(grid, text="Start", width=10).grid(row=0, column=2, padx=5)
        ttk.Label(grid, text="End", width=10).grid(row=0, column=3, padx=5)

        for i, day in enumerate(self.DAYS):
            day_schedule = self._settings.schedule.get_day(i)

            ttk.Label(grid, text=day, width=12).grid(row=i + 1, column=0, sticky=tk.W, pady=4, padx=(0, 8))

            enabled_var = tk.BooleanVar(value=day_schedule.enabled)
            self._day_vars[i] = enabled_var
            ttk.Checkbutton(grid, variable=enabled_var).grid(row=i + 1, column=1, pady=4)

            start_var = tk.StringVar(value=day_schedule.start_time)
            self._start_vars[i] = start_var
            ttk.Entry(grid, textvariable=start_var, width=8).grid(row=i + 1, column=2, padx=5, pady=4)

            end_var = tk.StringVar(value=day_schedule.stop_time)
            self._end_vars[i] = end_var
            ttk.Entry(grid, textvariable=end_var, width=8).grid(row=i + 1, column=3, padx=5, pady=4)

        ttk.Label(
            schedule_group,
            text="Times use 24-hour format (HH:MM). Example: 08:00, 17:00",
            foreground='#666666'
        ).pack(anchor=tk.W, pady=(10, 0))

    def _validate_time(self, time_str: str) -> bool:
        try:
            if not isinstance(time_str, str):
                return False
            parts = time_str.split(':')
            if len(parts) != 2:
                return False
            hours_str, minutes_str = parts[0], parts[1]
            if len(hours_str) != 2 or len(minutes_str) != 2:
                return False
            if not (hours_str.isdigit() and minutes_str.isdigit()):
                return False
            hours = int(hours_str)
            minutes = int(minutes_str)
            return 0 <= hours <= 23 and 0 <= minutes <= 59
        except (ValueError, AttributeError):
            return False

    def _on_ok(self) -> None:
        try:
            threshold_value = int(self._threshold_var.get())
            if threshold_value <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Invalid Value",
                "Please enter a positive integer for the idle threshold.",
                parent=self._dialog
            )
            return

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

        updated_schedule = WeeklySchedule()
        for i in range(7):
            day_schedule = DaySchedule(
                enabled=self._day_vars[i].get(),
                start_time=self._start_vars[i].get(),
                stop_time=self._end_vars[i].get(),
            )
            updated_schedule.set_day(i, day_schedule)

        self._result = Settings(
            idle_threshold_seconds=threshold_value,
            auto_start=self._autostart_var.get(),
            monitoring_enabled=self._settings.monitoring_enabled,
            schedule=updated_schedule,
        )
        self._dialog.destroy()

    def _on_cancel(self) -> None:
        self._result = None
        self._dialog.destroy()

    def _on_reset(self) -> None:
        default_schedule = WeeklySchedule()
        for i in range(7):
            day_schedule = default_schedule.get_day(i)
            self._day_vars[i].set(day_schedule.enabled)
            self._start_vars[i].set(day_schedule.start_time)
            self._end_vars[i].set(day_schedule.stop_time)

    def show(self) -> Optional[Settings]:
        self._dialog.mainloop()
        return self._result


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
    
    Note on threading approach (response to code review):
        While Tkinter is not officially thread-safe for sharing widgets across
        threads, creating a completely isolated Tk instance in a dedicated thread
        (with its own mainloop) is a well-established pattern that works reliably.
        Each dialog creates its own Tk root, runs its own mainloop, and destroys
        itself - no Tk objects are shared between threads. This approach is used
        because pystray callbacks run in a background thread, and we need to show
        modal dialogs without blocking the tray icon's event loop.
    
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
    
    Note on threading approach (response to code review):
        While Tkinter is not officially thread-safe for sharing widgets across
        threads, creating a completely isolated Tk instance in a dedicated thread
        (with its own mainloop) is a well-established pattern that works reliably.
        Each dialog creates its own Tk root, runs its own mainloop, and destroys
        itself - no Tk objects are shared between threads. This approach is used
        because pystray callbacks run in a background thread, and we need to show
        modal dialogs without blocking the tray icon's event loop.
    
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


def show_configuration_dialog(
    settings: Settings,
    autostart_enabled: bool,
) -> Optional[Settings]:
    """
    Show unified configuration dialog.

    Args:
        settings: Current settings
        autostart_enabled: Current autostart registry state

    Returns:
        Updated settings or None if cancelled.
    """
    result: list[Optional[Settings]] = [None]

    def run_dialog():
        dialog = ConfigurationDialog(None, settings, autostart_enabled)
        result[0] = dialog.show()

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
