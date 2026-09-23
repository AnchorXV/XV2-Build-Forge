"""
DBXV2 Build Forge — Application Controller.

Top-level coordinator:
1. Loads persistence data and initialises ``AppDataStore``.
2. Sets up language and theme before UI display.
3. Instantiates sub-controllers.
4. Creates and displays ``MainWindow``.
"""

from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QUndoStack

from app_config import DATA_FILE_PATH
from controllers.database_controller import DatabaseController
from controllers.editor_controller import EditorController
from controllers.export_controller import ExportController
from controllers.roster_controller import RosterController
from controllers.settings_controller import SettingsController
from locales.i18n_manager import init as init_i18n
from models.data_store import AppDataStore
from models.persistence import AtomicJsonPersistence
from styles.theme_manager import ThemeMode, apply_theme, resolve_theme_mode
from views.main_window import MainWindow

logger = logging.getLogger(__name__)


class AppController:
    """Master application controller."""

    def __init__(self, app: QApplication, data_file=DATA_FILE_PATH) -> None:
        self.app = app
        self.data_file = data_file

        # 1. Model & Persistence
        self.persistence = AtomicJsonPersistence(self.data_file)
        self.data_store = AppDataStore(self.persistence)

        # 2. i18n
        saved_lang = self.data_store.settings.get("language", "en")
        init_i18n(saved_lang)

        # 3. Theme (Permanent Dark Theme)
        self.theme_mode = ThemeMode.DARK
        apply_theme(self.app, self.theme_mode)

        # 4. Sub-controllers
        self.editor_ctrl = EditorController(self.data_store)
        self.roster_ctrl = RosterController(self.data_store)
        self.db_ctrl = DatabaseController(self.data_store)
        self.export_ctrl = ExportController()
        self.settings_ctrl = SettingsController(self.data_store)
        self.undo_stack = QUndoStack()

        # 5. Auto-backup
        self.backup_timer = QTimer(self.app)
        self.backup_timer.timeout.connect(self.persistence.backup)
        self.backup_timer.start(10 * 60 * 1000)  # 10 minutes
        self.app.aboutToQuit.connect(self.persistence.backup)

        # 6. View
        self.main_window: Optional[MainWindow] = None

    def start(self) -> None:
        """Create and display the main window."""
        self.main_window = MainWindow(self.data_store, self.undo_stack)
        self.main_window.show()
        logger.info("Application started successfully.")
