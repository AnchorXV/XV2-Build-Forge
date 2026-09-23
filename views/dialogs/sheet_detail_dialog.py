"""
DBXV2 Build Forge — Sheet Detail Dialog.

Displays the contents of a roster sheet in a read-only table with a
"Load into Editor" button for each row (PRD §3.4).

Migrated from the inline ``show_detail_table`` logic in ``main.py``.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
    QAbstractItemView,
)

from PySide6.QtGui import QUndoStack
from controllers.undo_commands import DeletePresetEntryCommand
from locales.i18n_manager import tr
from models.data_store import AppDataStore
from models.table_models import PresetDetailTableModel


class SheetDetailDialog(QDialog):
    """Modal dialog showing the preset entries within a single roster sheet.

    Signals:
        load_into_editor: Emitted with the *source-model row index*
            when the user clicks "Load into Editor" for a row.
    """

    load_into_editor = Signal(int)

    def __init__(
        self,
        sheet_name: str,
        model: PresetDetailTableModel,
        data_store: AppDataStore,
        undo_stack: QUndoStack,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._sheet_name = sheet_name
        self._store = data_store
        self._undo_stack = undo_stack
        self._model = model
        
        self.setWindowTitle(tr("roster.dialog.detail_title", name=sheet_name))
        self.setMinimumSize(950, 480)
        self.resize(1100, 520)

        layout = QVBoxLayout(self)

        self._table = QTableView()
        self._table.setModel(model)
        self._table.setSelectionBehavior(QTableView.SelectRows)
        self._table.setSelectionMode(QTableView.ExtendedSelection)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setMinimumSectionSize(110)
        self._table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._table.setEditTriggers(QTableView.NoEditTriggers)
        
        # Enable Drag and Drop
        self._table.setDragEnabled(True)
        self._table.setAcceptDrops(True)
        self._table.setDragDropMode(QAbstractItemView.InternalMove)
        self._table.setDropIndicatorShown(True)
        
        # Add Context Menu
        self._table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_context_menu)
        
        self._model.presets_reordered.connect(self._on_presets_reordered)
        
        layout.addWidget(self._table)

        # Bottom button row
        btn_row = QHBoxLayout()

        self.delete_btn = QPushButton(tr("roster.context_menu.delete"))
        self.delete_btn.setObjectName("deleteButton")
        self.delete_btn.clicked.connect(self._on_delete_clicked)
        btn_row.addWidget(self.delete_btn)

        btn_row.addStretch()

        self.load_btn = QPushButton(tr("dialog.sheet_detail.load_into_editor"))
        self.load_btn.setObjectName("saveButton")
        self.load_btn.clicked.connect(self._on_load_clicked)
        btn_row.addWidget(self.load_btn)

        self.close_btn = QPushButton(tr("dialog.sheet_detail.close"))
        self.close_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.close_btn)

        layout.addLayout(btn_row)

    def _on_load_clicked(self) -> None:
        indexes = self._table.selectionModel().selectedRows()
        if indexes:
            self.load_into_editor.emit(indexes[0].row())
            self.accept()

    def _on_context_menu(self, pos) -> None:
        index = self._table.indexAt(pos)
        if not index.isValid():
            return
            
        from PySide6.QtWidgets import QMenu, QMessageBox
        from views.dialogs.bulk_edit_dialog import BulkEditDialog
        
        selected_rows = self._table.selectionModel().selectedRows()
        
        menu = QMenu(self)
        delete_action = menu.addAction(tr("roster.context_menu.delete"))
        
        bulk_edit_action = None
        if len(selected_rows) > 1:
            # Sesuai PRD: Tampilkan jumlah preset
            bulk_edit_text = tr("dialog.bulk_edit.menu_title", count=len(selected_rows))
            if bulk_edit_text == "dialog.bulk_edit.menu_title": # Fallback if missing
                bulk_edit_text = f"Bulk Edit Selected ({len(selected_rows)} presets)"
            bulk_edit_action = menu.addAction(bulk_edit_text)
            
        action = menu.exec(self._table.viewport().mapToGlobal(pos))
        
        if action == delete_action:
            self._on_delete_clicked()
        elif bulk_edit_action and action == bulk_edit_action:
            entries = self._store.get_sheet_entries(self._sheet_name)
            selected_entries = []
            for idx in selected_rows:
                r = idx.row()
                if 0 <= r < len(entries):
                    selected_entries.append(entries[r])
            
            if selected_entries:
                dlg = BulkEditDialog(self._sheet_name, selected_entries, self._store, self._undo_stack, self)
                dlg.exec()
                # Refresh model after bulk edit
                self._model.update_data(self._store.get_sheet_entries(self._sheet_name))

    def _on_presets_reordered(self, old_order: list[str], new_order: list[str]) -> None:
        from controllers.undo_commands import ReorderPresetsCommand
        cmd = ReorderPresetsCommand(self._store, self._sheet_name, old_order, new_order)
        self._undo_stack.push(cmd)
        
        # Refresh model
        entries = self._store.get_sheet_entries(self._sheet_name)
        self._model.update_data(entries)

    def _on_delete_clicked(self) -> None:
        selected_rows = self._table.selectionModel().selectedRows()
        if not selected_rows:
            return
            
        from PySide6.QtWidgets import QMessageBox
        from PySide6.QtGui import QUndoCommand
        
        entries = self._store.get_sheet_entries(self._sheet_name)
        
        # If single preset selected
        if len(selected_rows) == 1:
            row = selected_rows[0].row()
            if 0 <= row < len(entries):
                entry = entries[row]
                reply = QMessageBox.question(
                    self,
                    tr("dialog.common.confirm"),
                    tr("roster.message.confirm_delete", name=entry.character_name),
                )
                if reply == QMessageBox.Yes:
                    cmd = DeletePresetEntryCommand(self._store, self._sheet_name, entry, row)
                    self._undo_stack.push(cmd)
                    
                    # Refresh model
                    entries = self._store.get_sheet_entries(self._sheet_name)
                    self._model.update_data(entries)
        else:
            # Delete multiple presets (we should group them in a macro command)
            reply = QMessageBox.question(
                self,
                tr("dialog.common.confirm"),
                tr("dialog.bulk_edit.confirm_delete_multiple", count=len(selected_rows)), # Assuming new locale key
            )
            if reply == QMessageBox.Yes:
                self._undo_stack.beginMacro(f"Delete {len(selected_rows)} presets from '{self._sheet_name}'")
                # Sort rows in reverse so deletion indices don't shift
                for idx in sorted(selected_rows, key=lambda x: x.row(), reverse=True):
                    r = idx.row()
                    if 0 <= r < len(entries):
                        cmd = DeletePresetEntryCommand(self._store, self._sheet_name, entries[r], r)
                        self._undo_stack.push(cmd)
                        entries.pop(r) # Manually update local list to keep indices matching for subsequent commands
                self._undo_stack.endMacro()
                
                # Refresh model
                entries = self._store.get_sheet_entries(self._sheet_name)
                self._model.update_data(entries)
