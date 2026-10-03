"""Thread-safe SQLite bağlantı yöneticisi.

Kamera worker thread'leri ve UI aynı veritabanına eş zamanlı erişebildiği
için WAL modu açılır ve tüm yazma işlemleri bir RLock ile serileştirilir.
"""

from __future__ import annotations

import logging
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path

from app.database.migrations import ensure_schema_up_to_date

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(
            str(self.db_path), check_same_thread=False, timeout=10.0
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.execute("PRAGMA journal_mode = WAL")
        self._conn.execute("PRAGMA synchronous = NORMAL")
        with self._lock:
            ensure_schema_up_to_date(self._conn)
        logger.info("Veritabanı hazır: %s", self.db_path)

    @contextmanager
    def cursor(self):
        """Yazma işlemleri için kilitli, otomatik commit/rollback yapan cursor."""
        with self._lock:
            cur = self._conn.cursor()
            try:
                yield cur
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise
            finally:
                cur.close()

    def query(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        with self._lock:
            return self._conn.execute(sql, params).fetchall()

    def query_one(self, sql: str, params: tuple = ()) -> sqlite3.Row | None:
        with self._lock:
            return self._conn.execute(sql, params).fetchone()

    def execute(self, sql: str, params: tuple = ()) -> int:
        """INSERT/UPDATE/DELETE çalıştırır, lastrowid döndürür."""
        with self.cursor() as cur:
            cur.execute(sql, params)
            return cur.lastrowid

    def close(self) -> None:
        with self._lock:
            self._conn.close()
