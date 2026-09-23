"""
DBXV2 Build Forge — Data Schemas.

Immutable dataclasses representing the core domain objects.
Every ``PresetEntry`` carries a UUID ``entry_id`` generated on first save,
enabling the *Load into Editor → Update* workflow (PRD §3.3).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Optional, Union


@dataclass
class CharacterEntry:
    """A playable or modded character in the database."""

    code: str
    name: str
    is_playable: bool = True

    # ── Serialisation helpers ──────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "Code": self.code,
            "Name": self.name,
            "Playable Character": "Yes" if self.is_playable else "No",
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CharacterEntry":
        return cls(
            code=d.get("Code", ""),
            name=d.get("Name", ""),
            is_playable=d.get("Playable Character", "Yes") == "Yes",
        )


@dataclass
class SkillEntry:
    """A skill entry (Super / Ultimate / Awoken / Evasive)."""

    skill_name: str
    skill_id: Optional[str] = None
    is_cac_skill: bool = False
    note: str = ""

    def to_dict(self) -> dict:
        d: dict = {
            "Skill Name": self.skill_name,
            "Is CaC Skill?": "Yes" if self.is_cac_skill else "No",
            "Note": self.note,
        }
        if self.skill_id is not None:
            d["Skill ID"] = self.skill_id
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "SkillEntry":
        return cls(
            skill_name=d.get("Skill Name", ""),
            skill_id=d.get("Skill ID"),
            is_cac_skill=d.get("Is CaC Skill?", "No") == "Yes",
            note=d.get("Note", ""),
        )


@dataclass
class SuperSoulEntry:
    """A Super Soul with up to two effect descriptions."""

    name: str
    effect_1: str = ""
    effect_2: str = ""
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "Super Soul": self.name,
            "Effect 1": self.effect_1,
            "Effect 2": self.effect_2,
            "Note": self.note,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SuperSoulEntry":
        return cls(
            name=d.get("Super Soul", ""),
            effect_1=d.get("Effect 1", ""),
            effect_2=d.get("Effect 2", ""),
            note=d.get("Note", ""),
        )


def _generate_entry_id() -> str:
    """Generate a new UUID4 string for a preset entry."""
    return str(uuid.uuid4())


@dataclass
class PresetEntry:
    """A single character build preset within a roster sheet.

    ``entry_id`` is a UUID4 string that uniquely identifies this preset,
    enabling the *Update* (in-place edit) workflow introduced in PRD §3.3.
    """

    character_name: str
    character_id: str = ""
    costume_name: str = ""
    costume_index: int = 0
    model_preset: Union[str, int] = ""
    super_skills: list[str] = field(default_factory=lambda: ["", "", "", ""])
    ultimate_skills: list[str] = field(default_factory=lambda: ["", ""])
    awoken_skill: str = ""
    evasive_skill: str = ""
    super_soul: str = ""
    entry_id: str = field(default_factory=_generate_entry_id)

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "Character Name": self.character_name,
            "Character ID": self.character_id,
            "Costume Name": self.costume_name,
            "Costume Index": self.costume_index,
            "Model Preset": str(self.model_preset),
            "Super Skill 1": self.super_skills[0] if len(self.super_skills) > 0 else "",
            "Super Skill 2": self.super_skills[1] if len(self.super_skills) > 1 else "",
            "Super Skill 3": self.super_skills[2] if len(self.super_skills) > 2 else "",
            "Super Skill 4": self.super_skills[3] if len(self.super_skills) > 3 else "",
            "Ultimate Skill 1": self.ultimate_skills[0] if len(self.ultimate_skills) > 0 else "",
            "Ultimate Skill 2": self.ultimate_skills[1] if len(self.ultimate_skills) > 1 else "",
            "Awoken Skill": self.awoken_skill,
            "Evasive Skill": self.evasive_skill,
            "Super Soul": self.super_soul,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PresetEntry":
        raw_c_idx = d.get("Costume Index", 0)
        try:
            costume_index = int(raw_c_idx)
        except (ValueError, TypeError):
            costume_index = 0

        raw_preset = d.get("Model Preset", "")
        try:
            model_preset = int(raw_preset) if raw_preset else 0
        except (ValueError, TypeError):
            model_preset = 0

        # Handle empty strings that might have been saved in legacy or from bad copies
        raw_entry_id = d.get("entry_id")
        final_entry_id = raw_entry_id if raw_entry_id else _generate_entry_id()

        return cls(
            entry_id=final_entry_id,
            character_name=d.get("Character Name", ""),
            character_id=d.get("Character ID", ""),
            costume_name=d.get("Costume Name", ""),
            costume_index=costume_index,
            model_preset=str(raw_preset),
            super_skills=[
                d.get("Super Skill 1", ""),
                d.get("Super Skill 2", ""),
                d.get("Super Skill 3", ""),
                d.get("Super Skill 4", ""),
            ],
            ultimate_skills=[
                d.get("Ultimate Skill 1", ""),
                d.get("Ultimate Skill 2", ""),
            ],
            awoken_skill=d.get("Awoken Skill", ""),
            evasive_skill=d.get("Evasive Skill", ""),
            super_soul=d.get("Super Soul", ""),
        )


@dataclass
class RosterSheet:
    """A named collection of preset entries (one 'sheet' in the planner)."""

    name: str
    presets: list[PresetEntry] = field(default_factory=list)
    note: str = ""
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "presets": [p.to_dict() for p in self.presets],
            "note": self.note,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "RosterSheet":
        return cls(
            name=d.get("name", ""),
            presets=[PresetEntry.from_dict(p) for p in d.get("presets", [])],
            note=d.get("note", ""),
            tags=d.get("tags", []),
        )


# ── Shorthand aliases ──────────────────────────────────────────
Character = CharacterEntry
Skill = SkillEntry
SuperSoul = SuperSoulEntry
