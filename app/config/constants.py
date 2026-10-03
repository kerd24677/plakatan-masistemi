"""Uygulama genelinde kullanılan sabitler."""

APP_NAME = "Plaka Tanıma Sistemi"
APP_ORG = "PlakaTanimaSistemi"
APP_VERSION = "1.0.0"

# Veritabanı şema sürümü. Her şema değişikliğinde artırılmalı ve
# app/database/migrations.py içine karşılık gelen migrasyon eklenmelidir.
SCHEMA_VERSION = 1

# Desteklenen görüntü akışı profilleri
STREAM_PROFILE_MAIN = "main"
STREAM_PROFILE_SUB = "sub"

# Kamera bağlantı durumları
CAMERA_STATUS_DISCONNECTED = "disconnected"
CAMERA_STATUS_CONNECTING = "connecting"
CAMERA_STATUS_CONNECTED = "connected"
CAMERA_STATUS_ERROR = "error"

# Varsayılan ayarlar (application_settings tablosuna ilk kurulumda yazılır)
DEFAULT_SETTINGS = {
    "detection_confidence_threshold": "0.5",
    "ocr_confidence_threshold": "0.55",
    "dedup_window_seconds": "8",
    "retention_days": "90",
    "rtsp_transport": "tcp",
    "default_stream_profile": STREAM_PROFILE_MAIN,
    "theme": "dark",
    "language": "tr",
    "save_detection_images": "true",
    "reconnect_initial_delay_seconds": "2",
    "reconnect_max_delay_seconds": "30",
}

# Türk plaka biçimleri (il kodu 01-81) için düzenli ifade grupları.
# Örn: 34 ABC 123 / 34 AB 1234 / 34 A 1234 / 34 ABC 12
TURKISH_PLATE_REGEXES = [
    r"^(0[1-9]|[1-7][0-9]|8[01])[A-PR-VYZ]{1}[0-9]{4,5}$",
    r"^(0[1-9]|[1-7][0-9]|8[01])[A-PR-VYZ]{2}[0-9]{3,4}$",
    r"^(0[1-9]|[1-7][0-9]|8[01])[A-PR-VYZ]{3}[0-9]{2,3}$",
]

# OCR'ın yanlış okuduğu ama plaka bağlamında karşılığı belli olan karakterler
OCR_CHAR_CORRECTIONS = {
    "O": "0",
    "I": "1",
    "Q": "0",
    "S": "5",
    "B": "8",
}
