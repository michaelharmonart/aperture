from shiboken6.Shiboken import Object


from maya import OpenMayaUI as omui
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QMainWindow, QPushButton, QScrollArea, QVBoxLayout, QWidget
from shiboken6 import wrapInstance
from shiboken6.Shiboken import Object
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin


def get_maya_main_window() -> Object:
    mw_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(mw_ptr), QMainWindow)


class ApertureWindow(MayaQWidgetDockableMixin, QWidget):
    def __init__(
        self,
        parent: QWidget | None = get_maya_main_window(),
    ) -> None:
        super().__init__(parent=parent)
        self.setWindowTitle("Aperture")


        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)
        
        title_label = QLabel("Aperture")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 14pt;
            font-weight: bold;
            padding: 6px;
        """)
        main_layout.addWidget(title_label)



        main_content = QWidget()
        main_layout.addWidget(main_content)
        horizontal_layout = QHBoxLayout()
        main_content.setLayout(horizontal_layout)

        scroll_content = QWidget()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
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

        load_button = QPushButton(f"Load Snapshot")
        static_layout.addWidget(load_button)
        static_layout.addWidget(QLabel("Test"))
        

def launch() -> None:
    aperture_window = ApertureWindow()
    aperture_window.show(dockable=True)
