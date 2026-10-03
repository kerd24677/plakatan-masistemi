from app.utils.credentials import CredentialStore, _FallbackFileStore


def test_fallback_file_store_roundtrip(tmp_path):
    store = _FallbackFileStore(tmp_path / "creds.local")
    store.set_password("camera_1", "s3cret")
    assert store.get_password("camera_1") == "s3cret"
    store.delete_password("camera_1")
    assert store.get_password("camera_1") is None


def test_credential_store_falls_back_when_keyring_unavailable(tmp_path, monkeypatch):
    store = CredentialStore(tmp_path / "creds.local")
    store._keyring_available = False  # Linux CI/geliştirme ortamını simüle eder
    store.set_password("camera_1", "myPassword")
    assert store.get_password("camera_1") == "myPassword"
    store.delete_password("camera_1")
    assert store.get_password("camera_1") is None
