"""Kullanıcı kimlik doğrulama. Parolalar PBKDF2-HMAC-SHA256 ile
(100.000 iterasyon, rastgele tuz) saklanır; düz metin parola veritabanına
asla yazılmaz."""

from __future__ import annotations

import hashlib
import hmac
import os

from app.database.models import User
from app.database.repositories import AuditLogRepository, UserRepository

_PBKDF2_ITERATIONS = 100_000


def hash_password(password: str, salt_hex: str | None = None) -> tuple[str, str]:
    salt_hex = salt_hex or os.urandom(16).hex()
    derived = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), _PBKDF2_ITERATIONS
    )
    return derived.hex(), salt_hex


def verify_password(password: str, password_hash: str, salt_hex: str) -> bool:
    candidate_hash, _ = hash_password(password, salt_hex)
    return hmac.compare_digest(candidate_hash, password_hash)


class AuthService:
    def __init__(self, user_repo: UserRepository, audit_repo: AuditLogRepository) -> None:
        self._user_repo = user_repo
        self._audit_repo = audit_repo

    def ensure_default_admin(self, username: str = "admin", password: str = "admin123") -> None:
        if self._user_repo.count() > 0:
            return
        password_hash, salt = hash_password(password)
        self._user_repo.create(
            username=username,
            password_hash=password_hash,
            password_salt=salt,
            role="admin",
            full_name="Sistem Yöneticisi",
        )
        self._audit_repo.log(action="default_admin_created", entity_type="users", entity_id=username)

    def login(self, username: str, password: str) -> User | None:
        user = self._user_repo.get_by_username(username)
        if user is None or not user.is_active:
            self._audit_repo.log(action="login_failed", entity_type="users", entity_id=username)
            return None
        if not verify_password(password, user.password_hash, user.password_salt):
            self._audit_repo.log(action="login_failed", entity_type="users", entity_id=username)
            return None
        self._user_repo.record_login(user.id)
        self._audit_repo.log(action="login_success", entity_type="users", entity_id=username, user_id=user.id)
        return user
