from __future__ import annotations

import csv
import logging
from pathlib import Path

from models.schemas import PresetEntry

logger = logging.getLogger(__name__)


HEADER_COLUMNS = [
    "Character Name",
    "Character ID",
    "Costume Name",
    "Costume Index",
    "Model Preset",
    "Super 1",
    "Super 2",
    "Super 3",
    "Super 4",
    "Ultimate 1",
    "Ultimate 2",
    "Awoken Skill",
    "Evasive Skill",
    "Super Soul",
]


def _entry_to_row(entry: PresetEntry) -> list[str]:
    supers = list(entry.super_skills) + [""] * max(0, 4 - len(entry.super_skills))
    ults = list(entry.ultimate_skills) + [""] * max(0, 2 - len(entry.ultimate_skills))
    return [
        entry.character_name,
        entry.character_id,
        entry.costume_name,
        str(entry.costume_index),
        str(entry.model_preset),
        supers[0],
        supers[1],
        supers[2],
        supers[3],
        ults[0],
        ults[1],
        entry.awoken_skill,
        entry.evasive_skill,
        entry.super_soul,
    ]


def _truncate_sheet_name(name: str) -> str:
    return name[:31] if name else "Sheet"


def write_xlsx_single(path: Path, sheets: dict[str, list[PresetEntry]]) -> None:
    import openpyxl

    wb = openpyxl.Workbook()
    default_sheet = wb.active

    for idx, (sheet_name, entries) in enumerate(sheets.items()):
        ws = default_sheet if idx == 0 else wb.create_sheet()
        ws.title = _truncate_sheet_name(sheet_name)

        for col_idx, col_name in enumerate(HEADER_COLUMNS, start=1):
            ws.cell(row=1, column=col_idx, value=col_name)

        for row_idx, entry in enumerate(entries, start=2):
            for col_idx, value in enumerate(_entry_to_row(entry), start=1):
                ws.cell(row=row_idx, column=col_idx, value=value)

    wb.save(str(path))


def write_xlsx_multi(folder: Path, sheets: dict[str, list[PresetEntry]]) -> int:
    import openpyxl

    count = 0
    for sheet_name, entries in sheets.items():
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = _truncate_sheet_name(sheet_name)

        for col_idx, col_name in enumerate(HEADER_COLUMNS, start=1):
            ws.cell(row=1, column=col_idx, value=col_name)

        for row_idx, entry in enumerate(entries, start=2):
            for col_idx, value in enumerate(_entry_to_row(entry), start=1):
                ws.cell(row=row_idx, column=col_idx, value=value)

        wb.save(str(folder / f"{sheet_name}.xlsx"))
        count += 1
    return count


def write_csv_single(path: Path, sheets: dict[str, list[PresetEntry]]) -> None:
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        for i, (sheet_name, entries) in enumerate(sheets.items()):
            if i > 0:
                writer.writerow([])
            writer.writerow([f"# Sheet: {sheet_name}"])
            writer.writerow(HEADER_COLUMNS)
            for entry in entries:
                writer.writerow(_entry_to_row(entry))


def write_csv_multi(folder: Path, sheets: dict[str, list[PresetEntry]]) -> int:
    count = 0
    for sheet_name, entries in sheets.items():
        path = folder / f"{sheet_name}.csv"
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(HEADER_COLUMNS)
            for entry in entries:
                writer.writerow(_entry_to_row(entry))
        count += 1
    return count