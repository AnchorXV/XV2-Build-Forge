from __future__ import annotations

from typing import Optional

from PySide6.QtGui import QUndoStack
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from controllers.undo_commands import BulkEditCommand
from locales.i18n_manager import tr
from models.data_store import AppDataStore
from models.schemas import PresetEntry


class BulkEditDialog(QDialog):

    def __init__(
        self,
        sheet_name: str,
        selected_entries: list[PresetEntry],
        data_store: AppDataStore,
        undo_stack: QUndoStack,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._sheet_name = sheet_name
        self._entries = selected_entries
        self._store = data_store
        self._undo_stack = undo_stack

        self._fields = {
            "super_soul": tr("editor.label.super_soul"),
            "awoken_skill": tr("editor.label.awoken_skill"),
            "evasive_skill": tr("editor.label.evasive_skill"),
            "costume_index": tr("editor.label.costume_index"),
            "model_preset": tr("editor.label.model_preset"),
        }
        self._field_keys = list(self._fields.keys())

        self.setWindowTitle(tr("dialog.bulk_edit.menu_title", count=len(selected_entries)))
        self.setMinimumWidth(400)

        self._build_ui()
        self._on_field_changed(0)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        info = QLabel(tr("dialog.bulk_edit.info", count=len(self._entries)))
        if info.text() == "dialog.bulk_edit.info":
            info.setText(f"Editing {len(self._entries)} selected presets.")
        layout.addWidget(info)

        form = QFormLayout()

        self.field_combo = QComboBox()
        for key in self._field_keys:
            self.field_combo.addItem(self._fields[key])
        self.field_combo.currentIndexChanged.connect(self._on_field_changed)
        form.addRow(tr("dialog.bulk_edit.field_to_edit", default="Field to Edit:"), self.field_combo)

        self.input_stack = QStackedWidget()

        self.val_combo = QComboBox()
        self.val_combo.setEditable(True)
        self.input_stack.addWidget(self.val_combo)

        self.val_spin = QSpinBox()
        self.val_spin.setMinimum(0)
        self.val_spin.setMaximum(9999)
        self.input_stack.addWidget(self.val_spin)

        form.addRow(tr("dialog.bulk_edit.new_value", default="New Value:"), self.input_stack)
        layout.addLayout(form)

        self.preview_lbl = QLabel()
        self.preview_lbl.setWordWrap(True)
        self.preview_lbl.setStyleSheet("color: #888; font-style: italic;")
        layout.addWidget(self.preview_lbl)

        self.val_combo.currentTextChanged.connect(self._update_preview)
        self.val_spin.valueChanged.connect(self._update_preview)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = QPushButton(tr("dialog.common.cancel", default="Cancel"))
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.apply_btn = QPushButton(tr("dialog.common.apply", default="Apply"))
        self.apply_btn.setObjectName("saveButton")
        self.apply_btn.clicked.connect(self._on_apply)
        btn_layout.addWidget(self.apply_btn)

        layout.addLayout(btn_layout)

    def _on_field_changed(self, index: int) -> None:
        field = self._field_keys[index]

        if field in ["costume_index", "model_preset"]:
            self.input_stack.setCurrentWidget(self.val_spin)
            self.val_spin.setValue(0)
        else:
            self.input_stack.setCurrentWidget(self.val_combo)
            self.val_combo.clear()
            if field == "super_soul":
                items = [s.get("name", "") for s in self._store.get_cache("super_souls")]
            elif field == "awoken_skill":
                items = [s.get("name", "") for s in self._store.get_cache("awoken_skills")]
            elif field == "evasive_skill":
                items = [s.get("name", "") for s in self._store.get_cache("evasive_skills")]
            else:
                items = []
            self.val_combo.addItems(items)
            self.val_combo.setCurrentText("")

        self._update_preview()

    def _update_preview(self, *args) -> None:
        if self.input_stack.currentWidget() == self.val_spin:
            new_val = str(self.val_spin.value())
        else:
            new_val = self.val_combo.currentText()

        text = tr("dialog.bulk_edit.preview", default=f"{len(self._entries)} presets will be updated to '{new_val}'.")
        self.preview_lbl.setText(text)

    def _on_apply(self) -> None:
        field = self._field_keys[self.field_combo.currentIndex()]
        if self.input_stack.currentWidget() == self.val_spin:
            new_val = str(self.val_spin.value())
        else:
            new_val = self.val_combo.currentText().strip()

        reply = QMessageBox.question(
            self,
            tr("dialog.common.confirm", default="Confirm"),
            tr("dialog.bulk_edit.confirm_apply", default=f"Apply changes to {len(self._entries)} presets?")
        )
        if reply != QMessageBox.Yes:
            return

        old_values = {}
        entry_ids = []
        for entry in self._entries:
            entry_ids.append(entry.entry_id)
            old_values[entry.entry_id] = str(BulkEditCommand.get_field_value(entry, field))

        cmd = BulkEditCommand(
            self._store,
            self._sheet_name,
            entry_ids,
            field,
            new_val,
            old_values
        )
        self._undo_stack.push(cmd)

        if field == "super_soul" and new_val:
            souls = self._store.dropdown_cache.get("super_souls", [])
            if not any(s.get("name") == new_val for s in souls):
                souls.append({
                    "name": new_val,
                    "owner": "",
                    "effect_1": "",
                    "effect_2": "",
                    "limit_burst": "",
                })
                self._store.save()
        elif field in ["awoken_skill", "evasive_skill"] and new_val:
            cat = "awoken_skills" if field == "awoken_skill" else "evasive_skills"
            skills = self._store.dropdown_cache.get(cat, [])
            if not any(s.get("name") == new_val for s in skills):
                skills.append({
                    "name": new_val,
                    "is_cac": False,
                    "skill_type": "",
                    "ki_used": None,
                    "note": "",
                })
                self._store.save()

        self.accept()