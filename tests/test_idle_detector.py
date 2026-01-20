"""
Unit tests for MoMo idle detector module.

Note: Some tests require Windows APIs and may be skipped on other platforms.
"""

import pytest
import sys
import time
import threading

# Add src to path for imports
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from momo.idle_detector import IdleDetector


# Skip all tests if not on Windows
pytestmark = pytest.mark.skipif(
    sys.platform != 'win32',
    reason="Idle detector tests require Windows"
)


class TestIdleDetector:
    """Tests for IdleDetector class."""
    
    def test_default_threshold(self):
        """Test default threshold value."""
        detector = IdleDetector()
        assert detector.threshold_seconds == 300
    
    def test_custom_threshold(self):
        """Test custom threshold value."""
        detector = IdleDetector(threshold_seconds=60)
        assert detector.threshold_seconds == 60
    
    def test_threshold_setter(self):
        """Test setting threshold via property."""
        detector = IdleDetector()
        detector.threshold_seconds = 120
        assert detector.threshold_seconds == 120
    
    def test_threshold_setter_rejects_negative(self):
        """Test that negative threshold is rejected."""
        detector = IdleDetector()
        with pytest.raises(ValueError):
            detector.threshold_seconds = -1
    
    def test_threshold_setter_rejects_zero(self):
        """Test that zero threshold is rejected."""
        detector = IdleDetector()
        with pytest.raises(ValueError):
            detector.threshold_seconds = 0
    
    def test_get_idle_time_returns_number(self):
        """Test that get_idle_time_seconds returns a number."""
        detector = IdleDetector()
        idle_time = detector.get_idle_time_seconds()
        assert isinstance(idle_time, float)
        assert idle_time >= 0
    
    def test_is_idle_with_high_threshold(self):
        """Test is_idle with a very high threshold."""
        detector = IdleDetector(threshold_seconds=999999)
        # With such a high threshold, user should not be idle
        assert detector.is_idle() is False
    
    def test_is_monitoring_initially_false(self):
        """Test that monitoring is initially off."""
        detector = IdleDetector()
        assert detector.is_monitoring is False
    
    def test_start_stop_monitoring(self):
        """Test starting and stopping monitoring."""
        detector = IdleDetector()
        
        detector.start_monitoring()
        assert detector.is_monitoring is True
        
        detector.stop_monitoring()
        assert detector.is_monitoring is False
    
    def test_callback_can_be_set(self):
        """Test that callback can be set."""
        detector = IdleDetector()
        callback_called = []
        
        def callback():
            callback_called.append(True)
        
        detector.set_idle_callback(callback)
        # Callback should be stored (we can't easily test it's called
        # without waiting for idle)
        assert detector._on_idle_callback is not None
    
    def test_multiple_start_calls_safe(self):
        """Test that multiple start calls don't cause issues."""
        detector = IdleDetector()
        
        detector.start_monitoring()
        detector.start_monitoring()  # Should be safe
        
        assert detector.is_monitoring is True
        
        detector.stop_monitoring()
    
    def test_multiple_stop_calls_safe(self):
        """Test that multiple stop calls don't cause issues."""
        detector = IdleDetector()
        
        detector.stop_monitoring()  # Not running yet
        detector.stop_monitoring()  # Should be safe
        
        assert detector.is_monitoring is False
