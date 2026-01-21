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
from datetime import datetime
from typing import Optional

from .idle_detector import IdleDetector
from .mouse_mover import MouseMover
from .settings import SettingsManager
from .schedule import ScheduleManager
from .tray_icon import TrayIcon
from .autostart import AutoStartManager
from .dialogs import show_configuration_dialog, show_error


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
        self._schedule_timer: Optional[threading.Timer] = None
        self._schedule_refresh_interval = 60.0
        
        # Set up callbacks
        self._setup_callbacks()
        
        # Sync autostart state
        autostart_enabled = self._autostart_manager.is_enabled()
        if self._settings.auto_start != autostart_enabled:
            self._settings.auto_start = autostart_enabled
            if not self._settings_manager.save():
                show_error(
                    "Settings Error",
                    "Failed to save auto-start setting. Changes may not persist."
                )
        self._tray_icon.set_autostart(autostart_enabled)
        self._tray_icon.set_threshold(self._settings.idle_threshold_seconds)
        self._tray_icon.set_monitoring(self._settings.monitoring_enabled)
        self._update_schedule_state(apply_monitoring=False)
    
    def _setup_callbacks(self):
        """Set up callbacks between components."""
        # Idle detector callback
        self._idle_detector.set_idle_callback(self._on_idle_detected)
        
        # Mouse mover callbacks
        self._mouse_mover.set_movement_callback(self._on_mouse_movement_start)
        self._mouse_mover.set_movement_complete_callback(self._on_mouse_movement_complete)
        
        # Tray icon callbacks
        self._tray_icon.set_on_start_stop(self._on_monitoring_toggled)
        self._tray_icon.set_on_configure(self._on_configure)
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
        # Reset movement flag immediately so we can respond to new idle events
        self._is_moving = False
        
        # Keep the green icon visible for a short time (visual feedback only)
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
        self._tray_icon.set_active(False)
    
    def _on_monitoring_toggled(self, is_enabled: bool):
        """Called when monitoring is toggled from tray menu."""
        self._settings.monitoring_enabled = is_enabled
        if not self._settings_manager.save():
            show_error(
                "Settings Error",
                "Failed to save monitoring setting. Changes may not persist."
            )
        self._tray_icon.set_monitoring(is_enabled)
        self._apply_monitoring_state()
    
    def _on_configure(self):
        """Called when unified configuration is requested."""
        current_autostart = self._autostart_manager.is_enabled()
        result = show_configuration_dialog(self._settings, current_autostart)

        if result is None:
            return

        desired_autostart = result.auto_start
        if desired_autostart != current_autostart:
            success = self._autostart_manager.set_enabled(desired_autostart)
            if not success:
                show_error(
                    "Auto-Start Error",
                    "Failed to update auto-start setting. Please try again."
                )
                desired_autostart = current_autostart

        self._settings.idle_threshold_seconds = result.idle_threshold_seconds
        self._settings.schedule = result.schedule
        self._settings.auto_start = desired_autostart

        self._idle_detector.threshold_seconds = result.idle_threshold_seconds
        self._schedule_manager.schedule = result.schedule

        self._tray_icon.set_autostart(desired_autostart)
        self._tray_icon.set_threshold(result.idle_threshold_seconds)
        self._tray_icon.set_monitoring(self._settings.monitoring_enabled)
        self._update_schedule_state()

        if not self._settings_manager.save():
            show_error(
                "Settings Error",
                "Failed to save configuration. Changes may not persist."
            )

    def _apply_monitoring_state(self, within_schedule: Optional[bool] = None) -> None:
        """Start or stop monitoring based on user and schedule state."""
        if within_schedule is None:
            within_schedule = self._schedule_manager.is_within_schedule()
        should_monitor = self._settings.monitoring_enabled and within_schedule

        if should_monitor:
            self._idle_detector.start_monitoring()
        else:
            self._idle_detector.stop_monitoring()

    def _get_schedule_label(self) -> str:
        """Return a schedule label for the tray menu."""
        day_index = datetime.now().weekday()
        day_name = self._schedule_manager.get_day_name(day_index)
        day_schedule = self._schedule_manager.get_current_day_schedule()

        if not day_schedule.enabled:
            return f"Schedule: {day_name} disabled"
        return f"Schedule: {day_name} {day_schedule.start_time}–{day_schedule.stop_time}"

    def _update_schedule_state(self, apply_monitoring: bool = True) -> None:
        within_schedule = self._schedule_manager.is_within_schedule()
        schedule_label = self._get_schedule_label()
        self._tray_icon.set_schedule_status(within_schedule, schedule_label)
        if apply_monitoring and self._running:
            self._apply_monitoring_state(within_schedule)

    def _schedule_tick(self) -> None:
        if not self._running:
            return
        self._update_schedule_state()
        self._schedule_timer = threading.Timer(self._schedule_refresh_interval, self._schedule_tick)
        self._schedule_timer.daemon = True
        self._schedule_timer.start()
    
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
        self._update_schedule_state()
        self._schedule_timer = threading.Timer(self._schedule_refresh_interval, self._schedule_tick)
        self._schedule_timer.daemon = True
        self._schedule_timer.start()
        
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
        if self._schedule_timer:
            self._schedule_timer.cancel()
        
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
