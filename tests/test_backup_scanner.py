import json
from datetime import datetime
from models.backup_scanner import _parse_timestamp_from_name, _read_backup_summary

def test_parse_timestamp_from_name():
    ts = _parse_timestamp_from_name("backup_20261028_143000.json")
    assert ts == datetime(2026, 10, 28, 14, 30, 0)
    assert _parse_timestamp_from_name("backup_invalid.json") is None

def test_read_backup_summary_corrupt(tmp_path):
    corrupt_file = tmp_path / "corrupt.json"
    corrupt_file.write_text("{invalid_json:", encoding="utf-8")
    assert _read_backup_summary(corrupt_file) == (0, 0, 0)

    non_dict_file = tmp_path / "nondict.json"
    non_dict_file.write_text("[1, 2, 3]", encoding="utf-8")
    assert _read_backup_summary(non_dict_file) == (0, 0, 0)

def test_read_backup_summary_valid(tmp_path):
    valid_file = tmp_path / "valid.json"
    data = {"rosters": {"Sheet1": [1, 2], "Sheet2": [3]}, "characters": [1, 2, 3]}
    valid_file.write_text(json.dumps(data), encoding="utf-8")
    assert _read_backup_summary(valid_file) == (2, 3, 3)