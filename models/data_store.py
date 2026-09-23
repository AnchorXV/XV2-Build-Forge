"""
DBXV2 Build Forge — Application Data Store.

Single source of truth for all in-memory state (rosters, dropdown caches, settings).
All mutations go through methods here so the persistence layer can be
notified uniformly.  Views never hold their own copy of the data.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional, Union

from app_config import CACHE_KEYS, DATA_FILE
from models.persistence import AtomicJsonPersistence
from models.schemas import CharacterEntry, PresetEntry

logger = logging.getLogger(__name__)


class AppDataStore:
    """Centralised mutable state container.

    Attributes:
        rosters: Ordered dict of sheet-name → list[PresetEntry].
        dropdown_cache: Dict of cache-key → list[dict[str, Any]].
        settings: Dict of app settings (language, theme).
    """

    def __init__(
        self,
        persistence: Optional[AtomicJsonPersistence] = None,
        data_file: Optional[Union[str, Path]] = None,
    ) -> None:
        self.data_file = Path(data_file or DATA_FILE)
        self._persistence = persistence or AtomicJsonPersistence(self.data_file)
        self.rosters: dict[str, list[PresetEntry]] = {}
        self.sheets_meta: dict[str, dict[str, Any]] = {}
        self.dropdown_cache: dict[str, list[Any]] = {k: [] for k in CACHE_KEYS}
        self.settings: dict[str, Any] = {"language": "en", "theme": "light"}

        self.load()

    # ── Persistence ────────────────────────────────────────────────────

    def load(self, path: Optional[Union[str, Path]] = None) -> None:
        """Hydrate store from the JSON data file."""
        target = Path(path or self.data_file)
        raw = self._persistence.load(target)
        if not raw:
            return

        # Restore settings
        if "settings" in raw and isinstance(raw["settings"], dict):
            self.settings.update(raw["settings"])

        # Restore dropdown caches
        migration_happened = False
        for key in CACHE_KEYS:
            if key in raw and isinstance(raw[key], list):
                migrated_list = []
                for item in raw[key]:
                    if isinstance(item, str):
                        # Migrate old simple string lists to dictionary schema
                        if key == "characters":
                            migrated_list.append({"Code": "MOD", "Name": item, "Playable Character": "Yes"})
                            migration_happened = True
                        elif key == "super_souls":
                            migrated_list.append({"Super Soul": item, "Effect 1": "", "Effect 2": "", "Note": ""})
                            migration_happened = True
                        elif key in ("super_skills", "ultimate_skills", "awoken_skills", "evasive_skills"):
                            migrated_list.append({"Skill Name": item, "Is CaC Skill?": "No", "Note": ""})
                            migration_happened = True
                        else:
                            migrated_list.append(item)
                    else:
                        migrated_list.append(item)
                self.dropdown_cache[key] = migrated_list

        # Restore rosters
        self.rosters.clear()
        raw_rosters = raw.get("rosters", {})
        if isinstance(raw_rosters, dict):
            for sheet_name, preset_list in raw_rosters.items():
                if isinstance(preset_list, list):
                    self.rosters[sheet_name] = [
                        PresetEntry.from_dict(p) if isinstance(p, dict) else p
                        for p in preset_list
                    ]

        # Restore sheets meta
        self.sheets_meta.clear()
        raw_meta = raw.get("sheets_meta", {})
        if isinstance(raw_meta, dict):
            for sheet_name, meta in raw_meta.items():
                if isinstance(meta, dict):
                    self.sheets_meta[sheet_name] = meta

        logger.info(
            "Loaded %d sheets from data store (file: %s).",
            len(self.rosters),
            target,
        )

    def save(self, path: Optional[Union[str, Path]] = None) -> None:
        """Persist entire store to the JSON data file."""
        target = Path(path or self.data_file)
        payload: dict[str, Any] = dict(self.dropdown_cache)
        payload["settings"] = self.settings
        payload["rosters"] = {
            name: [p.to_dict() for p in presets]
            for name, presets in self.rosters.items()
        }
        payload["sheets_meta"] = self.sheets_meta
        self._persistence.save(target, payload)

    # ── Roster Sheet Operations ────────────────────────────────────────

    def get_all_sheets(self) -> dict[str, list[PresetEntry]]:
        """Return dict of all roster sheets and their entries."""
        return self.rosters

    def get_recent_sheets(self) -> list[str]:
        """Return the list of up to 5 recently opened sheets."""
        return self.settings.get("recent_sheets", [])

    def add_recent_sheet(self, sheet_name: str) -> None:
        """Add a sheet to the recent sheets list."""
        if sheet_name not in self.rosters:
            return
        recents = self.get_recent_sheets()
        if sheet_name in recents:
            recents.remove(sheet_name)
        recents.insert(0, sheet_name)
        self.settings["recent_sheets"] = recents[:5]
        self.save()

    def get_sheet_entries(self, sheet_name: str) -> list[PresetEntry]:
        """Return the list of PresetEntry objects for a given sheet."""
        return self.rosters.get(sheet_name, [])

    def create_sheet(self, name: str) -> bool:
        """Create a new empty roster sheet. Returns False if already exists."""
        if name in self.rosters:
            return False
        self.rosters[name] = []
        self.sheets_meta[name] = {"note": "", "tags": []}
        if name not in self.dropdown_cache["table_names"]:
            self.dropdown_cache["table_names"].append(name)
        self.save()
        return True

    def rename_sheet(self, old_name: str, new_name: str) -> bool:
        """Rename a sheet. Returns False on conflict or if old_name doesn't exist."""
        if old_name not in self.rosters or new_name in self.rosters:
            return False
        self.rosters[new_name] = self.rosters.pop(old_name)
        if old_name in self.sheets_meta:
            self.sheets_meta[new_name] = self.sheets_meta.pop(old_name)
        tnames = self.dropdown_cache["table_names"]
        if old_name in tnames:
            tnames[tnames.index(old_name)] = new_name
        self.save()
        return True

    def delete_sheet(self, name: str) -> bool:
        """Delete a sheet and its presets. Returns False if not found."""
        if name not in self.rosters:
            return False
        del self.rosters[name]
        self.sheets_meta.pop(name, None)
        tnames = self.dropdown_cache["table_names"]
        if name in tnames:
            tnames.remove(name)
        self.save()
        return True

    def add_preset_entry(self, sheet_name: str, entry: PresetEntry) -> None:
        """Append a preset to the given sheet (creates sheet if needed)."""
        if sheet_name not in self.rosters:
            self.rosters[sheet_name] = []
            self.sheets_meta[sheet_name] = {"note": "", "tags": []}
            if sheet_name not in self.dropdown_cache["table_names"]:
                self.dropdown_cache["table_names"].append(sheet_name)
        self.rosters[sheet_name].append(entry)
        self.save()

    def update_preset_entry(self, sheet_name: str, updated: PresetEntry) -> bool:
        """Update an existing preset entry in-place by its ``entry_id``."""
        presets = self.rosters.get(sheet_name, [])
        for idx, p in enumerate(presets):
            if p.entry_id == updated.entry_id:
                presets[idx] = updated
                self.save()
                return True

        # If not found by entry_id, append as new entry
        self.add_preset_entry(sheet_name, updated)
        return False

    def get_sheet_meta(self, sheet_name: str) -> dict[str, Any]:
        """Return the metadata for a sheet (note, tags, etc)."""
        return self.sheets_meta.get(sheet_name, {"note": "", "tags": []})

    def update_sheet_meta(self, sheet_name: str, note: str, tags: list[str]) -> None:
        """Update the note and tags for a sheet."""
        if sheet_name not in self.sheets_meta:
            self.sheets_meta[sheet_name] = {}
        self.sheets_meta[sheet_name]["note"] = note
        self.sheets_meta[sheet_name]["tags"] = tags
        self.save()

    # ── Database Cache Operations ──────────────────────────────────────

    def get_cache(self, category: str) -> list[dict[str, Any]]:
        """Return all items for a given category."""
        return self.dropdown_cache.get(category, [])

    def add_to_cache(self, category: str, item: dict[str, Any]) -> None:
        """Append an item to a database cache category."""
        if category not in self.dropdown_cache:
            self.dropdown_cache[category] = []
        self.dropdown_cache[category].append(item)
        self.save()

    def update_cache_item(self, category: str, index: int, item: dict[str, Any]) -> None:
        """Update an item at index in a database cache category."""
        items = self.dropdown_cache.get(category, [])
        if 0 <= index < len(items):
            items[index] = item
            self.save()

    def remove_from_cache(self, category: str, index: int) -> None:
        """Remove an item at index from a database cache category."""
        items = self.dropdown_cache.get(category, [])
        if 0 <= index < len(items):
            items.pop(index)
            self.save()

    def force_migrate_cache(self, key: str) -> bool:
        """Force a migration pass on a specific cache category to convert legacy string items to dictionaries. Returns True if any migration occurred."""
        items = self.dropdown_cache.get(key, [])
        if not items:
            return False
            
        migrated_list = []
        migration_happened = False
        for item in items:
            if isinstance(item, str):
                if key == "characters":
                    migrated_list.append({"Code": "MOD", "Name": item, "Playable Character": "Yes"})
                    migration_happened = True
                elif key == "super_souls":
                    migrated_list.append({"Super Soul": item, "Effect 1": "", "Effect 2": "", "Note": ""})
                    migration_happened = True
                elif key in ("super_skills", "ultimate_skills", "awoken_skills", "evasive_skills"):
                    migrated_list.append({"Skill Name": item, "Is CaC Skill?": "No", "Note": ""})
                    migration_happened = True
                else:
                    migrated_list.append(item)
            else:
                migrated_list.append(item)
                
        if migration_happened:
            self.dropdown_cache[key] = migrated_list
            self.save()
            return True
        return False
