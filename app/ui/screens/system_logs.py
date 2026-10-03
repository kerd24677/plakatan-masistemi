from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QVBoxLayout

from app.ui.screens.base import BaseScreen

_MAX_TAIL_BYTES = 200_000
_REFRESH_INTERVAL_MS = 3000


class SystemLogsScreen(BaseScreen):
    def __init__(self, ctx, parent=None) -> None:
        super().__init__(ctx, parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("Sistem Logları")
        title.setObjectName("ScreenTitle")
        header.addWidget(title)
        header.addStretch(1)
        open_folder_btn = QPushButton("Log Klasörünü Aç")
        open_folder_btn.setObjectName("SecondaryButton")
        open_folder_btn.clicked.connect(self._open_logs_folder)
        header.addWidget(open_folder_btn)
        layout.addLayout(header)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setStyleSheet("font-family: Consolas, monospace; font-size: 12px;")
        layout.addWidget(self.log_view, stretch=1)

        self._last_size = -1
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh_log)
        self._timer.start(_REFRESH_INTERVAL_MS)
        self._refresh_log()

    def on_activated(self) -> None:
        self._refresh_log(force=True)

    def _open_logs_folder(self) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.ctx.paths.logs_dir)))

    def _refresh_log(self, force: bool = False) -> None:
        log_file = self.ctx.paths.logs_dir / "application.log"
        if not log_file.exists():
            return
        size = log_file.stat().st_size
        if size == self._last_size and not force:
            return
        self._last_size = size
        try:
            with log_file.open("rb") as f:
                if size > _MAX_TAIL_BYTES:
                    f.seek(size - _MAX_TAIL_BYTES)
                content = f.read().decode("utf-8", errors="replace")
        except OSError:
            return
        scrollbar = self.log_view.verticalScrollBar()
        was_at_bottom = scrollbar.value() >= scrollbar.maximum() - 4
        self.log_view.setPlainText(content)
        if was_at_bottom:
            scrollbar.setValue(scrollbar.maximum())
