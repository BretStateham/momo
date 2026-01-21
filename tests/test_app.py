"""
Unit tests for MoMo app module.
"""

from pathlib import Path
from typing import Optional

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import momo.app as app_module
from momo.settings import Settings, WeeklySchedule


def _build_app(monkeypatch, *,
               settings: Settings,
               save_result: bool = True,
               autostart_enabled: bool = False,
               autostart_set_result: bool = True,
               configuration_result: Optional[Settings] = None,
               within_schedule: bool = True,
               day_enabled: bool = True,
               day_start: str = "08:00",
               day_stop: str = "17:00"):
    errors: list[tuple[str, str]] = []

    class FakeSettingsManager:
        def __init__(self):
            self.settings = settings
            self.save_calls = 0

        def load(self):
            return self.settings

        def save(self):
            self.save_calls += 1
            return save_result

    class FakeIdleDetector:
        def __init__(self, threshold_seconds):
            self.threshold_seconds = threshold_seconds
            self.start_calls = 0
            self.stop_calls = 0

        def set_idle_callback(self, callback):
            self.callback = callback

        def start_monitoring(self):
            self.start_calls += 1

        def stop_monitoring(self):
            self.stop_calls += 1

    class FakeMouseMover:
        def set_movement_callback(self, callback):
            self.movement_callback = callback

        def set_movement_complete_callback(self, callback):
            self.movement_complete_callback = callback

    class FakeScheduleManager:
        def __init__(self, schedule):
            self._schedule = schedule
            self._within_schedule = within_schedule
            self._day_enabled = day_enabled
            self._day_start = day_start
            self._day_stop = day_stop

        @property
        def schedule(self):
            return self._schedule

        @schedule.setter
        def schedule(self, value):
            self._schedule = value

        def is_within_schedule(self, check_time=None):
            return self._within_schedule

        def get_current_day_schedule(self):
            day = self._schedule.get_day(0)
            day.enabled = self._day_enabled
            day.start_time = self._day_start
            day.stop_time = self._day_stop
            return day

        @staticmethod
        def get_day_name(day_index):
            return "Monday"

    class FakeAutoStartManager:
        def __init__(self):
            self.last_set_enabled = None

        def is_enabled(self):
            return autostart_enabled

        def set_enabled(self, enabled):
            self.last_set_enabled = enabled
            return autostart_set_result

    class FakeTrayIcon:
        def __init__(self):
            self.autostart_enabled = None
            self.threshold = None
            self.monitoring_enabled = None
            self.active = None
            self.within_schedule = None
            self.schedule_label = None

        def set_autostart(self, enabled):
            self.autostart_enabled = enabled

        def set_threshold(self, seconds):
            self.threshold = seconds

        def set_monitoring(self, is_monitoring):
            self.monitoring_enabled = is_monitoring

        def set_schedule_status(self, within_schedule, schedule_label):
            self.within_schedule = within_schedule
            self.schedule_label = schedule_label

        def set_active(self, is_active):
            self.active = is_active

        def set_on_start_stop(self, callback):
            self.on_start_stop = callback

        def set_on_configure_threshold(self, callback):
            self.on_configure_threshold = callback

        def set_on_configure_schedule(self, callback):
            self.on_configure_schedule = callback

        def set_on_configure(self, callback):
            self.on_configure = callback

        def set_on_exit(self, callback):
            self.on_exit = callback

        def run(self):
            pass

        def stop(self):
            pass

    def fake_show_error(title, message):
        errors.append((title, message))

    def fake_show_configuration_dialog(current_settings, current_autostart):
        return configuration_result

    monkeypatch.setattr(app_module, "SettingsManager", FakeSettingsManager)
    monkeypatch.setattr(app_module, "IdleDetector", FakeIdleDetector)
    monkeypatch.setattr(app_module, "MouseMover", FakeMouseMover)
    monkeypatch.setattr(app_module, "ScheduleManager", FakeScheduleManager)
    monkeypatch.setattr(app_module, "AutoStartManager", FakeAutoStartManager)
    monkeypatch.setattr(app_module, "TrayIcon", FakeTrayIcon)
    monkeypatch.setattr(app_module, "show_error", fake_show_error)
    monkeypatch.setattr(app_module, "show_configuration_dialog", fake_show_configuration_dialog)

    app = app_module.MoMoApp()
    return app, errors


def test_autostart_sync_updates_settings_and_tray(monkeypatch):
    settings = Settings(auto_start=False)
    app, errors = _build_app(
        monkeypatch,
        settings=settings,
        save_result=True,
        autostart_enabled=True
    )

    assert app._settings.auto_start is True
    assert app._tray_icon.autostart_enabled is True
    assert errors == []


def test_autostart_sync_save_failure_shows_error(monkeypatch):
    settings = Settings(auto_start=False)
    app, errors = _build_app(
        monkeypatch,
        settings=settings,
        save_result=False,
        autostart_enabled=True
    )

    assert app._settings.auto_start is True
    assert app._tray_icon.autostart_enabled is True
    assert len(errors) == 1


