
from typing import Any


from PySide6 import QtWidgets
from aperture.core.autosave import Autosaver
from maya import OpenMayaUI as omui
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from shiboken6 import wrapInstance
from shiboken6.Shiboken import Object

from aperture.core.file import get_current_filepath
from aperture.core.snapshot import Snapshot, get_or_init_repo, get_snapshots, load_snapshot, save_and_snapshot

def get_maya_main_window() -> Object:
    mw_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(mw_ptr), QMainWindow)


class SnapshotCard(QtWidgets.QFrame):
    def __init__(self, snapshot: Snapshot, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #2E3440;
                border-radius: 6px;
            }
        """)
        self.snapshot = snapshot
        self.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)

        layout = QtWidgets.QVBoxLayout(self)

        message = QtWidgets.QLabel(self.snapshot.commit.summary)
        message.setWordWrap(True)
        load_button = QtWidgets.QPushButton("Load Snapshot")
        load_button.clicked.connect(self.call_load_snapshot)

        layout.addWidget(message)
        layout.addWidget(load_button)

    def call_load_snapshot(self) -> None:
        load_snapshot(self.snapshot)

class ApertureWindow(MayaQWidgetDockableMixin, QWidget):
    def __init__(
        self,
        parent,
    ) -> None:
        super().__init__(parent=parent)
        self.autosaver = Autosaver.get_instance()
        self.snapshots: list[Snapshot] = []
        self.setup_ui()
        self.update_ui_from_autosaver()
        self.refresh_snapshots()
        self.autosaver.autosave_completed.connect(self.refresh_snapshots)

    def setup_ui(self):    
        self.setWindowTitle("Aperture")

        # ---------- MAIN LAYOUT (VERTICAL COLUMN) ----------
        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)
        
        # Title
        title_label = QLabel("Aperture")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 12pt;
            font-weight: bold;
            padding: 6px;
        """)
        main_layout.addWidget(title_label)

        # Filepath
        filepath = get_current_filepath()
        if filepath is not None:
            information_label = QLabel(str(filepath))
            information_label.setWordWrap(True)
            information_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            main_layout.addWidget(information_label)

        # Autosave Settings
        autosave_content = QGroupBox("Autosave Settings")
        main_layout.addWidget(autosave_content)
        autosave_layout = QHBoxLayout()
        autosave_content.setLayout(autosave_layout)

        self.autosave_checkbox = QtWidgets.QCheckBox("Enable")
        self.autosave_checkbox.stateChanged.connect(self.toggle_autosave)
        autosave_layout.addWidget(self.autosave_checkbox)
        
        # Interval controls
        interval_content = QWidget()
        interval_layout = QtWidgets.QHBoxLayout()
        interval_layout.addWidget(QtWidgets.QLabel("Interval:"))
        interval_content.setLayout(interval_layout)
        autosave_layout.addWidget(interval_content)
        self.interval_combo = QtWidgets.QComboBox()
        self.interval_combo.addItems(["1 min", "5 min", "10 min", "20min", "30 min"])
        self.interval_combo.setCurrentIndex(2)
        self.interval_combo.currentTextChanged.connect(self.change_interval)
        interval_layout.addWidget(self.interval_combo)

        # Snapshot Settings
        self.snapshot_name_line = QLineEdit()
        self.snapshot_name_line.setPlaceholderText("Enter Snapshot Name (Optional)")
        main_layout.addWidget(self.snapshot_name_line)

        save_button = QPushButton("Save Snapshot")
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #266e1e;
            }
        """)
        main_layout.addWidget(save_button)
        save_button.clicked.connect(self.save_snapshot)

        # Snapshots
        scroll_content = QWidget()
        scroll_area = QScrollArea()
        main_layout.addWidget(scroll_area)

        self.snapshot_scroll_layout = QVBoxLayout()
        scroll_content.setLayout(self.snapshot_scroll_layout)
        self.snapshot_scroll_layout.addStretch(1)
        scroll_area.setWidget(scroll_content)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.snapshot_scroll_layout.addStretch()


    def refresh_snapshots(self):
        for snapshot in reversed(get_snapshots()):
            if snapshot not in self.snapshots:
                card = SnapshotCard(snapshot)
                self.snapshot_scroll_layout.insertWidget(0, card)
                self.snapshots.append(snapshot)

    def save_snapshot(self):
        name = None
        if self.snapshot_name_line.text() != "":
            name = f"Snapshot: {self.snapshot_name_line.text()}"
        
        save_and_snapshot(name)
        self.refresh_snapshots()
        pass

    def update_ui_from_autosaver(self):
        """Update UI to match current autosaver state"""
        self.autosave_checkbox.setChecked(self.autosaver.is_enabled)
        
        # Set combo box to match current interval
        interval_text = f"{self.autosaver.interval_minutes} min"
        index = self.interval_combo.findText(interval_text)
        self.interval_combo.setCurrentIndex(index)

        print(self.autosaver.is_enabled, self.autosaver.interval_minutes)

    def toggle_autosave(self, state):
        if state == 0:
            self.autosaver.stop()
        else:
            self.autosaver.start()

    def change_interval(self, text: str):
        interval = int(text.split()[0])
        self.autosaver.set_interval(interval)
        pass

def launch() -> None:
    aperture_window = ApertureWindow(parent=get_maya_main_window())
    aperture_window.show(dockable=True)
