"""
DBXV2 Build Forge — Settings Dialog.

Allows the user to change Language and Theme with live preview.
Emits signals so the main window can apply changes without restart
(PRD §3.7 / §3.8).
"""

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
from styles.theme_manager import ThemeMode


_LANGUAGE_OPTIONS = [
    ("English", "en"),
    ("Bahasa Indonesia", "id"),
    ("日本語", "ja"),
]


class SettingsDialog(QDialog):
    """Modal settings dialog.

    Signals:
        language_changed: Emitted with the new language code (e.g. ``"ja"``).
    """

    language_changed = Signal(str)

    def __init__(
        self,
        current_lang: str,
        current_theme: Optional[Any] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("dialog.settings.title"))
        self.setMinimumWidth(320)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Language combo
        self._lang_combo = QComboBox()
        current_lang_idx = 0
        for idx, (display, code) in enumerate(_LANGUAGE_OPTIONS):
            self._lang_combo.addItem(display, code)
            if code == current_lang:
                current_lang_idx = idx
        self._lang_combo.setCurrentIndex(current_lang_idx)
        form.addRow(QLabel(tr("menu.settings.language")), self._lang_combo)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self) -> None:
        new_lang = self._lang_combo.currentData()
        self.language_changed.emit(new_lang)
        self.accept()
