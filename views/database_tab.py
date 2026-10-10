from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut, QUndoStack
from PySide6.QtWidgets import (
    QAbstractItemView,
    QMenu,
    QMessageBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from controllers.signal_bus import signal_bus
from controllers.undo_commands import (
    AddCacheItemCommand,
    CascadeRenameCharacterCommand,
    DeleteCacheItemCommand,
    EditCacheItemCommand,
    MergeEntryCommand,
)
from locales.i18n_manager import tr
from views.dialogs.merge_dialog import MergeDialog
from models.merge import count_merge_impact
from models.character_usage import find_character_variants
from models.data_store import AppDataStore
from models.table_models import (
    SORT_AZ,
    SORT_DATE,
    SORT_DATE_CREATED,
    SORT_DATE_MODIFIED,
    SORT_ROLE,
    SORT_SOURCE,
    SORT_ZA,
    DatabaseTableModel,
)
from views.dialogs.db_entry_dialog import (
    CharacterDialog,
    SkillDialog,
    SourceDialog,
    SuperSoulDialog,
)
from views.widgets.character_detail_panel import CharacterDetailPanel
from views.widgets.searchable_table_view import SearchableTableView
from views.widgets.toolbar_widget import ToolbarWidget

logger = logging.getLogger(__name__)


SPLIT_MODE_KEYS: set[str] = {"characters"}


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
        self._split_mode = category_key in SPLIT_MODE_KEYS

        if self._split_mode:
            self._model = DatabaseTableModel(
                data_store, category_key, columns=["Name"], entry_type="char"
            )
        else:
            self._model = DatabaseTableModel(data_store, category_key)

        self._detail_panel: Optional[CharacterDetailPanel] = None

        self._build_ui()
        self._connect_signals()
        self._setup_shortcuts()

    def _sort_options(self) -> list[tuple[str, str]]:
        az = tr("database.sort.az")
        za = tr("database.sort.za")
        if self._key == "sources":
            return [
                (az, SORT_AZ),
                (za, SORT_ZA),
                (tr("database.sort.date"), SORT_DATE),
            ]
        if self._key == "characters":
            return [
                (az, SORT_AZ),
                (za, SORT_ZA),
                (tr("database.sort.date_created"), SORT_DATE_CREATED),
                (tr("database.sort.date_modified"), SORT_DATE_MODIFIED),
                (tr("database.sort.source"), SORT_SOURCE),
            ]
        return [
            (az, SORT_AZ),
            (za, SORT_ZA),
            (tr("database.sort.date_created"), SORT_DATE_CREATED),
            (tr("database.sort.date_modified"), SORT_DATE_MODIFIED),
        ]

    def _apply_sort_mode(self, mode: str) -> None:
        self._model.set_sort_mode(mode)
        self._stv.proxy_model.setSortRole(SORT_ROLE)
        self._stv.proxy_model.setSortCaseSensitivity(Qt.CaseInsensitive)

        if mode == SORT_ZA:
            self._stv.proxy_model.sort(0, Qt.DescendingOrder)
        elif mode in (SORT_DATE_CREATED, SORT_DATE_MODIFIED):
            self._stv.proxy_model.sort(0, Qt.DescendingOrder)
        elif mode == SORT_DATE:
            self._stv.proxy_model.sort(2, Qt.AscendingOrder)
        elif mode == SORT_SOURCE:
            self._stv.proxy_model.sort(0, Qt.AscendingOrder)
        else:
            self._stv.proxy_model.sort(0, Qt.AscendingOrder)

    # ── UI ──────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        self._toolbar = ToolbarWidget(
            add_tooltip=tr("database.tooltip.add", type=self._display),
            search_placeholder=tr("database.placeholder.search", type=self._display),
            search_label=tr("database.label.search"),
            sort_options=self._sort_options(),
            fix_cache_label=tr("database.button.fix_cache"),
            parent=self,
        )
        layout.addWidget(self._toolbar)

        if self._split_mode:
            self._build_split_ui(layout)
        else:
            self._build_table_ui(layout)

    def _build_table_ui(self, parent_layout: QVBoxLayout) -> None:
        self._stv = SearchableTableView(
            self,
            sortable=True,
            selection_mode=QAbstractItemView.ExtendedSelection,
        )
        self._stv.set_source_model(self._model)
        self._stv.table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self._stv.set_edit_triggers(QAbstractItemView.NoEditTriggers)
        parent_layout.addWidget(self._stv, 1)

    def _build_split_ui(self, parent_layout: QVBoxLayout) -> None:
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(4)
        splitter.setObjectName("databaseSplitter")

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self._stv = SearchableTableView(
            self,
            sortable=True,
            selection_mode=QAbstractItemView.SingleSelection,
            stretch_columns=False,
        )
        self._stv.set_source_model(self._model)
        self._stv.table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self._stv.set_edit_triggers(QAbstractItemView.NoEditTriggers)

        header = self._stv.table_view.horizontalHeader()
        header.setSectionResizeMode(0, header.ResizeMode.Stretch)

        left_layout.addWidget(self._stv)
        splitter.addWidget(left)

        self._detail_panel = CharacterDetailPanel(self._store)
        self._detail_panel.edit_requested.connect(self._on_edit_panel)
        self._detail_panel.delete_requested.connect(self._on_delete_panel)
        splitter.addWidget(self._detail_panel)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([320, 700])

        parent_layout.addWidget(splitter, 1)

    # ── Signals ─────────────────────────────────────────────────────────

    def _connect_signals(self) -> None:
        self._toolbar.add_clicked.connect(self._on_add)
        self._toolbar.sort_changed.connect(self._apply_sort_mode)
        self._toolbar.search_changed.connect(self._stv.set_filter_text)
        self._toolbar.fix_cache_clicked.connect(self._on_fix_cache)
        self._stv.table_view.customContextMenuRequested.connect(self._on_context_menu)
        self._stv.table_view.doubleClicked.connect(self._on_edit)

        if self._split_mode:
            self._stv.table_view.selectionModel().selectionChanged.connect(
                self._on_selection_changed
            )

        signal_bus.data_changed.connect(self._on_data_changed)

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

    # ── Data refresh ────────────────────────────────────────────────────

    def _on_data_changed(self) -> None:
        self._model.refresh()
        if self._split_mode:
            self._refresh_detail_panel()

    def _on_selection_changed(self, *_args) -> None:
        self._refresh_detail_panel()

    def _refresh_detail_panel(self) -> None:
        if self._detail_panel is None:
            return

        rows = self._stv.selected_source_rows()
        items = self._store.get_cache(self._key)
        if not rows or rows[0] >= len(items):
            self._detail_panel.clear()
            return

        row = rows[0]
        self._detail_panel.set_character(row, items[row])

    def _on_edit_panel(self) -> None:
        if self._detail_panel is None:
            return
        row = self._detail_panel.current_row()
        if row < 0:
            return
        self._on_edit_for_row(row)

    def _on_delete_panel(self) -> None:
        if self._detail_panel is None:
            return
        row = self._detail_panel.current_row()
        if row < 0:
            return
        self._on_delete_for_row(row)

    def _on_edit_for_row(self, row: int) -> None:
        items = self._store.get_cache(self._key)
        if row >= len(items):
            return

        dlg = self._make_dialog(edit_data=items[row])
        if not dlg or not dlg.exec():
            return

        data = dlg.get_data()
        name = data.get("name", "").strip()
        if not name:
            QMessageBox.warning(self, tr("dialog.common.warning"), tr("database.message.empty_name"))
            return

        old_name = items[row].get("name", "")

        if self._key == "characters" and old_name and old_name != name:
            variants = find_character_variants(self._store, old_name)
            if variants:
                reply = QMessageBox.question(
                    self,
                    tr("dialog.common.confirm"),
                    tr(
                        "database.message.cascade_rename",
                        count=len(variants),
                        old=old_name,
                        new=name,
                    ),
                )
                if reply != QMessageBox.Yes:
                    return
                cmd = CascadeRenameCharacterCommand(self._store, old_name, name)
                self._undo_stack.push(cmd)
                return

        cmd = EditCacheItemCommand(self._store, self._key, row, items[row], data)
        self._undo_stack.push(cmd)

    def _on_merge(self) -> None:
        rows = self._stv.selected_source_rows()
        if not rows:
            return
        row = rows[0]
        items = self._store.get_cache(self._key)
        if row >= len(items):
            return

        source_name = items[row].get("name", "")
        if not source_name:
            return

        target_candidates = sorted(
            [
                i.get("name", "")
                for i in items
                if isinstance(i, dict) and i.get("name", "") and i.get("name", "") != source_name
            ],
            key=lambda s: s.lower(),
        )

        if not target_candidates:
            QMessageBox.information(
                self,
                tr("dialog.common.warning"),
                tr("database.message.merge_no_target"),
            )
            return

        impact = count_merge_impact(self._store, self._key, source_name)

        dlg = MergeDialog(
            category_display=self._display,
            source_name=source_name,
            target_candidates=target_candidates,
            impact_count=impact,
            parent=self,
        )
        if not dlg.exec():
            return

        target = dlg.selected_target()
        if not target or target == source_name:
            return

        cmd = MergeEntryCommand(self._store, self._key, source_name, target)
        self._undo_stack.push(cmd)

    def _on_delete_for_row(self, row: int) -> None:
        items = self._store.get_cache(self._key)
        if row >= len(items):
            return
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

    # ── Handlers ────────────────────────────────────────────────────────

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
        self._on_edit_for_row(row)

    def _on_context_menu(self, pos) -> None:
        index = self._stv.table_view.indexAt(pos)
        if not index.isValid():
            return

        source_row = self._stv.proxy_model.mapToSource(index).row()
        if source_row not in self._stv.selected_source_rows():
            sel = self._stv.table_view.selectionModel()
            sel.select(
                index,
                sel.SelectionFlag.Clear | sel.SelectionFlag.Select,
            )
            self._stv.table_view.setCurrentIndex(index)

        menu = QMenu(self)
        edit_action = menu.addAction(tr("database.context_menu.edit"))
        merge_action = menu.addAction(tr("database.context_menu.merge"))
        delete_action = menu.addAction(tr("database.context_menu.delete"))

        action = menu.exec(self._stv.table_view.viewport().mapToGlobal(pos))
        if action == edit_action:
            self._on_edit()
        elif action == merge_action:
            self._on_merge()
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
            self._on_delete_for_row(valid_rows[0])
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
            return CharacterDialog(
                episodes_provider=lambda: self._store.get_cache("sources"),
                parent=self,
                edit_data=edit_data,
            )
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
        current = self._toolbar.current_sort_value()
        self._toolbar.sort_combo.blockSignals(True)
        self._toolbar.sort_combo.clear()
        for display, value in self._sort_options():
            self._toolbar.sort_combo.addItem(display, value)
        idx = self._toolbar.sort_combo.findData(current)
        if idx >= 0:
            self._toolbar.sort_combo.setCurrentIndex(idx)
        self._toolbar.sort_combo.blockSignals(False)
        self._toolbar.retranslate(
            add_tooltip=tr("database.tooltip.add", type=display_title),
            search_placeholder=tr("database.placeholder.search", type=display_title),
            search_label=tr("database.label.search"),
            sort_label=tr("database.label.sort", default="Sort:"),
            fix_cache_label=tr("database.button.fix_cache"),
        )