from __future__ import annotations

from datetime import datetime, timedelta, timezone

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.ui.screens.base import BaseScreen
from app.ui.widgets.stat_card import StatCard
from app.ui.widgets.status_badge import StatusBadge
from app.utils.plate import format_plate_display


class DashboardScreen(BaseScreen):
    def __init__(self, ctx, parent=None) -> None:
        super().__init__(ctx, parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        title = QLabel("Dashboard")
        title.setObjectName("ScreenTitle")
        subtitle = QLabel("Sistem geneline hızlı bakış")
        subtitle.setObjectName("ScreenSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)
        self.card_total_today = StatCard("Bugünkü Tespitler")
        self.card_unauthorized = StatCard("Yetkisiz Araç (Bugün)")
        self.card_review = StatCard("İncelemesi Bekleyen")
        self.card_cameras = StatCard("Aktif Kamera")
        for card in (self.card_total_today, self.card_unauthorized, self.card_review, self.card_cameras):
            cards_layout.addWidget(card)
        layout.addLayout(cards_layout)

        camera_status_label = QLabel("Kamera Durumları")
        camera_status_label.setStyleSheet("font-weight: 600; margin-top: 8px;")
        layout.addWidget(camera_status_label)

        self.camera_status_grid = QGridLayout()
        self.camera_status_grid.setSpacing(10)
        layout.addLayout(self.camera_status_grid)
        self._status_badges: dict[int, StatusBadge] = {}

        recent_label = QLabel("Son Tespitler")
        recent_label.setStyleSheet("font-weight: 600; margin-top: 8px;")
        layout.addWidget(recent_label)

        self.recent_table = QTableWidget(0, 5)
        self.recent_table.setHorizontalHeaderLabels(
            ["Plaka", "Kamera", "Tarih-Saat", "Güven", "Durum"]
        )
        self.recent_table.horizontalHeader().setStretchLastSection(True)
        self.recent_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.recent_table.verticalHeader().setVisible(False)
        layout.addWidget(self.recent_table, stretch=1)

        self._rebuild_camera_status_grid()
        self.refresh()

    def on_activated(self) -> None:
        self.refresh()

    def on_detection(self, detection_id: int) -> None:
        self.refresh()

    def on_status(self, camera_id: int, status: str, error: str) -> None:
        if camera_id in self._status_badges:
            self._status_badges[camera_id].set_status(status, error)
        else:
            self._rebuild_camera_status_grid()

    def _rebuild_camera_status_grid(self) -> None:
        while self.camera_status_grid.count():
            item = self.camera_status_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._status_badges.clear()

        cameras = self.ctx.camera_repo.list_all()
        for i, camera in enumerate(cameras):
            name_label = QLabel(camera.name)
            badge = StatusBadge(camera.status)
            row_widget_layout = QHBoxLayout()
            row_widget_layout.addWidget(name_label)
            row_widget_layout.addWidget(badge)
            self.camera_status_grid.addWidget(name_label, i, 0)
            self.camera_status_grid.addWidget(badge, i, 1)
            self._status_badges[camera.id] = badge

        self.card_cameras.set_value(str(sum(1 for c in cameras if c.enabled)))

    def refresh(self) -> None:
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        detections_today = self.ctx.detection_repo.search(date_from=today_start.isoformat(), limit=5000)
        unauthorized_today = [d for d in detections_today if not d.is_authorized]
        pending_review = self.ctx.detection_repo.search(review_status="pending", limit=5000)

        self.card_total_today.set_value(str(len(detections_today)))
        self.card_unauthorized.set_value(str(len(unauthorized_today)))
        self.card_review.set_value(str(len(pending_review)))

        camera_names = {c.id: c.name for c in self.ctx.camera_repo.list_all()}
        recent = self.ctx.detection_repo.search(limit=25)
        self.recent_table.setRowCount(len(recent))
        for row, d in enumerate(recent):
            self.recent_table.setItem(row, 0, QTableWidgetItem(format_plate_display(d.plate_normalized)))
            self.recent_table.setItem(row, 1, QTableWidgetItem(camera_names.get(d.camera_id, "-")))
            self.recent_table.setItem(row, 2, QTableWidgetItem(d.detected_at))
            avg_conf = (d.detection_confidence + d.ocr_confidence) / 2 * 100
            self.recent_table.setItem(row, 3, QTableWidgetItem(f"%{avg_conf:.0f}"))
            status_text = "İnceleme Bekliyor" if d.needs_review else "Otomatik Onaylandı"
            self.recent_table.setItem(row, 4, QTableWidgetItem(status_text))
