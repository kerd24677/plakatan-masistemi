from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.ui.dialogs.vehicle_dialog import VehicleDialog
from app.ui.screens.base import BaseScreen
from app.utils.plate import format_plate_display


class AuthorizedVehiclesScreen(BaseScreen):
    def __init__(self, ctx, parent=None) -> None:
        super().__init__(ctx, parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("Yetkili Araçlar")
        title.setObjectName("ScreenTitle")
        header.addWidget(title)
        header.addStretch(1)
        add_button = QPushButton("+ Araç Ekle")
        add_button.clicked.connect(self._on_add)
        header.addWidget(add_button)
        layout.addLayout(header)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Plaka", "Açıklama", "İzin Durumu", "İşlemler"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table, stretch=1)

        self.refresh()

    def on_activated(self) -> None:
        self.refresh()

    def refresh(self) -> None:
        vehicles = self.ctx.vehicle_repo.list_all()
        self.table.setRowCount(len(vehicles))
        for row, v in enumerate(vehicles):
            self.table.setItem(row, 0, QTableWidgetItem(format_plate_display(v.plate_normalized)))
            self.table.setItem(row, 1, QTableWidgetItem(v.description))
            status_text = "Aktif" if v.permission_status == "active" else "Askıya Alındı"
            self.table.setItem(row, 2, QTableWidgetItem(status_text))

            container = QWidget()
            h = QHBoxLayout(container)
            h.setContentsMargins(0, 0, 0, 0)
            edit_btn = QPushButton("Düzenle")
            edit_btn.setObjectName("SecondaryButton")
            edit_btn.clicked.connect(lambda _, vv=v: self._on_edit(vv))
            delete_btn = QPushButton("Sil")
            delete_btn.setObjectName("DangerButton")
            delete_btn.clicked.connect(lambda _, vv=v: self._on_delete(vv))
            h.addWidget(edit_btn)
            h.addWidget(delete_btn)
            self.table.setCellWidget(row, 3, container)

    def _on_add(self) -> None:
        dialog = VehicleDialog(parent=self)
        if dialog.exec():
            fields = dialog.result_fields
            try:
                vehicle_id = self.ctx.vehicle_repo.create(**fields)
            except Exception:
                QMessageBox.warning(self, "Hata", "Bu plaka zaten yetkili araçlar listesinde mevcut.")
                return
            self.ctx.audit_repo.log(
                action="vehicle_created", entity_type="authorized_vehicles", entity_id=str(vehicle_id)
            )
            self.refresh()

    def _on_edit(self, vehicle) -> None:
        dialog = VehicleDialog(vehicle=vehicle, parent=self)
        if dialog.exec():
            fields = dialog.result_fields
            self.ctx.vehicle_repo.update(
                vehicle.id, description=fields["description"], permission_status=fields["permission_status"]
            )
            self.ctx.audit_repo.log(
                action="vehicle_updated", entity_type="authorized_vehicles", entity_id=str(vehicle.id)
            )
            self.refresh()

    def _on_delete(self, vehicle) -> None:
        confirm = QMessageBox.question(
            self, "Araç Sil", f"'{vehicle.plate_normalized}' plakasını silmek istediğinize emin misiniz?"
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self.ctx.vehicle_repo.delete(vehicle.id)
        self.ctx.audit_repo.log(
            action="vehicle_deleted", entity_type="authorized_vehicles", entity_id=str(vehicle.id)
        )
        self.refresh()
