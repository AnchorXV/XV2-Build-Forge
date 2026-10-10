from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QCursor, QKeySequence, QShortcut, QUndoStack
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QMenu,
    QPushButton,
    QTableView,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from controllers.undo_commands import (
    AddPresetEntryCommand,
    DeletePresetEntryCommand,
    ReorderPresetsCommand,
)
from locales.i18n_manager import tr
from models.data_store import AppDataStore
from models.preset_clipboard import PresetClipboard
from models.table_models import PresetDetailTableModel
from views.dialogs.bulk_edit_dialog import BulkEditDialog
from views.dialogs.find_replace_dialog import FindReplaceDialog


class SheetDetailDialog(QDialog):

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

        self._table.setDragEnabled(True)
        self._table.setAcceptDrops(True)
        self._table.setDragDropMode(QAbstractItemView.InternalMove)
        self._table.setDropIndicatorShown(True)

        self._table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_context_menu)

        self._model.presets_reordered.connect(self._on_presets_reordered)

        layout.addWidget(self._table)

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

        self._setup_shortcuts()

        if parent is not None:
            self.adjustSize()
            pg = parent.geometry()
            x = pg.x() + (pg.width() - self.width()) // 2
            y = pg.y() + (pg.height() - self.height()) // 3
            self.move(x, y)

    def _setup_shortcuts(self) -> None:
        QShortcut(
            QKeySequence("Ctrl+C"),
            self._table,
            self._on_copy,
            context=Qt.WidgetWithChildrenShortcut,
        )
        QShortcut(
            QKeySequence("Ctrl+X"),
            self._table,
            self._on_cut,
            context=Qt.WidgetWithChildrenShortcut,
        )
        QShortcut(
            QKeySequence("Ctrl+V"),
            self._table,
            self._on_paste,
            context=Qt.WidgetWithChildrenShortcut,
        )
        QShortcut(
            QKeySequence("Ctrl+R"),
            self._table,
            self._on_find_replace,
            context=Qt.WidgetWithChildrenShortcut,
        )

    def _on_load_clicked(self) -> None:
        indexes = self._table.selectionModel().selectedRows()
        if indexes:
            self.load_into_editor.emit(indexes[0].row())
            self.accept()

    def _on_context_menu(self, pos) -> None:
        index = self._table.indexAt(pos)
        if not index.isValid():
            return

        selected_rows = self._table.selectionModel().selectedRows()

        menu = QMenu(self)
        delete_action = menu.addAction(tr("roster.context_menu.delete"))

        bulk_edit_action = None
        if len(selected_rows) > 1:
            bulk_edit_action = menu.addAction(
                tr("dialog.bulk_edit.menu_title", count=len(selected_rows))
            )

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
                self._model.update_data(self._store.get_sheet_entries(self._sheet_name))

    def _on_delete_clicked(self) -> None:
        selected_rows = self._table.selectionModel().selectedRows()
        if not selected_rows:
            return

        entries = self._store.get_sheet_entries(self._sheet_name)
        valid_rows = sorted(
            [idx.row() for idx in selected_rows if 0 <= idx.row() < len(entries)],
            reverse=True,
        )
        if not valid_rows:
            return

        count = len(valid_rows)
        if count == 1:
            row = valid_rows[0]
            cmd = DeletePresetEntryCommand(self._store, self._sheet_name, entries[row], row)
            self._undo_stack.push(cmd)
            message = tr("roster.message.deleted_preset")
        else:
            self._undo_stack.beginMacro(
                tr("undo.macro.delete_presets", count=count, sheet=self._sheet_name)
            )
            for row in valid_rows:
                if 0 <= row < len(entries):
                    cmd = DeletePresetEntryCommand(self._store, self._sheet_name, entries[row], row)
                    self._undo_stack.push(cmd)
            self._undo_stack.endMacro()
            message = tr("roster.message.deleted_presets", count=count)

        self._model.update_data(self._store.get_sheet_entries(self._sheet_name))

        QToolTip.showText(
            QCursor.pos(),
            message,
            self._table,
        )

    def _on_presets_reordered(self, old_order: list[str], new_order: list[str]) -> None:
        cmd = ReorderPresetsCommand(self._store, self._sheet_name, old_order, new_order)
        self._undo_stack.push(cmd)
        self._model.update_data(self._store.get_sheet_entries(self._sheet_name))

    def _on_copy(self) -> None:
        selected = self._get_selected_entries()
        if not selected:
            return
        PresetClipboard.instance().set(selected)

        app = QApplication.instance()
        if app is not None:
            app.clipboard().setText(PresetClipboard.to_tsv(selected))

        QToolTip.showText(
            QCursor.pos(),
            tr("preset.clipboard.copied", count=len(selected)),
            self._table,
        )

    def _on_cut(self) -> None:
        selected_rows = self._table.selectionModel().selectedRows()
        if not selected_rows:
            return
        entries = self._store.get_sheet_entries(self._sheet_name)
        selected = [(idx.row(), entries[idx.row()])
                    for idx in selected_rows
                    if 0 <= idx.row() < len(entries)]
        if not selected:
            return

        PresetClipboard.instance().set([e for _, e in selected])

        self._undo_stack.beginMacro(
            tr("undo.macro.cut_presets", count=len(selected), sheet=self._sheet_name)
        )
        for row, entry in sorted(selected, key=lambda x: x[0], reverse=True):
            cmd = DeletePresetEntryCommand(self._store, self._sheet_name, entry, row)
            self._undo_stack.push(cmd)
        self._undo_stack.endMacro()

        self._model.update_data(self._store.get_sheet_entries(self._sheet_name))

        QToolTip.showText(
            QCursor.pos(),
            tr("preset.clipboard.cut", count=len(selected)),
            self._table,
        )

    def _on_paste(self) -> None:
        clipboard = PresetClipboard.instance()
        if not clipboard.has_content():
            return

        entries = clipboard.get_entries()
        count = len(entries)

        self._undo_stack.beginMacro(
            tr("undo.macro.paste_presets", count=count, sheet=self._sheet_name)
        )
        for e in entries:
            cloned = PresetClipboard.clone_with_new_id(e)
            cmd = AddPresetEntryCommand(self._store, self._sheet_name, cloned)
            self._undo_stack.push(cmd)
        self._undo_stack.endMacro()

        self._model.update_data(self._store.get_sheet_entries(self._sheet_name))

        QToolTip.showText(
            QCursor.pos(),
            tr("preset.clipboard.pasted", count=count, sheet=self._sheet_name),
            self._table,
        )

    def _get_selected_entries(self) -> list:
        entries = self._store.get_sheet_entries(self._sheet_name)
        rows = [idx.row() for idx in self._table.selectionModel().selectedRows()]
        return [entries[r] for r in rows if 0 <= r < len(entries)]

    def _on_find_replace(self) -> None:
        dlg = FindReplaceDialog(
            self._store,
            self._undo_stack,
            current_sheet=self._sheet_name,
            parent=self,
        )
        dlg.exec()
        self._model.update_data(self._store.get_sheet_entries(self._sheet_name))