"""
DBXV2 Build Forge — Undo/Redo Command Classes.

``QUndoCommand`` subclasses for every CRUD operation in the application.
Each command stores the minimal state needed to undo/redo the operation,
and emits ``signal_bus.data_changed`` on both undo and redo so views
refresh automatically.

All commands follow the same pattern:
    1. ``redo()`` applies the mutation via ``AppDataStore`` methods.
    2. ``undo()`` reverses the mutation.
    3. Both emit ``signal_bus.data_changed.emit()`` to trigger UI refresh.
"""

from __future__ import annotations

import copy
import logging
from typing import Any, Optional

from PySide6.QtGui import QUndoCommand

from controllers.signal_bus import signal_bus
from models.schemas import PresetEntry

logger = logging.getLogger(__name__)


# ── Preset Entry Commands ─────────────────────────────────────────────


class AddPresetEntryCommand(QUndoCommand):
    """Add a new preset entry to a roster sheet."""

    def __init__(self, data_store, sheet_name: str, entry: PresetEntry) -> None:
        super().__init__(f"Add Preset '{entry.character_name}' to '{sheet_name}'")
        self._store = data_store
        self._sheet = sheet_name
        self._entry = entry

    def redo(self) -> None:
        if self._sheet not in self._store.rosters:
            self._store.rosters[self._sheet] = []
            tnames = self._store.dropdown_cache.get("table_names", [])
            if self._sheet not in tnames:
                tnames.append(self._sheet)
        self._store.rosters[self._sheet].append(self._entry)
        self._store.save()
        signal_bus.data_changed.emit()

    def undo(self) -> None:
        presets = self._store.rosters.get(self._sheet, [])
        for i, p in enumerate(presets):
            if p.entry_id == self._entry.entry_id:
                presets.pop(i)
                break
        self._store.save()
        signal_bus.data_changed.emit()


class EditPresetEntryCommand(QUndoCommand):
    """Edit an existing preset entry in-place (swap old ↔ new)."""

    def __init__(
        self,
        data_store,
        sheet_name: str,
        old_entry: PresetEntry,
        new_entry: PresetEntry,
    ) -> None:
        super().__init__(f"Edit Preset '{new_entry.character_name}' in '{sheet_name}'")
        self._store = data_store
        self._sheet = sheet_name
        self._old = old_entry
        self._new = new_entry

    def redo(self) -> None:
        self._swap(self._old.entry_id, self._new)

    def undo(self) -> None:
        self._swap(self._new.entry_id, self._old)

    def _swap(self, target_id: str, replacement: PresetEntry) -> None:
        presets = self._store.rosters.get(self._sheet, [])
        for i, p in enumerate(presets):
            if p.entry_id == target_id:
                presets[i] = replacement
                break
        self._store.save()
        signal_bus.data_changed.emit()


class DeletePresetEntryCommand(QUndoCommand):
    """Delete a specific preset entry from a sheet."""

    def __init__(self, data_store, sheet_name: str, entry: PresetEntry, index: int) -> None:
        super().__init__(f"Delete Preset '{entry.character_name}' from '{sheet_name}'")
        self._store = data_store
        self._sheet = sheet_name
        self._entry = entry
        self._index = index  # Original position for undo re-insert

    def redo(self) -> None:
        presets = self._store.rosters.get(self._sheet, [])
        for i, p in enumerate(presets):
            if p.entry_id == self._entry.entry_id:
                presets.pop(i)
                break
        self._store.save()
        signal_bus.data_changed.emit()

    def undo(self) -> None:
        presets = self._store.rosters.get(self._sheet, [])
        # Re-insert at original position (clamped to valid range)
        idx = min(self._index, len(presets))
        presets.insert(idx, self._entry)
        self._store.save()
        signal_bus.data_changed.emit()


# ── Sheet Commands ────────────────────────────────────────────────────


