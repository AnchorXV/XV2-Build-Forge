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

@pytest.mark.parametrize("category,field_name,old,new", [
    ("super_skills", "super_skills", "Kamehamehaa", "Kamehameha"),
    ("ultimate_skills", "ultimate_skills", "Super Kamehamehaa", "Super Kamehameha"),
    ("awoken_skills", "awoken_skill", "Super Saiyajin", "Super Saiyan"),
    ("evasive_skills", "evasive_skill", "Spirit Explossion", "Spirit Explosion"),
])
class TestMergeSkills:
    def test_merges_skill_category(self, store, category, field_name, old, new):
        kwargs = {}
        if field_name == "super_skills":
            kwargs[field_name] = [old, "", "", ""]
        elif field_name == "ultimate_skills":
            kwargs[field_name] = [old, ""]
        else:
            kwargs[field_name] = old
            
        _add(store, "S1", character_name="X", **kwargs)
        
        store.dropdown_cache[category] = [
            {"name": old, "is_cac": False, "skill_type": "", "ki_used": None, "note": ""},
            {"name": new, "is_cac": False, "skill_type": "", "ki_used": None, "note": ""},
        ]

        merge_entry(store, category, old, new)

        entry = store.get_sheet_entries("S1")[0]
        value = getattr(entry, field_name)
        actual = value[0] if isinstance(value, list) else value
        
        assert actual == new
        assert len(store.dropdown_cache[category]) == 1


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