from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from locales.i18n_manager import tr
from models.backup_scanner import BackupInfo


class RestoreBackupDialog(QDialog):

    def __init__(
        self,
        backups: list[BackupInfo],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._backups = backups
        self._selected: Optional[BackupInfo] = None

        self.setWindowTitle(tr("dialog.restore.title"))
        self.setMinimumSize(560, 420)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        info_label = QLabel(tr("dialog.restore.info"))
        layout.addWidget(info_label)

        self._list = QListWidget()
        self._list.setObjectName("backupList")
        for info in backups:
            item = QListWidgetItem(info.display_label())
            item.setData(Qt.UserRole, info)
            self._list.addItem(item)
        self._list.currentRowChanged.connect(self._on_row_changed)
        layout.addWidget(self._list, 1)

        self._preview = QLabel("")
        self._preview.setObjectName("restorePreview")
        self._preview.setWordWrap(True)
        layout.addWidget(self._preview)

        self._warning = QLabel(tr("dialog.restore.warning"))
        self._warning.setObjectName("restoreWarning")
        self._warning.setWordWrap(True)
        layout.addWidget(self._warning)

        self._buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self._buttons.button(QDialogButtonBox.Ok).setText(tr("dialog.restore.restore_button"))
        self._buttons.accepted.connect(self._on_accept)
        self._buttons.rejected.connect(self.reject)
        layout.addWidget(self._buttons)

        if backups:
            self._list.setCurrentRow(0)
        else:
            self._buttons.button(QDialogButtonBox.Ok).setEnabled(False)

    def _on_row_changed(self, row: int) -> None:
        if 0 <= row < len(self._backups):
            self._selected = self._backups[row]
            self._preview.setText(self._selected.preview_text())
        else:
            self._selected = None
            self._preview.setText("")

    def _on_accept(self) -> None:
        if self._selected is None:
            return
        self.accept()

    def selected_backup(self) -> Optional[BackupInfo]:
        return self._selected