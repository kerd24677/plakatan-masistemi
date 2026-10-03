from __future__ import annotations

from collections import Counter

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDateEdit,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.ui.screens.base import BaseScreen


class ReportingScreen(BaseScreen):
    def __init__(self, ctx, parent=None) -> None:
        super().__init__(ctx, parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Raporlama")
        title.setObjectName("ScreenTitle")
        layout.addWidget(title)

        filters = QHBoxLayout()
        self.date_from = QDateEdit(QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True)
        self.date_to = QDateEdit(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        generate_button = QPushButton("Rapor Oluştur")
        generate_button.clicked.connect(self.refresh)
        filters.addWidget(QLabel("Başlangıç:"))
        filters.addWidget(self.date_from)
        filters.addWidget(QLabel("Bitiş:"))
        filters.addWidget(self.date_to)
        filters.addWidget(generate_button)
        filters.addStretch(1)
        layout.addLayout(filters)

        chart_label = QLabel("Kameraya Göre Tespit Sayısı")
        chart_label.setStyleSheet("font-weight: 600;")
        layout.addWidget(chart_label)
        self.chart_layout = QVBoxLayout()
        layout.addLayout(self.chart_layout)

        table_label = QLabel("Özet Tablo")
        table_label.setStyleSheet("font-weight: 600; margin-top: 8px;")
        layout.addWidget(table_label)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Kamera", "Toplam Tespit", "Yetkisiz", "İncelemede"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table, stretch=1)

        self.refresh()

    def on_activated(self) -> None:
        self.refresh()

    def refresh(self) -> None:
        date_from = self.date_from.date().toString("yyyy-MM-dd") + "T00:00:00"
        date_to = self.date_to.date().toString("yyyy-MM-dd") + "T23:59:59.999999"
        results = self.ctx.detection_repo.search(date_from=date_from, date_to=date_to, limit=100000)
        camera_names = {c.id: c.name for c in self.ctx.camera_repo.list_all()}

        total_counter = Counter(d.camera_id for d in results)
        unauthorized_counter = Counter(d.camera_id for d in results if not d.is_authorized)
        review_counter = Counter(d.camera_id for d in results if d.needs_review)

        while self.chart_layout.count():
            item = self.chart_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        max_count = max(total_counter.values(), default=1)
        for camera_id, count in sorted(total_counter.items(), key=lambda x: -x[1]):
            row = QHBoxLayout()
            name_label = QLabel(camera_names.get(camera_id, f"Kamera #{camera_id}"))
            name_label.setFixedWidth(160)
            bar = QProgressBar()
            bar.setMaximum(max_count)
            bar.setValue(count)
            bar.setFormat(f"{count}")
            row.addWidget(name_label)
            row.addWidget(bar)
            from PySide6.QtWidgets import QWidget

            row_widget = QWidget()
            row_widget.setLayout(row)
            self.chart_layout.addWidget(row_widget)

        camera_ids = sorted(total_counter.keys(), key=lambda cid: -total_counter[cid])
        self.table.setRowCount(len(camera_ids))
        for row, camera_id in enumerate(camera_ids):
            self.table.setItem(row, 0, QTableWidgetItem(camera_names.get(camera_id, f"Kamera #{camera_id}")))
            self.table.setItem(row, 1, QTableWidgetItem(str(total_counter[camera_id])))
            self.table.setItem(row, 2, QTableWidgetItem(str(unauthorized_counter.get(camera_id, 0))))
            self.table.setItem(row, 3, QTableWidgetItem(str(review_counter.get(camera_id, 0))))
