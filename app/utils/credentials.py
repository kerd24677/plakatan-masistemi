"""Kamera parolaları gibi hassas bilgiler için kimlik bilgisi deposu.

Windows'ta `keyring` paketi otomatik olarak Windows Credential Manager
arka ucunu kullanır — parolalar düz metin olarak diskte veya veritabanında
saklanmaz. Linux geliştirme ortamında bir Secret Service daemon'ı
bulunmayabilir; bu durumda, YALNIZCA geliştirme/test amaçlı, kullanıcıya
özel (chmod 600) yerel bir dosyaya base64 ile gizlenmiş biçimde yazılan
bir yedek mekanizmaya düşer. Bu yedek üretim (Windows) ortamında
kullanılmaz ve güvenlik açısından Credential Manager ile eşdeğer değildir.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import stat
from pathlib import Path

logger = logging.getLogger(__name__)

SERVICE_NAME = "PlakaTanimaSistemi"


class _FallbackFileStore:
    """Yalnızca OS kimlik bilgisi deposu kullanılamadığında devreye girer."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def _load(self) -> dict:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text())
        except (json.JSONDecodeError, OSError):
            logger.warning("Yedek kimlik bilgisi dosyası okunamadı, sıfırlanıyor")
            return {}

    def _save(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data))
        try:
            os.chmod(self.path, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass

    def set_password(self, key: str, password: str) -> None:
        data = self._load()
        data[key] = base64.b64encode(password.encode()).decode()
        self._save(data)

    def get_password(self, key: str) -> str | None:
        value = self._load().get(key)
        return base64.b64decode(value).decode() if value else None

    def delete_password(self, key: str) -> None:
        data = self._load()
        data.pop(key, None)
        self._save(data)


class CredentialStore:
    def __init__(self, fallback_path: Path) -> None:
        self._fallback = _FallbackFileStore(fallback_path)
        self._keyring_available = self._check_keyring()

    @staticmethod
    def _check_keyring() -> bool:
        try:
            import keyring
            import keyring.errors

            keyring.get_keyring()
            return True
        except Exception:
            logger.warning(
                "OS kimlik bilgisi deposuna erişilemedi; geliştirme amaçlı "
                "yerel yedek depo kullanılacak. Üretimde (Windows) bu "
                "durum normalde oluşmaz."
            )
            return False

    def set_password(self, key: str, password: str) -> None:
        if self._keyring_available:
            try:
                import keyring

                keyring.set_password(SERVICE_NAME, key, password)
                return
            except Exception:
                logger.exception("Keyring'e yazılamadı, yedek depo kullanılıyor: %s", key)
        self._fallback.set_password(key, password)

    def get_password(self, key: str) -> str | None:
        if self._keyring_available:
            try:
                import keyring

                value = keyring.get_password(SERVICE_NAME, key)
                if value is not None:
                    return value
            except Exception:
                logger.exception("Keyring'den okunamadı: %s", key)
        return self._fallback.get_password(key)

    def delete_password(self, key: str) -> None:
        if self._keyring_available:
            try:
                import keyring

                keyring.delete_password(SERVICE_NAME, key)
            except Exception:
                pass
        self._fallback.delete_password(key)
