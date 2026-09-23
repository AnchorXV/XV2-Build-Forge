"""
DBXV2 Build Forge — Searchable Table View Widget.

A ``QTableView`` with an integrated ``QSortFilterProxyModel`` and
an optional debounced search bar.  Replaces the manual ``filter_table()``
+ ``setRowHidden()`` pattern from the prototype (PRD §3.1).
"""

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
    """A ``QTableView`` wrapped with a proxy model for live filtering and sorting.

    The search bar (``QLineEdit``) is *not* included in this widget —
    it is provided externally by the toolbar and connected via
    :meth:`set_filter_text`.  This keeps the layout flexible.
    """

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
        self._proxy.setFilterKeyColumn(-1)  # Search across all columns

        self._table = QTableView(self)
        self._table.setModel(self._proxy)
        self._table.setSelectionBehavior(selection_behavior)
        self._table.setSelectionMode(selection_mode)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)

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
                # Clear initial sort
                self._proxy.sort(-1)
                self._table.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)
                self._update_drag_drop_state()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._table)

        # Debounce timer for search input (150 ms, per PRD §3.1 recommendation)
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(150)
        self._debounce_timer.timeout.connect(self._apply_filter)
        self._pending_filter: str = ""

    # ── Public API ─────────────────────────────────────────────────────

    @property
    def table_view(self) -> QTableView:
        """Direct access to the underlying ``QTableView``."""
        return self._table

    @property
    def proxy_model(self) -> QSortFilterProxyModel:
        """Direct access to the ``QSortFilterProxyModel``."""
        return self._proxy

    def set_source_model(self, model: Any) -> None:
        """Set the source ``QAbstractTableModel``."""
        self._proxy.setSourceModel(model)

    def set_filter_text(self, text: str) -> None:
        """Set the filter text with debounce.

        Called from the toolbar's search ``QLineEdit.textChanged`` signal.
        """
        self._pending_filter = text
        self._debounce_timer.start()

    def sort_toggle(self, column: int = 0) -> None:
        """Toggle sort order on *column*."""
        current_section = self._table.horizontalHeader().sortIndicatorSection()
        current_order = self._table.horizontalHeader().sortIndicatorOrder()
        
        if current_section == -1:
            self._proxy.sort(column, Qt.AscendingOrder)
            self._table.horizontalHeader().setSortIndicator(column, Qt.AscendingOrder)
        elif current_order == Qt.AscendingOrder:
            self._proxy.sort(column, Qt.DescendingOrder)
            self._table.horizontalHeader().setSortIndicator(column, Qt.DescendingOrder)
        else:
            self._proxy.sort(-1)
            self._table.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)

    def selected_source_rows(self) -> list[int]:
        """Return source-model row indices for all selected rows."""
        rows: list[int] = []
        for idx in self._table.selectionModel().selectedRows():
            source_idx = self._proxy.mapToSource(idx)
            rows.append(source_idx.row())
        return sorted(set(rows))

    def set_edit_triggers(self, triggers: QAbstractItemView.EditTriggers) -> None:
        """Set which user actions start editing cells."""
        self._table.setEditTriggers(triggers)

    # ── Internal ───────────────────────────────────────────────────────

    def _apply_filter(self) -> None:
        self._proxy.setFilterFixedString(self._pending_filter)

    def _update_drag_drop_state(self, *args) -> None:
        is_sorted = self._table.horizontalHeader().sortIndicatorSection() != -1
        self._table.setAcceptDrops(not is_sorted)
        self._table.setDragEnabled(not is_sorted)
