from app.database.repositories import AuditLogRepository, UserRepository
from app.services.auth_service import AuthService, hash_password, verify_password


def test_hash_and_verify_roundtrip():
    password_hash, salt = hash_password("gizliParola123")
    assert verify_password("gizliParola123", password_hash, salt)
    assert not verify_password("yanlisParola", password_hash, salt)


def test_hash_password_uses_random_salt_each_time():
    hash1, salt1 = hash_password("ayniParola")
    hash2, salt2 = hash_password("ayniParola")
    assert salt1 != salt2
    assert hash1 != hash2


def test_ensure_default_admin_creates_once(db):
    users = UserRepository(db)
    audit = AuditLogRepository(db)
    service = AuthService(users, audit)

    service.ensure_default_admin()
    assert users.count() == 1

    service.ensure_default_admin()  # ikinci çağrı yeni kullanıcı oluşturmamalı
    assert users.count() == 1


def test_login_success_and_failure(db):
    users = UserRepository(db)
    audit = AuditLogRepository(db)
    service = AuthService(users, audit)
    service.ensure_default_admin("admin", "admin123")

    assert service.login("admin", "admin123") is not None
    assert service.login("admin", "yanlis") is None
    assert service.login("olmayan", "x") is None
