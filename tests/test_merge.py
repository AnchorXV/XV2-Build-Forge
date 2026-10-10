import pytest

from models.data_store import AppDataStore
from models.merge import count_merge_impact, merge_entry
from models.schemas import PresetEntry


@pytest.fixture
def store(tmp_path):
    return AppDataStore(data_file=tmp_path / "test.json")


def _add(store, sheet, **kwargs):
    entry = PresetEntry(**kwargs)
    store.add_preset_entry(sheet, entry)
    return entry


class TestMergeCharacters:

    def test_merges_char_name_in_preset(self, store):
        _add(store, "S1", character_name="Gokou")
        _add(store, "S1", character_name="Goku")
        store.dropdown_cache["characters"] = [
            {"name": "Gokou", "code": "BAD", "is_playable": True, "base_character": "Gokou", "episodes": []},
            {"name": "Goku", "code": "GOK", "is_playable": True, "base_character": "Goku", "episodes": []},
        ]

        affected = merge_entry(store, "characters", "Gokou", "Goku")
        assert affected == 1

        entries = store.get_sheet_entries("S1")
        assert entries[0].character_name == "Goku"
        assert entries[1].character_name == "Goku"

        chars = store.dropdown_cache["characters"]
        assert len(chars) == 1
        assert chars[0]["name"] == "Goku"

    def test_merges_super_soul_owner(self, store):
        store.dropdown_cache["super_souls"] = [
            {"name": "Soul A", "owner": "Gokou", "effect_1": "", "effect_2": "", "limit_burst": ""},
        ]
        store.dropdown_cache["characters"] = [
            {"name": "Gokou", "code": "BAD", "is_playable": True, "base_character": "", "episodes": []},
            {"name": "Goku", "code": "GOK", "is_playable": True, "base_character": "", "episodes": []},
        ]

        merge_entry(store, "characters", "Gokou", "Goku")
        assert store.dropdown_cache["super_souls"][0]["owner"] == "Goku"

    def test_merges_base_character_reference(self, store):
        store.dropdown_cache["characters"] = [
            {"name": "Gokou", "code": "BAD", "is_playable": True, "base_character": "", "episodes": []},
            {"name": "Goku", "code": "GOK", "is_playable": True, "base_character": "", "episodes": []},
            {"name": "Gokou (SSJ)", "code": "BAD2", "is_playable": True, "base_character": "Gokou", "episodes": []},
        ]

        merge_entry(store, "characters", "Gokou", "Goku")
        chars = store.dropdown_cache["characters"]
        ssj = next(c for c in chars if c["name"] == "Gokou (SSJ)")
        assert ssj["base_character"] == "Goku"


class TestMergeSkills:

    def test_merges_super_skill(self, store):
        _add(store, "S1", character_name="X", super_skills=["Kamehamehaa", "", "", ""])
        store.dropdown_cache["super_skills"] = [
            {"name": "Kamehamehaa", "is_cac": False, "skill_type": "", "ki_used": None, "note": ""},
            {"name": "Kamehameha", "is_cac": False, "skill_type": "", "ki_used": None, "note": ""},
        ]

        affected = merge_entry(store, "super_skills", "Kamehamehaa", "Kamehameha")
        assert affected == 1
        assert store.get_sheet_entries("S1")[0].super_skills[0] == "Kamehameha"
        assert len(store.dropdown_cache["super_skills"]) == 1

    def test_merges_ultimate_skill(self, store):
        _add(store, "S1", character_name="X", ultimate_skills=["Super Kamehamehaa", ""])
        store.dropdown_cache["ultimate_skills"] = [
            {"name": "Super Kamehamehaa", "is_cac": False, "skill_type": "", "ki_used": None, "note": ""},
            {"name": "Super Kamehameha", "is_cac": False, "skill_type": "", "ki_used": None, "note": ""},
        ]

        merge_entry(store, "ultimate_skills", "Super Kamehamehaa", "Super Kamehameha")
        assert store.get_sheet_entries("S1")[0].ultimate_skills[0] == "Super Kamehameha"

    def test_merges_awoken_skill(self, store):
        _add(store, "S1", character_name="X", awoken_skill="Super Saiyajin")
        store.dropdown_cache["awoken_skills"] = [
            {"name": "Super Saiyajin", "is_cac": False, "skill_type": "", "ki_used": None, "note": ""},
            {"name": "Super Saiyan", "is_cac": False, "skill_type": "", "ki_used": None, "note": ""},
        ]

        merge_entry(store, "awoken_skills", "Super Saiyajin", "Super Saiyan")
        assert store.get_sheet_entries("S1")[0].awoken_skill == "Super Saiyan"

    def test_merges_evasive_skill(self, store):
        _add(store, "S1", character_name="X", evasive_skill="Spirit Explossion")
        store.dropdown_cache["evasive_skills"] = [
            {"name": "Spirit Explossion", "is_cac": False, "skill_type": "", "ki_used": None, "note": ""},
            {"name": "Spirit Explosion", "is_cac": False, "skill_type": "", "ki_used": None, "note": ""},
        ]

        merge_entry(store, "evasive_skills", "Spirit Explossion", "Spirit Explosion")
        assert store.get_sheet_entries("S1")[0].evasive_skill == "Spirit Explosion"

    def test_merges_skill_multiple_occurrences_same_preset(self, store):
        _add(store, "S1", character_name="X",
             super_skills=["Kamehamehaa", "", "", "Kamehamehaa"])
        store.dropdown_cache["super_skills"] = [
            {"name": "Kamehamehaa", "is_cac": False, "skill_type": "", "ki_used": None, "note": ""},
            {"name": "Kamehameha", "is_cac": False, "skill_type": "", "ki_used": None, "note": ""},
        ]

        merge_entry(store, "super_skills", "Kamehamehaa", "Kamehameha")
        entry = store.get_sheet_entries("S1")[0]
        assert entry.super_skills[0] == "Kamehameha"
        assert entry.super_skills[3] == "Kamehameha"


