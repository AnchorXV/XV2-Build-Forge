from __future__ import annotations
from typing import Optional
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)
from locales.i18n_manager import tr
from views.widgets.searchable_combo import setup_searchable_combo

class MergeDialog(QDialog):

    def __init__(
        self,
        category_display: str,
        source_name: str,
        target_candidates: list[str],
        impact_count: int,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._source = source_name
        self._impact_count = impact_count
        self._selected_target = ""

        self.setWindowTitle(tr("dialog.merge.title", type=category_display))
        self.setMinimumWidth(440)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        source_label = QLabel(source_name)
        source_label.setObjectName("mergeSourceLabel")
        form.addRow(QLabel(tr("dialog.merge.source")), source_label)

        self._target_combo = QComboBox()
        setup_searchable_combo(self._target_combo)

        for name in target_candidates:
            self._target_combo.addItem(name)

        form.addRow(QLabel(tr("dialog.merge.target")), self._target_combo)
        layout.addLayout(form)

        self._preview = QLabel()
        self._preview.setObjectName("mergePreviewLabel")
        self._preview.setWordWrap(True)
        layout.addWidget(self._preview)

        self._buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self._buttons.button(QDialogButtonBox.Ok).setText(tr("dialog.merge.merge_button"))
        self._buttons.accepted.connect(self._on_accept)
        self._buttons.rejected.connect(self.reject)
        layout.addWidget(self._buttons)

        self._target_combo.currentTextChanged.connect(self._update_preview)
        if target_candidates:
            self._target_combo.setCurrentIndex(0)
        self._update_preview()

    def _update_preview(self, _text: str = "") -> None:
        target = self._target_combo.currentText().strip()
        ok_btn = self._buttons.button(QDialogButtonBox.Ok)

        if not target or target == self._source:
            self._preview.setText(tr("dialog.merge.invalid_target"))
            ok_btn.setEnabled(False)
            return

        if self._impact_count == 0:
            self._preview.setText(
                tr("dialog.merge.no_impact", source=self._source)
            )
        else:
            self._preview.setText(
                tr(
                    "dialog.merge.impact",
                    count=self._impact_count,
                    source=self._source,
                    target=target,
                )
            )
        ok_btn.setEnabled(True)

    def _on_accept(self) -> None:
        self._selected_target = self._target_combo.currentText().strip()
        self.accept()

    def selected_target(self) -> str:
        return self._selected_target