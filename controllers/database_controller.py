"""
DBXV2 Build Forge — Database Controller.

Handles business logic for the database manager tabs:
- Adding, updating, deleting items in database caches
- Fetching cached records
"""

from __future__ import annotations

import logging
from typing import Any

from controllers.signal_bus import signal_bus
from models.data_store import AppDataStore

logger = logging.getLogger(__name__)


class DatabaseController:
    """Controller for database cache operations."""

    def __init__(self, data_store: AppDataStore) -> None:
        self._store = data_store

    def get_items(self, category: str) -> list[dict[str, Any]]:
        """Return all items for a given database category."""
        return self._store.get_cache(category)

    def add_item(self, category: str, item: dict[str, Any]) -> bool:
        """Add a new item to the database cache."""
        name = item.get("name", "").strip()
        if not name:
            return False
        self._store.add_to_cache(category, item)
        signal_bus.data_changed.emit()
        return True

    def update_item(self, category: str, index: int, item: dict[str, Any]) -> bool:
        """Update an existing item at index in the database cache."""
        name = item.get("name", "").strip()
        if not name:
            return False
        self._store.update_cache_item(category, index, item)
        signal_bus.data_changed.emit()
        return True

    def delete_item(self, category: str, index: int) -> bool:
        """Delete an item at index from the database cache."""
        self._store.remove_from_cache(category, index)
        signal_bus.data_changed.emit()
        return True
