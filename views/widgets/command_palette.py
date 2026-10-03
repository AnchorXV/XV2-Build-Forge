from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)


class CommandPalette(QDialog):

    action_selected = Signal(str, dict)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setModal(True)
        self.setFixedWidth(560)

        self._all_commands: list[dict] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._input = QLineEdit()
        self._input.setObjectName("commandPaletteInput")
        self._input.setPlaceholderText("Type a command or sheet name...")
        self._input.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._input)

        divider = QFrame()
        divider.setObjectName("commandPaletteDivider")
        divider.setFrameShape(QFrame.HLine)
        divider.setFixedHeight(1)
        layout.addWidget(divider)

        self._list = QListWidget()
        self._list.setObjectName("commandPaletteList")
        self._list.itemActivated.connect(self._on_item_activated)
        layout.addWidget(self._list)

        self._empty_label = QLabel("No matching commands")
        self._empty_label.setObjectName("commandPaletteEmpty")
        self._empty_label.setAlignment(Qt.AlignCenter)
        self._empty_label.hide()
        layout.addWidget(self._empty_label)

    def register_commands(self, commands: list[dict]) -> None:
        self._all_commands = commands
        self._refresh()

    def open_palette(self) -> None:
        self._input.clear()
        self._refresh()
        self._input.setFocus()

        if self.parent() is not None:
            parent_geo = self.parent().geometry()
            x = parent_geo.x() + (parent_geo.width() - self.width()) // 2
            y = parent_geo.y() + 120
            self.move(x, y)

        self.show()
        self.raise_()
        self.activateWindow()

    def _refresh(self) -> None:
        query = self._input.text().strip().lower()
        self._list.clear()

        matched = 0
        for cmd in self._all_commands:
            label = cmd.get("label", "")
            search_blob = cmd.get("search", label).lower()
            if query and query not in search_blob:
                continue

            item = QListWidgetItem(f"  {label}")
            item.setData(Qt.UserRole, cmd)
            self._list.addItem(item)
            matched += 1

        if matched == 0:
            self._list.hide()
            self._empty_label.show()
        else:
            self._list.show()
            self._empty_label.hide()
            self._list.setCurrentRow(0)

    def _on_text_changed(self, _text: str) -> None:
        self._refresh()

    def _on_item_activated(self, item: QListWidgetItem) -> None:
        cmd = item.data(Qt.UserRole)
        if not cmd:
            return
        self.accept()
        self.action_selected.emit(cmd.get("action", ""), cmd.get("data", {}))

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Escape:
            self.reject()
            return
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            item = self._list.currentItem()
            if item is not None:
                self._on_item_activated(item)
            return
        super().keyPressEvent(event)