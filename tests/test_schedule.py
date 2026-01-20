"""
Unit tests for MoMo schedule module.
"""

import pytest
from datetime import datetime, time

# Add src to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import momo.schedule as schedule_module
from momo.settings import WeeklySchedule, DaySchedule


class TestScheduleManager:
    """Tests for ScheduleManager class."""
    
    def test_default_schedule(self):
        """Test that default schedule is created."""
        manager = schedule_module.ScheduleManager()
        assert manager.schedule is not None
        assert isinstance(manager.schedule, WeeklySchedule)
    
    def test_is_within_schedule_weekday_during_hours(self):
        """Test detection when within schedule on weekday."""
        manager = schedule_module.ScheduleManager()
        
        # Monday at 10:00 AM (within default 8am-5pm)
        test_time = datetime(2026, 1, 19, 10, 0)  # Monday
        assert test_time.weekday() == 0  # Verify it's Monday
        
        assert manager.is_within_schedule(test_time) is True
    
    def test_is_within_schedule_weekday_outside_hours(self):
        """Test detection when outside schedule hours on weekday."""
        manager = schedule_module.ScheduleManager()
        
        # Monday at 6:00 PM (outside default 8am-5pm)
        test_time = datetime(2026, 1, 19, 18, 0)  # Monday
        
        assert manager.is_within_schedule(test_time) is False
    
    def test_is_within_schedule_weekend_disabled(self):
        """Test that weekend is not within schedule by default."""
        manager = schedule_module.ScheduleManager()
        
        # Saturday at 10:00 AM (weekend disabled by default)
        test_time = datetime(2026, 1, 24, 10, 0)  # Saturday
        assert test_time.weekday() == 5  # Verify it's Saturday
        
        assert manager.is_within_schedule(test_time) is False
    
    def test_is_within_schedule_at_start_time(self):
        """Test detection exactly at start time."""
        manager = schedule_module.ScheduleManager()
        
        # Monday at exactly 8:00 AM
        test_time = datetime(2026, 1, 19, 8, 0)
        
        assert manager.is_within_schedule(test_time) is True
    
    def test_is_within_schedule_at_end_time(self):
        """Test detection exactly at end time."""
        manager = schedule_module.ScheduleManager()
        
        # Monday at exactly 5:00 PM
        test_time = datetime(2026, 1, 19, 17, 0)
        
        assert manager.is_within_schedule(test_time) is True
    
    def test_is_within_schedule_just_after_end(self):
        """Test detection just after end time."""
        manager = ScheduleManager()
        
        # Monday at 5:01 PM
        test_time = datetime(2026, 1, 19, 17, 1)
        
        assert manager.is_within_schedule(test_time) is False
    
    def test_custom_schedule(self):
        """Test with custom schedule."""
        schedule = WeeklySchedule()
        # Enable Saturday with custom hours
        schedule.saturday = DaySchedule(enabled=True, start_time="10:00", stop_time="14:00")
        
        manager = schedule_module.ScheduleManager(schedule)
        
        # Saturday at 12:00 PM
        test_time = datetime(2026, 1, 24, 12, 0)
        assert manager.is_within_schedule(test_time) is True
        
        # Saturday at 3:00 PM (outside custom hours)
        test_time = datetime(2026, 1, 24, 15, 0)
        assert manager.is_within_schedule(test_time) is False
    
    def test_get_day_name(self):
        """Test day name lookup."""
        assert schedule_module.ScheduleManager.get_day_name(0) == "Monday"
        assert schedule_module.ScheduleManager.get_day_name(4) == "Friday"
        assert schedule_module.ScheduleManager.get_day_name(6) == "Sunday"
    
    def test_schedule_property_setter(self):
        """Test setting schedule via property."""
        manager = schedule_module.ScheduleManager()
        new_schedule = WeeklySchedule()
        new_schedule.monday.start_time = "07:00"
        
        manager.schedule = new_schedule
        
        assert manager.schedule.monday.start_time == "07:00"


