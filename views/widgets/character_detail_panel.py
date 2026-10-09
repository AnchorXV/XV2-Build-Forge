from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from locales.i18n_manager import tr


class CharacterDetailPanel(QFrame):

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("characterDetailPanel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        self._title = QLabel("")
        self._title.setObjectName("panelTitle")
        self._title.setWordWrap(True)
        layout.addWidget(self._title)

        self._info = QLabel("")
        self._info.setObjectName("panelInfo")
        self._info.setWordWrap(True)
        layout.addWidget(self._info)

        layout.addStretch()

        self.clear()

    def clear(self) -> None:
        self._title.setText(tr("database.character_panel.no_selection"))
        self._info.setText("")

    def set_character(self, data: dict) -> None:
        name = data.get("name", "") or "—"
        code = data.get("code", "") or "—"
        base = data.get("base_character", "") or "—"
        playable = "Yes" if data.get("is_playable", True) else "No"
        episodes = data.get("episodes", [])

        self._title.setText(name)

        lines = [
            f"<b>{tr('database.character_panel.code')}:</b> {code}",
            f"<b>{tr('database.character_panel.base')}:</b> {base}",
            f"<b>{tr('database.character_panel.playable')}:</b> {playable}",
            f"<b>{tr('database.character_panel.episodes')}:</b> {len(episodes)}",
        ]
        self._info.setText("<br>".join(lines))