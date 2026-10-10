from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from locales.i18n_manager import tr


class ColumnSelectDialog(QDialog):

    def __init__(
        self,
        all_columns: list[str],
        default_checked: Optional[list[str]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("dialog.export.columns_title"))
        self.setMinimumWidth(360)
        self.setMinimumHeight(440)

        if default_checked is None:
            default_checked = list(all_columns)
        checked_set = set(default_checked)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        info = QLabel(tr("dialog.export.columns_info"))
        info.setWordWrap(True)
        layout.addWidget(info)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        container = QWidget()
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(4, 4, 4, 4)
        c_layout.setSpacing(4)

        self._checkboxes: dict[str, QCheckBox] = {}
        for col in all_columns:
            cb = QCheckBox(col)
            cb.setChecked(col in checked_set)
            self._checkboxes[col] = cb
            c_layout.addWidget(cb)

        c_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

        btn_row = QHBoxLayout()
        select_all_btn = QPushButton(tr("dialog.export.select_all"))
        select_all_btn.clicked.connect(self._select_all)
        btn_row.addWidget(select_all_btn)

        deselect_all_btn = QPushButton(tr("dialog.export.deselect_all"))
        deselect_all_btn.clicked.connect(self._deselect_all)
        btn_row.addWidget(deselect_all_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _select_all(self) -> None:
        for cb in self._checkboxes.values():
            cb.setChecked(True)

    def _deselect_all(self) -> None:
        for cb in self._checkboxes.values():
            cb.setChecked(False)

    def _on_accept(self) -> None:
        if not self.selected_columns():
            return
        self.accept()

    def selected_columns(self) -> list[str]:
        return [col for col, cb in self._checkboxes.items() if cb.isChecked()]