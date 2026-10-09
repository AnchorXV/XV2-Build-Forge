from __future__ import annotations

from typing import Optional

from PySide6.QtGui import QUndoStack
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from locales.i18n_manager import tr
from models.data_store import AppDataStore
from views.database_tab import DatabaseTab


CATEGORIES = [
    ("characters", "character"),
    ("super_skills", "super_skill"),
    ("ultimate_skills", "ultimate_skill"),
    ("awoken_skills", "awoken_skill"),
    ("evasive_skills", "evasive_skill"),
    ("super_souls", "super_soul"),
    ("sources", "source"),
]


class DatabasePage(QWidget):

    def __init__(
        self,
        data_store: AppDataStore,
        undo_stack: QUndoStack,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._store = data_store
        self._undo_stack = undo_stack
        self._tabs: dict[str, DatabaseTab] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.setSpacing(10)

        self._category_label = QLabel(tr("database.label.category", default="Category:"))
        self._category_label.setObjectName("pageHeaderLabel")
        header.addWidget(self._category_label)

        self._category_combo = QComboBox()
        self._category_combo.setMinimumWidth(220)
        for key, locale_key in CATEGORIES:
            display = tr(f"tabs.{locale_key}")
            self._category_combo.addItem(display, key)
        header.addWidget(self._category_combo)

        header.addStretch()
        layout.addLayout(header)

        self._stack = QStackedWidget()
        for key, locale_key in CATEGORIES:
            display = tr(f"tabs.{locale_key}")
            tab = DatabaseTab(key, display, data_store, undo_stack, self)
            self._tabs[key] = tab
            self._stack.addWidget(tab)
        layout.addWidget(self._stack, 1)

        self._category_combo.currentIndexChanged.connect(self._stack.setCurrentIndex)
        self._stack.setCurrentIndex(0)

    def retranslate_ui(self) -> None:
        self._category_label.setText(tr("database.label.category", default="Category:"))
        for i, (key, locale_key) in enumerate(CATEGORIES):
            display = tr(f"tabs.{locale_key}")
            self._category_combo.setItemText(i, display)
            if key in self._tabs:
                self._tabs[key].retranslate_ui(display)

    def focus_search(self, text: str) -> None:
        idx = self._category_combo.currentIndex()
        widget = self._stack.widget(idx)
        if hasattr(widget, "_stv"):
            widget._stv.set_filter_text(text)