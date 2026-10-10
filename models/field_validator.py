from __future__ import annotations

from difflib import get_close_matches
from typing import Optional

from models.data_store import AppDataStore


FIELD_TO_CACHE: dict[str, str] = {
    "character_name": "characters",
    "super_skill_0": "super_skills",
    "super_skill_1": "super_skills",
    "super_skill_2": "super_skills",
    "super_skill_3": "super_skills",
    "ultimate_skill_0": "ultimate_skills",
    "ultimate_skill_1": "ultimate_skills",
    "awoken_skill": "awoken_skills",
    "evasive_skill": "evasive_skills",
    "super_soul": "super_souls",
}


def check_field(store: AppDataStore, field_key: str, value: str) -> Optional[list[str]]:
    if not value or not value.strip():
        return None

    cache_key = FIELD_TO_CACHE.get(field_key)
    if cache_key is None:
        return None

    value = value.strip()
    names = [item.get("name", "") for item in store.get_cache(cache_key) if isinstance(item, dict)]
    if value in names:
        return None

    matches = get_close_matches(value, names, n=3, cutoff=0.75)
    return matches