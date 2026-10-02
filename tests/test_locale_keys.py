import json

import pytest

from app_config import get_resource_path
from locales.i18n_manager import init, tr

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


class TestLocaleFile:

    def test_english_locale_loads(self):
        with open(LOCALES_DIR / "en.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict)
        assert len(data) > 0

    def test_all_keys_resolve(self):
        with open(LOCALES_DIR / "en.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        all_keys = _flatten_keys(data)
        for key in all_keys:
            result = tr(key)
            assert result != key, f"Key '{key}' did not resolve"


class TestTranslationMechanism:

    def test_tr_returns_string_from_locale(self):
        init("en")
        result = tr("app.title")
        assert result == "DBXV2 Build Forge"

    def test_tr_interpolation(self):
        init("en")
        formatted = tr("editor.label.super_skill", n=99)
        assert "99" in formatted
        assert "{n}" not in formatted

    def test_tr_returns_default_when_key_missing(self):
        init("en")
        result = tr("nonexistent.key.here", default="Fallback")
        assert result == "Fallback"

    def test_tr_returns_key_when_no_default(self):
        init("en")
        result = tr("nonexistent.key.here")
        assert result == "nonexistent.key.here"