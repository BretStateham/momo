"""
Schedule Management Module

Handles schedule evaluation to determine if MoMo should be active
based on the current day and time.
"""

from datetime import datetime, time, timedelta
from typing import Optional
from .settings import WeeklySchedule, DaySchedule


class ScheduleManager:
    """
    Manages schedule evaluation for MoMo.
    
    Determines if the current time falls within the configured
    active schedule for the current day of the week.
    """
    
    def __init__(self, schedule: Optional[WeeklySchedule] = None):
        """
        Initialize the schedule manager.
        
        Args:
            schedule: Weekly schedule configuration. Uses defaults if not provided.
        """
        self._schedule = schedule or WeeklySchedule()
    
    @property
    def schedule(self) -> WeeklySchedule:
        """Get the current schedule."""
        return self._schedule
    
    @schedule.setter
    def schedule(self, value: WeeklySchedule) -> None:
        """Set the schedule."""
        self._schedule = value
    
    def _parse_time(self, time_str: str) -> time:
        """
        Parse a time string in HH:MM format.
        
        Args:
            time_str: Time string in 24-hour format (HH:MM)
            
        Returns:
            time object
            
        Raises:
            ValueError: If time_str is not in valid HH:MM format
        """
        try:
            parts = time_str.split(':')
            if len(parts) != 2:
                raise ValueError(f"Invalid time format: {time_str}")
            hour = int(parts[0])
            minute = int(parts[1])
            if not (0 <= hour <= 23):
                raise ValueError(f"Hour must be 0-23, got {hour}")
            if not (0 <= minute <= 59):
                raise ValueError(f"Minute must be 0-59, got {minute}")
            return time(hour, minute)
        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid time format '{time_str}': expected HH:MM") from e
    
    def _is_time_in_range(self, current: time, start: time, end: time) -> bool:
        """
        Check if current time is within the start-end range.
        
        Args:
            current: Current time to check
            start: Start of the range
            end: End of the range
            
        Returns:
            True if current is within range, False otherwise.
        """
        # Handle normal case (start < end)
        if start <= end:
            return start <= current <= end
        
        # Handle overnight range (e.g., 22:00 to 06:00)
        return current >= start or current <= end
    
    def is_within_schedule(self, check_time: Optional[datetime] = None) -> bool:
        """
        Check if the given time is within the active schedule.
        
        Uses the system time zone for all comparisons.
        
        Args:
            check_time: Time to check. Uses current time if not provided.
            
        Returns:
            True if within schedule, False otherwise.
        """
        if check_time is None:
            check_time = datetime.now()
        
        # Get the day of week (0=Monday, 6=Sunday)
        day_index = check_time.weekday()
        
        # Get the schedule for this day
        day_schedule = self._schedule.get_day(day_index)
        
        # If the day is disabled, return False
        if not day_schedule.enabled:
            return False
        
        # Parse start and end times
        try:
            start_time = self._parse_time(day_schedule.start_time)
            end_time = self._parse_time(day_schedule.stop_time)
        except ValueError:
            return False
        
        # Get current time only
        current_time = check_time.time()
        
        # Check if within range
        return self._is_time_in_range(current_time, start_time, end_time)
    
    def get_current_day_schedule(self) -> DaySchedule:
        """
        Get the schedule for the current day.
        
        Returns:
            DaySchedule for today.
        """
        day_index = datetime.now().weekday()
        return self._schedule.get_day(day_index)
    
    def get_next_active_time(self) -> Optional[datetime]:
        """
        Get the next time the schedule will be active.
        
        Returns:
            datetime of next active period, or None if no schedule is enabled.
        """
        now = datetime.now()
        current_day = now.weekday()
        
        # Check each day starting from today
        for day_offset in range(7):
            day_index = (current_day + day_offset) % 7
            day_schedule = self._schedule.get_day(day_index)
            
            if not day_schedule.enabled:
                continue
            
            start_time = self._parse_time(day_schedule.start_time)
            
            # Calculate the datetime for this day
            target_date = now.date()
            if day_offset > 0:
                target_date = now.date() + timedelta(days=day_offset)
            
            target_datetime = datetime.combine(target_date, start_time)
            
            # If it's today but start time has passed, skip to next occurrence
            if day_offset == 0 and target_datetime <= now:
                # Check if we're still within today's schedule
                end_time = self._parse_time(day_schedule.stop_time)
                if self._is_time_in_range(now.time(), start_time, end_time):
                    return now  # Currently active
                continue
            
            return target_datetime
        
        return None
    
    @staticmethod
    def get_day_name(day_index: int) -> str:
        """
        Get the name of a day by index.
        
        Args:
            day_index: Day index (0=Monday, 6=Sunday)
            
        Returns:
            Day name string.
            
        Raises:
            ValueError: If day_index is not in range 0-6.
        """
        if not 0 <= day_index <= 6:
            raise ValueError(f"day_index must be 0-6, got {day_index}")
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
                'Friday', 'Saturday', 'Sunday']
        return days[day_index]
