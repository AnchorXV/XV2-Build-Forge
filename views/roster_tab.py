"""
DBXV2 Build Forge — Roster Table Preview Tab.

Shows all roster sheets in a summary table.  Supports:
- Left-click to select (multi-select with checkboxes).
- Double-click to open :class:`SheetDetailDialog`.
- Right-click context menu (Rename / Delete).
- "Export Selected" for multi-sheet export.
- Search bar for filtering.

Migrated from ``create_roster_tab()`` (~lines 490-680) of ``main.py``.
"""

from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtCore import QSortFilterProxyModel, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from controllers.signal_bus import signal_bus
from controllers.undo_commands import AddSheetCommand, DeleteSheetCommand, RenameSheetCommand, DuplicateSheetCommand, ReorderSheetsCommand, EditSheetNoteTagsCommand
from locales.i18n_manager import tr
from models.data_store import AppDataStore
from models.table_models import PresetDetailTableModel, RosterSummaryTableModel
from PySide6.QtGui import QUndoStack, QShortcut, QKeySequence
from PySide6.QtCore import Qt
from views.dialogs.export_dialog import run_export_flow
from views.dialogs.sheet_detail_dialog import SheetDetailDialog
from views.dialogs.sheet_note_tags_dialog import SheetNoteTagsDialog
from views.widgets.searchable_table_view import SearchableTableView
from views.widgets.toolbar_widget import ToolbarWidget

logger = logging.getLogger(__name__)


