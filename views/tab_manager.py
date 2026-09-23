"""
DBXV2 Build Forge — Tab Manager.

Manages the central ``QTabWidget``, housing:
1. Skillset Editor tab
2. Roster Table Preview tab
3. Character DB tab
4. Super Skill DB tab
5. Ultimate Skill DB tab
6. Awoken Skill DB tab
7. Evasive Skill DB tab
8. Super Soul DB tab

Provides programmatic tab switching and live i18n label updating (PRD §2.1, §3.8).
"""

from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtGui import QUndoStack
from PySide6.QtWidgets import QTabWidget, QWidget

from controllers.signal_bus import signal_bus
from locales.i18n_manager import tr
from models.data_store import AppDataStore
from views.database_tab import DatabaseTab
from views.editor_tab import EditorTab
from views.roster_tab import RosterTab

logger = logging.getLogger(__name__)


class TabManager(QTabWidget):
    """Central tab container for DBXV2 Build Forge."""

    TAB_INDEX_EDITOR = 0
    TAB_INDEX_ROSTER = 1

    def __init__(self, data_store: AppDataStore, undo_stack: QUndoStack, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._store = data_store
        self._undo_stack = undo_stack
        
        # UI Setup for TabBar
        self.tabBar().setExpanding(True)
        self.tabBar().setDocumentMode(True)

        # 1. Editor Tab
        self.editor_tab = EditorTab(data_store, undo_stack, self)
        self.addTab(self.editor_tab, tr("tabs.editor"))

        # 2. Roster Preview Tab
        self.roster_tab = RosterTab(data_store, undo_stack, self)
        self.addTab(self.roster_tab, tr("tabs.roster_preview"))

        # 3–8. Database Manager Tabs
        self.db_tabs: dict[str, DatabaseTab] = {}
        db_categories = [
            ("characters", "character"),
            ("super_skills", "super_skill"),
            ("ultimate_skills", "ultimate_skill"),
            ("awoken_skills", "awoken_skill"),
            ("evasive_skills", "evasive_skill"),
            ("super_souls", "super_soul"),
        ]
        for key, locale_key in db_categories:
            display_title = tr(f"tabs.{locale_key}")
            tab = DatabaseTab(key, display_title, data_store, undo_stack, self)
            self.db_tabs[key] = tab
            self.addTab(tab, display_title)

        self._connect_signals()

    def _connect_signals(self) -> None:
        # When "Load into Editor" is triggered from SheetDetailDialog, switch to Editor tab
        signal_bus.load_entry_to_editor.connect(self._on_load_entry)

    def _on_load_entry(self, entry, sheet_name: str) -> None:
        self.setCurrentIndex(self.TAB_INDEX_EDITOR)
        self.editor_tab.load_entry(entry, sheet_name)

    def retranslate_ui(self) -> None:
        """Update all tab header labels and child tabs when the application language changes."""
        self.setTabText(self.TAB_INDEX_EDITOR, tr("tabs.editor"))
        self.editor_tab.retranslate_ui()

        self.setTabText(self.TAB_INDEX_ROSTER, tr("tabs.roster_preview"))
        self.roster_tab.retranslate_ui()

        db_categories = [
            ("characters", "character"),
            ("super_skills", "super_skill"),
            ("ultimate_skills", "ultimate_skill"),
            ("awoken_skills", "awoken_skill"),
            ("evasive_skills", "evasive_skill"),
            ("super_souls", "super_soul"),
        ]
        for i, (key, locale_key) in enumerate(db_categories, start=2):
            display_title = tr(f"tabs.{locale_key}")
            self.setTabText(i, display_title)
            if key in self.db_tabs:
                self.db_tabs[key].retranslate_ui(display_title)
