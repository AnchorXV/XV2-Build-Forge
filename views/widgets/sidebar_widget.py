from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class SidebarWidget(QWidget):

    page_changed = Signal(int)
    about_clicked = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(190)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(4)

        workspace_label = QLabel("WORKSPACE")
        workspace_label.setObjectName("sidebarSection")
        layout.addWidget(workspace_label)

        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)

        self._page_buttons: list[QPushButton] = []

        pages = [
            ("◈", "Editor", 0),
            ("▤", "Roster", 1),
            ("▦", "Database", 2),
        ]
        for icon_text, label_text, index in pages:
            btn = self._make_nav_button(icon_text, label_text)
            btn.clicked.connect(lambda _checked=False, i=index: self.page_changed.emit(i))
            self._button_group.addButton(btn, index)
            self._page_buttons.append(btn)
            layout.addWidget(btn)

        layout.addSpacing(16)

        tools_label = QLabel("TOOLS")
        tools_label.setObjectName("sidebarSection")
        layout.addWidget(tools_label)

        self._about_btn = self._make_nav_button("?", "About")
        self._about_btn.setCheckable(False)
        self._about_btn.clicked.connect(self.about_clicked.emit)
        layout.addWidget(self._about_btn)

        layout.addStretch()

        self._version_label = QLabel("")
        self._version_label.setObjectName("sidebarVersion")
        self._version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._version_label)

        self.set_current_page(0)

    def _make_nav_button(self, icon_text: str, label_text: str) -> QPushButton:
        btn = QPushButton(f"  {icon_text}   {label_text}")
        btn.setObjectName("sidebarButton")
        btn.setCheckable(True)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn.setMinimumHeight(34)
        return btn

    def set_current_page(self, index: int) -> None:
        btn = self._button_group.button(index)
        if btn is not None:
            btn.setChecked(True)

    def set_version_text(self, text: str) -> None:
        self._version_label.setText(text)