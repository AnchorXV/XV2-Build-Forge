from __future__ import annotations

import copy
import logging
from typing import Any

from PySide6.QtGui import QUndoCommand

from controllers.signal_bus import signal_bus
from models.schemas import PresetEntry

logger = logging.getLogger(__name__)

def _register_entry_to_cache(
    store,
    entry: PresetEntry,
    target_sheet: str,
) -> None:
    """Register character, skills, dan super soul baru dari entry ke dropdown_cache.

    Dipanggil dari Add dan Edit command. Owner Super Soul hanya diisi saat
    entry baru dibuat, tidak menimpa owner yang sudah ada.
    Tidak save ke disk — caller yang bertanggung jawab save.
    """
    tables = store.dropdown_cache.get("table_names", [])
    if target_sheet and target_sheet not in tables:
        tables.append(target_sheet)

    if entry.character_name:
        chars = store.dropdown_cache.get("characters", [])
        if not any(c.get("name") == entry.character_name for c in chars):
            chars.append({
                "code": entry.character_id if entry.character_id else "MOD",
                "name": entry.character_name,
                "is_playable": True,
            })

    def _register_skill(category: str, skill_name: str) -> None:
        if not skill_name:
            return
        skills = store.dropdown_cache.get(category, [])
        if not any(s.get("name") == skill_name for s in skills):
            skills.append({
                "name": skill_name,
                "is_cac": False,
                "skill_type": "",
                "ki_used": None,
                "note": "",
            })

    for s in entry.super_skills:
        _register_skill("super_skills", s)
    for s in entry.ultimate_skills:
        _register_skill("ultimate_skills", s)
    _register_skill("awoken_skills", entry.awoken_skill)
    _register_skill("evasive_skills", entry.evasive_skill)

    if entry.super_soul:
        souls = store.dropdown_cache.get("super_souls", [])
        if not any(s.get("name") == entry.super_soul for s in souls):
            souls.append({
                "name": entry.super_soul,
                "owner": entry.character_name or "",
                "effect_1": "",
                "effect_2": "",
                "limit_burst": "",
            })

    if entry.source:
        sources = store.dropdown_cache.get("sources", [])
        if not any(s.get("name") == entry.source for s in sources):
            sources.append({
                "name": entry.source,
                "source_type": "",
                "day": None,
                "month": None,
                "year": None,
            })

class AddPresetEntryCommand(QUndoCommand):

    def __init__(self, data_store, sheet_name: str, entry: PresetEntry) -> None:
        super().__init__(f"Add Preset '{entry.character_name}' to '{sheet_name}'")
        self._store = data_store
        self._sheet = sheet_name
        self._entry = entry
        self._created_sheet = False

    def redo(self) -> None:
        if self._sheet not in self._store.rosters:
            self._store.rosters[self._sheet] = []
            tnames = self._store.dropdown_cache.get("table_names", [])
            if self._sheet not in tnames:
                tnames.append(self._sheet)
            self._created_sheet = True

        presets = self._store.rosters[self._sheet]
        if not any(p.entry_id == self._entry.entry_id for p in presets):
            presets.append(self._entry)

        self._store.save()
        signal_bus.data_changed.emit()

    def undo(self) -> None:
        presets = self._store.rosters.get(self._sheet, [])
        for i, p in enumerate(presets):
            if p.entry_id == self._entry.entry_id:
                presets.pop(i)
                break

        if self._created_sheet and not self._store.rosters.get(self._sheet):
            self._store.rosters.pop(self._sheet, None)
            tnames = self._store.dropdown_cache.get("table_names", [])
            if self._sheet in tnames:
                tnames.remove(self._sheet)

        self._store.save()
        signal_bus.data_changed.emit()


class AddPresetWithAutoRegisterCommand(QUndoCommand):

    def __init__(self, data_store, sheet_name: str, entry: PresetEntry) -> None:
        super().__init__(f"Add Preset '{entry.character_name}' to '{sheet_name}'")
        self._store = data_store
        self._sheet = sheet_name
        self._entry = entry
        self._cache_before: dict[str, list[Any]] | None = None
        self._add_cmd = AddPresetEntryCommand(data_store, sheet_name, entry)

    def redo(self) -> None:
        if self._cache_before is None:
            self._cache_before = copy.deepcopy(self._store.dropdown_cache)

        _register_entry_to_cache(self._store, self._entry, self._sheet)
        self._add_cmd.redo()

    def undo(self) -> None:
        self._add_cmd.undo()

        if self._cache_before is not None:
            self._store.dropdown_cache = copy.deepcopy(self._cache_before)
            self._store.save()
            signal_bus.data_changed.emit()