class RosterTab(QWidget):
    """Roster Table Preview — the second tab."""

    def __init__(self, data_store: AppDataStore, undo_stack: QUndoStack, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._store = data_store
        self._undo_stack = undo_stack
        self._model = RosterSummaryTableModel(data_store)

        self._build_ui()
        self._connect_signals()
        self._setup_shortcuts()

    # ── UI ──────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Toolbar
        self._toolbar = ToolbarWidget(
            add_tooltip=tr("roster.dialog.create_title"),
            search_placeholder=tr("roster.placeholder.search"),
            search_label=tr("roster.label.search"),
            sort_label=tr("roster.button.sort_az"),
            parent=self,
        )
        layout.addWidget(self._toolbar)

        # Table
        self._stv = SearchableTableView(
            self,
            sortable=True,
            selection_mode=QAbstractItemView.ExtendedSelection,
            drag_drop=True,
        )
        self._stv.set_source_model(self._model)
        self._stv.table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        
        # Configure table column sizing
        header = self._stv.table_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setMinimumSectionSize(115)
        
        layout.addWidget(self._stv)

        # Bottom row
        bottom = QHBoxLayout()

        self._hint_label = QLabel(tr("roster.label.hint"))
        self._hint_label.setObjectName("hintLabel")
        bottom.addWidget(self._hint_label, 1)

        self._note_tags_btn = QPushButton(tr("roster.button.edit_note_tags", default="Edit Note & Tags"))
        self._note_tags_btn.setObjectName("noteTagsButton")
        bottom.addWidget(self._note_tags_btn)

        self._export_btn = QPushButton(tr("roster.button.export_selected"))
        self._export_btn.setObjectName("exportButton")
        bottom.addWidget(self._export_btn)

        layout.addLayout(bottom)

    # ── Signals ─────────────────────────────────────────────────────────

    def _connect_signals(self) -> None:
        self._toolbar.add_clicked.connect(self._on_add_sheet)
        self._toolbar.sort_clicked.connect(lambda: self._stv.sort_toggle(0))
        self._toolbar.search_changed.connect(self._stv.set_filter_text)

        self._stv.table_view.doubleClicked.connect(self._on_double_click)
        self._stv.table_view.customContextMenuRequested.connect(self._on_context_menu)
        self._note_tags_btn.clicked.connect(self._on_edit_note_tags_clicked)
        self._export_btn.clicked.connect(self._on_export)
        
        self._model.sheets_reordered.connect(self._on_sheets_reordered)

        signal_bus.data_changed.connect(self._model.refresh)

    # ── Handlers ────────────────────────────────────────────────────────

    def _on_add_sheet(self) -> None:
        name, ok = QInputDialog.getText(
            self,
            tr("roster.dialog.create_title"),
            tr("roster.dialog.create_label"),
        )
        if ok and name.strip():
            name = name.strip()
            if name in self._store.get_all_sheets():
                QMessageBox.warning(self, tr("dialog.common.warning"), tr("roster.message.duplicate_sheet"))
                return
            cmd = AddSheetCommand(self._store, name)
            self._undo_stack.push(cmd)

    def _setup_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+F"), self, self._focus_search)
        QShortcut(QKeySequence("Ctrl+D"), self, self._duplicate_selected)
        QShortcut(QKeySequence("Delete"), self, self._delete_selected)

    def _focus_search(self) -> None:
        self._toolbar.search_input.setFocus()
        self._toolbar.search_input.selectAll()

    def _get_selected_sheet_name(self) -> Optional[str]:
        selection = self._stv.table_view.selectionModel()
        if not selection.hasSelection():
            return None
        indexes = selection.selectedRows()
        if not indexes:
            return None
        source_index = self._stv.proxy_model.mapToSource(indexes[0])
        return self._model.sheet_name_at(source_index.row())

    def _duplicate_selected(self) -> None:
        sheet_name = self._get_selected_sheet_name()
        if sheet_name:
            self._duplicate_sheet(sheet_name)

    def _delete_selected(self) -> None:
        sheet_name = self._get_selected_sheet_name()
        if sheet_name:
            self._delete_sheet(sheet_name)

    def _on_double_click(self, proxy_index) -> None:
        source_index = self._stv.proxy_model.mapToSource(proxy_index)
        row = source_index.row()
        sheet_name = self._model.sheet_name_at(row)
        if sheet_name is None:
            return

        entries = self._store.get_sheet_entries(sheet_name)
        self._store.add_recent_sheet(sheet_name)
        detail_model = PresetDetailTableModel(entries)
        # Pass undo_stack to SheetDetailDialog so it can push DeletePresetEntryCommand
        dlg = SheetDetailDialog(sheet_name, detail_model, self._store, self._undo_stack, self)
        dlg.load_into_editor.connect(lambda r: self._load_entry(sheet_name, r))
        dlg.exec()

    def _load_entry(self, sheet_name: str, row: int) -> None:
        entries = self._store.get_sheet_entries(sheet_name)
        if 0 <= row < len(entries):
            signal_bus.load_entry_to_editor.emit(entries[row], sheet_name)

    def _on_context_menu(self, pos) -> None:
        index = self._stv.table_view.indexAt(pos)
        if not index.isValid():
            return
        source_index = self._stv.proxy_model.mapToSource(index)
        sheet_name = self._model.sheet_name_at(source_index.row())
        if sheet_name is None:
            return

        menu = QMenu(self)
        rename_action = menu.addAction(tr("roster.context_menu.rename"))
        duplicate_action = menu.addAction(tr("roster.context_menu.duplicate", default="Duplicate Sheet"))
        note_tags_action = menu.addAction(tr("roster.context_menu.edit_note_tags", default="Edit Note & Tags"))
        menu.addSeparator()
        delete_action = menu.addAction(tr("roster.context_menu.delete"))

        action = menu.exec(self._stv.table_view.viewport().mapToGlobal(pos))
        if action == rename_action:
            self._rename_sheet(sheet_name)
        elif action == duplicate_action:
            self._duplicate_sheet(sheet_name)
        elif action == note_tags_action:
            self._edit_note_tags(sheet_name)
        elif action == delete_action:
            self._delete_sheet(sheet_name)

    def _rename_sheet(self, old_name: str) -> None:
        new_name, ok = QInputDialog.getText(
            self,
            tr("roster.dialog.rename_title", name=old_name),
            tr("roster.dialog.rename_label"),
            text=old_name,
        )
        if ok and new_name.strip() and new_name.strip() != old_name:
            new_name = new_name.strip()
            if new_name in self._store.get_all_sheets():
                QMessageBox.warning(self, tr("dialog.common.warning"), tr("roster.message.duplicate_sheet"))
                return
            cmd = RenameSheetCommand(self._store, old_name, new_name)
            self._undo_stack.push(cmd)

    def _duplicate_sheet(self, sheet_name: str) -> None:
        new_name, ok = QInputDialog.getText(
            self,
            tr("dialog.duplicate_sheet.title", default="Duplicate Sheet"),
            tr("dialog.duplicate_sheet.prompt", default="New sheet name:"),
            text=f"{sheet_name} (Copy)",
        )
        if ok and new_name.strip():
            new_name = new_name.strip()
            if new_name in self._store.get_all_sheets():
                QMessageBox.warning(self, tr("dialog.common.warning"), tr("roster.message.duplicate_sheet"))
                return
            cmd = DuplicateSheetCommand(self._store, sheet_name, new_name)
            self._undo_stack.push(cmd)

    def _on_edit_note_tags_clicked(self) -> None:
        sheet_name = self._get_selected_sheet_name()
        if sheet_name:
            self._edit_note_tags(sheet_name)
        else:
            QMessageBox.warning(self, tr("dialog.common.warning"), tr("roster.message.select_export", default="Please select a sheet first."))

    def _edit_note_tags(self, sheet_name: str) -> None:
        meta = self._store.get_sheet_meta(sheet_name)
        dialog = SheetNoteTagsDialog(sheet_name, meta, self)
        if dialog.exec():
            new_meta = dialog.get_meta()
            if new_meta != meta:
                cmd = EditSheetNoteTagsCommand(self._store, sheet_name, meta, new_meta)
                self._undo_stack.push(cmd)

    def _delete_sheet(self, name: str) -> None:
        reply = QMessageBox.question(
            self,
            tr("dialog.common.confirm"),
            tr("roster.message.confirm_delete", name=name),
        )
        if reply == QMessageBox.Yes:
            cmd = DeleteSheetCommand(self._store, name)
            self._undo_stack.push(cmd)

    def _on_export(self) -> None:
        selected_rows = self._stv.selected_source_rows()
        if not selected_rows:
            QMessageBox.warning(self, tr("dialog.common.warning"), tr("roster.message.select_export"))
            return

        sheets: dict[str, list] = {}
        for row in selected_rows:
            name = self._model.sheet_name_at(row)
            if name:
                sheets[name] = self._store.get_sheet_entries(name)

        run_export_flow(self, sheets)

    def _on_sheets_reordered(self, old_order: list[str], new_order: list[str]) -> None:
        cmd = ReorderSheetsCommand(self._store, old_order, new_order)
        self._undo_stack.push(cmd)

    def retranslate_ui(self) -> None:
        """Update visible text when the application language changes."""
        self._toolbar.retranslate(
            add_tooltip=tr("roster.dialog.create_title"),
            search_placeholder=tr("roster.placeholder.search"),
            search_label=tr("roster.label.search"),
            sort_label=tr("roster.button.sort_az"),
        )
        self._hint_label.setText(tr("roster.label.hint"))
        self._note_tags_btn.setText(tr("roster.button.edit_note_tags", default="Edit Note & Tags"))
        self._export_btn.setText(tr("roster.button.export_selected"))
