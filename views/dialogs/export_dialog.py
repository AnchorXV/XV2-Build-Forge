"""
DBXV2 Build Forge — Export Dialogs.

Multi-step export flow:
1. Ask single-file vs multi-file (if >1 sheet selected).
2. Ask file format (xlsx / csv).
3. Browse for save path / folder.

Migrated from the ``export_selected`` method in ``main.py`` with
``pandas`` removed in favour of ``openpyxl`` + ``csv`` (per user pref).
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from locales.i18n_manager import tr
from models.schemas import PresetEntry

logger = logging.getLogger(__name__)


def _write_xlsx_single(
    path: Path,
    sheets: dict[str, list[PresetEntry]],
) -> None:
    """Write multiple sheets into a single ``.xlsx`` file using ``openpyxl``."""
    import openpyxl

    wb = openpyxl.Workbook()
    first = True
    for sheet_name, entries in sheets.items():
        ws = wb.active if first else wb.create_sheet()
        first = False
        ws.title = sheet_name[:31]  # Excel 31-char limit
        _write_header(ws)
        for row_idx, entry in enumerate(entries, start=2):
            _write_entry_row(ws, row_idx, entry)
    wb.save(str(path))


def _write_xlsx_multi(folder: Path, sheets: dict[str, list[PresetEntry]]) -> int:
    """Write one ``.xlsx`` file per sheet into *folder*."""
    import openpyxl

    count = 0
    for sheet_name, entries in sheets.items():
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = sheet_name[:31]
        _write_header(ws)
        for row_idx, entry in enumerate(entries, start=2):
            _write_entry_row(ws, row_idx, entry)
        wb.save(str(folder / f"{sheet_name}.xlsx"))
        count += 1
    return count


def _write_csv_single(path: Path, sheets: dict[str, list[PresetEntry]]) -> None:
    """Write all sheets as sections in a single CSV, separated by blank lines."""
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        for i, (sheet_name, entries) in enumerate(sheets.items()):
            if i > 0:
                writer.writerow([])
            writer.writerow([f"# Sheet: {sheet_name}"])
            writer.writerow(_HEADER_COLS)
            for entry in entries:
                writer.writerow(_entry_to_row(entry))


def _write_csv_multi(folder: Path, sheets: dict[str, list[PresetEntry]]) -> int:
    """Write one CSV per sheet."""
    count = 0
    for sheet_name, entries in sheets.items():
        path = folder / f"{sheet_name}.csv"
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(_HEADER_COLS)
            for entry in entries:
                writer.writerow(_entry_to_row(entry))
        count += 1
    return count


# ── Header / row helpers ────────────────────────────────────────────

_HEADER_COLS = [
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


def _write_header(ws: "openpyxl.worksheet.worksheet.Worksheet") -> None:  # type: ignore[name-defined]
    for col_idx, col_name in enumerate(_HEADER_COLS, start=1):
        ws.cell(row=1, column=col_idx, value=col_name)


def _entry_to_row(e: PresetEntry) -> list[str]:
    supers = list(e.super_skills) + [""] * (4 - len(e.super_skills))
    ults = list(e.ultimate_skills) + [""] * (2 - len(e.ultimate_skills))
    return [
        e.character_name,
        e.character_id,
        e.costume_name,
        str(e.costume_index),
        e.model_preset,
        supers[0],
        supers[1],
        supers[2],
        supers[3],
        ults[0],
        ults[1],
        e.awoken_skill,
        e.evasive_skill,
        e.super_soul,
    ]


def _write_entry_row(ws: "openpyxl.worksheet.worksheet.Worksheet", row: int, entry: PresetEntry) -> None:  # type: ignore[name-defined]
    for col_idx, value in enumerate(_entry_to_row(entry), start=1):
        ws.cell(row=row, column=col_idx, value=value)


# ── Export method dialog ────────────────────────────────────────────

class ExportMethodDialog(QDialog):
    """Ask the user whether to export as single-file or multi-file."""

    SINGLE = "single"
    MULTI = "multi"

    def __init__(self, count: int, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("dialog.export.title"))
        self.setMinimumWidth(400)
        self.result_choice: Optional[str] = None

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(tr("dialog.export.message", count=count)))

        btn_row = QHBoxLayout()
        single_btn = QPushButton(tr("dialog.export.single_file"))
        single_btn.clicked.connect(lambda: self._choose(self.SINGLE))
        btn_row.addWidget(single_btn)

        multi_btn = QPushButton(tr("dialog.export.multi_file"))
        multi_btn.clicked.connect(lambda: self._choose(self.MULTI))
        btn_row.addWidget(multi_btn)

        cancel_btn = QPushButton(tr("dialog.export.cancel"))
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        layout.addLayout(btn_row)

    def _choose(self, choice: str) -> None:
        self.result_choice = choice
        self.accept()


# ── Top-level export function ───────────────────────────────────────

def run_export_flow(
    parent: QWidget,
    sheets: dict[str, list[PresetEntry]],
) -> None:
    """Drive the complete export UI flow.

    Args:
        parent: Parent widget for dialogs.
        sheets: ``{sheet_name: [PresetEntry, …]}``.
    """
    if not sheets:
        return

    # Step 1: single vs multi (only if > 1 sheet)
    method = ExportMethodDialog.SINGLE
    if len(sheets) > 1:
        dlg = ExportMethodDialog(len(sheets), parent)
        if dlg.exec() != QDialog.Accepted or dlg.result_choice is None:
            return
        method = dlg.result_choice

    # Step 2: format (xlsx or csv)
    if method == ExportMethodDialog.SINGLE:
        path, chosen_filter = QFileDialog.getSaveFileName(
            parent,
            tr("dialog.export.save_file"),
            "",
            "Excel Workbook (*.xlsx);;CSV File (*.csv)",
        )
        if not path:
            return
        p = Path(path)
        try:
            if chosen_filter.startswith("Excel") or p.suffix.lower() == ".xlsx":
                _write_xlsx_single(p, sheets)
            else:
                _write_csv_single(p, sheets)
            QMessageBox.information(
                parent,
                tr("dialog.export.success_title"),
                tr("dialog.export.success_single", path=str(p)),
            )
        except Exception as exc:
            logger.exception("Export failed")
            QMessageBox.warning(parent, tr("dialog.common.warning"), str(exc))
    else:
        folder = QFileDialog.getExistingDirectory(
            parent, tr("dialog.export.choose_folder")
        )
        if not folder:
            return
        fp = Path(folder)
        try:
            # Determine format from a quick dialog
            fmt_path, fmt_filter = QFileDialog.getSaveFileName(
                parent,
                tr("dialog.export.format_title"),
                str(fp / "sample.xlsx"),
                "Excel Workbook (*.xlsx);;CSV File (*.csv)",
            )
            if not fmt_path:
                return
            use_xlsx = fmt_filter.startswith("Excel") or Path(fmt_path).suffix.lower() == ".xlsx"
            count = (
                _write_xlsx_multi(fp, sheets) if use_xlsx else _write_csv_multi(fp, sheets)
            )
            QMessageBox.information(
                parent,
                tr("dialog.export.success_title"),
                tr("dialog.export.success_multi", count=count, folder=str(fp)),
            )
        except Exception as exc:
            logger.exception("Export failed")
            QMessageBox.warning(parent, tr("dialog.common.warning"), str(exc))
