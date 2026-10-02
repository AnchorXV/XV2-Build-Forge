"""
DBXV2 Build Forge — Internationalisation Manager.

Provides a global ``tr(key, **kwargs)`` function that looks up UI strings
from the active locale JSON file, with automatic fallback to English when
a key is missing (PRD §3.8).
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from app_config import DEFAULT_LANGUAGE, get_resource_path

logger = logging.getLogger(__name__)

# ── Module-level state ────────────────────────────────────────────────
_current_lang: str = DEFAULT_LANGUAGE
_strings: dict[str, Any] = {}
_fallback_strings: dict[str, Any] = {}  # Always English


def _load_locale(lang_code: str) -> dict[str, Any]:
    """Load a locale JSON file from the ``locales/`` resource directory.

    Args:
        lang_code: Two-letter language code (``"en"``, ``"id"``, ``"ja"``).

    Returns:
        Parsed dict tree, or empty dict on failure.
    """
    locale_path = get_resource_path(f"locales/{lang_code}.json")
    try:
        with open(locale_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Failed to load locale '%s' from %s: %s", lang_code, locale_path, exc)
        return {}


def init(language: Optional[str] = None) -> None:
    """Initialise (or re-initialise) the i18n system.

    Must be called once at application startup.  Can be called again
    when the user changes language via Settings.

    Args:
        language: Language code to activate.  Defaults to ``"en"``.
    """
    global _current_lang, _strings, _fallback_strings  # noqa: PLW0603

    _current_lang = language or DEFAULT_LANGUAGE

    # Always load English as fallback
    _fallback_strings = _load_locale("en")

    if _current_lang == "en":
        _strings = _fallback_strings
    else:
        _strings = _load_locale(_current_lang)
        if not _strings:
            logger.warning("Locale '%s' unavailable; falling back to English.", _current_lang)
            _strings = _fallback_strings

    logger.info("i18n initialised: language=%s", _current_lang)


def set_language(lang_code: str) -> None:
    """Switch the active language at runtime.

    Args:
        lang_code: Two-letter language code.
    """
    init(lang_code)


def get_language() -> str:
    """Return the currently active language code."""
    return _current_lang


def tr(key: str, default: Optional[str] = None, **kwargs: Any) -> str:
    """Translate a dotted key path into a localised string.

    Supports Python ``.format()``-style placeholders in the locale
    strings, e.g. ``tr("editor.message.save_success", sheet="Goku")``.

    Lookup order:
        1. Active locale (``_strings``).
        2. English fallback (``_fallback_strings``).
        3. The ``default`` argument, if provided.
        4. The raw key itself — so the UI never shows blank.

    Args:
        key: Dot-separated key path (e.g. ``"editor.label.character_name"``).
        default: Fallback string used if the key is missing in every locale.
        **kwargs: Format parameters to substitute into the string.

    Returns:
        The localised (and formatted) string.

    Examples:
        >>> tr("editor.label.character_name")
        'Character Name:'
        >>> tr("editor.message.save_success", sheet="Goku")
        "Preset entry has been saved to table: 'Goku'"
        >>> tr("nonexistent.key", default="Fallback")
        'Fallback'
    """
    result = _resolve(key, _strings)
    if result is None:
        result = _resolve(key, _fallback_strings)
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
    """Walk a dotted key path through a nested dict.

    Returns ``None`` if any segment is missing or the leaf is not a string.
    """
    parts = key.split(".")
    node: Any = tree
    for part in parts:
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return None
    return node if isinstance(node, str) else None