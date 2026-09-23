"""
DBXV2 Build Forge — Main Entry Point.

Modular MVC application entry point (PRD §2.1).
Supports development mode and Nuitka compiled onefile mode.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from app_config import APP_NAME, APP_ORG, APP_VERSION
from controllers.app_controller import AppController

# ── Logging Configuration ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("DBXV2BuildForge")


def is_compiled() -> bool:
    """Return True if running in a Nuitka or PyInstaller compiled binary."""
    return getattr(sys, "frozen", False) or "__compiled__" in globals()


def main() -> int:
    """Main application routine."""
    logger.info("Starting %s v%s (compiled=%s)...", APP_NAME, APP_VERSION, is_compiled())

    # High-DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_ORG)
    app.setApplicationVersion(APP_VERSION)

    # Force global text color to white for better dark theme visibility in item views
    palette = app.palette()
    palette.setColor(QPalette.WindowText, QColor("#FFFFFF"))
    palette.setColor(QPalette.Text, QColor("#FFFFFF"))
    app.setPalette(palette)

    controller = AppController(app)
    controller.start()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())