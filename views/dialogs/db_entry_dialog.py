from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QCompleter,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from locales.i18n_manager import tr


SKILL_TYPES_BY_CATEGORY: dict[str, list[str]] = {
    "super_skills": ["strike", "ki_blast", "buff", "other", "strike_raid", "ki_blast_raid"],
    "ultimate_skills": ["strike", "ki_blast", "buff", "other", "strike_raid", "ki_blast_raid"],
    "evasive_skills": ["strike", "ki_blast", "buff", "other", "strike_raid", "ki_blast_raid"],
    "awoken_skills": ["transformation"],
}


class CharacterDialog(QDialog):

    def __init__(
        self,
        episodes_provider=None,
        parent: Optional[QWidget] = None,
        *,
        edit_data: Optional[dict] = None,
    ) -> None:
        super().__init__(parent)
        self._is_edit = edit_data is not None
        self._episodes_provider = episodes_provider
        self._original_name = edit_data.get("name", "") if edit_data else ""
        self._original_base = edit_data.get("base_character", "") if edit_data else ""

        self._base_manually_edited = False
        self._last_auto_base = ""

        self.setWindowTitle(
            tr("dialog.character.edit_title") if self._is_edit else tr("dialog.character.add_title")
        )
        self.setMinimumWidth(480)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(tr("dialog.character.placeholder_name"))
        form.addRow(QLabel(tr("dialog.character.label_name")), self.name_input)

        self.base_input = QLineEdit()
        self.base_input.setPlaceholderText(tr("dialog.character.placeholder_base"))
        form.addRow(QLabel(tr("dialog.character.label_base")), self.base_input)

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText(tr("dialog.character.placeholder_code"))
        form.addRow(QLabel(tr("dialog.character.label_code")), self.code_input)

        self.playable_cb = QCheckBox()
        self.playable_cb.setChecked(True)
        form.addRow(QLabel(tr("dialog.character.label_playable")), self.playable_cb)

        episodes_label = QLabel(tr("dialog.character.label_episodes"))
        form.addRow(episodes_label)

        episodes_container = QWidget()
        episodes_layout = QVBoxLayout(episodes_container)
        episodes_layout.setContentsMargins(0, 0, 0, 0)
        episodes_layout.setSpacing(6)

        self.episodes_list = QListWidget()
        self.episodes_list.setMinimumHeight(80)
        episodes_layout.addWidget(self.episodes_list)

        add_row = QHBoxLayout()
        add_row.setSpacing(6)

        self.episodes_combo = QComboBox()
        self.episodes_combo.setEditable(True)
        self.episodes_combo.setInsertPolicy(QComboBox.NoInsert)
        completer = QCompleter(self.episodes_combo.model(), self.episodes_combo)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setMaxVisibleItems(15)
        self.episodes_combo.setCompleter(completer)
        add_row.addWidget(self.episodes_combo, 1)

        add_btn = QPushButton(tr("dialog.character.button_add_episode"))
        add_btn.clicked.connect(self._on_add_episode)
        add_row.addWidget(add_btn)

        remove_btn = QPushButton(tr("dialog.character.button_remove_episode"))
        remove_btn.clicked.connect(self._on_remove_episode)
        add_row.addWidget(remove_btn)

        episodes_layout.addLayout(add_row)
        form.addRow(episodes_container)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._populate_episodes_combo()

        if edit_data:
            self.name_input.setText(edit_data.get("name", ""))
            base_val = edit_data.get("base_character", "")
            self.base_input.setText(base_val)
            self.code_input.setText(edit_data.get("code", ""))
            self.playable_cb.setChecked(edit_data.get("is_playable", True))
            for ep in edit_data.get("episodes", []):
                self.episodes_list.addItem(ep)

            # Detect if stored base was manually edited (different from derived)
            derived = self._original_name.split("(")[0].strip() if self._original_name else ""
            if base_val.strip() and base_val.strip() != derived:
                self._base_manually_edited = True

        self.name_input.textChanged.connect(self._on_name_changed)
        self.base_input.textEdited.connect(self._on_base_edited)

        # Initial sync
        self._last_auto_base = ""
        self._sync_base_from_name()

    def _populate_episodes_combo(self) -> None:
        if self._episodes_provider is None:
            return
        try:
            eps = self._episodes_provider()
        except Exception:
            eps = []
        names = sorted([e.get("name", "") for e in eps if e.get("name")])
        self.episodes_combo.addItems(names)

    def _on_name_changed(self, new_name: str) -> None:
        self._sync_base_from_name()

    def _on_base_edited(self, text: str) -> None:
        if not text.strip():
            self._base_manually_edited = False
            return

        if text.strip() != self._last_auto_base:
            self._base_manually_edited = True

    def _sync_base_from_name(self) -> None:
        new_name = self.name_input.text().strip()
        new_derived = new_name.split("(")[0].strip() if new_name else ""
        self._last_auto_base = new_derived

        if self._base_manually_edited:
            return

        if self.base_input.text() != new_derived:
            self.base_input.setText(new_derived)

    def _on_add_episode(self) -> None:
        text = self.episodes_combo.currentText().strip()
        if not text:
            return
        existing = [self.episodes_list.item(i).text() for i in range(self.episodes_list.count())]
        if text in existing:
            return
        self.episodes_list.addItem(text)
        self.episodes_combo.setCurrentText("")

    def _on_remove_episode(self) -> None:
        for item in self.episodes_list.selectedItems():
            self.episodes_list.takeItem(self.episodes_list.row(item))

    def get_data(self) -> dict:
        episodes = [
            self.episodes_list.item(i).text()
            for i in range(self.episodes_list.count())
        ]
        return {
            "code": self.code_input.text().strip(),
            "name": self.name_input.text().strip(),
            "is_playable": self.playable_cb.isChecked(),
            "base_character": self.base_input.text().strip(),
            "episodes": episodes,
        }

