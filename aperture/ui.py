from maya import OpenMayaUI as omui
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from maya.OpenMaya import MSceneMessage
from PySide6 import QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
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

from aperture.core.autosave import Autosaver
from aperture.core.file import get_current_filepath
from aperture.core.snapshot import (
    Snapshot,
    get_snapshots,
    load_snapshot,
    save_and_snapshot,
)


def get_maya_main_window() -> Object:
    mw_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(mw_ptr), QMainWindow)


class SnapshotCard(QtWidgets.QFrame):
    def __init__(self, snapshot: Snapshot, parent=None) -> None:
        super().__init__(parent)
        self.color_pairs = {"Autosave:": "#23292b", "Snapshot:": "#41786b"}
        self.color_str = "#2E3440"
        for key, color in self.color_pairs.items():
            if snapshot.commit.message.startswith(key):
                self.color_str = color
        self.setStyleSheet(f"""
            QFrame {{
                border-color: {self.color_str};
                border-radius: 6px;
                border-style: solid;
                border-width: 4px;
            }}
        """)
        self.snapshot = snapshot
        self.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        load_button = QtWidgets.QPushButton(self.snapshot.commit.message)
        load_button.clicked.connect(self.call_load_snapshot)
        load_button.setStyleSheet("padding-left: 4px; text-align: left;")
        load_button.setMinimumWidth(50)
        load_button.setStyleSheet("""
            QPushButton {
                background-color: #454B4D;
                padding: 4px;
                text-align: left;
            }
        """)

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
        self._open_callbacks = MSceneMessage.addCallback(
            MSceneMessage.kAfterOpen, lambda *args: self.refresh()
        )
        self.snapshots: list[Snapshot] = []
        self.setup_ui()
        self.update_file_info()
        self.update_ui_from_autosaver()
        self.refresh_snapshots()
        self.autosaver.autosave_completed.connect(self.refresh_snapshots)

    def setup_ui(self):
        self.setWindowTitle("Aperture")

        # ---------- MAIN LAYOUT ----------
        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)

        # Filepath
        self.information_label = QLabel()
        self.information_label.setWordWrap(True)
        self.information_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.information_label)

        # Autosave Settings
        autosave_content = QGroupBox("Autosave Settings")
        main_layout.addWidget(autosave_content)
        autosave_layout = QHBoxLayout()
        autosave_layout.setContentsMargins(4, 4, 4, 4)
        autosave_content.setLayout(autosave_layout)

        self.autosave_checkbox = QtWidgets.QCheckBox("Enable")
        self.autosave_checkbox.stateChanged.connect(self.toggle_autosave)
        autosave_layout.addWidget(self.autosave_checkbox)
        autosave_layout.addStretch(1)

        # Interval controls
        interval_content = QWidget()
        interval_layout = QtWidgets.QHBoxLayout()
        interval_layout.setContentsMargins(0, 0, 0, 0)
        interval_layout.addWidget(QtWidgets.QLabel("Interval:"))
        interval_content.setLayout(interval_layout)
        autosave_layout.addWidget(interval_content)
        self.interval_combo = QtWidgets.QComboBox()
        self.interval_combo.addItems(["1 min", "5 min", "10 min", "20 min", "30 min"])
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
                background-color: #41786b;
            }
        """)
        main_layout.addWidget(save_button)
        save_button.clicked.connect(self.save_snapshot)

        # Snapshots
        scroll_content = QWidget()
        scroll_area = QScrollArea()
        main_layout.addWidget(scroll_area)

        self.snapshot_scroll_layout = QVBoxLayout()
        self.snapshot_scroll_layout.setSpacing(6)
        scroll_content.setLayout(self.snapshot_scroll_layout)
        self.snapshot_scroll_layout.addStretch(1)
        scroll_area.setWidget(scroll_content)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.snapshot_scroll_layout.addStretch()

    def update_file_info(self):
        filepath = get_current_filepath()
        if filepath is None:
            self.information_label.setText("Unsaved File")
        else:
            self.information_label.setText(str(filepath))

    def refresh(self):
        self.refresh_snapshots()
        self.update_file_info()

    def refresh_snapshots(self):
        new = set(get_snapshots())
        old = set(self.snapshots)
        to_add = new - old
        to_remove = old - new

        if to_remove:
            for i in reversed(range(self.snapshot_scroll_layout.count())):
                item = self.snapshot_scroll_layout.itemAt(i)
                widget = item.widget()
                if widget:
                    if isinstance(widget, SnapshotCard):
                        card = widget
                        if card.snapshot in to_remove:
                            widget.setParent(None)
                            self.snapshots.remove(card.snapshot)

        if to_add:
            for snapshot in reversed(get_snapshots()):
                if snapshot in to_add:
                    card = SnapshotCard(snapshot)
                    self.snapshot_scroll_layout.insertWidget(0, card)
                    self.snapshots.append(snapshot)

    def save_snapshot(self):
        name = None
        if self.snapshot_name_line.text() != "":
            name = f"Snapshot: {self.snapshot_name_line.text()}"
        self.snapshot_name_line.setText("")
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
