"""
Unit tests for models (schemas, persistence, data_store, validators).
"""

import tempfile
from pathlib import Path
import pytest

from models.data_store import AppDataStore
from models.persistence import AtomicJsonPersistence
from models.schemas import Character, PresetEntry, Skill
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
        assert entry.entry_id is not None
        assert len(entry.entry_id) > 10

        d = entry.to_dict()
        assert d["Character Name"] == "Goku"
        assert d["entry_id"] == entry.entry_id

        restored = PresetEntry.from_dict(d)
        assert restored.entry_id == entry.entry_id
        assert restored.character_name == "Goku"
        assert list(restored.super_skills) == ["Kamehameha", "Spirit Bomb", "", ""]

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

            # Modify and save again, checking backup creation
            test_payload["settings"]["language"] = "ja"
            p.save(test_payload)
            bak_path = file_path.with_suffix(".json.bak")
            assert bak_path.exists()

            # Corrupt the main file and verify fallback to .bak
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("INVALID JSON CORRUPTED DATA {{{")

            recovered = p.load()
            assert recovered is not None
            assert "settings" in recovered
            assert recovered["settings"]["language"] in ("id", "ja")

    def test_data_store_crud_and_update(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_store.json"
            store = AppDataStore(data_file=file_path)

            # Create sheet and add entry
            store.create_sheet("Goku_Presets")
            entry = PresetEntry(character_name="Goku", costume_name="Costume 1")
            store.add_preset_entry("Goku_Presets", entry)

            entries = store.get_sheet_entries("Goku_Presets")
            assert len(entries) == 1
            assert entries[0].character_name == "Goku"

            # Update entry
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
            
            # Test default meta
            meta = store.get_sheet_meta("Goku_Presets")
            assert meta["note"] == ""
            assert meta["tags"] == []
            
            # Update meta
            store.update_sheet_meta("Goku_Presets", "My custom note", ["Tag1", "Tag2"])
            meta_after = store.get_sheet_meta("Goku_Presets")
            assert meta_after["note"] == "My custom note"
            assert "Tag1" in meta_after["tags"]
            
            # Test recent sheets
            store.add_recent_sheet("Goku_Presets")
            assert store.get_recent_sheets()[0] == "Goku_Presets"
