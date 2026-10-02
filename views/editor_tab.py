from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QUndoStack
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from controllers.signal_bus import signal_bus
from controllers.undo_commands import AddPresetWithAutoRegisterCommand, EditPresetEntryCommand
from locales.i18n_manager import tr
from models.data_store import AppDataStore
from models.schemas import PresetEntry
from models.validators import validate_preset_entry
from views.widgets.section_header import SectionHeader

logger = logging.getLogger(__name__)


class EditorTab(QWidget):

    def __init__(self, data_store: AppDataStore, undo_stack: QUndoStack, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._store = data_store
        self._undo_stack = undo_stack
        self._editing_entry_id: Optional[str] = None
        self._editing_source_sheet: Optional[str] = None

        self._super_labels: list[QLabel] = []
        self._ult_labels: list[QLabel] = []

        self._build_ui()
        self._connect_signals()
        self._refresh_combos()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        scroll.setObjectName("editorScroll")

        container = QWidget()
        container.setMaximumWidth(980)
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(28, 20, 28, 28)
        main_layout.setSpacing(6)

        # ── Section 1: Character & Costume ────────────────────────────
        main_layout.addWidget(SectionHeader(tr("editor.group.character_info")))

        grp_char = QWidget()
        g1 = QGridLayout(grp_char)
        g1.setContentsMargins(0, 4, 0, 20)
        g1.setHorizontalSpacing(14)
        g1.setVerticalSpacing(10)
        g1.setColumnStretch(0, 0)
        g1.setColumnStretch(1, 1)
        g1.setColumnStretch(2, 0)
        g1.setColumnStretch(3, 1)

        lbl_char_name = QLabel(tr("editor.label.character_name"))
        self.char_name_combo = QComboBox()
        self.char_name_combo.setEditable(True)
        g1.addWidget(lbl_char_name, 0, 0)
        g1.addWidget(self.char_name_combo, 0, 1, 1, 3)

        lbl_char_id = QLabel(tr("editor.label.character_id"))
        self.char_id_input = QComboBox()
        self.char_id_input.setEditable(True)
        lbl_costume_name = QLabel(tr("editor.label.costume_name"))
        self.costume_name_input = QLineEdit()
        g1.addWidget(lbl_char_id, 1, 0)
        g1.addWidget(self.char_id_input, 1, 1)
        g1.addWidget(lbl_costume_name, 1, 2)
        g1.addWidget(self.costume_name_input, 1, 3)

        lbl_costume_idx = QLabel(tr("editor.label.costume_index"))
        self.costume_index_spin = QSpinBox()
        self.costume_index_spin.setMinimum(0)
        self.costume_index_spin.setMaximum(99)
        lbl_model_preset = QLabel(tr("editor.label.model_preset"))
        self.model_preset_input = QLineEdit()
        g1.addWidget(lbl_costume_idx, 2, 0)
        g1.addWidget(self.costume_index_spin, 2, 1)
        g1.addWidget(lbl_model_preset, 2, 2)
        g1.addWidget(self.model_preset_input, 2, 3)

        main_layout.addWidget(grp_char)

        # ── Section 2: Skillset ───────────────────────────────────────
        main_layout.addWidget(SectionHeader(tr("editor.group.skillset_matrix")))

        grp_skills = QWidget()
        g2 = QGridLayout(grp_skills)
        g2.setContentsMargins(0, 4, 0, 20)
        g2.setHorizontalSpacing(14)
        g2.setVerticalSpacing(10)
        g2.setColumnStretch(0, 0)
        g2.setColumnStretch(1, 1)
        g2.setColumnStretch(2, 0)
        g2.setColumnStretch(3, 1)

        self.super_combos: list[QComboBox] = []
        for i in range(4):
            label = QLabel(tr("editor.label.super_skill", n=i + 1))
            combo = QComboBox()
            combo.setEditable(True)
            self._super_labels.append(label)
            self.super_combos.append(combo)
            g2.addWidget(label, i, 0)
            g2.addWidget(combo, i, 1)

        self.ult_combos: list[QComboBox] = []
        for i in range(2):
            label = QLabel(tr("editor.label.ultimate_skill", n=i + 1))
            combo = QComboBox()
            combo.setEditable(True)
            self._ult_labels.append(label)
            self.ult_combos.append(combo)
            g2.addWidget(label, i, 2)
            g2.addWidget(combo, i, 3)

        self.awoken_combo = QComboBox()
        self.awoken_combo.setEditable(True)
        g2.addWidget(QLabel(tr("editor.label.awoken_skill")), 2, 2)
        g2.addWidget(self.awoken_combo, 2, 3)

        self.evasive_combo = QComboBox()
        self.evasive_combo.setEditable(True)
        g2.addWidget(QLabel(tr("editor.label.evasive_skill")), 3, 2)
        g2.addWidget(self.evasive_combo, 3, 3)

        self.super_soul_combo = QComboBox()
        self.super_soul_combo.setEditable(True)
        g2.addWidget(QLabel(tr("editor.label.super_soul")), 4, 0)
        g2.addWidget(self.super_soul_combo, 4, 1, 1, 3)

        main_layout.addWidget(grp_skills)

        # ── Section 3: Save ──────────────────────────────────────────
        main_layout.addWidget(SectionHeader(tr("editor.group.save_target")))

        grp_save = QWidget()
        g3 = QVBoxLayout(grp_save)
        g3.setContentsMargins(0, 4, 0, 0)
        g3.setSpacing(14)

        target_row = QHBoxLayout()
        target_row.setSpacing(14)
        lbl_target = QLabel(tr("editor.label.target_sheet"))
        lbl_target.setMinimumWidth(110)
        target_row.addWidget(lbl_target)
        self.target_sheet_combo = QComboBox()
        self.target_sheet_combo.setEditable(True)
        self.target_sheet_combo.setPlaceholderText(tr("editor.placeholder.target_sheet"))
        target_row.addWidget(self.target_sheet_combo, 1)
        g3.addLayout(target_row)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()

        self.reset_btn = QPushButton(tr("editor.button.reset"))
        self.reset_btn.setObjectName("resetButton")
        self.reset_btn.setMinimumWidth(100)
        btn_row.addWidget(self.reset_btn)

        self.save_btn = QPushButton(tr("editor.button.save"))
        self.save_btn.setObjectName("saveButton")
        self.save_btn.setMinimumWidth(120)
        btn_row.addWidget(self.save_btn)

        g3.addLayout(btn_row)
        main_layout.addWidget(grp_save)

        main_layout.addStretch()
        scroll.setWidget(container)
        root.addWidget(scroll)

    def _connect_signals(self) -> None:
        self.reset_btn.clicked.connect(self.reset_form)
        self.save_btn.clicked.connect(self._on_save)

        self.char_name_combo.currentTextChanged.connect(self._on_char_name_changed)

        signal_bus.data_changed.connect(self._refresh_combos)

    def reset_form(self) -> None:
        self.char_name_combo.setCurrentIndex(-1)
        self.char_name_combo.clearEditText()
        self.char_id_input.setCurrentIndex(-1)
        self.char_id_input.clearEditText()
        self.costume_name_input.clear()
        self.costume_index_spin.setValue(0)
        self.model_preset_input.clear()

        for combo in self.super_combos + self.ult_combos:
            combo.setCurrentIndex(-1)
            combo.clearEditText()
        self.awoken_combo.setCurrentIndex(-1)
        self.awoken_combo.clearEditText()
        self.evasive_combo.setCurrentIndex(-1)
        self.evasive_combo.clearEditText()
        self.super_soul_combo.setCurrentIndex(-1)
        self.super_soul_combo.clearEditText()

        self.target_sheet_combo.clearEditText()
        self._editing_entry_id = None
        self._editing_source_sheet = None

    def load_entry(self, entry: PresetEntry, sheet_name: str) -> None:
        self.char_name_combo.setCurrentText(entry.character_name)
        self.char_id_input.setCurrentText(entry.character_id)
        self.costume_name_input.setText(entry.costume_name)
        self.costume_index_spin.setValue(entry.costume_index)
        self.model_preset_input.setText(str(entry.model_preset))

        for i, combo in enumerate(self.super_combos):
            combo.setCurrentText(entry.super_skills[i] if i < len(entry.super_skills) else "")
        for i, combo in enumerate(self.ult_combos):
            combo.setCurrentText(entry.ultimate_skills[i] if i < len(entry.ultimate_skills) else "")

        self.awoken_combo.setCurrentText(entry.awoken_skill)
        self.evasive_combo.setCurrentText(entry.evasive_skill)
        self.super_soul_combo.setCurrentText(entry.super_soul)
        self.target_sheet_combo.setCurrentText(sheet_name)

        self._editing_entry_id = entry.entry_id
        self._editing_source_sheet = sheet_name

    def _collect_entry(self) -> PresetEntry:
        return PresetEntry(
            character_name=self.char_name_combo.currentText().strip(),
            character_id=self.char_id_input.currentText().strip(),
            costume_name=self.costume_name_input.text().strip(),
            costume_index=self.costume_index_spin.value(),
            model_preset=self.model_preset_input.text().strip(),
            super_skills=[c.currentText().strip() for c in self.super_combos],
            ultimate_skills=[c.currentText().strip() for c in self.ult_combos],
            awoken_skill=self.awoken_combo.currentText().strip(),
            evasive_skill=self.evasive_combo.currentText().strip(),
            super_soul=self.super_soul_combo.currentText().strip(),
        )

    def _on_char_name_changed(self, name: str) -> None:
        base_name = name.split("(")[0].strip()
        if base_name and not self.target_sheet_combo.currentText():
            self.target_sheet_combo.setCurrentText(base_name)

        code = self._store.get_character_code(name)
        if code:
            self.char_id_input.setCurrentText(code)

    def _on_save(self) -> None:
        target = self.target_sheet_combo.currentText().strip()
        if not target:
            QMessageBox.warning(self, tr("editor.message.validation_failed"), tr("editor.message.empty_target"))
            return

        entry = self._collect_entry()
        errors = validate_preset_entry(entry)
        if errors:
            QMessageBox.warning(self, tr("editor.message.validation_failed"), "\n".join(errors))
            return

        if self._editing_entry_id:
            self._save_update(target, entry)
        else:
            self._save_new(target, entry)

    def _save_new(self, target: str, entry: PresetEntry) -> None:
        cmd = AddPresetWithAutoRegisterCommand(self._store, target, entry)
        self._undo_stack.push(cmd)
        QMessageBox.information(
            self,
            tr("editor.message.save_success_title"),
            tr("editor.message.save_success", sheet=target),
        )

    def _save_update(self, target: str, entry: PresetEntry) -> None:
        if self._editing_source_sheet and self._editing_source_sheet != target:
            reply = QMessageBox.question(
                self,
                tr("editor.message.validation_failed"),
                tr(
                    "editor.message.target_changed",
                    default=(
                        f"Entry asli ada di sheet '{self._editing_source_sheet}', "
                        f"tapi target sekarang '{target}'.\n\n"
                        "Pilih 'Yes' untuk tetap update di sheet asal,\n"
                        "'No' untuk membatalkan dan reset form."
                    ),
                    old_sheet=self._editing_source_sheet,
                    new_sheet=target,
                ),
            )
            if reply != QMessageBox.Yes:
                return
            target = self._editing_source_sheet
            self.target_sheet_combo.setCurrentText(target)

        entry.entry_id = self._editing_entry_id
        old_entry = None
        for p in self._store.rosters.get(target, []):
            if p.entry_id == self._editing_entry_id:
                old_entry = p
                break

        if old_entry is None:
            QMessageBox.warning(
                self,
                tr("editor.message.validation_failed"),
                tr(
                    "editor.message.entry_not_found",
                    default=(
                        "Entry yang ingin di-update tidak ditemukan di sheet ini.\n\n"
                        "Kemungkinan sudah dihapus dari sheet lain. "
                        "Form akan di-reset. Klik 'Save as New' untuk menyimpan sebagai entry baru."
                    ),
                ),
            )
            self.reset_form()
            return

        cmd = EditPresetEntryCommand(self._store, target, old_entry, entry)
        self._undo_stack.push(cmd)
        QMessageBox.information(
            self,
            tr("editor.message.save_success_title"),
            tr("editor.message.update_success", sheet=target),
        )
        self._editing_entry_id = None
        self._editing_source_sheet = None

    def _refresh_combos(self) -> None:
        chars = self._store.get_cache("characters")
        self._refill_combo(self.char_name_combo, [c.get("name", "") for c in chars])

        codes = list(dict.fromkeys(c.get("code", "") for c in chars if c.get("code")))
        if "MOD" not in codes:
            codes.append("MOD")
        self._refill_combo(self.char_id_input, codes)

        supers = self._store.get_cache("super_skills")
        ults = self._store.get_cache("ultimate_skills")
        awokens = self._store.get_cache("awoken_skills")
        evasives = self._store.get_cache("evasive_skills")
        super_souls = self._store.get_cache("super_souls")

        for combo in self.super_combos:
            self._refill_combo(combo, [s.get("name", "") for s in supers])
        for combo in self.ult_combos:
            self._refill_combo(combo, [s.get("name", "") for s in ults])
        self._refill_combo(self.awoken_combo, [s.get("name", "") for s in awokens])
        self._refill_combo(self.evasive_combo, [s.get("name", "") for s in evasives])
        self._refill_combo(self.super_soul_combo, [s.get("name", "") for s in super_souls])

        sheets = list(self._store.get_all_sheets().keys())
        self._refill_combo(self.target_sheet_combo, sheets)

    @staticmethod
    def _refill_combo(combo: QComboBox, items: list[str]) -> None:
        current = combo.currentText()
        combo.blockSignals(True)
        combo.clear()
        combo.addItems(items)
        combo.setCurrentText(current)
        combo.blockSignals(False)