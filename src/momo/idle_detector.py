"""
Idle Detection Module

Monitors user activity (mouse and keyboard) to determine idle state
using Windows GetLastInputInfo API.
"""

from ctypes import Structure, c_uint, sizeof, byref, windll
from typing import Callable, Optional
import threading


class LASTINPUTINFO(Structure):
    """Windows LASTINPUTINFO structure."""
    _fields_ = [
        ('cbSize', c_uint),
        ('dwTime', c_uint),
    ]


class IdleDetector:
    """
    Monitors user idle time using Windows API.
    
    Uses GetLastInputInfo to detect the last time user provided
    any input (mouse movement or keyboard).
    """
    
    def __init__(self, threshold_seconds: int = 300):
        """
        Initialize the idle detector.
        
        Args:
            threshold_seconds: Number of seconds of inactivity before
                             considered idle. Default is 300 (5 minutes).
        """
        self._threshold_seconds = threshold_seconds
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._on_idle_callback: Optional[Callable[[], None]] = None
        self._check_interval = 1.0  # Check every second
        self._stop_event = threading.Event()
    
    @property
    def threshold_seconds(self) -> int:
        """Get the idle threshold in seconds."""
        return self._threshold_seconds
    
    @threshold_seconds.setter
    def threshold_seconds(self, value: int) -> None:
        """Set the idle threshold in seconds."""
        if value <= 0:
            raise ValueError("Threshold must be positive")
        self._threshold_seconds = value
    
    @property
    def is_monitoring(self) -> bool:
        """Check if idle monitoring is active."""
        return self._monitoring
    
    def get_idle_time_seconds(self) -> float:
        """
        Get the current idle time in seconds.
        
        Returns:
            Number of seconds since the last user input.
        """
        last_input_info = LASTINPUTINFO()
        last_input_info.cbSize = sizeof(LASTINPUTINFO)
        
        if windll.user32.GetLastInputInfo(byref(last_input_info)):
            # GetTickCount64 returns milliseconds since system start (64-bit, no wrap)
            current_tick = windll.kernel32.GetTickCount64()
            # dwTime is still 32-bit, so handle potential wrap-around
            elapsed_ms = (current_tick - last_input_info.dwTime) & 0xFFFFFFFF
            return elapsed_ms / 1000.0
        
        return 0.0
    
    def is_idle(self) -> bool:
        """
        Check if the user is currently idle.
        
        Returns:
            True if idle time exceeds threshold, False otherwise.
        """
        return self.get_idle_time_seconds() >= self._threshold_seconds
    
    def set_idle_callback(self, callback: Callable[[], None]) -> None:
        """
        Set the callback function to be called when idle is detected.
        
        Args:
            callback: Function to call when user becomes idle.
        """
        self._on_idle_callback = callback
    
    def start_monitoring(self) -> None:
        """Start monitoring for idle state in a background thread."""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._stop_event.clear()
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="IdleMonitor"
        )
        self._monitor_thread.start()
    
    def stop_monitoring(self) -> None:
        """Stop the idle monitoring thread."""
        if not self._monitoring:
            return
        
        self._monitoring = False
        self._stop_event.set()
        
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2.0)
        
        self._monitor_thread = None
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop that runs in a background thread."""
        while not self._stop_event.is_set():
            if self.is_idle() and self._on_idle_callback:
                self._on_idle_callback()
            
            # Wait for the check interval or until stop is requested
            self._stop_event.wait(self._check_interval)
