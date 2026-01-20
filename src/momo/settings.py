"""
Configuration and Settings Module

Handles loading, saving, and managing application settings.
Settings are stored in a JSON file in the same directory as the executable.
"""

import json
import os
import sys
from dataclasses import dataclass, field, asdict
from typing import Callable, Dict, List, Optional
from pathlib import Path


@dataclass
class DaySchedule:
    """Schedule configuration for a single day."""
    enabled: bool = True
    start_time: str = "08:00"  # 24-hour format HH:MM
    stop_time: str = "17:00"   # 24-hour format HH:MM
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DaySchedule':
        """Create from dictionary."""
        return cls(
            enabled=data.get('enabled', True),
            start_time=data.get('start_time', '08:00'),
            stop_time=data.get('stop_time', '17:00')
        )


@dataclass
class WeeklySchedule:
    """Weekly schedule configuration."""
    monday: DaySchedule = field(default_factory=lambda: DaySchedule())
    tuesday: DaySchedule = field(default_factory=lambda: DaySchedule())
    wednesday: DaySchedule = field(default_factory=lambda: DaySchedule())
    thursday: DaySchedule = field(default_factory=lambda: DaySchedule())
    friday: DaySchedule = field(default_factory=lambda: DaySchedule())
    saturday: DaySchedule = field(default_factory=lambda: DaySchedule(enabled=False))
    sunday: DaySchedule = field(default_factory=lambda: DaySchedule(enabled=False))
    
    def get_day(self, day_index: int) -> DaySchedule:
        """
        Get schedule for a day by index (0=Monday, 6=Sunday).
        
        Args:
            day_index: Day of week (0-6, Monday-Sunday)
            
        Returns:
            DaySchedule for the specified day.
        """
        days = [
            self.monday, self.tuesday, self.wednesday,
            self.thursday, self.friday, self.saturday, self.sunday
        ]
        return days[day_index]
    
    def set_day(self, day_index: int, schedule: DaySchedule) -> None:
        """
        Set schedule for a day by index.
        
        Args:
            day_index: Day of week (0-6, Monday-Sunday)
            schedule: DaySchedule to set
        """
        day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 
                     'friday', 'saturday', 'sunday']
        setattr(self, day_names[day_index], schedule)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'monday': self.monday.to_dict(),
            'tuesday': self.tuesday.to_dict(),
            'wednesday': self.wednesday.to_dict(),
            'thursday': self.thursday.to_dict(),
            'friday': self.friday.to_dict(),
            'saturday': self.saturday.to_dict(),
            'sunday': self.sunday.to_dict(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'WeeklySchedule':
        """Create from dictionary."""
        return cls(
            monday=DaySchedule.from_dict(data.get('monday', {})),
            tuesday=DaySchedule.from_dict(data.get('tuesday', {})),
            wednesday=DaySchedule.from_dict(data.get('wednesday', {})),
            thursday=DaySchedule.from_dict(data.get('thursday', {})),
            friday=DaySchedule.from_dict(data.get('friday', {})),
            saturday=DaySchedule.from_dict(data.get('saturday', {'enabled': False})),
            sunday=DaySchedule.from_dict(data.get('sunday', {'enabled': False})),
        )


@dataclass
class Settings:
    """Application settings."""
    idle_threshold_seconds: int = 300  # 5 minutes default
    auto_start: bool = False
    monitoring_enabled: bool = True
    schedule: WeeklySchedule = field(default_factory=WeeklySchedule)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'idle_threshold_seconds': self.idle_threshold_seconds,
            'auto_start': self.auto_start,
            'monitoring_enabled': self.monitoring_enabled,
            'schedule': self.schedule.to_dict(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Settings':
        """Create from dictionary."""
        schedule_data = data.get('schedule', {})
        return cls(
            idle_threshold_seconds=data.get('idle_threshold_seconds', 300),
            auto_start=data.get('auto_start', False),
            monitoring_enabled=data.get('monitoring_enabled', True),
            schedule=WeeklySchedule.from_dict(schedule_data),
        )


class SettingsManager:
    """
    Manages application settings persistence.
    
    Settings are stored in a JSON file in the same directory as the executable
    to maintain portability (per design decision DD-1).
    """
    
    SETTINGS_FILENAME = "momo_settings.json"
    
    def __init__(self, settings_path: Optional[Path] = None):
        """
        Initialize the settings manager.
        
        Args:
            settings_path: Optional path to settings file. If not provided,
                          uses the executable directory.
        """
        if settings_path:
            self._settings_path = settings_path
        else:
            self._settings_path = self._get_default_settings_path()
        
        self._settings: Settings = Settings()
        self._on_settings_changed: Optional[Callable[[Settings], None]] = None
    
    def _get_default_settings_path(self) -> Path:
        """Get the default settings file path (same directory as executable)."""
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            app_dir = Path(sys.executable).parent
        else:
            # Running as script
            app_dir = Path(__file__).parent.parent.parent
        
        return app_dir / self.SETTINGS_FILENAME
    
    @property
    def settings(self) -> Settings:
        """Get the current settings."""
        return self._settings
    
    def load(self) -> Settings:
        """
        Load settings from file.
        
        Returns:
            Loaded settings, or defaults if file doesn't exist.
        """
        try:
            if self._settings_path.exists():
                with open(self._settings_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._settings = Settings.from_dict(data)
            else:
                self._settings = Settings()
        except (json.JSONDecodeError, IOError) as e:
            # If there's an error, use defaults
            print(f"Warning: Could not load settings: {e}")
            self._settings = Settings()
        
        return self._settings
    
    def save(self) -> bool:
        """
        Save current settings to file.
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Ensure directory exists
            self._settings_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self._settings_path, 'w', encoding='utf-8') as f:
                json.dump(self._settings.to_dict(), f, indent=2)
            
            return True
        except IOError as e:
            print(f"Error saving settings: {e}")
            return False
    
    def update_settings(self, **kwargs) -> None:
        """
        Update settings with the provided values.
        
        Args:
            **kwargs: Setting names and values to update.
        """
        for key, value in kwargs.items():
            if hasattr(self._settings, key):
                setattr(self._settings, key, value)
        
        self.save()
        
        if self._on_settings_changed:
            self._on_settings_changed(self._settings)
    
    def set_settings_changed_callback(self, callback: Callable[[Settings], None]) -> None:
        """
        Set callback to be called when settings change.
        
        Args:
            callback: Function to call with updated settings.
        """
        self._on_settings_changed = callback
