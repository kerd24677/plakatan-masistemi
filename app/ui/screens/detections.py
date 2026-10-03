from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import QDate

from app.services.export_service import export_detections_csv
from app.ui.screens.base import BaseScreen
from app.utils.plate import format_plate_display

_REVIEW_STATUS_LABELS_TR = {
    "pending": "İnceleme Bekliyor",
    "auto": "Otomatik Onaylandı",
    "confirmed": "Onaylandı",
    "rejected": "Reddedildi",
}


class DetectionsScreen(BaseScreen):
    def __init__(self, ctx, parent=None) -> None:
        super().__init__(ctx, parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Plaka Tanıma Kayıtları")
        title.setObjectName("ScreenTitle")
        layout.addWidget(title)

        filters = QHBoxLayout()
        self.plate_filter = QLineEdit()
        self.plate_filter.setPlaceholderText("Plakaya göre ara...")
        self.camera_filter = QComboBox()
        self.camera_filter.addItem("Tüm Kameralar", None)
        self.date_from = QDateEdit(QDate.currentDate().addDays(-7))
        self.date_from.setCalendarPopup(True)
        self.date_to = QDateEdit(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.review_filter = QComboBox()
        for label, value in [
            ("Tümü", None), ("İnceleme Bekliyor", "pending"), ("Otomatik Onaylandı", "auto"),
            ("Onaylandı", "confirmed"), ("Reddedildi", "rejected"),
        ]:
            self.review_filter.addItem(label, value)

        filter_button = QPushButton("Filtrele")
        filter_button.clicked.connect(self.refresh)
        export_button = QPushButton("CSV Dışa Aktar")
        export_button.setObjectName("SecondaryButton")
        export_button.clicked.connect(self._on_export)

        filters.addWidget(QLabel("Plaka:"))
        filters.addWidget(self.plate_filter)
        filters.addWidget(QLabel("Kamera:"))
        filters.addWidget(self.camera_filter)
        filters.addWidget(QLabel("Başlangıç:"))
        filters.addWidget(self.date_from)
        filters.addWidget(QLabel("Bitiş:"))
        filters.addWidget(self.date_to)
        filters.addWidget(QLabel("Durum:"))
        filters.addWidget(self.review_filter)
        filters.addWidget(filter_button)
        filters.addWidget(export_button)
        layout.addLayout(filters)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["Plaka", "Tarih-Saat", "Kamera", "Tespit Güveni", "OCR Güveni", "Yetkili", "Durum", "İşlem"]
        )
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table, stretch=1)

        self._current_results = []
        self._populate_camera_filter()
        self.refresh()

    def on_activated(self) -> None:
        self._populate_camera_filter()
        self.refresh()

    def on_detection(self, detection_id: int) -> None:
        self.refresh()

    def _populate_camera_filter(self) -> None:
        current = self.camera_filter.currentData()
        self.camera_filter.blockSignals(True)
        self.camera_filter.clear()
        self.camera_filter.addItem("Tüm Kameralar", None)
        for camera in self.ctx.camera_repo.list_all():
            self.camera_filter.addItem(camera.name, camera.id)
        if current is not None:
            idx = self.camera_filter.findData(current)
            if idx >= 0:
                self.camera_filter.setCurrentIndex(idx)
        self.camera_filter.blockSignals(False)

    def refresh(self) -> None:
        results = self.ctx.detection_repo.search(
            plate=self.plate_filter.text().strip() or None,
            camera_id=self.camera_filter.currentData(),
            date_from=self.date_from.date().toString("yyyy-MM-dd") + "T00:00:00",
            date_to=self.date_to.date().toString("yyyy-MM-dd") + "T23:59:59.999999",
            review_status=self.review_filter.currentData(),
            limit=2000,
        )
        self._current_results = results
        camera_names = {c.id: c.name for c in self.ctx.camera_repo.list_all()}

        self.table.setRowCount(len(results))
        for row, d in enumerate(results):
            self.table.setItem(row, 0, QTableWidgetItem(format_plate_display(d.plate_normalized)))
            self.table.setItem(row, 1, QTableWidgetItem(d.detected_at))
            self.table.setItem(row, 2, QTableWidgetItem(camera_names.get(d.camera_id, "-")))
            self.table.setItem(row, 3, QTableWidgetItem(f"%{d.detection_confidence * 100:.0f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"%{d.ocr_confidence * 100:.0f}"))
            self.table.setItem(row, 5, QTableWidgetItem("Evet" if d.is_authorized else "Hayır"))
            status_label = _REVIEW_STATUS_LABELS_TR.get(d.review_status, d.review_status)
            self.table.setItem(row, 6, QTableWidgetItem(status_label))

            if d.review_status == "pending":
                container = QWidget()
                h = QHBoxLayout(container)
                h.setContentsMargins(0, 0, 0, 0)
                confirm_btn = QPushButton("Onayla")
                confirm_btn.setObjectName("SecondaryButton")
                confirm_btn.clicked.connect(lambda _, did=d.id: self._on_review(did, "confirmed"))
                reject_btn = QPushButton("Reddet")
                reject_btn.setObjectName("DangerButton")
                reject_btn.clicked.connect(lambda _, did=d.id: self._on_review(did, "rejected"))
                h.addWidget(confirm_btn)
                h.addWidget(reject_btn)
                self.table.setCellWidget(row, 7, container)
            else:
                self.table.setCellWidget(row, 7, None)

    def _on_review(self, detection_id: int, status: str) -> None:
        self.ctx.detection_repo.set_review_status(detection_id, status)
        self.ctx.audit_repo.log(
            action="detection_review", entity_type="detections", entity_id=str(detection_id), details=status
        )
        self.refresh()

    def _on_export(self) -> None:
        if not self._current_results:
            QMessageBox.information(self, "Dışa Aktar", "Dışa aktarılacak kayıt bulunamadı.")
            return
        path_str, _ = QFileDialog.getSaveFileName(self, "CSV Olarak Kaydet", "tespitler.csv", "CSV (*.csv)")
        if not path_str:
            return
        from pathlib import Path

        camera_names = {c.id: c.name for c in self.ctx.camera_repo.list_all()}
        export_detections_csv(self._current_results, camera_names, Path(path_str))
        QMessageBox.information(self, "Dışa Aktar", f"{len(self._current_results)} kayıt dışa aktarıldı:\n{path_str}")
