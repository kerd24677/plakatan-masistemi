from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from app.ui.screens.base import BaseScreen


class SettingsScreen(BaseScreen):
    def __init__(self, ctx, parent=None) -> None:
        super().__init__(ctx, parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Ayarlar")
        title.setObjectName("ScreenTitle")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)

        self.detection_threshold = QDoubleSpinBox()
        self.detection_threshold.setRange(0.0, 1.0)
        self.detection_threshold.setSingleStep(0.05)
        self.detection_threshold.setToolTip(
            "Bu değerin altındaki tespitler otomatik kabul edilmez, incelemeye işaretlenir."
        )

        self.ocr_threshold = QDoubleSpinBox()
        self.ocr_threshold.setRange(0.0, 1.0)
        self.ocr_threshold.setSingleStep(0.05)

        self.dedup_window = QSpinBox()
        self.dedup_window.setRange(1, 300)
        self.dedup_window.setSuffix(" sn")
        self.dedup_window.setToolTip("Aynı plakanın aynı kamerada tekrar kaydedilmemesi için bekleme süresi.")

        self.retention_days = QSpinBox()
        self.retention_days.setRange(1, 3650)
        self.retention_days.setSuffix(" gün")

        self.rtsp_transport = QComboBox()
        self.rtsp_transport.addItems(["tcp", "udp"])

        self.save_images = QCheckBox("Tespit edilen plaka görüntülerini diske kaydet")

        form.addRow("Plaka Tespit Güven Eşiği", self.detection_threshold)
        form.addRow("OCR Güven Eşiği", self.ocr_threshold)
        form.addRow("Tekrar Önleme Penceresi", self.dedup_window)
        form.addRow("Kayıt Saklama Süresi", self.retention_days)
        form.addRow("Varsayılan RTSP Taşıma Protokolü", self.rtsp_transport)
        form.addRow("", self.save_images)

        layout.addLayout(form)

        save_button = QPushButton("Ayarları Kaydet")
        save_button.clicked.connect(self._on_save)
        layout.addWidget(save_button)
        layout.addStretch(1)

        self._load_from_settings()

    def on_activated(self) -> None:
        self._load_from_settings()

    def _load_from_settings(self) -> None:
        s = self.ctx.settings
        self.detection_threshold.setValue(s.detection_confidence_threshold)
        self.ocr_threshold.setValue(s.ocr_confidence_threshold)
        self.dedup_window.setValue(int(s.dedup_window_seconds))
        self.retention_days.setValue(s.retention_days)
        self.rtsp_transport.setCurrentText(s.rtsp_transport)
        self.save_images.setChecked(s.save_detection_images)

    def _on_save(self) -> None:
        s = self.ctx.settings
        s.detection_confidence_threshold = self.detection_threshold.value()
        s.ocr_confidence_threshold = self.ocr_threshold.value()
        s.dedup_window_seconds = float(self.dedup_window.value())
        s.retention_days = self.retention_days.value()
        s.rtsp_transport = self.rtsp_transport.currentText()
        s.save_detection_images = self.save_images.isChecked()
        s.save(self.ctx.settings_repo)
        self.ctx.reload_settings()
        self.ctx.audit_repo.log(action="settings_updated", entity_type="application_settings")
        QMessageBox.information(self, "Ayarlar", "Ayarlar kaydedildi.")
