from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtGui import QUndoStack
from PySide6.QtWidgets import (
    QHBoxLayout,
    QStackedWidget,
    QWidget,
)

from app_config import APP_VERSION
from controllers.signal_bus import signal_bus
from models.data_store import AppDataStore
from views.database_page import DatabasePage
from views.editor_tab import EditorTab
from views.roster_tab import RosterTab
from views.widgets.sidebar_widget import SidebarWidget


class PageManager(QWidget):

    PAGE_EDITOR = 0
    PAGE_ROSTER = 1
    PAGE_DATABASE = 2

    about_requested = Signal()

    def __init__(
        self,
        data_store: AppDataStore,
        undo_stack: QUndoStack,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._sidebar = SidebarWidget(self)
        self._sidebar.set_version_text(f"v{APP_VERSION}")
        layout.addWidget(self._sidebar)

        self._stack = QStackedWidget()
        layout.addWidget(self._stack, 1)

        self.editor_tab = EditorTab(data_store, undo_stack, self)
        self._stack.addWidget(self.editor_tab)

        self.roster_tab = RosterTab(data_store, undo_stack, self)
        self._stack.addWidget(self.roster_tab)

        self.database_page = DatabasePage(data_store, undo_stack, self)
        self._stack.addWidget(self.database_page)

        self._sidebar.page_changed.connect(self.set_current_page)
        self._sidebar.about_clicked.connect(self.about_requested.emit)

        signal_bus.load_entry_to_editor.connect(self._on_load_entry)

        self.set_current_page(self.PAGE_EDITOR)

    def set_current_page(self, index: int) -> None:
        if 0 <= index < self._stack.count():
            self._stack.setCurrentIndex(index)
            self._sidebar.set_current_page(index)

    def _on_load_entry(self, entry, sheet_name: str) -> None:
        self.set_current_page(self.PAGE_EDITOR)
        self.editor_tab.load_entry(entry, sheet_name)