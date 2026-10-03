"""Gerçek RTSP kamera yokken kullanılan demo/test görüntü kaynağı.

ÖNEMLİ: Burada "sahte tanıma sonucu" ÜRETİLMEZ. Yalnızca, üzerinde
gerçek bir plaka benzeri metnin render edildiği bir video dosyası
oluşturulur; bu kare gerçek tespit (Haar cascade) ve gerçek OCR
(Tesseract) motorundan geçer. Motor plakayı okuyamazsa veya düşük
güvenle okursa, pipeline bunu olduğu gibi (başarısız/incelemeye
işaretli) kaydeder — sonuç asla elle enjekte edilmez.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DEMO_PLATE_TEXT = "34 ABC 123"
DEMO_VIDEO_FRAMES = 150
DEMO_VIDEO_FPS = 15
DEMO_VIDEO_SIZE = (960, 540)


_MIN_VALID_VIDEO_BYTES = 1024


def ensure_demo_video(demo_dir: Path) -> Path:
    """Demo videosu yoksa (veya önceki bir çalıştırmada kesintiye uğrayıp
    bozuk/boş kalmışsa) oluşturur, geçerliyse mevcut yolu döndürür."""
    import cv2
    import numpy as np

    demo_dir.mkdir(parents=True, exist_ok=True)
    path = demo_dir / "demo_plates.avi"
    if path.exists() and path.stat().st_size >= _MIN_VALID_VIDEO_BYTES:
        return path

    width, height = DEMO_VIDEO_SIZE
    fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    writer = cv2.VideoWriter(str(path), fourcc, DEMO_VIDEO_FPS, (width, height))
    try:
        for i in range(DEMO_VIDEO_FRAMES):
            frame = np.full((height, width, 3), 40, dtype=np.uint8)
            # Basit bir "araç" dikdörtgeni ve soldan sağa hareket eden plaka.
            x_offset = int((i / DEMO_VIDEO_FRAMES) * (width - 260))
            plate_w, plate_h = 220, 60
            px, py = x_offset + 20, height // 2 - plate_h // 2
            car_color = (90, 90, 90)
            cv2.rectangle(frame, (px - 60, py - 80), (px + plate_w + 60, py + plate_h + 100), car_color, -1)
            cv2.rectangle(frame, (px, py), (px + plate_w, py + plate_h), (240, 240, 240), -1)
            cv2.rectangle(frame, (px, py), (px + plate_w, py + plate_h), (20, 20, 20), 2)
            cv2.putText(
                frame, DEMO_PLATE_TEXT, (px + 10, py + 42),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (10, 10, 10), 2, cv2.LINE_AA,
            )
            writer.write(frame)
    finally:
        writer.release()
    logger.info("Demo video oluşturuldu: %s", path)
    return path
