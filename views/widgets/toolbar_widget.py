"""
DBXV2 Build Forge — Reusable Toolbar Widget.

Provides a standard horizontal bar with ``+`` (add), ``Sort A-Z``, and a
search ``QLineEdit``, used identically by every Database Manager tab and
the Roster Preview tab.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)


class ToolbarWidget(QWidget):
    """Horizontal toolbar emitting semantic signals.

    Signals:
        add_clicked: Emitted when the ``+`` button is pressed.
        sort_clicked: Emitted when the ``Sort A-Z`` button is pressed.
        search_changed: Emitted with the search text on every keystroke.
    """

    add_clicked = Signal()
    sort_clicked = Signal()
    search_changed = Signal(str)
    fix_cache_clicked = Signal()

    def __init__(
        self,
        *,
        add_tooltip: str = "",
        search_placeholder: str = "",
        search_label: str = "Search:",
        sort_label: str = "Sort A-Z",
        fix_cache_label: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Add button
        self.add_btn = QPushButton("+")
        self.add_btn.setObjectName("addButton")
        self.add_btn.setToolTip(add_tooltip)
        self.add_btn.setFixedSize(34, 30)
        self.add_btn.setStyleSheet("padding: 0px; margin: 0px; font-weight: bold; font-size: 18px; text-align: center;")
        self.add_btn.clicked.connect(self.add_clicked.emit)
        layout.addWidget(self.add_btn)

        # Sort button
        self.sort_btn = QPushButton(sort_label)
        self.sort_btn.setObjectName("sortButton")
        self.sort_btn.clicked.connect(self.sort_clicked.emit)
        layout.addWidget(self.sort_btn)

        # Fix cache button (optional)
        self.fix_cache_btn = None
        if fix_cache_label is not None:
            self.fix_cache_btn = QPushButton(fix_cache_label)
            self.fix_cache_btn.setObjectName("fixCacheButton")
            self.fix_cache_btn.clicked.connect(self.fix_cache_clicked.emit)
            layout.addWidget(self.fix_cache_btn)

        layout.addStretch()

        # Search
        self._search_label = QLabel(search_label)
        layout.addWidget(self._search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(search_placeholder)
        self.search_input.setFixedWidth(240)
        self.search_input.textChanged.connect(self.search_changed.emit)
        layout.addWidget(self.search_input)

    # ── Retranslation ──────────────────────────────────────────────────

    def retranslate(
        self,
        *,
        add_tooltip: str = "",
        search_placeholder: str = "",
        search_label: str = "Search:",
        sort_label: str = "Sort A-Z",
        fix_cache_label: Optional[str] = None,
    ) -> None:
        """Update all visible text for live language switching."""
        self.add_btn.setToolTip(add_tooltip)
        self.sort_btn.setText(sort_label)
        if self.fix_cache_btn and fix_cache_label is not None:
            self.fix_cache_btn.setText(fix_cache_label)
        self._search_label.setText(search_label)
        self.search_input.setPlaceholderText(search_placeholder)
