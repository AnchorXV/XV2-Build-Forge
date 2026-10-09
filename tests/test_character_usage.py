import pytest

from models.character_usage import (
    find_character_skills,
    find_character_souls,
    find_skill_usage,
    find_soul_usage,
)
from models.data_store import AppDataStore
from models.schemas import PresetEntry


@pytest.fixture
def store(tmp_path):
    return AppDataStore(data_file=tmp_path / "test.json")


def _add_preset(
    store,
    sheet,
    character,
    super_skills=None,
    ultimate_skills=None,
    awoken="",
    evasive="",
    soul="",
    costume="",
):
    entry = PresetEntry(
        character_name=character,
        costume_name=costume,
        super_skills=super_skills or ["", "", "", ""],
        ultimate_skills=ultimate_skills or ["", ""],
        awoken_skill=awoken,
        evasive_skill=evasive,
        super_soul=soul,
    )
    store.add_preset_entry(sheet, entry)
    return entry


class TestFindSkillUsage:

    def test_empty_skill(self, store):
        assert find_skill_usage(store, "", "super_skills") == []

    def test_unknown_category(self, store):
        assert find_skill_usage(store, "Kamehameha", "unknown") == []

    def test_finds_skill_in_super_slot(self, store):
        _add_preset(
            store, "Sheet1", "Goku",
            super_skills=["Kamehameha", "", "", ""],
            costume="Turtle Gi",
        )
        results = find_skill_usage(store, "Kamehameha", "super_skills")
        assert len(results) == 1
        assert results[0].character_name == "Goku"
        assert results[0].costume_name == "Turtle Gi"
        assert results[0].slot_label == "Super 1"
        assert results[0].sheet_name == "Sheet1"

    def test_finds_in_multiple_slots(self, store):
        _add_preset(
            store, "Sheet1", "Goku",
            super_skills=["Kamehameha", "", "", "Kamehameha"],
        )
        results = find_skill_usage(store, "Kamehameha", "super_skills")
        assert len(results) == 2
        slots = {r.slot_label for r in results}
        assert slots == {"Super 1", "Super 4"}

    def test_skill_across_sheets(self, store):
        _add_preset(store, "Sheet1", "Goku", super_skills=["Kamehameha", "", "", ""])
        _add_preset(store, "Sheet2", "Vegeta", super_skills=["Kamehameha", "", "", ""])
        results = find_skill_usage(store, "Kamehameha", "super_skills")
        assert len(results) == 2
        sheets = {r.sheet_name for r in results}
        assert sheets == {"Sheet1", "Sheet2"}

    def test_awoken_skill(self, store):
        _add_preset(store, "Sheet1", "Goku", awoken="Super Saiyan")
        results = find_skill_usage(store, "Super Saiyan", "awoken_skills")
        assert len(results) == 1
        assert results[0].slot_label == "Awoken"

    def test_evasive_skill(self, store):
        _add_preset(store, "Sheet1", "Goku", evasive="Spirit Explosion")
        results = find_skill_usage(store, "Spirit Explosion", "evasive_skills")
        assert len(results) == 1
        assert results[0].slot_label == "Evasive"

    def test_ultimate_skill(self, store):
        _add_preset(store, "Sheet1", "Goku", ultimate_skills=["Super Kamehameha", ""])
        results = find_skill_usage(store, "Super Kamehameha", "ultimate_skills")
        assert len(results) == 1
        assert results[0].slot_label == "Ultimate 1"

    def test_display_label_format(self, store):
        _add_preset(
            store, "Sheet1", "Goku",
            super_skills=["Kamehameha", "", "", ""],
            costume="Turtle Gi",
        )
        results = find_skill_usage(store, "Kamehameha", "super_skills")
        assert results[0].display_label() == "Goku · Turtle Gi · Super 1"

    def test_display_label_no_costume(self, store):
        _add_preset(store, "Sheet1", "Goku", super_skills=["Kamehameha", "", "", ""])
        results = find_skill_usage(store, "Kamehameha", "super_skills")
        assert results[0].display_label() == "Goku · — · Super 1"


