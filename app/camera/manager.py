"""Tüm kamera worker'larını yöneten merkezi sınıf.

UI ve tanıma servisi kameralarla yalnızca bu sınıf üzerinden konuşur;
doğrudan CameraWorker örneği oluşturmaz.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
from PySide6.QtCore import QObject, Qt, Signal

from app.camera.frame_store import LatestFrameStore
from app.camera.rtsp_worker import CameraWorker
from app.config.constants import STREAM_PROFILE_MAIN
from app.database.models import Camera
from app.database.repositories import CameraRepository
from app.utils.credentials import CredentialStore

logger = logging.getLogger(__name__)

DEMO_HOST_SENTINEL = "DEMO"


class CameraManager(QObject):
    frame_ready = Signal(int, np.ndarray)
    status_changed = Signal(int, str, str)

    def __init__(
        self,
        camera_repo: CameraRepository,
        credential_store: CredentialStore,
        demo_dir: Path,
        rtsp_transport: str = "tcp",
        reconnect_initial_delay: float = 2.0,
        reconnect_max_delay: float = 30.0,
    ) -> None:
        super().__init__()
        self._camera_repo = camera_repo
        self._credentials = credential_store
        self._demo_dir = demo_dir
        self._rtsp_transport = rtsp_transport
        self._reconnect_initial_delay = reconnect_initial_delay
        self._reconnect_max_delay = reconnect_max_delay
        self._workers: dict[int, CameraWorker] = {}
        self.frame_store = LatestFrameStore()

    def _make_url_provider(self, camera: Camera, profile: str):
        def provider() -> str | None:
            if camera.host == DEMO_HOST_SENTINEL:
                from app.camera.demo_source import ensure_demo_video

                return str(ensure_demo_video(self._demo_dir))
            password = self._credentials.get_password(camera.credential_ref) or ""
            return camera.rtsp_url(password, profile=profile)

        return provider

    def start_camera(self, camera_id: int, profile: str = STREAM_PROFILE_MAIN) -> None:
        if camera_id in self._workers:
            return
        camera = self._camera_repo.get(camera_id)
        if camera is None or not camera.enabled:
            logger.info("Kamera başlatılamadı (bulunamadı/devre dışı): id=%s", camera_id)
            return

        is_demo = camera.host == DEMO_HOST_SENTINEL
        worker = CameraWorker(
            camera_id=camera.id,
            camera_name=camera.name,
            camera_host=camera.host,
            url_provider=self._make_url_provider(camera, profile),
            transport=camera.transport or self._rtsp_transport,
            reconnect_initial_delay=self._reconnect_initial_delay,
            reconnect_max_delay=self._reconnect_max_delay,
            loop_video=is_demo,
        )
        # DirectConnection: worker thread'inde çalışır, yalnızca ucuz bir
        # dict yazımı yapar (frame_store). UI tüketimi için ayrıca normal
        # (queued) bağlantıyla frame_ready sinyali de iletilir.
        worker.frame_ready.connect(self._on_frame_from_worker, Qt.ConnectionType.DirectConnection)
        worker.frame_ready.connect(self.frame_ready)
        worker.status_changed.connect(self._on_worker_status_changed)
        self._workers[camera_id] = worker
        worker.start()
        logger.info("Kamera worker başlatıldı: %s (%s)", camera.name, camera.host)

    def _on_frame_from_worker(self, camera_id: int, frame: np.ndarray) -> None:
        self.frame_store.put(camera_id, frame)

    def _on_worker_status_changed(self, camera_id: int, status: str, error: str) -> None:
        self._camera_repo.update_status(camera_id, status, error or None)
        self.status_changed.emit(camera_id, status, error)

    def stop_camera(self, camera_id: int) -> None:
        worker = self._workers.pop(camera_id, None)
        if worker is None:
            return
        worker.stop()
        worker.wait(5000)
        self.frame_store.remove(camera_id)
        logger.info("Kamera worker durduruldu: id=%s", camera_id)

    def restart_camera(self, camera_id: int, profile: str = STREAM_PROFILE_MAIN) -> None:
        self.stop_camera(camera_id)
        self.start_camera(camera_id, profile)

    def start_all_enabled(self) -> None:
        for camera in self._camera_repo.list_all():
            if camera.enabled:
                self.start_camera(camera.id)

    def stop_all(self) -> None:
        for camera_id in list(self._workers):
            self.stop_camera(camera_id)
