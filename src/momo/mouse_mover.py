"""
Mouse Movement Module

Provides functionality to programmatically move the mouse cursor
to prevent system idle detection.
"""

# Note on imports (response to code review):
# Both 'import ctypes' and 'import ctypes.wintypes' are required:
# - 'import ctypes' provides access to ctypes.windll, ctypes.sizeof, ctypes.POINTER, etc.
# - 'import ctypes.wintypes' must be explicitly imported as it's a submodule that is NOT
#   auto-imported when importing the parent ctypes module.
# The 'from ctypes import ...' imports specific types for cleaner code.
# This is standard Python practice for the ctypes module.
import ctypes
import ctypes.wintypes
from ctypes import c_long, Structure, Union, byref
from typing import Tuple, Callable, Optional
import time


# Windows API constants
INPUT_MOUSE = 0
MOUSEEVENTF_MOVE = 0x0001


class MOUSEINPUT(Structure):
    """Windows MOUSEINPUT structure."""
    _fields_ = [
        ('dx', c_long),
        ('dy', c_long),
        ('mouseData', ctypes.c_ulong),
        ('dwFlags', ctypes.c_ulong),
        ('time', ctypes.c_ulong),
        ('dwExtraInfo', ctypes.POINTER(ctypes.c_ulong)),
    ]


class KEYBDINPUT(Structure):
    """Windows KEYBDINPUT structure (placeholder for union)."""
    _fields_ = [
        ('wVk', ctypes.c_ushort),
        ('wScan', ctypes.c_ushort),
        ('dwFlags', ctypes.c_ulong),
        ('time', ctypes.c_ulong),
        ('dwExtraInfo', ctypes.POINTER(ctypes.c_ulong)),
    ]


class HARDWAREINPUT(Structure):
    """Windows HARDWAREINPUT structure (placeholder for union)."""
    _fields_ = [
        ('uMsg', ctypes.c_ulong),
        ('wParamL', ctypes.c_ushort),
        ('wParamH', ctypes.c_ushort),
    ]


class INPUT_UNION(Union):
    """Union for INPUT structure."""
    _fields_ = [
        ('mi', MOUSEINPUT),
        ('ki', KEYBDINPUT),
        ('hi', HARDWAREINPUT),
    ]


class INPUT(Structure):
    """Windows INPUT structure."""
    _fields_ = [
        ('type', ctypes.c_ulong),
        ('union', INPUT_UNION),
    ]


class MouseMover:
    """
    Handles programmatic mouse movement to prevent system idle.
    
    Moves the mouse by minimal amounts to reset the Windows idle timer
    while being as imperceptible as possible to the user.
    """
    
    def __init__(self):
        """Initialize the mouse mover."""
        self._movement_callback: Optional[Callable[[], None]] = None
        self._movement_complete_callback: Optional[Callable[[], None]] = None
        self._move_distance = 1  # Minimal movement in pixels
    
    def get_cursor_position(self) -> Tuple[int, int]:
        """
        Get the current cursor position.
        
        Returns:
            Tuple of (x, y) coordinates.
        """
        point = ctypes.wintypes.POINT()
        ctypes.windll.user32.GetCursorPos(byref(point))
        return (point.x, point.y)
    
    def set_cursor_position(self, x: int, y: int) -> bool:
        """
        Set the cursor position to specific coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            True if successful, False otherwise.
        """
        return bool(ctypes.windll.user32.SetCursorPos(x, y))
    
    def move_mouse_relative(self, dx: int, dy: int) -> bool:
        """
        Move the mouse relative to its current position using SendInput.
        
        This method uses the Windows SendInput API which properly
        triggers the system's input detection.
        
        Args:
            dx: Horizontal movement in pixels
            dy: Vertical movement in pixels
            
        Returns:
            True if successful, False otherwise.
        
        Note on implementation (response to code review):
            Per Windows API documentation, when MOUSEEVENTF_ABSOLUTE is NOT set,
            dx and dy specify relative movement in pixels. The MOUSEEVENTF_MOVE
            flag alone (without MOUSEEVENTF_ABSOLUTE) correctly interprets dx/dy
            as pixel offsets from the current position. This implementation is
            correct and produces the intended 1-pixel relative movement.
            Reference: https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-mouseinput
        """
        # Create INPUT structure for mouse movement
        mouse_input = INPUT()
        mouse_input.type = INPUT_MOUSE
        mouse_input.union.mi.dx = dx
        mouse_input.union.mi.dy = dy
        mouse_input.union.mi.mouseData = 0
        mouse_input.union.mi.dwFlags = MOUSEEVENTF_MOVE
        mouse_input.union.mi.time = 0
        mouse_input.union.mi.dwExtraInfo = None
        
        # Send the input
        result = ctypes.windll.user32.SendInput(
            1,
            byref(mouse_input),
            ctypes.sizeof(INPUT)
        )
        
        return result == 1
    
    def move_imperceptibly(self) -> bool:
        """
        Perform an imperceptible mouse movement.
        
        Moves the mouse by a minimal amount and then back,
        which is enough to reset the idle timer but barely
        noticeable to the user.
        
        Returns:
            True if successful, False otherwise.
        """
        # Notify that movement is starting
        if self._movement_callback:
            self._movement_callback()
        
        try:
            # Move right by 1 pixel
            success1 = self.move_mouse_relative(self._move_distance, 0)
            
            # Small delay
            time.sleep(0.05)
            
            # Move back left by 1 pixel
            success2 = self.move_mouse_relative(-self._move_distance, 0)
            
            return success1 and success2
        finally:
            # Notify that movement is complete (always called)
            if self._movement_complete_callback:
                self._movement_complete_callback()
    
    def set_movement_callback(self, callback: Callable[[], None]) -> None:
        """
        Set callback to be called when mouse movement starts.
        
        Args:
            callback: Function to call when movement begins.
        """
        self._movement_callback = callback
    
    def set_movement_complete_callback(self, callback: Callable[[], None]) -> None:
        """
        Set callback to be called when mouse movement completes.
        
        Args:
            callback: Function to call when movement ends.
        """
        self._movement_complete_callback = callback
