"""
DBXV2 Build Forge — Input Validators.

Provides reusable validation functions for form inputs and database entries.
All validators return either a ``(is_valid, error_message)`` tuple or
a ``list[str]`` of errors so controllers/views can surface messages to the user.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from models.schemas import CharacterEntry, PresetEntry


def validate_not_empty(value: str, field_label: str = "Field") -> tuple[bool, str]:
    """Check that *value* is a non-empty, non-whitespace string."""
    if not value or not value.strip():
        return False, f"{field_label} must not be empty."
    return True, ""


def validate_unique_in_list(
    value: str,
    existing: list[str],
    field_label: str = "Entry",
) -> tuple[bool, str]:
    """Check that *value* does not already appear in *existing* (exact match)."""
    if value in existing:
        return False, f"{field_label} '{value}' already exists."
    return True, ""


def validate_sheet_name(name: str, existing_names: list[str]) -> tuple[bool, str]:
    """Validate a new or renamed sheet name."""
    ok, msg = validate_not_empty(name, "Sheet name")
    if not ok:
        return ok, msg
    return validate_unique_in_list(name.strip(), existing_names, "Sheet name")


def validate_entry_name(data: dict[str, Any], key_name: str) -> tuple[bool, str]:
    """Validate that the primary name field in *data* is non-empty."""
    return validate_not_empty(data.get(key_name, ""), key_name)


def validate_character(char: Any) -> list[str]:
    """Validate a Character or CharacterEntry object or dict.

    Returns:
        List of error strings (empty if valid).
    """
    errors: list[str] = []
    code = getattr(char, "code", None) if hasattr(char, "code") else char.get("code", "")
    name = getattr(char, "name", None) if hasattr(char, "name") else char.get("name", "")

    if not code or not str(code).strip():
        errors.append("Character code must not be empty.")
    if not name or not str(name).strip():
        errors.append("Character name must not be empty.")
    return errors


def validate_preset_entry(preset: Any) -> list[str]:
    """Validate a PresetEntry object.

    Returns:
        List of error strings (empty if valid).
    """
    errors: list[str] = []
    char_name = (
        getattr(preset, "character_name", "")
        if hasattr(preset, "character_name")
        else preset.get("character_name", "")
    )
    if not char_name or not str(char_name).strip():
        errors.append("Character name must not be empty.")
    return errors
