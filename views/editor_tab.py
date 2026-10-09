from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut, QUndoStack
from PySide6.QtWidgets import (
    QComboBox,
    QCompleter,
    QFrame,
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
from controllers.undo_commands import (
    AddPresetWithAutoRegisterCommand,
    EditPresetWithAutoRegisterCommand,
)
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
        self._editing_entry_name: Optional[str] = None

        self._build_ui()
        self._connect_signals()
        self._refresh_combos()

    # ── UI Construction ────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self._edit_banner = self._build_edit_banner()
        root.addWidget(self._edit_banner)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

        container = QWidget()
        container.setMaximumWidth(920)
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(28, 24, 28, 32)
        main_layout.setSpacing(20)

        main_layout.addWidget(SectionHeader(tr("editor.group.character_info")))
        main_layout.addWidget(self._build_char_card())

        main_layout.addWidget(SectionHeader(tr("editor.group.skillset_matrix")))
        main_layout.addWidget(self._build_skills_card())

        main_layout.addWidget(SectionHeader(tr("editor.group.save_target")))
        main_layout.addWidget(self._build_save_card())

        main_layout.addStretch()
        scroll.setWidget(container)
        root.addWidget(scroll)

    def _build_edit_banner(self) -> QFrame:
        banner = QFrame()
        banner.setObjectName("editBanner")

        layout = QHBoxLayout(banner)
        layout.setContentsMargins(20, 10, 12, 10)
        layout.setSpacing(12)

        self._banner_label = QLabel()
        self._banner_label.setObjectName("editBannerLabel")
        layout.addWidget(self._banner_label, 1)

        self._banner_cancel_btn = QPushButton("×")
        self._banner_cancel_btn.setObjectName("editBannerCancel")
        self._banner_cancel_btn.setFixedSize(26, 26)
        self._banner_cancel_btn.setCursor(Qt.PointingHandCursor)
        self._banner_cancel_btn.setToolTip(tr("editor.banner.cancel_tooltip"))
        self._banner_cancel_btn.clicked.connect(self.reset_form)
        layout.addWidget(self._banner_cancel_btn)

        banner.hide()
        return banner

    def _build_char_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("cardFrame")
        grid = QGridLayout(card)
        grid.setContentsMargins(24, 24, 24, 24)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(18)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        self.char_name_combo = QComboBox()
        self._setup_searchable_combo(self.char_name_combo)
        grid.addWidget(
            self._make_field(tr("editor.label.character_name"), self.char_name_combo),
            0, 0, 1, 2,
        )

        self.source_combo = QComboBox()
        self._setup_searchable_combo(self.source_combo)
        grid.addWidget(
            self._make_field(tr("editor.label.source"), self.source_combo),
            1, 0, 1, 2,
        )

        self.char_id_input = QComboBox()
        self._setup_searchable_combo(self.char_id_input)
        grid.addWidget(
            self._make_field(tr("editor.label.character_id"), self.char_id_input),
            2, 0,
        )

        self.costume_name_input = QLineEdit()
        grid.addWidget(
            self._make_field(tr("editor.label.costume_name"), self.costume_name_input),
            2, 1,
        )

        self.costume_index_spin = QSpinBox()
        self.costume_index_spin.setMinimum(0)
        self.costume_index_spin.setMaximum(99)
        grid.addWidget(
            self._make_field(tr("editor.label.costume_index"), self.costume_index_spin),
            3, 0,
        )

        self.model_preset_spin = QSpinBox()
        self.model_preset_spin.setMinimum(0)
        self.model_preset_spin.setMaximum(9999)
        grid.addWidget(
            self._make_field(tr("editor.label.model_preset"), self.model_preset_spin),
            3, 1,
        )

        return card

    def _build_skills_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("cardFrame")
        grid = QGridLayout(card)
        grid.setContentsMargins(24, 24, 24, 24)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(18)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        self.super_combos: list[QComboBox] = []
        for i in range(4):
            combo = QComboBox()
            self._setup_searchable_combo(combo)
            self.super_combos.append(combo)
            grid.addWidget(
                self._make_field(tr("editor.label.super_skill", n=i + 1), combo),
                i, 0,
            )

        self.ult_combos: list[QComboBox] = []
        for i in range(2):
            combo = QComboBox()
            self._setup_searchable_combo(combo)
            self.ult_combos.append(combo)
            grid.addWidget(
                self._make_field(tr("editor.label.ultimate_skill", n=i + 1), combo),
                i, 1,
            )

        self.awoken_combo = QComboBox()
        self._setup_searchable_combo(self.awoken_combo)
        grid.addWidget(
            self._make_field(tr("editor.label.awoken_skill"), self.awoken_combo),
            2, 1,
        )

        self.evasive_combo = QComboBox()
        self._setup_searchable_combo(self.evasive_combo)
        grid.addWidget(
            self._make_field(tr("editor.label.evasive_skill"), self.evasive_combo),
            3, 1,
        )

        self.super_soul_combo = QComboBox()
        self._setup_searchable_combo(self.super_soul_combo)
        grid.addWidget(
            self._make_field(tr("editor.label.super_soul"), self.super_soul_combo),
            4, 0, 1, 2,
        )

        return card

    def _build_save_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("cardFrame")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        self.target_sheet_combo = QComboBox()
        self._setup_searchable_combo(self.target_sheet_combo)
        self.target_sheet_combo.setPlaceholderText(tr("editor.placeholder.target_sheet"))
        layout.addWidget(
            self._make_field(tr("editor.label.target_sheet"), self.target_sheet_combo)
        )

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()

        self.reset_btn = QPushButton(tr("editor.button.reset"))
        self.reset_btn.setObjectName("resetButton")
        self.reset_btn.setMinimumWidth(100)
        btn_row.addWidget(self.reset_btn)

        self.save_as_new_btn = QPushButton(tr("editor.button.save_as_new"))
        self.save_as_new_btn.setObjectName("saveButton")
        self.save_as_new_btn.setMinimumWidth(140)
        btn_row.addWidget(self.save_as_new_btn)

        self.update_entry_btn = QPushButton(tr("editor.button.update_entry"))
        self.update_entry_btn.setObjectName("updateButton")
        self.update_entry_btn.setMinimumWidth(170)
        self.update_entry_btn.hide()
        btn_row.addWidget(self.update_entry_btn)

        layout.addLayout(btn_row)
        return card

    @staticmethod
    def _make_field(label_text: str, widget: QWidget) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        label = QLabel(label_text)
        label.setObjectName("fieldLabel")
        layout.addWidget(label)
        layout.addWidget(widget)

        return container

    @staticmethod
    def _setup_searchable_combo(combo: QComboBox) -> None:
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

    # ── Signal wiring ──────────────────────────────────────────────────

    def _connect_signals(self) -> None:
        self.reset_btn.clicked.connect(self.reset_form)
        self.save_as_new_btn.clicked.connect(self._on_save_as_new)
        self.update_entry_btn.clicked.connect(self._on_save_update)

        self.char_name_combo.currentTextChanged.connect(self._on_char_name_changed)

        signal_bus.data_changed.connect(self._refresh_combos)

        QShortcut(
            QKeySequence("Ctrl+Return"),
            self,
            self._on_save_default,
            context=Qt.WidgetWithChildrenShortcut,
        )
        QShortcut(
            QKeySequence("Ctrl+Enter"),
            self,
            self._on_save_default,
            context=Qt.WidgetWithChildrenShortcut,
        )

    # ── Public API ─────────────────────────────────────────────────────

    def reset_form(self) -> None:
        self.char_name_combo.setCurrentIndex(-1)
        self.char_name_combo.clearEditText()
        self.source_combo.setCurrentIndex(-1)
        self.source_combo.clearEditText()
        self.char_id_input.setCurrentIndex(-1)
        self.char_id_input.clearEditText()
        self.costume_name_input.clear()
        self.costume_index_spin.setValue(0)
        self.model_preset_spin.setValue(0)

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
        self._editing_entry_name = None
        self._update_edit_banner()

    def load_entry(self, entry: PresetEntry, sheet_name: str) -> None:
        self.char_name_combo.setCurrentText(entry.character_name)
        self.source_combo.setCurrentText(entry.source)
        self.char_id_input.setCurrentText(entry.character_id)
        self.costume_name_input.setText(entry.costume_name)
        self.costume_index_spin.setValue(entry.costume_index)

        try:
            self.model_preset_spin.setValue(int(entry.model_preset))
        except (ValueError, TypeError):
            self.model_preset_spin.setValue(0)

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
        self._editing_entry_name = entry.character_name or tr("editor.banner.unnamed")
        self._update_edit_banner()

    # ── Internal ───────────────────────────────────────────────────────

    def _collect_entry(self) -> PresetEntry:
        return PresetEntry(
            character_name=self.char_name_combo.currentText().strip(),
            source=self.source_combo.currentText().strip(),
            character_id=self.char_id_input.currentText().strip(),
            costume_name=self.costume_name_input.text().strip(),
            costume_index=self.costume_index_spin.value(),
            model_preset=str(self.model_preset_spin.value()),
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

    def _update_edit_banner(self) -> None:
        if self._editing_entry_id:
            name = self._editing_entry_name or tr("editor.banner.unnamed")
            sheet = self._editing_source_sheet or ""
            self._banner_label.setText(
                tr("editor.banner.editing", name=name, sheet=sheet)
            )
            self._edit_banner.show()
            self.update_entry_btn.show()
        else:
            self._edit_banner.hide()
            self.update_entry_btn.hide()

    def _exit_edit_mode(self) -> None:
        self._editing_entry_id = None
        self._editing_source_sheet = None
        self._editing_entry_name = None
        self._update_edit_banner()

    # ── Save handlers ──────────────────────────────────────────────────

    def _on_save_default(self) -> None:
        if self._editing_entry_id:
            self._on_save_update()
        else:
            self._on_save_as_new()

    def _on_save_as_new(self) -> None:
        target = self.target_sheet_combo.currentText().strip()
        if not target:
            QMessageBox.warning(self, tr("editor.message.validation_failed"), tr("editor.message.empty_target"))
            return

        entry = self._collect_entry()
        errors = validate_preset_entry(entry)
        if errors:
            QMessageBox.warning(self, tr("editor.message.validation_failed"), "\n".join(errors))
            return

        self._save_new(target, entry)
        self._exit_edit_mode()

    def _on_save_update(self) -> None:
        if not self._editing_entry_id:
            return

        target = self.target_sheet_combo.currentText().strip()
        if not target:
            QMessageBox.warning(self, tr("editor.message.validation_failed"), tr("editor.message.empty_target"))
            return

        entry = self._collect_entry()
        errors = validate_preset_entry(entry)
        if errors:
            QMessageBox.warning(self, tr("editor.message.validation_failed"), "\n".join(errors))
            return

        self._save_update(target, entry)
        self._update_edit_banner()

    def _save_new(self, target: str, entry: PresetEntry) -> None:
        cmd = AddPresetWithAutoRegisterCommand(self._store, target, entry)
        self._undo_stack.push(cmd)
        signal_bus.status_message.emit(
            tr("editor.message.save_success", sheet=target)
        )

    def _save_update(self, target: str, entry: PresetEntry) -> None:
        if self._editing_source_sheet and self._editing_source_sheet != target:
            reply = QMessageBox.question(
                self,
                tr("editor.message.validation_failed"),
                tr(
                    "editor.message.target_changed",
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
                tr("editor.message.entry_not_found"),
            )
            self.reset_form()
            return

        cmd = EditPresetWithAutoRegisterCommand(self._store, target, old_entry, entry)
        self._undo_stack.push(cmd)
        signal_bus.status_message.emit(
            tr("editor.message.update_success", sheet=target)
        )
        self._editing_entry_id = None
        self._editing_source_sheet = None
        self._editing_entry_name = None
        self._update_edit_banner()

    # ── Combo management ───────────────────────────────────────────────

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

        sources = self._store.get_cache("sources")
        self._refill_combo(self.source_combo, [s.get("name", "") for s in sources])

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