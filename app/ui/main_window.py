from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.config.constants import APP_NAME, APP_VERSION
from app.ui.screens.authorized_vehicles import AuthorizedVehiclesScreen
from app.ui.screens.camera_management import CameraManagementScreen
from app.ui.screens.dashboard import DashboardScreen
from app.ui.screens.detections import DetectionsScreen
from app.ui.screens.live_view import LiveViewScreen
from app.ui.screens.reporting import ReportingScreen
from app.ui.screens.settings import SettingsScreen
from app.ui.screens.system_logs import SystemLogsScreen

_NAV_ITEMS = [
    ("dashboard", "Dashboard", DashboardScreen),
    ("live", "Canlı İzleme", LiveViewScreen),
    ("cameras", "Kamera Yönetimi", CameraManagementScreen),
    ("detections", "Tanıma Kayıtları", DetectionsScreen),
    ("vehicles", "Yetkili Araçlar", AuthorizedVehiclesScreen),
    ("reports", "Raporlama", ReportingScreen),
    ("settings", "Ayarlar", SettingsScreen),
    ("logs", "Sistem Logları", SystemLogsScreen),
]


class MainWindow(QWidget):
    def __init__(self, ctx) -> None:
        super().__init__()
        self.ctx = ctx
        self.setWindowTitle(APP_NAME)
        self.resize(1440, 880)

        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        sidebar = self._build_sidebar()
        root_layout.addWidget(sidebar)

        self.stack = QStackedWidget()
        root_layout.addWidget(self.stack, stretch=1)

        self.screens: dict[str, QWidget] = {}
        for key, label, screen_cls in _NAV_ITEMS:
            screen = screen_cls(ctx)
            self.screens[key] = screen
            self.stack.addWidget(screen)

        ctx.camera_manager.frame_ready.connect(self._broadcast_frame)
        ctx.camera_manager.status_changed.connect(self._broadcast_status)
        ctx.recognition_service.detection_created.connect(self._broadcast_detection)
        ctx.recognition_service.ocr_unavailable.connect(self._on_ocr_unavailable)

        self._select_nav("dashboard")

        if not ctx.recognition_service.is_ready:
            QTimer.singleShot(
                200,
                lambda: QMessageBox.critical(
                    self, "Tanıma Motoru Başlatılamadı",
                    "Plaka tespit/OCR motoru yüklenemedi, tanıma devre dışı:\n\n"
                    f"{ctx.recognition_service.init_error}",
                ),
            )

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(230)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 12)
        layout.setSpacing(2)

        title = QLabel(APP_NAME)
        title.setObjectName("AppTitle")
        title.setWordWrap(True)
        subtitle = QLabel(f"Sürüm {APP_VERSION}")
        subtitle.setObjectName("AppSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        self._nav_group = QButtonGroup(self)
        self._nav_group.setExclusive(True)
        self._nav_buttons: dict[str, QPushButton] = {}
        for key, label, _cls in _NAV_ITEMS:
            btn = QPushButton(label)
            btn.setObjectName("SidebarButton")
            btn.setCheckable(True)
            btn.clicked.connect(lambda _checked, k=key: self._select_nav(k))
            self._nav_group.addButton(btn)
            self._nav_buttons[key] = btn
            layout.addWidget(btn)

        layout.addStretch(1)
        return sidebar

    def _select_nav(self, key: str) -> None:
        self._nav_buttons[key].setChecked(True)
        self.stack.setCurrentWidget(self.screens[key])
        self.screens[key].on_activated()

    def _broadcast_frame(self, camera_id: int, frame) -> None:
        for screen in self.screens.values():
            screen.on_frame(camera_id, frame)

    def _broadcast_status(self, camera_id: int, status: str, error: str) -> None:
        for screen in self.screens.values():
            screen.on_status(camera_id, status, error)

    def _broadcast_detection(self, detection_id: int) -> None:
        for screen in self.screens.values():
            screen.on_detection(detection_id)

    def _on_ocr_unavailable(self, message: str) -> None:
        QMessageBox.critical(
            self, "OCR Motoru Kullanılamıyor",
            "Tesseract OCR motoru bulunamadığı için plaka okuma durduruldu.\n"
            "Lütfen Tesseract-OCR kurulumunu kontrol edin (README.md).\n\n"
            f"Ayrıntı: {message}",
        )

    def closeEvent(self, event) -> None:
        self.ctx.shutdown()
        event.accept()
