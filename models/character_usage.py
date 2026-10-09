from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.data_store import AppDataStore

SKILL_CATEGORIES: dict[str, dict] = {
    "super_skills": {
        "slots": ["Super 1", "Super 2", "Super 3", "Super 4"],
        "suffix": "Super",
        "field": "super_skills",
    },
    "ultimate_skills": {
        "slots": ["Ultimate 1", "Ultimate 2"],
        "suffix": "Ultimate",
        "field": "ultimate_skills",
    },
    "awoken_skills": {
        "slots": ["Awoken"],
        "suffix": "Awoken",
        "field": "awoken_skill",
    },
    "evasive_skills": {
        "slots": ["Evasive"],
        "suffix": "Evasive",
        "field": "evasive_skill",
    },
}


@dataclass(frozen=True)
class UsageEntry:
    character_name: str
    costume_name: str
    slot_label: str
    sheet_name: str
    entry_id: str

    def display_label(self) -> str:
        costume = self.costume_name if self.costume_name else "—"
        return f"{self.character_name} · {costume} · {self.slot_label}"


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

def _get_skills_in_category(preset, category_key: str) -> list[str]:
    info = SKILL_CATEGORIES.get(category_key)
    if info is None:
        return []
    value = getattr(preset, info["field"], "")
    if isinstance(value, list):
        return value
    return [value] if value else []


def find_skill_usage(
    store: "AppDataStore",
    skill_name: str,
    category: str,
) -> list[UsageEntry]:
    """Cari semua tempat skill_name dipakai di kategori tertentu.

    Return flat list tanpa deduplikasi. Kalau skill dipakai di 2 slot
    di 1 preset, akan muncul 2 entries.
    """
    if not skill_name or category not in SKILL_CATEGORIES:
        return []

    info = SKILL_CATEGORIES[category]
    slots = info["slots"]
    target = skill_name.strip()

    results: list[UsageEntry] = []
    for sheet_name, presets in store.rosters.items():
        for preset in presets:
            skills = _get_skills_in_category(preset, category)
            for i, skill in enumerate(skills):
                if skill and skill.strip() == target:
                    slot_label = slots[i] if i < len(slots) else f"Slot {i + 1}"
                    results.append(UsageEntry(
                        character_name=preset.character_name,
                        costume_name=preset.costume_name,
                        slot_label=slot_label,
                        sheet_name=sheet_name,
                        entry_id=preset.entry_id,
                    ))
    return results


def find_soul_usage(
    store: "AppDataStore",
    soul_name: str,
) -> list[UsageEntry]:
    """Cari semua tempat soul_name dipakai sebagai super_soul."""
    if not soul_name:
        return []

    target = soul_name.strip()
    results: list[UsageEntry] = []
    for sheet_name, presets in store.rosters.items():
        for preset in presets:
            soul = (preset.super_soul or "").strip()
            if soul == target:
                results.append(UsageEntry(
                    character_name=preset.character_name,
                    costume_name=preset.costume_name,
                    slot_label="Super Soul",
                    sheet_name=sheet_name,
                    entry_id=preset.entry_id,
                ))
    return results


def find_character_skills(
    store: "AppDataStore",
    char_name: str,
) -> list[tuple[str, int]]:
    if not char_name:
        return []

    category_uses: dict[str, dict[str, set[str]]] = {
        cat: {} for cat in SKILL_CATEGORIES
    }

    for presets in store.rosters.values():
        for preset in presets:
            if preset.character_name != char_name:
                continue
            for cat_key in SKILL_CATEGORIES:
                for s in _get_skills_in_category(preset, cat_key):
                    s = (s or "").strip()
                    if s:
                        category_uses[cat_key].setdefault(s, set()).add(preset.entry_id)

    result: list[tuple[str, int]] = []
    for cat_key, skills in category_uses.items():
        suffix = SKILL_CATEGORIES[cat_key]["suffix"]
        for skill_name, entry_ids in skills.items():
            display = f"{skill_name} ({suffix})"
            result.append((display, len(entry_ids)))

    result.sort(key=lambda x: x[0].lower())
    return result


def find_character_souls(
    store: "AppDataStore",
    char_name: str,
) -> list[tuple[str, int]]:
    """Return list of (soul_name, preset_count) untuk Super Soul yang
    dipakai oleh char_name (exact match di semua costume)."""
    if not char_name:
        return []

    soul_uses: dict[str, set[str]] = {}
    for presets in store.rosters.values():
        for preset in presets:
            if preset.character_name != char_name:
                continue
            s = (preset.super_soul or "").strip()
            if s:
                soul_uses.setdefault(s, set()).add(preset.entry_id)

    result = [(name, len(ids)) for name, ids in soul_uses.items()]
    result.sort(key=lambda x: x[0].lower())
    return result