class AddSheetCommand(QUndoCommand):
    """Create a new empty roster sheet."""

    def __init__(self, data_store, sheet_name: str) -> None:
        super().__init__(f"Create Sheet '{sheet_name}'")
        self._store = data_store
        self._name = sheet_name

    def redo(self) -> None:
        self._store.rosters[self._name] = []
        tnames = self._store.dropdown_cache.get("table_names", [])
        if self._name not in tnames:
            tnames.append(self._name)
        self._store.save()
        signal_bus.data_changed.emit()

    def undo(self) -> None:
        self._store.rosters.pop(self._name, None)
        tnames = self._store.dropdown_cache.get("table_names", [])
        if self._name in tnames:
            tnames.remove(self._name)
        self._store.save()
        signal_bus.data_changed.emit()


class DeleteSheetCommand(QUndoCommand):
    """Delete an entire roster sheet (preserving data for undo)."""

    def __init__(self, data_store, sheet_name: str) -> None:
        super().__init__(f"Delete Sheet '{sheet_name}'")
        self._store = data_store
        self._name = sheet_name
        # Deep copy presets for undo restoration
        self._backup: list[PresetEntry] = list(data_store.rosters.get(sheet_name, []))

    def redo(self) -> None:
        self._store.rosters.pop(self._name, None)
        tnames = self._store.dropdown_cache.get("table_names", [])
        if self._name in tnames:
            tnames.remove(self._name)
        self._store.save()
        signal_bus.data_changed.emit()

    def undo(self) -> None:
        self._store.rosters[self._name] = list(self._backup)
        tnames = self._store.dropdown_cache.get("table_names", [])
        if self._name not in tnames:
            tnames.append(self._name)
        self._store.save()
        signal_bus.data_changed.emit()


class EditSheetNoteTagsCommand(QUndoCommand):
    """Edit the note and tags of a roster sheet."""

    def __init__(self, data_store, sheet_name: str, old_meta: dict, new_meta: dict) -> None:
        super().__init__(f"Edit Note/Tags for '{sheet_name}'")
        self._store = data_store
        self._sheet = sheet_name
        self._old_note = old_meta.get("note", "")
        self._old_tags = old_meta.get("tags", [])
        self._new_note = new_meta.get("note", "")
        self._new_tags = new_meta.get("tags", [])

    def redo(self) -> None:
        self._apply(self._new_note, self._new_tags)

    def undo(self) -> None:
        self._apply(self._old_note, self._old_tags)

    def _apply(self, note: str, tags: list[str]) -> None:
        sheet_obj = self._store.get_sheet_obj(self._sheet)
        if sheet_obj:
            sheet_obj.note = note
            sheet_obj.tags = list(tags)
            self._store.save()
            signal_bus.data_changed.emit()


class RenameSheetCommand(QUndoCommand):
    """Rename a roster sheet."""

    def __init__(self, data_store, old_name: str, new_name: str) -> None:
        super().__init__(f"Rename Sheet '{old_name}' → '{new_name}'")
        self._store = data_store
        self._old = old_name
        self._new = new_name

    def redo(self) -> None:
        self._do_rename(self._old, self._new)

    def undo(self) -> None:
        self._do_rename(self._new, self._old)

    def _do_rename(self, from_name: str, to_name: str) -> None:
        if from_name in self._store.rosters:
            self._store.rosters[to_name] = self._store.rosters.pop(from_name)
        tnames = self._store.dropdown_cache.get("table_names", [])
        if from_name in tnames:
            tnames[tnames.index(from_name)] = to_name
        self._store.save()
        signal_bus.data_changed.emit()


class DuplicateSheetCommand(QUndoCommand):
    """Duplicate a roster sheet with new entry_ids for all presets."""

    def __init__(self, data_store, source_name: str, new_name: str) -> None:
        super().__init__(f"Duplicate Sheet '{source_name}' → '{new_name}'")
        self._store = data_store
        self._source = source_name
        self._new_name = new_name

    def redo(self) -> None:
        import uuid

        source_presets = self._store.rosters.get(self._source, [])
        cloned: list[PresetEntry] = []
        for p in source_presets:
            d = p.to_dict()
            d["entry_id"] = str(uuid.uuid4())  # Generate fresh UUID
            cloned.append(PresetEntry.from_dict(d))

        self._store.rosters[self._new_name] = cloned
        tnames = self._store.dropdown_cache.get("table_names", [])
        if self._new_name not in tnames:
            tnames.append(self._new_name)
        self._store.save()
        signal_bus.data_changed.emit()

    def undo(self) -> None:
        self._store.rosters.pop(self._new_name, None)
        tnames = self._store.dropdown_cache.get("table_names", [])
        if self._new_name in tnames:
            tnames.remove(self._new_name)
        self._store.save()
        signal_bus.data_changed.emit()


