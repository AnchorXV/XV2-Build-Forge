from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal
from PySide6.QtGui import QBrush, QColor

from app_config import SUMMARY_COLUMNS, TABLE_COLUMNS

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

    def begin_add(self) -> None:
        row = len(self._entries)
        self.beginInsertRows(QModelIndex(), row, row)

    def end_add(self) -> None:
        self.endInsertRows()

    def begin_remove(self, row: int) -> None:
        self.beginRemoveRows(QModelIndex(), row, row)

    def end_remove(self) -> None:
        self.endRemoveRows()

    def get_entry(self, row: int) -> Optional[dict]:
        entries = self._entries
        if 0 <= row < len(entries):
            return entries[row]
        return None


class RosterSummaryTableModel(QAbstractTableModel):

    sheets_reordered = Signal(list, list)

    def __init__(self, data_store: "AppDataStore", parent: Any = None) -> None:
        super().__init__(parent)
        self._store = data_store
        self._summaries: list[dict[str, Any]] = []
        self.rebuild_summaries()

    def refresh(self) -> None:
        self.rebuild_summaries()

    def sheet_name_at(self, row: int) -> Optional[str]:
        return self.get_sheet_name(row)

    def rebuild_summaries(self) -> None:
        self.beginResetModel()
        self._summaries.clear()
        for sheet_name, presets in self._store.rosters.items():
            meta = self._store.get_sheet_meta(sheet_name)
            self._summaries.append(self._calculate_summary(sheet_name, presets, meta))
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._summaries)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(SUMMARY_COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid():
            return None
        row, col = index.row(), index.column()
        if row >= len(self._summaries):
            return None

        summary = self._summaries[row]
        warnings = summary.get("_warnings", [])
        meta = summary.get("_meta", {})
        has_note = bool(meta.get("note", "").strip())
        has_tags = bool(meta.get("tags", []))

        if role == Qt.DisplayRole:
            col_name = SUMMARY_COLUMNS[col]
            val = str(summary.get(col_name, ""))
            if col == 0:
                prefix = ""
                if warnings:
                    prefix += "⚠️ "
                if has_note or has_tags:
                    prefix += "🏷️ "
                val = f"{prefix}{val}"
            return val
        if role == Qt.ToolTipRole:
            tooltip_lines = []
            if has_note:
                tooltip_lines.append(f"<b>Note:</b> {meta.get('note')}")
            if has_tags:
                tooltip_lines.append(f"<b>Tags:</b> {', '.join(meta.get('tags'))}")
            if warnings:
                if tooltip_lines:
                    tooltip_lines.append("<hr>")
                tooltip_lines.append("<b>Incomplete Presets:</b>")
                for label, missing in warnings:
                    tooltip_lines.append(f"• {label}: <i>{', '.join(missing)}</i>")
            if tooltip_lines:
                return "<br>".join(tooltip_lines)
            return None
        if role == Qt.TextAlignmentRole:
            return int(Qt.AlignCenter)
        if role == Qt.ForegroundRole:
            if warnings:
                return QBrush(QColor("#FFCC00"))
            return None
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if 0 <= section < len(SUMMARY_COLUMNS):
                return SUMMARY_COLUMNS[section]
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

        insert_row = row if row >= 0 else len(self._summaries)
        insert_row = max(0, min(insert_row, len(self._summaries)))

        dragged_names = []
        for r in dragged_rows:
            name = self.get_sheet_name(r)
            if name:
                dragged_names.append(name)

        if not dragged_names:
            return False

        old_order = list(self._store.rosters.keys())

        remaining_names = []
        for i in range(len(self._summaries)):
            if i not in dragged_set:
                name = self.get_sheet_name(i)
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

    def get_sheet_name(self, row: int) -> Optional[str]:
        if 0 <= row < len(self._summaries):
            return str(self._summaries[row].get("Character Name", ""))
        return None

    @staticmethod
    def _calculate_summary(table_name: str, presets: list, meta: dict[str, Any] = None) -> dict[str, Any]:
        from models.completeness import check_preset_completeness

        costumes: set[Any] = set()
        supers: set[str] = set()
        ultimates: set[str] = set()
        awokens: set[str] = set()
        evasives: set[str] = set()
        supersouls: set[str] = set()
        warnings: list[tuple[str, list[str]]] = []

        for p in presets:
            if hasattr(p, "costume_index"):
                missing = check_preset_completeness(p)
                if missing:
                    label = p.character_name or "Unnamed"
                    if p.costume_name:
                        label = f"{label} ({p.costume_name})"
                    warnings.append((label, missing))
                costumes.add(p.costume_index)
                for s in p.super_skills:
                    if s.strip():
                        supers.add(s.strip())
                for u in p.ultimate_skills:
                    if u.strip():
                        ultimates.add(u.strip())
                if p.awoken_skill.strip():
                    awokens.add(p.awoken_skill.strip())
                if p.evasive_skill.strip():
                    evasives.add(p.evasive_skill.strip())
                if p.super_soul.strip():
                    supersouls.add(p.super_soul.strip())
            else:
                costumes.add(p.get("Costume Index", 0))
                for i in range(1, 5):
                    s = str(p.get(f"Super Skill {i}", "")).strip()
                    if s:
                        supers.add(s)
                for i in range(1, 3):
                    u = str(p.get(f"Ultimate Skill {i}", "")).strip()
                    if u:
                        ultimates.add(u)
                aw = str(p.get("Awoken Skill", "")).strip()
                if aw:
                    awokens.add(aw)
                ev = str(p.get("Evasive Skill", "")).strip()
                if ev:
                    evasives.add(ev)
                ss = str(p.get("Super Soul", "")).strip()
                if ss:
                    supersouls.add(ss)

        return {
            "Character Name": table_name,
            "Total Costume": len(costumes),
            "Total Preset": len(presets),
            "Total Super Skill": len(supers),
            "Total Ultimate Skill": len(ultimates),
            "Total Awoken Skill": len(awokens),
            "Total Evasive Skill": len(evasives),
            "Total Super Soul": len(supersouls),
            "_warnings": warnings,
            "_meta": meta or {},
        }


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

        missing = []
        if hasattr(p, "costume_index"):
            from models.completeness import check_preset_completeness
            missing = check_preset_completeness(p)

        if role == Qt.DisplayRole:
            if hasattr(p, "to_dict"):
                val = str(p.to_dict().get(col_name, ""))
            else:
                val = str(p.get(col_name, ""))
            if col == 0 and missing:
                val = f"⚠️ {val}"
            return val
        if role == Qt.ToolTipRole:
            if missing:
                return f"Missing slots: {', '.join(missing)}"
            return None
        if role == Qt.TextAlignmentRole:
            return int(Qt.AlignCenter)
        if role == Qt.ForegroundRole:
            if missing:
                return QBrush(QColor("#FFCC00"))
            return None
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