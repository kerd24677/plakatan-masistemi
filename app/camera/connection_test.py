"""Kamera ekleme/düzenleme ekranındaki 'Bağlantı Testi' için tek seferlik,
zaman aşımlı bağlantı denemesi. Sürekli çalışan CameraWorker'dan bağımsızdır.

Bu fonksiyon I/O yaptığı için UI thread'inde DEĞİL, çağıran tarafın
(app/ui/screens/cameras.py) açacağı kısa ömürlü bir QThread içinde
çalıştırılmalıdır.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class ConnectionTestResult:
    success: bool
    message: str
    width: int = 0
    height: int = 0


def test_connection(url: str, transport: str = "tcp", timeout_ms: int = 6000) -> ConnectionTestResult:
    import cv2

    if not url:
        return ConnectionTestResult(False, "Geçersiz bağlantı adresi")

    if url.startswith("rtsp://"):
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = f"rtsp_transport;{transport}"
        cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
    else:
        cap = cv2.VideoCapture(url)

    try:
        try:
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, timeout_ms)
            cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, timeout_ms)
        except Exception:
            pass

        if not cap.isOpened():
            return ConnectionTestResult(False, "Bağlantı açılamadı (zaman aşımı veya hatalı adres)")

        ok, frame = cap.read()
        if not ok or frame is None:
            return ConnectionTestResult(False, "Bağlantı açıldı ancak görüntü karesi alınamadı")

        height, width = frame.shape[:2]
        return ConnectionTestResult(True, "Bağlantı başarılı", width=width, height=height)
    except Exception as exc:  # pragma: no cover - savunma amaçlı
        return ConnectionTestResult(False, f"Beklenmeyen hata: {exc}")
    finally:
        cap.release()
