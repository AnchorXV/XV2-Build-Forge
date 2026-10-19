from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QCompleter


def setup_searchable_combo(combo: QComboBox) -> None:
    combo.setEditable(True)
    combo.setInsertPolicy(QComboBox.NoInsert)

    completer = combo.completer()
    if completer is None:
        completer = QCompleter(combo.model(), combo)
        combo.setCompleter(completer)

    completer.setCompletionMode(QCompleter.PopupCompletion)
    completer.setFilterMode(Qt.MatchContains)
    completer.setCaseSensitivity(Qt.CaseInsensitive)
    completer.setMaxVisibleItems(15)


def populate_combo(combo: QComboBox, items: list[str], *, sorted_items: bool = False) -> None:
    if sorted_items:
        items = sorted(items)
    combo.addItems(items)