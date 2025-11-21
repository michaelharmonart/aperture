from typing import Self


from PySide6 import QtCore
from PySide6.QtWidgets import QMainWindow
from aperture.core.snapshot import save_and_snapshot
from shiboken6 import Object, wrapInstance
from maya import OpenMayaUI as omui, cmds

class Autosaver(QtCore.QObject):

    _instance = None

    autosave_completed = QtCore.Signal()  # Signal emitted after autosave

    def __init__(self, parent = None) -> None:
        super().__init__(parent)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.autosave)
        self.is_enabled: bool = False
        self.interval_minutes = 1
        
        # Parent to Maya's main window to persist
        maya_main = self.get_maya_main_window()
        if maya_main:
            self.setParent(maya_main)

        self.load_preferences()

    def start(self, interval_minutes: float | None = None):
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

    def set_interval(self, interval_minutes):
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
        cmds.optionVar(intValue=('animSnapshot_autosave_enabled', int(self.is_enabled)))
        cmds.optionVar(intValue=('animSnapshot_autosave_interval', self.interval_minutes))
    
    def load_preferences(self):
        """Load autosave settings from Maya preferences"""
        if cmds.optionVar(exists='animSnapshot_autosave_enabled'):
            self.is_enabled = bool(cmds.optionVar(query='animSnapshot_autosave_enabled'))
        
        if cmds.optionVar(exists='animSnapshot_autosave_interval'):
            self.interval_minutes = cmds.optionVar(query='animSnapshot_autosave_interval')
        
        # Auto-start if it was enabled
        if self.is_enabled:
            self.start()

    @staticmethod    
    def get_maya_main_window() -> Object:
        mw_ptr = omui.MQtUtil.mainWindow()
        return wrapInstance(int(mw_ptr), QMainWindow)

    @classmethod
    def get_instance(cls) -> Self:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance