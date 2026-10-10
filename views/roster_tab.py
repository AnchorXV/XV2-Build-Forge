from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor, QKeySequence, QShortcut, QUndoStack
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from app_config import TABLE_COLUMNS
from controllers.signal_bus import signal_bus
from controllers.undo_commands import (
    AddPresetEntryCommand,
    AddSheetCommand,
    DeletePresetEntryCommand,
    DeleteSheetCommand,
    DuplicateSheetCommand,
    EditSheetNoteTagsCommand,
    RenameSheetCommand,
    ReorderPresetsCommand,
    ReorderSheetsCommand,
)
from locales.i18n_manager import tr
from models.data_store import AppDataStore
from models.preset_clipboard import PresetClipboard
from models.table_models import PresetDetailTableModel, RosterSummaryTableModel
from views.dialogs.find_replace_dialog import FindReplaceDialog
from views.dialogs.sheet_detail_dialog import SheetDetailDialog
from views.dialogs.sheet_note_tags_dialog import SheetNoteTagsDialog
from views.widgets.searchable_table_view import SearchableTableView

logger = logging.getLogger(__name__)


class RosterTab(QWidget):

    def __init__(self, data_store: AppDataStore, undo_stack: QUndoStack, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._store = data_store
        self._undo_stack = undo_stack
        self._current_sheet: Optional[str] = None

        self._sheet_model = RosterSummaryTableModel(data_store)
        self._preset_model = PresetDetailTableModel([])

        self._build_ui()
        self._connect_signals()
        self._setup_shortcuts()
        self._setup_column_visibility()

        if self._sheet_model.rowCount() > 0:
            self._select_sheet_row(0)
        else:
            self._load_sheet_into_right_panel(None)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(4)
        splitter.setObjectName("rosterSplitter")

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(16, 16, 8, 16)
        left_layout.setSpacing(8)

        self._sheets_header = QLabel(tr("roster.panel.sheets_header", default="SHEETS"))
        self._sheets_header.setObjectName("panelHeader")
        left_layout.addWidget(self._sheets_header)

        self._sheet_view = SearchableTableView(
            self,
            sortable=False,
            selection_mode=QAbstractItemView.ExtendedSelection,
            drag_drop=True,
            stretch_columns=False,
        )
        self._sheet_view.set_source_model(self._sheet_model)
        self._sheet_view.table_view.setObjectName("sheetList")
        self._sheet_view.table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self._sheet_view.table_view.verticalHeader().setVisible(False)
        self._sheet_view.table_view.setShowGrid(False)
        self._sheet_view.set_edit_triggers(QAbstractItemView.NoEditTriggers)

        sheet_header = self._sheet_view.table_view.horizontalHeader()
        sheet_header.setMinimumSectionSize(40)
        sheet_header.setSectionResizeMode(0, QHeaderView.Stretch)
        sheet_header.setSectionResizeMode(1, QHeaderView.Fixed)
        sheet_header.resizeSection(1, 64)

        left_layout.addWidget(self._sheet_view, 1)

        left_btn_row = QHBoxLayout()
        left_btn_row.setSpacing(6)

        self._new_sheet_btn = QPushButton(tr("roster.button.new_sheet", default="+ New"))
        self._new_sheet_btn.setObjectName("secondaryButton")
        self._new_sheet_btn.clicked.connect(self._on_add_sheet)
        left_btn_row.addWidget(self._new_sheet_btn)

        self._note_btn = QPushButton(tr("roster.button.edit_note_tags"))
        self._note_btn.setObjectName("secondaryButton")
        self._note_btn.clicked.connect(self._on_edit_note_tags_clicked)
        left_btn_row.addWidget(self._note_btn)

        self._delete_sheet_btn = QPushButton(tr("roster.context_menu.delete"))
        self._delete_sheet_btn.setObjectName("dangerButton")
        self._delete_sheet_btn.clicked.connect(self._on_delete_sheet_clicked)
        left_btn_row.addWidget(self._delete_sheet_btn)

        left_layout.addLayout(left_btn_row)
        splitter.addWidget(left)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(8, 16, 16, 16)
        right_layout.setSpacing(8)

        self._preset_header = QLabel(tr("roster.panel.select_sheet", default="Select a sheet"))
        self._preset_header.setObjectName("panelHeader")
        right_layout.addWidget(self._preset_header)

        self._right_stack = QStackedWidget()

        empty = QWidget()
        empty_layout = QVBoxLayout(empty)
        empty_layout.addStretch()
        empty_label = QLabel(tr("roster.panel.empty_state", default="Select a sheet from the left panel"))
        empty_label.setObjectName("emptyStateLabel")
        empty_label.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(empty_label)
        empty_layout.addStretch()
        self._right_stack.addWidget(empty)

        self._preset_view = SearchableTableView(
            sortable=True,
            selection_mode=QAbstractItemView.ExtendedSelection,
            drag_drop=True,
            stretch_columns=False,
        )
        self._preset_view.set_source_model(self._preset_model)
        self._preset_view.table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self._preset_view.table_view.verticalHeader().setVisible(False)
        self._preset_view.set_edit_triggers(QAbstractItemView.NoEditTriggers)

        preset_header = self._preset_view.table_view.horizontalHeader()
        preset_header.setMinimumSectionSize(60)
        preset_header.setSectionResizeMode(QHeaderView.Interactive)
        for i in range(1, len(TABLE_COLUMNS)):
            preset_header.resizeSection(i, 105)
        preset_header.setSectionResizeMode(0, QHeaderView.Interactive)
        preset_header.resizeSection(0, 170)

        self._right_stack.addWidget(self._preset_view)

        right_layout.addWidget(self._right_stack, 1)

        right_btn_row = QHBoxLayout()
        right_btn_row.setSpacing(6)
        right_btn_row.addStretch()

        self._load_btn = QPushButton(tr("dialog.sheet_detail.load_into_editor"))
        self._load_btn.setObjectName("secondaryButton")
        self._load_btn.clicked.connect(self._on_load_clicked)
        right_btn_row.addWidget(self._load_btn)

        self._open_detail_btn = QPushButton(tr("roster.button.open_detail", default="Open Detail Dialog"))
        self._open_detail_btn.setObjectName("secondaryButton")
        self._open_detail_btn.clicked.connect(self._on_open_detail_clicked)
        right_btn_row.addWidget(self._open_detail_btn)

        self._delete_preset_btn = QPushButton(tr("roster.context_menu.delete_preset"))
        self._delete_preset_btn.setObjectName("dangerButton")
        self._delete_preset_btn.clicked.connect(self._on_delete_preset_clicked)
        right_btn_row.addWidget(self._delete_preset_btn)

        right_layout.addLayout(right_btn_row)
        splitter.addWidget(right)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([280, 800])

        root.addWidget(splitter)

    def _connect_signals(self) -> None:
        self._sheet_view.table_view.selectionModel().selectionChanged.connect(self._on_sheet_selection_changed)
        self._sheet_view.table_view.customContextMenuRequested.connect(self._on_sheet_context_menu)
        self._sheet_view.table_view.doubleClicked.connect(self._on_sheet_double_clicked)
        self._sheet_model.sheets_reordered.connect(self._on_sheets_reordered)

        self._preset_view.table_view.doubleClicked.connect(self._on_preset_double_clicked)
        self._preset_view.table_view.customContextMenuRequested.connect(self._on_preset_context_menu)
        self._preset_model.presets_reordered.connect(self._on_presets_reordered)

        signal_bus.data_changed.connect(self._on_data_changed)

    def _setup_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+N"), self, self._on_add_sheet)
        QShortcut(
            QKeySequence("Delete"),
            self._sheet_view.table_view,
            self._on_delete_sheet_clicked,
            context=Qt.WidgetWithChildrenShortcut,
        )
        QShortcut(
            QKeySequence("Delete"),
            self._preset_view.table_view,
            self._on_delete_preset_clicked,
            context=Qt.WidgetWithChildrenShortcut,
        )
        QShortcut(
            QKeySequence("Ctrl+C"),
            self._preset_view.table_view,
            self._on_preset_copy,
            context=Qt.WidgetWithChildrenShortcut,
        )
        QShortcut(
            QKeySequence("Ctrl+X"),
            self._preset_view.table_view,
            self._on_preset_cut,
            context=Qt.WidgetWithChildrenShortcut,
        )
        QShortcut(
            QKeySequence("Ctrl+V"),
            self._preset_view.table_view,
            self._on_preset_paste,
            context=Qt.WidgetWithChildrenShortcut,
        )
        QShortcut(
            QKeySequence("Ctrl+R"),
            self,
            self._on_find_replace,
            context=Qt.WidgetWithChildrenShortcut,
        )
        QShortcut(
            QKeySequence("Ctrl+A"),
            self._sheet_view.table_view,
            self._sheet_view.table_view.selectAll,
            context=Qt.WidgetWithChildrenShortcut,
        )
        QShortcut(
            QKeySequence("Ctrl+A"),
            self._preset_view.table_view,
            self._preset_view.table_view.selectAll,
            context=Qt.WidgetWithChildrenShortcut,
        )

    def _setup_column_visibility(self) -> None:
        header = self._preset_view.table_view.horizontalHeader()
        header.setContextMenuPolicy(Qt.CustomContextMenu)
        header.customContextMenuRequested.connect(self._on_header_context_menu)
        self._apply_column_visibility()

    def _on_header_context_menu(self, pos) -> None:
        header = self._preset_view.table_view.horizontalHeader()
        hidden = set(self._get_hidden_columns())

        menu = QMenu(self)
        actions: dict = {}

        for col_name in TABLE_COLUMNS:
            is_locked = (col_name == "Character Name")
            action = menu.addAction(col_name)
            action.setCheckable(True)
            action.setChecked(is_locked or col_name not in hidden)
            if is_locked:
                action.setEnabled(False)
            actions[action] = col_name

        menu.addSeparator()
        reset_action = menu.addAction(tr("roster.column_menu.reset"))

        chosen = menu.exec(header.mapToGlobal(pos))
        if chosen is None:
            return
        if chosen == reset_action:
            self._set_hidden_columns([])
            return
        if chosen in actions:
            self._toggle_column(actions[chosen])

    def _toggle_column(self, col_name: str) -> None:
        if col_name == "Character Name":
            return
        hidden = self._get_hidden_columns()
        if col_name in hidden:
            hidden.remove(col_name)
        else:
            visible_count = len(TABLE_COLUMNS) - len(hidden)
            if visible_count <= 1:
                QMessageBox.information(
                    self,
                    tr("dialog.common.warning"),
                    tr("roster.column_menu.min_columns"),
                )
                return
            hidden.append(col_name)
        self._set_hidden_columns(hidden)

    def _get_hidden_columns(self) -> list[str]:
        raw = self._store.settings.get("roster_hidden_columns", [])
        if not isinstance(raw, list):
            return []
        return [str(x) for x in raw if isinstance(x, str) and x in TABLE_COLUMNS]

    def _set_hidden_columns(self, hidden: list[str]) -> None:
        self._store.settings["roster_hidden_columns"] = list(hidden)
        self._store.save()
        self._apply_column_visibility()

    def _apply_column_visibility(self) -> None:
        hidden = set(self._get_hidden_columns())
        table = self._preset_view.table_view
        for i, col_name in enumerate(TABLE_COLUMNS):
            table.setColumnHidden(i, col_name in hidden)

    # ── Navigation ─────────────────────────────────────────────────────

    def _select_sheet_row(self, row: int) -> None:
        proxy_index = self._sheet_view.proxy_model.mapFromSource(
            self._sheet_model.index(row, 0)
        )
        if not proxy_index.isValid():
            return

        sel = self._sheet_view.table_view.selectionModel()
        sel.select(
            proxy_index,
            sel.SelectionFlag.Select | sel.SelectionFlag.Clear,
        )
        self._sheet_view.table_view.setCurrentIndex(proxy_index)

    def select_sheet_by_name(self, sheet_name: str) -> bool:
        for i in range(self._sheet_model.rowCount()):
            if self._sheet_model.sheet_name_at(i) == sheet_name:
                self._select_sheet_row(i)
                return True
        return False

    def _get_selected_sheet_name(self) -> Optional[str]:
        sel = self._sheet_view.table_view.selectionModel()
        if not sel.hasSelection():
            return None
        indexes = sel.selectedRows()
        if not indexes:
            return None
        return self._sheet_model.sheet_name_at(indexes[0].row())

    def _get_selected_sheet_names(self) -> list[str]:
        sel = self._sheet_view.table_view.selectionModel()
        if not sel.hasSelection():
            return []
        names: list[str] = []
        for idx in sel.selectedRows():
            name = self._sheet_model.sheet_name_at(idx.row())
            if name:
                names.append(name)
        return names

    def _get_selected_preset_entries(self) -> list:
        if not self._current_sheet:
            return []
        rows = self._preset_view.selected_source_rows()
        if not rows:
            return []
        entries = self._store.get_sheet_entries(self._current_sheet)
        return [entries[r] for r in rows if 0 <= r < len(entries)]

    # ── Sheet events ───────────────────────────────────────────────────

    def _on_sheet_selection_changed(self, *_args) -> None:
        name = self._get_selected_sheet_name()
        self._load_sheet_into_right_panel(name)

    def _load_sheet_into_right_panel(self, sheet_name: Optional[str]) -> None:
        self._current_sheet = sheet_name
        if sheet_name is None:
            self._preset_header.setText(tr("roster.panel.select_sheet", default="Select a sheet"))
            self._right_stack.setCurrentIndex(0)
            self._set_right_buttons_enabled(False)
            return

        entries = self._store.get_sheet_entries(sheet_name)
        self._preset_model.update_data(entries)
        count = len(entries)
        label = f"{sheet_name}  ·  {count} preset"
        if count != 1:
            label += "s"
        self._preset_header.setText(label)
        self._right_stack.setCurrentIndex(1)
        self._set_right_buttons_enabled(True)

    def _set_right_buttons_enabled(self, enabled: bool) -> None:
        self._load_btn.setEnabled(enabled)
        self._open_detail_btn.setEnabled(enabled)
        self._delete_preset_btn.setEnabled(enabled)

    # ── Sheet operations ───────────────────────────────────────────────

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

    def _on_edit_note_tags_clicked(self) -> None:
        name = self._get_selected_sheet_name()
        if not name:
            QMessageBox.warning(self, tr("dialog.common.warning"), tr("roster.message.select_export"))
            return

        meta = self._store.get_sheet_meta(name)
        dialog = SheetNoteTagsDialog(name, meta, self)
        if dialog.exec():
            new_meta = dialog.get_meta()
            if new_meta != meta:
                cmd = EditSheetNoteTagsCommand(self._store, name, meta, new_meta)
                self._undo_stack.push(cmd)

    def _on_delete_sheet_clicked(self) -> None:
        names = self._get_selected_sheet_names()
        if not names:
            return

        if len(names) == 1:
            reply = QMessageBox.question(
                self,
                tr("dialog.common.confirm"),
                tr("roster.message.confirm_delete", name=names[0]),
            )
            if reply == QMessageBox.Yes:
                cmd = DeleteSheetCommand(self._store, names[0])
                self._undo_stack.push(cmd)
        else:
            reply = QMessageBox.question(
                self,
                tr("dialog.common.confirm"),
                tr("roster.message.confirm_delete_multiple", count=len(names)),
            )
            if reply == QMessageBox.Yes:
                self._undo_stack.beginMacro(
                    tr("undo.macro.delete_sheets", count=len(names))
                )
                for name in names:
                    cmd = DeleteSheetCommand(self._store, name)
                    self._undo_stack.push(cmd)
                self._undo_stack.endMacro()

    def _on_sheet_double_clicked(self, proxy_index) -> None:
        self._on_open_detail_clicked()

    def _on_sheet_context_menu(self, pos) -> None:
        index = self._sheet_view.table_view.indexAt(pos)
        if not index.isValid():
            return
        source_index = self._sheet_view.proxy_model.mapToSource(index)
        name = self._sheet_model.sheet_name_at(source_index.row())
        if name is None:
            return

        menu = QMenu(self)
        rename_action = menu.addAction(tr("roster.context_menu.rename"))
        duplicate_action = menu.addAction(tr("roster.context_menu.duplicate", default="Duplicate Sheet"))
        note_tags_action = menu.addAction(tr("roster.context_menu.edit_note_tags", default="Edit Note & Tags"))
        menu.addSeparator()
        delete_action = menu.addAction(tr("roster.context_menu.delete"))

        action = menu.exec(self._sheet_view.table_view.viewport().mapToGlobal(pos))
        if action == rename_action:
            self._rename_sheet(name)
        elif action == duplicate_action:
            self._duplicate_sheet(name)
        elif action == note_tags_action:
            self._on_edit_note_tags_clicked()
        elif action == delete_action:
            self._on_delete_sheet_clicked()

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

    def _on_sheets_reordered(self, old_order: list[str], new_order: list[str]) -> None:
        cmd = ReorderSheetsCommand(self._store, old_order, new_order)
        self._undo_stack.push(cmd)

    # ── Preset operations ──────────────────────────────────────────────

    def _on_load_clicked(self) -> None:
        if not self._current_sheet:
            return
        rows = self._preset_view.selected_source_rows()
        if not rows:
            return
        self._load_entry(self._current_sheet, rows[0])

    def _on_open_detail_clicked(self) -> None:
        name = self._get_selected_sheet_name()
        if not name:
            return
        entries = self._store.get_sheet_entries(name)
        self._store.add_recent_sheet(name)
        detail_model = PresetDetailTableModel(entries)
        dlg = SheetDetailDialog(name, detail_model, self._store, self._undo_stack, self)
        dlg.load_into_editor.connect(lambda r: self._load_entry(name, r))
        dlg.exec()
        self._load_sheet_into_right_panel(name)

    def _on_delete_preset_clicked(self) -> None:
        if not self._current_sheet:
            return
        rows = self._preset_view.selected_source_rows()
        if not rows:
            return

        entries = self._store.get_sheet_entries(self._current_sheet)
        valid_rows = sorted([r for r in rows if 0 <= r < len(entries)], reverse=True)
        if not valid_rows:
            return

        count = len(valid_rows)
        if count == 1:
            row = valid_rows[0]
            cmd = DeletePresetEntryCommand(self._store, self._current_sheet, entries[row], row)
            self._undo_stack.push(cmd)
            message = tr("roster.message.deleted_preset")
        else:
            self._undo_stack.beginMacro(
                tr("undo.macro.delete_presets", count=count, sheet=self._current_sheet)
            )
            for row in valid_rows:
                if 0 <= row < len(entries):
                    cmd = DeletePresetEntryCommand(self._store, self._current_sheet, entries[row], row)
                    self._undo_stack.push(cmd)
            self._undo_stack.endMacro()
            message = tr("roster.message.deleted_presets", count=count)

        QToolTip.showText(
            QCursor.pos(),
            message,
            self._preset_view.table_view,
        )

    def _on_preset_double_clicked(self, proxy_index) -> None:
        if not self._current_sheet:
            return
        source_index = self._preset_view.proxy_model.mapToSource(proxy_index)
        self._load_entry(self._current_sheet, source_index.row())

    def _on_preset_context_menu(self, pos) -> None:
        index = self._preset_view.table_view.indexAt(pos)
        if not index.isValid():
            return
        menu = QMenu(self)
        load_action = menu.addAction(tr("dialog.sheet_detail.load_into_editor"))
        delete_action = menu.addAction(tr("roster.context_menu.delete_preset"))
        action = menu.exec(self._preset_view.table_view.viewport().mapToGlobal(pos))
        if action == load_action:
            self._on_load_clicked()
        elif action == delete_action:
            self._on_delete_preset_clicked()

    def _on_presets_reordered(self, old_order: list[str], new_order: list[str]) -> None:
        if not self._current_sheet:
            return
        cmd = ReorderPresetsCommand(self._store, self._current_sheet, old_order, new_order)
        self._undo_stack.push(cmd)

    def _load_entry(self, sheet_name: str, row: int) -> None:
        entries = self._store.get_sheet_entries(sheet_name)
        if 0 <= row < len(entries):
            signal_bus.load_entry_to_editor.emit(entries[row], sheet_name)

    def _on_data_changed(self) -> None:
        sheet_name = self._current_sheet

        sel_model = self._sheet_view.table_view.selectionModel()
        if sel_model is not None:
            sel_model.blockSignals(True)

        try:
            self._sheet_model.refresh()

            if sheet_name and sheet_name in self._store.rosters:
                for i in range(self._sheet_model.rowCount()):
                    if self._sheet_model.sheet_name_at(i) == sheet_name:
                        self._select_sheet_row(i)
                        break
                self._current_sheet = sheet_name
                self._load_sheet_into_right_panel(sheet_name)
            else:
                self._current_sheet = None
                self._load_sheet_into_right_panel(None)
        finally:
            if sel_model is not None:
                sel_model.blockSignals(False)

    # ── Clipboard ──────────────────────────────────────────────────────

    def _on_preset_copy(self) -> None:
        selected = self._get_selected_preset_entries()
        if not selected:
            return
        PresetClipboard.instance().set(selected)

        app = QApplication.instance()
        if app is not None:
            app.clipboard().setText(PresetClipboard.to_tsv(selected))

        QToolTip.showText(
            QCursor.pos(),
            tr("preset.clipboard.copied", count=len(selected)),
            self._preset_view.table_view,
        )

    def _on_preset_cut(self) -> None:
        if not self._current_sheet:
            return
        rows = self._preset_view.selected_source_rows()
        if not rows:
            return
        entries = self._store.get_sheet_entries(self._current_sheet)
        selected = [(r, entries[r]) for r in rows if 0 <= r < len(entries)]
        if not selected:
            return

        PresetClipboard.instance().set([e for _, e in selected])

        self._undo_stack.beginMacro(
            tr("undo.macro.cut_presets", count=len(selected), sheet=self._current_sheet)
        )
        for row, entry in sorted(selected, key=lambda x: x[0], reverse=True):
            cmd = DeletePresetEntryCommand(self._store, self._current_sheet, entry, row)
            self._undo_stack.push(cmd)
        self._undo_stack.endMacro()

        QToolTip.showText(
            QCursor.pos(),
            tr("preset.clipboard.cut", count=len(selected)),
            self._preset_view.table_view,
        )

    def _on_preset_paste(self) -> None:
        if not self._current_sheet:
            return
        clipboard = PresetClipboard.instance()
        if not clipboard.has_content():
            return

        entries = clipboard.get_entries()
        count = len(entries)

        self._undo_stack.beginMacro(
            tr("undo.macro.paste_presets", count=count, sheet=self._current_sheet)
        )
        for e in entries:
            cloned = PresetClipboard.clone_with_new_id(e)
            cmd = AddPresetEntryCommand(self._store, self._current_sheet, cloned)
            self._undo_stack.push(cmd)
        self._undo_stack.endMacro()

        QToolTip.showText(
            QCursor.pos(),
            tr("preset.clipboard.pasted", count=count, sheet=self._current_sheet),
            self._preset_view.table_view,
        )

    # ── Find & Replace ─────────────────────────────────────────────────

    def _on_find_replace(self) -> None:
        dlg = FindReplaceDialog(
            self._store,
            self._undo_stack,
            current_sheet=self._current_sheet,
            parent=self,
        )
        dlg.exec()
        if self._current_sheet:
            self._load_sheet_into_right_panel(self._current_sheet)