import pytest

from controllers.undo_commands import (
    AddCacheItemCommand,
    AddPresetEntryCommand,
    AddPresetWithAutoRegisterCommand,
    AddSheetCommand,
    BulkEditCommand,
    DeleteCacheItemCommand,
    DeletePresetEntryCommand,
    DeleteSheetCommand,
    DuplicateSheetCommand,
    EditCacheItemCommand,
    EditPresetEntryCommand,
    EditSheetNoteTagsCommand,
    RenameSheetCommand,
    ReorderPresetsCommand,
    ReorderSheetsCommand,
)
from models.data_store import AppDataStore
from models.schemas import PresetEntry


@pytest.fixture
def store(tmp_path):
    return AppDataStore(data_file=tmp_path / "data.json")


class TestAddPresetEntryCommand:

    def test_redo_undo_redo_cycle_on_new_sheet(self, store):
        entry = PresetEntry(character_name="Goku")
        cmd = AddPresetEntryCommand(store, "NewSheet", entry)

        cmd.redo()
        assert "NewSheet" in store.rosters
        assert len(store.rosters["NewSheet"]) == 1
        assert "NewSheet" in store.dropdown_cache["table_names"]

        cmd.undo()
        assert "NewSheet" not in store.rosters
        assert "NewSheet" not in store.dropdown_cache["table_names"]

        cmd.redo()
        assert "NewSheet" in store.rosters
        assert len(store.rosters["NewSheet"]) == 1

    def test_undo_does_not_remove_existing_sheet(self, store):
        store.create_sheet("ExistingSheet")
        entry = PresetEntry(character_name="Vegeta")
        cmd = AddPresetEntryCommand(store, "ExistingSheet", entry)

        cmd.redo()
        assert len(store.rosters["ExistingSheet"]) == 1

        cmd.undo()
        assert "ExistingSheet" in store.rosters
        assert len(store.rosters["ExistingSheet"]) == 0

    def test_redo_is_idempotent(self, store):
        entry = PresetEntry(character_name="Goku")
        cmd = AddPresetEntryCommand(store, "Sheet", entry)

        cmd.redo()
        cmd.redo()
        cmd.redo()
        assert len(store.rosters["Sheet"]) == 1


class TestEditPresetEntryCommand:

    def test_swap_and_restore(self, store):
        store.create_sheet("Sheet")
        original = PresetEntry(character_name="Goku")
        store.add_preset_entry("Sheet", original)

        updated = PresetEntry(character_name="Goku SSJ", entry_id=original.entry_id)
        cmd = EditPresetEntryCommand(store, "Sheet", original, updated)

        cmd.redo()
        assert store.rosters["Sheet"][0].character_name == "Goku SSJ"

        cmd.undo()
        assert store.rosters["Sheet"][0].character_name == "Goku"

        cmd.redo()
        assert store.rosters["Sheet"][0].character_name == "Goku SSJ"


class TestDeletePresetEntryCommand:

    def test_delete_and_reinsert_at_correct_position(self, store):
        store.create_sheet("Sheet")
        a = PresetEntry(character_name="A")
        b = PresetEntry(character_name="B")
        c = PresetEntry(character_name="C")
        for entry in (a, b, c):
            store.add_preset_entry("Sheet", entry)

        cmd = DeletePresetEntryCommand(store, "Sheet", b, index=1)

        cmd.redo()
        assert [p.character_name for p in store.rosters["Sheet"]] == ["A", "C"]

        cmd.undo()
        assert [p.character_name for p in store.rosters["Sheet"]] == ["A", "B", "C"]

    def test_undo_with_out_of_range_index_clamps(self, store):
        store.create_sheet("Sheet")
        a = PresetEntry(character_name="A")
        store.add_preset_entry("Sheet", a)

        cmd = DeletePresetEntryCommand(store, "Sheet", a, index=99)
        cmd.redo()
        assert len(store.rosters["Sheet"]) == 0

        cmd.undo()
        assert len(store.rosters["Sheet"]) == 1


