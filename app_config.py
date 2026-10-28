import sys
from pathlib import Path
from typing import Final

APP_NAME: Final[str] = "DBXV2 Build Forge"
APP_ORG: Final[str] = "DBXV2Modding"
APP_VERSION: Final[str] = "1.0.0"

DATA_FILE: Final[str] = "build_forge_data.json"
SETTINGS_FILE: Final[str] = "settings.json"

TABLE_COLUMNS: Final[list[str]] = [
    "Character Name", "Character ID", "Costume Name", "Costume Index",
    "Model Preset",
    "Super Skill 1", "Super Skill 2", "Super Skill 3", "Super Skill 4",
    "Ultimate Skill 1", "Ultimate Skill 2",
    "Awoken Skill", "Evasive Skill", "Super Soul",
    "Source",
]

CHAR_DB_COLUMNS: Final[list[str]] = ["Code", "Name", "Playable Character"]
SKILL_DB_COLUMNS: Final[list[str]] = ["Skill Name", "Is CaC Skill?", "Skill Type", "Ki Used", "Description"]
SUPERSOUL_DB_COLUMNS: Final[list[str]] = ["Super Soul", "Owner", "Effect 1", "Effect 2", "Limit Burst"]
SOURCE_DB_COLUMNS: Final[list[str]] = ["Source Name", "Type", "Date"]

CACHE_KEYS: Final[list[str]] = [
    "characters", "character_ids", "costume_names",
    "super_skills", "ultimate_skills", "awoken_skills", "evasive_skills",
    "super_souls", "sources", "table_names",
]

DEFAULT_LANGUAGE: Final[str] = "en"

SKILL_TYPE_ICON_MAP: Final[dict[str, str]] = {
    "strike": "strike-skill.png",
    "ki_blast": "ki-blast-skill.png",
    "buff": "power-up.png",
    "other": "other.png",
    "strike_dual": "strike-skill-dual.png",
    "ki_blast_dual": "ki-blast-skill-dual.png",
    "buff_dual": "power-up-dual.png",
    "other_dual": "other-dual.png",
    "strike_raid": "strike-skill-crystal-raid.png",
    "ki_blast_raid": "ki-blast-skill-crystal-raid.png",
    "buff_raid": "power-up-crystal-raid.png",
    "other_raid": "other-crystal-raid.png",
    "transformation": "transformation.png",
    "transformation_dual": "transformation-dual.png",
    "transformation_raid": "transformation-crystal-raid.png",
}

NON_AWOKEN_TYPES = [
    "strike", "ki_blast", "buff", "other",
    "strike_dual", "ki_blast_dual", "buff_dual", "other_dual",
    "strike_raid", "ki_blast_raid", "buff_raid", "other_raid"
]

SKILL_TYPES_BY_CATEGORY: Final[dict[str, list[str]]] = {
    "super_skills": NON_AWOKEN_TYPES,
    "ultimate_skills": NON_AWOKEN_TYPES,
    "evasive_skills": NON_AWOKEN_TYPES,
    "awoken_skills": ["transformation", "transformation_dual", "transformation_raid"],
}


def is_compiled() -> bool:
    return getattr(sys, "frozen", False) or "__compiled__" in globals()


def get_app_dir() -> Path:
    if is_compiled():
        return Path(sys.argv[0]).resolve().parent
    return Path(__file__).resolve().parent


DATA_FILE_PATH: Final[Path] = get_app_dir() / DATA_FILE
SETTINGS_FILE_PATH: Final[Path] = get_app_dir() / SETTINGS_FILE


def get_resource_path(relative_path: str) -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).resolve().parent

    return base / relative_path