class TestMergeSuperSouls:

    def test_merges_super_soul(self, store):
        _add(store, "S1", character_name="X", super_soul="Soul A")
        store.dropdown_cache["super_souls"] = [
            {"name": "Soul A", "owner": "", "effect_1": "", "effect_2": "", "limit_burst": ""},
            {"name": "Soul A (fixed)", "owner": "", "effect_1": "", "effect_2": "", "limit_burst": ""},
        ]

        affected = merge_entry(store, "super_souls", "Soul A", "Soul A (fixed)")
        assert affected == 1
        assert store.get_sheet_entries("S1")[0].super_soul == "Soul A (fixed)"


class TestMergeSources:

    def test_merges_source(self, store):
        _add(store, "S1", character_name="X", source="DBZ: Broly")
        store.dropdown_cache["sources"] = [
            {"name": "DBZ: Broly", "source_type": "", "day": None, "month": None, "year": None},
            {"name": "Dragon Ball Z: Broly", "source_type": "", "day": None, "month": None, "year": None},
        ]

        affected = merge_entry(store, "sources", "DBZ: Broly", "Dragon Ball Z: Broly")
        assert affected == 1
        assert store.get_sheet_entries("S1")[0].source == "Dragon Ball Z: Broly"


class TestCountMergeImpact:

    def test_counts_matching_only(self, store):
        _add(store, "S1", character_name="Gokou")
        _add(store, "S1", character_name="Goku")
        _add(store, "S2", character_name="Gokou")
        assert count_merge_impact(store, "characters", "Gokou") == 2

    def test_zero_when_no_match(self, store):
        _add(store, "S1", character_name="Vegeta")
        assert count_merge_impact(store, "characters", "Goku") == 0

    def test_counts_skill_in_list(self, store):
        _add(store, "S1", character_name="X", super_skills=["A", "A", "", ""])
        assert count_merge_impact(store, "super_skills", "A") == 1


class TestEdgeCases:

    def test_same_name_returns_zero(self, store):
        assert merge_entry(store, "characters", "Goku", "Goku") == 0

    def test_empty_source_returns_zero(self, store):
        assert merge_entry(store, "characters", "", "Goku") == 0

    def test_empty_target_returns_zero(self, store):
        assert merge_entry(store, "characters", "Goku", "") == 0

    def test_unknown_category_returns_zero(self, store):
        assert merge_entry(store, "unknown_cat", "A", "B") == 0

    def test_source_not_in_cache_still_renames_presets(self, store):
        _add(store, "S1", character_name="Gokou")
        affected = merge_entry(store, "characters", "Gokou", "Goku")
        assert affected == 1
        assert store.get_sheet_entries("S1")[0].character_name == "Goku"