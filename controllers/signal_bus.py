from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class SignalBus(QObject):

    data_changed = Signal()
    load_entry_to_editor = Signal(object, str)


signal_bus = SignalBus()