class TestAddSheetCommand:

    def test_redo_undo_redo(self, store):
        cmd = AddSheetCommand(store, "TestSheet")

        cmd.redo()
        assert "TestSheet" in store.rosters
        assert "TestSheet" in store.dropdown_cache["table_names"]

        cmd.undo()
        assert "TestSheet" not in store.rosters
        assert "TestSheet" not in store.dropdown_cache["table_names"]

        cmd.redo()
        assert "TestSheet" in store.rosters


class TestDeleteSheetCommand:

    def test_delete_and_restore_with_presets(self, store):
        store.create_sheet("Sheet")
        store.add_preset_entry("Sheet", PresetEntry(character_name="Goku"))
        store.add_preset_entry("Sheet", PresetEntry(character_name="Vegeta"))

        cmd = DeleteSheetCommand(store, "Sheet")

        cmd.redo()
        assert "Sheet" not in store.rosters

        cmd.undo()
        assert "Sheet" in store.rosters
        assert len(store.rosters["Sheet"]) == 2
        assert [p.character_name for p in store.rosters["Sheet"]] == ["Goku", "Vegeta"]


class TestRenameSheetCommand:

    def test_rename_preserves_presets_and_meta(self, store):
        store.create_sheet("OldName")
        store.add_preset_entry("OldName", PresetEntry(character_name="Goku"))
        store.update_sheet_meta("OldName", "note", ["tag"])

        cmd = RenameSheetCommand(store, "OldName", "NewName")

        cmd.redo()
        assert "NewName" in store.rosters
        assert "OldName" not in store.rosters
        assert len(store.rosters["NewName"]) == 1
        assert store.sheets_meta["NewName"]["note"] == "note"
        assert "OldName" not in store.sheets_meta
        assert "NewName" in store.dropdown_cache["table_names"]
        assert "OldName" not in store.dropdown_cache["table_names"]

        cmd.undo()
        assert "OldName" in store.rosters
        assert "NewName" not in store.rosters
        assert store.sheets_meta["OldName"]["note"] == "note"


class TestDuplicateSheetCommand:

    def test_duplicate_generates_new_entry_ids(self, store):
        store.create_sheet("Source")
        original = PresetEntry(character_name="Goku")
        store.add_preset_entry("Source", original)

        cmd = DuplicateSheetCommand(store, "Source", "Copy")

        cmd.redo()
        assert "Copy" in store.rosters
        assert len(store.rosters["Copy"]) == 1
        assert store.rosters["Copy"][0].character_name == "Goku"
        assert store.rosters["Copy"][0].entry_id != original.entry_id

        cmd.undo()
        assert "Copy" not in store.rosters

    def test_duplicate_copies_meta(self, store):
        store.create_sheet("Source")
        store.update_sheet_meta("Source", "note", ["tag"])

        cmd = DuplicateSheetCommand(store, "Source", "Copy")
        cmd.redo()

        assert store.sheets_meta["Copy"]["note"] == "note"
        assert store.sheets_meta["Copy"]["tags"] == ["tag"]

        cmd.undo()
        assert "Copy" not in store.sheets_meta


class TestEditSheetNoteTagsCommand:

    def test_edit_and_restore(self, store):
        store.create_sheet("Sheet")
        store.update_sheet_meta("Sheet", "old note", ["old_tag"])

        old_meta = {"note": "old note", "tags": ["old_tag"]}
        new_meta = {"note": "new note", "tags": ["new_tag"]}
        cmd = EditSheetNoteTagsCommand(store, "Sheet", old_meta, new_meta)

        cmd.redo()
        assert store.sheets_meta["Sheet"]["note"] == "new note"
        assert store.sheets_meta["Sheet"]["tags"] == ["new_tag"]

        cmd.undo()
        assert store.sheets_meta["Sheet"]["note"] == "old note"
        assert store.sheets_meta["Sheet"]["tags"] == ["old_tag"]


