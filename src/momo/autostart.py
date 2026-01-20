"""
Auto-Start Module

Handles registering and unregistering MoMo to start with Windows.
Uses the current user's registry Run key to avoid requiring admin privileges.
"""

import os
import sys
import winreg
from typing import Optional


class AutoStartManager:
    """
    Manages Windows auto-start registration.
    
    Uses the HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run
    registry key, which does not require administrator privileges.
    """
    
    APP_NAME = "MoMo"
    REGISTRY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
    
    def __init__(self, executable_path: Optional[str] = None):
        """
        Initialize the auto-start manager.
        
        Args:
            executable_path: Path to the executable. If not provided,
                           uses the current executable path.
        """
        if executable_path:
            self._executable_path = executable_path
        else:
            self._executable_path = self._get_executable_path()
    
    def _get_executable_path(self) -> str:
        """Get the path to the current executable."""
        if getattr(sys, 'frozen', False):
            # Running as compiled executable - quote path for spaces
            return f'"{sys.executable}"'
        else:
            # Running as script - use pythonw to avoid console
            python_path = sys.executable
            script_path = os.path.abspath(sys.argv[0])
            return f'"{python_path}" "{script_path}"'
    
    def is_enabled(self) -> bool:
        """
        Check if auto-start is currently enabled.
        
        Returns:
            True if auto-start is enabled, False otherwise.
        """
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.REGISTRY_PATH,
                0,
                winreg.KEY_READ
            ) as key:
                try:
                    value, _ = winreg.QueryValueEx(key, self.APP_NAME)
                    return bool(value)
                except FileNotFoundError:
                    return False
        except OSError:
            return False
    
    def enable(self) -> bool:
        """
        Enable auto-start with Windows.
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.REGISTRY_PATH,
                0,
                winreg.KEY_SET_VALUE
            ) as key:
                winreg.SetValueEx(
                    key,
                    self.APP_NAME,
                    0,
                    winreg.REG_SZ,
                    self._executable_path
                )
            return True
        except OSError as e:
            print(f"Failed to enable auto-start: {e}")
            return False
    
    def disable(self) -> bool:
        """
        Disable auto-start with Windows.
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.REGISTRY_PATH,
                0,
                winreg.KEY_SET_VALUE
            ) as key:
                try:
                    winreg.DeleteValue(key, self.APP_NAME)
                except FileNotFoundError:
                    # Already disabled
                    pass
            return True
        except OSError as e:
            print(f"Failed to disable auto-start: {e}")
            return False
    
    def set_enabled(self, enabled: bool) -> bool:
        """
        Set auto-start enabled state.
        
        Args:
            enabled: True to enable, False to disable
            
        Returns:
            True if successful, False otherwise.
        """
        if enabled:
            return self.enable()
        else:
            return self.disable()
    
    def get_registered_path(self) -> Optional[str]:
        """
        Get the currently registered executable path.
        
        Returns:
            The registered path, or None if not registered.
        """
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.REGISTRY_PATH,
                0,
                winreg.KEY_READ
            ) as key:
                try:
                    value, _ = winreg.QueryValueEx(key, self.APP_NAME)
                    return value
                except FileNotFoundError:
                    return None
        except OSError:
            return None
