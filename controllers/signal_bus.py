"""
DBXV2 Build Forge — Centralised Signal Bus.

All cross-component communication goes through this singleton QObject.
Views and controllers connect to these signals rather than calling each
other directly, decoupling the MVC layers (PRD §2.2).
"""

from __future__ import annotations

from typing import Any
from PySide6.QtCore import QObject, Signal


class SignalBus(QObject):
    """Application-wide event bus using Qt Signals."""

    # Data mutation signals
    data_changed = Signal()
    dropdown_cache_changed = Signal()
    roster_changed = Signal()
    data_saved = Signal()

    # Editor workflow signals
    load_entry_to_editor = Signal(object, str)  # (PresetEntry, sheet_name)
    preset_load_requested = Signal(dict)

    # App settings signals
    language_changed = Signal(str)
    theme_changed = Signal(object)  # ThemeMode or str

    # General signals
    sheet_selected = Signal(str)
    status_message = Signal(str)


# Global singleton instance for module-level import
signal_bus = SignalBus()
