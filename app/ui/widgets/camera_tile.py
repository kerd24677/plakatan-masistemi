from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout

from app.ui.widgets.image_convert import bgr_frame_to_qpixmap
from app.ui.widgets.status_badge import StatusBadge


class CameraTile(QFrame):
    """Canlı izleme ve dashboard'da tekrar kullanılan tek kamera görünümü."""

    def __init__(self, camera_id: int, camera_name: str, parent=None) -> None:
        super().__init__(parent)
        self.camera_id = camera_id
        self.setObjectName("Card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        header = QHBoxLayout()
        self._name_label = QLabel(camera_name)
        self._name_label.setStyleSheet("font-weight: 600;")
        self._status_badge = StatusBadge("disconnected")
        header.addWidget(self._name_label)
        header.addStretch(1)
        header.addWidget(self._status_badge)
        layout.addLayout(header)

        self._image_label = QLabel("Görüntü bekleniyor...")
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setMinimumSize(320, 180)
        self._image_label.setStyleSheet("background-color: #0C0E12; border-radius: 6px; color: #9AA2AF;")
        self._image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self._image_label, stretch=1)

    def set_camera_name(self, name: str) -> None:
        self._name_label.setText(name)

    def update_frame(self, frame) -> None:
        pixmap = bgr_frame_to_qpixmap(frame)
        scaled = pixmap.scaled(
            self._image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._image_label.setPixmap(scaled)

    def set_status(self, status: str, error_message: str = "") -> None:
        self._status_badge.set_status(status, error_message)
        if status != "connected":
            self._image_label.clear()
            self._image_label.setText("Görüntü yok")