class SkillDialog(QDialog):

    KI_USED_NONE = -1

    def __init__(
        self,
        category_key: str,
        display_label: str,
        parent: Optional[QWidget] = None,
        *,
        edit_data: Optional[dict] = None,
    ) -> None:
        super().__init__(parent)
        self._is_edit = edit_data is not None
        self._category_key = category_key
        self._display_label = display_label
        self._skill_types = SKILL_TYPES_BY_CATEGORY.get(category_key, [])

        self.setWindowTitle(
            tr("dialog.skill.edit_title", type=display_label)
            if self._is_edit
            else tr("dialog.skill.add_title", type=display_label)
        )
        self.setMinimumWidth(440)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_input = QLineEdit()
        form.addRow(QLabel(tr("dialog.skill.label_name")), self.name_input)

        self.type_combo: Optional[QComboBox] = None
        if self._skill_types:
            self.type_combo = QComboBox()
            self.type_combo.addItem(tr("dialog.skill.type.none"), "")
            for code in self._skill_types:
                self.type_combo.addItem(tr(f"dialog.skill.type.{code}"), code)
            form.addRow(QLabel(tr("dialog.skill.label_skill_type")), self.type_combo)

        self.ki_used_spin = QSpinBox()
        self.ki_used_spin.setMinimum(self.KI_USED_NONE)
        self.ki_used_spin.setMaximum(9999)
        self.ki_used_spin.setSpecialValueText("—")
        form.addRow(QLabel(tr("dialog.skill.label_ki_used")), self.ki_used_spin)

        self.cac_cb = QCheckBox()
        form.addRow(QLabel(tr("dialog.skill.label_cac")), self.cac_cb)

        self.description_input = QPlainTextEdit()
        self.description_input.setPlaceholderText(tr("dialog.skill.placeholder_description"))
        self.description_input.setMinimumHeight(80)
        form.addRow(QLabel(tr("dialog.skill.label_description")), self.description_input)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if edit_data:
            self.name_input.setText(edit_data.get("name", ""))
            self.cac_cb.setChecked(edit_data.get("is_cac", False))

            ki = edit_data.get("ki_used")
            if ki is None:
                self.ki_used_spin.setValue(self.KI_USED_NONE)
            else:
                try:
                    self.ki_used_spin.setValue(int(ki))
                except (ValueError, TypeError):
                    self.ki_used_spin.setValue(self.KI_USED_NONE)

            if self.type_combo is not None:
                current_type = edit_data.get("skill_type", "")
                idx = self.type_combo.findData(current_type)
                if idx >= 0:
                    self.type_combo.setCurrentIndex(idx)

            self.description_input.setPlainText(edit_data.get("note", ""))

    def get_data(self) -> dict:
        ki = self.ki_used_spin.value()
        ki_used = None if ki == self.KI_USED_NONE else ki

        skill_type = ""
        if self.type_combo is not None:
            skill_type = self.type_combo.currentData() or ""

        return {
            "name": self.name_input.text().strip(),
            "is_cac": self.cac_cb.isChecked(),
            "skill_type": skill_type,
            "ki_used": ki_used,
            "note": self.description_input.toPlainText().strip(),
        }


