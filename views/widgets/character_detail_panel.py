from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from locales.i18n_manager import tr
from models.character_usage import find_character_skills, find_character_souls

if TYPE_CHECKING:
    from models.data_store import AppDataStore


class CharacterDetailPanel(QFrame):

    edit_requested = Signal()
    delete_requested = Signal()

    def __init__(self, store: "AppDataStore", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("characterDetailPanel")
        self._store = store
        self._current_row: int = -1

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setObjectName("characterDetailScroll")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Title
        self._title = QLabel("")
        self._title.setObjectName("panelTitle")
        self._title.setWordWrap(True)
        layout.addWidget(self._title)

        # Character (base)
        self._character_label = self._make_field_label(
            tr("database.character_panel.character")
        )
        layout.addWidget(self._character_label)

        self._character_value = QLabel("")
        self._character_value.setObjectName("panelValue")
        self._character_value.setWordWrap(True)
        layout.addWidget(self._character_value)

        # Appear on Source
        self._episodes_label = self._make_field_label(
            tr("database.character_panel.episodes")
        )
        layout.addWidget(self._episodes_label)

        self._episodes_list = QListWidget()
        self._episodes_list.setObjectName("panelList")
        self._episodes_list.setMinimumHeight(80)
        self._episodes_list.setMaximumHeight(140)
        layout.addWidget(self._episodes_list)

        # Code + Playable row
        code_row = QHBoxLayout()
        code_row.setSpacing(12)

        self._code_label = self._make_field_label(
            tr("database.character_panel.code")
        )
        code_row.addWidget(self._code_label)

        self._code_value = QLabel("")
        self._code_value.setObjectName("panelValueInline")
        code_row.addWidget(self._code_value)

        code_row.addStretch()

        self._playable_label = self._make_field_label(
            tr("database.character_panel.playable")
        )
        code_row.addWidget(self._playable_label)

        self._playable_value = QLabel("")
        self._playable_value.setObjectName("panelValueInline")
        code_row.addWidget(self._playable_value)

        layout.addLayout(code_row)

        # Skill used by
        self._skills_label = self._make_field_label("")
        layout.addWidget(self._skills_label)

        self._skills_list = QListWidget()
        self._skills_list.setObjectName("panelList")
        self._skills_list.setMinimumHeight(100)
        self._skills_list.setMaximumHeight(180)
        layout.addWidget(self._skills_list)

        # Super Soul used by
        self._souls_label = self._make_field_label("")
        layout.addWidget(self._souls_label)

        self._souls_list = QListWidget()
        self._souls_list.setObjectName("panelList")
        self._souls_list.setMinimumHeight(80)
        self._souls_list.setMaximumHeight(140)
        layout.addWidget(self._souls_list)

        layout.addStretch()

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.addStretch()

        self._edit_btn = QPushButton(tr("database.character_panel.edit"))
        self._edit_btn.setObjectName("secondaryButton")
        self._edit_btn.clicked.connect(self.edit_requested.emit)
        btn_row.addWidget(self._edit_btn)

        self._delete_btn = QPushButton(tr("database.character_panel.delete"))
        self._delete_btn.setObjectName("dangerButton")
        self._delete_btn.clicked.connect(self.delete_requested.emit)
        btn_row.addWidget(self._delete_btn)

        layout.addLayout(btn_row)

        scroll.setWidget(container)
        outer.addWidget(scroll)

        self.clear()

    @staticmethod
    def _make_field_label(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("panelFieldLabel")
        return label

    def clear(self) -> None:
        self._current_row = -1
        self._title.setText(tr("database.character_panel.no_selection"))
        self._character_value.setText("")
        self._episodes_list.clear()
        self._code_value.setText("")
        self._playable_value.setText("")
        self._skills_label.setText("")
        self._skills_list.clear()
        self._souls_label.setText("")
        self._souls_list.clear()
        self._set_buttons_enabled(False)

    def set_character(self, row: int, data: dict) -> None:
        self._current_row = row

        name = data.get("name", "") or "—"
        self._title.setText(name)

        self._character_value.setText(data.get("base_character", "") or "—")

        episodes = data.get("episodes", [])
        self._episodes_label.setText(
            tr("database.character_panel.episodes_with_count", count=len(episodes))
        )
        self._episodes_list.clear()
        for ep in episodes:
            self._episodes_list.addItem(ep)

        self._code_value.setText(data.get("code", "") or "—")
        self._playable_value.setText(
            tr("dialog.common.yes") if data.get("is_playable", True) else tr("dialog.common.no")
        )

        char_name = data.get("name", "")
        skills = find_character_skills(self._store, char_name)
        self._skills_label.setText(
            tr("database.character_panel.skill_used_by", name=name)
        )
        self._skills_list.clear()
        for skill_display, count in skills:
            label = tr(
                "database.character_panel.list_item",
                name=skill_display,
                count=count,
            )
            self._skills_list.addItem(label)

        souls = find_character_souls(self._store, char_name)
        self._souls_label.setText(
            tr("database.character_panel.soul_used_by", name=name)
        )
        self._souls_list.clear()
        for soul_name, count in souls:
            label = tr(
                "database.character_panel.list_item",
                name=soul_name,
                count=count,
            )
            self._souls_list.addItem(label)

        self._set_buttons_enabled(True)

    def _set_buttons_enabled(self, enabled: bool) -> None:
        self._edit_btn.setEnabled(enabled)
        self._delete_btn.setEnabled(enabled)

    def current_row(self) -> int:
        return self._current_row