# ── Database Cache Commands ───────────────────────────────────────────


class AddCacheItemCommand(QUndoCommand):
    """Add a new item to a database cache category."""

    def __init__(self, data_store, category: str, item: dict[str, Any]) -> None:
        name = item.get("name", "???")
        super().__init__(f"Add {category} '{name}'")
        self._store = data_store
        self._category = category
        self._item = item

    def redo(self) -> None:
        items = self._store.dropdown_cache.get(self._category, [])
        items.append(self._item)
        self._store.save()
        signal_bus.data_changed.emit()

    def undo(self) -> None:
        items = self._store.dropdown_cache.get(self._category, [])
        # Remove the last occurrence that matches
        for i in range(len(items) - 1, -1, -1):
            if items[i] is self._item or items[i] == self._item:
                items.pop(i)
                break
        self._store.save()
        signal_bus.data_changed.emit()


class EditCacheItemCommand(QUndoCommand):
    """Edit an existing item in a database cache category."""

    def __init__(
        self,
        data_store,
        category: str,
        index: int,
        old_item: dict[str, Any],
        new_item: dict[str, Any],
    ) -> None:
        name = new_item.get("name", "???")
        super().__init__(f"Edit {category} '{name}'")
        self._store = data_store
        self._category = category
        self._index = index
        self._old = old_item
        self._new = new_item

    def redo(self) -> None:
        items = self._store.dropdown_cache.get(self._category, [])
        if 0 <= self._index < len(items):
            items[self._index] = self._new
        self._store.save()
        signal_bus.data_changed.emit()

    def undo(self) -> None:
        items = self._store.dropdown_cache.get(self._category, [])
        if 0 <= self._index < len(items):
            items[self._index] = self._old
        self._store.save()
        signal_bus.data_changed.emit()


class DeleteCacheItemCommand(QUndoCommand):
    """Delete an item from a database cache category."""

    def __init__(
        self,
        data_store,
        category: str,
        index: int,
        item: dict[str, Any],
    ) -> None:
        name = item.get("name", "???")
        super().__init__(f"Delete {category} '{name}'")
        self._store = data_store
        self._category = category
        self._index = index
        self._item = item

    def redo(self) -> None:
        items = self._store.dropdown_cache.get(self._category, [])
        if 0 <= self._index < len(items):
            items.pop(self._index)
        self._store.save()
        signal_bus.data_changed.emit()

    def undo(self) -> None:
        items = self._store.dropdown_cache.get(self._category, [])
        idx = min(self._index, len(items))
        items.insert(idx, self._item)
        self._store.save()
        signal_bus.data_changed.emit()


# ── Bulk Edit Command ─────────────────────────────────────────────────


