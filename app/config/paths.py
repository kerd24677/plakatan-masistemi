"""Platforma göre uygulama veri/günlük/görüntü dizinlerini çözümler.

Geliştirme (Linux) ve üretim (Windows) ortamlarının ikisinde de çalışır.
PyInstaller ile paketlendiğinde (frozen) yol çözümlemesi EXE'nin yanı
değil, kullanıcının yazılabilir profil dizinini kullanır.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from app.config.constants import APP_NAME, APP_ORG


def _base_app_data_dir() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        if base:
            return Path(base) / APP_ORG
        return Path.home() / "AppData" / "Local" / APP_ORG
    # Linux/macOS geliştirme ortamı için XDG uyumlu yol
    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg) if xdg else Path.home() / ".local" / "share"
    return base / APP_ORG


class AppPaths:
    """Tüm kalıcı veri yollarını tek bir yerden sağlar."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or _base_app_data_dir()
        self.data_dir = self.base_dir / "data"
        self.db_path = self.data_dir / "plaka_tanima.db"
        self.logs_dir = self.base_dir / "logs"
        self.captures_dir = self.base_dir / "captures"
        self.config_file = self.base_dir / "config.json"
        self.models_dir = self._resource_dir("models")
        self.assets_dir = self._resource_dir("assets")

    @staticmethod
    def _resource_dir(name: str) -> Path:
        """PyInstaller ile paketlendiğinde (onedir) _MEIPASS/<name>,
        kaynak koddan çalışırken proje kökü/<name> dizinini döndürür."""
        if getattr(sys, "frozen", False):
            base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        else:
            base = Path(__file__).resolve().parents[2]
        return base / name

    def ensure_dirs(self) -> None:
        for d in (self.data_dir, self.logs_dir, self.captures_dir):
            d.mkdir(parents=True, exist_ok=True)


APP_PATHS = AppPaths()
