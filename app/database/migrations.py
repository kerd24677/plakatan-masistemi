"""Şema sürümleme ve migrasyon uygulama mantığı.

Uygulama her açıldığında çalışır: veritabanı yoksa sıfırdan kurar,
varsa schema_meta.version ile app.config.constants.SCHEMA_VERSION'ı
karşılaştırıp eksik migrasyonları sırayla uygular. Mevcut kayıtlar
korunur; hiçbir migrasyon DROP TABLE veya veri kaybına yol açacak
şekilde yazılmamalıdır.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable

from app.config.constants import DEFAULT_SETTINGS, SCHEMA_VERSION
from app.database.schema import SCHEMA_STATEMENTS

MigrationFn = Callable[[sqlite3.Connection], None]


def _migration_v1(conn: sqlite3.Connection) -> None:
    for statement in SCHEMA_STATEMENTS:
        conn.execute(statement)
    for key, value in DEFAULT_SETTINGS.items():
        conn.execute(
            "INSERT OR IGNORE INTO application_settings (key, value) VALUES (?, ?)",
            (key, value),
        )


# Sıradaki her şema değişikliği için (version, fonksiyon) ekleyin.
# Örn: (2, _migration_v2_add_column)
MIGRATIONS: list[tuple[int, MigrationFn]] = [
    (1, _migration_v1),
]


def get_current_version(conn: sqlite3.Connection) -> int:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_meta'"
    )
    if cur.fetchone() is None:
        return 0
    row = conn.execute("SELECT version FROM schema_meta WHERE id = 1").fetchone()
    return row[0] if row else 0


def apply_migrations(conn: sqlite3.Connection) -> int:
    """Eksik migrasyonları uygular, son sürümü döndürür."""
    current = get_current_version(conn)
    with conn:
        for version, fn in MIGRATIONS:
            if version > current:
                fn(conn)
                conn.execute(
                    "INSERT INTO schema_meta (id, version) VALUES (1, ?) "
                    "ON CONFLICT(id) DO UPDATE SET version = excluded.version",
                    (version,),
                )
                current = version
    return current


def ensure_schema_up_to_date(conn: sqlite3.Connection) -> int:
    version = apply_migrations(conn)
    if version != SCHEMA_VERSION and version < SCHEMA_VERSION:
        raise RuntimeError(
            f"Veritabanı şeması güncellenemedi: mevcut={version}, "
            f"beklenen={SCHEMA_VERSION}. MIGRATIONS listesine eksik "
            "sürüm eklenmemiş olabilir."
        )
    return version
