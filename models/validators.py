from __future__ import annotations

from typing import Any


def validate_not_empty(value: str, field_label: str = "Field") -> tuple[bool, str]:
    if not value or not value.strip():
        return False, f"{field_label} must not be empty."
    return True, ""


def validate_unique_in_list(
    value: str,
    existing: list[str],
    field_label: str = "Entry",
) -> tuple[bool, str]:
    if value in existing:
        return False, f"{field_label} '{value}' already exists."
    return True, ""


def validate_sheet_name(name: str, existing_names: list[str]) -> tuple[bool, str]:
    ok, msg = validate_not_empty(name, "Sheet name")
    if not ok:
        return ok, msg
    return validate_unique_in_list(name.strip(), existing_names, "Sheet name")


def validate_entry_name(data: dict[str, Any], key_name: str) -> tuple[bool, str]:
    return validate_not_empty(data.get(key_name, ""), key_name)


def validate_character(char: Any) -> list[str]:
    errors: list[str] = []
    code = getattr(char, "code", None) if hasattr(char, "code") else char.get("code", "")
    name = getattr(char, "name", None) if hasattr(char, "name") else char.get("name", "")

    if not code or not str(code).strip():
        errors.append("Character code must not be empty.")
    if not name or not str(name).strip():
        errors.append("Character name must not be empty.")
    return errors


def validate_preset_entry(preset: Any) -> list[str]:
    errors: list[str] = []
    char_name = (
        getattr(preset, "character_name", "")
        if hasattr(preset, "character_name")
        else preset.get("character_name", "")
    )
    if not char_name or not str(char_name).strip():
        errors.append("Character name must not be empty.")
    return errors