class SuperSoulDialog(QDialog):

    def __init__(
        self,
        characters_provider,
        parent: Optional[QWidget] = None,
        *,
        edit_data: Optional[dict] = None,
    ) -> None:
        super().__init__(parent)
        self._is_edit = edit_data is not None
        self._characters_provider = characters_provider

        self.setWindowTitle(
            tr("dialog.super_soul.edit_title") if self._is_edit else tr("dialog.super_soul.add_title")
        )
        self.setMinimumWidth(480)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_input = QLineEdit()
        form.addRow(QLabel(tr("dialog.super_soul.label_name")), self.name_input)

        self.owner_combo = QComboBox()
        self.owner_combo.setEditable(True)
        self.owner_combo.setInsertPolicy(QComboBox.NoInsert)
        self.owner_combo.setPlaceholderText(tr("dialog.super_soul.placeholder_owner"))
        completer = QCompleter(self.owner_combo.model(), self.owner_combo)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setMaxVisibleItems(15)
        self.owner_combo.setCompleter(completer)
        self._populate_owners()
        form.addRow(QLabel(tr("dialog.super_soul.label_owner")), self.owner_combo)

        self.effect1_input = QPlainTextEdit()
        self.effect1_input.setMinimumHeight(60)
        form.addRow(QLabel(tr("dialog.super_soul.label_effect1")), self.effect1_input)

        self.effect2_input = QPlainTextEdit()
        self.effect2_input.setMinimumHeight(60)
        form.addRow(QLabel(tr("dialog.super_soul.label_effect2")), self.effect2_input)

        self.limit_burst_input = QPlainTextEdit()
        self.limit_burst_input.setMinimumHeight(60)
        form.addRow(QLabel(tr("dialog.super_soul.label_limit_burst")), self.limit_burst_input)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if edit_data:
            self.name_input.setText(edit_data.get("name", ""))
            self.owner_combo.setCurrentText(edit_data.get("owner", ""))
            self.effect1_input.setPlainText(edit_data.get("effect_1", ""))
            self.effect2_input.setPlainText(edit_data.get("effect_2", ""))
            self.limit_burst_input.setPlainText(edit_data.get("limit_burst", ""))

    def _populate_owners(self) -> None:
        try:
            chars = self._characters_provider()
        except Exception:
            chars = []
        names = [c.get("name", "") for c in chars if c.get("name")]
        self.owner_combo.addItems(sorted(names))

    def get_data(self) -> dict:
        return {
            "name": self.name_input.text().strip(),
            "owner": self.owner_combo.currentText().strip(),
            "effect_1": self.effect1_input.toPlainText().strip(),
            "effect_2": self.effect2_input.toPlainText().strip(),
            "limit_burst": self.limit_burst_input.toPlainText().strip(),
        }