class EditPresetWithAutoRegisterCommand(QUndoCommand):

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
        self._cache_before: dict[str, list[Any]] | None = None
        self._edit_cmd = EditPresetEntryCommand(data_store, sheet_name, old_entry, new_entry)

    def redo(self) -> None:
        if self._cache_before is None:
            self._cache_before = copy.deepcopy(self._store.dropdown_cache)

        _register_entry_to_cache(self._store, self._new, self._sheet)
        self._edit_cmd.redo()

    def undo(self) -> None:
        self._edit_cmd.undo()

        if self._cache_before is not None:
            self._store.dropdown_cache = copy.deepcopy(self._cache_before)
            self._store.save()
            signal_bus.data_changed.emit()

class EditPresetEntryCommand(QUndoCommand):

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

    def __init__(self, data_store, sheet_name: str, entry: PresetEntry, index: int) -> None:
        super().__init__(f"Delete Preset '{entry.character_name}' from '{sheet_name}'")
        self._store = data_store
        self._sheet = sheet_name
        self._entry = entry
        self._index = index

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
        idx = min(self._index, len(presets))
        presets.insert(idx, self._entry)
        self._store.save()
        signal_bus.data_changed.emit()


class AddSheetCommand(QUndoCommand):

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

    def __init__(self, data_store, sheet_name: str) -> None:
        super().__init__(f"Delete Sheet '{sheet_name}'")
        self._store = data_store
        self._name = sheet_name
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
        if self._sheet is not None:
            self._store.sheets_meta.setdefault(self._sheet, {"note": "", "tags": []})
            self._store.sheets_meta[self._sheet]["note"] = note
            self._store.sheets_meta[self._sheet]["tags"] = list(tags)
            self._store.save()
            signal_bus.data_changed.emit()


class RenameSheetCommand(QUndoCommand):

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
        if from_name in self._store.sheets_meta:
            self._store.sheets_meta[to_name] = self._store.sheets_meta.pop(from_name)
        tnames = self._store.dropdown_cache.get("table_names", [])
        if from_name in tnames:
            tnames[tnames.index(from_name)] = to_name
        self._store.save()
        signal_bus.data_changed.emit()


class DuplicateSheetCommand(QUndoCommand):

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
            d["entry_id"] = str(uuid.uuid4())
            cloned.append(PresetEntry.from_dict(d))

        self._store.rosters[self._new_name] = cloned
        self._store.sheets_meta.setdefault(
            self._new_name,
            dict(self._store.sheets_meta.get(self._source, {"note": "", "tags": []})),
        )
        tnames = self._store.dropdown_cache.get("table_names", [])
        if self._new_name not in tnames:
            tnames.append(self._new_name)
        self._store.save()
        signal_bus.data_changed.emit()

    def undo(self) -> None:
        self._store.rosters.pop(self._new_name, None)
        self._store.sheets_meta.pop(self._new_name, None)
        tnames = self._store.dropdown_cache.get("table_names", [])
        if self._new_name in tnames:
            tnames.remove(self._new_name)
        self._store.save()
        signal_bus.data_changed.emit()


class AddCacheItemCommand(QUndoCommand):

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
        for i in range(len(items) - 1, -1, -1):
            if items[i] is self._item or items[i] == self._item:
                items.pop(i)
                break
        self._store.save()
        signal_bus.data_changed.emit()


class EditCacheItemCommand(QUndoCommand):

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


class BulkEditCommand(QUndoCommand):

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
        self._old_values = old_values

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
        elif field == "source":
            entry.source = value

    @staticmethod
    def get_field_value(entry: PresetEntry, field_name: str) -> str:
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
        elif field_name == "source":
            return entry.source
        return ""


class ReorderPresetsCommand(QUndoCommand):

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
        self._old_order = old_order
        self._new_order = new_order

    def redo(self) -> None:
        self._reorder(self._new_order)

    def undo(self) -> None:
        self._reorder(self._old_order)

    def _reorder(self, order: list[str]) -> None:
        presets = self._store.rosters.get(self._sheet, [])
        id_to_preset = {p.entry_id: p for p in presets}
        reordered = [id_to_preset[eid] for eid in order if eid in id_to_preset]
        seen = set(order)
        for p in presets:
            if p.entry_id not in seen:
                reordered.append(p)
        self._store.rosters[self._sheet] = reordered
        self._store.save()
        signal_bus.data_changed.emit()


class ReorderSheetsCommand(QUndoCommand):

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
        for sheet_name in order:
            if sheet_name in self._store.rosters:
                new_rosters[sheet_name] = self._store.rosters[sheet_name]
        for sheet_name, presets in self._store.rosters.items():
            if sheet_name not in new_rosters:
                new_rosters[sheet_name] = presets

        self._store.rosters = new_rosters

        tnames = self._store.dropdown_cache.get("table_names", [])
        new_tnames = [name for name in order if name in tnames]
        for name in tnames:
            if name not in new_tnames:
                new_tnames.append(name)
        self._store.dropdown_cache["table_names"] = new_tnames

        self._store.save()
        signal_bus.data_changed.emit()