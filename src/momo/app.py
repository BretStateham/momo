"""
MoMo - Main Application Module

The main entry point that coordinates all components:
- Idle detection
- Mouse movement
- System tray icon
- Settings management
- Schedule management
- Auto-start
"""

import sys
import threading
import time
from typing import Optional

from .idle_detector import IdleDetector
from .mouse_mover import MouseMover
from .settings import SettingsManager, Settings
from .schedule import ScheduleManager
from .tray_icon import TrayIcon
from .autostart import AutoStartManager
from .dialogs import show_threshold_dialog, show_schedule_dialog, show_error


class MoMoApp:
    """
    Main MoMo application class.
    
    Coordinates all components to provide the idle prevention functionality.
    """
    
    def __init__(self):
        """Initialize the MoMo application."""
        # Initialize components
        self._settings_manager = SettingsManager()
        self._settings = self._settings_manager.load()
        
        self._idle_detector = IdleDetector(self._settings.idle_threshold_seconds)
        self._mouse_mover = MouseMover()
        self._schedule_manager = ScheduleManager(self._settings.schedule)
        self._autostart_manager = AutoStartManager()
        self._tray_icon = TrayIcon()
        
        # State
        self._running = False
        self._is_moving = False
        self._active_icon_timer: Optional[threading.Timer] = None
        
        # Set up callbacks
        self._setup_callbacks()
        
        # Sync autostart state
        self._tray_icon.set_autostart(self._autostart_manager.is_enabled())
        self._tray_icon.set_threshold(self._settings.idle_threshold_seconds)
        self._tray_icon.set_monitoring(self._settings.monitoring_enabled)
    
    def _setup_callbacks(self):
        """Set up callbacks between components."""
        # Idle detector callback
        self._idle_detector.set_idle_callback(self._on_idle_detected)
        
        # Mouse mover callbacks
        self._mouse_mover.set_movement_callback(self._on_mouse_movement_start)
        self._mouse_mover.set_movement_complete_callback(self._on_mouse_movement_complete)
        
        # Tray icon callbacks
        self._tray_icon.set_on_start_stop(self._on_monitoring_toggled)
        self._tray_icon.set_on_configure_threshold(self._on_configure_threshold)
        self._tray_icon.set_on_configure_schedule(self._on_configure_schedule)
        self._tray_icon.set_on_toggle_autostart(self._on_autostart_toggled)
        self._tray_icon.set_on_exit(self._on_exit)
    
    def _on_idle_detected(self):
        """Called when idle threshold is exceeded."""
        # Check if monitoring is enabled
        if not self._settings.monitoring_enabled:
            return
        
        # Check if within schedule
        if not self._schedule_manager.is_within_schedule():
            return
        
        # Prevent re-entry while already moving
        if self._is_moving:
            return
        
        # Move the mouse
        self._mouse_mover.move_imperceptibly()
    
    def _on_mouse_movement_start(self):
        """Called when mouse movement starts."""
        self._is_moving = True
        self._tray_icon.set_active(True)
    
    def _on_mouse_movement_complete(self):
        """Called when mouse movement completes."""
        # Keep the green icon visible for a short time
        if self._active_icon_timer:
            self._active_icon_timer.cancel()
        
        self._active_icon_timer = threading.Timer(
            1.5,  # Show green icon for 1.5 seconds
            self._reset_active_icon
        )
        self._active_icon_timer.daemon = True
        self._active_icon_timer.start()
    
    def _reset_active_icon(self):
        """Reset the tray icon to normal state."""
        self._is_moving = False
        self._tray_icon.set_active(False)
    
    def _on_monitoring_toggled(self, is_enabled: bool):
        """Called when monitoring is toggled from tray menu."""
        self._settings.monitoring_enabled = is_enabled
        self._settings_manager.save()
        
        if is_enabled:
            self._idle_detector.start_monitoring()
        else:
            self._idle_detector.stop_monitoring()
    
    def _on_configure_threshold(self):
        """Called when threshold configuration is requested."""
        result = show_threshold_dialog(self._settings.idle_threshold_seconds)
        
        if result is not None:
            self._settings.idle_threshold_seconds = result
            self._idle_detector.threshold_seconds = result
            self._settings_manager.save()
            self._tray_icon.set_threshold(result)
    
    def _on_configure_schedule(self):
        """Called when schedule configuration is requested."""
        result = show_schedule_dialog(self._settings.schedule)
        
        if result is not None:
            self._settings.schedule = result
            self._schedule_manager.schedule = result
            self._settings_manager.save()
    
    def _on_autostart_toggled(self, is_enabled: bool):
        """Called when autostart is toggled from tray menu."""
        success = self._autostart_manager.set_enabled(is_enabled)
        
        if success:
            self._settings.auto_start = is_enabled
            self._settings_manager.save()
        else:
            # Revert the UI state if failed
            self._tray_icon.set_autostart(not is_enabled)
            show_error(
                "Auto-Start Error",
                "Failed to update auto-start setting. Please try again."
            )
    
    def _on_exit(self):
        """Called when exit is requested from tray menu."""
        # Cleanup is handled by stop() which is called by the tray icon
        self._idle_detector.stop_monitoring()
        if self._active_icon_timer:
            self._active_icon_timer.cancel()
    
    def run(self):
        """
        Run the MoMo application.
        
        This is the main entry point that starts all components
        and runs the event loop.
        """
        self._running = True
        
        # Start monitoring if enabled in settings
        if self._settings.monitoring_enabled:
            self._idle_detector.start_monitoring()
        
        try:
            # Run the tray icon (blocking)
            self._tray_icon.run()
        except Exception as e:
            show_error("MoMo Error", f"An unexpected error occurred:\n\n{e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the MoMo application."""
        self._running = False
        
        # Stop the idle detector
        self._idle_detector.stop_monitoring()
        
        # Cancel any pending timers
        if self._active_icon_timer:
            self._active_icon_timer.cancel()
        
        # Stop the tray icon
        self._tray_icon.stop()


def main():
    """Main entry point for the application."""
    try:
        app = MoMoApp()
        app.run()
    except Exception as e:
        show_error("MoMo Startup Error", f"Failed to start MoMo:\n\n{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
