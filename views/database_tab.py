from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut, QUndoStack
from PySide6.QtWidgets import (
    QAbstractItemView,
    QMenu,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from controllers.signal_bus import signal_bus
from controllers.undo_commands import (
    AddCacheItemCommand,
    DeleteCacheItemCommand,
    EditCacheItemCommand,
)
from locales.i18n_manager import tr
from models.data_store import AppDataStore
from models.table_models import DatabaseTableModel
from views.dialogs.db_entry_dialog import (
    CharacterDialog,
    SkillDialog,
    SourceDialog,
    SuperSoulDialog,
)
from views.widgets.searchable_table_view import SearchableTableView
from views.widgets.toolbar_widget import ToolbarWidget

logger = logging.getLogger(__name__)


class DatabaseTab(QWidget):

    def __init__(
        self,
        category_key: str,
        display_name: str,
        data_store: AppDataStore,
        undo_stack: QUndoStack,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._key = category_key
        self._display = display_name
        self._store = data_store
        self._undo_stack = undo_stack
        self._model = DatabaseTableModel(data_store, category_key)

        self._build_ui()
        self._connect_signals()
        self._setup_shortcuts()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        self._toolbar = ToolbarWidget(
            add_tooltip=tr("database.tooltip.add", type=self._display),
            search_placeholder=tr("database.placeholder.search", type=self._display),
            search_label=tr("database.label.search"),
            sort_label=tr("database.button.sort_az"),
            fix_cache_label=tr("database.button.fix_cache"),
            parent=self,
        )
        layout.addWidget(self._toolbar)

        self._stv = SearchableTableView(
            self,
            sortable=True,
            selection_mode=QAbstractItemView.ExtendedSelection,
        )
        self._stv.set_source_model(self._model)
        self._stv.table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self._stv.set_edit_triggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self._stv)

    def _connect_signals(self) -> None:
        self._toolbar.add_clicked.connect(self._on_add)
        self._toolbar.sort_clicked.connect(lambda: self._stv.sort_toggle(0))
        self._toolbar.search_changed.connect(self._stv.set_filter_text)
        self._toolbar.fix_cache_clicked.connect(self._on_fix_cache)
        self._stv.table_view.customContextMenuRequested.connect(self._on_context_menu)
        self._stv.table_view.doubleClicked.connect(self._on_edit)

        signal_bus.data_changed.connect(self._model.refresh)

    def _setup_shortcuts(self) -> None:
        QShortcut(
            QKeySequence("Ctrl+F"),
            self,
            self._focus_search,
        )
        QShortcut(
            QKeySequence("Ctrl+A"),
            self._stv.table_view,
            self._stv.table_view.selectAll,
            context=Qt.WidgetWithChildrenShortcut,
        )

    def _focus_search(self) -> None:
        self._toolbar.search_input.setFocus()
        self._toolbar.search_input.selectAll()

    def _on_add(self) -> None:
        dlg = self._make_dialog()
        if dlg and dlg.exec():
            data = dlg.get_data()
            name = data.get("name", "").strip()
            if not name:
                QMessageBox.warning(self, tr("dialog.common.warning"), tr("database.message.empty_name"))
                return
            cmd = AddCacheItemCommand(self._store, self._key, data)
            self._undo_stack.push(cmd)

    def _on_fix_cache(self) -> None:
        migrated = self._store.force_migrate_cache(self._key)
        if migrated:
            signal_bus.data_changed.emit()
            QMessageBox.information(
                self,
                tr("dialog.common.ok"),
                tr("database.message.cache_migrated"),
            )
        else:
            QMessageBox.information(
                self,
                tr("dialog.common.ok"),
                tr("database.message.cache_already_ok"),
            )

    def _on_edit(self, proxy_index=None) -> None:
        if proxy_index is not None and proxy_index.isValid():
            source_index = self._stv.proxy_model.mapToSource(proxy_index)
            row = source_index.row()
        else:
            rows = self._stv.selected_source_rows()
            if not rows:
                return
            row = rows[0]

        items = self._store.get_cache(self._key)
        if row >= len(items):
            return

        dlg = self._make_dialog(edit_data=items[row])
        if dlg and dlg.exec():
            data = dlg.get_data()
            name = data.get("name", "").strip()
            if not name:
                QMessageBox.warning(self, tr("dialog.common.warning"), tr("database.message.empty_name"))
                return
            cmd = EditCacheItemCommand(self._store, self._key, row, items[row], data)
            self._undo_stack.push(cmd)

    def _on_context_menu(self, pos) -> None:
        index = self._stv.table_view.indexAt(pos)
        if not index.isValid():
            return

        menu = QMenu(self)
        edit_action = menu.addAction(tr("database.context_menu.edit"))
        delete_action = menu.addAction(tr("database.context_menu.delete"))

        action = menu.exec(self._stv.table_view.viewport().mapToGlobal(pos))
        if action == edit_action:
            self._on_edit()
        elif action == delete_action:
            self._on_delete()

    def _on_delete(self) -> None:
        rows = self._stv.selected_source_rows()
        if not rows:
            return
        items = self._store.get_cache(self._key)
        valid_rows = sorted([r for r in rows if 0 <= r < len(items)], reverse=True)
        if not valid_rows:
            return

        if len(valid_rows) == 1:
            row = valid_rows[0]
            name = items[row].get("name", "???")
            reply = QMessageBox.question(
                self,
                tr("dialog.common.confirm"),
                tr("database.message.confirm_delete", name=name),
            )
            if reply == QMessageBox.Yes:
                item = items[row]
                cmd = DeleteCacheItemCommand(self._store, self._key, row, item)
                self._undo_stack.push(cmd)
        else:
            reply = QMessageBox.question(
                self,
                tr("dialog.common.confirm"),
                tr("database.message.confirm_delete_multiple", count=len(valid_rows)),
            )
            if reply == QMessageBox.Yes:
                self._undo_stack.beginMacro(
                    tr("undo.macro.delete_items", count=len(valid_rows), category=self._key)
                )
                for row in valid_rows:
                    if row < len(items):
                        item = items[row]
                        cmd = DeleteCacheItemCommand(self._store, self._key, row, item)
                        self._undo_stack.push(cmd)
                self._undo_stack.endMacro()

    def _make_dialog(self, edit_data: Optional[dict] = None):
        if self._key == "characters":
            return CharacterDialog(self, edit_data=edit_data)
        elif self._key == "super_souls":
            return SuperSoulDialog(
                characters_provider=lambda: self._store.get_cache("characters"),
                parent=self,
                edit_data=edit_data,
            )
        elif self._key == "sources":
            return SourceDialog(self, edit_data=edit_data)
        else:
            return SkillDialog(self._key, self._display, self, edit_data=edit_data)

    def retranslate_ui(self, display_title: str) -> None:
        self._display = display_title
        self._toolbar.retranslate(
            add_tooltip=tr("database.tooltip.add", type=display_title),
            search_placeholder=tr("database.placeholder.search", type=display_title),
            search_label=tr("database.label.search"),
            sort_label=tr("database.button.sort_az"),
            fix_cache_label=tr("database.button.fix_cache"),
        )