class TestScheduleEdgeCases:
    """Edge case tests for schedule management."""
    
    def test_all_days_disabled(self):
        """Test when all days are disabled."""
        schedule = WeeklySchedule()
        for i in range(7):
            day = schedule.get_day(i)
            day.enabled = False
            schedule.set_day(i, day)
        
        manager = schedule_module.ScheduleManager(schedule)
        
        # Any time should return False
        test_time = datetime(2026, 1, 19, 10, 0)
        assert manager.is_within_schedule(test_time) is False
    
    def test_minute_precision(self):
        """Test that minutes are correctly evaluated."""
        schedule = WeeklySchedule()
        schedule.monday = DaySchedule(enabled=True, start_time="08:30", stop_time="17:30")
        
        manager = schedule_module.ScheduleManager(schedule)
        
        # Monday at 8:29 AM - should be outside
        test_time = datetime(2026, 1, 19, 8, 29)
        assert manager.is_within_schedule(test_time) is False
        
        # Monday at 8:30 AM - should be inside
        test_time = datetime(2026, 1, 19, 8, 30)
        assert manager.is_within_schedule(test_time) is True

    def test_is_within_schedule_invalid_time_strings(self):
        """Test that invalid time strings return False without raising."""
        schedule = WeeklySchedule()
        schedule.monday = DaySchedule(enabled=True, start_time="invalid", stop_time="17:00")
        manager = schedule_module.ScheduleManager(schedule)

        test_time = datetime(2026, 1, 19, 10, 0)
        assert manager.is_within_schedule(test_time) is False

    def test_get_next_active_time_currently_active(self, monkeypatch):
        """Test get_next_active_time returns now when currently active."""
        fixed_now = datetime(2026, 1, 19, 10, 0)  # Monday

        class FixedDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                return fixed_now

        monkeypatch.setattr(schedule_module, "datetime", FixedDateTime)

        schedule = WeeklySchedule()
        schedule.monday = DaySchedule(enabled=True, start_time="08:00", stop_time="17:00")
        manager = schedule_module.ScheduleManager(schedule)

        assert manager.get_next_active_time() == fixed_now

    def test_get_next_active_time_future_today(self, monkeypatch):
        """Test get_next_active_time returns today's start time when upcoming."""
        fixed_now = datetime(2026, 1, 19, 7, 0)  # Monday

        class FixedDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                return fixed_now

        monkeypatch.setattr(schedule_module, "datetime", FixedDateTime)

        schedule = WeeklySchedule()
        schedule.monday = DaySchedule(enabled=True, start_time="08:00", stop_time="17:00")
        manager = schedule_module.ScheduleManager(schedule)

        expected = datetime(2026, 1, 19, 8, 0)
        assert manager.get_next_active_time() == expected

    def test_get_next_active_time_overnight_currently_active(self, monkeypatch):
        """Test overnight schedule reports currently active across midnight."""
        fixed_now = datetime(2026, 1, 19, 23, 0)  # Monday

        class FixedDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                return fixed_now

        monkeypatch.setattr(schedule_module, "datetime", FixedDateTime)

        schedule = WeeklySchedule()
        schedule.monday = DaySchedule(enabled=True, start_time="22:00", stop_time="06:00")
        manager = ScheduleManager(schedule)

        assert manager.get_next_active_time() == fixed_now

    def test_get_next_active_time_returns_none_when_disabled(self, monkeypatch):
        """Test get_next_active_time returns None when no days are enabled."""
        fixed_now = datetime(2026, 1, 19, 10, 0)

        class FixedDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                return fixed_now

        monkeypatch.setattr(schedule_module, "datetime", FixedDateTime)

        schedule = WeeklySchedule()
        for i in range(7):
            day = schedule.get_day(i)
            day.enabled = False
            schedule.set_day(i, day)

        manager = ScheduleManager(schedule)

        assert manager.get_next_active_time() is None
