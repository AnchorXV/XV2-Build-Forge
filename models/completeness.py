"""
DBXV2 Build Forge — Preset Completeness Checker.

Utility functions that inspect a ``PresetEntry`` and report which
mandatory slots are empty.  Used by ``RosterSummaryTableModel`` to
display visual warnings (icon + tooltip) on incomplete presets.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.schemas import PresetEntry


def check_preset_completeness(entry: "PresetEntry") -> list[str]:
    """Return a list of human-readable labels for empty mandatory slots.

    The mandatory slots are:
        - Super Skill 1–4
        - Ultimate Skill 1–2
        - Awoken Skill
        - Evasive Skill
        - Super Soul

    Args:
        entry: The preset entry to inspect.

    Returns:
        A list of missing slot labels, e.g.
        ``["Super Skill 3", "Super Skill 4", "Ultimate Skill 2"]``.
        Empty list means the preset is complete.
    """
    missing: list[str] = []

    # Super Skills (4 slots)
    for i, skill in enumerate(entry.super_skills):
        if not skill or not skill.strip():
            missing.append(f"Super Skill {i + 1}")

    # Ultimate Skills (2 slots)
    for i, skill in enumerate(entry.ultimate_skills):
        if not skill or not skill.strip():
            missing.append(f"Ultimate Skill {i + 1}")

    # Single slots
    if not entry.awoken_skill or not entry.awoken_skill.strip():
        missing.append("Awoken Skill")
    if not entry.evasive_skill or not entry.evasive_skill.strip():
        missing.append("Evasive Skill")
    if not entry.super_soul or not entry.super_soul.strip():
        missing.append("Super Soul")

    return missing


def get_sheet_completeness_summary(
    presets: list["PresetEntry"],
) -> list[tuple[str, list[str]]]:
    """Check completeness for all presets in a sheet.

    Args:
        presets: List of ``PresetEntry`` objects in the sheet.

    Returns:
        A list of ``(preset_label, missing_slots)`` tuples.
        Only presets with missing slots are included.
    """
    warnings: list[tuple[str, list[str]]] = []
    for entry in presets:
        missing = check_preset_completeness(entry)
        if missing:
            label = entry.character_name or "Unnamed"
            if entry.costume_name:
                label = f"{label} ({entry.costume_name})"
            warnings.append((label, missing))
    return warnings
