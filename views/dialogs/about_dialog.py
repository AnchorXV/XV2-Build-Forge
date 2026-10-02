import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)

from app_config import APP_NAME, APP_VERSION
from locales.i18n_manager import tr


class AboutDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{tr('menu.about.title')} - {APP_NAME}")
        self.setFixedSize(450, 250)

        main_layout = QHBoxLayout(self)

        icon_label = QLabel()
        icon = self.style().standardIcon(self.style().StandardPixmap.SP_MessageBoxInformation)
        pixmap = icon.pixmap(64, 64)
        icon_label.setPixmap(pixmap)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        main_layout.addWidget(icon_label)

        details_layout = QVBoxLayout()

        app_name_label = QLabel(f"<b>{APP_NAME}</b>")
        font = app_name_label.font()
        font.setPointSize(16)
        app_name_label.setFont(font)
        details_layout.addWidget(app_name_label)

        version_label = QLabel(f"Version: {APP_VERSION}")
        details_layout.addWidget(version_label)

        from PySide6 import __version__ as pyside_version
        sys_version = f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        tech_label = QLabel(f"Built with {sys_version} & PySide6 {pyside_version}")
        tech_label.setStyleSheet("color: gray;")
        details_layout.addWidget(tech_label)

        desc_label = QLabel(
            f"<br>{tr('menu.about.description', default='A preset builder and roster manager for DBXV2.')}<br><br>"
            "Clean MVC Architecture with PySide6.<br>"
            "Copyright © 2026."
        )
        desc_label.setWordWrap(True)
        details_layout.addWidget(desc_label)

        details_layout.addStretch()

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept)
        details_layout.addWidget(button_box)

        main_layout.addLayout(details_layout)