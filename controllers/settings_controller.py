"""
DBXV2 Build Forge — Settings Controller.

Coordinates application configuration, theme switching, and language switching.
"""

from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtWidgets import QApplication

from controllers.signal_bus import signal_bus
from locales.i18n_manager import set_language
from models.data_store import AppDataStore
from styles.theme_manager import ThemeMode, apply_theme, resolve_theme_mode

logger = logging.getLogger(__name__)


class SettingsController:
    """Controller for application preferences and settings persistence."""

    def __init__(self, data_store: AppDataStore) -> None:
        self._store = data_store

    def get_language(self) -> str:
        """Return the current configured language code."""
        return self._store.settings.get("language", "en")

    def set_language(self, lang_code: str) -> None:
        """Change the active language, persist it, and emit signal."""
        set_language(lang_code)
        self._store.settings["language"] = lang_code
        self._store.save()
        signal_bus.language_changed.emit(lang_code)

    def get_theme_mode(self) -> ThemeMode:
        """Return the current configured ThemeMode."""
        raw = self._store.settings.get("theme", "dark")
        return resolve_theme_mode(raw)

    def set_theme_mode(self, mode: ThemeMode, app: Optional[QApplication] = None) -> None:
        """Apply theme to QApplication, persist it, and emit signal."""
        if app is None:
            app = QApplication.instance()
        if app:
            apply_theme(app, mode)
        self._store.settings["theme"] = mode.value
        self._store.save()
        signal_bus.theme_changed.emit(mode)
