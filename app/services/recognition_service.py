"""Kamera karelerini gerçek tespit+OCR pipeline'ından geçirip
veritabanına kaydeden arka plan servisi.

Kendi QThread'inde çalışır; her döngüde aktif kameraların yalnızca EN SON
karesini işler (app.camera.frame_store.LatestFrameStore), böylece işleme
hızı kare üretim hızının gerisinde kalsa bile UI/kamera thread'leri asla
bloklanmaz ve birikme oluşmaz.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from app.camera.frame_store import LatestFrameStore
from app.config.settings import RuntimeSettings
from app.database.repositories import AuthorizedVehicleRepository, DetectionRepository
from app.recognition.detector import PlateDetector
from app.recognition.ocr import PlateOCR, TesseractNotAvailableError
from app.recognition.pipeline import RecognitionPipeline, RecognitionResult

logger = logging.getLogger(__name__)

_UNREADABLE_KEY = "__UNREADABLE__"
_MIN_FALLBACK_LEN = 4
_IDLE_SLEEP_MS = 30
_DEDUP_CACHE_HARD_LIMIT = 5000


class RecognitionService(QThread):
    detection_created = Signal(int)  # detection_id
    ocr_unavailable = Signal(str)  # Tesseract bulunamadığında bir kez yayılır

    def __init__(
        self,
        frame_store: LatestFrameStore,
        detection_repo: DetectionRepository,
        vehicle_repo: AuthorizedVehicleRepository,
        settings: RuntimeSettings,
        captures_dir: Path,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._frame_store = frame_store
        self._detection_repo = detection_repo
        self._vehicle_repo = vehicle_repo
        self._settings = settings
        self._captures_dir = captures_dir
        self._stop_requested = False
        self._dedup_cache: dict[tuple[int, str], float] = {}
        self._ocr_unavailable = False

        self._pipeline: RecognitionPipeline | None = None
        self.init_error: str | None = None
        try:
            self._pipeline = RecognitionPipeline(PlateDetector(), PlateOCR())
        except Exception as exc:
            self.init_error = str(exc)
            logger.error("Tanıma motoru başlatılamadı: %s", exc)

    @property
    def is_ready(self) -> bool:
        return self._pipeline is not None

    def update_settings(self, settings: RuntimeSettings) -> None:
        self._settings = settings

    def stop(self) -> None:
        self._stop_requested = True

    def run(self) -> None:
        if self._pipeline is None:
            return  # Model yüklenemedi; servis çalışmaz, UI init_error'ı gösterir.
        while not self._stop_requested:
            if self._ocr_unavailable:
                # OCR motoru kullanılamıyor; tekrar tekrar deneyip log
                # kirletmek yerine servisi etkin biçimde boşta tut.
                self.msleep(500)
                continue
            processed_any = False
            for camera_id in self._frame_store.active_camera_ids():
                frame = self._frame_store.get_if_new(camera_id)
                if frame is None:
                    continue
                processed_any = True
                try:
                    self._process_frame(camera_id, frame)
                except TesseractNotAvailableError as exc:
                    self._ocr_unavailable = True
                    logger.error("OCR motoru kullanılamıyor, tanıma durduruldu: %s", exc)
                    self.ocr_unavailable.emit(str(exc))
                    break
                except Exception:
                    logger.exception("Kare işlenirken hata: camera_id=%s", camera_id)
            if not processed_any:
                self.msleep(_IDLE_SLEEP_MS)

    def _process_frame(self, camera_id: int, frame) -> None:
        results = self._pipeline.process_frame(frame)
        now = time.monotonic()
        self._maybe_cleanup_dedup_cache(now)
        for result in results:
            self._handle_result(camera_id, frame, result, now)

    def _handle_result(self, camera_id: int, frame, result: RecognitionResult, now: float) -> None:
        if result.is_valid_format:
            plate_value = result.plate_normalized
            dedup_key = (camera_id, plate_value)
            needs_review = (
                result.detection_confidence < self._settings.detection_confidence_threshold
                or result.ocr_confidence < self._settings.ocr_confidence_threshold
            )
        else:
            fallback = RecognitionPipeline.cleaned_fallback_text(result.raw_text)
            if len(fallback) < _MIN_FALLBACK_LEN:
                return  # Anlamlı metin yok; gürültü, kayıt etme.
            plate_value = fallback
            dedup_key = (camera_id, _UNREADABLE_KEY)
            needs_review = True

        last_seen = self._dedup_cache.get(dedup_key)
        if last_seen is not None and (now - last_seen) < self._settings.dedup_window_seconds:
            return
        self._dedup_cache[dedup_key] = now

        is_authorized = False
        if result.is_valid_format:
            vehicle = self._vehicle_repo.find_by_plate(plate_value)
            is_authorized = vehicle is not None

        image_path = None
        if self._settings.save_detection_images:
            image_path = self._save_crop(camera_id, frame, result)

        detected_at = datetime.now(timezone.utc).isoformat()
        try:
            detection_id = self._detection_repo.create(
                camera_id=camera_id,
                plate_raw=result.raw_text,
                plate_normalized=plate_value,
                detection_confidence=result.detection_confidence,
                ocr_confidence=result.ocr_confidence,
                image_path=str(image_path) if image_path else None,
                is_authorized=is_authorized,
                needs_review=needs_review,
                detected_at=detected_at,
            )
        except Exception:
            logger.exception("Tespit kaydı veritabanına yazılamadı")
            return
        self.detection_created.emit(detection_id)

    def _save_crop(self, camera_id: int, frame, result: RecognitionResult) -> Path | None:
        try:
            import cv2

            x, y, w, h = result.bbox
            crop = frame[y : y + h, x : x + w]
            if crop.size == 0:
                return None
            day_dir = self._captures_dir / datetime.now().strftime("%Y-%m-%d")
            day_dir.mkdir(parents=True, exist_ok=True)
            filename = f"cam{camera_id}_{int(time.time() * 1000)}.jpg"
            path = day_dir / filename
            cv2.imwrite(str(path), crop)
            return path
        except Exception:
            logger.exception("Tespit görüntüsü kaydedilemedi")
            return None

    def _maybe_cleanup_dedup_cache(self, now: float) -> None:
        if len(self._dedup_cache) < _DEDUP_CACHE_HARD_LIMIT:
            return
        expiry = self._settings.dedup_window_seconds * 4
        stale = [k for k, t in self._dedup_cache.items() if (now - t) > expiry]
        for k in stale:
            del self._dedup_cache[k]
