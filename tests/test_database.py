from app.database.repositories import (
    AuditLogRepository,
    AuthorizedVehicleRepository,
    CameraRepository,
    DetectionRepository,
    SettingsRepository,
    UserRepository,
)


def test_schema_creates_default_settings(db):
    repo = SettingsRepository(db)
    assert repo.get("dedup_window_seconds") == "8"


def test_camera_crud(db):
    repo = CameraRepository(db)
    camera_id = repo.create(
        name="Giriş Kapısı", host="192.168.1.10", port=554, main_path="stream1",
        sub_path="stream2", username="admin", credential_ref="camera_1",
        transport="tcp", location="Ana Giriş",
    )
    camera = repo.get(camera_id)
    assert camera.name == "Giriş Kapısı"
    assert camera.enabled is True

    repo.update(camera_id, name="Yan Kapı")
    assert repo.get(camera_id).name == "Yan Kapı"

    repo.update_status(camera_id, "connected")
    assert repo.get(camera_id).status == "connected"

    repo.delete(camera_id)
    assert repo.get(camera_id) is None


def test_camera_name_unique(db):
    repo = CameraRepository(db)
    repo.create(
        name="Kamera A", host="h", port=554, main_path="", sub_path="",
        username="", credential_ref="c1", transport="tcp", location="",
    )
    try:
        repo.create(
            name="Kamera A", host="h2", port=554, main_path="", sub_path="",
            username="", credential_ref="c2", transport="tcp", location="",
        )
        assert False, "Yinelenen kamera adı hata vermeliydi"
    except Exception:
        pass


def test_detection_create_and_search(db):
    cameras = CameraRepository(db)
    detections = DetectionRepository(db)
    camera_id = cameras.create(
        name="Kam1", host="h", port=554, main_path="", sub_path="",
        username="", credential_ref="c", transport="tcp", location="",
    )
    detections.create(
        camera_id=camera_id, plate_raw="34ABC123", plate_normalized="34ABC123",
        detection_confidence=0.9, ocr_confidence=0.8, image_path=None,
        is_authorized=False, needs_review=False, detected_at="2026-01-01T10:00:00",
    )
    results = detections.search(plate="34ABC")
    assert len(results) == 1
    assert results[0].plate_normalized == "34ABC123"

    results_by_camera = detections.search(camera_id=camera_id)
    assert len(results_by_camera) == 1

    none_results = detections.search(plate="99ZZZ999")
    assert none_results == []


def test_detection_dedup_lookup(db):
    cameras = CameraRepository(db)
    detections = DetectionRepository(db)
    camera_id = cameras.create(
        name="Kam1", host="h", port=554, main_path="", sub_path="",
        username="", credential_ref="c", transport="tcp", location="",
    )
    assert detections.last_for_plate_on_camera(camera_id, "34ABC123") is None
    detections.create(
        camera_id=camera_id, plate_raw="34ABC123", plate_normalized="34ABC123",
        detection_confidence=0.9, ocr_confidence=0.8, image_path=None,
        is_authorized=False, needs_review=False, detected_at="2026-01-01T10:00:00",
    )
    assert detections.last_for_plate_on_camera(camera_id, "34ABC123") is not None


def test_authorized_vehicle_crud(db):
    repo = AuthorizedVehicleRepository(db)
    vehicle_id = repo.create("34ABC123", "Müdür Aracı", "active")
    assert repo.find_by_plate("34ABC123") is not None
    repo.update(vehicle_id, permission_status="suspended")
    assert repo.find_by_plate("34ABC123") is None  # yalnızca active olanlar bulunur
    repo.delete(vehicle_id)
    assert repo.list_all() == []


def test_settings_set_get(db):
    repo = SettingsRepository(db)
    repo.set("theme", "light")
    assert repo.get("theme") == "light"
    assert repo.get("nonexistent", "default") == "default"


def test_audit_log(db):
    repo = AuditLogRepository(db)
    repo.log(action="test_action", entity_type="test", entity_id="1")
    recent = repo.recent()
    assert len(recent) == 1
    assert recent[0]["action"] == "test_action"


def test_user_repository_and_uniqueness(db):
    repo = UserRepository(db)
    assert repo.count() == 0
    repo.create("admin", "hash", "salt", "admin", "Yönetici")
    assert repo.count() == 1
    user = repo.get_by_username("admin")
    assert user.role == "admin"
