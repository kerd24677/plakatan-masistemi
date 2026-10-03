"""Gerçek Haar cascade + gerçek Tesseract OCR motorlarını kullanan uçtan uca
'duman testi' (smoke test). Amaç mükemmel OCR doğruluğu değil; pipeline'ın
gerçek bileşenlerle çökmeden çalıştığını ve beklenen veri tiplerini
döndürdüğünü doğrulamaktır. cv2/pytesseract veya sistemde kurulu Tesseract
ikili dosyası yoksa test atlanır (xfail/skip)."""

import pytest

cv2 = pytest.importorskip("cv2")
pytest.importorskip("pytesseract")

from app.recognition.detector import PlateDetector  # noqa: E402
from app.recognition.ocr import PlateOCR, TesseractNotAvailableError  # noqa: E402
from app.recognition.pipeline import RecognitionPipeline  # noqa: E402


def _tesseract_available() -> bool:
    import pytesseract

    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _tesseract_available(), reason="Tesseract OCR sistemde kurulu değil")
def test_pipeline_runs_without_crashing_on_synthetic_frame(tmp_path):
    from app.camera.demo_source import ensure_demo_video

    video_path = ensure_demo_video(tmp_path)
    cap = cv2.VideoCapture(str(video_path))
    ok, frame = cap.read()
    cap.release()
    assert ok, "Demo video oluşturulamadı veya okunamadı"

    pipeline = RecognitionPipeline(PlateDetector(), PlateOCR())
    results = pipeline.process_frame(frame)

    assert isinstance(results, list)
    for r in results:
        assert 0.0 <= r.detection_confidence <= 1.0
        assert 0.0 <= r.ocr_confidence <= 1.0
        assert isinstance(r.raw_text, str)


def test_ocr_raises_clear_error_when_tesseract_missing(monkeypatch):
    ocr = PlateOCR()

    def fail(*args, **kwargs):
        raise FileNotFoundError("tesseract not found")

    import pytesseract

    monkeypatch.setattr(pytesseract, "get_tesseract_version", fail)
    with pytest.raises(TesseractNotAvailableError):
        ocr._verify_available()
