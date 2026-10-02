from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QWidget,
)


class SectionHeader(QWidget):

    def __init__(self, title: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 6)
        layout.setSpacing(4)

        self._title_label = QLabel(title.upper())
        self._title_label.setObjectName("sectionHeaderTitle")
        layout.addWidget(self._title_label)

        line = QFrame()
        line.setObjectName("sectionHeaderLine")
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Plain)
        line.setFixedHeight(1)
        layout.addWidget(line)

    def set_title(self, text: str) -> None:
        self._title_label.setText(text.upper())