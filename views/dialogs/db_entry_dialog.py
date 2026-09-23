"""
DBXV2 Build Forge — Database Entry Dialogs.

Modal dialogs for adding / editing records in the five Database Manager
tabs: Character, Super, Ultimate, Awoken, Evasive, and Super Soul.

Migrated from ``CharacterDialog``, ``SkillDialog``, and
``SuperSoulDialog`` classes in the original ``main.py``.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from locales.i18n_manager import tr


# ── Character Dialog ────────────────────────────────────────────────────

class CharacterDialog(QDialog):
    """Add / edit a Character record."""

    def __init__(self, parent: Optional[QWidget] = None, *, edit_data: Optional[dict] = None) -> None:
        super().__init__(parent)
        self._is_edit = edit_data is not None
        self.setWindowTitle(
            tr("dialog.character.edit_title") if self._is_edit else tr("dialog.character.add_title")
        )
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText(tr("dialog.character.placeholder_code"))
        form.addRow(QLabel(tr("dialog.character.label_code")), self.code_input)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(tr("dialog.character.placeholder_name"))
        form.addRow(QLabel(tr("dialog.character.label_name")), self.name_input)

        self.playable_cb = QCheckBox()
        self.playable_cb.setChecked(True)
        form.addRow(QLabel(tr("dialog.character.label_playable")), self.playable_cb)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Pre-fill for edit mode
        if edit_data:
            self.code_input.setText(edit_data.get("code", ""))
            self.name_input.setText(edit_data.get("name", ""))
            self.playable_cb.setChecked(edit_data.get("is_playable", True))

    def get_data(self) -> dict:
        """Return the dialog data as a dict."""
        return {
            "code": self.code_input.text().strip(),
            "name": self.name_input.text().strip(),
            "is_playable": self.playable_cb.isChecked(),
        }


# ── Skill Dialog (shared by Super / Ultimate / Awoken / Evasive) ────

class SkillDialog(QDialog):
    """Add / edit a Skill record (any skill type)."""

    def __init__(
        self,
        skill_type_label: str,
        parent: Optional[QWidget] = None,
        *,
        edit_data: Optional[dict] = None,
    ) -> None:
        super().__init__(parent)
        self._is_edit = edit_data is not None
        self._type_label = skill_type_label
        self.setWindowTitle(
            tr("dialog.skill.edit_title", type=skill_type_label)
            if self._is_edit
            else tr("dialog.skill.add_title", type=skill_type_label)
        )
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_input = QLineEdit()
        form.addRow(QLabel(tr("dialog.skill.label_name")), self.name_input)

        self.cac_cb = QCheckBox()
        form.addRow(QLabel(tr("dialog.skill.label_cac")), self.cac_cb)

        self.note_input = QLineEdit()
        self.note_input.setPlaceholderText(tr("dialog.skill.placeholder_note"))
        form.addRow(QLabel(tr("dialog.skill.label_note")), self.note_input)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if edit_data:
            self.name_input.setText(edit_data.get("name", ""))
            self.cac_cb.setChecked(edit_data.get("is_cac", False))
            self.note_input.setText(edit_data.get("note", ""))

    def get_data(self) -> dict:
        return {
            "name": self.name_input.text().strip(),
            "is_cac": self.cac_cb.isChecked(),
            "note": self.note_input.text().strip(),
        }


# ── Super Soul Dialog ────────────────────────────────────────────────

class SuperSoulDialog(QDialog):
    """Add / edit a Super Soul record."""

    def __init__(self, parent: Optional[QWidget] = None, *, edit_data: Optional[dict] = None) -> None:
        super().__init__(parent)
        self._is_edit = edit_data is not None
        self.setWindowTitle(
            tr("dialog.super_soul.edit_title") if self._is_edit else tr("dialog.super_soul.add_title")
        )
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_input = QLineEdit()
        form.addRow(QLabel(tr("dialog.super_soul.label_name")), self.name_input)

        self.effect1_input = QLineEdit()
        form.addRow(QLabel(tr("dialog.super_soul.label_effect1")), self.effect1_input)

        self.effect2_input = QLineEdit()
        form.addRow(QLabel(tr("dialog.super_soul.label_effect2")), self.effect2_input)

        self.note_input = QLineEdit()
        form.addRow(QLabel(tr("dialog.super_soul.label_note")), self.note_input)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if edit_data:
            self.name_input.setText(edit_data.get("name", ""))
            self.effect1_input.setText(edit_data.get("effect1", ""))
            self.effect2_input.setText(edit_data.get("effect2", ""))
            self.note_input.setText(edit_data.get("note", ""))

    def get_data(self) -> dict:
        return {
            "name": self.name_input.text().strip(),
            "effect1": self.effect1_input.text().strip(),
            "effect2": self.effect2_input.text().strip(),
            "note": self.note_input.text().strip(),
        }
