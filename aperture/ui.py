
from maya import OpenMayaUI as omui
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from shiboken6 import wrapInstance
from shiboken6.Shiboken import Object

from aperture.core.file import get_current_filepath
from aperture.core.snapshot import save_and_snapshot

def get_maya_main_window() -> Object:
    mw_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(mw_ptr), QMainWindow)


class ApertureWindow(MayaQWidgetDockableMixin, QWidget):
    def __init__(
        self,
        parent,
    ) -> None:
        super().__init__(parent=parent)
        self.setWindowTitle("Aperture")
        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)

        title_label = QLabel("Aperture: Animation Snapshots")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 12pt;
            font-weight: bold;
            padding: 6px;
        """)
        main_layout.addWidget(title_label)
        filepath = get_current_filepath()
        if filepath is not None:
            information_label = QLabel(str(filepath))
            information_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            main_layout.addWidget(information_label)


        main_content = QWidget()
        main_layout.addWidget(main_content)
        horizontal_layout = QHBoxLayout()
        main_content.setLayout(horizontal_layout)

        scroll_content = QWidget()

        scroll_area = QScrollArea()
        #scroll_area.setWidgetResizable(True)
        horizontal_layout.addWidget(scroll_area)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_content.setLayout(scroll_layout)


        for i in range(10):
            button = QPushButton(f"Snapshot {i}")
            scroll_layout.addWidget(button)

        scroll_layout.addStretch(1)
        scroll_area.setWidget(scroll_content)

        static_content = QWidget()
        static_layout = QVBoxLayout()
        static_content.setLayout(static_layout)
        horizontal_layout.addWidget(static_content)

        save_button = QPushButton("Save Snapshot")
        static_layout.addWidget(save_button)
        save_button.clicked.connect(save_snapshot)

        load_button = QPushButton("Load Snapshot")
        static_layout.addWidget(load_button)
        static_layout.addWidget(QLabel("Test"))
        
def save_snapshot():
    save_and_snapshot()
    pass

def launch() -> None:
    aperture_window = ApertureWindow(parent=get_maya_main_window())
    aperture_window.show(dockable=True)
