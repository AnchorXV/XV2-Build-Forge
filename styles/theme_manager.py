from __future__ import annotations

import logging
import re

from PySide6.QtWidgets import QApplication

from app_config import get_resource_path

logger = logging.getLogger(__name__)


def _resolve_asset_urls(qss: str) -> str:
    assets_root = get_resource_path("assets")
    normalized = str(assets_root).replace("\\", "/")

    def _replace(match: re.Match) -> str:
        inner = match.group(1).strip().strip("'\"")
        if inner.startswith(":/") or inner.startswith("http"):
            return match.group(0)
        if "assets/" in inner:
            rel = inner.split("assets/", 1)[1]
            return f'url("{normalized}/{rel}")'
        return match.group(0)

    return re.sub(r"url\(([^)]+)\)", _replace, qss)


def apply_theme(app: QApplication) -> None:
    qss_path = get_resource_path("styles/dark_theme.qss")
    try:
        with open(qss_path, "r", encoding="utf-8") as f:
            qss = f.read()
        qss = _resolve_asset_urls(qss)
        app.setStyleSheet(qss)
        logger.info("Applied dark theme.")
    except OSError as exc:
        logger.warning("Failed to load QSS file %s: %s", qss_path, exc)