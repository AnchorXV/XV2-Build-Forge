from models.completeness import (
    check_preset_completeness,
    get_sheet_completeness_summary,
)
from models.schemas import PresetEntry


def _complete_entry(name="Goku"):
    return PresetEntry(
        character_name=name,
        super_skills=["s1", "s2", "s3", "s4"],
        ultimate_skills=["u1", "u2"],
        awoken_skill="a",
        evasive_skill="e",
        super_soul="ss",
    )


class TestCheckPresetCompleteness:

    def test_complete_entry_returns_empty_list(self):
        assert check_preset_completeness(_complete_entry()) == []

    def test_empty_entry_lists_all_mandatory_slots(self):
        entry = PresetEntry(character_name="Goku")
        missing = check_preset_completeness(entry)
        assert "Super Skill 1" in missing
        assert "Super Skill 2" in missing
        assert "Super Skill 3" in missing
        assert "Super Skill 4" in missing
        assert "Ultimate Skill 1" in missing
        assert "Ultimate Skill 2" in missing
        assert "Awoken Skill" in missing
        assert "Evasive Skill" in missing
        assert "Super Soul" in missing
        assert len(missing) == 9

    def test_partial_super_skills(self):
        entry = _complete_entry()
        entry.super_skills = ["s1", "", "s3", ""]
        missing = check_preset_completeness(entry)
        assert "Super Skill 2" in missing
        assert "Super Skill 4" in missing
        assert "Super Skill 1" not in missing
        assert "Super Skill 3" not in missing

    def test_whitespace_only_counts_as_missing(self):
        entry = _complete_entry()
        entry.awoken_skill = "   "
        missing = check_preset_completeness(entry)
        assert "Awoken Skill" in missing

    def test_missing_ultimate_only(self):
        entry = _complete_entry()
        entry.ultimate_skills = ["u1", ""]
        missing = check_preset_completeness(entry)
        assert missing == ["Ultimate Skill 2"]

    def test_order_is_super_then_ultimate_then_singles(self):
        entry = PresetEntry(character_name="Goku")
        missing = check_preset_completeness(entry)
        assert missing[0] == "Super Skill 1"
        assert missing[4] == "Ultimate Skill 1"
        assert missing[6] == "Awoken Skill"
        assert missing[7] == "Evasive Skill"
        assert missing[8] == "Super Soul"


class TestGetSheetCompletenessSummary:

    def test_all_complete_returns_empty_list(self):
        entries = [_complete_entry("Goku"), _complete_entry("Vegeta")]
        assert get_sheet_completeness_summary(entries) == []

    def test_returns_label_and_missing_for_incomplete_entries(self):
        complete = _complete_entry("Goku")
        incomplete = PresetEntry(character_name="Vegeta")
        result = get_sheet_completeness_summary([complete, incomplete])

        assert len(result) == 1
        label, missing = result[0]
        assert label == "Vegeta"
        assert "Super Skill 1" in missing

    def test_label_includes_costume_name_when_present(self):
        entry = PresetEntry(character_name="Goku", costume_name="Turtle Gi")
        result = get_sheet_completeness_summary([entry])

        assert len(result) == 1
        label, _ = result[0]
        assert label == "Goku (Turtle Gi)"

    def test_unnamed_entry_labeled_as_unnamed(self):
        entry = PresetEntry(character_name="")
        result = get_sheet_completeness_summary([entry])

        assert len(result) == 1
        label, _ = result[0]
        assert label == "Unnamed"

    def test_mixed_list_only_reports_incomplete(self):
        entries = [
            _complete_entry("Goku"),
            PresetEntry(character_name="Vegeta"),
            _complete_entry("Gohan"),
            PresetEntry(character_name="Trunks", costume_name="Jacket"),
        ]
        result = get_sheet_completeness_summary(entries)
        assert len(result) == 2
        labels = [label for label, _ in result]
        assert "Vegeta" in labels
        assert "Trunks (Jacket)" in labels