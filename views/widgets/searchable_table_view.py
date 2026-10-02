from __future__ import annotations

from typing import Any, Optional

from PySide6.QtCore import (
    QSortFilterProxyModel,
    QTimer,
    Qt,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableView,
    QVBoxLayout,
    QWidget,
)


class SearchableTableView(QWidget):

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        *,
        sortable: bool = True,
        selection_mode: QAbstractItemView.SelectionMode = QAbstractItemView.SingleSelection,
        selection_behavior: QAbstractItemView.SelectionBehavior = QAbstractItemView.SelectRows,
        stretch_columns: bool = True,
        drag_drop: bool = False,
    ) -> None:
        super().__init__(parent)

        self._proxy = QSortFilterProxyModel(self)
        self._proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self._proxy.setFilterKeyColumn(-1)

        self._table = QTableView(self)
        self._table.setModel(self._proxy)
        self._table.setSelectionBehavior(selection_behavior)
        self._table.setSelectionMode(selection_mode)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)

        self._sortable = sortable
        self._drag_drop_enabled = drag_drop

        if sortable:
            self._table.setSortingEnabled(True)
            self._table.horizontalHeader().setSortIndicatorShown(True)

        if stretch_columns:
            self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        if drag_drop:
            self._table.setDragEnabled(True)
            self._table.setAcceptDrops(True)
            self._table.setDragDropMode(QAbstractItemView.InternalMove)
            self._table.setDropIndicatorShown(True)
            if sortable:
                self._table.horizontalHeader().sortIndicatorChanged.connect(self._update_drag_drop_state)
                self._proxy.sort(-1)
                self._table.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)
            self._update_drag_drop_state()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._table)

        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(150)
        self._debounce_timer.timeout.connect(self._apply_filter)
        self._pending_filter: str = ""

    # ── Public API ─────────────────────────────────────────────────────

    @property
    def table_view(self) -> QTableView:
        return self._table

    @property
    def proxy_model(self) -> QSortFilterProxyModel:
        return self._proxy

    def set_source_model(self, model: Any) -> None:
        self._proxy.setSourceModel(model)
        self._update_drag_drop_state()

    def set_filter_text(self, text: str) -> None:
        self._pending_filter = text
        self._debounce_timer.start()

    def sort_toggle(self, column: int = 0) -> None:
        header = self._table.horizontalHeader()
        current_section = header.sortIndicatorSection()
        current_order = header.sortIndicatorOrder()

        if current_section != column:
            self._table.sortByColumn(column, Qt.AscendingOrder)
        elif current_order == Qt.AscendingOrder:
            self._table.sortByColumn(column, Qt.DescendingOrder)
        else:
            self._reset_sorting()

        self._update_drag_drop_state()

    def _reset_sorting(self) -> None:
        header = self._table.horizontalHeader()
        self._table.setSortingEnabled(False)
        header.setSortIndicator(-1, Qt.AscendingOrder)
        self._proxy.sort(-1, Qt.AscendingOrder)
        self._proxy.invalidate()
        self._table.setSortingEnabled(True)

    def selected_source_rows(self) -> list[int]:
        sel = self._table.selectionModel()
        if sel is None:
            return []
        source_rows: set[int] = set()
        for idx in sel.selectedIndexes():
            source_rows.add(self._proxy.mapToSource(idx).row())
        return sorted(source_rows)

    def set_edit_triggers(self, triggers: QAbstractItemView.EditTriggers) -> None:
        self._table.setEditTriggers(triggers)

    # ── Internal ───────────────────────────────────────────────────────

    def _apply_filter(self) -> None:
        self._proxy.setFilterFixedString(self._pending_filter)

    def _update_drag_drop_state(self, *args) -> None:
        if not self._drag_drop_enabled:
            return
        is_sorted = self._table.horizontalHeader().sortIndicatorSection() != -1
        self._table.setAcceptDrops(not is_sorted)
        self._table.setDragEnabled(not is_sorted)