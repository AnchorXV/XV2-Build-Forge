import sys
from pathlib import Path
from typing import Final

APP_NAME: Final[str] = "DBXV2 Build Forge"
APP_ORG: Final[str] = "DBXV2Modding"
APP_VERSION: Final[str] = "1.0.0"

DATA_FILE: Final[str] = "build_forge_data.json"
DATA_FILE_PATH: Final[Path] = Path(DATA_FILE)
SETTINGS_FILE: Final[str] = "settings.json"
SETTINGS_FILE_PATH: Final[Path] = Path(SETTINGS_FILE)

TABLE_COLUMNS: Final[list[str]] = [
    "Character Name", "Character ID", "Costume Name", "Costume Index",
    "Model Preset",
    "Super Skill 1", "Super Skill 2", "Super Skill 3", "Super Skill 4",
    "Ultimate Skill 1", "Ultimate Skill 2",
    "Awoken Skill", "Evasive Skill", "Super Soul",
]

SUMMARY_COLUMNS: Final[list[str]] = [
    "Character Name", "Total Costume", "Total Preset",
    "Total Super Skill", "Total Ultimate Skill",
    "Total Awoken Skill", "Total Evasive Skill", "Total Super Soul",
]

CHAR_DB_COLUMNS: Final[list[str]] = ["Code", "Name", "Playable Character"]
SKILL_DB_COLUMNS: Final[list[str]] = ["Skill Name", "Is CaC Skill?", "Note"]
SUPERSOUL_DB_COLUMNS: Final[list[str]] = ["Super Soul", "Effect 1", "Effect 2", "Note"]

CACHE_KEYS: Final[list[str]] = [
    "characters", "character_ids", "costume_names",
    "super_skills", "ultimate_skills", "awoken_skills", "evasive_skills",
    "super_souls", "table_names",
]

SUPPORTED_LANGUAGES: Final[dict[str, str]] = {
    "en": "English",
    "id": "Bahasa Indonesia",
    "ja": "日本語",
}
DEFAULT_LANGUAGE: Final[str] = "en"
DEFAULT_THEME: Final[str] = "dark"


def get_resource_path(relative_path: str) -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).resolve().parent

    return base / relative_path