from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)


class ToolbarWidget(QWidget):

    add_clicked = Signal()
    sort_changed = Signal(str)
    search_changed = Signal(str)
    fix_cache_clicked = Signal()

    def __init__(
        self,
        *,
        add_tooltip: str = "",
        search_placeholder: str = "",
        search_label: str = "Search:",
        sort_options: Optional[list[tuple[str, str]]] = None,
        fix_cache_label: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.add_btn = QPushButton("+")
        self.add_btn.setObjectName("addButton")
        self.add_btn.setToolTip(add_tooltip)
        self.add_btn.setFixedSize(34, 30)
        self.add_btn.clicked.connect(self.add_clicked.emit)
        layout.addWidget(self.add_btn)

        self._sort_label = None
        self.sort_combo = None
        if sort_options:
            self._sort_label = QLabel("Sort:")
            layout.addWidget(self._sort_label)

            self.sort_combo = QComboBox()
            self.sort_combo.setMinimumWidth(150)
            for display, value in sort_options:
                self.sort_combo.addItem(display, value)
            self.sort_combo.currentIndexChanged.connect(self._on_sort_changed)
            layout.addWidget(self.sort_combo)

        self.fix_cache_btn = None
        if fix_cache_label is not None:
            self.fix_cache_btn = QPushButton(fix_cache_label)
            self.fix_cache_btn.setObjectName("fixCacheButton")
            self.fix_cache_btn.clicked.connect(self.fix_cache_clicked.emit)
            layout.addWidget(self.fix_cache_btn)

        layout.addStretch()

        self._search_label = QLabel(search_label)
        layout.addWidget(self._search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(search_placeholder)
        self.search_input.setFixedWidth(240)
        self.search_input.textChanged.connect(self.search_changed.emit)
        layout.addWidget(self.search_input)

    def _on_sort_changed(self, _index: int) -> None:
        if self.sort_combo is None:
            return
        value = self.sort_combo.currentData()
        if value:
            self.sort_changed.emit(str(value))

    def set_sort_value(self, value: str) -> None:
        if self.sort_combo is None:
            return
        idx = self.sort_combo.findData(value)
        if idx >= 0:
            self.sort_combo.blockSignals(True)
            self.sort_combo.setCurrentIndex(idx)
            self.sort_combo.blockSignals(False)

    def current_sort_value(self) -> str:
        if self.sort_combo is None:
            return ""
        data = self.sort_combo.currentData()
        return str(data) if data else ""

    def retranslate(
        self,
        *,
        add_tooltip: str = "",
        search_placeholder: str = "",
        search_label: str = "Search:",
        sort_label: str = "Sort:",
        fix_cache_label: Optional[str] = None,
    ) -> None:
        self.add_btn.setToolTip(add_tooltip)
        if self._sort_label is not None:
            self._sort_label.setText(sort_label)
        if self.fix_cache_btn and fix_cache_label is not None:
            self.fix_cache_btn.setText(fix_cache_label)
        self._search_label.setText(search_label)
        self.search_input.setPlaceholderText(search_placeholder)