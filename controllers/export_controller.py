"""
DBXV2 Build Forge — Export Controller.

Coordinates data export operations without GUI dependencies:
- Writing multi-sheet Excel workbooks via ``openpyxl``
- Writing individual Excel workbooks per sheet
- Writing single-file CSVs with sections
- Writing separate CSVs per sheet
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Sequence

from models.schemas import PresetEntry
from views.dialogs.export_dialog import (
    _write_csv_multi,
    _write_csv_single,
    _write_xlsx_multi,
    _write_xlsx_single,
)

logger = logging.getLogger(__name__)


class ExportController:
    """Non-GUI controller for exporting roster sheets to XLSX / CSV."""

    @staticmethod
    def export_xlsx_single(path: Path, sheets: dict[str, list[PresetEntry]]) -> None:
        """Export all sheets into a single XLSX file."""
        _write_xlsx_single(path, sheets)

    @staticmethod
    def export_xlsx_multi(folder: Path, sheets: dict[str, list[PresetEntry]]) -> int:
        """Export each sheet to a separate XLSX file in folder."""
        return _write_xlsx_multi(folder, sheets)

    @staticmethod
    def export_csv_single(path: Path, sheets: dict[str, list[PresetEntry]]) -> None:
        """Export all sheets into a single sectioned CSV file."""
        _write_csv_single(path, sheets)

    @staticmethod
    def export_csv_multi(folder: Path, sheets: dict[str, list[PresetEntry]]) -> int:
        """Export each sheet to a separate CSV file in folder."""
        return _write_csv_multi(folder, sheets)
