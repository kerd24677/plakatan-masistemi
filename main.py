"""Plaka Tanıma Sistemi - uygulama giriş noktası."""

from __future__ import annotations

import logging
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from app.services.app_context import AppContext
from app.services.retention_service import purge_expired_detections
from app.ui.dialogs.login_dialog import LoginDialog
from app.ui.main_window import MainWindow
from app.ui.theme import DARK_QSS
from app.utils.tesseract_locator import configure_tesseract_path

logger = logging.getLogger(__name__)

_RETENTION_CHECK_INTERVAL_MS = 6 * 60 * 60 * 1000  # 6 saatte bir


def main() -> int:
    configure_tesseract_path()
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_QSS)

    ctx = AppContext()

    is_first_run = ctx.user_repo.count() <= 1
    login = LoginDialog(ctx.auth_service, show_default_hint=is_first_run)
    if not login.exec():
        ctx.shutdown()
        return 0

    ctx.start()

    def run_retention_check() -> None:
        try:
            purge_expired_detections(ctx.detection_repo, ctx.audit_repo, ctx.settings.retention_days)
        except Exception:
            logger.exception("Saklama süresi temizliği başarısız oldu")

    retention_timer = QTimer()
    retention_timer.timeout.connect(run_retention_check)
    retention_timer.start(_RETENTION_CHECK_INTERVAL_MS)
    QTimer.singleShot(2000, run_retention_check)

    window = MainWindow(ctx)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