class TestFindSoulUsage:

    def test_finds_soul(self, store):
        _add_preset(store, "Sheet1", "Goku", soul="Hope of Universe", costume="Base")
        results = find_soul_usage(store, "Hope of Universe")
        assert len(results) == 1
        assert results[0].character_name == "Goku"
        assert results[0].slot_label == "Super Soul"

    def test_multiple_presets(self, store):
        _add_preset(store, "Sheet1", "Goku", soul="Hope")
        _add_preset(store, "Sheet1", "Vegeta", soul="Hope")
        results = find_soul_usage(store, "Hope")
        assert len(results) == 2

    def test_empty_soul(self, store):
        assert find_soul_usage(store, "") == []


class TestFindCharacterSkills:

    def test_no_presets(self, store):
        assert find_character_skills(store, "Goku") == []

    def test_only_matching_character(self, store):
        _add_preset(store, "Sheet1", "Goku", super_skills=["Kamehameha", "", "", ""])
        _add_preset(store, "Sheet1", "Vegeta", super_skills=["Galick Gun", "", "", ""])
        results = find_character_skills(store, "Goku")
        assert len(results) == 1
        assert results[0][0] == "Kamehameha"

    def test_exact_match_not_variant(self, store):
        _add_preset(store, "Sheet1", "Goku", super_skills=["Kamehameha", "", "", ""])
        _add_preset(store, "Sheet1", "Goku (SSG)", super_skills=["God Kamehameha", "", "", ""])
        results = find_character_skills(store, "Goku")
        names = [r[0] for r in results]
        assert "Kamehameha" in names
        assert "God Kamehameha" not in names

    def test_across_costumes(self, store):
        _add_preset(store, "Sheet1", "Goku", super_skills=["Kamehameha", "", "", ""], costume="A")
        _add_preset(store, "Sheet1", "Goku", super_skills=["Kamehameha", "", "", ""], costume="B")
        results = find_character_skills(store, "Goku")
        assert len(results) == 1
        assert results[0] == ("Kamehameha", 2)

    def test_duplicate_in_same_preset_counted_once(self, store):
        _add_preset(store, "Sheet1", "Goku", super_skills=["Kamehameha", "", "", "Kamehameha"])
        results = find_character_skills(store, "Goku")
        assert results[0] == ("Kamehameha", 1)

    def test_suffix_when_same_name_in_two_categories(self, store):
        _add_preset(
            store, "Sheet1", "Goku",
            super_skills=["Eagle Kick", "", "", ""],
            evasive="Eagle Kick",
        )
        results = find_character_skills(store, "Goku")
        labels = [r[0] for r in results]
        assert "Eagle Kick (Super)" in labels
        assert "Eagle Kick (Evasive)" in labels

    def test_no_suffix_when_unique(self, store):
        _add_preset(store, "Sheet1", "Goku", super_skills=["Kamehameha", "", "", ""])
        results = find_character_skills(store, "Goku")
        assert results[0][0] == "Kamehameha"

    def test_all_four_categories(self, store):
        _add_preset(
            store, "Sheet1", "Goku",
            super_skills=["S1", "", "", ""],
            ultimate_skills=["U1", ""],
            awoken="A1",
            evasive="E1",
        )
        results = find_character_skills(store, "Goku")
        labels = {r[0] for r in results}
        assert labels == {"S1", "U1", "A1", "E1"}

    def test_sorted_alphabetically(self, store):
        _add_preset(store, "Sheet1", "Goku", super_skills=["Zebra", "Apple", "Mango", ""])
        results = find_character_skills(store, "Goku")
        labels = [r[0] for r in results]
        assert labels == ["Apple", "Mango", "Zebra"]


class TestFindCharacterSouls:

    def test_no_souls(self, store):
        _add_preset(store, "Sheet1", "Goku")
        assert find_character_souls(store, "Goku") == []

    def test_finds_soul(self, store):
        _add_preset(store, "Sheet1", "Goku", soul="Hope")
        results = find_character_souls(store, "Goku")
        assert results == [("Hope", 1)]

    def test_across_costumes(self, store):
        _add_preset(store, "Sheet1", "Goku", soul="Hope", costume="A")
        _add_preset(store, "Sheet1", "Goku", soul="Hope", costume="B")
        results = find_character_souls(store, "Goku")
        assert results == [("Hope", 2)]

    def test_only_matching_character(self, store):
        _add_preset(store, "Sheet1", "Goku", soul="Hope")
        _add_preset(store, "Sheet1", "Vegeta", soul="Pride")
        results = find_character_souls(store, "Goku")
        assert results == [("Hope", 1)]