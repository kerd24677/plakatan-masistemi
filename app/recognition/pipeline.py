"""Tespit + OCR + normalizasyonu tek bir çerçeve (frame) için birleştiren
durumsuz (stateless) pipeline. Veritabanı, dedup veya kamera bilgisi
içermez — bu sorumluluklar app.services.recognition_service içindedir.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.recognition.detector import PlateDetector
from app.recognition.ocr import PlateOCR
from app.utils.plate import clean_raw_text, normalize_plate


@dataclass
class RecognitionResult:
    bbox: tuple[int, int, int, int]
    detection_confidence: float
    raw_text: str
    plate_normalized: str | None
    ocr_confidence: float

    @property
    def is_valid_format(self) -> bool:
        return self.plate_normalized is not None


class RecognitionPipeline:
    def __init__(self, detector: PlateDetector, ocr: PlateOCR, max_candidates_per_frame: int = 3) -> None:
        self._detector = detector
        self._ocr = ocr
        self._max_candidates = max_candidates_per_frame

    def process_frame(self, frame_bgr) -> list[RecognitionResult]:
        results: list[RecognitionResult] = []
        candidates = self._detector.detect(frame_bgr)[: self._max_candidates]
        for candidate in candidates:
            crop = candidate.crop(frame_bgr)
            if crop.size == 0:
                continue
            raw_text, ocr_confidence = self._ocr.read(crop)
            normalized = normalize_plate(raw_text) if raw_text else None
            results.append(
                RecognitionResult(
                    bbox=(candidate.x, candidate.y, candidate.w, candidate.h),
                    detection_confidence=candidate.confidence,
                    raw_text=raw_text,
                    plate_normalized=normalized,
                    ocr_confidence=ocr_confidence,
                )
            )
        return results

    @staticmethod
    def cleaned_fallback_text(raw_text: str) -> str:
        """Biçim doğrulamasından geçemeyen ama en az 4 karakterlik
        anlamlı metin içeren okumalar için denetim amaçlı temizlenmiş metin."""
        return clean_raw_text(raw_text)