SOURCE_TYPE_CODES: list[str] = [
    "series",
    "manga",
    "movie",
    "game",
    "fan_made",
    "ova_special",
    "live_action",
    "unknown",
]


class SourceDialog(QDialog):

    def __init__(self, parent: Optional[QWidget] = None, *, edit_data: Optional[dict] = None) -> None:
        super().__init__(parent)
        self._is_edit = edit_data is not None
        self.setWindowTitle(
            tr("dialog.source.edit_title") if self._is_edit else tr("dialog.source.add_title")
        )
        self.setMinimumWidth(440)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_input = QLineEdit()
        form.addRow(QLabel(tr("dialog.source.label_name")), self.name_input)

        self.type_combo = QComboBox()
        self.type_combo.addItem("—", "")
        for code in SOURCE_TYPE_CODES:
            self.type_combo.addItem(tr(f"dialog.source.type.{code}"), code)
        form.addRow(QLabel(tr("dialog.source.label_type")), self.type_combo)

        date_widget = QWidget()
        date_layout = QHBoxLayout(date_widget)
        date_layout.setContentsMargins(0, 0, 0, 0)
        date_layout.setSpacing(8)

        self.year_spin = QSpinBox()
        self.year_spin.setMinimum(0)
        self.year_spin.setMaximum(9999)
        self.year_spin.setSpecialValueText("—")
        date_layout.addWidget(QLabel(tr("dialog.source.label_year")))
        date_layout.addWidget(self.year_spin, 1)

        self.month_combo = QComboBox()
        self.month_combo.addItem("—", 0)
        for i in range(1, 13):
            self.month_combo.addItem(tr(f"date.month.{i}"), i)
        date_layout.addWidget(QLabel(tr("dialog.source.label_month")))
        date_layout.addWidget(self.month_combo, 2)

        self.day_spin = QSpinBox()
        self.day_spin.setMinimum(0)
        self.day_spin.setMaximum(31)
        self.day_spin.setSpecialValueText("—")
        date_layout.addWidget(QLabel(tr("dialog.source.label_day")))
        date_layout.addWidget(self.day_spin, 1)

        form.addRow(QLabel(tr("dialog.source.label_date")), date_widget)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.year_spin.valueChanged.connect(self._update_date_state)
        self.month_combo.currentIndexChanged.connect(self._update_date_state)

        if edit_data:
            self.name_input.setText(edit_data.get("name", ""))
            t = edit_data.get("source_type", "")
            idx = self.type_combo.findData(t)
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)

            if edit_data.get("year") is not None:
                self.year_spin.setValue(int(edit_data["year"]))
            if edit_data.get("month") is not None:
                midx = self.month_combo.findData(int(edit_data["month"]))
                if midx >= 0:
                    self.month_combo.setCurrentIndex(midx)
            if edit_data.get("day") is not None:
                self.day_spin.setValue(int(edit_data["day"]))

        self._update_date_state()

    def _update_date_state(self) -> None:
        year = self.year_spin.value()
        has_year = year > 0

        self.month_combo.setEnabled(has_year)
        if not has_year:
            self.month_combo.setCurrentIndex(0)

        has_month = (self.month_combo.currentData() or 0) > 0
        self.day_spin.setEnabled(has_year and has_month)
        if not has_month:
            self.day_spin.setValue(0)

    def get_data(self) -> dict:
        year = self.year_spin.value() or None
        month = self.month_combo.currentData() or None
        day = self.day_spin.value() or None

        if year is None:
            month = None
            day = None
        if month is None:
            day = None

        return {
            "name": self.name_input.text().strip(),
            "source_type": self.type_combo.currentData() or "",
            "day": day,
            "month": month,
            "year": year,
        }