class TestBulkEditCommand:

    def test_bulk_edit_super_skill_and_undo(self, store):
        store.create_sheet("Sheet")
        a = PresetEntry(character_name="A", super_skills=["OldSkill", "", "", ""])
        b = PresetEntry(character_name="B", super_skills=["", "", "", ""])
        store.add_preset_entry("Sheet", a)
        store.add_preset_entry("Sheet", b)

        old_values = {
            a.entry_id: "OldSkill",
            b.entry_id: "",
        }
        cmd = BulkEditCommand(
            store, "Sheet",
            entry_ids=[a.entry_id, b.entry_id],
            field_name="super_skill_1",
            new_value="NewSkill",
            old_values=old_values,
        )

        cmd.redo()
        assert store.rosters["Sheet"][0].super_skills[0] == "NewSkill"
        assert store.rosters["Sheet"][1].super_skills[0] == "NewSkill"

        cmd.undo()
        assert store.rosters["Sheet"][0].super_skills[0] == "OldSkill"
        assert store.rosters["Sheet"][1].super_skills[0] == ""

    def test_bulk_edit_character_name(self, store):
        store.create_sheet("Sheet")
        a = PresetEntry(character_name="A")
        store.add_preset_entry("Sheet", a)

        cmd = BulkEditCommand(
            store, "Sheet",
            entry_ids=[a.entry_id],
            field_name="character_name",
            new_value="Goku",
            old_values={a.entry_id: "A"},
        )
        cmd.redo()
        assert store.rosters["Sheet"][0].character_name == "Goku"

        cmd.undo()
        assert store.rosters["Sheet"][0].character_name == "A"


class TestReorderPresetsCommand:

    def test_reorder_and_undo(self, store):
        store.create_sheet("Sheet")
        a = PresetEntry(character_name="A")
        b = PresetEntry(character_name="B")
        c = PresetEntry(character_name="C")
        for entry in (a, b, c):
            store.add_preset_entry("Sheet", entry)

        old_order = [a.entry_id, b.entry_id, c.entry_id]
        new_order = [c.entry_id, a.entry_id, b.entry_id]
        cmd = ReorderPresetsCommand(store, "Sheet", old_order, new_order)

        cmd.redo()
        assert [p.character_name for p in store.rosters["Sheet"]] == ["C", "A", "B"]

        cmd.undo()
        assert [p.character_name for p in store.rosters["Sheet"]] == ["A", "B", "C"]


class TestReorderSheetsCommand:

    def test_reorder_sheets_and_undo(self, store):
        for name in ("A", "B", "C"):
            store.create_sheet(name)

        cmd = ReorderSheetsCommand(store, ["A", "B", "C"], ["C", "A", "B"])

        cmd.redo()
        assert list(store.rosters.keys()) == ["C", "A", "B"]
        assert store.dropdown_cache["table_names"] == ["C", "A", "B"]

        cmd.undo()
        assert list(store.rosters.keys()) == ["A", "B", "C"]
        assert store.dropdown_cache["table_names"] == ["A", "B", "C"]


