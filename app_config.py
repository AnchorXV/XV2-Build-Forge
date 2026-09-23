"""
DBXV2 Build Forge — Global Application Configuration.

Central location for all application-wide constants, column definitions,
file paths, and resource resolution logic compatible with both source
execution and Nuitka onefile builds.
"""

import os
import sys
from pathlib import Path
from typing import Final

# ── Application Identity ──────────────────────────────────────────────
APP_NAME: Final[str] = "DBXV2 Build Forge"
APP_ORG: Final[str] = "DBXV2Modding"
APP_VERSION: Final[str] = "1.0.0"

# ── Data Files (stored in CWD) ────────────────────────────────────────
DATA_FILE: Final[str] = "build_forge_data.json"
DATA_FILE_PATH: Final[Path] = Path(DATA_FILE)
SETTINGS_FILE: Final[str] = "settings.json"
SETTINGS_FILE_PATH: Final[Path] = Path(SETTINGS_FILE)

# ── Table Column Definitions ──────────────────────────────────────────
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

# ── Database Manager Column Sets ──────────────────────────────────────
CHAR_DB_COLUMNS: Final[list[str]] = ["Code", "Name", "Playable Character"]
SKILL_DB_COLUMNS: Final[list[str]] = ["Skill Name", "Is CaC Skill?", "Note"]
SUPERSOUL_DB_COLUMNS: Final[list[str]] = ["Super Soul", "Effect 1", "Effect 2", "Note"]

# ── Dropdown Cache Keys ───────────────────────────────────────────────
CACHE_KEYS: Final[list[str]] = [
    "characters", "character_ids", "costume_names",
    "super_skills", "ultimate_skills", "awoken_skills", "evasive_skills",
    "super_souls", "table_names",
]

# ── Supported Languages & Themes ──────────────────────────────────────
SUPPORTED_LANGUAGES: Final[dict[str, str]] = {
    "en": "English",
    "id": "Bahasa Indonesia",
    "ja": "日本語",
}
DEFAULT_LANGUAGE: Final[str] = "en"
DEFAULT_THEME: Final[str] = "dark"


def get_resource_path(relative_path: str) -> Path:
    """Resolve a resource path that works both in source and compiled builds.

    In Nuitka onefile mode, resources are extracted to a temporary directory
    that `__file__` points to. For PyInstaller onefile, `sys._MEIPASS` is used.

    Args:
        relative_path: Path relative to the project root (e.g. ``"styles/light_theme.qss"``).

    Returns:
        Absolute ``Path`` to the resource file.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # PyInstaller one-file mode
        base = Path(sys._MEIPASS)
    else:
        # Source mode or Nuitka (both standalone and one-file mode)
        # Nuitka correctly sets __file__ to the temp dir in one-file mode
        # or the dist dir in standalone mode.
        base = Path(__file__).resolve().parent

    return base / relative_path