class BulkEditCommand(QUndoCommand):
    """Apply a single field change to multiple preset entries at once.

    Stores the old values for each affected entry so undo restores them
    individually.
    """

    def __init__(
        self,
        data_store,
        sheet_name: str,
        entry_ids: list[str],
        field_name: str,
        new_value: str,
        old_values: dict[str, str],
    ) -> None:
        super().__init__(f"Bulk Edit {len(entry_ids)} presets: {field_name} = '{new_value}'")
        self._store = data_store
        self._sheet = sheet_name
        self._entry_ids = entry_ids
        self._field = field_name
        self._new_value = new_value
        self._old_values = old_values  # {entry_id: old_field_value}

    def redo(self) -> None:
        self._apply_values({eid: self._new_value for eid in self._entry_ids})

    def undo(self) -> None:
        self._apply_values(self._old_values)

    def _apply_values(self, values: dict[str, str]) -> None:
        presets = self._store.rosters.get(self._sheet, [])
        for p in presets:
            if p.entry_id in values:
                val = values[p.entry_id]
                self._set_field(p, val)
        self._store.save()
        signal_bus.data_changed.emit()

    def _set_field(self, entry: PresetEntry, value: str) -> None:
        """Set a field on a PresetEntry by field name."""
        field = self._field
        if field.startswith("super_skill_"):
            idx = int(field.split("_")[-1]) - 1
            skills = list(entry.super_skills)
            if 0 <= idx < len(skills):
                skills[idx] = value
                entry.super_skills = skills
        elif field.startswith("ultimate_skill_"):
            idx = int(field.split("_")[-1]) - 1
            skills = list(entry.ultimate_skills)
            if 0 <= idx < len(skills):
                skills[idx] = value
                entry.ultimate_skills = skills
        elif field == "awoken_skill":
            entry.awoken_skill = value
        elif field == "evasive_skill":
            entry.evasive_skill = value
        elif field == "super_soul":
            entry.super_soul = value
        elif field == "character_name":
            entry.character_name = value
        elif field == "character_id":
            entry.character_id = value
        elif field == "costume_name":
            entry.costume_name = value

    @staticmethod
    def get_field_value(entry: PresetEntry, field_name: str) -> str:
        """Read a field value from a PresetEntry by field name."""
        if field_name.startswith("super_skill_"):
            idx = int(field_name.split("_")[-1]) - 1
            return entry.super_skills[idx] if idx < len(entry.super_skills) else ""
        elif field_name.startswith("ultimate_skill_"):
            idx = int(field_name.split("_")[-1]) - 1
            return entry.ultimate_skills[idx] if idx < len(entry.ultimate_skills) else ""
        elif field_name == "awoken_skill":
            return entry.awoken_skill
        elif field_name == "evasive_skill":
            return entry.evasive_skill
        elif field_name == "super_soul":
            return entry.super_soul
        elif field_name == "character_name":
            return entry.character_name
        elif field_name == "character_id":
            return entry.character_id
        elif field_name == "costume_name":
            return entry.costume_name
        return ""


# ── Reorder Commands ──────────────────────────────────────────────────


class ReorderPresetsCommand(QUndoCommand):
    """Reorder presets within a sheet (drag-and-drop)."""

    def __init__(
        self,
        data_store,
        sheet_name: str,
        old_order: list[str],
        new_order: list[str],
    ) -> None:
        super().__init__(f"Reorder presets in '{sheet_name}'")
        self._store = data_store
        self._sheet = sheet_name
        self._old_order = old_order  # List of entry_ids in old order
        self._new_order = new_order  # List of entry_ids in new order

    def redo(self) -> None:
        self._reorder(self._new_order)

    def undo(self) -> None:
        self._reorder(self._old_order)

    def _reorder(self, order: list[str]) -> None:
        presets = self._store.rosters.get(self._sheet, [])
        id_to_preset = {p.entry_id: p for p in presets}
        reordered = [id_to_preset[eid] for eid in order if eid in id_to_preset]
        # Append any entries not in the order list (safety)
        seen = set(order)
        for p in presets:
            if p.entry_id not in seen:
                reordered.append(p)
        self._store.rosters[self._sheet] = reordered
        self._store.save()
        signal_bus.data_changed.emit()


class ReorderSheetsCommand(QUndoCommand):
    """Reorder roster sheets (drag-and-drop)."""

    def __init__(
        self,
        data_store,
        old_order: list[str],
        new_order: list[str],
    ) -> None:
        super().__init__("Reorder sheets")
        self._store = data_store
        self._old_order = old_order
        self._new_order = new_order

    def redo(self) -> None:
        self._reorder(self._new_order)

    def undo(self) -> None:
        self._reorder(self._old_order)

    def _reorder(self, order: list[str]) -> None:
        new_rosters = {}
        # Add keys in the new order
        for sheet_name in order:
            if sheet_name in self._store.rosters:
                new_rosters[sheet_name] = self._store.rosters[sheet_name]
        # Append any missing keys (safety)
        for sheet_name, presets in self._store.rosters.items():
            if sheet_name not in new_rosters:
                new_rosters[sheet_name] = presets
                
        self._store.rosters = new_rosters
        
        # Also reorder dropdown_cache["table_names"]
        tnames = self._store.dropdown_cache.get("table_names", [])
        new_tnames = [name for name in order if name in tnames]
        for name in tnames:
            if name not in new_tnames:
                new_tnames.append(name)
        self._store.dropdown_cache["table_names"] = new_tnames
        
        self._store.save()
        signal_bus.data_changed.emit()
