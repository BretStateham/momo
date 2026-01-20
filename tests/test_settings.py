"""
Unit tests for MoMo settings module.
"""

import pytest
import json
import tempfile
from pathlib import Path

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from momo.settings import DaySchedule, WeeklySchedule, Settings, SettingsManager


class TestDaySchedule:
    """Tests for DaySchedule class."""
    
    def test_default_values(self):
        """Test default day schedule values."""
        schedule = DaySchedule()
        assert schedule.enabled is True
        assert schedule.start_time == "08:00"
        assert schedule.stop_time == "17:00"
    
    def test_custom_values(self):
        """Test custom day schedule values."""
        schedule = DaySchedule(enabled=False, start_time="09:00", stop_time="18:00")
        assert schedule.enabled is False
        assert schedule.start_time == "09:00"
        assert schedule.stop_time == "18:00"
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        schedule = DaySchedule(enabled=True, start_time="10:00", stop_time="16:00")
        d = schedule.to_dict()
        assert d == {'enabled': True, 'start_time': '10:00', 'stop_time': '16:00'}
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {'enabled': False, 'start_time': '07:00', 'stop_time': '15:00'}
        schedule = DaySchedule.from_dict(data)
        assert schedule.enabled is False
        assert schedule.start_time == "07:00"
        assert schedule.stop_time == "15:00"


class TestWeeklySchedule:
    """Tests for WeeklySchedule class."""
    
    def test_default_weekdays_enabled(self):
        """Test that weekdays are enabled by default."""
        schedule = WeeklySchedule()
        assert schedule.monday.enabled is True
        assert schedule.tuesday.enabled is True
        assert schedule.wednesday.enabled is True
        assert schedule.thursday.enabled is True
        assert schedule.friday.enabled is True
    
    def test_default_weekends_disabled(self):
        """Test that weekends are disabled by default."""
        schedule = WeeklySchedule()
        assert schedule.saturday.enabled is False
        assert schedule.sunday.enabled is False
    
    def test_get_day_by_index(self):
        """Test getting day schedule by index."""
        schedule = WeeklySchedule()
        # Monday = 0, Sunday = 6
        assert schedule.get_day(0) == schedule.monday
        assert schedule.get_day(4) == schedule.friday
        assert schedule.get_day(6) == schedule.sunday
    
    def test_set_day_by_index(self):
        """Test setting day schedule by index."""
        schedule = WeeklySchedule()
        new_day = DaySchedule(enabled=False, start_time="10:00", stop_time="14:00")
        schedule.set_day(0, new_day)  # Monday
        assert schedule.monday.enabled is False
        assert schedule.monday.start_time == "10:00"
    
    def test_to_dict_and_from_dict(self):
        """Test round-trip conversion."""
        original = WeeklySchedule()
        original.monday.start_time = "09:30"
        
        data = original.to_dict()
        restored = WeeklySchedule.from_dict(data)
        
        assert restored.monday.start_time == "09:30"
        assert restored.saturday.enabled is False


class TestSettings:
    """Tests for Settings class."""
    
    def test_default_values(self):
        """Test default settings values."""
        settings = Settings()
        assert settings.idle_threshold_seconds == 300
        assert settings.auto_start is False
        assert settings.monitoring_enabled is True
        assert isinstance(settings.schedule, WeeklySchedule)
    
    def test_to_dict_and_from_dict(self):
        """Test round-trip conversion."""
        original = Settings(idle_threshold_seconds=600, auto_start=True)
        
        data = original.to_dict()
        restored = Settings.from_dict(data)
        
        assert restored.idle_threshold_seconds == 600
        assert restored.auto_start is True


class TestSettingsManager:
    """Tests for SettingsManager class."""
    
    def test_save_and_load(self):
        """Test saving and loading settings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings_path = Path(tmpdir) / "test_settings.json"
            
            # Create manager and modify settings
            manager = SettingsManager(settings_path)
            manager.settings.idle_threshold_seconds = 120
            manager.settings.auto_start = True
            manager.save()
            
            # Create new manager and load
            manager2 = SettingsManager(settings_path)
            loaded = manager2.load()
            
            assert loaded.idle_threshold_seconds == 120
            assert loaded.auto_start is True
    
    def test_load_missing_file_returns_defaults(self):
        """Test that loading from missing file returns defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings_path = Path(tmpdir) / "nonexistent.json"
            
            manager = SettingsManager(settings_path)
            settings = manager.load()
            
            assert settings.idle_threshold_seconds == 300
            assert settings.auto_start is False
    
    def test_update_settings(self):
        """Test updating settings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings_path = Path(tmpdir) / "test_settings.json"
            
            manager = SettingsManager(settings_path)
            manager.update_settings(idle_threshold_seconds=180)
            
            assert manager.settings.idle_threshold_seconds == 180
            
            # Verify it was saved
            with open(settings_path) as f:
                data = json.load(f)
            assert data['idle_threshold_seconds'] == 180
