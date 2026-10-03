from __future__ import annotations

from PySide6.QtWidgets import QWidget


class BaseScreen(QWidget):
    """Tüm ekranlar için ortak arayüz. MainWindow, kamera/tespit olaylarını
    her ekrana bu hook'lar üzerinden iletir; ilgisiz ekranlar no-op kalır."""

    def __init__(self, ctx, parent=None) -> None:
        super().__init__(parent)
        self.ctx = ctx

    def on_frame(self, camera_id: int, frame) -> None:
        pass

    def on_status(self, camera_id: int, status: str, error: str) -> None:
        pass

    def on_detection(self, detection_id: int) -> None:
        pass

    def on_activated(self) -> None:
        """Ekran sekmesi açıldığında çağrılır (tembel yenileme için)."""
        pass
