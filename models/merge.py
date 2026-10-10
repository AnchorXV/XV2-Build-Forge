from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.data_store import AppDataStore


SKILL_CATEGORY_TO_FIELD: dict[str, str] = {
    "super_skills": "super_skills",
    "ultimate_skills": "ultimate_skills",
    "awoken_skills": "awoken_skill",
    "evasive_skills": "evasive_skill",
}


def count_merge_impact(store: "AppDataStore", category: str, source_name: str) -> int:
    if not source_name:
        return 0

    count = 0

    if category == "characters":
        for presets in store.rosters.values():
            for p in presets:
                if p.character_name == source_name:
                    count += 1
        return count

    if category in SKILL_CATEGORY_TO_FIELD:
        field = SKILL_CATEGORY_TO_FIELD[category]
        for presets in store.rosters.values():
            for p in presets:
                value = getattr(p, field, "")
                if isinstance(value, list):
                    if any(v == source_name for v in value):
                        count += 1
                elif value == source_name:
                    count += 1
        return count

    if category == "super_souls":
        for presets in store.rosters.values():
            for p in presets:
                if p.super_soul == source_name:
                    count += 1
        return count

    if category == "sources":
        for presets in store.rosters.values():
            for p in presets:
                if p.source == source_name:
                    count += 1
        return count

    return 0


def merge_entry(
    store: "AppDataStore",
    category: str,
    source_name: str,
    target_name: str,
) -> int:
    if not source_name or not target_name or source_name == target_name:
        return 0

    affected = 0

    if category == "characters":
        for presets in store.rosters.values():
            for p in presets:
                if p.character_name == source_name:
                    p.character_name = target_name
                    affected += 1
        for s in store.dropdown_cache.get("super_souls", []):
            if isinstance(s, dict) and s.get("owner", "") == source_name:
                s["owner"] = target_name
        for c in store.dropdown_cache.get("characters", []):
            if isinstance(c, dict) and c.get("base_character", "") == source_name:
                c["base_character"] = target_name

    elif category in SKILL_CATEGORY_TO_FIELD:
        field = SKILL_CATEGORY_TO_FIELD[category]
        for presets in store.rosters.values():
            for p in presets:
                value = getattr(p, field, "")
                if isinstance(value, list):
                    new_list = list(value)
                    changed = False
                    for i, v in enumerate(new_list):
                        if v == source_name:
                            new_list[i] = target_name
                            changed = True
                    if changed:
                        setattr(p, field, new_list)
                        affected += 1
                elif value == source_name:
                    setattr(p, field, target_name)
                    affected += 1

    elif category == "super_souls":
        for presets in store.rosters.values():
            for p in presets:
                if p.super_soul == source_name:
                    p.super_soul = target_name
                    affected += 1

    elif category == "sources":
        for presets in store.rosters.values():
            for p in presets:
                if p.source == source_name:
                    p.source = target_name
                    affected += 1

    else:
        return 0

    items = store.dropdown_cache.get(category, [])
    store.dropdown_cache[category] = [
        item for item in items
        if not (isinstance(item, dict) and item.get("name") == source_name)
    ]

    return affected