from __future__ import annotations
import logging
from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QUndoStack
from PySide6.QtWidgets import (
    QAbstractItemView,
    QMenu,
    QMessageBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)
from app_config import get_resource_path
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
from views.widgets.database_detail_panel import DatabaseDetailPanel
from views.widgets.multi_field_filter_proxy import MultiFieldFilterProxy

logger = logging.getLogger(__name__)

SPLIT_MODE_KEYS: set[str] = {
    "characters",
    "super_skills",
    "ultimate_skills",
    "awoken_skills",
    "evasive_skills",
    "super_souls",
}

SKILL_FILTER_FIELDS = ["name", "skill_type", "ki_used", "note"]
SUPER_SOUL_FILTER_FIELDS = ["name", "owner", "effect_1", "effect_2", "limit_burst"]


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
            if category_key == "characters":
                self._model = DatabaseTableModel(
                    data_store,
                    category_key,
                    columns=["Name"],
                    entry_type="char",
                )
                filter_fields = ["name", "code", "base_character"]
            elif category_key == "super_souls":
                self._model = DatabaseTableModel(
                    data_store,
                    category_key,
                    columns=["Super Soul"],
                    entry_type="supersoul",
                )
                filter_fields = SUPER_SOUL_FILTER_FIELDS
            else:
                self._model = DatabaseTableModel(
                    data_store,
                    category_key,
                    columns=["Skill Name"],
                    entry_type="skill",
                )
                filter_fields = SKILL_FILTER_FIELDS
            self._filter_fields = filter_fields
        else:
            self._model = DatabaseTableModel(data_store, category_key)
            self._filter_fields = ["name"]

        self._detail_panel: Optional[DatabaseDetailPanel] = None

        self._build_ui()
        self._connect_signals()

    def _sort_options(self) -> list[tuple[str, str, str]]:
        az = tr("database.sort.az")
        za = tr("database.sort.za")
        if self._key == "sources":
            return [
                (az, SORT_AZ, "arrow-up-a-z.svg"),
                (za, SORT_ZA, "arrow-down-a-z.svg"),
                (tr("database.sort.date"), SORT_DATE, "calendar-plus.svg"),
            ]
        if self._key == "characters":
            return [
                (az, SORT_AZ, "arrow-up-a-z.svg"),
                (za, SORT_ZA, "arrow-down-a-z.svg"),
                (tr("database.sort.date_created"), SORT_DATE_CREATED, "calendar-plus.svg"),
                (tr("database.sort.date_modified"), SORT_DATE_MODIFIED, "rotate-cw-clock.svg"),
                (tr("database.sort.source"), SORT_SOURCE, "list-clock.svg"),
            ]
        return [
            (az, SORT_AZ, "arrow-up-a-z.svg"),
            (za, SORT_ZA, "arrow-down-a-z.svg"),
            (tr("database.sort.date_created"), SORT_DATE_CREATED, "calendar-plus.svg"),
            (tr("database.sort.date_modified"), SORT_DATE_MODIFIED, "rotate-cw-clock.svg"),
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
        layout.setContentsMargins(0, 0, 0, 0)

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
            selection_mode=QAbstractItemView.ExtendedSelection,
            stretch_columns=False,
        )

        proxy = MultiFieldFilterProxy(self._filter_fields, self)
        proxy.setSourceModel(self._model)
        self._stv.table_view.setModel(proxy)
        self._stv._proxy = proxy

        self._stv.table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self._stv.set_edit_triggers(QAbstractItemView.NoEditTriggers)

        header = self._stv.table_view.horizontalHeader()
        header.setSectionResizeMode(0, header.ResizeMode.Stretch)

        left_layout.addWidget(self._stv)
        splitter.addWidget(left)

        if self._key == "characters":
            self._detail_panel = CharacterDetailPanel(self._store, self)
            self._detail_panel.edit_requested.connect(self._on_edit_panel)
            self._detail_panel.delete_requested.connect(self._on_delete_panel)
            self._detail_panel.playable_changed.connect(self._on_playable_changed)
        else:
            self._detail_panel = DatabaseDetailPanel(
                self._store, self._undo_stack, self._key, self
            )
            self._detail_panel.edit_requested.connect(self._on_edit_panel)
            self._detail_panel.delete_requested.connect(self._on_delete_panel)
            self._detail_panel.navigate_requested.connect(
                lambda sheet, eid: signal_bus.navigate_to_preset.emit(sheet, eid)
            )
        splitter.addWidget(self._detail_panel)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([300, 700])

        parent_layout.addWidget(splitter, 1)

    # ── Signals ─────────────────────────────────────────────────────────

    def _connect_signals(self) -> None:
        self._stv.table_view.customContextMenuRequested.connect(self._on_context_menu)
        self._stv.table_view.doubleClicked.connect(self._on_edit)
        self._stv.table_view.selectionModel().selectionChanged.connect(
            self._on_selection_changed
        )
        signal_bus.data_changed.connect(self._on_data_changed)

    def _on_search_changed(self, text: str) -> None:
        if self._split_mode:
            proxy = self._stv.table_view.model()
            if hasattr(proxy, "set_filter_text"):
                proxy.set_filter_text(text)
        else:
            self._stv.set_filter_text(text)

    # ── Data refresh ────────────────────────────────────────────────────

    def _on_data_changed(self) -> None:
        if not self._split_mode:
            self._model.refresh()
            return

        old_count = self._model.rowCount()
        new_count = len(self._store.get_cache(self._key))

        if old_count == new_count:
            self._model.layoutChanged.emit()
        else:
            self._model.refresh()
        
        self._refresh_detail_panel()

    def _on_selection_changed(self, *_args) -> None:
        self._refresh_detail_panel()

    def _refresh_detail_panel(self) -> None:
        if self._detail_panel is None:
            return

        rows = self._stv.selected_source_rows()
        items = self._store.get_cache(self._key)
        valid_rows = [r for r in rows if 0 <= r < len(items)]

        if not valid_rows:
            self._detail_panel.clear()
            return

        if self._key == "characters":
            if len(valid_rows) >= 1:
                self._detail_panel.set_character(valid_rows[0], items[valid_rows[0]])
            else:
                self._detail_panel.clear()
        else:
            if len(valid_rows) == 1:
                self._detail_panel.set_single(valid_rows[0], items[valid_rows[0]])
            else:
                self._detail_panel.set_multi([items[r] for r in valid_rows])

    def _on_edit_panel(self) -> None:
        if self._detail_panel is None:
            return
        row = self._detail_panel.current_row()
        if row < 0:
            return
        self._on_edit_for_row(row)

    def _on_playable_changed(self, checked: bool) -> None:
        items = self._store.get_cache("characters")
        row = self._detail_panel.current_row()
        if row < 0 or row >= len(items):
            return
        old_entry = items[row]
        new_entry = dict(old_entry)
        new_entry["is_playable"] = checked
        cmd = EditCacheItemCommand(self._store, "characters", row, old_entry, new_entry)
        self._undo_stack.push(cmd)

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

        impact = count_merge_impact(self._store, self._key, name)
        if impact > 0:
            type_key = self._key
            if type_key in ("super_skills", "ultimate_skills", "awoken_skills", "evasive_skills"):
                type_key = "skill"
            elif type_key == "super_souls":
                type_key = "super_soul"
            elif type_key == "characters":
                type_key = "character"
            elif type_key == "sources":
                type_key = "source"

            msg = tr("database.message.confirm_delete_with_usage",
                     name=name, count=impact, type=type_key)
        else:
            msg = tr("database.message.confirm_delete", name=name)

        reply = QMessageBox.question(
            self,
            tr("dialog.common.confirm"),
            msg,
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
        icon_dir = get_resource_path("assets/icons")
        
        edit_action = menu.addAction(QIcon(str(icon_dir / "pencil.svg")), tr("database.context_menu.edit"))
        merge_action = menu.addAction(QIcon(str(icon_dir / "merge.svg")), tr("database.context_menu.merge"))
        delete_action = menu.addAction(QIcon(str(icon_dir / "trash.svg")), tr("database.context_menu.delete"))

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