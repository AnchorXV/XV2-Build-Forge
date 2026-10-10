from models.preset_clipboard import PresetClipboard
from models.schemas import PresetEntry


class TestToTsv:

    def test_empty_returns_empty_string(self):
        assert PresetClipboard.to_tsv([]) == ""

    def test_single_entry_one_line(self):
        entry = PresetEntry(
            character_name="Goku",
            character_id="GOK",
            costume_name="Turtle Gi",
            super_skills=["Kamehameha", "", "", ""],
            super_soul="Hope",
            source="DBZ",
        )
        result = PresetClipboard.to_tsv([entry])
        lines = result.split("\n")
        assert len(lines) == 1
        cells = lines[0].split("\t")
        assert cells[0] == "Goku"
        assert cells[1] == "GOK"
        assert cells[2] == "Turtle Gi"
        assert cells[5] == "Kamehameha"
        assert cells[-1] == "DBZ"

    def test_multiple_entries_multiple_lines(self):
        e1 = PresetEntry(character_name="Goku")
        e2 = PresetEntry(character_name="Vegeta")
        result = PresetClipboard.to_tsv([e1, e2])
        lines = result.split("\n")
        assert len(lines) == 2
        assert lines[0].split("\t")[0] == "Goku"
        assert lines[1].split("\t")[0] == "Vegeta"

    def test_tab_count_matches_columns(self):
        from app_config import TABLE_COLUMNS
        entry = PresetEntry(character_name="Goku")
        result = PresetClipboard.to_tsv([entry])
        cells = result.split("\t")
        assert len(cells) == len(TABLE_COLUMNS)

    def test_numeric_fields_as_string(self):
        entry = PresetEntry(
            character_name="Goku",
            costume_index=3,
            model_preset="7",
        )
        result = PresetClipboard.to_tsv([entry])
        cells = result.split("\t")
        assert cells[3] == "3"
        assert cells[4] == "7"


class TestClipboardSingleton:

    def test_set_and_get(self):
        cb = PresetClipboard.instance()
        cb.clear()
        e = PresetEntry(character_name="Goku")
        cb.set([e])
        assert cb.count() == 1
        assert cb.has_content()

    def test_get_entries_is_clone(self):
        cb = PresetClipboard.instance()
        cb.clear()
        e = PresetEntry(character_name="Goku")
        cb.set([e])
        got = cb.get_entries()
        got[0].character_name = "Modified"
        assert cb.get_entries()[0].character_name == "Goku"