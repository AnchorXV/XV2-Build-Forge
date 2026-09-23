"""
DBXV2 Build Forge — Theme Manager.

Loads QSS stylesheets and applies them to the running ``QApplication``.
Supports Light (default), Dark, and System-follows-OS modes (PRD §3.7).
"""

from __future__ import annotations

import enum
import logging
import sys
from typing import Optional

from PySide6.QtWidgets import QApplication

from app_config import get_resource_path

logger = logging.getLogger(__name__)


class ThemeMode(enum.Enum):
    """Available application themes."""
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


def _detect_system_prefers_dark() -> bool:
    """Detect whether the OS prefers a dark colour scheme.

    Tries the Qt 6.5+ ``QStyleHints.colorScheme()`` API first,
    falling back to reading the Windows registry.
    """
    try:
        from PySide6.QtGui import QGuiApplication
        hints = QGuiApplication.styleHints()
        if hasattr(hints, "colorScheme"):
            from PySide6.QtCore import Qt
            return hints.colorScheme() == Qt.ColorScheme.Dark
    except Exception:
        pass

    # Windows registry fallback
    if sys.platform == "win32":
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            )
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            return value == 0  # 0 = dark, 1 = light
        except Exception:
            pass

    return False  # Default to light if detection fails


def _load_qss(theme_name: str) -> str:
    """Read a QSS file from the ``styles/`` resource directory.

    Args:
        theme_name: ``"light"`` or ``"dark"``.

    Returns:
        The stylesheet string, or empty string on failure.
    """
    qss_path = get_resource_path(f"styles/{theme_name}_theme.qss")
    try:
        with open(qss_path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError as exc:
        logger.warning("Failed to load QSS file %s: %s", qss_path, exc)
        return ""


def apply_theme(app: QApplication, mode: ThemeMode) -> None:
    """Apply the given theme to the running application.

    Changes take effect immediately without requiring an app restart.

    Args:
        app: The running ``QApplication`` instance.
        mode: The desired theme mode.
    """
    if mode == ThemeMode.SYSTEM:
        effective = "dark" if _detect_system_prefers_dark() else "light"
    else:
        effective = mode.value

    qss = _load_qss(effective)
    app.setStyleSheet(qss)
    logger.info("Applied theme: %s (effective: %s)", mode.value, effective)


def resolve_theme_mode(setting: Optional[str]) -> ThemeMode:
    """Convert a settings string to a ``ThemeMode`` enum.

    Args:
        setting: Raw string from ``settings.json`` (e.g. ``"dark"``).

    Returns:
        The matching ``ThemeMode``, defaulting to ``LIGHT``.
    """
    try:
        return ThemeMode(setting)
    except (ValueError, KeyError):
        return ThemeMode.DARK
