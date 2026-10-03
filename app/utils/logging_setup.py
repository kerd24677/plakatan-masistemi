"""Uygulama genelinde günlükleme yapılandırması.

ÖNEMLİ: Kamera parolaları veya tam RTSP URL'leri (parola içerebileceğinden)
hiçbir yerde log.info/debug/error çağrısına argüman olarak verilmemelidir.
Kamera modülü ve repository'ler bu kurala uyacak şekilde yazılmıştır:
yalnızca host/port/kamera adı loglanır.
"""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path


def setup_logging(logs_dir: Path, level: int = logging.INFO) -> None:
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / "application.log"

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(file_handler)
    root.addHandler(console_handler)

    # Gürültülü üçüncü parti kütüphaneleri sessizleştir
    logging.getLogger("PySide6").setLevel(logging.WARNING)
