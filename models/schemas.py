from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Union

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

@dataclass
class CharacterEntry:
    code: str
    name: str
    is_playable: bool = True
    base_character: str = ""
    episodes: list[str] = field(default_factory=list)
    created_at: str = ""
    modified_at: str = ""

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "name": self.name,
            "is_playable": self.is_playable,
            "base_character": self.base_character,
            "episodes": list(self.episodes),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CharacterEntry":
        if "Code" in d or "Name" in d or "Playable Character" in d:
            return cls(
                code=d.get("Code", ""),
                name=d.get("Name", ""),
                is_playable=str(d.get("Playable Character", "Yes")).lower() == "yes",
                base_character=d.get("Base Character", ""),
                episodes=list(d.get("Episodes", [])),
            )
        return cls(
            code=d.get("code", ""),
            name=d.get("name", ""),
            is_playable=bool(d.get("is_playable", True)),
            base_character=d.get("base_character", ""),
            episodes=list(d.get("episodes", [])),
        )


@dataclass
class SkillEntry:
    skill_name: str
    skill_id: Optional[str] = None
    is_cac_skill: bool = False
    skill_type: str = ""
    ki_used: Optional[int] = None
    note: str = ""
    created_at: str = ""
    modified_at: str = ""

    def to_dict(self) -> dict:
        d: dict = {
            "name": self.skill_name,
            "is_cac": self.is_cac_skill,
            "skill_type": self.skill_type,
            "ki_used": self.ki_used,
            "note": self.note,
        }
        if self.skill_id is not None:
            d["skill_id"] = self.skill_id
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "SkillEntry":
        if "Skill Name" in d or "Is CaC Skill?" in d:
            return cls(
                skill_name=d.get("Skill Name", ""),
                skill_id=d.get("Skill ID"),
                is_cac_skill=str(d.get("Is CaC Skill?", "No")).lower() == "yes",
                skill_type=d.get("Skill Type", ""),
                ki_used=d.get("Ki Used"),
                note=d.get("Note", ""),
            )
        return cls(
            skill_name=d.get("name", ""),
            skill_id=d.get("skill_id"),
            is_cac_skill=bool(d.get("is_cac", False)),
            skill_type=d.get("skill_type", ""),
            ki_used=d.get("ki_used"),
            note=d.get("note", ""),
        )


@dataclass
class SuperSoulEntry:
    name: str
    owner: str = ""
    effect_1: str = ""
    effect_2: str = ""
    limit_burst: str = ""
    created_at: str = ""
    modified_at: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "owner": self.owner,
            "effect_1": self.effect_1,
            "effect_2": self.effect_2,
            "limit_burst": self.limit_burst,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SuperSoulEntry":
        if "Super Soul" in d or "Effect 1" in d:
            return cls(
                name=d.get("Super Soul", ""),
                owner=d.get("Owner", ""),
                effect_1=d.get("Effect 1", ""),
                effect_2=d.get("Effect 2", ""),
                limit_burst=d.get("Limit Burst", ""),
            )
        return cls(
            name=d.get("name", ""),
            owner=d.get("owner", ""),
            effect_1=d.get("effect_1", ""),
            effect_2=d.get("effect_2", ""),
            limit_burst=d.get("limit_burst", ""),
        )

@dataclass
class SourceEntry:
    name: str
    source_type: str = ""
    day: Optional[int] = None
    month: Optional[int] = None
    year: Optional[int] = None
    created_at: str = ""
    modified_at: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "source_type": self.source_type,
            "day": self.day,
            "month": self.month,
            "year": self.year,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SourceEntry":
        def _to_int_or_none(v):
            if v is None:
                return None
            try:
                return int(v)
            except (ValueError, TypeError):
                return None

        return cls(
            name=d.get("name", ""),
            source_type=d.get("source_type", ""),
            day=_to_int_or_none(d.get("day")),
            month=_to_int_or_none(d.get("month")),
            year=_to_int_or_none(d.get("year")),
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
    source: str = ""
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
            "Source": self.source,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PresetEntry":
        raw_c_idx = d.get("Costume Index", 0)
        try:
            costume_index = int(raw_c_idx)
        except (ValueError, TypeError):
            costume_index = 0

        raw_preset = d.get("Model Preset", "")

        # Handle empty strings that might have been saved in legacy or from bad copies
        raw_entry_id = d.get("entry_id")
        final_entry_id = raw_entry_id if raw_entry_id else _generate_entry_id()

        return cls(
            entry_id=final_entry_id,
            character_name=d.get("Character Name", ""),
            character_id=d.get("Character ID", ""),
            costume_name=d.get("Costume Name", ""),
            costume_index=costume_index,
            model_preset=str(raw_preset) if raw_preset else "",
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
            source=d.get("Source", ""),
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
Source = SourceEntry