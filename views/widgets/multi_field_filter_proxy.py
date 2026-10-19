from __future__ import annotations
from PySide6.QtCore import QModelIndex, QSortFilterProxyModel, Qt

class MultiFieldFilterProxy(QSortFilterProxyModel):

    def __init__(self, field_keys: list[str], parent=None) -> None:
        super().__init__(parent)
        self._field_keys = list(field_keys)
        self._filter_text = ""
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.setDynamicSortFilter(True)

    def set_field_keys(self, field_keys: list[str]) -> None:
        self.beginFilterChange()
        self._field_keys = list(field_keys)
        self.endFilterChange(QSortFilterProxyModel.Direction.Rows)

    def set_filter_text(self, text: str) -> None:
        self.beginFilterChange()
        self._filter_text = (text or "").strip().lower()
        self.endFilterChange(QSortFilterProxyModel.Direction.Rows)

    def filter_text(self) -> str:
        return self._filter_text

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        if not self._filter_text:
            return True
        model = self.sourceModel()
        if model is None or not hasattr(model, "get_entry"):
            return True
        entry = model.get_entry(source_row)
        if not isinstance(entry, dict):
            return True
        needle = self._filter_text
        for key in self._field_keys:
            val = entry.get(key, "")
            if val is None:
                continue
            if needle in str(val).lower():
                return True
        return False