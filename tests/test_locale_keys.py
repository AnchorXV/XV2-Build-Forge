"""
Unit tests for locales consistency (PRD §3.8).
Ensures all supported languages have 100% matching key paths.
"""

import json
from pathlib import Path
import pytest

from locales.i18n_manager import init, set_language, tr

LOCALES_DIR = Path(__file__).resolve().parent.parent / "locales"


def _flatten_keys(data: dict, prefix: str = "") -> set[str]:
    """Recursively collect all leaf key paths (e.g. 'editor.label.character_name')."""
    keys = set()
    for k, v in data.items():
        full_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            keys.update(_flatten_keys(v, full_key))
        else:
            keys.add(full_key)
    return keys


class TestLocaleConsistency:
    @pytest.fixture
    def en_keys(self) -> set[str]:
        with open(LOCALES_DIR / "en.json", "r", encoding="utf-8") as f:
            return _flatten_keys(json.load(f))

    @pytest.fixture
    def id_keys(self) -> set[str]:
        with open(LOCALES_DIR / "id.json", "r", encoding="utf-8") as f:
            return _flatten_keys(json.load(f))

    @pytest.fixture
    def ja_keys(self) -> set[str]:
        with open(LOCALES_DIR / "ja.json", "r", encoding="utf-8") as f:
            return _flatten_keys(json.load(f))

    def test_indonesian_has_all_english_keys(self, en_keys, id_keys):
        missing = en_keys - id_keys
        assert not missing, f"id.json is missing keys present in en.json: {missing}"

    def test_english_has_all_indonesian_keys(self, en_keys, id_keys):
        extra = id_keys - en_keys
        assert not extra, f"id.json has extra keys not in en.json: {extra}"

    def test_japanese_has_all_english_keys(self, en_keys, ja_keys):
        missing = en_keys - ja_keys
        assert not missing, f"ja.json is missing keys present in en.json: {missing}"

    def test_english_has_all_japanese_keys(self, en_keys, ja_keys):
        extra = ja_keys - en_keys
        assert not extra, f"ja.json has extra keys not in en.json: {extra}"

    def test_tr_functionality(self):
        init("en")
        assert tr("app.title") == "DBXV2 Build Forge"
        set_language("ja")
        assert tr("tabs.editor") == "スキルセットエディタ"
        set_language("id")
        assert tr("tabs.editor") == "Editor Skillset"

    def test_tr_interpolation(self):
        init("en")
        formatted = tr("editor.label.super_skill", n=2)
        assert "2" in formatted
