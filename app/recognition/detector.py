"""Plaka bölgesi tespiti.

OpenCV ile birlikte dağıtılan, BSD lisanslı Haar cascade sınıflandırıcısı
(haarcascade_russian_plate_number.xml) kullanılır. Bu dosya genel dikdörtgen
plaka şekillerini tespit etmek için eğitilmiştir (Türkiye'ye özel değildir,
ancak Türk plakalarının en-boy oranıyla uyumludur) ve OpenCV paketiyle
birlikte GERÇEKTEN gelir — ayrıca indirme gerektirmez, lisans belirsizliği
yoktur. Model dosyası bulunamaz veya yüklenemezse RuntimeError fırlatılır;
sahte/rastgele sonuç üretilmez.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class PlateCandidate:
    x: int
    y: int
    w: int
    h: int
    confidence: float

    def crop(self, frame_bgr):
        return frame_bgr[self.y : self.y + self.h, self.x : self.x + self.w]


class PlateDetector:
    def __init__(self, cascade_path: str | None = None) -> None:
        import cv2

        path = cascade_path or os.path.join(
            cv2.data.haarcascades, "haarcascade_russian_plate_number.xml"
        )
        if not os.path.exists(path):
            raise RuntimeError(
                f"Plaka tespit modeli bulunamadı: {path}. OpenCV kurulumu "
                "eksik veya bozuk olabilir."
            )
        self._cascade = cv2.CascadeClassifier(path)
        if self._cascade.empty():
            raise RuntimeError(
                f"Plaka tespit modeli yüklenemedi (dosya bozuk olabilir): {path}"
            )
        self.model_path = path

    def detect(self, frame_bgr) -> list[PlateCandidate]:
        import cv2

        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        rects, _reject_levels, level_weights = self._cascade.detectMultiScale3(
            gray,
            scaleFactor=1.05,
            minNeighbors=5,
            minSize=(60, 18),
            outputRejectLevels=True,
        )
        candidates: list[PlateCandidate] = []
        for (x, y, w, h), weight in zip(rects, level_weights):
            # Haar cascade kalibre edilmiş bir olasılık vermez; levelWeights
            # değerini 0..1 aralığına yaklaşık ölçekleyerek bir güven skoru
            # türetiyoruz (deneysel ölçek faktörü = 8.0).
            confidence = max(0.0, min(1.0, float(weight) / 8.0))
            candidates.append(PlateCandidate(int(x), int(y), int(w), int(h), confidence))
        candidates.sort(key=lambda c: c.confidence, reverse=True)
        return candidates
