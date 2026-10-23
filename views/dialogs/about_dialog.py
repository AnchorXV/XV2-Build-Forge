import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QFrame,
)
from app_config import APP_NAME, APP_VERSION
from locales.i18n_manager import tr


class AboutDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{tr('menu.help.about')} - {APP_NAME}")
        self.setFixedSize(460, 320)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # Top part
        top_layout = QHBoxLayout()
        top_layout.setSpacing(16)

        icon_label = QLabel()
        icon = self.style().standardIcon(self.style().StandardPixmap.SP_MessageBoxInformation)
        pixmap = icon.pixmap(64, 64)
        icon_label.setPixmap(pixmap)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        top_layout.addWidget(icon_label)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)

        app_name_label = QLabel(APP_NAME)
        font = app_name_label.font()
        font.setPointSize(18)
        font.setBold(True)
        app_name_label.setFont(font)
        title_layout.addWidget(app_name_label)

        version_label = QLabel(f"Version {APP_VERSION}")
        version_label.setStyleSheet("color: #8b8c93; font-size: 13px;")
        title_layout.addWidget(version_label)

        desc_label = QLabel(
            tr("menu.about.description", default="Roster and Skillset Planner for Dragon Ball Xenoverse 2 Modding.")
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("font-size: 14px; margin-top: 8px;")
        title_layout.addWidget(desc_label)

        top_layout.addLayout(title_layout, 1)
        main_layout.addLayout(top_layout)

        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #232428; border: none;")
        line.setFixedHeight(1)
        main_layout.addWidget(line)

        # Bottom part (Tech + Copyright)
        bottom_layout = QVBoxLayout()
        bottom_layout.setSpacing(4)

        from PySide6 import __version__ as pyside_version
        sys_version = f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        tech_label = QLabel(f"Built with {sys_version} & PySide6 {pyside_version}")
        tech_label.setStyleSheet("color: #8b8c93; font-size: 11px;")
        bottom_layout.addWidget(tech_label)

        copyright_label = QLabel("Copyright © 2026 AnchorXV")
        copyright_label.setStyleSheet("color: #8b8c93; font-size: 11px;")
        bottom_layout.addWidget(copyright_label)

        main_layout.addLayout(bottom_layout)
        main_layout.addStretch()

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept)
        main_layout.addWidget(button_box)