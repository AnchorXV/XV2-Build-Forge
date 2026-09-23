"""
DBXV2 Build Forge — Editor Controller.

Handles business logic for the Skillset Editor:
- Validating preset entries
- Saving new entries or updating existing entries in the data store
- Character ID auto-lookup
"""

from __future__ import annotations

import logging
from typing import Optional

from controllers.signal_bus import signal_bus
from models.data_store import AppDataStore
from models.schemas import PresetEntry
from models.validators import validate_preset_entry

logger = logging.getLogger(__name__)


class EditorController:
    """Controller for the Skillset Editor tab."""

    def __init__(self, data_store: AppDataStore) -> None:
        self._store = data_store

    def save_new_entry(self, sheet_name: str, entry: PresetEntry) -> tuple[bool, list[str]]:
        """Validate and add a new preset entry to *sheet_name*.

        Returns:
            Tuple of (success_flag, error_list).
        """
        errors = validate_preset_entry(entry)
        if errors:
            return False, errors

        self._store.add_preset_entry(sheet_name, entry)
        signal_bus.data_changed.emit()
        return True, []

    def update_entry(self, sheet_name: str, entry: PresetEntry) -> tuple[bool, list[str]]:
        """Validate and update an existing preset entry in *sheet_name*.

        Returns:
            Tuple of (success_flag, error_list).
        """
        errors = validate_preset_entry(entry)
        if errors:
            return False, errors

        found = self._store.update_preset_entry(sheet_name, entry)
        signal_bus.data_changed.emit()
        return found, []

    def lookup_character_id(self, character_name: str) -> Optional[str]:
        """Find the code/ID for a given character name from the database cache."""
        for char in self._store.get_cache("characters"):
            if char.get("name", "") == character_name:
                return char.get("code", "")
        return None
