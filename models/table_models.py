from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal

from app_config import TABLE_COLUMNS

if TYPE_CHECKING:
    from models.data_store import AppDataStore


class DatabaseTableModel(QAbstractTableModel):

    def __init__(
        self,
        data_store: "AppDataStore",
        cache_key: str,
        columns: Optional[list[str]] = None,
        entry_type: Optional[str] = None,
        parent: Any = None,
    ) -> None:
        super().__init__(parent)
        self._store = data_store
        self._cache_key = cache_key

        if columns is None:
            if cache_key == "characters":
                from app_config import CHAR_DB_COLUMNS
                self._columns = CHAR_DB_COLUMNS
                self._entry_type = entry_type or "char"
            elif cache_key == "super_souls":
                from app_config import SUPERSOUL_DB_COLUMNS
                self._columns = SUPERSOUL_DB_COLUMNS
                self._entry_type = entry_type or "supersoul"
            else:
                from app_config import SKILL_DB_COLUMNS
                self._columns = SKILL_DB_COLUMNS
                self._entry_type = entry_type or "skill"
        else:
            self._columns = columns
            self._entry_type = entry_type or "skill"

    @property
    def _entries(self) -> list[dict]:
        return self._store.dropdown_cache.get(self._cache_key, [])

    def _map_col_to_key(self, col_name: str) -> str:
        if self._entry_type == "char":
            mapping = {
                "Code": "code",
                "Name": "name",
                "Playable Character": "is_playable",
            }
        elif self._entry_type == "supersoul":
            mapping = {
                "Super Soul": "name",
                "Effect 1": "effect_1",
                "Effect 2": "effect_2",
                "Note": "note",
            }
        else:
            mapping = {
                "Skill Name": "name",
                "Is CaC Skill?": "is_cac",
                "Note": "note",
            }
        return mapping.get(col_name, col_name.lower())

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._entries)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._columns)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid():
            return None
        row, col = index.row(), index.column()
        if row >= len(self._entries):
            return None

        entry = self._entries[row]
        col_name = self._columns[col]
        dict_key = self._map_col_to_key(col_name)

        if isinstance(entry, str):
            val = entry if col == 0 else ""
        else:
            val = entry.get(dict_key, "")

        if isinstance(val, bool):
            val = "Yes" if val else "No"

        if role in (Qt.DisplayRole, Qt.EditRole):
            return str(val)
        if role == Qt.TextAlignmentRole:
            return int(Qt.AlignCenter)
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if 0 <= section < len(self._columns):
                return self._columns[section]
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        base = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if not index.isValid():
            return base
        col_name = self._columns[index.column()]
        if col_name == "Note" and self._entry_type in ("skill", "supersoul"):
            return base | Qt.ItemIsEditable
        return base

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.EditRole) -> bool:
        if role != Qt.EditRole or not index.isValid():
            return False
        row, col = index.row(), index.column()
        col_name = self._columns[col]
        dict_key = self._map_col_to_key(col_name)

        if dict_key == "note" and self._entry_type in ("skill", "supersoul"):
            if row < len(self._entries):
                self._entries[row]["note"] = str(value).strip()
                self._store.save()
                self.dataChanged.emit(index, index, [Qt.DisplayRole])
                return True
        return False

    def refresh(self) -> None:
        self.beginResetModel()
        self.endResetModel()

    def get_entry(self, row: int) -> Optional[dict]:
        entries = self._entries
        if 0 <= row < len(entries):
            return entries[row]
        return None


class RosterSummaryTableModel(QAbstractTableModel):

    sheets_reordered = Signal(list, list)

    COLUMNS = ["Sheet Name", "Presets"]

    def __init__(self, data_store: "AppDataStore", parent: Any = None) -> None:
        super().__init__(parent)
        self._store = data_store
        self._sheets: list[tuple[str, int]] = []
        self.rebuild_summaries()

    def rebuild_summaries(self) -> None:
        self.beginResetModel()
        self._sheets.clear()
        for name, presets in self._store.rosters.items():
            self._sheets.append((name, len(presets)))
        self.endResetModel()

    def refresh(self) -> None:
        self.rebuild_summaries()

    def sheet_name_at(self, row: int) -> Optional[str]:
        if 0 <= row < len(self._sheets):
            return self._sheets[row][0]
        return None

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._sheets)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 2

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid():
            return None
        row, col = index.row(), index.column()
        if row >= len(self._sheets):
            return None

        name, count = self._sheets[row]

        if role == Qt.DisplayRole:
            return name if col == 0 else str(count)
        if role == Qt.TextAlignmentRole:
            if col == 0:
                return int(Qt.AlignLeft | Qt.AlignVCenter)
            return int(Qt.AlignCenter)
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if 0 <= section < len(self.COLUMNS):
                return self.COLUMNS[section]
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        base = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if index.isValid():
            return base | Qt.ItemIsDragEnabled
        return base | Qt.ItemIsDropEnabled

    def supportedDropActions(self) -> Qt.DropActions:
        return Qt.MoveAction

    def mimeTypes(self) -> list[str]:
        return ["application/x-sheet-row"]

    def mimeData(self, indexes: list[QModelIndex]) -> Any:
        from PySide6.QtCore import QMimeData
        import json
        mime_data = QMimeData()
        rows = sorted(set(idx.row() for idx in indexes if idx.column() == 0))
        if not rows and indexes:
            rows = sorted(set(idx.row() for idx in indexes))
        mime_data.setData("application/x-sheet-row", json.dumps(rows).encode("utf-8"))
        return mime_data

    def dropMimeData(self, data: Any, action: Qt.DropAction, row: int, column: int, parent: QModelIndex) -> bool:
        if action != Qt.MoveAction:
            return False
        if not data.hasFormat("application/x-sheet-row"):
            return False

        import json
        try:
            dragged_rows = json.loads(data.data("application/x-sheet-row").data().decode("utf-8"))
        except (ValueError, TypeError):
            return False

        if not dragged_rows:
            return False

        dragged_rows = sorted(set(dragged_rows))
        dragged_set = set(dragged_rows)

        insert_row = row if row >= 0 else len(self._sheets)
        insert_row = max(0, min(insert_row, len(self._sheets)))

        dragged_names = []
        for r in dragged_rows:
            name = self.sheet_name_at(r)
            if name:
                dragged_names.append(name)

        if not dragged_names:
            return False

        old_order = list(self._store.rosters.keys())

        remaining_names = []
        for i in range(len(self._sheets)):
            if i not in dragged_set:
                name = self.sheet_name_at(i)
                if name:
                    remaining_names.append(name)

        adjusted_insert = insert_row
        for dr in dragged_rows:
            if dr < insert_row:
                adjusted_insert -= 1
        adjusted_insert = max(0, min(adjusted_insert, len(remaining_names)))

        new_order = (
            remaining_names[:adjusted_insert]
            + dragged_names
            + remaining_names[adjusted_insert:]
        )

        if new_order != old_order:
            self.sheets_reordered.emit(old_order, new_order)

        return False


