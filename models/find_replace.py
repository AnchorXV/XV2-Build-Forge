from __future__ import annotations

import re

from models.schemas import PresetEntry


FIELD_KEYS: list[str] = [
    "character_name",
    "costume_name",
    "source",
    "super_skill_1",
    "super_skill_2",
    "super_skill_3",
    "super_skill_4",
    "ultimate_skill_1",
    "ultimate_skill_2",
    "awoken_skill",
    "evasive_skill",
    "super_soul",
]


FIELD_LABELS: dict[str, str] = {
    "character_name": "Character Name",
    "costume_name": "Costume Name",
    "source": "Source",
    "super_skill_1": "Super Skill 1",
    "super_skill_2": "Super Skill 2",
    "super_skill_3": "Super Skill 3",
    "super_skill_4": "Super Skill 4",
    "ultimate_skill_1": "Ultimate Skill 1",
    "ultimate_skill_2": "Ultimate Skill 2",
    "awoken_skill": "Awoken Skill",
    "evasive_skill": "Evasive Skill",
    "super_soul": "Super Soul",
}


def get_field_value(entry: PresetEntry, field_key: str) -> str:
    if field_key == "character_name":
        return entry.character_name
    if field_key == "costume_name":
        return entry.costume_name
    if field_key == "source":
        return entry.source
    if field_key.startswith("super_skill_"):
        i = int(field_key.split("_")[-1]) - 1
        return entry.super_skills[i] if 0 <= i < len(entry.super_skills) else ""
    if field_key.startswith("ultimate_skill_"):
        i = int(field_key.split("_")[-1]) - 1
        return entry.ultimate_skills[i] if 0 <= i < len(entry.ultimate_skills) else ""
    if field_key == "awoken_skill":
        return entry.awoken_skill
    if field_key == "evasive_skill":
        return entry.evasive_skill
    if field_key == "super_soul":
        return entry.super_soul
    return ""

def set_field_value(entry: PresetEntry, field_key: str, value: str) -> None:
    if field_key == "character_name":
        entry.character_name = value
    elif field_key == "costume_name":
        entry.costume_name = value
    elif field_key == "source":
        entry.source = value
    elif field_key.startswith("super_skill_"):
        i = int(field_key.split("_")[-1]) - 1
        if 0 <= i < len(entry.super_skills):
            skills = list(entry.super_skills)
            skills[i] = value
            entry.super_skills = skills
    elif field_key.startswith("ultimate_skill_"):
        i = int(field_key.split("_")[-1]) - 1
        if 0 <= i < len(entry.ultimate_skills):
            skills = list(entry.ultimate_skills)
            skills[i] = value
            entry.ultimate_skills = skills
    elif field_key == "awoken_skill":
        entry.awoken_skill = value
    elif field_key == "evasive_skill":
        entry.evasive_skill = value
    elif field_key == "super_soul":
        entry.super_soul = value

def _matches(haystack: str, needle: str, case_sensitive: bool) -> bool:
    if not needle:
        return False
    if case_sensitive:
        return needle in haystack
    return needle.lower() in haystack.lower()


def _replace_in(haystack: str, needle: str, replacement: str, case_sensitive: bool) -> str:
    if case_sensitive:
        return haystack.replace(needle, replacement)
    return re.sub(re.escape(needle), replacement, haystack, flags=re.IGNORECASE)


def count_matches(
    presets: list[PresetEntry],
    find_text: str,
    field_keys: list[str],
    case_sensitive: bool = False,
) -> int:
    if not find_text:
        return 0

    use_all = "all" in field_keys
    keys_to_check = FIELD_KEYS if use_all else field_keys

    count = 0
    for entry in presets:
        for key in keys_to_check:
            if _matches(get_field_value(entry, key), find_text, case_sensitive):
                count += 1
    return count


def find_replace_changes(
    presets: list[PresetEntry],
    find_text: str,
    replace_text: str,
    field_keys: list[str],
    case_sensitive: bool = False,
) -> list[tuple[PresetEntry, PresetEntry]]:
    if not find_text or find_text == replace_text:
        return []

    use_all = "all" in field_keys
    keys_to_check = FIELD_KEYS if use_all else field_keys

    changes: list[tuple[PresetEntry, PresetEntry]] = []
    for entry in presets:
        new_entry = PresetEntry.from_dict(entry.to_dict())
        modified = False
        for key in keys_to_check:
            old_val = get_field_value(entry, key)
            if _matches(old_val, find_text, case_sensitive):
                new_val = _replace_in(old_val, find_text, replace_text, case_sensitive)
                if new_val != old_val:
                    set_field_value(new_entry, key, new_val)
                    modified = True
        if modified:
            changes.append((entry, new_entry))
    return changes