from __future__ import annotations

import secrets

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from app.camera.connection_test import ConnectionTestResult, test_connection
from app.camera.manager import DEMO_HOST_SENTINEL
from app.database.models import Camera


class _ConnectionTestThread(QThread):
    finished_with_result = Signal(object)

    def __init__(self, url: str, transport: str, parent=None) -> None:
        super().__init__(parent)
        self._url = url
        self._transport = transport

    def run(self) -> None:
        result = test_connection(self._url, self._transport)
        self.finished_with_result.emit(result)


class CameraDialog(QDialog):
    """Kamera ekleme/düzenleme diyaloğu. Parola veritabanına yazılmaz;
    kaydedildiğinde CredentialStore üzerinden OS kimlik bilgisi deposuna
    (Windows'ta Credential Manager) yazılır."""

    def __init__(self, credential_store, camera: Camera | None = None, parent=None) -> None:
        super().__init__(parent)
        self._credential_store = credential_store
        self._camera = camera
        self._test_thread: _ConnectionTestThread | None = None
        self.setWindowTitle("Kamera Düzenle" if camera else "Yeni Kamera Ekle")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        self.name_edit = QLineEdit(camera.name if camera else "")
        self.demo_checkbox = QCheckBox("Demo/Test kaynağı kullan (gerçek RTSP kamera gerekmez)")
        self.demo_checkbox.setChecked(bool(camera and camera.host == DEMO_HOST_SENTINEL))
        self.host_edit = QLineEdit(camera.host if camera and camera.host != DEMO_HOST_SENTINEL else "")
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(camera.port if camera else 554)
        self.main_path_edit = QLineEdit(camera.main_path if camera else "")
        self.sub_path_edit = QLineEdit(camera.sub_path if camera else "")
        self.username_edit = QLineEdit(camera.username if camera else "")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText(
            "Değiştirmek için girin (boş bırakılırsa mevcut parola korunur)" if camera else ""
        )
        self.transport_combo = QComboBox()
        self.transport_combo.addItems(["tcp", "udp"])
        if camera:
            self.transport_combo.setCurrentText(camera.transport)
        self.location_edit = QLineEdit(camera.location if camera else "")
        self.enabled_checkbox = QCheckBox("Etkin")
        self.enabled_checkbox.setChecked(camera.enabled if camera else True)

        form.addRow("Kamera Adı *", self.name_edit)
        form.addRow("", self.demo_checkbox)
        form.addRow("Host / IP *", self.host_edit)
        form.addRow("Port", self.port_spin)
        form.addRow("Ana Akış Yolu (örn. stream1)", self.main_path_edit)
        form.addRow("Alt Akış Yolu (opsiyonel)", self.sub_path_edit)
        form.addRow("Kullanıcı Adı", self.username_edit)
        form.addRow("Parola", self.password_edit)
        form.addRow("Taşıma Protokolü", self.transport_combo)
        form.addRow("Konum / Açıklama", self.location_edit)
        form.addRow("", self.enabled_checkbox)

        layout.addLayout(form)

        self.test_result_label = QLabel("")
        layout.addWidget(self.test_result_label)

        self.test_button = QPushButton("Bağlantıyı Test Et")
        self.test_button.setObjectName("SecondaryButton")
        self.test_button.clicked.connect(self._on_test_connection)
        layout.addWidget(self.test_button)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.demo_checkbox.toggled.connect(self._on_demo_toggled)
        self._on_demo_toggled(self.demo_checkbox.isChecked())

        self.result_camera_fields: dict | None = None

    def _on_demo_toggled(self, checked: bool) -> None:
        for widget in (
            self.host_edit, self.port_spin, self.main_path_edit, self.sub_path_edit,
            self.username_edit, self.password_edit, self.transport_combo,
        ):
            widget.setDisabled(checked)

    def _build_rtsp_url_for_test(self) -> tuple[str, str]:
        if self.demo_checkbox.isChecked():
            from pathlib import Path

            from app.camera.demo_source import ensure_demo_video
            from app.config.paths import APP_PATHS

            path = ensure_demo_video(APP_PATHS.assets_dir / "demo")
            return str(path), "tcp"
        auth = ""
        if self.username_edit.text():
            auth = f"{self.username_edit.text()}:{self.password_edit.text()}@"
        url = f"rtsp://{auth}{self.host_edit.text()}:{self.port_spin.value()}/{self.main_path_edit.text().lstrip('/')}"
        return url, self.transport_combo.currentText()

    def _on_test_connection(self) -> None:
        if not self.demo_checkbox.isChecked() and not self.host_edit.text():
            QMessageBox.warning(self, "Eksik Bilgi", "Lütfen host/IP adresini girin.")
            return
        url, transport = self._build_rtsp_url_for_test()
        self.test_button.setEnabled(False)
        self.test_result_label.setText("Bağlantı test ediliyor...")
        self.test_result_label.setStyleSheet("color: #F5A623;")
        self._test_thread = _ConnectionTestThread(url, transport, self)
        self._test_thread.finished_with_result.connect(self._on_test_result)
        self._test_thread.start()

    def _on_test_result(self, result: ConnectionTestResult) -> None:
        self.test_button.setEnabled(True)
        if result.success:
            self.test_result_label.setText(f"✓ {result.message} ({result.width}x{result.height})")
            self.test_result_label.setStyleSheet("color: #2ECC71;")
        else:
            self.test_result_label.setText(f"✗ {result.message}")
            self.test_result_label.setStyleSheet("color: #E74C3C;")

    def _on_accept(self) -> None:
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Eksik Bilgi", "Kamera adı zorunludur.")
            return
        if not self.demo_checkbox.isChecked() and not self.host_edit.text().strip():
            QMessageBox.warning(self, "Eksik Bilgi", "Host/IP adresi zorunludur.")
            return

        self.result_camera_fields = {
            "name": self.name_edit.text().strip(),
            "host": DEMO_HOST_SENTINEL if self.demo_checkbox.isChecked() else self.host_edit.text().strip(),
            "port": self.port_spin.value(),
            "main_path": self.main_path_edit.text().strip(),
            "sub_path": self.sub_path_edit.text().strip(),
            "username": self.username_edit.text().strip(),
            "transport": self.transport_combo.currentText(),
            "location": self.location_edit.text().strip(),
            "enabled": self.enabled_checkbox.isChecked(),
            "password": self.password_edit.text(),
        }
        self.accept()

    def save_credentials(self, camera_id: int) -> str:
        """Parolayı kimlik bilgisi deposuna yazar ve credential_ref döndürür."""
        credential_ref = self._camera.credential_ref if self._camera else f"camera_{camera_id}_{secrets.token_hex(4)}"
        password = self.result_camera_fields["password"]
        if password:
            self._credential_store.set_password(credential_ref, password)
        elif not self._camera:
            self._credential_store.set_password(credential_ref, "")
        return credential_ref
