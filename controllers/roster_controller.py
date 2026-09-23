"""
DBXV2 Build Forge — Roster Controller.

Handles business logic for roster sheets:
- Creating new sheets
- Renaming sheets
- Deleting sheets
- Loading preset entries into the editor via signal bus
"""

from __future__ import annotations

import logging
from typing import Optional

from controllers.signal_bus import signal_bus
from models.data_store import AppDataStore
from models.schemas import PresetEntry

logger = logging.getLogger(__name__)


class RosterController:
    """Controller for the Roster Preview tab and sheet operations."""

    def __init__(self, data_store: AppDataStore) -> None:
        self._store = data_store

    def create_sheet(self, sheet_name: str) -> bool:
        """Create a new roster sheet. Returns False if duplicate or invalid."""
        name = sheet_name.strip()
        if not name or name in self._store.get_all_sheets():
            return False

        self._store.create_sheet(name)
        signal_bus.data_changed.emit()
        return True

    def rename_sheet(self, old_name: str, new_name: str) -> bool:
        """Rename an existing roster sheet. Returns False if target exists or invalid."""
        new_clean = new_name.strip()
        if not new_clean or new_clean == old_name:
            return False
        if new_clean in self._store.get_all_sheets():
            return False

        self._store.rename_sheet(old_name, new_clean)
        signal_bus.data_changed.emit()
        return True

    def delete_sheet(self, sheet_name: str) -> bool:
        """Delete a roster sheet."""
        self._store.delete_sheet(sheet_name)
        signal_bus.data_changed.emit()
        return True

    def get_sheet_entries(self, sheet_name: str) -> list[PresetEntry]:
        """Return all preset entries for a given sheet."""
        return self._store.get_sheet_entries(sheet_name)

    def load_entry_into_editor(self, entry: PresetEntry, sheet_name: str) -> None:
        """Emit signal to load *entry* into the editor tab."""
        signal_bus.load_entry_to_editor.emit(entry, sheet_name)
