from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.data_store import AppDataStore


def find_character_variants(store: "AppDataStore", base_name: str) -> list[str]:
    if not base_name:
        return []
    chars = store.dropdown_cache.get("characters", [])
    result: list[str] = []
    for c in chars:
        name = c.get("name", "")
        if name and name != base_name and c.get("base_character", "") == base_name:
            result.append(name)
    return result


def apply_cascade_rename(
    store: "AppDataStore",
    old_base: str,
    new_base: str,
) -> None:
    if not old_base or not new_base or old_base == new_base:
        return

    def _rename_value(value: str) -> str:
        if value == old_base:
            return new_base
        prefix = old_base + " ("
        if value.startswith(prefix):
            return new_base + value[len(old_base):]
        return value

    chars = store.dropdown_cache.get("characters", [])
    for c in chars:
        old_name = c.get("name", "")
        new_name = _rename_value(old_name)
        if new_name != old_name:
            c["name"] = new_name

        old_bc = c.get("base_character", "")
        if old_bc == old_base:
            c["base_character"] = new_base

    souls = store.dropdown_cache.get("super_souls", [])
    for s in souls:
        owner = s.get("owner", "")
        new_owner = _rename_value(owner)
        if new_owner != owner:
            s["owner"] = new_owner

    for presets in store.rosters.values():
        for p in presets:
            new_name = _rename_value(p.character_name)
            if new_name != p.character_name:
                p.character_name = new_name