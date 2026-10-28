from __future__ import annotations

from typing import Optional

from PySide6.QtGui import QKeySequence, QShortcut, QUndoStack
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
from views.widgets.toolbar_widget import ToolbarWidget
from models.table_models import (
    SORT_AZ, SORT_ZA, SORT_DATE_CREATED, SORT_DATE_MODIFIED, SORT_DATE, SORT_SOURCE
)

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
        header.setSpacing(12)

        self._category_label = QLabel(tr("database.label.category", default="Category:"))
        self._category_label.setObjectName("pageHeaderLabel")
        header.addWidget(self._category_label)

        self._category_combo = QComboBox()
        self._category_combo.setMinimumWidth(180)
        self._category_combo.setFixedHeight(36)
        for key, locale_key in CATEGORIES:
            display = tr(f"tabs.{locale_key}")
            self._category_combo.addItem(display, key)
        header.addWidget(self._category_combo)
        
        line = QWidget()
        line.setFixedWidth(1)
        line.setStyleSheet("background-color: #333333; margin-top: 4px; margin-bottom: 4px;")
        header.addWidget(line)

        self._toolbar = ToolbarWidget(
            search_label="",
            sort_options=[("Dummy", "az", "arrow-up-a-z.svg")], # Dummy agar combobox dibuat
            parent=self
        )
        header.addWidget(self._toolbar, 1)
        
        layout.addLayout(header)

        self._stack = QStackedWidget()
        for key, locale_key in CATEGORIES:
            display = tr(f"tabs.{locale_key}")
            tab = DatabaseTab(key, display, data_store, undo_stack, self)
            self._tabs[key] = tab
            self._stack.addWidget(tab)
        
        layout.addWidget(self._stack, 1)

        self._category_combo.currentIndexChanged.connect(self._on_category_changed)
        self._toolbar.add_clicked.connect(self._on_add_clicked)
        self._toolbar.search_changed.connect(self._on_search_changed)
        self._toolbar.sort_changed.connect(self._on_sort_changed)
        
        QShortcut(QKeySequence("Ctrl+F"), self, self._focus_search)

        self._stack.setCurrentIndex(0)
        self._update_toolbar()

    def _current_tab(self) -> DatabaseTab:
        return self._stack.currentWidget()

    def _on_category_changed(self, index: int) -> None:
        self._stack.setCurrentIndex(index)
        self._update_toolbar()

    def _update_toolbar(self) -> None:
        tab = self._current_tab()
        self._toolbar.set_add_tooltip(tr("database.tooltip.add", type=tab._display))
        self._toolbar.set_search_placeholder(tr("database.placeholder.search", type=tab._display))
        self._toolbar.update_sort_options(tab._sort_options())
        tab._apply_sort_mode(self._toolbar.current_sort_value())

    def _on_add_clicked(self) -> None:
        self._current_tab()._on_add()

    def _on_search_changed(self, text: str) -> None:
        self._current_tab()._on_search_changed(text)

    def _on_sort_changed(self, mode: str) -> None:
        self._current_tab()._apply_sort_mode(mode)

    def _focus_search(self) -> None:
        self._toolbar.search_input.setFocus()
        self._toolbar.search_input.selectAll()

    def retranslate_ui(self) -> None:
        self._category_label.setText(tr("database.label.category", default="Category:"))
        for i, (key, locale_key) in enumerate(CATEGORIES):
            display = tr(f"tabs.{locale_key}")
            self._category_combo.setItemText(i, display)
            if key in self._tabs:
                self._tabs[key].retranslate_ui(display)
        self._toolbar.retranslate(
            search_label=tr("database.label.search"),
            sort_label=tr("database.label.sort", default="Sort:"),
        )
        self._update_toolbar()

    def focus_search(self, text: str) -> None:
        idx = self._category_combo.currentIndex()
        widget = self._stack.widget(idx)
        if hasattr(widget, "_stv"):
            widget._stv.set_filter_text(text)