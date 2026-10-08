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
from views.widgets.command_palette import CommandPalette

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

        self._palette = CommandPalette(self)
        self._palette.action_selected.connect(self._on_palette_action)

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

        self._act_palette = QAction(tr("menu.edit.command_palette", default="Command Palette"), self)
        self._act_palette.setShortcut("Ctrl+P")
        self._act_palette.triggered.connect(self._open_command_palette)
        self._menu_edit.addSeparator()
        self._menu_edit.addAction(self._act_palette)

        self._menu_help = menubar.addMenu(tr("menu.about.title", default="About"))
        self._act_about = QAction(tr("menu.about.title", default="About"), self)
        self._act_about.triggered.connect(self._show_about_dialog)
        self._menu_help.addAction(self._act_about)

    def _open_command_palette(self) -> None:
        commands = self._build_commands()
        self._palette.register_commands(commands)
        self._palette.open_palette()

    def _build_commands(self) -> list[dict]:
        commands: list[dict] = []

        for sheet_name in self._store.get_all_sheets().keys():
            count = len(self._store.get_sheet_entries(sheet_name))
            commands.append({
                "label": f"▸  Open Roster: {sheet_name}  ({count})",
                "search": f"roster sheet {sheet_name}",
                "action": "open_sheet",
                "data": {"sheet": sheet_name},
            })

        for char in self._store.get_cache("characters"):
            name = char.get("name", "")
            if not name:
                continue
            commands.append({
                "label": f"⌕  Find Character: {name}",
                "search": f"character db {name}",
                "action": "find_character",
                "data": {"name": name},
            })

        commands.append({
            "label": "+  New Sheet",
            "search": "new sheet create",
            "action": "new_sheet",
            "data": {},
        })
        commands.append({
            "label": "↓  Save / Backup",
            "search": "save backup",
            "action": "save",
            "data": {},
        })

        return commands

    def _on_palette_action(self, action: str, data: dict) -> None:
        if action == "open_sheet":
            sheet_name = data.get("sheet")
            if sheet_name:
                self.page_manager.set_current_page(PageManager.PAGE_ROSTER)
                self.page_manager.roster_tab.select_sheet_by_name(sheet_name)
        elif action == "find_character":
            self.page_manager.set_current_page(PageManager.PAGE_DATABASE)
            name = data.get("name", "")
            self.page_manager.database_page.focus_search(name)
        elif action == "new_sheet":
            self._on_new_sheet()
        elif action == "save":
            self._on_save()

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
        self.page_manager.roster_tab.select_sheet_by_name(sheet_name)

    def _on_new_sheet(self) -> None:
        self.page_manager.set_current_page(PageManager.PAGE_ROSTER)
        self.page_manager.roster_tab._on_add_sheet()

    def _on_save(self) -> None:
        self._store.save()
        self._store._persistence.backup()
        self.statusBar().showMessage(tr("status.saved"), 3000)

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
                tr("dialog.common.warning"),
                tr("status.error_saving_before_exit", error=exc),
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()