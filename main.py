from __future__ import annotations

import logging
import sys

from PySide6.QtCore import Qt
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

    # ── Note: Global palette override intentionally removed. ──────────
    # Earlier versions forced QPalette.WindowText and QPalette.Text to
    # white globally to make item views readable in the dark theme. That
    # approach broke the light theme and any widget not explicitly styled
    # via QSS (notably QToolTip and QMessageBox), producing white text on
    # white/yellow backgrounds.
    #
    # All theme colors are now controlled exclusively by the QSS files in
    # styles/. Do NOT reintroduce a palette override here.

    controller = AppController(app)
    controller.start()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())