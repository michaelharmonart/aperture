from typing import Self, cast

from maya import OpenMayaUI as omui
from PySide6 import QtCore
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QMainWindow
from shiboken6 import Object, wrapInstance

from aperture.core.optionvar import BoolOptionVar, IntOptionVar
from aperture.core.snapshot import save_and_snapshot


class Autosaver(QtCore.QObject):
    _instance = None

    autosave_completed = QtCore.Signal()  # Signal emitted after autosave

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.autosave)
        self.is_enabled: bool = False
        self.interval_minutes = 5

        self.enabled_option = BoolOptionVar("aperture.autosave_enabled", False)
        self.interval_minutes_option = IntOptionVar("aperture.autosave_interval", 5)

        # Parent to Maya's main window to persist
        maya_main = self.get_maya_main_window()
        if maya_main is not None:
            self.setParent(maya_main)

        self.load_preferences()

    def start(self, interval_minutes: int | None = None):
        """Start autosave timer with specified interval"""
        if interval_minutes is not None:
            self.interval_minutes = interval_minutes

        # Stop existing timer before starting new one
        self.timer.stop()

        # Start timer with interval in milliseconds
        interval_ms = self.interval_minutes * 60 * 1000
        self.timer.start(int(interval_ms))
        self.is_enabled = True
        print(f"Autosave started: every {self.interval_minutes} minutes")
        self.save_preferences()

    def stop(self):
        self.timer.stop()
        self.is_enabled = False
        self.save_preferences()

    def set_interval(self, interval_minutes: int):
        """Change the autosave interval and restart timer if running"""
        self.interval_minutes = interval_minutes
        self.save_preferences()
        # If timer is running, restart with new interval
        if self.is_enabled and self.interval_minutes != interval_minutes:
            self.start()

    def autosave(self) -> None:
        save_and_snapshot(autosave=True)
        self.autosave_completed.emit()
        pass

    def save_preferences(self):
        """Save autosave settings to Maya preferences"""
        self.enabled_option.value = self.is_enabled
        self.interval_minutes_option.value = self.interval_minutes

    def load_preferences(self):
        """Load autosave settings from Maya preferences"""
        self.is_enabled = self.enabled_option.value
        self.interval_minutes = self.interval_minutes_option.value

        # Auto-start if it was enabled
        if self.is_enabled:
            self.start()

    @staticmethod
    def get_maya_main_window() -> QObject:
        mw_ptr = omui.MQtUtil.mainWindow()
        return cast(QObject, wrapInstance(int(mw_ptr), QMainWindow))

    @classmethod
    def get_instance(cls) -> Self:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
