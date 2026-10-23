from __future__ import annotations
from typing import Optional
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QDialogButtonBox,
    QHeaderView,
    QWidget,
)
from locales.i18n_manager import tr


class KeyboardShortcutsDialog(QDialog):

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("dialog.shortcuts.title", default="Keyboard Shortcuts"))
        self.resize(450, 500)

        layout = QVBoxLayout(self)

        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels([
            tr("dialog.shortcuts.action", default="Action"),
            tr("dialog.shortcuts.shortcut", default="Shortcut")
        ])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionMode(QTableWidget.NoSelection)
        table.setShowGrid(False)

        shortcuts = [
            ("Ctrl+P", tr("dialog.shortcuts.cmd_palette", default="Command Palette")),
            ("Ctrl+R", tr("dialog.shortcuts.find_replace", default="Find & Replace")),
            ("Ctrl+C", tr("dialog.shortcuts.copy", default="Copy selected preset(s)")),
            ("Ctrl+X", tr("dialog.shortcuts.cut", default="Cut selected preset(s)")),
            ("Ctrl+V", tr("dialog.shortcuts.paste", default="Paste preset(s)")),
            ("Ctrl+A", tr("dialog.shortcuts.select_all", default="Select all in current table")),
            ("Ctrl+Shift+Click", tr("dialog.shortcuts.extend_sel", default="Extend selection to clicked row")),
            ("Ctrl+Z", tr("dialog.shortcuts.undo", default="Undo")),
            ("Ctrl+Y", tr("dialog.shortcuts.redo", default="Redo")),
            ("Ctrl+N", tr("dialog.shortcuts.new_sheet", default="New sheet")),
            ("Ctrl+S", tr("dialog.shortcuts.save", default="Save and backup")),
            ("Delete", tr("dialog.shortcuts.delete", default="Delete selected item")),
            ("Esc", tr("dialog.shortcuts.esc", default="Close dialog")),
        ]

        table.setRowCount(len(shortcuts))
        for row, (shortcut, action) in enumerate(shortcuts):
            item_action = QTableWidgetItem(action)
            item_shortcut = QTableWidgetItem(shortcut)
            table.setItem(row, 0, item_action)
            table.setItem(row, 1, item_shortcut)

        layout.addWidget(table)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)