class PresetDetailTableModel(QAbstractTableModel):

    presets_reordered = Signal(list, list)

    def __init__(self, presets: list, parent: Any = None) -> None:
        super().__init__(parent)
        self._presets = presets

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._presets)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(TABLE_COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid():
            return None
        row, col = index.row(), index.column()
        if row >= len(self._presets):
            return None

        p = self._presets[row]
        col_name = TABLE_COLUMNS[col]

        if role == Qt.DisplayRole:
            if hasattr(p, "to_dict"):
                val = str(p.to_dict().get(col_name, ""))
            else:
                val = str(p.get(col_name, ""))
            return val
        if role == Qt.TextAlignmentRole:
            return int(Qt.AlignCenter)
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if 0 <= section < len(TABLE_COLUMNS):
                return TABLE_COLUMNS[section]
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        base = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if index.isValid():
            return base | Qt.ItemIsDragEnabled
        return base | Qt.ItemIsDropEnabled

    def supportedDropActions(self) -> Qt.DropActions:
        return Qt.MoveAction

    def mimeTypes(self) -> list[str]:
        return ["application/x-preset-row"]

    def mimeData(self, indexes: list[QModelIndex]) -> Any:
        from PySide6.QtCore import QMimeData
        import json
        mime_data = QMimeData()
        rows = sorted(set(idx.row() for idx in indexes if idx.column() == 0))
        if not rows and indexes:
            rows = sorted(set(idx.row() for idx in indexes))
        mime_data.setData("application/x-preset-row", json.dumps(rows).encode("utf-8"))
        return mime_data

    def dropMimeData(self, data: Any, action: Qt.DropAction, row: int, column: int, parent: QModelIndex) -> bool:
        if action != Qt.MoveAction:
            return False
        if not data.hasFormat("application/x-preset-row"):
            return False

        import json
        try:
            dragged_rows = json.loads(data.data("application/x-preset-row").data().decode("utf-8"))
        except (ValueError, TypeError):
            return False

        if not dragged_rows:
            return False

        dragged_rows = sorted(set(dragged_rows))
        dragged_set = set(dragged_rows)

        insert_row = row if row >= 0 else len(self._presets)
        insert_row = max(0, min(insert_row, len(self._presets)))

        def _entry_id(p):
            if hasattr(p, "entry_id"):
                return p.entry_id
            if isinstance(p, dict):
                return p.get("entry_id")
            return None

        old_order = [_entry_id(p) for p in self._presets]

        dragged_ids = []
        for r in dragged_rows:
            if 0 <= r < len(self._presets):
                eid = _entry_id(self._presets[r])
                if eid is not None:
                    dragged_ids.append(eid)

        if not dragged_ids:
            return False

        remaining_ids = []
        for i, p in enumerate(self._presets):
            if i not in dragged_set:
                eid = _entry_id(p)
                if eid is not None:
                    remaining_ids.append(eid)

        adjusted_insert = insert_row
        for dr in dragged_rows:
            if dr < insert_row:
                adjusted_insert -= 1
        adjusted_insert = max(0, min(adjusted_insert, len(remaining_ids)))

        new_order = (
            remaining_ids[:adjusted_insert]
            + dragged_ids
            + remaining_ids[adjusted_insert:]
        )

        if new_order != old_order:
            self.presets_reordered.emit(old_order, new_order)

        return False

    def get_preset(self, row: int) -> Any:
        if 0 <= row < len(self._presets):
            return self._presets[row]
        return None

    def update_data(self, new_presets: list) -> None:
        self.beginResetModel()
        self._presets = new_presets
        self.endResetModel()