def test_monitoring_toggle_save_failure_still_toggles(monkeypatch):
    settings = Settings()
    app, errors = _build_app(
        monkeypatch,
        settings=settings,
        save_result=False
    )

    app._on_monitoring_toggled(True)

    assert app._settings.monitoring_enabled is True
    assert app._idle_detector.start_calls == 1
    assert len(errors) == 1


def test_configure_save_failure_still_updates(monkeypatch):
    settings = Settings()
    new_schedule = WeeklySchedule()
    new_schedule.monday.start_time = "09:00"
    configuration_result = Settings(
        idle_threshold_seconds=600,
        auto_start=True,
        monitoring_enabled=settings.monitoring_enabled,
        schedule=new_schedule
    )

    app, errors = _build_app(
        monkeypatch,
        settings=settings,
        save_result=False,
        autostart_enabled=False,
        autostart_set_result=True,
        configuration_result=configuration_result
    )

    app._on_configure()

    assert app._settings.idle_threshold_seconds == 600
    assert app._idle_detector.threshold_seconds == 600
    assert app._tray_icon.threshold == 600
    assert app._schedule_manager.schedule is new_schedule
    assert app._tray_icon.autostart_enabled is True
    assert len(errors) == 1


def test_configure_autostart_toggle_failure_reverts(monkeypatch):
    settings = Settings(auto_start=False)
    configuration_result = Settings(
        idle_threshold_seconds=settings.idle_threshold_seconds,
        auto_start=True,
        monitoring_enabled=settings.monitoring_enabled,
        schedule=settings.schedule
    )

    app, errors = _build_app(
        monkeypatch,
        settings=settings,
        save_result=True,
        autostart_enabled=False,
        autostart_set_result=False,
        configuration_result=configuration_result
    )

    app._on_configure()

    assert app._settings.auto_start is False
    assert app._tray_icon.autostart_enabled is False
    assert len(errors) == 1


def test_apply_monitoring_state_starts_when_enabled_and_in_schedule(monkeypatch):
    settings = Settings(monitoring_enabled=True)
    app, _ = _build_app(
        monkeypatch,
        settings=settings,
        within_schedule=True
    )

    app._apply_monitoring_state(within_schedule=True)

    assert app._idle_detector.start_calls == 1
    assert app._idle_detector.stop_calls == 0


def test_apply_monitoring_state_stops_when_outside_schedule(monkeypatch):
    settings = Settings(monitoring_enabled=True)
    app, _ = _build_app(
        monkeypatch,
        settings=settings,
        within_schedule=False
    )

    app._apply_monitoring_state(within_schedule=False)

    assert app._idle_detector.stop_calls == 1


def test_apply_monitoring_state_stops_when_disabled(monkeypatch):
    settings = Settings(monitoring_enabled=False)
    app, _ = _build_app(
        monkeypatch,
        settings=settings,
        within_schedule=True
    )

    app._apply_monitoring_state(within_schedule=True)

    assert app._idle_detector.stop_calls == 1


def test_get_schedule_label_enabled_day(monkeypatch):
    fixed_now = app_module.datetime(2026, 1, 19, 10, 0)  # Monday

    class FixedDateTime(app_module.datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now

    monkeypatch.setattr(app_module, "datetime", FixedDateTime)

    settings = Settings()
    app, _ = _build_app(
        monkeypatch,
        settings=settings,
        day_enabled=True,
        day_start="09:00",
        day_stop="17:30"
    )

    assert app._get_schedule_label() == "Schedule: Monday 09:00–17:30"


def test_get_schedule_label_disabled_day(monkeypatch):
    fixed_now = app_module.datetime(2026, 1, 19, 10, 0)  # Monday

    class FixedDateTime(app_module.datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now

    monkeypatch.setattr(app_module, "datetime", FixedDateTime)

    settings = Settings()
    app, _ = _build_app(
        monkeypatch,
        settings=settings,
        day_enabled=False
    )

    assert app._get_schedule_label() == "Schedule: Monday disabled"


def test_schedule_tick_updates_and_reschedules(monkeypatch):
    settings = Settings()
    app, _ = _build_app(monkeypatch, settings=settings)

    calls = {"count": 0}

    def fake_update():
        calls["count"] += 1

    class FakeTimer:
        def __init__(self, interval, callback):
            self.interval = interval
            self.callback = callback
            self.started = False

        def start(self):
            self.started = True

        def cancel(self):
            self.cancelled = True

    monkeypatch.setattr(app, "_update_schedule_state", fake_update)
    monkeypatch.setattr(app_module.threading, "Timer", FakeTimer)

    app._running = True
    app._schedule_tick()

    assert calls["count"] == 1
    assert isinstance(app._schedule_timer, FakeTimer)
    assert app._schedule_timer.started is True


def test_stop_cancels_schedule_timer(monkeypatch):
    settings = Settings()
    app, _ = _build_app(monkeypatch, settings=settings)

    class FakeTimer:
        def __init__(self):
            self.cancelled = False

        def cancel(self):
            self.cancelled = True

    app._schedule_timer = FakeTimer()
    app.stop()

    assert app._schedule_timer.cancelled is True
