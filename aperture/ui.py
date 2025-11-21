
from typing import Any


from PySide6 import QtWidgets
from maya import OpenMayaUI as omui
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
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

        self.snapshots: list[Snapshot] = []

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

        # Snapshot Settings
        self.snapshot_name_line = QLineEdit()
        self.snapshot_name_line.setPlaceholderText("Enter Snapshot Name (Optional)")
        main_layout.addWidget(self.snapshot_name_line)

        save_button = QPushButton("Save Snapshot")
        main_layout.addWidget(save_button)
        save_button.clicked.connect(self.save_snapshot)

        # Snapshots
        scroll_content = QWidget()
        scroll_area = QScrollArea()
        main_layout.addWidget(scroll_area)

        scroll_content = QWidget()
        self.snapshot_scroll_layout = QVBoxLayout()
        scroll_content.setLayout(self.snapshot_scroll_layout)
        self.snapshot_scroll_layout.addStretch(1)
        scroll_area.setWidget(scroll_content)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.snapshot_scroll_layout.addStretch()

        self.refresh_snapshots()

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

def launch() -> None:
    aperture_window = ApertureWindow(parent=get_maya_main_window())
    aperture_window.show(dockable=True)
