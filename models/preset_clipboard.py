from __future__ import annotations

import uuid
from typing import Optional

from models.schemas import PresetEntry


class PresetClipboard:

    _instance: Optional["PresetClipboard"] = None

    def __init__(self) -> None:
        self._entries: list[PresetEntry] = []

    @classmethod
    def instance(cls) -> "PresetClipboard":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def set(self, entries: list[PresetEntry]) -> None:
        self._entries = [self._clone(e) for e in entries]

    def has_content(self) -> bool:
        return bool(self._entries)

    def count(self) -> int:
        return len(self._entries)

    def get_entries(self) -> list[PresetEntry]:
        return [self._clone(e) for e in self._entries]

    def clear(self) -> None:
        self._entries = []

    @staticmethod
    def clone_with_new_id(entry: PresetEntry) -> PresetEntry:
        d = entry.to_dict()
        d["entry_id"] = str(uuid.uuid4())
        return PresetEntry.from_dict(d)

    @staticmethod
    def _clone(entry: PresetEntry) -> PresetEntry:
        return PresetEntry.from_dict(entry.to_dict())