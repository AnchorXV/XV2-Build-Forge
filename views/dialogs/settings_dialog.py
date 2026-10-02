from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Signal
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


_LANGUAGE_OPTIONS = [
    ("English", "en"),
    ("Bahasa Indonesia", "id"),
    ("日本語", "ja"),
]

_THEME_OPTIONS = [
    ("light", "light"),
    ("dark", "dark"),
    ("system", "system"),
]


class SettingsDialog(QDialog):

    language_changed = Signal(str)
    theme_changed = Signal(str)

    def __init__(
        self,
        current_lang: str,
        current_theme: str = "dark",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("dialog.settings.title", default="Settings"))
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._lang_combo = QComboBox()
        current_lang_idx = 0
        for idx, (display, code) in enumerate(_LANGUAGE_OPTIONS):
            self._lang_combo.addItem(display, code)
            if code == current_lang:
                current_lang_idx = idx
        self._lang_combo.setCurrentIndex(current_lang_idx)
        form.addRow(
            QLabel(tr("menu.settings.language", default="Language:")),
            self._lang_combo,
        )

        self._theme_combo = QComboBox()
        current_theme_idx = 0
        for idx, (display_key, value) in enumerate(_THEME_OPTIONS):
            display_text = tr(
                f"dialog.settings.theme_{display_key}",
                default=display_key.title(),
            )
            self._theme_combo.addItem(display_text, value)
            if value == current_theme:
                current_theme_idx = idx
        self._theme_combo.setCurrentIndex(current_theme_idx)
        form.addRow(
            QLabel(tr("menu.settings.theme", default="Theme:")),
            self._theme_combo,
        )

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self) -> None:
        self.language_changed.emit(self._lang_combo.currentData())
        self.theme_changed.emit(self._theme_combo.currentData())
        self.accept()