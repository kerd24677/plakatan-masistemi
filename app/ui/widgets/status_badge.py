from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from app.ui.theme import STATUS_COLORS, STATUS_LABELS_TR


class StatusBadge(QWidget):
    """Kamera/sistem durumunu renkli nokta + metin olarak gösterir."""

    def __init__(self, status: str = "disconnected", error_message: str | None = None, parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._dot = QLabel("●")
        self._text = QLabel()
        layout.addWidget(self._dot)
        layout.addWidget(self._text)
        layout.addStretch(1)
        self.set_status(status, error_message)

    def set_status(self, status: str, error_message: str | None = None) -> None:
        color = STATUS_COLORS.get(status, STATUS_COLORS["disconnected"])
        label = STATUS_LABELS_TR.get(status, status)
        self._dot.setStyleSheet(f"color: {color}; font-size: 14px;")
        self._text.setText(label)
        self._text.setStyleSheet(f"color: {color}; font-weight: 600;")
        tooltip = error_message or ""
        self.setToolTip(tooltip)
