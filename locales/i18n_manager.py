from __future__ import annotations

import json
import logging
from typing import Any, Optional

from app_config import DEFAULT_LANGUAGE, get_resource_path

logger = logging.getLogger(__name__)

_current_lang: str = DEFAULT_LANGUAGE
_strings: dict[str, Any] = {}


def _load_locale(lang_code: str) -> dict[str, Any]:
    locale_path = get_resource_path(f"locales/{lang_code}.json")
    try:
        with open(locale_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Failed to load locale '%s' from %s: %s", lang_code, locale_path, exc)
        return {}


def init(language: Optional[str] = None) -> None:
    global _current_lang, _strings  # noqa: PLW0603
    _current_lang = language or DEFAULT_LANGUAGE
    _strings = _load_locale(_current_lang)
    logger.info("i18n initialised: language=%s", _current_lang)


def get_language() -> str:
    return _current_lang


def tr(key: str, default: Optional[str] = None, **kwargs: Any) -> str:
    result = _resolve(key, _strings)
    if result is None:
        logger.warning("Missing i18n key: '%s'", key)
        if default is None:
            return key
        result = default

    if kwargs:
        try:
            return result.format(**kwargs)
        except (KeyError, IndexError) as exc:
            logger.warning("Format error for key '%s': %s", key, exc)
            return result
    return result


def _resolve(key: str, tree: dict[str, Any]) -> Optional[str]:
    parts = key.split(".")
    node: Any = tree
    for part in parts:
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return None
    return node if isinstance(node, str) else None