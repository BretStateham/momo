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
               threshold_result: Optional[int] = None,
               schedule_result: Optional[WeeklySchedule] = None):
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

        @property
        def schedule(self):
            return self._schedule

        @schedule.setter
        def schedule(self, value):
            self._schedule = value

        def is_within_schedule(self, check_time=None):
            return True

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

        def set_autostart(self, enabled):
            self.autostart_enabled = enabled

        def set_threshold(self, seconds):
            self.threshold = seconds

        def set_monitoring(self, is_monitoring):
            self.monitoring_enabled = is_monitoring

        def set_active(self, is_active):
            self.active = is_active

        def set_on_start_stop(self, callback):
            self.on_start_stop = callback

        def set_on_configure_threshold(self, callback):
            self.on_configure_threshold = callback

        def set_on_configure_schedule(self, callback):
            self.on_configure_schedule = callback

        def set_on_toggle_autostart(self, callback):
            self.on_toggle_autostart = callback

        def set_on_exit(self, callback):
            self.on_exit = callback

        def run(self):
            pass

        def stop(self):
            pass

    def fake_show_error(title, message):
        errors.append((title, message))

    def fake_show_threshold_dialog(current_value):
        return threshold_result

    def fake_show_schedule_dialog(schedule):
        return schedule_result

    monkeypatch.setattr(app_module, "SettingsManager", FakeSettingsManager)
    monkeypatch.setattr(app_module, "IdleDetector", FakeIdleDetector)
    monkeypatch.setattr(app_module, "MouseMover", FakeMouseMover)
    monkeypatch.setattr(app_module, "ScheduleManager", FakeScheduleManager)
    monkeypatch.setattr(app_module, "AutoStartManager", FakeAutoStartManager)
    monkeypatch.setattr(app_module, "TrayIcon", FakeTrayIcon)
    monkeypatch.setattr(app_module, "show_error", fake_show_error)
    monkeypatch.setattr(app_module, "show_threshold_dialog", fake_show_threshold_dialog)
    monkeypatch.setattr(app_module, "show_schedule_dialog", fake_show_schedule_dialog)

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


def test_configure_threshold_save_failure_still_updates(monkeypatch):
    settings = Settings()
    app, errors = _build_app(
        monkeypatch,
        settings=settings,
        save_result=False,
        threshold_result=600
    )

    app._on_configure_threshold()

    assert app._settings.idle_threshold_seconds == 600
    assert app._idle_detector.threshold_seconds == 600
    assert app._tray_icon.threshold == 600
    assert len(errors) == 1


def test_configure_schedule_save_failure_still_updates(monkeypatch):
    settings = Settings()
    new_schedule = WeeklySchedule()
    new_schedule.monday.start_time = "09:00"

    app, errors = _build_app(
        monkeypatch,
        settings=settings,
        save_result=False,
        schedule_result=new_schedule
    )

    app._on_configure_schedule()

    assert app._schedule_manager.schedule is new_schedule
    assert len(errors) == 1


def test_autostart_toggle_success_save_failure(monkeypatch):
    settings = Settings(auto_start=False)
    app, errors = _build_app(
        monkeypatch,
        settings=settings,
        save_result=False,
        autostart_enabled=False,
        autostart_set_result=True
    )

    app._on_autostart_toggled(True)

    assert app._settings.auto_start is True
    assert app._tray_icon.autostart_enabled is True
    assert len(errors) == 1


def test_autostart_toggle_failure_reverts_tray(monkeypatch):
    settings = Settings(auto_start=False)
    app, errors = _build_app(
        monkeypatch,
        settings=settings,
        save_result=True,
        autostart_enabled=False,
        autostart_set_result=False
    )

    app._on_autostart_toggled(True)

    assert app._tray_icon.autostart_enabled is False
    assert len(errors) == 1
