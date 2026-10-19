from models.schemas import PresetEntry
from models.validators import find_duplicate_skill_slots, find_identical_presets


class TestFindDuplicateSkillSlots:

    def test_no_duplicates(self):
        e = PresetEntry(
            character_name="Goku",
            super_skills=["A", "B", "C", "D"],
            ultimate_skills=["E", "F"],
        )
        assert find_duplicate_skill_slots(e) == {}

    def test_duplicate_super(self):
        e = PresetEntry(character_name="Goku", super_skills=["A", "", "A", ""])
        assert find_duplicate_skill_slots(e) == {"super_skill": [0, 2]}

    def test_duplicate_ultimate(self):
        e = PresetEntry(character_name="Goku", ultimate_skills=["X", "X"])
        assert find_duplicate_skill_slots(e) == {"ultimate_skill": [0, 1]}

    def test_empty_values_ignored(self):
        e = PresetEntry(character_name="Goku", super_skills=["", "", "", ""])
        assert find_duplicate_skill_slots(e) == {}

    def test_whitespace_stripped(self):
        e = PresetEntry(character_name="Goku", super_skills=["A", " A ", "", ""])
        assert find_duplicate_skill_slots(e) == {"super_skill": [0, 1]}

    def test_three_way_duplicate(self):
        e = PresetEntry(character_name="Goku", super_skills=["A", "A", "A", ""])
        assert find_duplicate_skill_slots(e) == {"super_skill": [0, 1, 2]}


class TestFindIdenticalPresets:

    def test_no_existing(self):
        e = PresetEntry(character_name="Goku")
        assert find_identical_presets(e, []) == []

    def test_match(self):
        e1 = PresetEntry(
            character_name="Goku", costume_name="Gi",
            super_skills=["A", "B", "", ""],
        )
        e2 = PresetEntry(
            character_name="Goku", costume_name="Gi",
            super_skills=["A", "B", "", ""],
        )
        assert find_identical_presets(e1, [e2]) == [e2]

    def test_different_skill(self):
        e1 = PresetEntry(character_name="Goku", super_skills=["A", "", "", ""])
        e2 = PresetEntry(character_name="Goku", super_skills=["B", "", "", ""])
        assert find_identical_presets(e1, [e2]) == []

    def test_different_costume(self):
        e1 = PresetEntry(character_name="Goku", costume_name="Gi")
        e2 = PresetEntry(character_name="Goku", costume_name="Armor")
        assert find_identical_presets(e1, [e2]) == []

    def test_same_entry_id_skipped(self):
        e = PresetEntry(character_name="Goku", entry_id="same-id")
        other = PresetEntry(character_name="Goku", entry_id="same-id")
        assert find_identical_presets(e, [other]) == []

    def test_empty_character_name_returns_empty(self):
        e1 = PresetEntry(character_name="", super_skills=["A", "", "", ""])
        e2 = PresetEntry(character_name="", super_skills=["A", "", "", ""])
        assert find_identical_presets(e1, [e2]) == []

    def test_multiple_matches(self):
        e = PresetEntry(character_name="Goku", costume_name="Gi")
        m1 = PresetEntry(character_name="Goku", costume_name="Gi")
        m2 = PresetEntry(character_name="Goku", costume_name="Gi")
        m3 = PresetEntry(character_name="Vegeta", costume_name="Gi")
        result = find_identical_presets(e, [m1, m2, m3])
        assert len(result) == 2