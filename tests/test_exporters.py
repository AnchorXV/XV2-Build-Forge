from models.exporters import _truncate_sheet_name, _sanitize_filename, _resolve_columns, _entry_value
from models.schemas import PresetEntry
from app_config import TABLE_COLUMNS

def test_truncate_sheet_name():
    assert _truncate_sheet_name("A" * 40) == "A" * 31
    assert _truncate_sheet_name("Sheet/Name*With|Bad?Chars[]") == "Sheet_Name_With_Bad_Chars__"
    assert _truncate_sheet_name("") == "Sheet"

def test_sanitize_filename():
    assert _sanitize_filename("Sheet/Name:With*Bad?Chars") == "Sheet_Name_With_Bad_Chars"
    assert _sanitize_filename("") == "Sheet"

def test_resolve_columns():
    assert _resolve_columns(None) == TABLE_COLUMNS
    assert _resolve_columns(["Character Name", "Invalid"]) == ["Character Name"]

def test_entry_value_out_of_bounds():
    entry = PresetEntry(character_name="Goku", super_skills=["A", "B", "C", "D"])
    assert _entry_value(entry, "Super Skill 1") == "A"
    assert _entry_value(entry, "Super Skill 4") == "D"
    assert _entry_value(entry, "Super Skill 5") == ""
    assert _entry_value(entry, "Ultimate Skill 1") == ""