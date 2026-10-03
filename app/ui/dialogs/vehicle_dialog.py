from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from app.database.models import AuthorizedVehicle
from app.utils.plate import normalize_plate


class VehicleDialog(QDialog):
    def __init__(self, vehicle: AuthorizedVehicle | None = None, parent=None) -> None:
        super().__init__(parent)
        self._vehicle = vehicle
        self.setWindowTitle("Yetkili Araç Düzenle" if vehicle else "Yetkili Araç Ekle")
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.plate_edit = QLineEdit(vehicle.plate_normalized if vehicle else "")
        self.plate_edit.setPlaceholderText("Örn: 34 ABC 123")
        if vehicle:
            self.plate_edit.setDisabled(True)
        self.description_edit = QLineEdit(vehicle.description if vehicle else "")
        self.status_combo = QComboBox()
        self.status_combo.addItems(["active", "suspended"])
        if vehicle:
            self.status_combo.setCurrentText(vehicle.permission_status)

        form.addRow("Plaka *", self.plate_edit)
        form.addRow("Açıklama", self.description_edit)
        form.addRow("İzin Durumu", self.status_combo)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.result_fields: dict | None = None

    def _on_accept(self) -> None:
        normalized = normalize_plate(self.plate_edit.text())
        if normalized is None:
            QMessageBox.warning(
                self, "Geçersiz Plaka",
                "Girilen plaka geçerli bir Türk plaka biçimine uymuyor (örn. 34 ABC 123).",
            )
            return
        self.result_fields = {
            "plate_normalized": normalized,
            "description": self.description_edit.text().strip(),
            "permission_status": self.status_combo.currentText(),
        }
        self.accept()
