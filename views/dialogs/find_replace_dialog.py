from __future__ import annotations

from typing import Optional

from PySide6.QtGui import QUndoStack
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from controllers.signal_bus import signal_bus
from controllers.undo_commands import EditPresetEntryCommand
from locales.i18n_manager import tr
from models.data_store import AppDataStore
from models.find_replace import (
    FIELD_KEYS,
    FIELD_LABELS,
    count_matches,
    find_replace_changes,
)


class FindReplaceDialog(QDialog):

    def __init__(
        self,
        data_store: AppDataStore,
        undo_stack: QUndoStack,
        current_sheet: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._store = data_store
        self._undo_stack = undo_stack
        self._current_sheet = current_sheet

        self.setWindowTitle(tr("dialog.find_replace.title", default="Find & Replace"))
        self.setMinimumWidth(520)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._field_combo = QComboBox()
        self._field_combo.addItem(
            tr("dialog.find_replace.all_fields", default="All text fields"),
            "all",
        )
        for key in FIELD_KEYS:
            label = FIELD_LABELS.get(key, key)
            self._field_combo.addItem(label, key)
        form.addRow(
            QLabel(tr("dialog.find_replace.field_label", default="Field:")),
            self._field_combo,
        )

        scope_widget = QWidget()
        scope_layout = QVBoxLayout(scope_widget)
        scope_layout.setContentsMargins(0, 0, 0, 0)
        scope_layout.setSpacing(4)

        self._scope_current_rb = QRadioButton()
        self._scope_all_rb = QRadioButton(
            tr("dialog.find_replace.scope_all", default="All sheets")
        )

        if current_sheet is not None:
            self._scope_current_rb.setText(
                tr("dialog.find_replace.scope_current", default="Current sheet: ") + current_sheet
            )
            self._scope_current_rb.setChecked(True)
            self._scope_all_rb.setChecked(False)
        else:
            self._scope_current_rb.setText(
                tr("dialog.find_replace.scope_current_none", default="Current sheet (none selected)")
            )
            self._scope_current_rb.setEnabled(False)
            self._scope_all_rb.setChecked(True)

        scope_layout.addWidget(self._scope_current_rb)
        scope_layout.addWidget(self._scope_all_rb)
        form.addRow(
            QLabel(tr("dialog.find_replace.scope_label", default="Scope:")),
            scope_widget,
        )

        self._find_input = QLineEdit()
        self._find_input.setPlaceholderText(
            tr("dialog.find_replace.find_placeholder", default="Text to find")
        )
        form.addRow(
            QLabel(tr("dialog.find_replace.find_label", default="Find:")),
            self._find_input,
        )

        self._replace_input = QLineEdit()
        self._replace_input.setPlaceholderText(
            tr("dialog.find_replace.replace_placeholder", default="Replacement text")
        )
        form.addRow(
            QLabel(tr("dialog.find_replace.replace_label", default="Replace:")),
            self._replace_input,
        )

        layout.addLayout(form)

        self._case_cb = QCheckBox(
            tr("dialog.find_replace.case_sensitive", default="Case sensitive")
        )
        layout.addWidget(self._case_cb)

        self._preview_label = QLabel()
        self._preview_label.setObjectName("previewLabel")
        self._preview_label.setWordWrap(True)
        layout.addWidget(self._preview_label)

        buttons = QDialogButtonBox()
        self._replace_btn = buttons.addButton(
            tr("dialog.find_replace.replace_all", default="Replace All"),
            QDialogButtonBox.AcceptRole,
        )
        self._replace_btn.setObjectName("saveButton")
        buttons.addButton(QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_replace_all)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._find_input.textChanged.connect(self._update_preview)
        self._field_combo.currentIndexChanged.connect(self._update_preview)
        self._scope_current_rb.toggled.connect(self._update_preview)
        self._case_cb.toggled.connect(self._update_preview)

        self._update_preview()

    def _scope_presets(self) -> list:
        if self._scope_current_rb.isChecked() and self._current_sheet:
            return self._store.get_sheet_entries(self._current_sheet)
        result = []
        for sheet_name in self._store.get_all_sheets().keys():
            result.extend(self._store.get_sheet_entries(sheet_name))
        return result

    def _selected_field_keys(self) -> list[str]:
        key = self._field_combo.currentData()
        return [key] if key else ["all"]

    def _update_preview(self, *_args) -> None:
        find_text = self._find_input.text()
        if not find_text:
            self._preview_label.setText("")
            self._replace_btn.setEnabled(False)
            return

        presets = self._scope_presets()
        field_keys = self._selected_field_keys()
        case_sensitive = self._case_cb.isChecked()

        matches = count_matches(presets, find_text, field_keys, case_sensitive)
        if matches == 0:
            self._preview_label.setText(
                tr("dialog.find_replace.no_matches", default="No matches found.")
            )
            self._replace_btn.setEnabled(False)
        else:
            self._preview_label.setText(
                tr(
                    "dialog.find_replace.preview",
                    default=f"{matches} match(es) will be replaced.",
                    count=matches,
                )
            )
            self._replace_btn.setEnabled(True)

    def _on_replace_all(self) -> None:
        find_text = self._find_input.text()
        replace_text = self._replace_input.text()
        if not find_text:
            return
        if find_text == replace_text:
            QMessageBox.information(
                self,
                tr("dialog.common.warning", default="Warning"),
                tr(
                    "dialog.find_replace.same_text",
                    default="Find and Replace are identical. Nothing to do.",
                ),
            )
            return

        scope_all = self._scope_all_rb.isChecked()
        field_keys = self._selected_field_keys()
        case_sensitive = self._case_cb.isChecked()

        total_changes = 0

        if scope_all:
            self._undo_stack.beginMacro(f"Find & Replace: '{find_text}' → '{replace_text}' (all sheets)")
            for sheet_name in list(self._store.get_all_sheets().keys()):
                presets = self._store.get_sheet_entries(sheet_name)
                changes = find_replace_changes(
                    presets, find_text, replace_text, field_keys, case_sensitive
                )
                for old_entry, new_entry in changes:
                    cmd = EditPresetEntryCommand(self._store, sheet_name, old_entry, new_entry)
                    self._undo_stack.push(cmd)
                    total_changes += 1
            self._undo_stack.endMacro()
        else:
            if not self._current_sheet:
                return
            presets = self._store.get_sheet_entries(self._current_sheet)
            changes = find_replace_changes(
                presets, find_text, replace_text, field_keys, case_sensitive
            )
            if changes:
                self._undo_stack.beginMacro(
                    f"Find & Replace: '{find_text}' → '{replace_text}' in '{self._current_sheet}'"
                )
                for old_entry, new_entry in changes:
                    cmd = EditPresetEntryCommand(self._store, self._current_sheet, old_entry, new_entry)
                    self._undo_stack.push(cmd)
                    total_changes += 1
                self._undo_stack.endMacro()

        if total_changes == 0:
            QMessageBox.information(
                self,
                tr("dialog.common.warning", default="Warning"),
                tr("dialog.find_replace.no_matches", default="No matches found."),
            )
            return

        signal_bus.data_changed.emit()
        self.accept()