"""Kayıt saklama süresi politikasını uygular: ayarlanan gün sayısından
eski tespit kayıtlarını ve ilişkili görüntü dosyalarını siler."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.database.repositories import AuditLogRepository, DetectionRepository

logger = logging.getLogger(__name__)


def purge_expired_detections(
    detection_repo: DetectionRepository,
    audit_repo: AuditLogRepository,
    retention_days: int,
) -> int:
    if retention_days <= 0:
        return 0
    cutoff = (datetime.now(timezone.utc) - timedelta(days=retention_days)).isoformat()
    image_paths = detection_repo.delete_older_than(cutoff)
    for path_str in image_paths:
        try:
            Path(path_str).unlink(missing_ok=True)
        except OSError:
            logger.warning("Tespit görüntüsü silinemedi: %s", path_str)
    if image_paths:
        audit_repo.log(
            action="retention_purge",
            entity_type="detections",
            details=f"{len(image_paths)} kayıt ve görüntü, {retention_days} günlük "
            "saklama politikası nedeniyle silindi.",
        )
    return len(image_paths)
