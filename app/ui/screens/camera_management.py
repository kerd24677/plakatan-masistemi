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
)

from app.ui.dialogs.camera_dialog import CameraDialog
from app.ui.screens.base import BaseScreen
from app.ui.widgets.status_badge import StatusBadge


class CameraManagementScreen(BaseScreen):
    def __init__(self, ctx, parent=None) -> None:
        super().__init__(ctx, parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("Kamera Yönetimi")
        title.setObjectName("ScreenTitle")
        header.addWidget(title)
        header.addStretch(1)
        add_button = QPushButton("+ Kamera Ekle")
        add_button.clicked.connect(self._on_add)
        header.addWidget(add_button)
        layout.addLayout(header)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["Ad", "Host", "Konum", "Protokol", "Etkin", "Durum", "İşlemler"]
        )
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table, stretch=1)

        self.refresh()

    def on_activated(self) -> None:
        self.refresh()

    def on_status(self, camera_id: int, status: str, error: str) -> None:
        self.refresh()

    def refresh(self) -> None:
        cameras = self.ctx.camera_repo.list_all()
        self.table.setRowCount(len(cameras))
        for row, camera in enumerate(cameras):
            self.table.setItem(row, 0, QTableWidgetItem(camera.name))
            host_display = "Demo/Test Kaynağı" if camera.host == "DEMO" else camera.host
            self.table.setItem(row, 1, QTableWidgetItem(host_display))
            self.table.setItem(row, 2, QTableWidgetItem(camera.location))
            self.table.setItem(row, 3, QTableWidgetItem(camera.transport.upper()))
            self.table.setItem(row, 4, QTableWidgetItem("Evet" if camera.enabled else "Hayır"))
            self.table.setCellWidget(row, 5, StatusBadge(camera.status, error_message=camera.last_error))

            edit_btn = QPushButton("Düzenle")
            edit_btn.setObjectName("SecondaryButton")
            edit_btn.clicked.connect(lambda _, c=camera: self._on_edit(c))
            reconnect_btn = QPushButton("Yeniden Bağlan")
            reconnect_btn.setObjectName("SecondaryButton")
            reconnect_btn.setEnabled(camera.enabled)
            reconnect_btn.clicked.connect(lambda _, c=camera: self._on_reconnect(c))
            delete_btn = QPushButton("Sil")
            delete_btn.setObjectName("DangerButton")
            delete_btn.clicked.connect(lambda _, c=camera: self._on_delete(c))
            from PySide6.QtWidgets import QWidget

            container = QWidget()
            h = QHBoxLayout(container)
            h.setContentsMargins(0, 0, 0, 0)
            h.addWidget(edit_btn)
            h.addWidget(reconnect_btn)
            h.addWidget(delete_btn)
            self.table.setCellWidget(row, 6, container)

    def _on_add(self) -> None:
        dialog = CameraDialog(self.ctx.credentials, parent=self)
        if dialog.exec():
            fields = dialog.result_camera_fields
            camera_id = self.ctx.camera_repo.create(
                name=fields["name"], host=fields["host"], port=fields["port"],
                main_path=fields["main_path"], sub_path=fields["sub_path"],
                username=fields["username"], credential_ref="",
                transport=fields["transport"], location=fields["location"],
            )
            credential_ref = dialog.save_credentials(camera_id)
            self.ctx.db.execute(
                "UPDATE cameras SET credential_ref = ? WHERE id = ?", (credential_ref, camera_id)
            )
            if fields["enabled"]:
                self.ctx.camera_manager.start_camera(camera_id)
            self.ctx.audit_repo.log(action="camera_created", entity_type="cameras", entity_id=str(camera_id))
            self.refresh()

    def _on_edit(self, camera) -> None:
        dialog = CameraDialog(self.ctx.credentials, camera=camera, parent=self)
        if dialog.exec():
            fields = dialog.result_camera_fields
            self.ctx.camera_repo.update(
                camera.id, name=fields["name"], host=fields["host"], port=fields["port"],
                main_path=fields["main_path"], sub_path=fields["sub_path"],
                username=fields["username"], transport=fields["transport"],
                location=fields["location"], enabled=fields["enabled"],
            )
            dialog.save_credentials(camera.id)
            self.ctx.camera_manager.stop_camera(camera.id)
            if fields["enabled"]:
                self.ctx.camera_manager.start_camera(camera.id)
            self.ctx.audit_repo.log(action="camera_updated", entity_type="cameras", entity_id=str(camera.id))
            self.refresh()

    def _on_reconnect(self, camera) -> None:
        self.ctx.camera_manager.restart_camera(camera.id)
        self.ctx.audit_repo.log(action="camera_reconnect", entity_type="cameras", entity_id=str(camera.id))
        self.refresh()

    def _on_delete(self, camera) -> None:
        confirm = QMessageBox.question(
            self, "Kamerayı Sil",
            f"'{camera.name}' kamerasını silmek istediğinize emin misiniz? "
            "Bu kameraya ait geçmiş tespit kayıtları da silinecektir.",
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self.ctx.camera_manager.stop_camera(camera.id)
        self.ctx.credentials.delete_password(camera.credential_ref)
        self.ctx.camera_repo.delete(camera.id)
        self.ctx.audit_repo.log(action="camera_deleted", entity_type="cameras", entity_id=str(camera.id))
        self.refresh()
