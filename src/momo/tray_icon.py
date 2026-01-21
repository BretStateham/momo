"""
System Tray UI Module

Provides the system tray icon and context menu for MoMo.
"""


import threading
from typing import Any, Callable, Optional, Tuple
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem, Menu


class TrayIcon:
    """
    Manages the system tray icon and context menu.
    
    Displays a mouse icon that changes to green when actively
    moving the mouse to prevent idle.
    """
    
    # Icon size
    ICON_SIZE = 64
    
    # Colors
    COLOR_NORMAL = (128, 128, 128, 255)      # Gray mouse
    COLOR_ACTIVE = (0, 200, 0, 255)          # Green when active
    COLOR_DISABLED = (100, 100, 100, 128)    # Dimmed when disabled
    COLOR_TRANSPARENT = (0, 0, 0, 0)
    
    def __init__(self):
        """Initialize the tray icon."""
        self._icon: Any = None  # pystray.Icon instance
        self._is_active = False
        self._monitoring_enabled = True
        self._within_schedule = True
        self._schedule_label = "Schedule: Not configured"
        self._lock = threading.RLock()
        
        # Callbacks
        self._on_start_stop: Optional[Callable[[bool], None]] = None
        self._on_configure: Optional[Callable[[], None]] = None
        self._on_exit: Optional[Callable[[], None]] = None
        
        # State
        self._autostart_enabled = False
        self._current_threshold = 300
        
        # Create icons
        self._normal_icon = self._create_mouse_icon(self.COLOR_NORMAL)
        self._active_icon = self._create_mouse_icon(self.COLOR_ACTIVE)
        self._disabled_icon = self._create_mouse_icon(self.COLOR_DISABLED)
    
    def _create_mouse_icon(self, color: Tuple[int, int, int, int]) -> Image.Image:
        """
        Create a simple mouse icon.
        
        Args:
            color: RGBA color tuple for the mouse
            
        Returns:
            PIL Image of the mouse icon
        """
        size = self.ICON_SIZE
        image = Image.new('RGBA', (size, size), self.COLOR_TRANSPARENT)
        draw = ImageDraw.Draw(image)
        
        # Draw a simple mouse shape
        # Mouse body (oval)
        body_margin = size // 8
        draw.ellipse(
            [body_margin, size // 4, size - body_margin, size - body_margin],
            fill=color
        )
        
        # Mouse ears (two small circles at top)
        ear_size = size // 5
        ear_y = size // 4 - ear_size // 2
        
        # Left ear
        left_ear_x = size // 4
        draw.ellipse(
            [left_ear_x - ear_size//2, ear_y,
             left_ear_x + ear_size//2, ear_y + ear_size],
            fill=color
        )
        
        # Right ear
        right_ear_x = size - size // 4
        draw.ellipse(
            [right_ear_x - ear_size//2, ear_y,
             right_ear_x + ear_size//2, ear_y + ear_size],
            fill=color
        )
        
        # Mouse tail (curved line)
        draw.arc(
            [size // 4, size - size // 3, size - size // 4, size],
            start=0, end=180,
            fill=color, width=3
        )
        
        return image
    
    def _get_current_icon(self) -> Image.Image:
        """Get the icon based on current state."""
        with self._lock:
            if not (self._monitoring_enabled and self._within_schedule):
                return self._disabled_icon
            elif self._is_active:
                return self._active_icon
            else:
                return self._normal_icon
    
    def _create_menu(self) -> Menu:
        """Create the context menu."""
        with self._lock:
            if not self._within_schedule:
                monitoring_text = "Monitoring disabled in schedule"
            elif self._monitoring_enabled:
                monitoring_text = "Stop Monitoring"
            else:
                monitoring_text = "Start Monitoring"
            schedule_text = self._schedule_label
        
        return Menu(
            MenuItem(
                monitoring_text,
                self._on_start_stop_clicked,
                enabled=lambda item: self._within_schedule
            ),
            MenuItem(
                schedule_text,
                None,
                enabled=False
            ),
            Menu.SEPARATOR,
            MenuItem(
                "Configuration...",
                self._on_configure_clicked
            ),
            Menu.SEPARATOR,
            MenuItem(
                "Exit",
                self._on_exit_clicked
            ),
        )
    
    def _on_start_stop_clicked(self, icon, item):
        """Handle start/stop menu click."""
        with self._lock:
            if not self._within_schedule:
                return
            self._monitoring_enabled = not self._monitoring_enabled
            new_state = self._monitoring_enabled
        self._update_icon()
        if self._on_start_stop:
            self._on_start_stop(new_state)
    
    def _on_configure_clicked(self, icon, item):
        """Handle configuration click."""
        if self._on_configure:
            self._on_configure()
    
    def _on_exit_clicked(self, icon, item):
        """Handle exit click."""
        # Stop the icon first, then call callback
        self.stop()
        if self._on_exit:
            self._on_exit()
    
    def _update_icon(self):
        """Update the tray icon based on current state."""
        icon_obj = None
        new_icon = None
        new_menu = None
        with self._lock:
            if self._icon:
                icon_obj = self._icon
                new_icon = self._get_current_icon()
                new_menu = self._create_menu()

        if icon_obj:
            icon_obj.icon = new_icon
            icon_obj.menu = new_menu

    def set_active(self, is_active: bool) -> None:
        """
        Set the active state (green icon when moving mouse).
        
        Args:
            is_active: True when actively moving mouse
        """
        with self._lock:
            self._is_active = is_active
        self._update_icon()
    
    def set_monitoring(self, is_monitoring: bool) -> None:
        """
        Set the monitoring state.
        
        Args:
            is_monitoring: True when monitoring is enabled
        """
        with self._lock:
            self._monitoring_enabled = is_monitoring
        self._update_icon()

    def set_schedule_status(self, within_schedule: bool, schedule_label: str) -> None:
        """Set the schedule status and label used in the menu."""
        with self._lock:
            self._within_schedule = within_schedule
            self._schedule_label = schedule_label
        self._update_icon()
    
    def set_autostart(self, enabled: bool) -> None:
        """
        Set the autostart state for menu display.
        
        Args:
            enabled: True if autostart is enabled
        """
        with self._lock:
            self._autostart_enabled = enabled
        self._update_icon()
    
    def set_threshold(self, seconds: int) -> None:
        """
        Set the current threshold for menu display.
        
        Args:
            seconds: Current threshold in seconds
        """
        with self._lock:
            self._current_threshold = seconds
        self._update_icon()
    
    # Callback setters
    def set_on_start_stop(self, callback: Callable[[bool], None]) -> None:
        """Set callback for start/stop toggle."""
        self._on_start_stop = callback
    
    def set_on_configure(self, callback: Callable[[], None]) -> None:
        """Set callback for configuration dialog."""
        self._on_configure = callback
    
    def set_on_exit(self, callback: Callable[[], None]) -> None:
        """Set callback for exit."""
        self._on_exit = callback
    
    def run(self) -> None:
        """
        Run the tray icon (blocking).
        
        This should be called from the main thread.
        """
        self._icon = pystray.Icon(
            name="MoMo",
            icon=self._get_current_icon(),
            title="MoMo - Mouse Mover",
            menu=self._create_menu()
        )
        self._icon.run()
    
    def run_detached(self) -> None:
        """
        Run the tray icon in a separate thread.
        
        Use this when you need the tray icon to run alongside other code.
        """
        self._icon = pystray.Icon(
            name="MoMo",
            icon=self._get_current_icon(),
            title="MoMo - Mouse Mover",
            menu=self._create_menu()
        )
        self._icon.run_detached()
    
    def stop(self) -> None:
        """Stop the tray icon."""
        icon_to_stop = None
        with self._lock:
            if self._icon:
                icon_to_stop = self._icon
                self._icon = None

        if icon_to_stop:
            icon_to_stop.stop()
    
    def show_notification(self, title: str, message: str) -> None:
        """
        Show a notification from the tray icon.
        
        Args:
            title: Notification title
            message: Notification message
        """
        icon_obj = None
        with self._lock:
            if self._icon:
                icon_obj = self._icon

        if icon_obj:
            icon_obj.notify(message, title)
