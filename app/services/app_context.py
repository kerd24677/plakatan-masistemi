"""Tüm servis ve repository'leri tek bir yerde kurup birbirine bağlayan
kompozisyon kökü (composition root). UI katmanı yalnızca bu sınıf
üzerinden veritabanı/kamera/tanıma servislerine erişir."""

from __future__ import annotations

import logging

from app.camera.manager import CameraManager
from app.config.paths import APP_PATHS
from app.config.settings import RuntimeSettings
from app.database.connection import Database
from app.database.repositories import (
    AuditLogRepository,
    AuthorizedVehicleRepository,
    CameraRepository,
    DetectionRepository,
    SettingsRepository,
    UserRepository,
)
from app.services.auth_service import AuthService
from app.services.recognition_service import RecognitionService
from app.utils.credentials import CredentialStore
from app.utils.logging_setup import setup_logging

logger = logging.getLogger(__name__)


class AppContext:
    def __init__(self) -> None:
        self.paths = APP_PATHS
        self.paths.ensure_dirs()
        setup_logging(self.paths.logs_dir)

        self.db = Database(self.paths.db_path)
        self.camera_repo = CameraRepository(self.db)
        self.detection_repo = DetectionRepository(self.db)
        self.vehicle_repo = AuthorizedVehicleRepository(self.db)
        self.user_repo = UserRepository(self.db)
        self.settings_repo = SettingsRepository(self.db)
        self.audit_repo = AuditLogRepository(self.db)

        self.settings = RuntimeSettings.load(self.settings_repo)
        self.credentials = CredentialStore(self.paths.data_dir / "credentials.local")

        self.auth_service = AuthService(self.user_repo, self.audit_repo)
        self.auth_service.ensure_default_admin()

        self.camera_manager = CameraManager(
            camera_repo=self.camera_repo,
            credential_store=self.credentials,
            demo_dir=self.paths.assets_dir / "demo",
            rtsp_transport=self.settings.rtsp_transport,
            reconnect_initial_delay=self.settings.reconnect_initial_delay_seconds,
            reconnect_max_delay=self.settings.reconnect_max_delay_seconds,
        )
        self.recognition_service = RecognitionService(
            frame_store=self.camera_manager.frame_store,
            detection_repo=self.detection_repo,
            vehicle_repo=self.vehicle_repo,
            settings=self.settings,
            captures_dir=self.paths.captures_dir,
        )

    def start(self) -> None:
        if not self.recognition_service.is_ready:
            logger.error("Tanıma motoru hazır değil: %s", self.recognition_service.init_error)
        self.camera_manager.start_all_enabled()
        self.recognition_service.start()

    def reload_settings(self) -> None:
        self.settings = RuntimeSettings.load(self.settings_repo)
        self.recognition_service.update_settings(self.settings)

    def shutdown(self) -> None:
        logger.info("Uygulama kapatılıyor, kaynaklar serbest bırakılıyor...")
        self.recognition_service.stop()
        self.recognition_service.wait(5000)
        self.camera_manager.stop_all()
        self.db.close()
