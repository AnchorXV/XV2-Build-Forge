from __future__ import annotations

import logging

from PySide6.QtWidgets import QApplication

from app_config import get_resource_path

logger = logging.getLogger(__name__)


def apply_theme(app: QApplication) -> None:
    qss_path = get_resource_path("styles/dark_theme.qss")
    try:
        with open(qss_path, "r", encoding="utf-8") as f:
            qss = f.read()
        app.setStyleSheet(qss)
        logger.info("Applied dark theme.")
    except OSError as exc:
        logger.warning("Failed to load QSS file %s: %s", qss_path, exc)