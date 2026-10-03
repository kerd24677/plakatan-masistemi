"""Her tablo için parametreli sorgular kullanan repository sınıfları."""

from __future__ import annotations

import logging

from app.database.connection import Database
from app.database.models import AuthorizedVehicle, Camera, Detection, User

logger = logging.getLogger(__name__)


class CameraRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def list_all(self) -> list[Camera]:
        rows = self.db.query("SELECT * FROM cameras ORDER BY name")
        return [Camera.from_row(r) for r in rows]

    def get(self, camera_id: int) -> Camera | None:
        row = self.db.query_one("SELECT * FROM cameras WHERE id = ?", (camera_id,))
        return Camera.from_row(row) if row else None

    def create(
        self,
        name: str,
        host: str,
        port: int,
        main_path: str,
        sub_path: str,
        username: str,
        credential_ref: str,
        transport: str,
        location: str,
    ) -> int:
        try:
            return self.db.execute(
                """INSERT INTO cameras
                   (name, host, port, main_path, sub_path, username,
                    credential_ref, transport, location)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (name, host, port, main_path, sub_path, username,
                 credential_ref, transport, location),
            )
        except Exception:
            logger.exception("Kamera oluşturulamadı: %s", name)
            raise

    def update(self, camera_id: int, **fields) -> None:
        if not fields:
            return
        allowed = {
            "name", "host", "port", "main_path", "sub_path", "username",
            "transport", "location", "enabled",
        }
        unknown = set(fields) - allowed
        if unknown:
            raise ValueError(f"Güncellenemeyen alanlar: {unknown}")
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = [*fields.values(), camera_id]
        try:
            self.db.execute(
                f"UPDATE cameras SET {set_clause}, updated_at = datetime('now') "
                "WHERE id = ?",
                tuple(values),
            )
        except Exception:
            logger.exception("Kamera güncellenemedi: id=%s", camera_id)
            raise

    def update_status(self, camera_id: int, status: str, error: str | None = None) -> None:
        self.db.execute(
            "UPDATE cameras SET status = ?, last_status_at = datetime('now'), "
            "last_error = ? WHERE id = ?",
            (status, error, camera_id),
        )

    def delete(self, camera_id: int) -> None:
        try:
            self.db.execute("DELETE FROM cameras WHERE id = ?", (camera_id,))
        except Exception:
            logger.exception("Kamera silinemedi: id=%s", camera_id)
            raise


class DetectionRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create(
        self,
        camera_id: int,
        plate_raw: str,
        plate_normalized: str,
        detection_confidence: float,
        ocr_confidence: float,
        image_path: str | None,
        is_authorized: bool,
        needs_review: bool,
        detected_at: str,
    ) -> int:
        try:
            return self.db.execute(
                """INSERT INTO detections
                   (camera_id, plate_raw, plate_normalized, detection_confidence,
                    ocr_confidence, image_path, is_authorized, needs_review,
                    review_status, detected_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (camera_id, plate_raw, plate_normalized, detection_confidence,
                 ocr_confidence, image_path, int(is_authorized), int(needs_review),
                 "pending" if needs_review else "auto", detected_at),
            )
        except Exception:
            logger.exception("Tespit kaydı oluşturulamadı: plaka=%s", plate_normalized)
            raise

    def last_for_plate_on_camera(self, camera_id: int, plate_normalized: str) -> Detection | None:
        row = self.db.query_one(
            """SELECT * FROM detections WHERE camera_id = ? AND plate_normalized = ?
               ORDER BY detected_at DESC LIMIT 1""",
            (camera_id, plate_normalized),
        )
        return Detection.from_row(row) if row else None

    def search(
        self,
        plate: str | None = None,
        camera_id: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        review_status: str | None = None,
        limit: int = 500,
    ) -> list[Detection]:
        clauses = []
        params: list = []
        if plate:
            clauses.append("plate_normalized LIKE ?")
            params.append(f"%{plate.upper()}%")
        if camera_id:
            clauses.append("camera_id = ?")
            params.append(camera_id)
        if date_from:
            clauses.append("detected_at >= ?")
            params.append(date_from)
        if date_to:
            clauses.append("detected_at <= ?")
            params.append(date_to)
        if review_status:
            clauses.append("review_status = ?")
            params.append(review_status)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        rows = self.db.query(
            f"SELECT * FROM detections {where} ORDER BY detected_at DESC LIMIT ?",
            tuple(params),
        )
        return [Detection.from_row(r) for r in rows]

    def set_review_status(self, detection_id: int, status: str) -> None:
        self.db.execute(
            "UPDATE detections SET review_status = ?, needs_review = 0 WHERE id = ?",
            (status, detection_id),
        )

    def delete_older_than(self, cutoff_iso: str) -> list[str]:
        """Eşiğin öncesindeki kayıtları siler, silinen kayıtların
        (varsa) görüntü yollarını döndürür — dosyaları silmek çağırana aittir."""
        rows = self.db.query(
            "SELECT image_path FROM detections WHERE detected_at < ? AND image_path IS NOT NULL",
            (cutoff_iso,),
        )
        self.db.execute("DELETE FROM detections WHERE detected_at < ?", (cutoff_iso,))
        return [r["image_path"] for r in rows]


class AuthorizedVehicleRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def list_all(self) -> list[AuthorizedVehicle]:
        rows = self.db.query("SELECT * FROM authorized_vehicles ORDER BY plate_normalized")
        return [AuthorizedVehicle.from_row(r) for r in rows]

    def find_by_plate(self, plate_normalized: str) -> AuthorizedVehicle | None:
        row = self.db.query_one(
            "SELECT * FROM authorized_vehicles WHERE plate_normalized = ? "
            "AND permission_status = 'active'",
            (plate_normalized,),
        )
        return AuthorizedVehicle.from_row(row) if row else None

    def create(self, plate_normalized: str, description: str, permission_status: str) -> int:
        try:
            return self.db.execute(
                """INSERT INTO authorized_vehicles (plate_normalized, description, permission_status)
                   VALUES (?, ?, ?)""",
                (plate_normalized, description, permission_status),
            )
        except Exception:
            logger.exception("Yetkili araç oluşturulamadı: %s", plate_normalized)
            raise

    def update(self, vehicle_id: int, **fields) -> None:
        allowed = {"description", "permission_status"}
        unknown = set(fields) - allowed
        if unknown:
            raise ValueError(f"Güncellenemeyen alanlar: {unknown}")
        if not fields:
            return
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = [*fields.values(), vehicle_id]
        self.db.execute(
            f"UPDATE authorized_vehicles SET {set_clause}, updated_at = datetime('now') "
            "WHERE id = ?",
            tuple(values),
        )

    def delete(self, vehicle_id: int) -> None:
        self.db.execute("DELETE FROM authorized_vehicles WHERE id = ?", (vehicle_id,))


class UserRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def get_by_username(self, username: str) -> User | None:
        row = self.db.query_one("SELECT * FROM users WHERE username = ?", (username,))
        return User.from_row(row) if row else None

    def list_all(self) -> list[User]:
        return [User.from_row(r) for r in self.db.query("SELECT * FROM users ORDER BY username")]

    def create(
        self, username: str, password_hash: str, password_salt: str, role: str, full_name: str
    ) -> int:
        return self.db.execute(
            """INSERT INTO users (username, password_hash, password_salt, role, full_name)
               VALUES (?, ?, ?, ?, ?)""",
            (username, password_hash, password_salt, role, full_name),
        )

    def record_login(self, user_id: int) -> None:
        self.db.execute(
            "UPDATE users SET last_login_at = datetime('now') WHERE id = ?", (user_id,)
        )

    def count(self) -> int:
        row = self.db.query_one("SELECT COUNT(*) AS c FROM users")
        return row["c"] if row else 0


class SettingsRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def get(self, key: str, default: str | None = None) -> str | None:
        row = self.db.query_one("SELECT value FROM application_settings WHERE key = ?", (key,))
        return row["value"] if row else default

    def get_all(self) -> dict[str, str]:
        rows = self.db.query("SELECT key, value FROM application_settings")
        return {r["key"]: r["value"] for r in rows}

    def set(self, key: str, value: str) -> None:
        self.db.execute(
            """INSERT INTO application_settings (key, value, updated_at)
               VALUES (?, ?, datetime('now'))
               ON CONFLICT(key) DO UPDATE SET value = excluded.value,
               updated_at = datetime('now')""",
            (key, value),
        )


class AuditLogRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def log(
        self, action: str, entity_type: str = "", entity_id: str = "",
        details: str = "", user_id: int | None = None,
    ) -> None:
        try:
            self.db.execute(
                """INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, action, entity_type, entity_id, details),
            )
        except Exception:
            logger.exception("Denetim kaydı yazılamadı: action=%s", action)

    def recent(self, limit: int = 200) -> list[dict]:
        rows = self.db.query(
            "SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        return [dict(r) for r in rows]
