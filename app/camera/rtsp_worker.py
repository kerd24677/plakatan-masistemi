"""RTSP/dosya/sentetik görüntü kaynaklarını ayrı bir thread'de okuyan worker.

Tasarım notları:
  * UI thread'i asla bloklanmaz: her kamera kendi QThread'inde çalışır.
  * Bağlantı koptuğunda üstel geri çekilmeli (exponential backoff) otomatik
    yeniden bağlanma uygulanır.
  * RTSP URL'si (parola içerdiği için) ASLA loglanmaz; yalnızca kamera adı
    ve host bilgisi loglanır.
  * stop() çağrıldığında thread güvenli biçimde sonlanır ve VideoCapture
    serbest bırakılır (uygulama kapanışında kaynak sızıntısı olmaz).
"""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable

import numpy as np
from PySide6.QtCore import QThread, Signal

from app.config.constants import (
    CAMERA_STATUS_CONNECTED,
    CAMERA_STATUS_DISCONNECTED,
    CAMERA_STATUS_ERROR,
)

logger = logging.getLogger(__name__)

OPEN_TIMEOUT_MS = 5000
READ_TIMEOUT_MS = 5000
MAX_CONSECUTIVE_READ_FAILURES = 15


class CameraWorker(QThread):
    """camera_id'ye bağlı tek bir görüntü kaynağını yönetir."""

    frame_ready = Signal(int, np.ndarray)
    status_changed = Signal(int, str, str)  # camera_id, status, mesaj

    def __init__(
        self,
        camera_id: int,
        camera_name: str,
        camera_host: str,
        url_provider: Callable[[], str | None],
        transport: str = "tcp",
        target_fps: float = 8.0,
        reconnect_initial_delay: float = 2.0,
        reconnect_max_delay: float = 30.0,
        loop_video: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.camera_id = camera_id
        self.camera_name = camera_name
        self.camera_host = camera_host
        self._url_provider = url_provider
        self._transport = transport
        self._target_fps = target_fps
        self._reconnect_initial_delay = reconnect_initial_delay
        self._reconnect_max_delay = reconnect_max_delay
        self._loop_video = loop_video
        self._stop_requested = False
        # QThread güvenli durdurma için QMutex/QWaitCondition yerine
        # basit bir event benzeri mekanizma: msleep ile parçalı bekleme.

    def stop(self) -> None:
        self._stop_requested = True

    def _sleep_interruptible(self, seconds: float) -> None:
        end = time.monotonic() + seconds
        while not self._stop_requested and time.monotonic() < end:
            self.msleep(100)

    def _open_capture(self):
        import cv2

        url = self._url_provider()
        if not url:
            return None
        if url.startswith("rtsp://"):
            os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = f"rtsp_transport;{self._transport}"
            cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
        else:
            cap = cv2.VideoCapture(url)
        try:
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, OPEN_TIMEOUT_MS)
            cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, READ_TIMEOUT_MS)
        except Exception:
            pass  # Bazı OpenCV derlemelerinde bu özellikler yok; sorun değil.
        return cap

    def run(self) -> None:
        delay = self._reconnect_initial_delay
        while not self._stop_requested:
            self.status_changed.emit(self.camera_id, "connecting", "")
            cap = self._open_capture()
            if cap is None or not cap.isOpened():
                logger.warning(
                    "Kamera açılamadı: %s (%s)", self.camera_name, self.camera_host
                )
                self.status_changed.emit(
                    self.camera_id, CAMERA_STATUS_ERROR, "Bağlantı açılamadı"
                )
                if cap is not None:
                    cap.release()
                self._sleep_interruptible(delay)
                delay = min(delay * 2, self._reconnect_max_delay)
                continue

            logger.info("Kamera bağlandı: %s (%s)", self.camera_name, self.camera_host)
            self.status_changed.emit(self.camera_id, CAMERA_STATUS_CONNECTED, "")
            delay = self._reconnect_initial_delay
            self._read_loop(cap)
            cap.release()

            if not self._stop_requested:
                logger.warning(
                    "Kamera bağlantısı koptu, yeniden denenecek: %s", self.camera_name
                )
                self.status_changed.emit(
                    self.camera_id, CAMERA_STATUS_DISCONNECTED, "Bağlantı koptu"
                )
                self._sleep_interruptible(delay)
                delay = min(delay * 2, self._reconnect_max_delay)

        self.status_changed.emit(self.camera_id, CAMERA_STATUS_DISCONNECTED, "")

    def _read_loop(self, cap) -> None:
        frame_interval = 1.0 / self._target_fps if self._target_fps > 0 else 0.0
        last_emit = 0.0
        consecutive_failures = 0
        while not self._stop_requested:
            ok, frame = cap.read()
            if (not ok or frame is None) and self._loop_video:
                import cv2

                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ok, frame = cap.read()
            if not ok or frame is None:
                consecutive_failures += 1
                if consecutive_failures >= MAX_CONSECUTIVE_READ_FAILURES:
                    return
                self.msleep(50)
                continue
            consecutive_failures = 0
            now = time.monotonic()
            if frame_interval <= 0 or (now - last_emit) >= frame_interval:
                self.frame_ready.emit(self.camera_id, frame)
                last_emit = now
