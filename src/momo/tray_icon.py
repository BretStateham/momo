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
        self._is_monitoring = True
        self._lock = threading.RLock()
        
        # Callbacks
        self._on_start_stop: Optional[Callable[[bool], None]] = None
        self._on_configure_threshold: Optional[Callable[[], None]] = None
        self._on_configure_schedule: Optional[Callable[[], None]] = None
        self._on_toggle_autostart: Optional[Callable[[bool], None]] = None
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
            if not self._is_monitoring:
                return self._disabled_icon
            elif self._is_active:
                return self._active_icon
            else:
                return self._normal_icon
    
    def _create_menu(self) -> Menu:
        """Create the context menu."""
        with self._lock:
            monitoring_text = "Stop Monitoring" if self._is_monitoring else "Start Monitoring"
            autostart_text = "✓ Start with Windows" if self._autostart_enabled else "Start with Windows"
        
        return Menu(
            MenuItem(
                monitoring_text,
                self._on_start_stop_clicked
            ),
            Menu.SEPARATOR,
            MenuItem(
                f"Idle Threshold: {self._current_threshold}s",
                self._on_threshold_clicked
            ),
            MenuItem(
                "Configure Schedule...",
                self._on_schedule_clicked
            ),
            Menu.SEPARATOR,
            MenuItem(
                autostart_text,
                self._on_autostart_clicked,
                checked=lambda item: self._autostart_enabled
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
            self._is_monitoring = not self._is_monitoring
            new_state = self._is_monitoring
        self._update_icon()
        if self._on_start_stop:
            self._on_start_stop(new_state)
    
    def _on_threshold_clicked(self, icon, item):
        """Handle threshold configuration click."""
        if self._on_configure_threshold:
            self._on_configure_threshold()
    
    def _on_schedule_clicked(self, icon, item):
        """Handle schedule configuration click."""
        if self._on_configure_schedule:
            self._on_configure_schedule()
    
    def _on_autostart_clicked(self, icon, item):
        """Handle autostart toggle click."""
        with self._lock:
            desired_state = not self._autostart_enabled
        if self._on_toggle_autostart:
            # Let the callback handle the state change and update UI
            # The callback is responsible for calling set_autostart() on success
            self._on_toggle_autostart(desired_state)
        else:
            # No callback registered; just update local state
            with self._lock:
                self._autostart_enabled = desired_state
            self._update_icon()
    
    def _on_exit_clicked(self, icon, item):
        """Handle exit click."""
        # Stop the icon first, then call callback
        self.stop()
        if self._on_exit:
            self._on_exit()
    
    def _update_icon(self):
        """Update the tray icon based on current state."""
        with self._lock:
            if self._icon:
                self._icon.icon = self._get_current_icon()
                self._icon.menu = self._create_menu()
    
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
            self._is_monitoring = is_monitoring
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
    
    def set_on_configure_threshold(self, callback: Callable[[], None]) -> None:
        """Set callback for threshold configuration."""
        self._on_configure_threshold = callback
    
    def set_on_configure_schedule(self, callback: Callable[[], None]) -> None:
        """Set callback for schedule configuration."""
        self._on_configure_schedule = callback
    
    def set_on_toggle_autostart(self, callback: Callable[[bool], None]) -> None:
        """Set callback for autostart toggle."""
        self._on_toggle_autostart = callback
    
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
        with self._lock:
            if self._icon:
                self._icon.stop()
                self._icon = None
    
    def show_notification(self, title: str, message: str) -> None:
        """
        Show a notification from the tray icon.
        
        Args:
            title: Notification title
            message: Notification message
        """
        with self._lock:
            if self._icon:
                self._icon.notify(message, title)
