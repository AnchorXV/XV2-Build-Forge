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

from locales.i18n_manager import tr
from models.exporters import (
    write_csv_multi,
    write_csv_single,
    write_xlsx_multi,
    write_xlsx_single,
)
from models.schemas import PresetEntry

logger = logging.getLogger(__name__)


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

    if method == ExportMethodDialog.SINGLE:
        _run_single_export(parent, sheets)
    else:
        _run_multi_export(parent, sheets)


def _run_single_export(parent: QWidget, sheets: dict[str, list[PresetEntry]]) -> None:
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
            write_xlsx_single(p, sheets)
        else:
            write_csv_single(p, sheets)
        QMessageBox.information(
            parent,
            tr("dialog.export.success_title"),
            tr("dialog.export.success_single", path=str(p)),
        )
    except Exception as exc:
        logger.exception("Export failed")
        QMessageBox.warning(parent, tr("dialog.common.warning"), str(exc))


def _run_multi_export(parent: QWidget, sheets: dict[str, list[PresetEntry]]) -> None:
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
        "Excel Workbook (*.xlsx);;CSV File (*.csv)",
    )
    if not fmt_path:
        return

    use_xlsx = fmt_filter.startswith("Excel") or Path(fmt_path).suffix.lower() == ".xlsx"
    try:
        count = (
            write_xlsx_multi(fp, sheets) if use_xlsx else write_csv_multi(fp, sheets)
        )
        QMessageBox.information(
            parent,
            tr("dialog.export.success_title"),
            tr("dialog.export.success_multi", count=count, folder=str(fp)),
        )
    except Exception as exc:
        logger.exception("Export failed")
        QMessageBox.warning(parent, tr("dialog.common.warning"), str(exc))