from datetime import datetime, timedelta, timezone

from app.database.repositories import AuditLogRepository, CameraRepository, DetectionRepository
from app.services.retention_service import purge_expired_detections


def test_purge_expired_detections_removes_old_rows(db, tmp_path):
    cameras = CameraRepository(db)
    detections = DetectionRepository(db)
    audit = AuditLogRepository(db)

    camera_id = cameras.create(
        name="Kam1", host="h", port=554, main_path="", sub_path="",
        username="", credential_ref="c", transport="tcp", location="",
    )

    old_image = tmp_path / "old.jpg"
    old_image.write_bytes(b"fake")
    old_date = (datetime.now(timezone.utc) - timedelta(days=100)).isoformat()
    recent_date = datetime.now(timezone.utc).isoformat()

    detections.create(
        camera_id=camera_id, plate_raw="34ABC123", plate_normalized="34ABC123",
        detection_confidence=0.9, ocr_confidence=0.9, image_path=str(old_image),
        is_authorized=False, needs_review=False, detected_at=old_date,
    )
    detections.create(
        camera_id=camera_id, plate_raw="06XYZ999", plate_normalized="06XYZ999",
        detection_confidence=0.9, ocr_confidence=0.9, image_path=None,
        is_authorized=False, needs_review=False, detected_at=recent_date,
    )

    removed = purge_expired_detections(detections, audit, retention_days=90)

    assert removed == 1
    assert not old_image.exists()
    remaining = detections.search(limit=10)
    assert len(remaining) == 1
    assert remaining[0].plate_normalized == "06XYZ999"


def test_purge_disabled_when_retention_days_zero(db):
    detections = DetectionRepository(db)
    audit = AuditLogRepository(db)
    removed = purge_expired_detections(detections, audit, retention_days=0)
    assert removed == 0
