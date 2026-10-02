from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtCore import QTimer
from PySide6.QtGui import QUndoStack
from PySide6.QtWidgets import QApplication

from app_config import DATA_FILE_PATH
from controllers.export_controller import ExportController
from locales.i18n_manager import init as init_i18n
from models.data_store import AppDataStore
from models.persistence import AtomicJsonPersistence
from styles.theme_manager import ThemeMode, apply_theme, resolve_theme_mode
from views.main_window import MainWindow

logger = logging.getLogger(__name__)


class AppController:

    def __init__(self, app: QApplication, data_file=DATA_FILE_PATH) -> None:
        self.app = app
        self.data_file = data_file

        self.persistence = AtomicJsonPersistence(self.data_file)
        self.data_store = AppDataStore(self.persistence)

        saved_lang = self.data_store.settings.get("language", "en")
        init_i18n(saved_lang)

        saved_theme = self.data_store.settings.get("theme", "dark")
        self.theme_mode = resolve_theme_mode(saved_theme)
        apply_theme(self.app, self.theme_mode)

        self.export_ctrl = ExportController()
        self.undo_stack = QUndoStack()

        self.backup_timer = QTimer(self.app)
        self.backup_timer.timeout.connect(self.persistence.backup)
        self.backup_timer.start(10 * 60 * 1000)
        self.app.aboutToQuit.connect(self._on_about_to_quit)

        self.main_window: Optional[MainWindow] = None

    def _on_about_to_quit(self) -> None:
        self.backup_timer.stop()
        self.persistence.backup()

    def start(self) -> None:
        self.main_window = MainWindow(self.data_store, self.undo_stack)
        self.main_window.show()
        logger.info("Application started successfully.")