class TestCacheItemCommands:

    def test_add_cache_item_and_undo(self, store):
        item = {"name": "Goku", "code": "GOK", "is_playable": True}
        cmd = AddCacheItemCommand(store, "characters", item)

        cmd.redo()
        assert any(c.get("name") == "Goku" for c in store.dropdown_cache["characters"])

        cmd.undo()
        assert not any(c.get("name") == "Goku" for c in store.dropdown_cache["characters"])

    def test_edit_cache_item_and_undo(self, store):
        old = {"name": "Goku", "code": "GOK", "is_playable": True}
        new = {"name": "Goku SSJ", "code": "GOK", "is_playable": True}
        store.dropdown_cache["characters"] = [old]

        cmd = EditCacheItemCommand(store, "characters", 0, old, new)

        cmd.redo()
        assert store.dropdown_cache["characters"][0]["name"] == "Goku SSJ"

        cmd.undo()
        assert store.dropdown_cache["characters"][0]["name"] == "Goku"

    def test_delete_cache_item_and_undo(self, store):
        a = {"name": "A", "code": "A", "is_playable": True}
        b = {"name": "B", "code": "B", "is_playable": True}
        c = {"name": "C", "code": "C", "is_playable": True}
        store.dropdown_cache["characters"] = [a, b, c]

        cmd = DeleteCacheItemCommand(store, "characters", 1, b)

        cmd.redo()
        assert [x["name"] for x in store.dropdown_cache["characters"]] == ["A", "C"]

        cmd.undo()
        assert [x["name"] for x in store.dropdown_cache["characters"]] == ["A", "B", "C"]

    def test_add_cache_item_sets_timestamps(self, store):
        item = {"name": "Goku", "code": "GOK", "is_playable": True}
        cmd = AddCacheItemCommand(store, "characters", item)
        cmd.redo()

        stored = store.dropdown_cache["characters"][0]
        assert stored["created_at"] != ""
        assert stored["modified_at"] != ""
        assert stored["created_at"] == stored["modified_at"]

    def test_edit_cache_item_updates_modified_preserves_created(self, store):
        old = {"name": "Goku", "code": "GOK", "is_playable": True,
               "created_at": "2026-01-01T00:00:00+00:00",
               "modified_at": "2026-01-01T00:00:00+00:00"}
        store.dropdown_cache["characters"] = [old]

        new = {"name": "Goku SSJ", "code": "GOK", "is_playable": True}
        cmd = EditCacheItemCommand(store, "characters", 0, old, new)
        cmd.redo()

        stored = store.dropdown_cache["characters"][0]
        assert stored["created_at"] == "2026-01-01T00:00:00+00:00"
        assert stored["modified_at"] != "2026-01-01T00:00:00+00:00"

    def test_add_cache_item_redo_preserves_timestamps(self, store):
        item = {"name": "Goku", "code": "GOK", "is_playable": True}
        cmd = AddCacheItemCommand(store, "characters", item)
        cmd.redo()
        first_created = store.dropdown_cache["characters"][0]["created_at"]

        cmd.undo()
        cmd.redo()

        stored = store.dropdown_cache["characters"][0]
        assert stored["created_at"] == first_created


class TestAddPresetWithAutoRegisterCommand:

    def test_undo_restores_cache_and_removes_preset(self, store):
        initial_chars = list(store.dropdown_cache["characters"])
        initial_skills = list(store.dropdown_cache["super_skills"])

        entry = PresetEntry(
            character_name="BrandNewChar",
            super_skills=["BrandNewSkill", "", "", ""],
        )
        cmd = AddPresetWithAutoRegisterCommand(store, "TestSheet", entry)

        cmd.redo()
        assert "TestSheet" in store.rosters
        assert any(c.get("name") == "BrandNewChar" for c in store.dropdown_cache["characters"])
        assert any(s.get("name") == "BrandNewSkill" for s in store.dropdown_cache["super_skills"])

        cmd.undo()
        assert "TestSheet" not in store.rosters
        assert store.dropdown_cache["characters"] == initial_chars
        assert store.dropdown_cache["super_skills"] == initial_skills

    def test_redo_undo_redo_cycle_re_registers(self, store):
        entry = PresetEntry(
            character_name="CycleChar",
            super_skills=["CycleSkill", "", "", ""],
        )
        cmd = AddPresetWithAutoRegisterCommand(store, "Sheet", entry)

        cmd.redo()
        cmd.undo()
        cmd.redo()

        assert "Sheet" in store.rosters
        assert len(store.rosters["Sheet"]) == 1
        assert any(c.get("name") == "CycleChar" for c in store.dropdown_cache["characters"])
        assert any(s.get("name") == "CycleSkill" for s in store.dropdown_cache["super_skills"])