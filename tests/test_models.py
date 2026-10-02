import tempfile
import uuid
from pathlib import Path

from models.data_store import AppDataStore
from models.persistence import AtomicJsonPersistence
from models.schemas import Character, PresetEntry
from models.validators import validate_character, validate_preset_entry


class TestModels:

    def test_preset_entry_uuid_and_roundtrip(self):
        entry = PresetEntry(
            character_name="Goku",
            character_id="GOK",
            costume_name="Turtle Hermit Gi",
            costume_index=0,
            model_preset="Normal",
            super_skills=["Kamehameha", "Spirit Bomb", "", ""],
            ultimate_skills=["Super Kamehameha", ""],
            awoken_skill="Super Saiyan",
            evasive_skill="Spirit Explosion",
            super_soul="Hope of the Universe",
        )

        assert isinstance(entry.entry_id, str)
        uuid.UUID(entry.entry_id)

        assert isinstance(entry.super_skills, list)
        assert entry.super_skills == ["Kamehameha", "Spirit Bomb", "", ""]
        assert isinstance(entry.ultimate_skills, list)

        d = entry.to_dict()
        assert d["Character Name"] == "Goku"
        assert d["entry_id"] == entry.entry_id

        restored = PresetEntry.from_dict(d)
        assert restored.entry_id == entry.entry_id
        assert restored.character_name == "Goku"
        assert isinstance(restored.super_skills, list)
        assert isinstance(restored.ultimate_skills, list)
        assert restored.super_skills == entry.super_skills
        assert restored.ultimate_skills == entry.ultimate_skills

    def test_persistence_atomic_write_and_recovery(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_data.json"
            p = AtomicJsonPersistence(file_path)

            test_payload = {
                "version": "1.0.0",
                "settings": {"language": "id", "theme": "dark"},
                "rosters": {},
                "characters": [],
            }
            p.save(test_payload)
            assert file_path.exists()

            loaded = p.load()
            assert loaded["settings"]["language"] == "id"

            test_payload["settings"]["language"] = "ja"
            p.save(test_payload)
            bak_path = file_path.with_suffix(".json.bak")
            assert bak_path.exists()

            with open(file_path, "w", encoding="utf-8") as f:
                f.write("INVALID JSON CORRUPTED DATA {{{")

            recovered = p.load()
            assert recovered["settings"]["language"] == "id"

    def test_persistence_non_dict_root_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.json"
            p = AtomicJsonPersistence(file_path)

            file_path.write_text("[1, 2, 3]", encoding="utf-8")
            assert p.load() == {}

            file_path.write_text('"just a string"', encoding="utf-8")
            assert p.load() == {}

            file_path.write_text("42", encoding="utf-8")
            assert p.load() == {}

    def test_data_store_crud_and_update(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_store.json"
            store = AppDataStore(data_file=file_path)

            store.create_sheet("Goku_Presets")
            entry = PresetEntry(character_name="Goku", costume_name="Costume 1")
            store.add_preset_entry("Goku_Presets", entry)

            entries = store.get_sheet_entries("Goku_Presets")
            assert len(entries) == 1
            assert entries[0].character_name == "Goku"

            modified = PresetEntry(
                character_name="Goku SSJ",
                costume_name="Costume 1 Modified",
                entry_id=entry.entry_id,
            )
            success = store.update_preset_entry("Goku_Presets", modified)
            assert success is True

            entries_after = store.get_sheet_entries("Goku_Presets")
            assert len(entries_after) == 1
            assert entries_after[0].character_name == "Goku SSJ"

    def test_update_preset_entry_unknown_id_does_not_append(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.json"
            store = AppDataStore(data_file=file_path)
            store.create_sheet("Sheet")
            entry = PresetEntry(character_name="Goku")
            store.add_preset_entry("Sheet", entry)

            ghost = PresetEntry(character_name="Ghost", entry_id="nonexistent-id")
            success = store.update_preset_entry("Sheet", ghost)

            assert success is False
            assert len(store.get_sheet_entries("Sheet")) == 1

    def test_validators(self):
        valid_char = Character(code="GOK", name="Goku")
        assert validate_character(valid_char) == []

        invalid_char = Character(code="", name="")
        assert len(validate_character(invalid_char)) >= 1

        valid_preset = PresetEntry(character_name="Vegeta")
        assert validate_preset_entry(valid_preset) == []

        invalid_preset = PresetEntry(character_name="")
        assert len(validate_preset_entry(invalid_preset)) >= 1

    def test_data_store_meta_and_recent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_store_meta.json"
            store = AppDataStore(data_file=file_path)

            store.create_sheet("Goku_Presets")

            meta = store.get_sheet_meta("Goku_Presets")
            assert meta["note"] == ""
            assert meta["tags"] == []

            store.update_sheet_meta("Goku_Presets", "My custom note", ["Tag1", "Tag2"])
            meta_after = store.get_sheet_meta("Goku_Presets")
            assert meta_after["note"] == "My custom note"
            assert "Tag1" in meta_after["tags"]

            store.add_recent_sheet("Goku_Presets")
            assert store.get_recent_sheets()[0] == "Goku_Presets"

    def test_get_character_code(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.json"
            store = AppDataStore(data_file=file_path)
            store.dropdown_cache["characters"] = [
                {"code": "GOK", "name": "Goku", "is_playable": True},
                {"code": "VEG", "name": "Vegeta", "is_playable": True},
            ]

            assert store.get_character_code("Goku") == "GOK"
            assert store.get_character_code("Vegeta") == "VEG"
            assert store.get_character_code("Unknown") == ""

    def test_store_roundtrip_via_disk(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.json"

            store1 = AppDataStore(data_file=file_path)
            store1.create_sheet("Sheet1")
            store1.add_preset_entry("Sheet1", PresetEntry(character_name="Goku"))
            store1.update_sheet_meta("Sheet1", "note", ["tag"])
            store1.dropdown_cache["characters"] = [
                {"code": "GOK", "name": "Goku", "is_playable": True}
            ]
            store1.save()

            store2 = AppDataStore(data_file=file_path)
            assert "Sheet1" in store2.rosters
            assert len(store2.get_sheet_entries("Sheet1")) == 1
            assert store2.get_sheet_meta("Sheet1")["note"] == "note"
            assert store2.get_sheet_meta("Sheet1")["tags"] == ["tag"]
            assert store2.get_cache("characters")[0]["name"] == "Goku"

    def test_canonicalize_legacy_strings(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.json"
            store = AppDataStore(data_file=file_path)

            result = store._canonicalize_cache_item("characters", "Goku")
            assert result == {"code": "MOD", "name": "Goku", "is_playable": True}

            result = store._canonicalize_cache_item(
                "characters",
                {"Code": "GOK", "Name": "Goku", "Playable Character": "Yes"},
            )
            assert result == {"code": "GOK", "name": "Goku", "is_playable": True}

            canonical = {"code": "GOK", "name": "Goku", "is_playable": True}
            result = store._canonicalize_cache_item("characters", canonical)
            assert result == canonical

            result = store._canonicalize_cache_item("super_souls", "Hope")
            assert result == {"name": "Hope", "effect_1": "", "effect_2": "", "note": ""}