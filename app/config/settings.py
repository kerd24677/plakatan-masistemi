"""Çalışma zamanı ayarları.

İlk kurulum bilgisi (veritabanı/log dizini gibi "bootstrap" yollar)
AppPaths üzerinden sabittir. Kullanıcının değiştirebileceği ayarlar
(eşik değerleri, saklama süresi, tema vb.) application_settings
tablosunda tutulur ve SettingsRepository ile okunur/yazılır.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.database.repositories import SettingsRepository


@dataclass
class RuntimeSettings:
    detection_confidence_threshold: float
    ocr_confidence_threshold: float
    dedup_window_seconds: float
    retention_days: int
    rtsp_transport: str
    default_stream_profile: str
    theme: str
    language: str
    save_detection_images: bool
    reconnect_initial_delay_seconds: float
    reconnect_max_delay_seconds: float

    @classmethod
    def load(cls, repo: SettingsRepository) -> "RuntimeSettings":
        values = repo.get_all()
        return cls(
            detection_confidence_threshold=float(values.get("detection_confidence_threshold", 0.5)),
            ocr_confidence_threshold=float(values.get("ocr_confidence_threshold", 0.55)),
            dedup_window_seconds=float(values.get("dedup_window_seconds", 8)),
            retention_days=int(values.get("retention_days", 90)),
            rtsp_transport=values.get("rtsp_transport", "tcp"),
            default_stream_profile=values.get("default_stream_profile", "main"),
            theme=values.get("theme", "dark"),
            language=values.get("language", "tr"),
            save_detection_images=values.get("save_detection_images", "true") == "true",
            reconnect_initial_delay_seconds=float(values.get("reconnect_initial_delay_seconds", 2)),
            reconnect_max_delay_seconds=float(values.get("reconnect_max_delay_seconds", 30)),
        )

    def save(self, repo: SettingsRepository) -> None:
        repo.set("detection_confidence_threshold", str(self.detection_confidence_threshold))
        repo.set("ocr_confidence_threshold", str(self.ocr_confidence_threshold))
        repo.set("dedup_window_seconds", str(self.dedup_window_seconds))
        repo.set("retention_days", str(self.retention_days))
        repo.set("rtsp_transport", self.rtsp_transport)
        repo.set("default_stream_profile", self.default_stream_profile)
        repo.set("theme", self.theme)
        repo.set("language", self.language)
        repo.set("save_detection_images", "true" if self.save_detection_images else "false")
        repo.set("reconnect_initial_delay_seconds", str(self.reconnect_initial_delay_seconds))
        repo.set("reconnect_max_delay_seconds", str(self.reconnect_max_delay_seconds))
