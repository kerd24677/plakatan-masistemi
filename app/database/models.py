"""Veritabanı satırlarını temsil eden hafif veri sınıfları."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass
class Camera:
    id: int
    name: str
    host: str
    port: int
    main_path: str
    sub_path: str
    username: str
    credential_ref: str
    transport: str
    location: str
    enabled: bool
    status: str
    last_status_at: str | None
    last_error: str | None
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Camera":
        d = dict(row)
        d["enabled"] = bool(d["enabled"])
        return cls(**d)

    def rtsp_url(self, password: str, profile: str = "main") -> str:
        path = self.main_path if profile == "main" else self.sub_path
        path = path or self.main_path
        auth = f"{self.username}:{password}@" if self.username else ""
        return f"rtsp://{auth}{self.host}:{self.port}/{path.lstrip('/')}"


@dataclass
class Detection:
    id: int
    camera_id: int
    plate_raw: str
    plate_normalized: str
    detection_confidence: float
    ocr_confidence: float
    image_path: str | None
    is_authorized: bool
    needs_review: bool
    review_status: str
    detected_at: str
    created_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Detection":
        d = dict(row)
        d["is_authorized"] = bool(d["is_authorized"])
        d["needs_review"] = bool(d["needs_review"])
        return cls(**d)


@dataclass
class AuthorizedVehicle:
    id: int
    plate_normalized: str
    description: str
    permission_status: str
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "AuthorizedVehicle":
        return cls(**dict(row))


@dataclass
class User:
    id: int
    username: str
    password_hash: str
    password_salt: str
    role: str
    full_name: str
    is_active: bool
    created_at: str
    last_login_at: str | None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "User":
        d = dict(row)
        d["is_active"] = bool(d["is_active"])
        return cls(**d)
