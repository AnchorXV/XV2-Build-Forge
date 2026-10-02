from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtGui import QAction, QCloseEvent, QUndoStack
from PySide6.QtWidgets import (
    QMainWindow,
    QMessageBox,
    QWidget,
)

from app_config import APP_NAME, APP_VERSION
from locales.i18n_manager import tr
from models.data_store import AppDataStore
from views.page_manager import PageManager

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):

    def __init__(self, data_store: AppDataStore, undo_stack: QUndoStack, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._store = data_store
        self._undo_stack = undo_stack

        self.setWindowTitle(f"{tr('app.title', default=APP_NAME)} v{APP_VERSION}")
        self.setMinimumSize(1050, 720)
        self.resize(1150, 780)

        self.page_manager = PageManager(data_store, self._undo_stack, self)
        self.setCentralWidget(self.page_manager)

        self._build_menu_bar()

    def _build_menu_bar(self) -> None:
        menubar = self.menuBar()
        menubar.clear()

        self._menu_file = menubar.addMenu(tr("menu.file.title", default="File"))

        self._act_new_sheet = QAction(tr("menu.file.new_sheet", default="New Sheet"), self)
        self._act_new_sheet.setShortcut("Ctrl+N")
        self._act_new_sheet.triggered.connect(self._on_new_sheet)
        self._menu_file.addAction(self._act_new_sheet)

        self._act_save = QAction(tr("menu.file.save", default="Save / Backup"), self)
        self._act_save.setShortcut("Ctrl+S")
        self._act_save.triggered.connect(self._on_save)
        self._menu_file.addAction(self._act_save)

        self._menu_recent = self._menu_file.addMenu(
            tr("menu.file.recent_sheets", default="Recent Sheets")
        )
        self._menu_recent.aboutToShow.connect(self._update_recent_menu)

        self._menu_edit = menubar.addMenu(tr("menu.edit.title", default="Edit"))
        self._act_undo = self._undo_stack.createUndoAction(self, tr("menu.edit.undo", default="Undo"))
        self._act_undo.setShortcut("Ctrl+Z")
        self._act_redo = self._undo_stack.createRedoAction(self, tr("menu.edit.redo", default="Redo"))
        self._act_redo.setShortcut("Ctrl+Y")
        self._menu_edit.addAction(self._act_undo)
        self._menu_edit.addAction(self._act_redo)

        self._menu_help = menubar.addMenu(tr("menu.about.title", default="About"))
        self._act_about = QAction(tr("menu.about.title", default="About"), self)
        self._act_about.triggered.connect(self._show_about_dialog)
        self._menu_help.addAction(self._act_about)

    def _update_recent_menu(self) -> None:
        self._menu_recent.clear()
        recent_sheets = self._store.get_recent_sheets()
        if not recent_sheets:
            act = QAction(tr("menu.file.no_recent", default="(No recent sheets)"), self)
            act.setEnabled(False)
            self._menu_recent.addAction(act)
        else:
            for sheet_name in recent_sheets:
                if sheet_name in self._store.rosters:
                    act = QAction(sheet_name, self)
                    act.triggered.connect(
                        lambda _checked=False, s=sheet_name: self._open_recent_sheet(s)
                    )
                    self._menu_recent.addAction(act)

    def _open_recent_sheet(self, sheet_name: str) -> None:
        self.page_manager.set_current_page(PageManager.PAGE_ROSTER)
        entries = self._store.get_sheet_entries(sheet_name)
        from views.dialogs.sheet_detail_dialog import SheetDetailDialog
        from models.table_models import PresetDetailTableModel
        detail_model = PresetDetailTableModel(entries)
        dlg = SheetDetailDialog(sheet_name, detail_model, self._store, self._undo_stack, self)
        dlg.load_into_editor.connect(lambda r: self.page_manager.roster_tab._load_entry(sheet_name, r))
        dlg.exec()

    def _on_new_sheet(self) -> None:
        self.page_manager.set_current_page(PageManager.PAGE_ROSTER)
        self.page_manager.roster_tab._on_add_sheet()

    def _on_save(self) -> None:
        self._store.save()
        self._store._persistence.backup()
        self.statusBar().showMessage(
            tr("status.saved", default="Data saved and backed up."),
            3000,
        )

    def _show_about_dialog(self) -> None:
        from views.dialogs.about_dialog import AboutDialog
        dlg = AboutDialog(self)
        dlg.exec()

    def closeEvent(self, event: QCloseEvent) -> None:
        logger.info("Application closing — persisting state...")
        try:
            self._store.save()
            event.accept()
        except Exception as exc:
            logger.exception("Error saving data on close: %s", exc)
            reply = QMessageBox.warning(
                self,
                tr("dialog.common.warning", default="Warning"),
                f"Error saving data before exit: {exc}\nExit anyway?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()