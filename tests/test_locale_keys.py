import json

import pytest

from app_config import get_resource_path
from locales.i18n_manager import init, set_language, tr

LOCALES_DIR = get_resource_path("locales")


def _flatten_keys(data: dict, prefix: str = "") -> set[str]:
    keys = set()
    for k, v in data.items():
        full_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            keys.update(_flatten_keys(v, full_key))
        else:
            keys.add(full_key)
    return keys


@pytest.fixture(autouse=True)
def reset_i18n():
    init("en")
    yield
    init("en")


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


class TestTranslationMechanism:

    def test_language_switch_changes_result(self):
        init("en")
        en_result = tr("tabs.editor")

        set_language("ja")
        ja_result = tr("tabs.editor")

        set_language("id")
        id_result = tr("tabs.editor")

        assert en_result != "tabs.editor"
        assert ja_result != "tabs.editor"
        assert id_result != "tabs.editor"

        assert len({en_result, ja_result, id_result}) >= 2

    def test_tr_interpolation(self):
        init("en")
        formatted = tr("editor.label.super_skill", n=99)
        assert "99" in formatted
        assert "{n}" not in formatted
        assert "editor.label" not in formatted

    def test_tr_returns_default_when_key_missing(self):
        init("en")
        result = tr("nonexistent.key.here", default="Fallback")
        assert result == "Fallback"

    def test_tr_returns_key_when_no_default(self):
        init("en")
        result = tr("nonexistent.key.here")
        assert result == "nonexistent.key.here"