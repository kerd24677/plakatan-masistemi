from app.database.models import Detection
from app.services.export_service import export_detections_csv


def _make_detection(**overrides) -> Detection:
    base = dict(
        id=1, camera_id=1, plate_raw="34ABC123", plate_normalized="34ABC123",
        detection_confidence=0.9, ocr_confidence=0.85, image_path=None,
        is_authorized=True, needs_review=False, review_status="auto",
        detected_at="2026-01-01T10:00:00", created_at="2026-01-01T10:00:00",
    )
    base.update(overrides)
    return Detection(**base)


def test_export_detections_csv(tmp_path):
    detections = [_make_detection()]
    output = tmp_path / "out.csv"
    export_detections_csv(detections, {1: "Giriş Kapısı"}, output)

    content = output.read_text(encoding="utf-8-sig")
    assert "Plaka" in content
    assert "34 ABC 123" in content
    assert "Giriş Kapısı" in content
    assert "Evet" in content
