import logging
import sys

from PySide6.QtCore import Qt, QtMsgType, qInstallMessageHandler
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QFontDatabase

from typing import Optional

from app_config import APP_NAME, APP_ORG, APP_VERSION, get_resource_path
from controllers.app_controller import AppController

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("DBXV2BuildForge")

def _qt_msg_handler(msg_type, context, message):
    if "setPointSize" in message:
        return
    if msg_type in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg):
        sys.stderr.write(f"[Qt] {message}\n")

def _load_fonts(app: QApplication) -> None:
    font_files = [
        "assets/fonts/PlusJakartaSans-VariableFont_wght.ttf",
    ]

    loaded_family: Optional[str] = None

    for rel_path in font_files:
        path = get_resource_path(rel_path)
        if not path.exists():
            logger.warning("Font not found: %s", path)
            continue
        font_id = QFontDatabase.addApplicationFont(str(path))
        if font_id == -1:
            logger.warning("Failed to load font: %s", path)
            continue

        families = QFontDatabase.applicationFontFamilies(font_id)
        logger.info("Loaded font: %s", families)

        # Pilih family "utama" — yang paling pendek namanya
        if families and loaded_family is None:
            loaded_family = min(families, key=len)

    # Verify family benar-benar ada di QFontDatabase
    if loaded_family and loaded_family in QFontDatabase.families():
        base_font = QFont(loaded_family, 10)
        logger.info("Using base font: %s", loaded_family)
    else:
        base_font = QFont("Segoe UI", 10)
        logger.info("Falling back to Segoe UI")

    app.setFont(base_font)

def is_compiled() -> bool:
    return getattr(sys, "frozen", False) or "__compiled__" in globals()


def main() -> int:
    qInstallMessageHandler(_qt_msg_handler)
    logger.info("Starting %s v%s (compiled=%s)...", APP_NAME, APP_VERSION, is_compiled())

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_ORG)
    app.setApplicationVersion(APP_VERSION)

    _load_fonts(app)

    controller = AppController(app)
    controller.start()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())