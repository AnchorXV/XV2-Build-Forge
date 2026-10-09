from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional, Union

from app_config import CACHE_KEYS, DATA_FILE
from models.persistence import AtomicJsonPersistence
from models.schemas import PresetEntry

logger = logging.getLogger(__name__)


class AppDataStore:

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
        target = Path(path or self.data_file)
        raw = self._persistence.load(target)
        if not raw:
            return

        if "settings" in raw and isinstance(raw["settings"], dict):
            self.settings.update(raw["settings"])

        for key in CACHE_KEYS:
            if key in raw and isinstance(raw[key], list):
                self.dropdown_cache[key] = [
                    self._canonicalize_cache_item(key, item) for item in raw[key]
                ]

        self.rosters.clear()
        raw_rosters = raw.get("rosters", {})
        if isinstance(raw_rosters, dict):
            for sheet_name, preset_list in raw_rosters.items():
                if isinstance(preset_list, list):
                    self.rosters[sheet_name] = [
                        PresetEntry.from_dict(p) if isinstance(p, dict) else p
                        for p in preset_list
                    ]

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
        return self.rosters

    def get_recent_sheets(self) -> list[str]:
        return self.settings.get("recent_sheets", [])

    def add_recent_sheet(self, sheet_name: str) -> None:
        if sheet_name not in self.rosters:
            return
        recents = self.get_recent_sheets()
        if sheet_name in recents:
            recents.remove(sheet_name)
        recents.insert(0, sheet_name)
        self.settings["recent_sheets"] = recents[:5]
        self.save()

    def get_sheet_entries(self, sheet_name: str) -> list[PresetEntry]:
        return self.rosters.get(sheet_name, [])

    def create_sheet(self, name: str) -> bool:
        if name in self.rosters:
            return False
        self.rosters[name] = []
        self.sheets_meta[name] = {"note": "", "tags": []}
        if name not in self.dropdown_cache["table_names"]:
            self.dropdown_cache["table_names"].append(name)
        self.save()
        return True

    def rename_sheet(self, old_name: str, new_name: str) -> bool:
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
        if sheet_name not in self.rosters:
            self.rosters[sheet_name] = []
            self.sheets_meta[sheet_name] = {"note": "", "tags": []}
            if sheet_name not in self.dropdown_cache["table_names"]:
                self.dropdown_cache["table_names"].append(sheet_name)
        self.rosters[sheet_name].append(entry)
        self.save()

    def update_preset_entry(self, sheet_name: str, updated: PresetEntry) -> bool:
        presets = self.rosters.get(sheet_name, [])
        for idx, p in enumerate(presets):
            if p.entry_id == updated.entry_id:
                presets[idx] = updated
                self.save()
                return True

        logger.warning(
            "update_preset_entry: entry_id '%s' not found in sheet '%s'.",
            updated.entry_id,
            sheet_name,
        )
        return False

    def get_sheet_meta(self, sheet_name: str) -> dict[str, Any]:
        return self.sheets_meta.get(sheet_name, {"note": "", "tags": []})

    def update_sheet_meta(self, sheet_name: str, note: str, tags: list[str]) -> None:
        if sheet_name not in self.sheets_meta:
            self.sheets_meta[sheet_name] = {}
        self.sheets_meta[sheet_name]["note"] = note
        self.sheets_meta[sheet_name]["tags"] = tags
        self.save()

    # ── Database Cache Operations ──────────────────────────────────────

    def get_cache(self, category: str) -> list[dict[str, Any]]:
        return self.dropdown_cache.get(category, [])

    def get_character_code(self, name: str) -> str:
        for char in self.dropdown_cache.get("characters", []):
            if char.get("name") == name:
                return char.get("code", "")
        return ""

    def add_to_cache(self, category: str, item: dict[str, Any]) -> None:
        if category not in self.dropdown_cache:
            self.dropdown_cache[category] = []
        self.dropdown_cache[category].append(item)
        self.save()

    def update_cache_item(self, category: str, index: int, item: dict[str, Any]) -> None:
        items = self.dropdown_cache.get(category, [])
        if 0 <= index < len(items):
            items[index] = item
            self.save()

    def remove_from_cache(self, category: str, index: int) -> None:
        items = self.dropdown_cache.get(category, [])
        if 0 <= index < len(items):
            items.pop(index)
            self.save()

    # ── Cache Normalization ────────────────────────────────────────────

    def _canonicalize_cache_item(self, key: str, item: Any) -> Any:
        if isinstance(item, str):
            if key == "characters":
                return {"code": "MOD", "name": item, "is_playable": True}
            if key == "super_souls":
                return {
                    "name": item,
                    "owner": "",
                    "effect_1": "",
                    "effect_2": "",
                    "limit_burst": "",
                }
            if key in ("super_skills", "ultimate_skills", "awoken_skills", "evasive_skills"):
                return {
                    "name": item,
                    "is_cac": False,
                    "skill_type": "",
                    "ki_used": None,
                    "note": "",
                }
            return item

        if not isinstance(item, dict):
            return item

        if key == "characters":
            if any(k in item for k in ("Code", "Name", "Playable Character")):
                return {
                    "code": item.get("Code", ""),
                    "name": item.get("Name", ""),
                    "is_playable": str(item.get("Playable Character", "Yes")).lower() == "yes",
                }
            return {
                "code": item.get("code", ""),
                "name": item.get("name", ""),
                "is_playable": bool(item.get("is_playable", True)),
            }

        if key == "super_souls":
            if any(k in item for k in ("Super Soul", "Effect 1", "Effect 2")):
                return {
                    "name": item.get("Super Soul", ""),
                    "owner": item.get("Owner", ""),
                    "effect_1": item.get("Effect 1", ""),
                    "effect_2": item.get("Effect 2", ""),
                    "limit_burst": item.get("Limit Burst", ""),
                }
            return {
                "name": item.get("name", ""),
                "owner": item.get("owner", ""),
                "effect_1": item.get("effect_1", ""),
                "effect_2": item.get("effect_2", ""),
                "limit_burst": item.get("limit_burst", ""),
            }

        if key in ("super_skills", "ultimate_skills", "awoken_skills", "evasive_skills"):
            if any(k in item for k in ("Skill Name", "Is CaC Skill?", "Skill ID")):
                result: dict[str, Any] = {
                    "name": item.get("Skill Name", ""),
                    "is_cac": str(item.get("Is CaC Skill?", "No")).lower() == "yes",
                    "skill_type": item.get("Skill Type", ""),
                    "ki_used": item.get("Ki Used"),
                    "note": item.get("Note", ""),
                }
                if "Skill ID" in item:
                    result["skill_id"] = item["Skill ID"]
                return result
            result = {
                "name": item.get("name", ""),
                "is_cac": bool(item.get("is_cac", False)),
                "skill_type": item.get("skill_type", ""),
                "ki_used": item.get("ki_used"),
                "note": item.get("note", ""),
            }
            if "skill_id" in item:
                result["skill_id"] = item["skill_id"]
            return result

        return item

    def force_migrate_cache(self, key: str) -> bool:
        items = self.dropdown_cache.get(key, [])
        if not items:
            return False

        migrated = [self._canonicalize_cache_item(key, item) for item in items]
        if migrated == items:
            return False

        self.dropdown_cache[key] = migrated
        self.save()
        return True