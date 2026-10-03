from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)


class LoginDialog(QDialog):
    def __init__(self, auth_service, show_default_hint: bool = False, parent=None) -> None:
        super().__init__(parent)
        self._auth_service = auth_service
        self.authenticated_user = None
        self.setWindowTitle("Plaka Tanıma Sistemi - Giriş")
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)
        if show_default_hint:
            hint = QLabel(
                "İlk kurulum: varsayılan kullanıcı adı 'admin', parola 'admin123'.\n"
                "Lütfen giriş yaptıktan sonra parolanızı değiştirin."
            )
            hint.setStyleSheet("color: #F5A623;")
            hint.setWordWrap(True)
            layout.addWidget(hint)

        form = QFormLayout()
        self.username_edit = QLineEdit("admin" if show_default_hint else "")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Kullanıcı Adı", self.username_edit)
        form.addRow("Parola", self.password_edit)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Giriş Yap")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Çıkış")
        buttons.accepted.connect(self._on_login)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_login(self) -> None:
        user = self._auth_service.login(self.username_edit.text().strip(), self.password_edit.text())
        if user is None:
            QMessageBox.warning(self, "Giriş Başarısız", "Kullanıcı adı veya parola hatalı.")
            return
        self.authenticated_user = user
        self.accept()
