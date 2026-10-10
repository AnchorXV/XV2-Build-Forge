from __future__ import annotations

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

from app_config import TABLE_COLUMNS
from locales.i18n_manager import tr
from models.exporters import (
    write_csv_multi,
    write_csv_single,
    write_md_multi,
    write_md_single,
    write_text_multi,
    write_text_single,
    write_xlsx_multi,
    write_xlsx_single,
)
from models.schemas import PresetEntry
from views.dialogs.column_select_dialog import ColumnSelectDialog

logger = logging.getLogger(__name__)

FILE_FILTERS = (
    "Excel Workbook (*.xlsx);;"
    "CSV File (*.csv);;"
    "Text File (*.txt);;"
    "Markdown File (*.md)"
)


class ExportMethodDialog(QDialog):

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


def _detect_format(path: Path, chosen_filter: str) -> str:
    suffix = path.suffix.lower()
    if chosen_filter.startswith("Excel") or suffix == ".xlsx":
        return "xlsx"
    if chosen_filter.startswith("CSV") or suffix == ".csv":
        return "csv"
    if chosen_filter.startswith("Text") or suffix == ".txt":
        return "txt"
    if chosen_filter.startswith("Markdown") or suffix in (".md", ".markdown"):
        return "md"
    return "xlsx"


def run_export_flow(
    parent: QWidget,
    sheets: dict[str, list[PresetEntry]],
) -> None:
    if not sheets:
        return

    method = ExportMethodDialog.SINGLE
    if len(sheets) > 1:
        dlg = ExportMethodDialog(len(sheets), parent)
        if dlg.exec() != QDialog.Accepted or dlg.result_choice is None:
            return
        method = dlg.result_choice

    col_dlg = ColumnSelectDialog(list(TABLE_COLUMNS), parent=parent)
    if col_dlg.exec() != QDialog.Accepted:
        return
    columns = col_dlg.selected_columns()
    if not columns:
        return

    if method == ExportMethodDialog.SINGLE:
        _run_single_export(parent, sheets, columns)
    else:
        _run_multi_export(parent, sheets, columns)


def _run_single_export(
    parent: QWidget,
    sheets: dict[str, list[PresetEntry]],
    columns: list[str],
) -> None:
    path, chosen_filter = QFileDialog.getSaveFileName(
        parent,
        tr("dialog.export.save_file"),
        "",
        FILE_FILTERS,
    )
    if not path:
        return

    p = Path(path)
    fmt = _detect_format(p, chosen_filter)
    try:
        if fmt == "xlsx":
            write_xlsx_single(p, sheets, columns)
        elif fmt == "csv":
            write_csv_single(p, sheets, columns)
        elif fmt == "txt":
            write_text_single(p, sheets, columns)
        elif fmt == "md":
            write_md_single(p, sheets, columns)
        else:
            write_xlsx_single(p, sheets, columns)

        QMessageBox.information(
            parent,
            tr("dialog.export.success_title"),
            tr("dialog.export.success_single", path=str(p)),
        )
    except Exception as exc:
        logger.exception("Export failed")
        QMessageBox.warning(parent, tr("dialog.common.warning"), str(exc))


def _run_multi_export(
    parent: QWidget,
    sheets: dict[str, list[PresetEntry]],
    columns: list[str],
) -> None:
    folder = QFileDialog.getExistingDirectory(
        parent, tr("dialog.export.choose_folder")
    )
    if not folder:
        return

    fp = Path(folder)
    fmt_path, fmt_filter = QFileDialog.getSaveFileName(
        parent,
        tr("dialog.export.format_title"),
        str(fp / "sample.xlsx"),
        FILE_FILTERS,
    )
    if not fmt_path:
        return

    fmt = _detect_format(Path(fmt_path), fmt_filter)
    try:
        if fmt == "xlsx":
            count = write_xlsx_multi(fp, sheets, columns)
        elif fmt == "csv":
            count = write_csv_multi(fp, sheets, columns)
        elif fmt == "txt":
            count = write_text_multi(fp, sheets, columns)
        elif fmt == "md":
            count = write_md_multi(fp, sheets, columns)
        else:
            count = write_xlsx_multi(fp, sheets, columns)

        QMessageBox.information(
            parent,
            tr("dialog.export.success_title"),
            tr("dialog.export.success_multi", count=count, folder=str(fp)),
        )
    except Exception as exc:
        logger.exception("Export failed")
        QMessageBox.warning(parent, tr("dialog.common.warning"), str(exc))